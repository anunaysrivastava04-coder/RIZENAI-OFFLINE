#!/usr/bin/env bash
# RIZEN OFFLINE AI - automatic setup and launch for macOS and Linux
set -e
cd "$(dirname "$0")"

echo
echo "================================================"
echo "  RIZEN OFFLINE AI - automatic setup"
echo "================================================"
echo

PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "Python 3 was not found. Install Python 3.10 to 3.12 from https://www.python.org/downloads/"
  echo "then run ./start.sh again."
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "[1/4] Creating the Python environment. This is a one-time step."
  "$PY" -m venv .venv
fi

if [ ! -f ".venv/rizen_ready.txt" ]; then
  echo "[2/4] Installing the web server and the Qwen engine."
  echo "      The AI engine can take a few minutes the first time. Please wait."
  .venv/bin/python -m pip install --upgrade pip >/dev/null
  .venv/bin/python -m pip install -r requirements.txt
  echo "ready" > .venv/rizen_ready.txt
fi

if [ ! -f "models/Qwen3-8B-Q4_K_M.gguf" ]; then
  echo "[3/4] Downloading the Qwen3-8B model. It is about 5 GB and happens only once."
  .venv/bin/python download_model.py
fi

echo "[4/4] Starting RIZEN OFFLINE AI. Your browser will open in a moment."
echo "      Press Ctrl+C to stop the app."
exec .venv/bin/python app.py
