from models import Payment, Customer, Device, RiskSignal, Policy
from schemas import PaymentRiskRequest
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

class RiskSignalEngine:
    @staticmethod
    def extract_features_and_signals(
        request: PaymentRiskRequest,
        customer: Customer,
        historical_payments: List[Payment],
        historical_chargebacks: int,
        device: Device,
        policy_violation_codes: List[str],
        db: Optional[Session] = None
    ) -> Tuple[Dict[str, Any], List[RiskSignal]]:
        
        signals = []
        
        # 1. Calculate features for ML
        now = datetime.utcnow()
        time_window = now - timedelta(hours=24)
        recent_txs = [t for t in historical_payments if t.created_at >= time_window]
        velocity_24h = len(recent_txs)
        
        # attempt_count: number of payment attempts on the same order
        # In production this would track retry attempts for this specific payment.
        # We derive it from historical payments on the same order_id if available.
        attempt_count = 1
        if db is not None and request.order_id:
            order_payment_count = db.query(func.count(Payment.id)).filter(
                Payment.order_id == request.order_id
            ).scalar() or 0
            # Current payment hasn't been committed yet, so add 1
            attempt_count = order_payment_count + 1

        is_new_device = 1 if device.is_new else 0
        account_age_days = customer.account_age_days
        amount = request.amount
        
        # Calculate amount_vs_customer_baseline
        amount_vs_customer_baseline = 1.0
        past_tx_count = len(historical_payments)
        if past_tx_count >= 5:
            avg_past = sum(t.amount for t in historical_payments) / past_tx_count
            if avg_past > 0:
                amount_vs_customer_baseline = amount / avg_past
                
        # device_customer_count: count of distinct customers historically associated
        # with this device fingerprint, matching training logic in generate_synthetic_data
        device_customer_count = 1
        if db is not None:
            distinct_customers = db.query(func.count(func.distinct(Device.customer_id))).filter(
                Device.device_fingerprint == request.device_fingerprint
            ).scalar() or 0
            # If the current customer isn't already in the set, add 1
            current_customer_on_device = db.query(Device.id).filter(
                Device.device_fingerprint == request.device_fingerprint,
                Device.customer_id == customer.id
            ).first()
            if current_customer_on_device:
                device_customer_count = max(1, distinct_customers)
            else:
                device_customer_count = distinct_customers + 1
        
        # failed_attempt_ratio: ratio of failed payments to total payments for this customer,
        # matching training logic: (attempt_count - 1) / attempt_count
        failed_attempt_ratio = (attempt_count - 1) / attempt_count if attempt_count > 0 else 0.0
        
        features = {
            'amount': amount,
            'is_new_device': is_new_device,
            'attempt_count': attempt_count,
            'previous_chargebacks': historical_chargebacks,
            'velocity_24h': velocity_24h,
            'account_age_days': account_age_days,
            'amount_vs_customer_baseline': amount_vs_customer_baseline,
            'device_customer_count': device_customer_count,
            'failed_attempt_ratio': failed_attempt_ratio
        }
        
        # 2. Generate deterministic RiskSignals for explainability
        
        # Amount anomaly
        if historical_payments:
            avg_amount = sum(t.amount for t in historical_payments) / len(historical_payments)
            if avg_amount > 0 and amount > (avg_amount * 3):
                ratio = amount / avg_amount
                signals.append(RiskSignal(
                    signal_type="AMOUNT_ANOMALY",
                    severity="HIGH" if ratio > 5 else "MEDIUM",
                    value=round(ratio, 2),
                    description=f"Transaction is {round(ratio, 2)}x the historical average"
                ))
                
        # Velocity anomaly
        if velocity_24h >= 3:
            signals.append(RiskSignal(
                signal_type="VELOCITY_ANOMALY",
                severity="HIGH" if velocity_24h > 5 else "MEDIUM",
                value=float(velocity_24h),
                description=f"{velocity_24h} transactions in the last 24 hours"
            ))
            
        # Previous chargebacks
        if historical_chargebacks > 0:
            signals.append(RiskSignal(
                signal_type="PREVIOUS_CHARGEBACKS",
                severity="CRITICAL",
                value=float(historical_chargebacks),
                description=f"Customer has {historical_chargebacks} previous chargeback(s)"
            ))
            
        # Device
        if is_new_device:
            signals.append(RiskSignal(
                signal_type="NEW_DEVICE",
                severity="MEDIUM",
                value=1.0,
                description="Payment originating from a new device fingerprint"
            ))

        # Policy violations
        for code in policy_violation_codes:
            signals.append(RiskSignal(
                signal_type="POLICY_VIOLATION",
                severity="CRITICAL",
                value=1.0,
                description=f"Policy violation: {code}"
            ))

        return features, signals

