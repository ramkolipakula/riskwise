from policy_engine import PolicyEvaluationResult
from models import RiskSignal
from typing import List, Tuple

class DecisionEngine:
    @staticmethod
    def make_decision(policy_result: PolicyEvaluationResult, signals: List[RiskSignal], ml_probability: float) -> Tuple[str, int, str]:
        """
        Returns:
            decision (str): ALLOW, REVIEW, BLOCK
            risk_score (int): 0-100 deterministic combined score
            severity (str): LOW, MEDIUM, HIGH, CRITICAL
        """
        
        # Base deterministic score from signals
        base_score = 0
        severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        
        for s in signals:
            if s.severity == "CRITICAL":
                base_score += 40
            elif s.severity == "HIGH":
                base_score += 25
            elif s.severity == "MEDIUM":
                base_score += 10
            elif s.severity == "LOW":
                base_score += 5
            severity_counts[s.severity] += 1
            
        # Add ML factor to risk score (just for visualization/legacy)
        risk_score = min(100, base_score + int(ml_probability * 50))
        
        # Severity calculation
        if severity_counts["CRITICAL"] > 0 or risk_score >= 80:
            severity = "CRITICAL"
        elif severity_counts["HIGH"] > 0 or risk_score >= 60:
            severity = "HIGH"
        elif severity_counts["MEDIUM"] > 0 or risk_score >= 30:
            severity = "MEDIUM"
        else:
            severity = "LOW"
            
        # Deterministic override (Policy overrides all)
        if policy_result.decision == "BLOCK":
            decision = "BLOCK"
        elif policy_result.decision == "REVIEW":
            decision = "REVIEW"
        else:
            # Fallback to score if policy didn't trigger
            if risk_score >= 80:
                decision = "BLOCK"
            elif risk_score >= 60:
                decision = "REVIEW"
            else:
                decision = "ALLOW"
                
        return decision, risk_score, severity
