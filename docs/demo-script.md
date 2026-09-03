# RiskWise Demo Script (5 minutes)

## 0:00–0:30 — Problem Statement
"Chargebacks cost merchants billions annually — and the problem gets worse as AI commerce agents begin making purchases on behalf of users. An agent can't explain itself after a dispute. We need a system that evaluates every payment — whether initiated by a human or an agent — and catches fraud *before* the money is lost. That's what RiskWise does."

## 0:30–1:00 — Security Boundary (Lead with this)
*Navigate to the **Review Queue**, click **Investigate** on a recent case.*
"Before we simulate anything, let me show you the core of the architecture. This is the Security Boundary view. At the top, the ML Chargeback Model gives a probability. Below it, the Deterministic Risk Engine evaluates hard policy rules. The AI Evidence Responder — note the provider badge showing whether it's Mock or Real — provides advisory context only. And at the bottom, the Final Merchant Action, which is always driven by deterministic policy. The AI cannot override a BLOCK."

## 1:00–1:45 — Safe Purchase (ALLOW)
*Navigate to the **Risk Simulator**.*
"Let's see RiskWise in action. We'll run Preset 1: Normal Customer, Low Risk. A $120 purchase on a trusted device from a customer with 180-day account history."
*Click Evaluate Risk.*
"The ML model returns a low chargeback probability, no policy violations fire, and the decision is **ALLOW**."

## 1:45–2:30 — High Value + New Device (REVIEW)
"Now let's increase the risk. Preset 2: $2,500 on a new device in a high-risk category. Same customer."
*Click Evaluate Risk.*
"The ML score spikes. The high-risk category triggers a policy REVIEW. The AI Evidence Responder summarizes exactly why — amount anomaly relative to customer baseline, new device fingerprint."

## 2:30–3:20 — Policy Hard Block
"What about a hard limit? Preset 3: $6,000, which exceeds the merchant's $5,000 max transaction policy."
*Click Evaluate Risk.*
"The Deterministic Policy Engine enforces a **BLOCK**, regardless of what the ML score or AI recommendation says. This is the invariant: policy_result.decision always wins."

## 3:20–4:00 — Model Evaluation
*Navigate to the **Model Evaluation** page.*
"Here we show the held-out test metrics transparently. HistGradientBoosting at threshold 0.70: 59.4% Precision, 50.2% Recall, F1 of 0.544. The False Positive Cost — note the asterisk — is an illustrative $10/review assumption on synthetic data, not a Razorpay figure. We chose threshold 0.70 to halve FP cost versus 0.60, a deliberate merchant-value tradeoff."

## 4:00–4:30 — Policy Configuration
*Navigate to **Policies**.*
"RiskWise gives human operators absolute control. Maximum Transaction Amount, high-risk categories, ML block and review thresholds — all configurable. The system guarantees that if the AI hallucinates and says 'ALLOW', but the transaction exceeds a deterministic limit, RiskWise will enforce a **BLOCK**."

## 4:30–5:00 — Audit Trail + Close
*Navigate to **Audit Trail**.*
"Every decision is immutable. We log the exact policy version, model version, risk score, and whether AI was involved. The same pipeline applies identically whether a human or an AI commerce agent initiated the payment — the risk inputs don't change. RiskWise uses AI to scale merchant security, while keeping humans in control."
