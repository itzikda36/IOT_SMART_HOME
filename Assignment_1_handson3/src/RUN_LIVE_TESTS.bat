@echo off
setlocal
cd /d "%~dp0"
title Assignment 1 MQTT - Itzhak Davidov 6233

echo Installing paho-mqtt if needed...
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo ERROR: Python/pip dependency installation failed.
  pause
  exit /b 1
)

echo.
echo Running MQTT Tests 1-5 against broker.hivemq.com:1883...
echo This fixed runner uses unique client IDs, waits for SUBACK/DISCONNECT,
echo and retries transient broker connections automatically.
echo.
py mqtt_test_runner_6233.py

echo.
echo A copy of the output is saved in live_test_results_6233.txt
pause
endlocal
