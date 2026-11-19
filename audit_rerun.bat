@echo off
REM Audit 19 Nov: (1) independent re-test of the principal rules on the FULL data, then (2) re-run notebooks 02, 03, 04
set PY=%USERPROFILE%\anaconda3\python.exe
set T=C:\cjy\y3s2\UMDAC\outputs\tables
set A=C:\cjy\y3s2\UMDAC\outputs\audit
echo audit started %date% %time% > "%A%\_audit_status.txt"
cd /d C:\cjy\y3s2\UMDAC
"%PY%" "%A%\verify_rules.py" "C:\cjy\y3s2\UMDAC\data\processed\payments_clean.parquet" - "%A%\independent_check_full.csv" > "%A%\verify_log.txt" 2>&1
echo verify exit %errorlevel% %date% %time% >> "%A%\_audit_status.txt"
call "C:\cjy\y3s2\UMDAC\rerun_02_03_04.bat"
echo audit done %date% %time% >> "%A%\_audit_status.txt"
