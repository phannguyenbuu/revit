@echo off
title RevitAI Automation Hub Dashboard
cd /d "%~dp0"

echo =======================================================
echo   RevitAI Dashboard (Flask + Tailwind)
echo =======================================================
echo.

netstat -ano | findstr /R /C:":5000 " >nul 2>&1
if errorlevel 1 goto LAUNCH_SERVER

echo [THONG BAO] Dashboard da dang chay tren cong 5000!
echo Dang mo trinh duyet: http://127.0.0.1:5000
start http://127.0.0.1:5000
ping 127.0.0.1 -n 2 >nul
exit /b 0

:LAUNCH_SERVER
start "" cmd /c "ping 127.0.0.1 -n 3 >nul && start http://127.0.0.1:5000"
python "%~dp0web_dashboard.py"
pause
