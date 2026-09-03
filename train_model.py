import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix, accuracy_score
import joblib
import json

def generate_synthetic_data(n_samples=10000):
    np.random.seed(42)
    
    start_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
    dates = [start_date + timedelta(minutes=int(x)) for x in np.random.randint(0, 300000, n_samples)]
    dates.sort()
    
    data = []
    
    # Track states for feature engineering to avoid leakage
    customer_tx_count = {}
    customer_amount_sum = {}
    device_customers = {}
    
    for i in range(n_samples):
        date = dates[i]
        
        # Base independent features
        customer_id = np.random.randint(1, 1000)
        device_id = np.random.randint(1, 2000)
        
        amount = np.random.lognormal(mean=4, sigma=1) * 10
        is_new_device = np.random.choice([0, 1], p=[0.7, 0.3])
        attempt_count = np.random.choice([1, 2, 3, 4], p=[0.8, 0.1, 0.05, 0.05])
        previous_chargebacks = np.random.choice([0, 1, 2], p=[0.95, 0.04, 0.01])
        velocity_24h = np.random.poisson(lam=1) if previous_chargebacks == 0 else np.random.poisson(lam=3)
        account_age_days = np.random.randint(0, 365)
        
        # Feature Engineering (Leakage Free: only uses PAST information)
        past_tx_count = customer_tx_count.get(customer_id, 0)
        past_amount_sum = customer_amount_sum.get(customer_id, 0)
        
        amount_vs_customer_baseline = 1.0
        if past_tx_count >= 5:
            avg_past = past_amount_sum / past_tx_count
            amount_vs_customer_baseline = amount / avg_past
            
        device_cust_set = device_customers.get(device_id, set())
        device_customer_count = len(device_cust_set)
        if customer_id not in device_cust_set:
            device_customer_count += 1 # Includes current
            
        failed_attempt_ratio = (attempt_count - 1) / attempt_count
        
        # Update states for next rows
        customer_tx_count[customer_id] = past_tx_count + 1
        customer_amount_sum[customer_id] = past_amount_sum + amount
        device_cust_set.add(customer_id)
        device_customers[device_id] = device_cust_set
        
        # Ground Truth Generation (Non-trivial,        # Base risk is low
        risk_logit = -4.0
        
        # Linear risk factors (Stronger signal)
        risk_logit += 1.0 * is_new_device
        risk_logit += 1.5 * failed_attempt_ratio
        risk_logit += 2.5 * previous_chargebacks
        risk_logit += 0.3 * velocity_24h
        risk_logit += 1.0 * (1 if amount_vs_customer_baseline > 3.0 else 0)
        risk_logit += 1.0 * (1 if device_customer_count > 2 else 0)
        risk_logit -= 1.0 * (1 if account_age_days > 90 else 0)
        
        # NON-TRIVIAL PATTERNS (Interaction terms)
        if amount > 2000 and is_new_device:
            risk_logit += 2.0
        if velocity_24h > 5 and account_age_days < 30:
            risk_logit += 2.0
        if previous_chargebacks > 0 and is_new_device:
            risk_logit += 2.5
            
        risk_logit += np.random.normal(0, 0.2)
            
        prob = 1 / (1 + np.exp(-risk_logit))
        is_chargeback = int(np.random.random() < prob)
        
        data.append({
            'timestamp': date,
            'amount': amount,
            'is_new_device': is_new_device,
            'attempt_count': attempt_count,
            'previous_chargebacks': previous_chargebacks,
            'velocity_24h': velocity_24h,
            'account_age_days': account_age_days,
            'amount_vs_customer_baseline': amount_vs_customer_baseline,
            'device_customer_count': device_customer_count,
            'failed_attempt_ratio': failed_attempt_ratio,
            'is_chargeback': is_chargeback
        })
        
    return pd.DataFrame(data)

def train_and_evaluate():
    print("Generating synthetic chargeback dataset...")
    df = generate_synthetic_data(10000)
    
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/chargeback_dataset.csv', index=False)
    print(f"Total dataset: {len(df)} rows. Chargeback rate: {df['is_chargeback'].mean():.2%}")
    
    # Temporal Train/Test split (Chronological, No Random Shuffling)
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    
    features = ['amount', 'is_new_device', 'attempt_count', 'previous_chargebacks', 
                'velocity_24h', 'account_age_days', 'amount_vs_customer_baseline', 
                'device_customer_count', 'failed_attempt_ratio']
    target = 'is_chargeback'
    
    X_train = train_df[features]
    y_train = train_df[target]
    X_test = test_df[features]
    y_test = test_df[target]
    
    # Models to compare
    models = {
        'Logistic Regression': Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))
        ]),
        'Random Forest': Pipeline([
            ('scaler', StandardScaler()),
            ('clf', RandomForestClassifier(n_estimators=100, max_depth=10, class_weight='balanced', random_state=42))
        ]),
        'HistGradientBoosting': Pipeline([
            ('scaler', StandardScaler()),
            ('clf', HistGradientBoostingClassifier(max_iter=100, random_state=42, class_weight='balanced'))
        ])
    }
    
    best_f1 = -1
    best_model_name = ""
    best_model = None
    all_model_metrics = {}
    
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    manual_review_cost = 10.0 # Illustrative assumption
    
    for name, pipeline in models.items():
        print(f"\nTraining {name}...")
        pipeline.fit(X_train, y_train)
        
        y_probs = pipeline.predict_proba(X_test)[:, 1]
        
        model_thresh_metrics = []
        for thresh in thresholds:
            y_pred = (y_probs >= thresh).astype(int)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            cm = confusion_matrix(y_test, y_pred)
            tn, fp, fn, tp = cm.ravel() if len(cm.ravel()) == 4 else (0,0,0,0)
            fp_cost = fp * manual_review_cost
            
            model_thresh_metrics.append({
                'threshold': thresh,
                'precision': round(precision, 3),
                'recall': round(recall, 3),
                'f1': round(f1, 3),
                'false_positives': int(fp),
                'false_negatives': int(fn),
                'false_positive_cost': float(round(fp_cost, 2))
            })
            
            # Select the model that achieves the highest F1 score overall across any threshold
            if f1 > best_f1:
                best_f1 = f1
                best_model_name = name
                best_model = pipeline
                best_threshold = thresh
                
        all_model_metrics[name] = model_thresh_metrics
        
    print(f"\nSelected Model: {best_model_name} (Best Threshold: {best_threshold}, F1: {best_f1:.3f})")
    
    os.makedirs('models', exist_ok=True)
    joblib.dump(best_model, 'models/chargeback_model.pkl')
    
    # Calculate prevented loss for the best model at default threshold
    default_thresh = best_threshold
    y_probs_best = best_model.predict_proba(X_test)[:, 1]
    y_pred_best = (y_probs_best >= default_thresh).astype(int)
    
    metrics_list = []
    for m in all_model_metrics[best_model_name]:
        y_pred_t = (y_probs_best >= m['threshold']).astype(int)
        tp_indices = (y_pred_t == 1) & (y_test == 1)
        prevented_loss = float(round(test_df.loc[tp_indices, 'amount'].sum(), 2))
        
        metrics_list.append({
            'threshold': m['threshold'],
            'precision': m['precision'],
            'recall': m['recall'],
            'f1': m['f1'],
            'accuracy': round(accuracy_score(y_test, y_pred_t), 3),
            'false_positives': m['false_positives'],
            'false_negatives': m['false_negatives'],
            'true_positives': int(sum(tp_indices)),
            'true_negatives': int(sum((y_pred_t == 0) & (y_test == 0))),
            'false_positive_cost': m['false_positive_cost'],
            'prevented_loss': prevented_loss
        })

    eval_results = {
        'model_name': f"chargeback-{best_model_name.lower().replace(' ', '-')}-v2",
        'model_architecture': best_model_name,
        'dataset_version': 'dataset-v2',
        'evaluation_timestamp': datetime.now(timezone.utc).isoformat(),
        'default_threshold': default_thresh,
        'features': features,
        'metrics_by_threshold': metrics_list,
        'candidate_models': all_model_metrics,
        'test_set_size': len(test_df),
        'train_set_size': len(train_df)
    }
    
    with open('data/model_evaluation.json', 'w') as f:
        json.dump(eval_results, f, indent=2)
        
    print("\nModel evaluation complete and saved to data/model_evaluation.json")

if __name__ == "__main__":
    train_and_evaluate()
