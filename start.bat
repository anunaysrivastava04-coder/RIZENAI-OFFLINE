@echo off
rem RIZEN OFFLINE AI - automatic setup and launch for Windows
setlocal
title RIZEN OFFLINE AI
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PY="
set "VENV_PY=.venv\Scripts\python.exe"
set "MODEL=models\Qwen3-8B-Q4_K_M.gguf"

echo.
echo ================================================
echo   RIZEN OFFLINE AI - automatic setup
echo ================================================
echo.

py -3 --version >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if not defined PY (
  python --version >nul 2>&1
  if not errorlevel 1 set "PY=python"
)
if not defined PY goto :no_python
echo Found Python: %PY%

if not exist "%VENV_PY%" (
  echo.
  echo [1/4] Creating the Python environment. This is a one-time step.
  %PY% -m venv .venv
  if errorlevel 1 goto :failed
)

if not exist ".venv\rizen_ready.txt" (
  echo.
  echo [2/4] Installing the web server and the Qwen engine.
  echo        The AI engine can take a few minutes the first time. Please wait.
  "%VENV_PY%" -m pip install --upgrade pip >nul
  "%VENV_PY%" -m pip install -r requirements.txt
  if errorlevel 1 goto :failed
  echo ready> ".venv\rizen_ready.txt"
)

if not exist "%MODEL%" (
  echo.
  echo [3/4] Downloading the Qwen3-8B model. It is about 5 GB and happens only once.
  echo        Keep this window open. If the download stops, run start.bat again and it resumes.
  "%VENV_PY%" download_model.py
  if errorlevel 1 goto :failed
)

echo.
echo [4/4] Starting RIZEN OFFLINE AI. Your browser will open in a moment.
echo        Keep this window open while you chat. Press Ctrl+C to stop the app.
echo.
"%VENV_PY%" app.py
echo.
echo RIZEN OFFLINE AI has stopped.
pause
exit /b 0

:no_python
echo Python 3.10, 3.11 or 3.12 was not found on this computer.
echo Install it from https://www.python.org/downloads/
echo Tick "Add python.exe to PATH" during the install, then run start.bat again.
pause
exit /b 1

:failed
echo.
echo Setup stopped because of an error. Read the messages above.
echo Common fixes are listed in README.md under Troubleshooting.
pause
exit /b 1
