@echo off
REM Runs the four notebooks in the required order: 04 -> 01 -> 02 -> 03 -> 04, logging progress
cd /d C:\cjy\y3s2\UMDAC\notebooks
set PY=%USERPROFILE%\anaconda3\python.exe
set T=C:\cjy\y3s2\UMDAC\outputs\tables
echo started %date% %time% > "%T%\_run_status.txt"
for %%N in (04_integration_validation 01_currency_payment_analysis 02_member2_analysis 03_anomalies_accounts_details 04_integration_validation) do (
  echo running %%N >> "%T%\_run_status.txt"
  "%PY%" -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 %%N.ipynb >> "%T%\_run_log.txt" 2>&1 || (echo FAILED %%N >> "%T%\_run_status.txt" & exit /b 1)
  echo done %%N >> "%T%\_run_status.txt"
)
echo ALL DONE %date% %time% >> "%T%\_run_status.txt"
