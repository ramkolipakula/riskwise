import pytest
import os
from fastapi.testclient import TestClient
from main import app
from database import Base, engine, get_db, SessionLocal
from seed import seed_data
from models import Merchant, Customer, Device, Payment, RiskEvaluation, AuditEvent

os.environ["AI_PROVIDER"] = "mock"

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    # Setup test DB
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

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200

def test_scenario_1_normal_payment(setup_database, db_session):
    merchant, customer, device = get_test_data(db_session)
    payload = {
        "merchant_id": merchant.id,
        "customer_id": customer.id,
        "order_id": "test_order_1",
        "amount": 100,
        "currency": "USD",
        "payment_method": "card",
        "device_fingerprint": device.device_fingerprint,
        "item_category": "books"
    }
    response = client.post("/api/v1/risk/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "ALLOW"
    
    # Check persistence
    payment = db_session.query(Payment).filter(Payment.order_id == "test_order_1").first()
    assert payment is not None
    assert payment.risk_evaluation is not None
    assert payment.risk_evaluation.decision == "ALLOW"
    assert db_session.query(AuditEvent).filter(AuditEvent.payment_id == payment.id).count() == 1

def test_scenario_2_ml_probability_review(setup_database, db_session):
    # Simulate high amount + new device which spikes ML probability in our mocked predictor (or actual predictor)
    merchant, customer, _ = get_test_data(db_session)
    payload = {
        "merchant_id": merchant.id,
        "customer_id": customer.id,
        "order_id": "test_order_2",
        "amount": 4000, 
        "currency": "USD",
        "payment_method": "card",
        "device_fingerprint": "new_device_fp", # New device
        "item_category": "books"
    }
    response = client.post("/api/v1/risk/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # ML prob > 0.4 triggers review based on policy in seed.py
    # With Amount > 1000 and new device, prob is high.
    # It might hit block_threshold (0.7) or review_threshold (0.4) depending on the exact ML logic, but definitely not ALLOW.
    assert data["decision"] in ["REVIEW", "BLOCK"]

def test_scenario_3_policy_hard_block(setup_database, db_session):
    merchant, customer, device = get_test_data(db_session)
    # Exceed max amount (5000 in seed.py policy)
    payload = {
        "merchant_id": merchant.id,
        "customer_id": customer.id,
        "order_id": "test_order_3",
        "amount": 6000,
        "currency": "USD",
        "payment_method": "card",
        "device_fingerprint": device.device_fingerprint,
        "item_category": "books"
    }
    response = client.post("/api/v1/risk/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    assert "AMOUNT_EXCEEDS_POLICY_LIMIT" in data["reason_codes"]

def test_scenario_4_high_risk_category(setup_database, db_session):
    merchant, customer, device = get_test_data(db_session)
    # category "digital_goods" is in high_risk_categories (seed.py policy)
    payload = {
        "merchant_id": merchant.id,
        "customer_id": customer.id,
        "order_id": "test_order_4",
        "amount": 50,
        "currency": "USD",
        "payment_method": "card",
        "device_fingerprint": device.device_fingerprint,
        "item_category": "digital_goods"
    }
    response = client.post("/api/v1/risk/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] in ["REVIEW", "BLOCK"]
    assert "HIGH_RISK_MERCHANT_CATEGORY" in data["reason_codes"]

def test_deterministic_authority(setup_database, db_session):
    # ML ALLOW + hard policy violation = FINAL BLOCK
    # We can force AI ALLOW by setting env var for mock, but Policy is deterministic.
    os.environ["TEST_AI_FORCE_ALLOW"] = "1"
    merchant, customer, device = get_test_data(db_session)
    payload = {
        "merchant_id": merchant.id,
        "customer_id": customer.id,
        "order_id": "test_order_5",
        "amount": 9000, # Block policy > 5000
        "currency": "USD",
        "payment_method": "card",
        "device_fingerprint": device.device_fingerprint,
        "item_category": "books"
    }
    response = client.post("/api/v1/risk/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Even if AI recommends ALLOW (which it does via mock), the Policy overrides it.
    assert data["decision"] == "BLOCK"
    assert data["ai_analysis"]["recommended_action"] == "ALLOW"
    assert "AMOUNT_EXCEEDS_POLICY_LIMIT" in data["reason_codes"]
    del os.environ["TEST_AI_FORCE_ALLOW"]
