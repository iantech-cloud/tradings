# Flask Trading System

A comprehensive Flask-based trading system that generates real-time and historically validated trading signals for major forex pairs, Gold, and Bitcoin with full transparency and automated journaling.

## 🚀 Features

- **Real-time Signal Generation**: BUY, SELL, HOLD signals with detailed reasoning
- **Multi-Asset Support**: EUR/USD, GBP/USD, USD/JPY, USD/CAD, AUD/USD, Gold (XAU/USD), Bitcoin (BTC/USD)
- **Technical Analysis**: 20+ indicators including RSI, MACD, Bollinger Bands, Stochastic, etc.
- **Smart Money Concepts**: Market structure, order blocks, fair value gaps, liquidity zones
- **Telegram Integration**: Automated signal delivery with detailed explanations
- **Auto-Journaling**: Complete trade logging and performance tracking
- **Professional Dashboard**: Real-time charts, analytics, and system monitoring

## 📋 Prerequisites

- Python 3.11 or higher
- MySQL (optional, SQLite used by default)
- Telegram Bot Token (optional, for notifications)

## 🛠️ Local Installation

### Option 1: Automated Setup (Recommended)

\`\`\`bash
# Clone or download the project
cd flask-trading-system

# Run the automated setup script
python setup_local.py
\`\`\`

### Option 2: Manual Setup

1. **Create Virtual Environment**
\`\`\`bash
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
\`\`\`

2. **Install Dependencies**
\`\`\`bash
pip install --upgrade pip
pip install -r requirements.txt
\`\`\`

3. **Environment Configuration**
\`\`\`bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API keys
nano .env  # or use your preferred editor
\`\`\`

4. **Database Setup**
\`\`\`bash
# Initialize database
python scripts/init_database.py

# Seed sample data (optional)
python scripts/seed_sample_data.py
\`\`\`

5. **Run Application**
\`\`\`bash
python app.py
\`\`\`

## 🔧 Configuration

### Required API Keys

1. **Alpha Vantage** (Free): https://www.alphavantage.co/support/#api-key
2. **Currency Layer** (Free): https://currencylayer.com/signup/free
3. **Twelve Data** (Free): https://twelvedata.com/pricing

### Optional Telegram Setup

1. Create a Telegram bot via @BotFather
2. Get your chat ID by messaging @userinfobot
3. Add credentials to `.env` file

### Environment Variables

\`\`\`env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
DATABASE_URL=sqlite:///trading_system.db

# API Keys
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
CURRENCY_LAYER_API_KEY=your-currency-layer-key
TWELVE_DATA_API_KEY=your-twelve-data-key

# Telegram (Optional)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
\`\`\`

## 🚀 Running the System

### Start Main Application
\`\`\`bash
python app.py
# Access dashboard at http://localhost:5000
\`\`\`

### Start Background Services
\`\`\`bash
# Data collection service
python data_acquisition/scheduler.py

# Signal generation service
python signal_generation/scheduler.py

# Telegram notifications
python telegram_bot/scheduler.py
\`\`\`

### Development Mode
\`\`\`bash
# Run with auto-reload
export FLASK_ENV=development
python app.py
\`\`\`

## 📊 Usage

1. **Dashboard**: View real-time market data, signals, and performance metrics
2. **Signals Page**: Review historical signals with detailed reasoning
3. **Performance**: Analyze system performance and trading statistics
4. **Settings**: Configure trading parameters and API settings

## 🧪 Testing

\`\`\`bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/test_indicators.py
python -m pytest tests/test_signals.py
\`\`\`

## 📁 Project Structure

\`\`\`
flask-trading-system/
├── app.py                      # Main Flask application
├── main.py                     # Production entry point
├── config.py                   # Configuration settings
├── models.py                   # Database models
├── routes.py                   # API routes
├── requirements.txt            # Python dependencies
├── data_acquisition/           # Data fetching modules
├── technical_analysis/         # Indicators and analysis
├── signal_generation/          # Signal generation engine
├── telegram_bot/              # Telegram integration
├── journaling/                # Performance tracking
├── templates/                 # HTML templates
├── static/                    # CSS, JS, images
└── scripts/                   # Database and utility scripts
\`\`\`

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated
2. **Database Errors**: Run `python scripts/init_database.py`
3. **API Errors**: Check API keys in `.env` file
4. **Port Conflicts**: Change port in `app.py` if 5000 is in use

### Performance Optimization

1. **Database**: Use MySQL for production instead of SQLite
2. **Caching**: Redis recommended for high-frequency trading
3. **Monitoring**: Check logs in `logs/` directory

## 📈 Production Deployment

The system is configured for Vercel deployment with `vercel.json`. For other platforms:

1. **Heroku**: Use `Procfile` with gunicorn
2. **AWS**: Deploy with Elastic Beanstalk or Lambda
3. **Docker**: Use provided Dockerfile

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## ⚠️ Disclaimer

This trading system is for educational and research purposes. Always perform your own analysis and risk management. Past performance does not guarantee future results.
\`\`\`

```txt file="" isHidden
