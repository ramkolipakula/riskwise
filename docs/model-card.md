# Model Card: Chargeback Risk Predictor

## Problem Statement
Merchants suffer from financial loss due to chargebacks. The goal of this model is to estimate the probability that a given payment will result in a chargeback, allowing the deterministic Policy Engine to flag high-risk transactions for manual review or block them entirely.

## Target Variable
`is_chargeback` (binary). 1 indicates a chargeback occurred, 0 indicates a good payment.

## Dataset Description
- **Source**: Synthetic dataset generated using `np.random` with domain-specific conditional probabilities and non-linear interactions.
- **Size**: 10,000 transactions.
- **Chargeback Prevalence**: ~8.95% (Imbalanced).

### Features
1. `amount` (float): The transaction amount in USD.
2. `is_new_device` (int): 1 if the device fingerprint is new, 0 otherwise.
3. `attempt_count` (int): Number of attempts made to process this payment.
4. `previous_chargebacks` (int): Historical count of chargebacks from this customer.
5. `velocity_24h` (int): Number of transactions by this customer in the past 24 hours.
6. `account_age_days` (int): Age of the customer account in days.
7. `amount_vs_customer_baseline` (float): Ratio of the current amount to the customer's historical average amount.
8. `device_customer_count` (int): Number of unique customers seen using this device.
9. `failed_attempt_ratio` (float): Ratio of failed attempts prior to this successful one.

### Temporal Split
The dataset is chronologically sorted by timestamp. The first 8,000 rows (earlier 80%) form the Training Set, while the final 2,000 rows (later 20%) form the Held-Out Test Set. This strictly prevents temporal leakage (e.g., predicting the past using the future).

## Evaluation Methodology

### Candidate Models
1. **Logistic Regression** (Baseline) - Pipeline with StandardScaler and balanced class weights.
2. **Random Forest Classifier** - Pipeline with StandardScaler, 100 estimators, max depth 10, balanced class weights.
3. **HistGradientBoosting Classifier** (Final Model) - Pipeline with StandardScaler and balanced class weights.

### Final Model
**HistGradientBoostingClassifier** was selected as it achieved the highest F1 score overall while maintaining a reasonable precision-recall balance.

### Selected Threshold
**Threshold: 0.70**
A higher threshold was selected to prioritize operational efficiency (reducing False Positives). A merchant spends an estimated $10 per manual review, so a lower threshold would result in excessive operational overhead.

### Final Held-Out Metrics
- **F1 Score**: 0.544
- **Precision**: 59.4%
- **Recall**: 50.2%
- **False Positives**: 78
- **False Negatives**: 113
- **False-Positive Cost**: $780.00 (Assuming $10/review)

## Limitations and Known Risks
1. **Synthetic Data Limitations**: The model was trained on synthetic data. Real-world fraud patterns evolve rapidly and contain significantly more noise, latent variables, and adversarial behavior not captured here.
2. **Calibration**: The output score is a "risk probability", but it is not perfectly calibrated to absolute real-world probability. It should be treated as a relative risk score.
3. **Imbalance**: The 8.95% prevalence is higher than most real-world chargeback rates (typically <1%). Precision in production may be significantly lower if prevalence drops.
4. **Leakage Safety**: While target leakage (using future information) was removed, in a production system, features like `device_customer_count` must be strictly computed using only data available *at the exact millisecond* of the transaction.

## Versioning
- **Model Version**: chargeback-histgradientboosting-v2
- **Dataset Version**: dataset-v2
- **Training Timestamp**: Dynamically recorded in `model_evaluation.json`.
