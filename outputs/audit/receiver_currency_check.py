"""Audit check for slide 7 (R-CCY1, rejected alternative "priced in the receiver's currency").

The 4.2% "Receiver local" class in ccy1_currency_choice.csv is exclusive (receiver's local currency but NOT the
sender's), so it cannot reject receiver pricing on its own. The discriminating test is: among payments whose sender
and receiver local currencies DIFFER, which of the two currencies is used?

Data: data/processed/sample_20pct.parquet (the same 20% sample used for the regressions).
Local currency of a BIC country = the currency its senders use most (same definition as notebook 01).
Output: outputs/audit/receiver_currency_check.csv
Run from the project root:  python outputs/audit/receiver_currency_check.py
"""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / 'data' / 'processed' / 'sample_20pct.parquet'
OUT = ROOT / 'outputs' / 'audit' / 'receiver_currency_check.csv'

con = duckdb.connect()
con.execute(f"CREATE VIEW p AS SELECT * FROM read_parquet('{SAMPLE.as_posix()}')")
con.execute("""CREATE TABLE lc AS SELECT o_cc AS cc, arg_max(CURRENCY_CODE, n) AS local_ccy
               FROM (SELECT o_cc, CURRENCY_CODE, count(*) n FROM p GROUP BY ALL) GROUP BY o_cc""")
res = con.execute("""
WITH t AS (
  SELECT p.CURRENCY_CODE AS c, ls.local_ccy AS sl, lr.local_ccy AS rl, lf.local_ccy AS fl
  FROM p
  LEFT JOIN lc ls ON p.o_cc = ls.cc
  LEFT JOIN lc lr ON p.b_cc = lr.cc
  LEFT JOIN lc lf ON substr(BIC8_PATH, 5, 2) = lf.cc          -- country of the first bank on the path
)
SELECT count(*)                                              AS n_payments,
       avg((c = sl)::INT)                                    AS sender_local,
       avg((c = rl)::INT)                                    AS receiver_local_inclusive,
       avg((c = rl AND c <> sl)::INT)                        AS receiver_local_not_sender,
       avg((sl = rl)::INT)                                   AS share_same_local_currency,
       avg((sl <> rl)::INT)                                  AS share_different_local_currency,
       avg(CASE WHEN sl <> rl THEN (c = rl)::INT END)        AS receiver_local_when_different,
       avg(CASE WHEN sl <> rl THEN (c = sl)::INT END)        AS sender_local_when_different,
       avg(CASE WHEN sl <> rl THEN (c = fl)::INT END)        AS first_bank_local_when_different,
       avg((c = fl)::INT)                                    AS first_bank_local
FROM t""").df()
res.insert(0, 'data', '20% sample (sample_20pct.parquet)')
OUT.parent.mkdir(parents=True, exist_ok=True)
res.to_csv(OUT, index=False)
print(res.T.to_string())
