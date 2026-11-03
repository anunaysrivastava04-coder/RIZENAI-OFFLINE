@echo off
rem RIZEN OFFLINE AI - open the chat straight in your browser
rem Run start.bat once first (setup). After that, use this file to open the chat quickly.
setlocal
title RIZEN OFFLINE AI - open
cd /d "%~dp0"
set "URL=http://127.0.0.1:7860"
set "VENV_PY=.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
  echo RIZEN OFFLINE AI is not set up yet.
  echo Run start.bat first. It installs everything once.
  pause
  exit /b 1
)

rem Already running? Then just open the link.
curl.exe -s -o nul --max-time 2 "%URL%/api/status" >nul 2>&1
if not errorlevel 1 goto :open

if not exist "models\Qwen3-8B-Q4_K_M.gguf" (
  echo The Qwen3-8B model is not downloaded yet.
  echo Run start.bat once while connected to the internet.
  pause
  exit /b 1
)

echo Starting RIZEN OFFLINE AI in a small window...
set "RIZEN_NO_BROWSER=1"
start "RIZEN OFFLINE AI server" /min "%VENV_PY%" app.py

set /a WAIT=0

:wait
ping -n 2 127.0.0.1 >nul
curl.exe -s -o nul --max-time 2 "%URL%/api/status" >nul 2>&1
if not errorlevel 1 goto :open
set /a WAIT+=1
if %WAIT% GEQ 90 goto :too_slow
goto :wait

:open
echo Opening %URL% in your browser...
start "" "%URL%"
exit /b 0

:too_slow
echo The app did not answer within 90 seconds.
echo Open the minimized "RIZEN OFFLINE AI server" window on the taskbar to read the message.
pause
exit /b 1
