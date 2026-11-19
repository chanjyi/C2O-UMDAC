# UMDAC Datathon 2026: Swift payments (Preliminary Round)

The task is to reverse-engineer the business rules Swift used to generate an artificial set of cross-border payments (10M rows).
Deliverables are a dashboard PDF (5–15 dashboards, one per feature group) and a slide deck PDF (10–20 slides).
**Deadline: Thu 19 Nov 2026, 12:00 PM.**

## Project structure
```
UMDAC/
├── data/
│   ├── raw/          the competition CSV (not committed)
│   └── processed/    payments_clean.parquet (+ derived columns), sample_20pct.parquet, anomalies.parquet, built by notebook 04
├── notebooks/
│   ├── 04_integration_validation.ipynb      RUN FIRST: shared load, QC issues log, rule validation   (Jia Yi)
│   ├── 01_currency_payment_analysis.ipynb   currency, USD amount, business vs consumer             (Jia Yi)
│   ├── 02_member2_analysis.ipynb            routing, duration, FX                                  (Wan Ning)
│   └── 03_anomalies_accounts_details.ipynb  anomalies, accounts, party details and tokens          (Agnes)
├── outputs/
│   ├── figures/      charts for dashboards and slides (PNG, named by rule / hypothesis ID)
│   └── tables/       QC log, summary tables, hypotheses_03.csv, rules_log.csv (combined), evidence_matrix.csv,
│                     FINDINGS.md (generated), submission_readiness.csv, principal_rule_signoff.csv
│       └── rules/    one rules file per notebook (rules_04_core.csv, rules_03_anomalies.csv, rules_02.csv)
├── requirements.txt
└── README.md
```

## How to run
1. Put `swift_umdac_datathon_2026_fictitious_payment_data.csv` in `data/raw/`. It should be the only CSV there.
2. `pip install -r requirements.txt` (Anaconda already has most of these. You may only need `pip install duckdb`.)
3. Double-click `run_notebooks_in_order.bat`. It runs **04 → 01 → 02 → 03 → 04** (about 25 minutes) and writes progress to
   `outputs/tables/_run_status.txt`. Do not open or save the notebooks while it runs (that would overwrite the executed outputs).
   The first 04 builds the data (10–15 minutes the first time); the last 04 combines all rules and checks readiness.
4. Low on memory? Set `SWIFT_MEMORY=4GB` and `SWIFT_THREADS=4` before starting Jupyter.
5. Read `outputs/tables/FINDINGS.md` (generated from the evidence matrix on every run; never edit it by hand).

## Before submitting: human sign-off
- `outputs/tables/submission_readiness.csv` must be all True. The last row is the **human sign-off**.
- Open `outputs/tables/principal_rule_signoff.csv`. For each of the 11 key rules, check `current_value` against the table / figure in
  `evidence_files`, then set `approved` = True and write your name in `reviewer`. Re-run notebook 04 (or the .bat) afterwards.
- A sign-off is tied to the value you saw. If a later run changes that value, the notebook resets `approved` to False and writes a note.

## Shared definitions
- *Country* = bank (BIC) country, from BIC characters 5–6.
- *Local currency* = the currency a country's senders use most, inferred from this dataset.
- Shared derived columns (built once in notebook 04): `rid, ts, o_cc, b_cc, pair, anomaly, cross_border, path_len, path_gap, o_det_cc, b_det_cc, o_det_acct, b_det_acct, b_party_text`.
- If you change a derived column, bump `SCHEMA_VERSION` in the setup cell of **every** notebook. Notebook 04 then rebuilds the data.

## Rules log
- Each notebook writes `outputs/tables/rules/rules_<notebook>.csv`. `combine_rules()` merges them into `outputs/tables/rules_log.csv`.
- Shared columns: `id, group, rule, test, value, verdict, evidence_files, interpretation`.
- One verdict system (notebook 04). *Accuracy* rules (a deterministic prediction) are graded by the share of rows that obey them:
  **Confirmed** ≥99% · **Strong** 95–99% · **Partial** 70–95% · **Weak** <70%. *Effect* rules (a size, an independence, a distribution):
  **Supported** (effect holds and the source notebook reports an agreeing holdout) · **Approximate** · **Rejected** · **Inconclusive**.
- Causal status: **Mechanism** · **Association** · **Structural** · **Rejected** · **Unresolved**. None of these proves the generator's code.
- Detector precision / recall (notebook 03) are in-sample and exploratory, not holdout performance.
- Rule IDs match the chart file names and the slides.

## Team conventions
- Always `SET TimeZone='UTC'` in DuckDB (the shared `connect()` does this).
- Flag anomalies and outliers. **Never delete them.**
- Report effect sizes (ratios, ln-effects with CIs, R², Cramér's V), not just p-values.
- Log rejected hypotheses too. They are worth marks.
- Chart titles state the rule. Footnotes give the data source and any limits.
- External **reference statistics** (e.g. GDP per capita) may be cited in APA to explain a rule (handbook Sec. 3). Never use them as an input dataset.
