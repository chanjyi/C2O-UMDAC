# Changelog

## 19 November 2026, 20:22: three minor dashboard display fixes (no numbers changed)
- p.9 share-of-USD chart: 4 decimals, so tiny shares no longer read as 0.00% (e.g. romance 0.0005%, recall 0.0032%).
- p.11 D1: chart says "of lines" with axis "individual details line (10% row sample)"; the 99.92% tile now says
  "complete details texts ... (full data, lowest side x type)", so the two units are clearly different.
- p.11 D3 widened (top row 560 / 540 / 660 px) so the 9.15% and 9.34% labels show again.
- Exported to outputs/C2O_Dashboard.pdf (the team's file name; replaces the 19:42 copy) and outputs/dashboard.pbix.

## 19 November 2026, 19:45: one direct chart per rule (dashboard; no notebook or rule change)
- Submission asks for charts showing how each rule appears in the data. Five rules had only a number, now each has a chart:
  p.3 R-AMT1 ln-amount residuals vs a normal curve (replaces the B2B value-share chart; the 73% tile stays);
  p.8 A2 bursts by copies per burst (185 bursts of 2-5) and A3 romance vs normal C2C pairs (rising 98.8% vs 50.4%,
  within one day 100% vs 0.1%) (replace the money-share chart, moved to p.9, and the R-DUR3 repeat, still on p.6);
  p.10 AC2 currency code = local currency 99.6% (13.3% of non-IBAN numbers carry a code); p.11 D1 line-length histogram.
- New evidence script outputs/audit/dashboard_evidence.py writes outputs/tables/ev_amt1_residuals.csv, ev_amt1_summary.csv
  and ev_a2_burst_sizes.csv with the notebooks' definitions; it reproduces skew -0.016, kurtosis 0.024, sd 2.08 and
  185 bursts / 679 copies exactly. The other three charts use existing notebook tables.
- New project folder outputs/dashboard_v6 (supersedes dashboard_v5). Refreshed, saved, exported to outputs/dashboard.pdf
  (13 pages) and outputs/dashboard.pbix. Also: D2 legend "Neither format (residual)"; appendix subtitle reworded.

## 19 November 2026, 18:45: review round 6 (wording and one worked example; no numbers changed)
- Dashboard pp.12-13: appendix subtitle now points to the topic pages (every one of the 45 rule IDs appears with its result on
  pp.2-11) instead of only to FINDINGS.md / evidence_matrix.csv, so the PDF can be judged on its own. Refreshed before export.
- Slide 5 (Method): worked example of a control removing a false pattern (cross-border x0.62 raw -> x1.00 within the same
  sender country, rejected).
- Slide 14: card is "Monitoring relevance (in-sample only)", text starts "Exploratory, on artificial labels".
- Slides 15-16: one data-based relevance line each (IBAN/BIC always agree, so a mismatch is a data-quality check; only 20-21%
  of party texts follow a parseable layout).
- Checked, not changed: slide 19 references (~10.5 pt at A4) and dashboard appendix text (~11 pt at 100% zoom) are readable;
  a larger appendix font would risk scrollbars that cut rows in the PDF.

## 19 November 2026, 18:21: slide 7 rejection test (new audit check; no notebook or dashboard change)
- The 4.2% "Receiver local" class is exclusive (receiver's currency but not the sender's), so alone it cannot reject
  "priced in the receiver's currency". New check outputs/audit/receiver_currency_check.py (20% sample, same local-currency
  definition as notebook 01): sender and receiver local currencies coincide in 15.5% of payments; where they differ (84.5%),
  5.0% use the receiver's currency vs 88.5% the sender's and 92.7% the first bank's. Including the 15.5% overlap, 18.9%
  match the receiver's currency. Slide 7 "Rejected alternative" now uses the 84.5% comparison.

## 19 November 2026, 18:06: fix of a dashboard regression from the 17:40 export
- Cause: the 17:37 PDF was exported from outputs/dashboard_v5 without Refresh, so Power BI used its cached data from 09:02.
  Rule texts read from outputs/tables (evidence_matrix.csv, a_detector_performance.csv) fell back to the old wording:
  R-BC1 "all 10M rows", R-RT5 "independently", R-DUR1 "set by routing", CEO detector "(payment held)", A2 "unlabelled original".
- Fix: refreshed the project from outputs/tables, saved it (cache now current), re-exported outputs/dashboard.pdf and
  outputs/dashboard.pbix. The PDF now equals the 15:39 version plus the intended round-3 edits only.
- Also: p.1 tile "33 hold" -> "33 confirmed, strong or supported findings (12 · 3 · 18)"; p.2 R-CCY1 and slide 7 now define
  4.2% as "receiver's local currency but not the sender's" (the exclusive category in ccy1_currency_choice.csv).
- Rule for future exports: always press Refresh in Power BI before exporting the PDF.

## 19 November 2026, 17:40: third review round (wording and business relevance; every value, verdict and statistic unchanged)
- Dashboard p.4: R-BC4 tile "0 / 0" (looked like a ratio) -> "0" with "R-BC4 exceptions: CEO scams from consumers, romance
  from businesses". p.5: "5% per link" -> "~5% per link", labelled as a fitted model. Re-exported outputs/dashboard.pdf
  (13 pages) and outputs/dashboard.pbix from outputs/dashboard_v5.
- Slides: cover says domestic AND cross-border payments; answer slide scopes 100% to 1.85M sampled complete paths; data prep
  says no payment ROWS were deleted (DISCLAIMER column dropped); currency chart labels are marked as separate, overlapping
  measures; B2B 73% is "among normal payments" and "payroll" removed; end-of-day batching and "correspondents book funds"
  are no longer stated as observed; 79-80% party texts "match neither format" (residual); generator gap rate is a fitted model.
- Business relevance added without outcome claims: amount (segment-specific baselines), routing (route complexity),
  duration (time expectations, R2 only 0.046), FX (full path 97.8% -> 100%; Swift 2025b on payment investigations),
  anomalies (in-sample alert volume vs precision), generator summary line. No external statistics enter any calculation.
- References: added Swift (2025b) It's time to transform exceptions and investigations; IBAN registry is now Swift (2025a).

## 19 November 2026, 15:30: second review round (wording only; every value, verdict and statistic unchanged)
- Rule texts corrected in the notebooks and regenerated (rerun 02, 03, 04 at 15:04-15:23; evidence_matrix values identical):
  R-BC1 "all 10M rows" -> "all 9,992,994 normal payments" (04); R-RT5 now says the gap frequencies are CONSISTENT WITH an
  independent 5%-per-link model (02); R-DUR1 "duration is set by routing / every bank adds time" -> "median duration rises with
  routing type and every extra bank" (02); A2 "no unlabelled original" -> "no excess beyond chance" (03); detector label
  "(payment held)" removed (03).
- Dashboard: p.2 currency exceptions (paths starting elsewhere explain part; 6.6% unexplained), p.6 title and R-DUR1 line,
  p.8 "Money at risk" -> "Share of payments vs share of USD value, by anomaly type", A2 wording.
- Slides 11, 12, 14: "opposite of real practice" softened; duration no longer causal; "fraud type" -> "anomaly type";
  duplicate wording; speaker note on controls.
- rerun_04_only.bat and rerun_02_03_04.bat now force the Anaconda "python3" kernel (an editor had saved kernel
  "cds6314", which has no duckdb, into notebook 04, so the rerun failed with "No module named duckdb").

## 19 November 2026, 14:10: review fixes (wording and layout; no numbers changed)
- Dashboard p.1: rules are tested on the full data OR a 20% sample; 28 of 45 have a time-split holdout (it said every rule had one).
- p.3: amounts are "approximately" log-normal; B2B 73% is labelled as normal payments (20% sample, anomalies excluded);
  bottom charts made taller so all 10 factors and all 14 countries show (they had scrollbars in the PDF).
- p.4 / p.5 titles no longer claim independence (association negligible; mechanism not proven).
- p.8: CUSTOMER_RECALL = 314 of 317 with no matching earlier payment (3 do match); romance 98.8% vs 50.4% rising shown.
- p.10: AC1 adds IBAN characters 5-8 = BIC characters 1-4 (100% in all 76 IBAN countries).
- p.11: filler line = no meaningful difference detected (gaps <= 3.3 points), not "no signal".
- Slides: same corrections (cover, method p-value note, data-prep missing values, B/C and gap independence wording,
  duration "negligible, not proven zero", screening as a possible reading, A5 marked Inconclusive on "What did not hold").

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
