@echo off
REM Re-runs notebooks 01, 03 and then 04 (rules log, evidence matrix, readiness check)
cd /d C:\cjy\y3s2\UMDAC\notebooks
set PY=%USERPROFILE%\anaconda3\python.exe
set T=C:\cjy\y3s2\UMDAC\outputs\tables
echo rerun started %date% %time% >> "%T%\_run_status.txt"
for %%N in (01_currency_payment_analysis 03_anomalies_accounts_details 04_integration_validation) do (
  echo running %%N >> "%T%\_run_status.txt"
  "%PY%" -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 %%N.ipynb >> "%T%\_run_log.txt" 2>&1 || (echo FAILED %%N >> "%T%\_run_status.txt" & exit /b 1)
  echo done %%N >> "%T%\_run_status.txt"
)
echo RERUN DONE %date% %time% >> "%T%\_run_status.txt"
