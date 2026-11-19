# Changelog

## 19 November 2026, 08:40-09:21: dashboard redesign (13 pages, outputs/dashboard_v5)
- New Power BI project outputs/dashboard_v5/dashboard.pbip (supersedes outputs/dashboard_pbip); exported to
  outputs/dashboard.pdf (13 pages) and outputs/dashboard.pbix. Same tables and numbers; layout only, plus the fixes below.
- Every topic page now opens with 3-4 headline tiles computed from the CSVs; the main finding is the largest chart.
- p.1 Overview: 45-row rule table replaced by 4 tiles (45 / 33 hold / 5 partial / 7 rejected); full table moved to
  Appendix A-B (p.12-13) with the full rule statement, verdict and causal status.
- p.2 Currency: 93.4% first-path-bank chart is the main visual; duplicate currency-choice chart removed.
- p.3 Amount: x7.4 per business party and 73% of USD value from B2B as tiles and top charts.
- p.4 Business vs consumer: x4.5 activity is the largest chart; "INFERRED clock" stays in the R-BC2 title.
- p.5 Routing: short chart titles; q = 0.37 as the first tile. p.6 Duration: R-DUR1 (median by banks on path) is the main chart.
- p.7 FX: 100.0% exact match on 1,848,326 paths and 100.000% on 617,078 holdout rows as tiles; one large chart.
- p.8-9 Anomalies split into signatures and detection performance. p.10-11 Accounts and Party details split.
- Fixes found while checking: Duration tile said "Indirect (one correspondent) 281 s"; 281 s is the median of ALL
  Indirect paths (one correspondent = 87 s). "+150-250 s per extra bank" is now computed (+140-240 s, cells >= 1,000).
  Detection page said duplicates are "flagged precisely"; their precision is at most 17.0% (romance up to 94.4%).

## 19 November 2026, 04:20-08:10: audit fixes (scientific validity, reproducibility, sign-off)
- Clean in-order rerun (04 -> 01 -> 02 -> 03 -> 04, 03:42-04:08): no errors; all 84 output tables rewritten; no stale files.
  Rule values identical to the 03:22 run; only row order, float last digits, approximate SUMMARIZE quantiles,
  the R-BC3 bootstrap CI (x4.55 [4.32, 4.78] vs [4.32, 4.76]) and the R-DUR3 Mann-Whitney p-values changed.
- 02 R-RT5: the per-link gap model is now judged by a chi-square goodness of fit over all path lengths
  (full data p = 0.10; test period, q learned on train, p = 0.43). The old rule ("independence NOT confirmed,
  model misses by up to 1.4 points") ignored that the 1.4-point miss is at 10 banks (n = 2,205, standard error ~1 point).
  Verdict Approximate -> Supported, causal status Association -> Mechanism.
- 02 R-DUR3: the control sample is drawn from a sorted series, so the seeded sample no longer depends on DuckDB row order.
- 03 A1: "100x / 2 orders of magnitude" wording corrected. The 72.0% vs 9.7% uses the ROUNDED log10 distance
  (|k| >= 2, i.e. about 32x or more). Numbers unchanged.
- 03 A2: duplicates come in 185 bursts of 2-5 identical labelled copies (same sender, payee, currency, exact amount),
  median 1,099 s apart. All 494 later copies match an earlier labelled copy; the first copy has an earlier unlabelled
  match in 9.2% of bursts, the same as the chance rate for normal payments (9.2%). New table a_duplicate_bursts.csv.
- 04 R-BC1: computed on all 9,992,994 normal rows (it used the 20% sample while slides said "full data"),
  with an account-clustered test next to the naive chi-square.
- 04 sign-off: an approval is now tied to the value AND the final verdict the reviewer saw (new column verdict_reviewed).
  This run reset R-RT5, A2 and R-BC1: re-review them and set approved = True again.
- 04 note: the unreproducible "~96% match with real time zones" remark was replaced (no external table is evidence).
- New: outputs/audit/verify_rules.py (independent re-test of the 11 principal rules, own code) and its full-data result
  outputs/audit/independent_check_full.csv; audit_rerun.bat. Backups in outputs/audit/backup_0408/.

## 19 November 2026, 03:20: sign-off run
- The 04 error ("No module named 'duckdb'") came from running notebook 04 in a Python environment without duckdb. Use the .bat files (Anaconda) or pick the Anaconda kernel.
- 02: N-DUR1 practical meaning no longer says night/weekend payments are "not slower" (negligible, zero not proven).
- 03: hypothesis table says "test grade" for notebook 03's own grade; 04 adds the final verdict as `final_verdict`.
- 03: D2 result text lists the two sides in a fixed order (the order changed between runs and reset the D2 sign-off).
- 04: within-country demeaning in numpy (pandas groupby transform gave N2 x1.03 in one run and x1.00 in another).
- New: rerun_02_03_04.bat, rerun_04_only.bat. Backup of the sign-off: outputs/tables/principal_rule_signoff_backup_0243.csv.
- Result: all 16 readiness checks True, READY.

## 18 November 2026: merged version (your refined notebooks + earlier output fixes)

Kept from your refined version
- 02 c35/c39: no FX-fee claim; R-RT7 "negligible association, not proof of independence"; N-DUR1 / N-FX1 "negligible", not "zero".
- 03 c35/c66: detector precision/recall labelled in-sample and exploratory; `validation_scope` column.
- 03 c61: AC2 chart counts accounts by (BIC8, account), the same key as AC3.
- 03 c66: A1 no longer claims an exact x10^k multiplier.
- 04 c26: verdict notes say "source-reported holdout". 04 readiness: human sign-off of 11 key rules.
- 01: new amt4 caption.

Restored (lost because the refined copy started from an older version)
- 03: detector CI text as `[0.0301, 0.0602]` (was `(np.float64(0.0301), ...)`).
- 03: empty columns from the old rules template are dropped.
- 04: FINDINGS.md and FINDINGS_currency_amount_BC.md are generated on every run.

Fixed
- 01 and 04: R² by group computed in numpy. pandas groupby().transform('mean') gave receiver-country R² = 1.000 on the laptop.
- 03 A1: verdict follows the test of the rule as worded (size outliers vs control) instead of a hard-coded 'Partial'
  (which turned a well-supported rule into 'Approximate').
- 03 D2: claims only what is tested (numbered and BIC-line formats never occur together; free text is the residual class),
  verdict from that share, plus a practical meaning (the missing practical meaning failed a readiness check).
- 03: hypothesis table status for A1 and D2 explains what was and was not shown.
- 04: sign-off file shows each rule's current value, verdict and evidence files; a sign-off resets if the value changes.
- 04: readiness prints automated checks and human sign-off separately.
- 01 c20: "FX fee" wording removed (fees are not in the data).
- requirements.txt: nbformat, nbconvert, ipykernel added; seaborn removed (not used).
