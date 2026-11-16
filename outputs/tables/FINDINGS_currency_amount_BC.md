# Datathon 2026: findings for Currency, USD amount and Business/Consumer behaviour

Data: `swift_umdac_datathon_2026_fictitious_payment_data.csv` (4.95 GB, 10,000,000 rows, timestamps 2023-04-30 to 2023-07-31 UTC).
Tools: DuckDB 2.0 on the full file. Model fitting on a 20% Bernoulli sample (2.0M rows, seed 42).

**Verdicts (full data, notebook 04):** 8 Confirmed, 2 Strong (R-CCY2, R-BC2), 1 Partial (R-CCY1), 4 Rejected (N1–N4).

**Where things live:** `notebooks/04_integration_validation.ipynb` (integration, QC, validation; run first), `notebooks/01_currency_payment_analysis.ipynb` (analysis and charts), `outputs/figures/` (charts), `outputs/tables/rules_log.csv` (every rule with its test).

## 1. Data integration
- Dropped the `DISCLAIMER` column. It holds 1 non-null value: a notice saying the data was generated with "hard-coded rules, NumPy random calls and the Python Faker library".
- Converted the CSV to `data/processed/payments_clean.parquet` (1.7 GB, zstd, including the shared derived columns). Teammates should load this instead of the CSV, since it is about 10× faster.
- Derived columns: `o_cc` / `b_cc` = BIC letters 5–6 (country); `pair` = ORDERING_TYPE + "2" + BENEFICIARY_TYPE; `anomaly` = ANOMALY_TYPE or NONE; local hour and weekday from the sender country's time zone.
- ⚠️ DuckDB shows timestamps in the laptop's time zone (+08). Always set `SET TimeZone='UTC'` first.

## 2. Quality control (full data)

| Check | Result |
|---|---|
| Missing values | 0 in every column except ANOMALY_TYPE (blank = normal payment) |
| Amount range | 0.01 to 15.66 billion USD. No zero or negative values. Extreme values are FAT_FINGER rows |
| Duration | 2 to 21,649 s. No negatives |
| Codes | Every currency code is 3 letters and every BIC8 is 8 characters. 155 currencies, 228 sender countries |
| CONTINUITY_QFLAG | N ⇔ path contains "..." in **100%** of rows (767,204 rows = 7.7%) |
| Conversions vs hops | CURRENCY_CONVERSION_COUNT ≤ PARTICIPANT_COUNT − 1 in **100%** of rows |
| Direct payments | PARTICIPANT_COUNT = 2 in **100%** of Direct rows |
| Path length | Can exceed PARTICIPANT_COUNT. The "..." placeholder and repeated BICs inflate it (routing teammate to check) |
| Exact duplicate rows | Only 1 pair, so DUPLICATE_PAYMENT rows are **not** exact copies |
| Anomalies | 7,006 rows (0.07%). **CUSTOMER_RECALL (317 rows) is not in the official appendix** |
| Kept, not removed | All outliers and anomalies stay in the data and are only flagged |

## 3. Rules found

| ID | Rule | Evidence | Validation |
|---|---|---|---|
| R-CCY1 | Payment currency = the **sender country's local currency** | 89.4% of all 10M payments are sender-local | Only 4.2% use the receiver's currency instead (18.9% match it when same-currency pairs are included). Verdict: Partial, exceptions not yet explained |
| R-CCY2 | **Direct** payments: 1 conversion if sender and receiver local currencies differ, otherwise 0 | 98.8% / 94.8% match | Overall accuracy 97.8% (6.3M Direct rows) |
| R-CCY3 | Conversions can happen at each hop, so they never exceed hops | Indirect/Covered peak at 2 conversions | 100% of rows satisfy conv ≤ participants − 1 |
| R-AMT1 | Amounts are **log-normal** | ln(amount) residual: skew −0.01, kurtosis 0.02 | Residual σ ≈ 2.08, identical for all 4 pairs |
| R-AMT2 | **Each business party multiplies the amount by e² ≈ 7.4** (sender and receiver, additive in ln, no interaction) | Effect in ln: sender B +1.999, receiver B +2.002 | 95% cluster-bootstrap CI (resampling sender accounts): sender [1.98, 2.02], receiver [1.99, 2.01]. B2B ≈ 7.4² ≈ 55× C2C (observed 52×) |
| R-AMT3 | The **sender country** sets the base amount (rich economies high, poor low) | MC, LI, LU, BM, KY, IE highest. YE, GW, RW, UG, NG lowest. About 900× range | Sender country R² 0.13. Receiver country adds R² 0.0003 (none) |
| R-BC1 | Sender type and receiver type are drawn **independently**: 79% of payments have a business sender and 29% a business receiver | Observed pair shares = product of the marginals | χ² p = 0.67, Cramér's V = 0.0003 |
| R-BC2 | Timestamps follow the **sender's local working day**: 08:00 peak, lunch dip, 17:00–19:00 peak, low at night. Weekends about 4–7% per day | Profile is sharp in local time and blurred in UTC | Same for B and C senders |
| R-BC3 | **Business sender accounts are about 4.5× more active** | 44.8 vs 9.9 payments per account | Receiving accounts are the same for B and C (≈3.8) |
| R-BC4 | Fraud types depend on the sender type | CEO_SCAM only has B senders. ROMANCE_SCAM only has C senders | Full data, 100% |

**Combined amount model:** `ln(USD_AMOUNT) ~ Normal( base[sender country] + 2·[sender is B] + 2·[receiver is B] , 2.08² )`

## 4. Negative results (keep these for the slides)
- **Vowel/consonant currency rule** (the handout's example): no effect. The difference in ln is 0.002.
- **Cross-border vs domestic amount:** the raw median is 5,669 vs 3,529, but the effect falls to ×1.00 after controlling for sender country. The gap is caused by **country mix (confounding)**, not by crossing a border.
- Paying in a non-local currency, transaction type, hour and weekday have no effect on amount (each R² < 0.003).
- Payment timing doesn't differ between B and C senders.

## 5. Possible economic explanations
- R-CCY1: The sender's bank debits in its home currency, and FX is handled downstream (sender-pays model).
- R-CCY2/3: Each correspondent bank in the chain may do an FX conversion, so longer chains mean more conversions.
- R-AMT1: Payment sizes from many multiplying factors are naturally log-normal.
- R-AMT2: Businesses handle invoices and payroll, which are much larger than personal transfers.
- R-AMT3: The base amount tracks national income (GDP per capita). Check this against World Bank data and cite it in APA.
- R-BC2: Payments start in office hours and in end-of-day batches.
- R-BC3: Companies pay many suppliers and staff, so each account sends many payments.

## 6. Limitations and next steps
- Multi-time-zone countries (US, RU, CA, AU, BR) use one zone, which slightly blurs the hour profile.
- The ~5–7% exceptions to R-CCY1/R-CCY2 are not explained yet. Test whether they depend on account, BIC or anomaly.
- Correlate the country base (`outputs/tables/amt3_country_base_amount.csv`) with GDP per capita (external reference).
