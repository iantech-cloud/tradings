import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql://username:password@localhost/trading_system')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys
    ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', 'S8TGJSEMXSZ7AVKD')
    CURRENCY_LAYER_API_KEY = os.environ.get('CURRENCY_LAYER_API_KEY', '98b6f093d586c1655625b63bf1a713fc')
    TWELVE_DATA_API_KEY = os.environ.get('TWELVE_DATA_API_KEY', 'ddfecc2b71d24284843bbdd231999d80')
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
    
    # Trading Configuration
    SUPPORTED_PAIRS = [
        'EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CAD', 'AUD/USD',
        'XAU/USD',  # Gold
        'BTC/USD'   # Bitcoin
    ]
    
    # Rate Limiting Configuration
    FOREX_UPDATE_INTERVAL = 300  # 5 minutes in seconds
    CRYPTO_UPDATE_INTERVAL = 30  # 30 seconds for BTC and Gold
    MAX_API_CALLS_PER_MINUTE = 5
    
    # Signal Generation Configuration
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    MACD_SIGNAL_THRESHOLD = 0.001
    BOLLINGER_BAND_PERIODS = 20

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
