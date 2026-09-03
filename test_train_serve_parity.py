"""
Test train/serve feature parity.

Constructs a synthetic transaction through both the training-time feature
construction logic (generate_synthetic_data) and the live
RiskSignalEngine.extract_features_and_signals, then asserts the two feature
dicts match on every key.

This test exists as a permanent regression guard against train/serve feature skew.
"""
import pytest
import os
import numpy as np
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

os.environ["AI_PROVIDER"] = "mock"

from train_model import generate_synthetic_data
from risk_signal_engine import RiskSignalEngine
from models import Payment, Customer, Device
from schemas import PaymentRiskRequest


def _build_mock_db_session(order_payment_count: int, device_customer_ids: list, current_customer_id: str, device_fingerprint: str):
    """Build a mock db session that returns controlled query results matching synthetic data."""
    db = MagicMock()
    
    # Mock for attempt_count query: func.count(Payment.id).filter(order_id=...)
    # Returns the number of prior payments on this order
    mock_attempt_query = MagicMock()
    mock_attempt_filter = MagicMock()
    mock_attempt_filter.scalar.return_value = order_payment_count
    mock_attempt_query.filter.return_value = mock_attempt_filter
    
    # Mock for device_customer_count: func.count(func.distinct(Device.customer_id)).filter(fingerprint=...)
    mock_device_count_query = MagicMock()
    mock_device_count_filter = MagicMock()
    mock_device_count_filter.scalar.return_value = len(set(device_customer_ids))
    mock_device_count_query.filter.return_value = mock_device_count_filter
    
    # Mock for current_customer_on_device check
    mock_device_check_query = MagicMock()
    mock_device_check_filter = MagicMock()
    if current_customer_id in device_customer_ids:
        mock_device_check_filter.first.return_value = MagicMock()  # Non-None = found
    else:
        mock_device_check_filter.first.return_value = None
    mock_device_check_query.filter.return_value = mock_device_check_filter
    
    # Chain calls: db.query(...).filter(...).scalar() or .first()
    call_count = [0]
    def query_side_effect(*args):
        call_count[0] += 1
        if call_count[0] == 1:
            return mock_attempt_query
        elif call_count[0] == 2:
            return mock_device_count_query
        elif call_count[0] == 3:
            return mock_device_check_query
        return MagicMock()
    
    db.query.side_effect = query_side_effect
    return db


def test_train_serve_feature_parity():
    """
    Take one synthetic transaction from the training data generator,
    reconstruct the same scenario for the live RiskSignalEngine, and
    assert all 9 feature values match.
    """
    # Generate synthetic data and pick a specific row
    np.random.seed(42)
    df = generate_synthetic_data(100)  # Small sample for speed
    
    # Pick a row that has non-trivial values (not all defaults)
    # Choose a row with attempt_count > 1 for a meaningful test
    test_row = None
    for _, row in df.iterrows():
        if row['attempt_count'] > 1 and row['device_customer_count'] > 1:
            test_row = row
            break
    
    if test_row is None:
        # Fallback: use any row
        test_row = df.iloc[50]
    
    # Build corresponding inputs for RiskSignalEngine
    request = PaymentRiskRequest(
        merchant_id="test-merchant",
        customer_id="test-customer",
        order_id="test-order",
        amount=test_row['amount'],
        currency="USD",
        payment_method="card",
        device_fingerprint="test-device-fp",
        item_category="electronics"
    )
    
    customer = MagicMock(spec=Customer)
    customer.account_age_days = int(test_row['account_age_days'])
    
    device = MagicMock(spec=Device)
    device.is_new = bool(test_row['is_new_device'])
    
    # Build historical payments to match amount_vs_customer_baseline
    historical_payments = []
    if test_row['amount_vs_customer_baseline'] != 1.0:
        # If baseline != 1.0, there were >= 5 prior transactions
        # avg_past = amount / baseline
        avg_past = test_row['amount'] / test_row['amount_vs_customer_baseline']
        for i in range(5):
            mock_payment = MagicMock(spec=Payment)
            mock_payment.amount = avg_past
            mock_payment.created_at = datetime.utcnow() - timedelta(days=30)
            mock_payment.status = "COMPLETED"
            historical_payments.append(mock_payment)
    
    # Add recent payments for velocity_24h
    for i in range(int(test_row['velocity_24h'])):
        mock_payment = MagicMock(spec=Payment)
        mock_payment.amount = 100.0  # doesn't affect baseline since we set it above
        mock_payment.created_at = datetime.utcnow() - timedelta(hours=1)
        mock_payment.status = "COMPLETED"
        historical_payments.append(mock_payment)
    
    historical_chargebacks = int(test_row['previous_chargebacks'])
    
    # Build mock db session
    # attempt_count in training: raw value. In serve: order_payment_count + 1
    # So order_payment_count = attempt_count - 1
    attempt_count = int(test_row['attempt_count'])
    
    # device_customer_count in training includes current customer
    device_customer_count = int(test_row['device_customer_count'])
    # Simulate that the current customer is already in the device set
    device_customer_ids = [f"cust_{i}" for i in range(device_customer_count)]
    device_customer_ids[0] = "test-customer"  # current customer is in the set
    
    db = _build_mock_db_session(
        order_payment_count=attempt_count - 1,
        device_customer_ids=device_customer_ids,
        current_customer_id="test-customer",
        device_fingerprint="test-device-fp"
    )
    
    # Run the live feature extraction
    features, _ = RiskSignalEngine.extract_features_and_signals(
        request=request,
        customer=customer,
        historical_payments=historical_payments,
        historical_chargebacks=historical_chargebacks,
        device=device,
        policy_violation_codes=[],
        db=db
    )
    
    # Assert parity on all 9 features
    training_features = {
        'amount': test_row['amount'],
        'is_new_device': int(test_row['is_new_device']),
        'attempt_count': int(test_row['attempt_count']),
        'previous_chargebacks': int(test_row['previous_chargebacks']),
        'velocity_24h': int(test_row['velocity_24h']),
        'account_age_days': int(test_row['account_age_days']),
        'amount_vs_customer_baseline': test_row['amount_vs_customer_baseline'],
        'device_customer_count': int(test_row['device_customer_count']),
        'failed_attempt_ratio': test_row['failed_attempt_ratio']
    }
    
    # Verify all keys match
    assert set(features.keys()) == set(training_features.keys()), \
        f"Feature key mismatch: serve={set(features.keys())}, train={set(training_features.keys())}"
    
    for key in training_features:
        serve_val = features[key]
        train_val = training_features[key]
        
        if isinstance(train_val, float):
            assert abs(serve_val - train_val) < 0.01, \
                f"Feature '{key}' skew: serve={serve_val}, train={train_val}"
        else:
            assert serve_val == train_val, \
                f"Feature '{key}' skew: serve={serve_val}, train={train_val}"


def test_feature_keys_match_training():
    """Verify that the feature keys from RiskSignalEngine match exactly
    the feature list used in train_model.py."""
    # Build minimal inputs
    request = PaymentRiskRequest(
        merchant_id="m", customer_id="c", order_id="o",
        amount=100, currency="USD", payment_method="card",
        device_fingerprint="fp", item_category="books"
    )
    customer = MagicMock(spec=Customer)
    customer.account_age_days = 30
    device = MagicMock(spec=Device)
    device.is_new = False
    
    features, _ = RiskSignalEngine.extract_features_and_signals(
        request=request, customer=customer,
        historical_payments=[], historical_chargebacks=0,
        device=device, policy_violation_codes=[]
    )
    
    expected_keys = {
        'amount', 'is_new_device', 'attempt_count', 'previous_chargebacks',
        'velocity_24h', 'account_age_days', 'amount_vs_customer_baseline',
        'device_customer_count', 'failed_attempt_ratio'
    }
    
    assert set(features.keys()) == expected_keys, \
        f"Feature key mismatch: got {set(features.keys())}, expected {expected_keys}"


def test_failed_attempt_ratio_formula():
    """Verify failed_attempt_ratio = (attempt_count - 1) / attempt_count,
    matching the training data generation logic."""
    for attempt_count in [1, 2, 3, 4]:
        expected_ratio = (attempt_count - 1) / attempt_count
        
        request = PaymentRiskRequest(
            merchant_id="m", customer_id="c", order_id="o",
            amount=100, currency="USD", payment_method="card",
            device_fingerprint="fp", item_category="books"
        )
        customer = MagicMock(spec=Customer)
        customer.account_age_days = 30
        device = MagicMock(spec=Device)
        device.is_new = False
        
        # Mock db to return attempt_count - 1 prior payments on this order
        db = _build_mock_db_session(
            order_payment_count=attempt_count - 1,
            device_customer_ids=["c"],
            current_customer_id="c",
            device_fingerprint="fp"
        )
        
        features, _ = RiskSignalEngine.extract_features_and_signals(
            request=request, customer=customer,
            historical_payments=[], historical_chargebacks=0,
            device=device, policy_violation_codes=[], db=db
        )
        
        assert abs(features['failed_attempt_ratio'] - expected_ratio) < 0.001, \
            f"attempt_count={attempt_count}: expected ratio={expected_ratio}, got={features['failed_attempt_ratio']}"
        assert features['attempt_count'] == attempt_count
