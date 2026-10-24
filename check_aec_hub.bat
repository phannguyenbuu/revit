@echo off
title AEC Multi-CAD Automation Hub (AutoCAD - 3ds Max - Revit)
cd /d "%~dp0"

netstat -ano | findstr /R /C:":5000 " >nul 2>&1
if errorlevel 1 goto START_DASH

REM Server da chay truoc do, mo giao dien tren trinh duyet
start http://127.0.0.1:5000
goto SHOW_STATUS

:START_DASH
echo [*] Dang tu dong khoi chay RevitAI Dashboard tren cong 5000...
start "RevitAI Automation Hub Dashboard" cmd /k "%~dp0run_dashboard.bat"
ping 127.0.0.1 -n 3 >nul

:SHOW_STATUS
python -X utf8 aec_hub.py
echo.
pause
