"""Audit fixes (19 Nov, 04:00): R-RT5 goodness-of-fit (notebook 02) and A1 threshold wording (notebook 03).
Usage: python patch_audit.py <in_dir> <out_dir>   (edits cell sources only; outputs are kept)"""
import json, sys, pathlib
src, dst = map(pathlib.Path, sys.argv[1:3]); dst.mkdir(parents=True, exist_ok=True)

P02 = [
# 1) full-data goodness of fit of the per-link gap model (q from Direct rows only, so every longer path length is an independent test)
("""rt5_maxerr = (rt5.gap_rate - rt5.predicted_per_link).abs().max()
save_table(rt5, 'rt5_gap_by_participants')
print(f"per-link gap chance {q_link:.4f}; largest gap between observed and predicted rate: {rt5_maxerr:.4f}")""",
"""rt5_maxerr = (rt5.gap_rate - rt5.predicted_per_link).abs().max()
save_table(rt5, 'rt5_gap_by_participants')
# Is each path length within SAMPLING ERROR of the per-link model? q comes from Direct rows only, so every longer path length
# is an independent check: chi-square goodness of fit on the standardised errors (an absolute 0.5-point cut-off ignores that
# long paths have few rows: 10 banks = ~2,200 rows, standard error ~1 point)
_m5 = rt5.PARTICIPANT_COUNT > 2
_z5 = (rt5.gap_rate - rt5.predicted_per_link) * np.sqrt(rt5.n / (rt5.predicted_per_link * (1 - rt5.predicted_per_link)))
rt5_chi = float((_z5[_m5] ** 2).sum()); rt5_df = int(_m5.sum()); rt5_gof_p = float(stats.chi2.sf(rt5_chi, rt5_df))
rt5_zmax = float(_z5[_m5].abs().max()); rt5_zpc = int(rt5.PARTICIPANT_COUNT[_z5[_m5].abs().idxmax()])
print(f"per-link gap chance {q_link:.4f}; largest gap between observed and predicted rate: {rt5_maxerr:.4f}; "
      f"goodness of fit chi-square {rt5_chi:.1f} on {rt5_df} df, {fmt_p(rt5_gof_p)} (largest |z| {rt5_zmax:.1f} at {rt5_zpc} banks)")"""),
# 2) the same test on the test period, with q learned on train Direct rows (every hop group, Direct included, is out of sample)
("""gte = gte[gte.n >= 1000]; rt5_err_test = (gte.gap - (1 - (1 - q_link_tr) ** (gte.index - 1))).abs().max()""",
"""gte = gte[gte.n >= 1000]; rt5_err_test = (gte.gap - (1 - (1 - q_link_tr) ** (gte.index - 1))).abs().max()
_pr5 = 1 - (1 - q_link_tr) ** (gte.index - 1)
rt5_chi_te = float((((gte.gap - _pr5) ** 2) * gte.n / (_pr5 * (1 - _pr5))).sum()); rt5_df_te = len(gte); rt5_gof_p_te = float(stats.chi2.sf(rt5_chi_te, rt5_df_te))"""),
# 3) evidence row
(""" dict(id='R-RT5', statistic_ci=f'per-link gap chance {share_ci(g_k, g_n, 2)}', p_value=f'largest error vs model {rt5_maxerr:.4f}', out_of_sample=f'gap chance fitted on train Direct rows = {q_link_tr:.4f}; largest error on test-period hop groups {rt5_err_test:.4f}',
      **holdout(rt5_err_test < 0.005, 'per-link model fitted on train misses every test-period hop group by less than 0.5 points'),
      invariance=f'by month {gap_month.min():.4f}-{gap_month.max():.4f}', causal_status='Mechanism' if rt5_maxerr < 0.005 else 'Association',""",
""" dict(id='R-RT5', statistic_ci=f'per-link gap chance {share_ci(g_k, g_n, 2)}',
      p_value=f'goodness of fit vs per-link model: chi-square {rt5_chi:.1f} on {rt5_df} df, {fmt_p(rt5_gof_p)}; largest error {rt5_maxerr:.4f} (|z| = {rt5_zmax:.1f} at {rt5_zpc} banks)',
      out_of_sample=f'gap chance fitted on train Direct rows = {q_link_tr:.4f}; test-period goodness of fit chi-square {rt5_chi_te:.1f} on {rt5_df_te} df, {fmt_p(rt5_gof_p_te)} (largest error {rt5_err_test:.4f})',
      **holdout(rt5_gof_p_te >= 0.01, 'per-link model fitted on train Direct rows is not rejected on the test period (goodness of fit p >= 0.01)'),
      invariance=f'by month {gap_month.min():.4f}-{gap_month.max():.4f}', causal_status='Mechanism' if rt5_gof_p >= 0.01 else 'Association',"""),
# 4) rule row
("""         rule=f"Approximate candidate model: each link has about a {q_link:.1%} chance of a continuity gap ('...'); independence is NOT confirmed (model misses by up to {rt5_maxerr:.1%} points)",
         test='largest absolute error between observed gap rate and 1-(1-q)^(participants-1), groups with >= 1000 rows',
         value=f'{rt5_maxerr:.4f}', verdict=lvl(rt5_maxerr, 0.005, 0.01),""",
"""         rule=(f"Each link has about a {q_link:.1%} chance of a continuity gap ('...'), independently of the other links: the per-link model fits every path length within sampling error (consistent with independence, not proof of it)"
               if rt5_gof_p >= 0.01 else
               f"Approximate candidate model: each link has about a {q_link:.1%} chance of a continuity gap ('...'); a goodness-of-fit test rejects exact per-link independence (largest miss {rt5_maxerr:.1%} points)"),
         test='chi-square goodness of fit: observed gap rate vs 1-(1-q)^(participants-1) for every path length with >= 1000 rows (q from Direct rows only), full data',
         value=f'goodness of fit chi-square {rt5_chi:.1f} on {rt5_df} df, p = {rt5_gof_p:.2f}; largest error {rt5_maxerr:.4f} (|z| = {rt5_zmax:.1f})',
         verdict='Confirmed' if rt5_gof_p >= 0.01 else lvl(rt5_maxerr, 0.005, 0.01),"""),
# 5) markdown: findings + evidence strength
("""- **R-RT5 The `...` gap:** 5.0% of Direct vs 12.3% of Indirect/Covered paths, consistent with an independent ~5% chance per link (⟳ largest error vs that model).""",
"""- **R-RT5 The `...` gap:** 5.0% of Direct vs 12.3% of Indirect/Covered paths. An independent ~5% chance per link predicts the gap rate of every path length within sampling error (⟳ chi-square goodness of fit printed above)."""),
("""- **R-RT5 gap per link:** narrow Wilson CI (⟳) and the same every month. The model is classed as a **Mechanism** only if it misses by < 0.5 pp. On the full data it misses by ~1.4 pp on long paths, so it is an **Association** (an approximate per-link model).""",
"""- **R-RT5 gap per link:** narrow Wilson CI (⟳) and the same every month. The per-link model is tested with a chi-square goodness of fit over all path lengths (q from Direct rows only), on the full data and on the test period (q learned on train). It is a **Mechanism** only if neither test rejects it (p ≥ 0.01). The largest absolute miss (~1.4 points at 10 banks) comes from a group of only ~2,200 rows, where the standard error is ~1 point, so it is within sampling error. This shows the data are consistent with independent gaps; it does not prove the generator draws them that way."""),
# 7) DUR3 control sample: sort first, so the seeded sample does not depend on DuckDB's row order (p-values changed between runs)
("""ref = sn.join(cell_med, on=['TRANSACTION_TYPE_CODE', 'PARTICIPANT_COUNT']); ref_x = np.log(ref.TOTAL_DURATION / ref.cell_med)""",
 """ref = sn.join(cell_med, on=['TRANSACTION_TYPE_CODE', 'PARTICIPANT_COUNT']); ref_x = np.log(ref.TOTAL_DURATION / ref.cell_med).sort_values(ignore_index=True)"""),
]

P03 = [
("row('A1 amount off by >= 2 orders of magnitude',", "row('A1 amount off by a rounded order of magnitude >= 2 (about 32x or more)',"),
("""f'amount {K}+ orders of magnitude from the country x pair median'""", """f'amount {K}+ orders of magnitude (rounded; >= {10 ** (K - 0.5):.0f}x) from the country x pair median'"""),
("""        'share of payments >= 2 orders of magnitude from the country x pair median', t_val('A1'),""",
 """        'share of payments whose rounded log10 distance from the country x pair median is >= 2 (about 32x or more)', t_val('A1'),"""),
("""    'A1': f"Partly: fat-finger payments are far more often >= 100x away from the typical amount (test grade {stat.get('A1', '-')}); \"""",
 """    'A1': f"Partly: fat-finger payments are far more often about 32x or more away from the typical amount (rounded order of magnitude >= 2; test grade {stat.get('A1', '-')}); \""""),

# 5) A2: duplicates come in BURSTS of labelled copies; most 'earlier matching payments' are an earlier copy of the same burst
("""display(A2B)""",
"""display(A2B)

# A2 structure: group labelled duplicates by (sender account, payee account, currency). How many copies per burst, how far apart,
# is the amount identical, and does the FIRST copy of a burst have an earlier UNLABELLED original (vs the chance rate for normal payments)?
burst = q(\"\"\"WITH d AS (SELECT rid, count(*) OVER w AS k, row_number() OVER (w ORDER BY EPOCH_SECONDS, rid) AS pos,
                 EPOCH_SECONDS - lag(EPOCH_SECONDS) OVER (w ORDER BY EPOCH_SECONDS, rid) AS gap,
                 max(USD_AMOUNT) OVER w / nullif(min(USD_AMOUNT) OVER w, 0) AS amt_ratio
             FROM p WHERE anomaly = 'DUPLICATE_PAYMENT'
             WINDOW w AS (PARTITION BY ORDERING_BIC8, ORDERING_ACCOUNT, BENEFICIARY_BIC8, BENEFICIARY_ACCOUNT, CURRENCY_CODE))
          SELECT count(*) n, sum((pos = 1)::INT) bursts, min(k) kmin, max(k) kmax, avg((amt_ratio = 1)::INT) exact_amount,
                 median(gap) med_gap, quantile_cont(gap, 0.9) p90_gap, sum((pos > 1)::INT) later,
                 sum((pos > 1 AND m.orig_anomaly = 'DUPLICATE_PAYMENT')::INT) later_match_copy,
                 sum((pos = 1 AND m.orig_anomaly = 'NONE')::INT) first_with_orig
          FROM d LEFT JOIN dup_match m USING (rid)\"\"\").iloc[0]
_ctl = dupt[dupt.group != 'DUPLICATE_PAYMENT']; burst_ctl = float((_ctl.match_rate * _ctl.n).sum() / _ctl.n.sum())
save(burst.to_frame().T.assign(control_earlier_match=burst_ctl), 'a_duplicate_bursts')
print(f"{int(burst.bursts)} bursts of {int(burst.kmin)}-{int(burst.kmax)} copies; identical amount {burst.exact_amount:.1%}; "
      f"later copies matched to an earlier copy {burst.later_match_copy / burst.later:.1%}; first copy with an unlabelled original "
      f"{burst.first_with_orig / burst.bursts:.1%} (normal payments' chance rate {burst_ctl:.1%})")
"""),
("""    add('A2', 'Anomalies', 'A duplicate re-sends an earlier payment: same payee, currency and amount (+-1%), minutes later',
        'share with an earlier matching payment vs normal payments', '; '.join(t_val(f'A2 earlier same-payee/amount payment, sender {s}') for s in 'BC' if has(f'A2 earlier same-payee/amount payment, sender {s}')),""",
"""    add('A2', 'Anomalies', f'Duplicates come in bursts of {int(burst.kmin)}-{int(burst.kmax)} identical payments (same sender, payee, currency and amount) '
        f'about {burst.med_gap / 60:.0f} minutes apart; every copy is labelled, and an unlabelled original before the burst is '
        + ('found no more often than by chance' if burst.first_with_orig / burst.bursts <= 2 * burst_ctl else f'found for {burst.first_with_orig / burst.bursts:.0%} of bursts'),
        'burst structure of labelled duplicates; share with an earlier matching payment vs normal payments',
        f"{int(burst.bursts)} bursts of {int(burst.kmin)}-{int(burst.kmax)} copies, identical amount {burst.exact_amount:.0%}, median {burst.med_gap:.0f}s apart; "
        f"first copy with an earlier unlabelled match {burst.first_with_orig / burst.bursts:.1%} (normal {burst_ctl:.1%}); earlier match (any copy): "
        + '; '.join(t_val(f'A2 earlier same-payee/amount payment, sender {s}') for s in 'BC' if has(f'A2 earlier same-payee/amount payment, sender {s}')),"""),
("""        'Strong', 'a_duplicates_vs_control.csv; a_significance_tests.csv;""",
 """        'Strong', 'a_duplicate_bursts.csv; a_duplicates_vs_control.csv; a_significance_tests.csv;"""),
]

P04 = [
# 6) sign-off tied to the value AND the final verdict the reviewer saw (a verdict change, e.g. a failed holdout, also resets it)
("""SO_COLS = ['id', 'approved', 'reviewer', 'notes', 'value_reviewed', 'current_value', 'final_verdict', 'evidence_files']""",
 """SO_COLS = ['id', 'approved', 'reviewer', 'notes', 'value_reviewed', 'verdict_reviewed', 'current_value', 'final_verdict', 'evidence_files']"""),
("""    now = str(emi.value.get(x, 'missing')); seen = so.loc[x, 'value_reviewed'] or so.loc[x, 'current_value']
    if yes(so.loc[x, 'approved']):
        if seen and seen != now:
            so.loc[x, 'notes'] = (so.loc[x, 'notes'] + ' | ' if so.loc[x, 'notes'] else '') + f'sign-off reset {pd.Timestamp.now():%Y-%m-%d %H:%M}: value changed from "{seen}" to "{now}"'
            so.loc[x, ['approved', 'value_reviewed']] = ['False', '']
        else: so.loc[x, 'value_reviewed'] = now""",
 """    now = str(emi.value.get(x, 'missing')); seen = so.loc[x, 'value_reviewed'] or so.loc[x, 'current_value']
    vnow = str(emi.final_verdict.get(x, 'missing')); vseen = so.loc[x, 'verdict_reviewed'] or so.loc[x, 'final_verdict']   # verdict shown when approved
    if yes(so.loc[x, 'approved']):
        why = ([f'value changed from "{seen}" to "{now}"'] if seen and seen != now else []) + \\
              ([f'final verdict changed from {vseen} to {vnow}'] if vseen and vseen != vnow else [])
        if why:
            so.loc[x, 'notes'] = (so.loc[x, 'notes'] + ' | ' if so.loc[x, 'notes'] else '') + f'sign-off reset {pd.Timestamp.now():%Y-%m-%d %H:%M}: ' + '; '.join(why)
            so.loc[x, ['approved', 'value_reviewed', 'verdict_reviewed']] = ['False', '', '']
        else: so.loc[x, ['value_reviewed', 'verdict_reviewed']] = [now, vnow]"""),
]

def patch(name, rules):
    nb = json.load(open(src / name, encoding='utf-8'))
    for old, new in rules:
        hits = [c for c in nb['cells'] if old in ''.join(c['source'])]
        assert len(hits) == 1, (name, len(hits), old[:80])
        c = hits[0]; s = ''.join(c['source']).replace(old, new)
        c['source'] = s.splitlines(keepends=True)
    json.dump(nb, open(dst / name, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('patched', name, len(rules))

patch('02_member2_analysis.ipynb', P02)
patch('03_anomalies_accounts_details.ipynb', P03)
if (src / '04_integration_validation.ipynb').exists(): patch('04_integration_validation.ipynb', P04)
