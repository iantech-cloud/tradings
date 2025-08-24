#!/usr/bin/env python3
"""
Flask Trading System Startup Script
Starts all components of the trading system
"""

import os
import subprocess
import sys
import time
import threading
from pathlib import Path

def run_service(command, service_name):
    """Run a service in the background"""
    print(f"🚀 Starting {service_name}...")
    try:
        process = subprocess.Popen(command, shell=True)
        return process
    except Exception as e:
        print(f"❌ Failed to start {service_name}: {e}")
        return None

def check_environment():
    """Check if environment is properly set up"""
    if not os.path.exists('.env'):
        print("❌ .env file not found. Run 'python setup_local.py' first")
        return False
    
    if not os.path.exists('venv'):
        print("❌ Virtual environment not found. Run 'python setup_local.py' first")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🎯 Flask Trading System - Startup")
    print("=" * 40)
    
    if not check_environment():
        return
    
    # Determine activation command based on OS
    if os.name == 'nt':  # Windows
        activate_cmd = 'venv\\Scripts\\activate && '
    else:  # Unix/Linux/macOS
        activate_cmd = 'source venv/bin/activate && '
    
    processes = []
    
    try:
        # Start main Flask application
        flask_process = run_service(f'{activate_cmd}python app.py', 'Flask Web Application')
        if flask_process:
            processes.append(('Flask App', flask_process))
        
        time.sleep(3)  # Give Flask time to start
        
        # Start data acquisition service
        data_process = run_service(f'{activate_cmd}python data_acquisition/scheduler.py', 'Data Acquisition Service')
        if data_process:
            processes.append(('Data Service', data_process))
        
        # Start signal generation service
        signal_process = run_service(f'{activate_cmd}python signal_generation/scheduler.py', 'Signal Generation Service')
        if signal_process:
            processes.append(('Signal Service', signal_process))
        
        # Start Telegram bot (optional)
        telegram_process = run_service(f'{activate_cmd}python telegram_bot/scheduler.py', 'Telegram Bot Service')
        if telegram_process:
            processes.append(('Telegram Bot', telegram_process))
        
        print("\n✅ All services started successfully!")
        print("\n🌐 Access the dashboard at: http://localhost:5000")
        print("\n📊 Services running:")
        for name, _ in processes:
            print(f"  • {name}")
        
        print("\n⚠️  Press Ctrl+C to stop all services")
        
        # Wait for user interrupt
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping all services...")
            for name, process in processes:
                try:
                    process.terminate()
                    print(f"✅ Stopped {name}")
                except:
                    pass
            print("👋 All services stopped. Goodbye!")
    
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        # Clean up any started processes
        for name, process in processes:
            try:
                process.terminate()
            except:
                pass

if __name__ == '__main__':
    main()
