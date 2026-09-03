from models import Policy, Customer, Device
from schemas import PaymentRiskRequest
from typing import List, Optional

class PolicyEvaluationResult:
    def __init__(self, is_violation: bool, decision: Optional[str], reason_codes: List[str]):
        self.is_violation = is_violation
        self.decision = decision # "BLOCK", "REVIEW", or None
        self.reason_codes = reason_codes

class PolicyEngine:
    @staticmethod
    def evaluate(policy: Policy, request: PaymentRiskRequest, ml_probability: float) -> PolicyEvaluationResult:
        is_violation = False
        decision = None
        reason_codes = []

        # 1. Hard Limits
        if request.amount > policy.max_transaction_amount:
            is_violation = True
            reason_codes.append("AMOUNT_EXCEEDS_POLICY_LIMIT")
            decision = "BLOCK"

        # 2. High Risk Category
        if request.item_category in policy.high_risk_categories:
            is_violation = True
            reason_codes.append("HIGH_RISK_MERCHANT_CATEGORY")
            if not decision:
                decision = "REVIEW"

        # 3. ML Thresholding
        if ml_probability >= policy.block_threshold:
            is_violation = True
            reason_codes.append("ML_CHARGEBACK_PROBABILITY_CRITICAL")
            decision = "BLOCK"
        elif ml_probability >= policy.review_threshold:
            is_violation = True
            reason_codes.append("ML_CHARGEBACK_PROBABILITY_ELEVATED")
            if not decision:
                decision = "REVIEW"

        return PolicyEvaluationResult(is_violation, decision, reason_codes)
