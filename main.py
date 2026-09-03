import time
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from database import engine, Base, get_db
from models import Merchant, Customer, Device, Order, Payment, Policy, RiskSignal, RiskEvaluation, AuditEvent, Chargeback
from schemas import PaymentRiskRequest, RiskDecisionResponse, RiskSignalResponse
from policy_engine import PolicyEngine
from risk_signal_engine import RiskSignalEngine
from decision_engine import DecisionEngine
from investigation_agent import get_investigation_agent
from ml_detector import ChargebackPredictor

# Create tables (for testing, normally use Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RiskWise — Merchant Chargeback Risk Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api_routes import router as ui_router
app.include_router(ui_router)

predictor = ChargebackPredictor()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/v1/risk/evaluate", response_model=RiskDecisionResponse)
def evaluate_risk(request: PaymentRiskRequest, db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.id == request.merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=400, detail="Invalid merchant")
    
    customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
    if not customer:
        raise HTTPException(status_code=400, detail="Invalid customer")
        
    order = db.query(Order).filter(Order.id == request.order_id).first()
    if not order:
        # Auto-create order for demo purposes if it doesn't exist
        order = Order(id=request.order_id, merchant_id=merchant.id, customer_id=customer.id, amount=request.amount, currency=request.currency, item_category=request.item_category)
        db.add(order)
        db.flush()

    device = db.query(Device).filter(Device.device_fingerprint == request.device_fingerprint).first()
    if not device:
        device = Device(customer_id=customer.id, device_fingerprint=request.device_fingerprint, is_new=True, ip_address=request.ip_address)
        db.add(device)
        db.flush()

    policy = db.query(Policy).filter((Policy.merchant_id == merchant.id) | (Policy.merchant_id == None)).first()
    if not policy:
        raise HTTPException(status_code=400, detail="Missing policy")

    historical_payments = db.query(Payment).filter(Payment.customer_id == customer.id).all()
    historical_chargebacks = db.query(Chargeback).filter(Chargeback.customer_id == customer.id).count()

    # Create payment record
    payment = Payment(
        merchant_id=merchant.id,
        customer_id=customer.id,
        order_id=order.id,
        device_id=device.id,
        amount=request.amount,
        currency=request.currency,
        payment_method=request.payment_method,
        status="PENDING"
    )
    db.add(payment)
    db.flush()

    try:
        # 1. Feature Extraction & Deterministic Signals
        features, signals_data = RiskSignalEngine.extract_features_and_signals(
            request=request,
            customer=customer,
            historical_payments=historical_payments,
            historical_chargebacks=historical_chargebacks,
            device=device,
            policy_violation_codes=[],
            db=db
        )
        
        # 2. ML Prediction
        ml_probability = predictor.predict_probability(features)

        # 3. Policy Evaluation
        policy_result = PolicyEngine.evaluate(policy, request, ml_probability)
        
        # Update signals with policy violations
        if policy_result.is_violation:
             _, extra_signals = RiskSignalEngine.extract_features_and_signals(
                request=request, customer=customer, historical_payments=historical_payments,
                historical_chargebacks=historical_chargebacks, device=device,
                policy_violation_codes=policy_result.reason_codes,
                db=db
             )
             signals_data = extra_signals # Replacing for simplicity or extend

        # 4. Deterministic Decision Engine
        decision_str, score, severity = DecisionEngine.make_decision(policy_result, signals_data, ml_probability)
        recommended_action = decision_str 

        # 5. AI Investigation
        investigation_agent = get_investigation_agent()
        ai_analysis = investigation_agent.analyze_risk(
            request_data=request.dict(),
            features=features,
            ml_prob=ml_probability,
            signals=signals_data
        )

        # Persist signals and decision
        for sig in signals_data:
            sig.payment_id = payment.id
            db.add(sig)
            
        risk_evaluation = RiskEvaluation(
            payment_id=payment.id,
            ml_probability=ml_probability,
            model_version=predictor.model_version,
            risk_score=score,
            severity=severity,
            decision=decision_str,
            reason_codes=policy_result.reason_codes,
            recommended_action=recommended_action,
            ai_analysis=ai_analysis.dict() if ai_analysis else None
        )
        db.add(risk_evaluation)
        db.flush()

        audit_event = AuditEvent(
            payment_id=payment.id,
            risk_evaluation_id=risk_evaluation.id,
            event_type="CHARGEBACK_RISK_EVALUATION",
            decision=decision_str,
            ml_probability=ml_probability,
            model_version=predictor.model_version,
            policy_version=policy.version,
            ai_involved=ai_analysis is not None,
            ai_model_used=ai_analysis.model_used if ai_analysis else None,
            ai_model_version=ai_analysis.model_version if ai_analysis else None,
            ai_recommendation=ai_analysis.recommended_action if ai_analysis else None
        )
        db.add(audit_event)
        
        # Update payment status
        payment.status = "COMPLETED" if decision_str == "ALLOW" else ("BLOCKED" if decision_str == "BLOCK" else "REVIEW")
        if decision_str == "ALLOW":
            order.status = "COMPLETED"
        elif decision_str == "BLOCK":
            order.status = "CANCELLED"

        db.commit()

        return RiskDecisionResponse(
            ml_probability=ml_probability,
            risk_score=score,
            severity=severity,
            decision=decision_str,
            reason_codes=policy_result.reason_codes,
            signals=[RiskSignalResponse(
                signal_type=s.signal_type,
                severity=s.severity,
                value=s.value,
                description=s.description
            ) for s in signals_data],
            recommended_action=recommended_action,
            ai_analysis=ai_analysis
        )

    except Exception as e:
        db.rollback()
        print(f"Internal evaluation error: {e}")
        raise HTTPException(status_code=500, detail="Internal evaluation error")
