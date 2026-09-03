import os
import joblib
import pandas as pd
from typing import Dict, Any
import json

class ChargebackPredictor:
    def __init__(self, model_path="models/chargeback_model.pkl", eval_path="data/model_evaluation.json"):
        self.model = None
        self.model_version = "chargeback-histgradientboosting-v2" # fallback
        
        if os.path.exists(eval_path):
            try:
                with open(eval_path, 'r') as f:
                    eval_data = json.load(f)
                    self.model_version = eval_data.get('model_name', self.model_version)
            except Exception:
                pass
                
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
            
    def predict_probability(self, features: Dict[str, Any]) -> float:
        if not self.model:
            # Fallback heuristic if no model found
            base = 0.05
            if features.get('previous_chargebacks', 0) > 0:
                base += 0.5
            if features.get('amount', 0) > 1000:
                base += 0.2
            return min(0.99, base)
            
        # Convert dictionary to DataFrame for scikit-learn
        feature_order = ['amount', 'is_new_device', 'attempt_count', 'previous_chargebacks', 
                         'velocity_24h', 'account_age_days', 'amount_vs_customer_baseline', 
                         'device_customer_count', 'failed_attempt_ratio']
        df = pd.DataFrame([{k: features.get(k, 0) for k in feature_order}])
        
        prob = self.model.predict_proba(df)[0][1]
        return float(prob)
