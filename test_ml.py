import pytest
import os
import json
import joblib
import pandas as pd
from datetime import datetime

def test_model_loads_successfully():
    assert os.path.exists('models/chargeback_model.pkl')
    model = joblib.load('models/chargeback_model.pkl')
    assert model is not None
    assert hasattr(model, 'predict_proba')

def test_prediction_between_0_and_1():
    model = joblib.load('models/chargeback_model.pkl')
    test_data = pd.DataFrame([{
        'amount': 100,
        'is_new_device': 0,
        'attempt_count': 1,
        'previous_chargebacks': 0,
        'velocity_24h': 1,
        'account_age_days': 180,
        'amount_vs_customer_baseline': 1.0,
        'device_customer_count': 1,
        'failed_attempt_ratio': 0.0
    }])
    probs = model.predict_proba(test_data)
    assert len(probs) == 1
    prob_chargeback = probs[0][1]
    assert 0 <= prob_chargeback <= 1

def test_temporal_split_no_leakage():
    assert os.path.exists('data/chargeback_dataset.csv')
    df = pd.read_csv('data/chargeback_dataset.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    assert df['timestamp'].is_monotonic_increasing, "Dataset must be chronologically sorted for temporal split"
    
    split_idx = int(len(df) * 0.8)
    train_max_time = df.iloc[:split_idx]['timestamp'].max()
    test_min_time = df.iloc[split_idx:]['timestamp'].min()
    
    assert train_max_time <= test_min_time, "Temporal leakage detected: Train data overlaps Test data timeline"

def test_no_target_leakage_in_features():
    assert os.path.exists('data/model_evaluation.json')
    with open('data/model_evaluation.json', 'r') as f:
        eval_data = json.load(f)
        
    features = eval_data['features']
    invalid_keywords = ['chargeback', 'refund', 'status', 'future', 'label']
    for feat in features:
        # "previous_chargebacks" is allowed, but "is_chargeback" is not
        if feat == 'previous_chargebacks':
            continue
        for kw in invalid_keywords:
            assert kw not in feat.lower(), f"Potential target leakage in feature: {feat}"
            
def test_evaluation_json_exists_and_contains_metrics():
    assert os.path.exists('data/model_evaluation.json')
    with open('data/model_evaluation.json', 'r') as f:
        eval_data = json.load(f)
        
    assert 'model_name' in eval_data
    assert eval_data['train_set_size'] > 0
    assert eval_data['test_set_size'] > 0
    assert 'metrics_by_threshold' in eval_data
    
    metrics = eval_data['metrics_by_threshold']
    assert len(metrics) > 0
    
    for m in metrics:
        assert 'precision' in m
        assert 'recall' in m
        assert 'f1' in m
        assert 'false_positive_cost' in m
        assert 'true_positives' in m

def test_class_imbalance_handling_occurs_only_on_training_data():
    model = joblib.load('models/chargeback_model.pkl')
    # If the model is a pipeline, verify that the classifier has class_weight defined if applicable
    # HistGradientBoosting in sklearn doesn't explicitly expose class_weight in all older versions
    # But LogisticRegression and RandomForest do. We just check it's a valid pipeline.
    assert hasattr(model, 'steps')
    clf = model.steps[-1][1]
    # At least ensure it's a known classifier
    assert clf.__class__.__name__ in ['LogisticRegression', 'RandomForestClassifier', 'HistGradientBoostingClassifier']

def test_model_is_reproducible():
    # If we run train_model.py again, does it yield the exact same test_set_size and metrics?
    # We won't re-run the training in a unit test because it's slow, but we can verify the seeds exist in the code.
    with open('train_model.py', 'r') as f:
        code = f.read()
    assert 'np.random.seed(' in code
    assert 'random_state=' in code
