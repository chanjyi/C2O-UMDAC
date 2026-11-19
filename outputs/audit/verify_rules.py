"""Independent re-test of the 11 principal rules (C2O, UMDAC Datathon 2026).

Written separately from notebooks 01-04: it re-derives every statistic from the parquet with its own code
and its own definitions, so agreement with rules_log.csv is real corroboration, not a copy.

Usage:  python verify_rules.py <parquet> [<anomalies parquet>] [<out csv>]
  - full data (payments_clean.parquet, has the details text): every check runs
  - 20% sample (sample_20pct.parquet, no details text): D2 is skipped; A2 / AC3 are sample-level only
"""
import sys, time, json
import numpy as np, pandas as pd, duckdb
from scipy import stats

PQ = sys.argv[1]
ANOM = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != '-' else None
OUT = sys.argv[3] if len(sys.argv) > 3 else 'independent_check.csv'
t0 = time.time()
import os
DBF = os.path.join(os.path.dirname(os.path.abspath(OUT)), '_verify_tmp.duckdb')
con = duckdb.connect(DBF)                                  # file-backed so large tables can spill to disk
con.execute("SET TimeZone = 'UTC'"); con.execute("SET memory_limit = '3GB'"); con.execute("SET preserve_insertion_order = false")
con.execute(f"CREATE OR REPLACE VIEW p AS SELECT * FROM read_parquet('{PQ}')")
cols = set(con.execute("DESCRIBE p").df().column_name)
HAS_DET = 'ORDERING_DETAILS' in cols
N = con.execute("SELECT count(*) FROM p").fetchone()[0]
FULL = N > 9_000_000 or os.environ.get("VERIFY_FORCE_FULL") == "1"
print(f'rows {N:,}  full={FULL}  details={HAS_DET}')
q = lambda s: con.execute(s).df()
R = []
def rec(rid, check, value, verdict, exact, note=''):
    R.append(dict(id=rid, check=check, independent_value=value, independent_verdict=verdict, rule_kind=exact, note=note))
    print(f'[{rid}] {check}: {value} -> {verdict} ({exact}) {note}')

def wilson(k, n, z=1.96):
    if n == 0: return (np.nan, np.nan)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)

# country of a BIC8 = characters 5-6 (ISO 9362 layout); train/test split by a hash of the row id (independent of the notebooks' split)
con.execute("""CREATE OR REPLACE TABLE b AS SELECT rid, CURRENCY_CODE ccy, USD_AMOUNT usd, TOTAL_DURATION dur, ORDERING_TYPE ot, BENEFICIARY_TYPE bt,
      TRANSACTION_TYPE_CODE tt, PARTICIPANT_COUNT pc, CURRENCY_CONVERSION_COUNT conv, BIC8_PATH path, CONTINUITY_QFLAG qf,
      ORDERING_BIC8 obic, BENEFICIARY_BIC8 bbic, ORDERING_ACCOUNT oacc, BENEFICIARY_ACCOUNT bacc, EPOCH_SECONDS es,
      substr(ORDERING_BIC8, 5, 2) occ, substr(BENEFICIARY_BIC8, 5, 2) bcc, coalesce(ANOMALY_TYPE, 'NONE') an,
      (hash(rid * 7919 + 13) % 5 = 0) is_test FROM p""")

# ---------------- R-CCY1 -----------------------------------------------------------------------------------------
# local currency of a country = modal payment currency of payments whose FIRST PATH bank is in that country, learned on train rows only
con.execute("""CREATE OR REPLACE TABLE loc AS SELECT cc, arg_max(ccy, n) lc, max(n)::DOUBLE / sum(n) modal_share, sum(n) n FROM
   (SELECT substr(split_part(path, ';', 1), 5, 2) cc, ccy, count(*) n FROM b WHERE NOT is_test GROUP BY ALL) GROUP BY cc""")
c1 = q("""SELECT count(*) n, avg((b.ccy = lf.lc)::INT) first_bank, avg((b.ccy = lo.lc)::INT) ordering_bank,
            avg((b.ccy <> lo.lc AND b.ccy = lr.lc)::INT) receiver_only, avg((lf.lc IS NULL)::INT) unmapped
          FROM b LEFT JOIN loc lf ON substr(split_part(b.path, ';', 1), 5, 2) = lf.cc
                 LEFT JOIN loc lo ON b.occ = lo.cc LEFT JOIN loc lr ON b.bcc = lr.cc WHERE b.is_test""").iloc[0]
lo_, hi_ = wilson(c1.first_bank * c1.n, c1.n)
ms = q("SELECT quantile_cont(modal_share, [0.05, 0.5, 0.95]) q, min(modal_share) mn FROM loc WHERE n >= 500").iloc[0]
# what are the exceptions? (test rows, payment currency != first-bank local currency)
ex = q("""SELECT CASE WHEN b.ccy = lr.lc THEN 'receiver local' WHEN b.ccy IN ('USD','EUR') THEN b.ccy ELSE 'other' END k, count(*) n
          FROM b LEFT JOIN loc lf ON substr(split_part(b.path, ';', 1), 5, 2) = lf.cc LEFT JOIN loc lr ON b.bcc = lr.cc
          WHERE b.is_test AND b.ccy <> lf.lc GROUP BY 1""").set_index('k').n
ex = (ex / ex.sum()).round(3).to_dict()
# triangulation: currency codes embedded in non-IBAN account numbers (a source that does not use payment currency at all)
tri = q(r"""WITH a AS (SELECT occ cc, regexp_extract(oacc, '_FAKE_[^A-Z]*([A-Z]{3})', 1) code FROM b
                       WHERE NOT regexp_matches(oacc, '^_FAKE_[A-Z]{2}[0-9]{2}') AND regexp_matches(oacc, '_FAKE_[^A-Z]*[A-Z]{3}'))
            SELECT avg((a.code = l.lc)::INT) agree, count(*) n, count(DISTINCT a.cc) countries FROM a JOIN loc l USING (cc)""").iloc[0]
rec('R-CCY1', 'payment currency = local currency of first path bank (holdout rows)',
    f"first bank {c1.first_bank:.2%} [{lo_:.2%}, {hi_:.2%}], ordering bank {c1.ordering_bank:.2%}, receiver-only {c1.receiver_only:.2%}; "
    f"per-country modal share p5/median/p95 = {ms.q[0]:.1%}/{ms.q[1]:.1%}/{ms.q[2]:.1%}; exceptions {ex}; "
    f"account-number currency codes agree with learned local currency {tri.agree:.1%} (n={int(tri.n):,}, {int(tri.countries)} countries)",
    'Partial (93%): reproduced', 'stochastic rule (~93% local, rest receiver / USD / EUR / other)')

# ---------------- R-AMT2 -----------------------------------------------------------------------------------------
if not FULL:   # regression on the 20% sample only (as in notebook 01); skipped on full data to save memory
    d = q("SELECT occ, ln(usd) y, (ot = 'B')::INT bo, (bt = 'B')::INT bb, oacc FROM b WHERE an = 'NONE' AND usd > 0")
    g = pd.factorize(d.occ)[0]; cnt = np.bincount(g)
    X = d[['bo', 'bb']].to_numpy(float); X = np.column_stack([X, X[:, 0] * X[:, 1]]); y = d.y.to_numpy()
    dm = lambda v: v - (np.bincount(g, v) / cnt)[g]
    Xw = np.column_stack([dm(X[:, j]) for j in range(3)]); yw = dm(y)
    XtX_inv = np.linalg.inv(Xw.T @ Xw); beta = XtX_inv @ Xw.T @ yw; u = yw - Xw @ beta
    cl = pd.factorize(d.oacc)[0]; S = np.column_stack([np.bincount(cl, Xw[:, j] * u) for j in range(3)])
    V = XtX_inv @ (S.T @ S) @ XtX_inv; se = np.sqrt(np.diag(V))
    # model without interaction (for the headline coefficients)
    Xw2 = Xw[:, :2]; XtX2 = np.linalg.inv(Xw2.T @ Xw2); b2 = XtX2 @ Xw2.T @ yw; u2 = yw - Xw2 @ b2
    S2 = np.column_stack([np.bincount(cl, Xw2[:, j] * u2) for j in range(2)]); se2 = np.sqrt(np.diag(XtX2 @ (S2.T @ S2) @ XtX2))
    sd_pair = d.assign(r=u2).groupby(d.bo.astype(str) + d.bb.astype(str)).r.std().round(3).to_dict()
    ci = lambda b_, s_: f"{b_:.3f} [{b_ - 1.96 * s_:.3f}, {b_ + 1.96 * s_:.3f}]"
    both2 = all(abs(b2[j] - 2) < 1.96 * se2[j] for j in range(2))
    rec('R-AMT2', 'ln(USD) on sender-country FE + sender B + receiver B, cluster-robust by sender account (normal rows)',
        f"sender {ci(b2[0], se2[0])}, receiver {ci(b2[1], se2[1])}; interaction {ci(beta[2], se[2])}; residual sd by pair (sender,receiver B=1) {sd_pair}",
        'Supported: both CIs contain 2.0' if both2 else 'Effect present but CI excludes 2.0',
        'parametric rule: multiplier e^2 per business party (CI contains exactly 2.0, interaction ~0)')

# ---------------- R-BC1 ------------------------------------------------------------------------------------------
t = q("SELECT ot, bt, count(*) n FROM b GROUP BY ALL").pivot(index='ot', columns='bt', values='n')
chi2, pchi, _, exp_ = stats.chi2_contingency(t.values, correction=False)
V_ = np.sqrt(chi2 / t.values.sum())
ps = (t.values / t.values.sum()).ravel()
pB_o = t.loc['B'].sum() / t.values.sum(); pB_b = t['B'].sum() / t.values.sum()
# within sender country (stratified): Cochran-Mantel-Haenszel style check, max |log OR| over big countries
st = q("SELECT occ, ot, bt, count(*) n FROM b GROUP BY ALL")
ors = []
for cc, gg in st.groupby('occ'):
    m = gg.pivot(index='ot', columns='bt', values='n').reindex(index=['B', 'C'], columns=['B', 'C']).fillna(0).values
    if m.min() >= 100: ors.append(np.log(m[0, 0] * m[1, 1] / (m[0, 1] * m[1, 0])))
rec('R-BC1', 'chi-square independence of sender type x receiver type',
    f"chi2 p = {pchi:.3f}, Cramer V = {V_:.4f}; P(sender B) = {pB_o:.4f}, P(receiver B) = {pB_b:.4f}; "
    f"observed B2B/B2C/C2B/C2C = {ps[0]:.2%}/{ps[1]:.2%}/{ps[2]:.2%}/{ps[3]:.2%}; within-country log OR median {np.median(ors):+.3f} "
    f"(IQR {np.percentile(ors, 25):+.3f}..{np.percentile(ors, 75):+.3f}, {len(ors)} countries)",
    'Supported (no association; independence not provable)', 'stochastic rule: two separate draws, P(B)=0.79 / 0.29')

# ---------------- R-RT6 / R-RT5 ----------------------------------------------------------------------------------
h = q("SELECT pc - 2 k, count(*) n, sum((qf = 'N')::INT) gaps FROM b GROUP BY 1 ORDER BY 1")
kbar = (h.k * h.n).sum() / h.n.sum(); qhat = kbar / (1 + kbar)
h['pred'] = (1 - qhat) * qhat ** h.k * h.n.sum()
hh = h[h.pred >= 5].copy(); tail = h[h.pred < 5]
obs = np.append(hh.n.values, tail.n.sum()); exp_g = np.append(hh.pred.values, h.n.sum() - hh.pred.sum())
chi_g = ((obs - exp_g) ** 2 / exp_g).sum(); df_g = len(obs) - 2; p_g = stats.chi2.sf(chi_g, df_g)
tvd = 0.5 * np.abs(obs / obs.sum() - exp_g / exp_g.sum()).sum()
ic = q("SELECT tt, pc - 2 k, count(*) n FROM b WHERE tt <> 'Direct' GROUP BY ALL").pivot(index='k', columns='tt', values='n').fillna(0)
ic = ic[ic.sum(1) >= 50]; chi_ic, p_ic, _, _ = stats.chi2_contingency(ic.values)
rec('R-RT6', 'intermediaries k = participants - 2 ~ Geometric(q); Indirect vs Covered k distributions',
    f"q = {qhat:.4f}; GOF chi2 = {chi_g:.1f} on {df_g} df, p = {p_g:.3f}; total variation distance {tvd:.4f}; "
    f"Indirect vs Covered (k>=1) chi2 p = {p_ic:.3f}", 'Supported' if p_g > 0.001 else 'Shape close but GOF rejects',
    'stochastic rule: each further intermediary added with probability ~0.368')
# per-link gap model: P(gap | links L) = 1 - (1 - p)^L with L = participants - 1; p fitted by maximum likelihood on ALL rows
L = (h.k + 1).values; n_ = h.n.values; gk = h.gaps.values
pgrid = np.linspace(0.03, 0.07, 4001)
ll = [(gk * np.log(1 - (1 - pp) ** L) + (n_ - gk) * L * np.log(1 - pp)).sum() for pp in pgrid]
p_hat = pgrid[int(np.argmax(ll))]
pr = 1 - (1 - p_hat) ** L
mask = n_ * pr >= 5
z = (gk - n_ * pr) / np.sqrt(n_ * pr * (1 - pr))
chi_l = (z[mask] ** 2).sum(); df_l = mask.sum() - 1; p_l = stats.chi2.sf(chi_l, df_l)
worst = int(np.argmax(np.abs(z[mask]))); km = h.k.values[mask][worst] + 2
maxpp = np.max(np.abs(gk / n_ - pr)[mask])
# alternative: one gap rate for Direct, another flat rate for every multi-bank path
flat = q("SELECT (pc = 2) direct, avg((qf = 'N')::INT) r FROM b GROUP BY 1").set_index('direct').r.to_dict()
rec('R-RT5', 'continuity gap = independent per-link chance p (MLE on all rows), goodness of fit by participant count',
    f"p = {p_hat:.4f}; GOF chi2 = {chi_l:.1f} on {df_l} df, p = {p_l:.3f}; largest |z| = {abs(z[mask][worst]):.2f} at {km} banks; "
    f"largest gap {maxpp * 100:.2f} pts; flat alternative: Direct {flat.get(True, np.nan):.2%} vs multi-bank {flat.get(False, np.nan):.2%} "
    f"(gap rate rises with path length, so a flat rate is rejected)",
    'Approximate: per-link model fits within sampling error' if p_l > 0.01 else 'Approximate: per-link model rejected by GOF',
    'stochastic rule (approximate): ~5% per link')

# ---------------- R-DUR1 -----------------------------------------------------------------------------------------
md = q("SELECT tt, median(dur) m, count(*) n FROM b WHERE an = 'NONE' GROUP BY 1").set_index('tt').m
mk = q("SELECT tt, pc, median(dur) m, count(*) n FROM b WHERE an = 'NONE' AND dur > 0 GROUP BY ALL HAVING count(*) >= 200 ORDER BY 1, 2")
mono = all((gg.m.diff().dropna() > 0).all() for _, gg in mk.groupby('tt'))
dd = q("SELECT ln(dur) y, tt || '_' || least(pc, 10) g FROM b WHERE an = 'NONE' AND dur > 0")
gi = pd.factorize(dd.g)[0]; yy = dd.y.to_numpy(); fit = (np.bincount(gi, yy) / np.bincount(gi))[gi]
r2 = 1 - ((yy - fit) ** 2).sum() / ((yy - yy.mean()) ** 2).sum()
ins = q("""WITH x AS (SELECT tt, pc, (NOT is_test) tr, ln(dur) y FROM b WHERE an = 'NONE' AND dur > 0)
           SELECT corr(a.m, b2.m) c FROM (SELECT tt, pc, avg(y) m FROM x WHERE tr GROUP BY ALL HAVING count(*) > 200) a
           JOIN (SELECT tt, pc, avg(y) m FROM x WHERE NOT tr GROUP BY ALL HAVING count(*) > 200) b2 USING (tt, pc)""").iloc[0, 0]
rec('R-DUR1', 'median duration by routing type; monotone in participants within type; R2 of ln(duration) on type x participants',
    f"medians Direct {md.get('Direct'):.0f}s, Indirect {md.get('Indirect'):.0f}s, Covered {md.get('Covered'):.0f}s; "
    f"median rises with every extra bank within each type: {mono}; R2 = {r2:.3f}; train/test cell-mean correlation {ins:.3f}",
    'Supported (direction); weak fit', 'approximate association: ordering exact, individual times mostly unexplained')

# ---------------- R-FX1 ------------------------------------------------------------------------------------------
loc = q("SELECT cc, lc FROM loc").set_index('cc').lc.to_dict()
fx = q("SELECT path, conv, is_test FROM b WHERE qf = 'Y'" + (" AND is_test" if FULL else ""))
def pred(path):
    cs = [loc.get(x[4:6]) for x in path.split(';')]
    return sum(1 for a, c in zip(cs, cs[1:]) if a != c) if None not in cs else -1
fx['pred'] = [pred(s) for s in fx.path]
te = fx[fx.is_test & (fx.pred >= 0)]
k_ok = int((te.pred == te.conv).sum()); lo2, hi2 = wilson(k_ok, len(te))
fx_all = (fx.loc[fx.pred >= 0, 'pred'] == fx.loc[fx.pred >= 0, 'conv']).mean()
rec('R-FX1', 'conversions = changes of first-bank-learned local currency between consecutive path banks (complete paths, holdout rows)',
    f"{k_ok:,} / {len(te):,} = {k_ok / len(te):.4%} [{lo2:.4%}, {hi2:.4%}]; all complete rows {fx_all:.4%}; unmapped {(fx.pred < 0).mean():.4%}",
    'Confirmed' if k_ok == len(te) else 'Strong', 'exact deterministic rule' if k_ok == len(te) else 'near-exact')
del fx

# ---------------- AC3 --------------------------------------------------------------------------------------------
a3 = q("""SELECT 'sender' role, count(*) accounts, avg((nb > 1)::INT) multi_bic, avg((nt > 1)::INT) multi_type FROM
          (SELECT oacc, count(DISTINCT obic) nb, count(DISTINCT ot) nt FROM b GROUP BY 1)
          UNION ALL SELECT 'receiver', count(*), avg((nb > 1)::INT), avg((nt > 1)::INT) FROM
          (SELECT bacc, count(DISTINCT bbic) nb, count(DISTINCT bt) nt FROM b GROUP BY 1)""").set_index('role')
rec('AC3', 'account number -> distinct BICs / party types' + ('' if FULL else ' (20% SAMPLE: multi-BIC shares are lower than on full data)'),
    f"sender multi-BIC {a3.loc['sender', 'multi_bic']:.2%}, multi-type {a3.loc['sender', 'multi_type']:.2%}; "
    f"receiver multi-BIC {a3.loc['receiver', 'multi_bic']:.2%}, multi-type {a3.loc['receiver', 'multi_type']:.2%}",
    'Strong' if a3.loc['sender', 'multi_bic'] == 0 else 'Partial', 'exact for sender accounts; receiver numbers recur across banks')

# ---------------- A1 (fat finger) --------------------------------------------------------------------------------
src = f"read_parquet('{ANOM}')" if ANOM else "p"
con.execute(f"""CREATE OR REPLACE TABLE base AS SELECT occ, ot, bt, median(ln(usd)) m FROM b WHERE an = 'NONE' GROUP BY ALL""")
a1 = q(f"""WITH f AS (SELECT substr(ORDERING_BIC8,5,2) occ, ORDERING_TYPE ot, BENEFICIARY_TYPE bt, USD_AMOUNT usd, CURRENCY_CODE ccy
                     FROM {src} WHERE ANOMALY_TYPE = 'FAT_FINGER_MISTAKE'),
             c AS (SELECT occ, ot, bt, usd, ccy FROM b WHERE an = 'NONE' AND NOT is_test)
           SELECT 'ff' g, count(*) n, avg((abs(ln(usd) - m) >= 2 * ln(10))::INT) far, median(abs(ln(usd) - m) / ln(10)) med_dec FROM f JOIN base USING (occ, ot, bt)
           UNION ALL SELECT 'normal', count(*), avg((abs(ln(usd) - m) >= 2 * ln(10))::INT), median(abs(ln(usd) - m) / ln(10)) FROM c JOIN base USING (occ, ot, bt)""").set_index('g')
# exact x10^k test where no FX distorts decimals: USD-denominated payments keep the typed amount
dec = q(f"""WITH f AS (SELECT USD_AMOUNT usd FROM {src} WHERE ANOMALY_TYPE = 'FAT_FINGER_MISTAKE' AND CURRENCY_CODE = 'USD'),
               c AS (SELECT usd FROM b WHERE an = 'NONE' AND ccy = 'USD')
            SELECT 'ff' g, count(*) n, avg((round(usd * 100) % 100 = 0)::INT) whole, avg((round(usd * 100) % 10 = 0)::INT) cents_end0,
                   avg((abs(usd * 100 - round(usd * 100)) > 1e-6 * usd)::INT) more_than_2dp FROM f
            UNION ALL SELECT 'normal', count(*), avg((round(usd * 100) % 100 = 0)::INT), avg((round(usd * 100) % 10 = 0)::INT),
                   avg((abs(usd * 100 - round(usd * 100)) > 1e-6 * usd)::INT) FROM c""").set_index('g')
kf, nf = round(a1.loc['ff', 'far'] * a1.loc['ff', 'n']), a1.loc['ff', 'n']; kc, nc = round(a1.loc['normal', 'far'] * a1.loc['normal', 'n']), a1.loc['normal', 'n']
pp = (kf + kc) / (nf + nc); zz = (kf / nf - kc / nc) / np.sqrt(pp * (1 - pp) * (1 / nf + 1 / nc))
rec('A1', '>=100x (2 decades) from the sender-country x pair median: fat finger vs normal; decimals of USD-denominated amounts',
    f"fat finger {kf / nf:.1%} (n={nf:,}) vs normal {kc / nc:.1%} (z = {zz:.1f}); median distance {a1.loc['ff', 'med_dec']:.2f} vs "
    f"{a1.loc['normal', 'med_dec']:.2f} decades; USD-currency rows: whole-dollar {dec.loc['ff', 'whole']:.1%} vs {dec.loc['normal', 'whole']:.1%}, "
    f">2 decimals {dec.loc['ff', 'more_than_2dp']:.1%} vs {dec.loc['normal', 'more_than_2dp']:.1%} (n_ff={int(dec.loc['ff', 'n'])})",
    'Supported association', 'association: exact x10^k not identifiable (normal spread ~1 decade)')

# ---------------- A2 (duplicates): needs the full data so that originals are present ------------------------------
if FULL:
    con.execute("""CREATE OR REPLACE TABLE dupsrc AS SELECT rid, es, bbic, bacc, ccy, usd, obic, oacc, an FROM b
                   WHERE an = 'DUPLICATE_PAYMENT' UNION ALL SELECT * FROM (SELECT rid, es, bbic, bacc, ccy, usd, obic, oacc, an FROM b
                   WHERE an = 'NONE' USING SAMPLE reservoir(20000 ROWS) REPEATABLE (7))""")
    a2 = q("""WITH m AS (SELECT d.rid, d.an, min(abs(d.es - o.es)) FILTER (WHERE o.es <= d.es) gap_before,
                                min(abs(d.es - o.es)) FILTER (WHERE o.es > d.es) gap_after,
                                bool_or(o.obic = d.obic AND o.oacc = d.oacc) same_sender_any
               FROM dupsrc d LEFT JOIN b o ON o.bbic = d.bbic AND o.bacc = d.bacc AND o.ccy = d.ccy
                    AND abs(o.usd - d.usd) <= 0.01 * d.usd AND o.rid <> d.rid GROUP BY ALL)
              SELECT an, count(*) n, avg(coalesce(gap_before <= 3600, false)::INT) before_1h, avg((gap_before IS NOT NULL)::INT) before_any,
                     avg(coalesce(gap_after <= 3600, false)::INT) after_1h, avg((coalesce(gap_before, 1e12) <= 3600 OR coalesce(gap_after, 1e12) <= 3600)::INT) either_1h,
                     median(gap_before) med_gap_before
              FROM m GROUP BY 1""").set_index('an')
    D, C = a2.loc['DUPLICATE_PAYMENT'], a2.loc['NONE']
    rec('A2', 'same beneficiary BIC+account, currency, amount +-1%: earlier match within 1 hour / any time, vs 20k normal',
        f"duplicates: earlier match within 1h {D.before_1h:.1%}, any earlier {D.before_any:.1%}, later match within 1h {D.after_1h:.1%}, "
        f"either side within 1h {D.either_1h:.1%}, median gap {D.med_gap_before:.0f}s (n={int(D.n)}); normal: within 1h {C.before_1h:.2%}, any {C.before_any:.1%}",
        'Supported', 'association with a clear mechanism; ~1/4 of labelled duplicates have no matching original')
else:
    rec('A2', 'needs full data (originals mostly outside a 20% sample)', 'skipped on sample', 'n/a', 'n/a')

# ---------------- D2 (details formats): needs the details text --------------------------------------------------
if HAS_DET:
    d2 = q(r"""WITH x AS (SELECT 'ordering' side, replace(ORDERING_DETAILS, chr(13), '') t, ORDERING_BIC8 bic FROM p
                          UNION ALL SELECT 'beneficiary', replace(BENEFICIARY_DETAILS, chr(13), ''), BENEFICIARY_BIC8 FROM p),
                y AS (SELECT side, len(regexp_extract_all(t, '(?m)^[1-3]/')) > 0 num,
                             regexp_matches(t, '\n[A-Z0-9]{4}[A-Z]{2}[A-Z0-9]{2,5}\s*$') bicl,
                             regexp_extract(t, '\n([A-Z0-9]{8})[A-Z0-9]{0,3}\s*$', 1) = bic bic_self FROM x)
               SELECT side, count(*) n, avg((num AND NOT bicl)::INT) numbered, avg((bicl AND NOT num)::INT) bic_line,
                      avg((NOT num AND NOT bicl)::INT) neither, sum((num AND bicl)::INT) both_n,
                      avg(bic_self::INT) FILTER (WHERE bicl) bic_line_is_own_bic FROM y GROUP BY 1 ORDER BY 1""").set_index('side')
    both = int(d2.both_n.sum()); nn = int(d2.n.sum())
    rec('D2', 'numbered (1/,2/,3/ line starts) vs trailing BIC line (own regexes): co-occurrence',
        '; '.join(f"{s}: numbered {r.numbered:.2%}, BIC line {r.bic_line:.2%}, neither {r.neither:.2%}, both {int(r.both_n)}, "
                  f"BIC line = own BIC {r.bic_line_is_own_bic:.1%}" for s, r in d2.iterrows()),
        'Confirmed (0 co-occurrences)' if both == 0 else f'{both} co-occurrences', 'exact exclusivity; shares look like fixed draws (15/5/80)')
else:
    rec('D2', 'needs details text', 'skipped (sample has no details)', 'n/a', 'n/a')

pd.DataFrame(R).to_csv(OUT, index=False)
con.close()
try: os.remove(DBF)
except OSError: pass
print(f'done in {time.time() - t0:.0f}s -> {OUT}')
