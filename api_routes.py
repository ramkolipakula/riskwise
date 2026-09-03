from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Merchant, Customer, Device, Order, Payment, Policy, RiskSignal, RiskEvaluation, AuditEvent, Chargeback
from typing import List, Dict, Any
from sqlalchemy import desc

router = APIRouter(prefix="/api/v1", tags=["UI"])

@router.get("/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_evaluations = db.query(RiskEvaluation).count()
    high_risk = db.query(RiskEvaluation).filter(RiskEvaluation.severity.in_(["HIGH", "CRITICAL"])).count()
    review_queue = db.query(RiskEvaluation).filter(RiskEvaluation.decision == "REVIEW").count()
    predicted_chargebacks = db.query(RiskEvaluation).filter(RiskEvaluation.decision == "BLOCK").count()
    
    # Calculate estimated prevented loss (sum of amounts for blocked/predicted chargebacks)
    prevented_loss = 0
    blocked_payments = db.query(Payment).join(RiskEvaluation).filter(RiskEvaluation.decision == "BLOCK").all()
    prevented_loss = sum(p.amount for p in blocked_payments)

    return {
        "total_evaluations": total_evaluations,
        "high_risk": high_risk,
        "review_queue": review_queue,
        "predicted_chargebacks": predicted_chargebacks,
        "prevented_loss": prevented_loss
    }

@router.get("/payments")
def get_payments(db: Session = Depends(get_db)):
    payments = db.query(Payment).order_by(desc(Payment.created_at)).limit(50).all()
    res = []
    for p in payments:
        res.append({
            "id": p.id,
            "amount": p.amount,
            "currency": p.currency,
            "customer_id": p.customer_id,
            "payment_method": p.payment_method,
            "status": p.status,
            "created_at": p.created_at,
            "ml_probability": p.risk_evaluation.ml_probability if p.risk_evaluation else None,
            "severity": p.risk_evaluation.severity if p.risk_evaluation else None,
            "decision": p.risk_evaluation.decision if p.risk_evaluation else None,
        })
    return res

@router.get("/payments/{id}")
def get_payment(id: str, db: Session = Depends(get_db)):
    p = db.query(Payment).filter(Payment.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found")

    signals = []
    for s in p.signals:
        signals.append({
            "signal_type": s.signal_type,
            "severity": s.severity,
            "value": s.value,
            "description": s.description
        })

    return {
        "id": p.id,
        "amount": p.amount,
        "currency": p.currency,
        "customer_id": p.customer_id,
        "payment_method": p.payment_method,
        "status": p.status,
        "created_at": p.created_at,
        "customer": {"id": p.customer.id, "name": p.customer.name, "account_age_days": p.customer.account_age_days} if p.customer else None,
        "decision": {
            "ml_probability": p.risk_evaluation.ml_probability if p.risk_evaluation else None,
            "decision": p.risk_evaluation.decision if p.risk_evaluation else None,
            "severity": p.risk_evaluation.severity if p.risk_evaluation else None,
            "risk_score": p.risk_evaluation.risk_score if p.risk_evaluation else None,
            "reason_codes": p.risk_evaluation.reason_codes if p.risk_evaluation else [],
            "recommended_action": p.risk_evaluation.recommended_action if p.risk_evaluation else None,
            "ai_analysis": p.risk_evaluation.ai_analysis if p.risk_evaluation else None
        } if p.risk_evaluation else None,
        "signals": signals
    }

@router.get("/reviews")
def get_reviews(db: Session = Depends(get_db)):
    evals = (
        db.query(RiskEvaluation)
        .filter(RiskEvaluation.decision == "REVIEW")
        .order_by(desc(RiskEvaluation.ml_probability))
        .all()
    )
    res = []
    for e in evals:
        p = e.payment
        if not p:
            continue
        res.append({
            "case_id": e.id,
            "payment_id": p.id,
            "ml_probability": e.ml_probability,
            "severity": e.severity,
            "amount": p.amount,
            "currency": p.currency,
            "reason_codes": e.reason_codes,
            "customer_id": p.customer_id,
            "created_at": e.created_at,
            "status": p.status,
            "ai_analysis": e.ai_analysis
        })
    return res

@router.get("/audit-events")
def get_audit_events(db: Session = Depends(get_db)):
    events = db.query(AuditEvent).order_by(desc(AuditEvent.created_at)).limit(100).all()
    res = []
    for e in events:
        res.append({
            "id": e.id,
            "payment_id": e.payment_id,
            "event_type": e.event_type,
            "decision": e.decision,
            "ml_probability": e.ml_probability,
            "model_version": e.model_version,
            "policy_version": e.policy_version,
            "ai_involved": e.ai_involved,
            "ai_model_used": e.ai_model_used,
            "ai_model_version": e.ai_model_version,
            "ai_recommendation": e.ai_recommendation,
            "created_at": e.created_at
        })
    return res

@router.get("/merchants")
def get_merchants(db: Session = Depends(get_db)):
    merchants = db.query(Merchant).all()
    return [{"id": m.id, "name": m.name} for m in merchants]

@router.get("/customers")
def get_customers(db: Session = Depends(get_db)):
    customers = db.query(Customer).all()
    res = []
    for c in customers:
        res.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "account_age_days": c.account_age_days,
            "created_at": c.created_at
        })
    return res

@router.get("/devices")
def get_devices(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    return [{"id": d.id, "fingerprint": d.device_fingerprint, "customer_id": d.customer_id, "is_new": d.is_new} for d in devices]

@router.get("/policies")
def get_policies(db: Session = Depends(get_db)):
    pols = db.query(Policy).all()
    res = []
    for p in pols:
        res.append({
            "id": p.id,
            "merchant_id": p.merchant_id,
            "max_transaction_amount": p.max_transaction_amount,
            "high_risk_categories": p.high_risk_categories,
            "block_threshold": p.block_threshold,
            "review_threshold": p.review_threshold,
            "version": p.version,
            "created_at": p.created_at
        })
    return res

@router.get("/model/evaluation")
def get_model_evaluation():
    import json
    import os
    path = "data/model_evaluation.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

@router.get("/config")
def get_config():
    """Surface server-side configuration to the frontend for badge display."""
    import os
    provider = os.getenv("AI_PROVIDER", "none").lower()
    provider_label = {
        "mock": "Mock (Rule-based)",
        "llm": os.getenv("AI_MODEL", "LLM"),
        "none": "None (Deterministic only)"
    }.get(provider, provider)
    return {
        "ai_provider": provider,
        "ai_provider_label": provider_label
    }

