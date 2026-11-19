"""Audit fix 2 (19 Nov ~04:35): R-BC1 on all 10M normal rows (it used the 20% sample while slides said 'full data'),
with an account-clustered test; notebook 04 note on the clock-offset sanity check. Usage: python patch_audit2.py <in_dir> <out_dir>"""
import json, sys, pathlib
src, dst = map(pathlib.Path, sys.argv[1:3]); dst.mkdir(parents=True, exist_ok=True)
P04 = [
("""v, pv = cramers_v(n.ORDERING_TYPE, n.BENEFICIARY_TYPE)
add('R-BC1', 'Business/consumer', 'Sender and receiver party types show no measurable association (consistent with independent assignment; not proof of independent draws)', "chi-square p, Cramér's V",
    f'p = {pv:.2f}, V = {v:.4f}', 'Confirmed' if v < 0.01 else 'Rejected', 'bc1_type_independence.png', 'Consistent with separate draws for who pays and who gets paid')""",
"""# R-BC1 on ALL normal rows (the 20% sample hides a tiny association that 10M rows can detect). Rows are not independent:
# one sender account makes many payments, so the naive chi-square p is too small; an account-clustered test is reported too.
bc1 = sql(\"\"\"SELECT ORDERING_TYPE t, ORDERING_BIC8, ORDERING_ACCOUNT, count(*) n, sum((BENEFICIARY_TYPE = 'B')::INT) k
              FROM p WHERE anomaly = 'NONE' GROUP BY ALL\"\"\")
g1 = bc1.groupby('t')[['n', 'k']].sum()
ct1 = np.array([[g1.loc['B', 'k'], g1.loc['B', 'n'] - g1.loc['B', 'k']], [g1.loc['C', 'k'], g1.loc['C', 'n'] - g1.loc['C', 'k']]], float)
chi1, pv, _, _ = stats.chi2_contingency(ct1, correction=False); v = float(np.sqrt(chi1 / ct1.sum()))
pr1 = g1.k / g1.n
var1 = {t_: float((((d_.k - d_.n * pr1[t_]) ** 2).sum()) / g1.loc[t_, 'n'] ** 2) for t_, d_ in bc1.groupby('t')}   # cluster = sender account
p_cl = float(2 * stats.norm.sf(abs(pr1['B'] - pr1['C']) / np.sqrt(var1['B'] + var1['C'])))
add('R-BC1', 'Business/consumer', 'Sender and receiver party types have a negligible association on all 10M rows (consistent with independent assignment; not proof of independent draws)',
    "Cramér's V and P(receiver B) by sender type, all normal rows; chi-square p naive and clustered by sender account",
    f"V = {v:.4f}; P(receiver B) {pr1['B']:.2%} for B vs {pr1['C']:.2%} for C senders; p = {pv:.3f} naive, {p_cl:.3f} account-clustered",
    'Confirmed' if v < 0.01 else 'Rejected', 'bc1_type_independence.png', 'Consistent with separate draws for who pays and who gets paid')"""),
("""A one-off sanity check during development, outside this pipeline, found the offsets equal to the standard (non-summer) UTC offsets for ~96% of countries. The rest are multi-zone countries such as CA, RU and BR, where the data picks the busiest zone.""",
 """Any comparison with real time zones was an informal check outside this pipeline; it is not evidence for any rule, and no time-zone table enters a calculation."""),
]
def patch(name, rules):
    nb = json.load(open(src / name, encoding='utf-8'))
    for old, new in rules:
        hits = [c for c in nb['cells'] if old in ''.join(c['source'])]
        assert len(hits) == 1, (name, len(hits), old[:80])
        c = hits[0]; c['source'] = ''.join(c['source']).replace(old, new).splitlines(keepends=True)
    json.dump(nb, open(dst / name, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('patched', name, len(rules))
patch('04_integration_validation.ipynb', P04)
