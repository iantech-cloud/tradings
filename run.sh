#!/bin/bash
# Quick start script for Unix/Linux/macOS

echo "🚀 Starting Flask Trading System..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Running setup..."
    python3 setup_local.py
fi

# Activate virtual environment and start system
source venv/bin/activate
python start_system.py
