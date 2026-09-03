import pytest
import os
import json
from fastapi.testclient import TestClient
from main import app
from database import Base, engine, get_db, SessionLocal
from seed import seed_data
from models import Merchant, Customer, Device, Payment, RiskEvaluation, AuditEvent

os.environ["AI_PROVIDER"] = "mock"

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    seed_data()
    yield
    
@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_test_data(db_session):
    merchant = db_session.query(Merchant).first()
    customer = db_session.query(Customer).first()
    device = db_session.query(Device).filter(Device.customer_id == customer.id).first()
    return merchant, customer, device

def test_ai_investigation_returns_structured_evidence(setup_database, db_session):
    merchant, customer, device = get_test_data(db_session)
    payload = {
        "merchant_id": merchant.id,
        "customer_id": customer.id,
        "order_id": "test_ai_1",
        "amount": 250000, # Will trigger AMOUNT anomaly hint in MockAIProvider
        "currency": "USD",
        "payment_method": "card",
        "device_fingerprint": device.device_fingerprint,
        "item_category": "books"
    }
    response = client.post("/api/v1/risk/evaluate", json=payload)
    data = response.json()
    ai = data.get("ai_analysis")
    assert ai is not None
    assert "risk_summary" in ai
    assert "evidence" in ai
    assert len(ai["evidence"]) > 0
    assert ai["evidence"][0]["reason_code"] == "AMOUNT_ANOMALY"
    assert ai["model_used"] == "mock-provider"

def test_ai_recommendation_advisory_only(setup_database, db_session):
    # AI BLOCK + deterministic ALLOW = ALLOW (where policy permits and risk score is low)
    os.environ["TEST_AI_FORCE_BLOCK"] = "1"
    merchant, customer, device = get_test_data(db_session)
    payload = {
        "merchant_id": merchant.id,
        "customer_id": customer.id,
        "order_id": "test_ai_2",
        "amount": 10, # Very low amount, no deterministic policy hit
        "currency": "USD",
        "payment_method": "card",
        "device_fingerprint": device.device_fingerprint,
        "item_category": "books"
    }
    response = client.post("/api/v1/risk/evaluate", json=payload)
    data = response.json()
    
    assert data["ai_analysis"]["recommended_action"] == "BLOCK"
    # Even if AI recommends BLOCK, the final decision is driven by deterministic policy/score.
    # Since risk score is very low, decision is ALLOW.
    assert data["decision"] == "ALLOW"
    del os.environ["TEST_AI_FORCE_BLOCK"]

def test_ai_fallback_timeout(setup_database, db_session):
    os.environ["TEST_AI_TIMEOUT"] = "1"
    merchant, customer, device = get_test_data(db_session)
    payload = {
        "merchant_id": merchant.id,
        "customer_id": customer.id,
        "order_id": "test_ai_3",
        "amount": 100,
        "currency": "USD",
        "payment_method": "card",
        "device_fingerprint": device.device_fingerprint,
        "item_category": "books"
    }
    response = client.post("/api/v1/risk/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Should safely fallback to deterministic evaluation without crashing
    assert data["ai_analysis"] is None
    assert data["decision"] == "ALLOW"
    del os.environ["TEST_AI_TIMEOUT"]

def test_ai_fallback_error(setup_database, db_session):
    os.environ["TEST_AI_ERROR"] = "1"
    merchant, customer, device = get_test_data(db_session)
    payload = {
        "merchant_id": merchant.id,
        "customer_id": customer.id,
        "order_id": "test_ai_4",
        "amount": 100,
        "currency": "USD",
        "payment_method": "card",
        "device_fingerprint": device.device_fingerprint,
        "item_category": "books"
    }
    response = client.post("/api/v1/risk/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ai_analysis"] is None
    del os.environ["TEST_AI_ERROR"]

def test_ai_result_is_persisted_and_audited(setup_database, db_session):
    merchant, customer, device = get_test_data(db_session)
    payload = {
        "merchant_id": merchant.id,
        "customer_id": customer.id,
        "order_id": "test_ai_5",
        "amount": 200,
        "currency": "USD",
        "payment_method": "card",
        "device_fingerprint": device.device_fingerprint,
        "item_category": "books"
    }
    response = client.post("/api/v1/risk/evaluate", json=payload)
    data = response.json()
    assert data["ai_analysis"] is not None
    
    payment = db_session.query(Payment).filter(Payment.order_id == "test_ai_5").first()
    eval_record = payment.risk_evaluation
    assert eval_record.ai_analysis is not None
    assert eval_record.ai_analysis["model_used"] == "mock-provider"
    
    audit = db_session.query(AuditEvent).filter(AuditEvent.payment_id == payment.id).first()
    assert audit.ai_involved is True
    assert audit.ai_model_used == "mock-provider"
    assert audit.ai_model_version == "test-only"
    assert audit.ai_recommendation in ["ALLOW", "REVIEW", "BLOCK"]
