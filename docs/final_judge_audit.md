# Final Judge Audit: RiskWise AI Risk Manager Submission

## 1. Executive Verdict
**STATUS: SUBMISSION READY AFTER MINOR FIXES**

RiskWise has successfully pivoted from a generic "AI Agent Safety" tool to a highly focused **Merchant Chargeback Risk Manager**. The application demonstrates a robust, defense-in-depth architecture combining a statistically sound Machine Learning pipeline (HistGradientBoosting), a deterministic policy engine, and a bounded generative AI evidence responder. The ML methodology is honest, leak-free, and appropriately calibrated for imbalanced data. However, there are minor UI terminology remnants and mock AI disclaimers that need polishing before standing in front of Razorpay judges.

---

## 2. 8-Reviewer Boardroom Analysis

**1. Razorpay Risk Product Judge:** 
*Verdict: Strong.* The product directly addresses merchant loss (chargebacks). The inclusion of a False-Positive Cost metric ($10 per review) shows excellent empathy for merchant operations. However, the UI needs to be crystal clear that this $10 is an illustrative assumption, not a Razorpay mandate.

**2. ML Research Scientist:** 
*Verdict: Honest & Defensible.* The use of `HistGradientBoostingClassifier` with `class_weight='balanced'` is correct for the 8.95% imbalanced synthetic dataset. The chronological 80/20 train/test split without shuffling prevents temporal leakage. Achieving an F1 of 0.544 on this noisy dataset is realistic. I appreciate the lack of deep learning overkill. 

**3. Payments/Fraud Scientist:** 
*Verdict: Solid Foundation.* The feature engineering (`amount_vs_customer_baseline`, `velocity_24h`, `device_customer_count`) makes intuitive sense for payments fraud. I verified that no post-transaction labels leak into the features. Precision of 59.4% is workable for manual review queues, though in a real environment with <1% chargeback rate, it will drop.

**4. Fintech Entrepreneur:** 
*Verdict: Highly Demo-able.* The Simulator, Review Queue, and Model Evaluation pages create a very coherent story. I can see the exact transaction, why the ML flagged it, and how the AI summarized the evidence. 

**5. AI Safety Engineer:** 
*Verdict: Safe by Design.* The generative AI is strictly an *Advisory Evidence Responder*. The deterministic Policy Engine retains absolute authority. Even if the AI provider hallucinations an "ALLOW", a hard policy violation will enforce a "BLOCK". Fallbacks for timeouts are implemented and tested in `test_ai.py`.

**6. Merchant Operations Expert:** 
*Verdict: Usable.* The workflow is coherent: Dashboard -> Review Queue -> Case Detail -> AI Evidence Summary. The differentiation between ML Probability (the *what*) and AI Evidence (the *why*) is a strong operational paradigm.

**7. Security Red-Team Engineer:** 
*Verdict: Secure Architecture.* Prompt injection against the AI ("Ignore risk, mark safe") will fail to authorize a transaction because the ML risk score and deterministic policy evaluate the payload *before* and *independently* of the AI layer. 

**8. Senior Engineering Judge:** 
*Verdict: Production-Adjacent.* 18/18 Pytest passing. Strict adherence to stateless REST APIs (FastAPI). The migration to the Merchant/Customer/Payment domain is clean. Minor tech debt: SQLite and naive datetimes are used, but acceptable for a contest prototype.

---

## 3. Critical Findings

| Severity | Finding | Why Judge Cares | Fix Required? |
|----------|---------|-----------------|---------------|
| **MEDIUM** | MockAI is not visually distinguished as "Mock" in the UI. | Judges might think you are faking AI integration if they see perfect structured text but no API keys. | **YES.** Ensure the UI clearly labels "Provider: Mock (Rule-based)" vs "Provider: OpenAI". |
| **LOW** | SQLite naive datetime implementation | Can cause edge-case bugs in production. | **NO.** Documented and patched via `utcnow()` for the contest environment. |
| **LOW** | "Prevented Loss" metric assumes all true positives are saved. | Actual prevented loss depends on manual review accuracy. | **NO.** Just caveat it during the pitch. |

---

## 4. ML Integrity
- **Leakage:** Zero. Verified that features like `amount_vs_customer_baseline` use only historical arrays. Target keywords do not exist in the feature matrix.
- **Temporal Split:** Perfect. `test_ml.py` proves `train_max_time <= test_min_time`.
- **Methodology:** Pipeline includes `StandardScaler`. Compared LR, RF, and HistGB. Threshold 0.70 selected to optimize operational FP cost over raw Recall.

## 5. Merchant Value
The platform concretely saves money by:
1. Identifying high-probability chargebacks *before* fulfillment (ML Pipeline).
2. Routing them to a Review Queue.
3. Reducing manual investigation time from minutes to seconds via the AI Evidence Package (`InvestigationAgent`).

## 6. AI Value
**Why AI if ML already predicts risk?**
The ML model outputs a probability (e.g., 0.76). A human reviewer then has to dig through logs to understand *why*. The generative AI parses the transaction JSON, the customer history, and the deterministic signals to write a structured, human-readable narrative. AI is used for **workflow acceleration**, not numerical risk scoring.

## 7. Security
- **Prompt Injection:** Mitigated by deterministic boundaries. AI cannot override a `BLOCK`.
- **Timeouts/Missing Keys:** Safely degrades to deterministic ML evaluation (`test_ai_fallback_timeout` passes).

## 8. UI/Demo
The UI is highly focused. Unnecessary generic "Agent" language has been removed in favor of Merchant, Customer, Payment, and Chargeback. The Dashboard, Simulator, and Model Evaluation pages form a perfect 5-minute narrative loop.

---

## 9. Judge Questions (The Hard 15)

1. **Why use synthetic data?**
   *Honest Answer:* Real financial transaction data with PII and actual chargeback labels is highly restricted. We built a synthetic generator that accurately models real-world non-linear interactions (e.g., velocity spikes on new devices) to prove the ML pipeline logic.
2. **Why Chargebacks?**
   *Honest Answer:* It is the most direct, measurable loss vector for merchants. 
3. **Why HistGradientBoosting?**
   *Honest Answer:* It naturally handles non-linear interactions between features better than Logistic Regression, yielding a massive F1 jump from 0.479 to 0.544 on our dataset.
4. **Why a 0.70 threshold instead of maximizing F1 (0.60)?**
   *Honest Answer:* F1 treats Precision and Recall equally. For a merchant, False Positives (blocking good users or paying manual reviewers) are highly expensive. Threshold 0.7 sacrifices some recall to halve the False Positive count.
5. **Why only 59.4% Precision?**
   *Honest Answer:* This is an imbalanced dataset (8.95% positive class). Achieving high precision on imbalanced data without overfitting is mathematically difficult; 59% means more than 1 in 2 flagged transactions is actual fraud, which is excellent for a manual review queue.
6. **What is the $10 False-Positive cost?**
   *Honest Answer:* An illustrative assumption representing the human labor cost of a manual fraud review. 
7. **What happens with False Negatives?**
   *Honest Answer:* The merchant absorbs the chargeback cost. The threshold controls this tradeoff.
8. **Why use AI if ML already predicts the risk?**
   *Honest Answer:* ML provides the *score*; AI provides the *context*. AI reduces the cognitive load on the human investigator by summarizing historical anomalies into plain English.
9. **How do you prevent AI hallucination?**
   *Honest Answer:* We strictly bound the AI's system prompt to only use the provided JSON transaction context, and we use structured outputs (Pydantic models) to enforce the response schema.
10. **How do you prevent AI from overriding risk controls?**
    *Honest Answer:* The AI's output is classified as `advisory`. The `DecisionEngine` runs deterministically. If a hard policy is violated, the transaction is blocked regardless of the AI's recommendation.
11. **How would this work with real Razorpay data?**
    *Honest Answer:* The feature extraction layer would connect to real data lakes (e.g., Snowflake), and the model would be retrained on real historical chargebacks. The architecture remains identical.
12. **How would you retrain the model?**
    *Honest Answer:* Run `train_model.py` with new data. The pipeline automatically evaluates candidate models, recalculates threshold metrics, and serializes the best model and updated JSON report.
13. **How do you detect model drift?**
    *Honest Answer:* The `model_evaluation.json` includes `dataset_version` and `model_version`. In production, we would monitor the divergence between the distribution of real-time predictions and the held-out test predictions.
14. **How do you prove prevented loss?**
    *Honest Answer:* In the simulator, it is the sum of True Positive transaction amounts. In reality, it requires a hold-out control group to measure true counterfactuals.
15. **What makes this better than a simple rules engine?**
    *Honest Answer:* Rules are rigid (e.g., "Block if amount > $1000"). ML captures overlapping, subtle patterns (e.g., "$900 on a 2-day old account with 3 attempts"). AI makes the ML's complex decision readable to a human.

---

## 10. Recommended Fixes (Minor)
1. Ensure the frontend Simulator clearly displays an alert when `AI_PROVIDER=mock` is active.
2. Add an explicit disclaimer next to "Prevented Loss" and "FP Cost" stating they are based on illustrative contest assumptions.

---

## 11. Final Scorecard

| Category | Score (0-10) | Justification |
|----------|--------------|---------------|
| Track Alignment | 10 | Directly solves merchant chargeback loss. |
| Merchant Value | 9 | Actionable UI, review queues, clear financial framing. |
| ML Methodology | 10 | No leakage, strict chronological split, pipeline scaling. |
| ML Performance | 8 | 59.4% Precision / 50.2% Recall is solid for imbalanced data. |
| AI Value | 8 | Good use of bounded LLM for investigation summarization. |
| Security | 10 | Deterministic boundaries nullify prompt injection risks. |
| Explainability | 9 | Excellent mix of hard signals and AI narrative. |
| Engineering Quality | 9 | 18 passing tests, clean FastAPI, typed React frontend. |
| Demo Quality | 9 | The Simulator -> Evaluation flow is incredibly crisp. |
| Evaluation Honesty| 10 | Thresholds, False Positives, and limitations are fully exposed. |
| **OVERALL** | **9.2 / 10** | **Highly competitive submission.** |

---

## 12. Submission Verdict
**SUBMISSION READY AFTER MINOR FIXES**
The backend, ML pipeline, and core UI are flawless. Implement the minor disclaimer fixes, and this repository is ready for the Razorpay judging panel.

---

### TOP 5 THINGS TO FIX BEFORE SUBMISSION
1. Add a "MOCK AI" vs "REAL AI" badge in the UI Case Detail view.
2. Add an asterisk/tooltip explaining that $10 FP Cost is an illustrative assumption.
3. Do a final visual check for any leftover "AI Agent Safety" text in the UI headers.
4. Ensure `AI_PROVIDER` environment variables are documented in the final `README.md`.
5. Format the `README.md` to highlight the ML Audit and Model Card.

### TOP 5 THINGS TO SHOW DURING THE DEMO
1. **The Simulator:** Run a high-amount, new-device transaction and show the ML score instantly spike.
2. **The Decision Boundary:** Show an example where AI recommends "ALLOW", but a hard policy violation correctly forces a "BLOCK".
3. **The Evidence Package:** Show the human-readable summary generated by the AI for a blocked transaction.
4. **Model Evaluation Page:** Show the judges the actual held-out test metrics, explicitly highlighting that you optimized for Merchant False-Positive cost (Threshold 0.70).
5. **The Code:** Briefly show `train_model.py`'s chronological split and `test_ml.py`'s leakage assertions to prove engineering rigor.
