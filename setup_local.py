#!/usr/bin/env python3
"""
Local setup script for Flask Trading System
Run this script to set up the project locally on your laptop
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}: {e.stderr}")
        return None

def check_python_version():
    """Check if Python 3.11+ is installed"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} found. Python 3.11+ required")
        return False

def create_env_file():
    """Create .env file with default configuration"""
    env_content = """# Flask Trading System Environment Variables

# Flask Configuration
SECRET_KEY=your-secret-key-change-in-production
FLASK_ENV=development
DATABASE_URL=sqlite:///trading_system.db

# API Keys (Replace with your actual keys)
ALPHA_VANTAGE_API_KEY=S8TGJSEMXSZ7AVKD
CURRENCY_LAYER_API_KEY=98b6f093d586c1655625b63bf1a713fc
TWELVE_DATA_API_KEY=ddfecc2b71d24284843bbdd231999d80

# Telegram Bot Configuration (Optional)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id

# MySQL Database (Optional - for production)
# DATABASE_URL=mysql://username:password@localhost/trading_system
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with default configuration")
    else:
        print("ℹ️  .env file already exists")

def main():
    """Main setup function"""
    print("🚀 Flask Trading System - Local Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        print("\n📥 Please install Python 3.11+ from https://python.org")
        return
    
    # Create virtual environment
    if not os.path.exists('venv'):
        run_command('python -m venv venv', 'Creating virtual environment')
    else:
        print("ℹ️  Virtual environment already exists")
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = 'venv\\Scripts\\activate && '
    else:  # Unix/Linux/macOS
        activate_cmd = 'source venv/bin/activate && '
    
    run_command(f'{activate_cmd}pip install --upgrade pip', 'Upgrading pip')
    run_command(f'{activate_cmd}pip install -r requirements.txt', 'Installing Python dependencies')
    
    # Create environment file
    create_env_file()
    
    # Initialize database
    run_command(f'{activate_cmd}python scripts/init_database.py', 'Initializing database')
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Activate virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    print("2. Update .env file with your API keys")
    print("3. Run the application:")
    print("   python app.py")
    print("4. Open http://localhost:5000 in your browser")
    
    print("\n📚 Additional Commands:")
    print("• Run tests: python -m pytest")
    print("• Start data collection: python data_acquisition/scheduler.py")
    print("• Start Telegram bot: python telegram_bot/scheduler.py")

if __name__ == '__main__':
    main()
