import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, JSON, Table
from sqlalchemy.orm import relationship
from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Merchant(Base):
    __tablename__ = "merchants"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    orders = relationship("Order", back_populates="merchant")
    payments = relationship("Payment", back_populates="merchant")
    refunds = relationship("Refund", back_populates="merchant")
    chargebacks = relationship("Chargeback", back_populates="merchant")
    policies = relationship("Policy", back_populates="merchant")

class Customer(Base):
    __tablename__ = "customers"
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    account_age_days = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    orders = relationship("Order", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")
    refunds = relationship("Refund", back_populates="customer")
    chargebacks = relationship("Chargeback", back_populates="customer")
    devices = relationship("Device", back_populates="customer")

class Device(Base):
    __tablename__ = "devices"
    id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    device_fingerprint = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    is_new = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    customer = relationship("Customer", back_populates="devices")

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="USD")
    item_category = Column(String, nullable=False)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    merchant = relationship("Merchant", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    payments = relationship("Payment", back_populates="order")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    device_id = Column(String, ForeignKey("devices.id"), nullable=True)
    
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="USD")
    payment_method = Column(String, nullable=False)
    attempt_count = Column(Integer, default=1)
    status = Column(String, default="PENDING") # PENDING, COMPLETED, FAILED, BLOCKED, REVIEW
    
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    merchant = relationship("Merchant", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")
    order = relationship("Order", back_populates="payments")
    chargeback = relationship("Chargeback", back_populates="payment", uselist=False)
    refunds = relationship("Refund", back_populates="payment")
    
    risk_evaluation = relationship("RiskEvaluation", back_populates="payment", uselist=False)
    signals = relationship("RiskSignal", back_populates="payment")

class Chargeback(Base):
    __tablename__ = "chargebacks"
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    payment_id = Column(String, ForeignKey("payments.id"), nullable=False)
    amount = Column(Float, nullable=False)
    reason_code = Column(String, nullable=False)
    status = Column(String, default="OPEN")
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    merchant = relationship("Merchant", back_populates="chargebacks")
    customer = relationship("Customer", back_populates="chargebacks")
    payment = relationship("Payment", back_populates="chargeback")

class Refund(Base):
    __tablename__ = "refunds"
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    payment_id = Column(String, ForeignKey("payments.id"), nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    merchant = relationship("Merchant", back_populates="refunds")
    customer = relationship("Customer", back_populates="refunds")
    payment = relationship("Payment", back_populates="refunds")

class Policy(Base):
    __tablename__ = "policies"
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=True) # Nullable for global policies
    max_transaction_amount = Column(Float, nullable=False)
    high_risk_categories = Column(JSON, nullable=False) # e.g. ["electronics", "digital_goods"]
    block_threshold = Column(Float, nullable=False) # ML Probability threshold to auto-block
    review_threshold = Column(Float, nullable=False) # ML Probability threshold to manual review
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    merchant = relationship("Merchant", back_populates="policies")

class RiskSignal(Base):
    __tablename__ = "risk_signals"
    id = Column(String, primary_key=True, default=generate_uuid)
    payment_id = Column(String, ForeignKey("payments.id"), nullable=False)
    signal_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    value = Column(Float, nullable=True)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    payment = relationship("Payment", back_populates="signals")

class RiskEvaluation(Base):
    __tablename__ = "risk_evaluations"
    id = Column(String, primary_key=True, default=generate_uuid)
    payment_id = Column(String, ForeignKey("payments.id"), nullable=False)
    
    ml_probability = Column(Float, nullable=False) # e.g. 0.87
    model_version = Column(String, nullable=False) # e.g. chargeback-histgradientboosting-v2
    
    risk_score = Column(Integer, nullable=False) # legacy deterministic score, or combined
    severity = Column(String, nullable=False)
    decision = Column(String, nullable=False) # ALLOW, REVIEW, BLOCK
    reason_codes = Column(JSON, nullable=False)
    recommended_action = Column(String, nullable=False)
    
    ai_analysis = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    payment = relationship("Payment", back_populates="risk_evaluation")
    audit_events = relationship("AuditEvent", back_populates="risk_evaluation")

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(String, primary_key=True, default=generate_uuid)
    payment_id = Column(String, ForeignKey("payments.id"), nullable=False)
    risk_evaluation_id = Column(String, ForeignKey("risk_evaluations.id"), nullable=False)
    event_type = Column(String, nullable=False)
    decision = Column(String, nullable=False)
    
    ml_probability = Column(Float, nullable=True)
    model_version = Column(String, nullable=True)
    
    policy_version = Column(Integer, nullable=False)
    
    ai_involved = Column(Boolean, default=False)
    ai_model_used = Column(String, nullable=True)
    ai_model_version = Column(String, nullable=True)
    ai_recommendation = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    risk_evaluation = relationship("RiskEvaluation", back_populates="audit_events")
