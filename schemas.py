from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List

class PaymentRiskRequest(BaseModel):
    merchant_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    order_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    payment_method: str = Field(...)
    device_fingerprint: str = Field(...)
    ip_address: Optional[str] = None
    item_category: str = Field(...)
    context: Optional[Dict[str, Any]] = None

    @validator("currency")
    def validate_currency(cls, v):
        allowed_currencies = ["INR", "USD", "EUR", "GBP"]
        if v.upper() not in allowed_currencies:
            raise ValueError(f"Unsupported currency: {v}")
        return v.upper()

class RiskSignalResponse(BaseModel):
    signal_type: str
    severity: str
    value: Optional[float] = None
    description: str

class AIEvidence(BaseModel):
    reason_code: str
    severity: str
    description: str
    source: str

class AIAnalysisResult(BaseModel):
    risk_summary: str
    evidence: List[AIEvidence]
    risk_factors: List[str]
    recommended_action: str
    confidence: float
    model_used: Optional[str] = None
    model_version: Optional[str] = None

class RiskDecisionResponse(BaseModel):
    ml_probability: float
    risk_score: int
    severity: str
    decision: str # ALLOW, REVIEW, BLOCK
    reason_codes: List[str]
    signals: List[RiskSignalResponse]
    recommended_action: str
    ai_analysis: Optional[AIAnalysisResult] = None
