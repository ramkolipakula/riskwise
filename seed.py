"""Curated synthetic demo dataset for RiskWise Chargeback Manager.
Creates baselines and seeds DB for the ML prediction flow.
"""
import uuid
import random
from database import SessionLocal, Base, engine
from models import Merchant, Customer, Device, Order, Payment, Chargeback, Refund, Policy, RiskSignal, RiskEvaluation, AuditEvent
from datetime import datetime, timedelta, timezone

def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Clear ALL tables for repeatability
        db.query(AuditEvent).delete()
        db.query(RiskSignal).delete()
        db.query(RiskEvaluation).delete()
        db.query(Chargeback).delete()
        db.query(Refund).delete()
        db.query(Payment).delete()
        db.query(Order).delete()
        db.query(Device).delete()
        db.query(Policy).delete()
        db.query(Customer).delete()
        db.query(Merchant).delete()
        db.commit()

        # --- Core entities ---
        merchant_id = str(uuid.uuid4())
        merchant = Merchant(id=merchant_id, name="Acme Electronics Demo")
        db.add(merchant)

        policy = Policy(
            merchant_id=merchant_id,
            max_transaction_amount=5000.0,
            high_risk_categories=["digital_goods", "electronics_high_value"],
            block_threshold=0.70,
            review_threshold=0.40,
            version=1
        )
        db.add(policy)

        # 1. Normal Customer (Good history)
        cust_normal_id = str(uuid.uuid4())
        cust_normal = Customer(id=cust_normal_id, merchant_id=merchant_id, name="Alice Good", email="alice@example.com", account_age_days=180)
        db.add(cust_normal)
        
        dev_normal = Device(customer_id=cust_normal_id, device_fingerprint="fp_alice_trusted", ip_address="192.168.1.10", is_new=False)
        db.add(dev_normal)

        # 2. Fraudulent Customer (Chargeback history)
        cust_fraud_id = str(uuid.uuid4())
        cust_fraud = Customer(id=cust_fraud_id, merchant_id=merchant_id, name="Bob Fraud", email="bob@example.com", account_age_days=5)
        db.add(cust_fraud)

        dev_fraud = Device(customer_id=cust_fraud_id, device_fingerprint="fp_bob_new", ip_address="10.0.0.50", is_new=True)
        db.add(dev_fraud)
        
        db.commit()

        # --- Historical baseline payments ---
        base_time = datetime.now(timezone.utc) - timedelta(days=30)
        
        # Alice has 5 good payments
        for i in range(5):
            o = Order(merchant_id=merchant_id, customer_id=cust_normal_id, amount=100.0 + (i * 10), currency="USD", item_category="accessories", status="COMPLETED")
            db.add(o)
            db.flush()
            p = Payment(merchant_id=merchant_id, customer_id=cust_normal_id, order_id=o.id, device_id=dev_normal.id, amount=o.amount, payment_method="card_6789", status="COMPLETED", created_at=base_time + timedelta(days=i*5))
            db.add(p)
            
        # Bob has 2 payments, both charged back
        for i in range(2):
            o = Order(merchant_id=merchant_id, customer_id=cust_fraud_id, amount=800.0, currency="USD", item_category="electronics_high_value", status="COMPLETED")
            db.add(o)
            db.flush()
            p = Payment(merchant_id=merchant_id, customer_id=cust_fraud_id, order_id=o.id, device_id=dev_fraud.id, amount=o.amount, payment_method="card_1234", status="COMPLETED", created_at=base_time + timedelta(days=i*2))
            db.add(p)
            db.flush()
            cb = Chargeback(merchant_id=merchant_id, customer_id=cust_fraud_id, payment_id=p.id, amount=o.amount, reason_code="fraudulent", status="OPEN", created_at=base_time + timedelta(days=i*2 + 1))
            db.add(cb)

        db.commit()

        print(f"Seed data created.")
        print(f"MERCHANT_ID:      {merchant_id}")
        print(f"CUST_NORMAL_ID:   {cust_normal_id}")
        print(f"CUST_FRAUD_ID:    {cust_fraud_id}")
        print()
        print("Database seeded with historical baselines (Chargebacks and Good Payments).")
        print("Use the Simulator to test ML chargeback prediction.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
