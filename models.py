from app import db
from datetime import datetime
from sqlalchemy import Index

class MarketData(db.Model):
    """Store real-time and historical market data"""
    __tablename__ = 'market_data'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    open_price = db.Column(db.Float, nullable=False)
    high_price = db.Column(db.Float, nullable=False)
    low_price = db.Column(db.Float, nullable=False)
    close_price = db.Column(db.Float, nullable=False)
    volume = db.Column(db.BigInteger, default=0)
    source = db.Column(db.String(20), nullable=False)  # alpha_vantage, currency_layer, twelve_data
    
    # Create composite index for efficient queries
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
    )

class TechnicalIndicators(db.Model):
    """Store calculated technical indicators"""
    __tablename__ = 'technical_indicators'
    
    id = db.Column(db.Integer, primary_key=True)
    market_data_id = db.Column(db.Integer, db.ForeignKey('market_data.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Trend Indicators
    sma_20 = db.Column(db.Float)
    sma_50 = db.Column(db.Float)
    ema_12 = db.Column(db.Float)
    ema_26 = db.Column(db.Float)
    macd = db.Column(db.Float)
    macd_signal = db.Column(db.Float)
    macd_histogram = db.Column(db.Float)
    
    # Momentum Indicators
    rsi = db.Column(db.Float)
    stochastic_k = db.Column(db.Float)
    stochastic_d = db.Column(db.Float)
    cci = db.Column(db.Float)
    williams_r = db.Column(db.Float)
    
    # Volatility Indicators
    bollinger_upper = db.Column(db.Float)
    bollinger_middle = db.Column(db.Float)
    bollinger_lower = db.Column(db.Float)
    atr = db.Column(db.Float)
    
    # Volume Indicators
    obv = db.Column(db.Float)
    ad_line = db.Column(db.Float)
    
    # Relationships
    market_data = db.relationship('MarketData', backref='indicators')

class SmartMoneyAnalysis(db.Model):
    """Store Smart Money Concepts analysis"""
    __tablename__ = 'smart_money_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    market_data_id = db.Column(db.Integer, db.ForeignKey('market_data.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Market Structure
    market_structure = db.Column(db.String(20))  # bullish, bearish, ranging
    bos_detected = db.Column(db.Boolean, default=False)  # Break of Structure
    choch_detected = db.Column(db.Boolean, default=False)  # Change of Character
    
    # Liquidity Zones
    liquidity_sweep = db.Column(db.Boolean, default=False)
    stop_hunt_level = db.Column(db.Float)
    
    # Order Blocks
    order_block_type = db.Column(db.String(10))  # bullish, bearish
    order_block_price = db.Column(db.Float)
    order_block_strength = db.Column(db.Float)
    
    # Fair Value Gaps
    fvg_detected = db.Column(db.Boolean, default=False)
    fvg_high = db.Column(db.Float)
    fvg_low = db.Column(db.Float)
    
    # Relationships
    market_data = db.relationship('MarketData', backref='smc_analysis')

class TradingSignals(db.Model):
    """Store generated trading signals with reasoning"""
    __tablename__ = 'trading_signals'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    signal_type = db.Column(db.String(10), nullable=False)  # BUY, SELL, HOLD
    entry_price = db.Column(db.Float, nullable=False)
    stop_loss = db.Column(db.Float)
    take_profit = db.Column(db.Float)
    risk_reward_ratio = db.Column(db.Float)
    
    # Signal Reasoning
    reasoning = db.Column(db.Text, nullable=False)
    confidence_score = db.Column(db.Float)  # 0-100
    
    # Technical Analysis Context
    rsi_value = db.Column(db.Float)
    macd_value = db.Column(db.Float)
    trend_direction = db.Column(db.String(10))  # bullish, bearish, neutral
    
    # SMC Context
    smc_confluence = db.Column(db.Text)
    
    # Signal Status
    status = db.Column(db.String(20), default='active')  # active, hit_tp, hit_sl, closed_manual
    outcome = db.Column(db.String(20))  # profit, loss, breakeven
    pnl = db.Column(db.Float, default=0.0)
    
    # Notification Status
    telegram_sent = db.Column(db.Boolean, default=False)
    telegram_message_id = db.Column(db.String(50))

class SystemPerformance(db.Model):
    """Track system performance metrics"""
    __tablename__ = 'system_performance'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    symbol = db.Column(db.String(10), nullable=False)
    
    # Daily Statistics
    total_signals = db.Column(db.Integer, default=0)
    winning_signals = db.Column(db.Integer, default=0)
    losing_signals = db.Column(db.Integer, default=0)
    win_rate = db.Column(db.Float, default=0.0)
    
    # P&L Tracking
    total_pnl = db.Column(db.Float, default=0.0)
    average_win = db.Column(db.Float, default=0.0)
    average_loss = db.Column(db.Float, default=0.0)
    profit_factor = db.Column(db.Float, default=0.0)
    
    # Risk Metrics
    max_drawdown = db.Column(db.Float, default=0.0)
    sharpe_ratio = db.Column(db.Float, default=0.0)
    
    # Create unique constraint
    __table_args__ = (
        db.UniqueConstraint('date', 'symbol', name='unique_daily_performance'),
    )

class APIUsage(db.Model):
    """Track API usage for rate limiting"""
    __tablename__ = 'api_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    api_provider = db.Column(db.String(20), nullable=False)  # alpha_vantage, currency_layer, twelve_data
    endpoint = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    response_time = db.Column(db.Float)  # in seconds
    status_code = db.Column(db.Integer)
    error_message = db.Column(db.Text)
