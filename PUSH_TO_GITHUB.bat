@echo off
setlocal
cd /d "%~dp0"
echo.
echo IOT_SMART_HOME - GitHub upload helper
echo.
where git >nul 2>&1
if errorlevel 1 (
  echo ERROR: Git is not installed or not on PATH.
  echo Install Git for Windows, then run this file again.
  pause
  exit /b 1
)
set /p REMOTE=Paste the EMPTY GitHub repository URL ending in .git: 
if "%REMOTE%"=="" exit /b 1
if not exist .git git init
git branch -M main
git add .
git commit -m "IoT Smart Home course project - Itzhak Davidov 6233"
git remote remove origin >nul 2>&1
git remote add origin %REMOTE%
git push -u origin main
if errorlevel 1 (
  echo.
  echo Push did not complete. Read the Git message above.
) else (
  echo.
  echo SUCCESS - repository uploaded.
)
pause
