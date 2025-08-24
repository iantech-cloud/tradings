@echo off
REM Quick start script for Windows

echo 🚀 Starting Flask Trading System...

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Virtual environment not found. Running setup...
    python setup_local.py
)

REM Activate virtual environment and start system
call venv\Scripts\activate
python start_system.py
