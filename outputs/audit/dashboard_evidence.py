"""Extra evidence tables for the dashboard (one direct chart per rule).

Writes two small tables to outputs/tables, computed with the same definitions as the notebooks:
  ev_amt1_residuals.csv   R-AMT1: distribution of ln(USD amount) residuals after sender country and party types
                          (notebook 01 model: within-sender-country regression fitted on the first 2/3 of time),
                          observed share per 0.5-wide bin vs a normal curve with the same sd. 20% sample, normal payments.
  ev_amt1_summary.csv     n, sd, skewness and excess kurtosis of those residuals (all rows and test period).
  ev_a2_burst_sizes.csv   A2: labelled duplicates grouped by (sender account, payee account, currency) as in notebook 03:
                          number of bursts by copies per burst, and the median gap between copies.
Inputs: data/processed/sample_20pct.parquet, data/processed/anomalies.parquet (both built by notebook 04).
Run from the project root:  python outputs/audit/dashboard_evidence.py
"""
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
PROC, TAB = ROOT / 'data' / 'processed', ROOT / 'outputs' / 'tables'

# ---------------------------------------------------------------- R-AMT1 residuals (20% sample, normal payments)
n = pd.read_parquet(PROC / 'sample_20pct.parquet', columns=['EPOCH_SECONDS', 'USD_AMOUNT', 'o_cc', 'ORDERING_TYPE', 'BENEFICIARY_TYPE', 'anomaly'])
n = n[(n.anomaly == 'NONE') & (n.USD_AMOUNT > 0)].reset_index(drop=True)
n['la'] = np.log(n.USD_AMOUNT); n['ob'] = (n.ORDERING_TYPE == 'B').astype(float); n['bb'] = (n.BENEFICIARY_TYPE == 'B').astype(float)
T_SPLIT = int(np.quantile(n.EPOCH_SECONDS, 2 / 3, method='inverted_cdf'))
def fit_amount(d):
    W = d[['la', 'ob', 'bb']] - d.groupby('o_cc')[['la', 'ob', 'bb']].transform('mean')
    b = np.linalg.lstsq(W[['ob', 'bb']].values, W.la.values, rcond=None)[0]
    return b, (d.la - b[0] * d.ob - b[1] * d.bb).groupby(d.o_cc).mean()
is_tr = n.EPOCH_SECONDS < T_SPLIT
b, base = fit_amount(n[is_tr])
res = (n.la - (n.o_cc.map(base) + b[0] * n.ob + b[1] * n.bb)).dropna()
res_te = res[~is_tr.loc[res.index]]
summ = pd.DataFrame([dict(rows=k, n=len(r), sd=r.std(), skew=stats.skew(r), excess_kurtosis=stats.kurtosis(r), b_sender=b[0], b_receiver=b[1])
                     for k, r in [('all', res), ('test period', res_te)]])
sd = res.std(); edges = np.arange(-9, 9.0001, 0.5); mids = (edges[:-1] + edges[1:]) / 2
obs = np.histogram(res, bins=edges)[0] / len(res)
nrm = np.diff(stats.norm.cdf(edges, loc=res.mean(), scale=sd))
hist = pd.DataFrame({'residual_ln': mids, 'observed': obs, 'normal_model': nrm})

# ---------------------------------------------------------------- A2 duplicate bursts (all labelled duplicates)
con = duckdb.connect()
bursts = con.execute(f"""
  WITH d AS (SELECT count(*) OVER w AS k, row_number() OVER (w ORDER BY EPOCH_SECONDS, rid) AS pos,
                    EPOCH_SECONDS - lag(EPOCH_SECONDS) OVER (w ORDER BY EPOCH_SECONDS, rid) AS gap
             FROM read_parquet('{(PROC / 'anomalies.parquet').as_posix()}') WHERE anomaly = 'DUPLICATE_PAYMENT'
             WINDOW w AS (PARTITION BY ORDERING_BIC8, ORDERING_ACCOUNT, BENEFICIARY_BIC8, BENEFICIARY_ACCOUNT, CURRENCY_CODE))
  SELECT k AS copies_per_burst, sum((pos = 1)::INT) AS bursts, count(*) AS copies, median(gap) AS median_gap_s
  FROM d GROUP BY k ORDER BY k""").df().astype({'bursts': int, 'copies': int})

hist.to_csv(TAB / 'ev_amt1_residuals.csv', index=False, float_format='%.8f')
summ.to_csv(TAB / 'ev_amt1_summary.csv', index=False)
bursts.to_csv(TAB / 'ev_a2_burst_sizes.csv', index=False)
print(summ.to_string(index=False)); print(bursts.to_string(index=False))
print('residual share within +-2 sd:', float(((res - res.mean()).abs() <= 2 * sd).mean()))
