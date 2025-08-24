"""
Seed database with sample data for testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import *
from datetime import datetime, timedelta
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_sample_data():
    """Seed database with sample market data and signals"""
    try:
        with app.app_context():
            logger.info("Seeding sample data...")
            
            # Sample symbols
            symbols = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'XAU/USD', 'BTC/USD']
            
            # Create sample market data (last 30 days)
            create_sample_market_data(symbols)
            
            # Create sample trading signals
            create_sample_signals(symbols)
            
            # Create sample performance data
            create_sample_performance_data(symbols)
            
            logger.info("Sample data seeded successfully!")
            
    except Exception as e:
        logger.error(f"Error seeding sample data: {str(e)}")
        raise

def create_sample_market_data(symbols):
    """Create sample market data"""
    logger.info("Creating sample market data...")
    
    base_prices = {
        'EUR/USD': 1.0850,
        'GBP/USD': 1.2650,
        'USD/JPY': 149.50,
        'XAU/USD': 2050.00,
        'BTC/USD': 43500.00
    }
    
    for symbol in symbols:
        base_price = base_prices.get(symbol, 1.0000)
        current_price = base_price
        
        # Generate 30 days of hourly data
        for i in range(30 * 24):
            timestamp = datetime.utcnow() - timedelta(hours=30*24-i)
            
            # Simulate price movement
            change_percent = random.uniform(-0.02, 0.02)  # ±2% change
            price_change = current_price * change_percent
            
            open_price = current_price
            high_price = current_price + abs(price_change) * random.uniform(0.5, 1.5)
            low_price = current_price - abs(price_change) * random.uniform(0.5, 1.5)
            close_price = current_price + price_change
            
            # Ensure high >= low
            if high_price < low_price:
                high_price, low_price = low_price, high_price
            
            # Ensure OHLC relationships
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            volume = random.randint(1000, 10000) if symbol in ['XAU/USD', 'BTC/USD'] else 0
            
            market_data = MarketData(
                symbol=symbol,
                timestamp=timestamp,
                open_price=round(open_price, 5),
                high_price=round(high_price, 5),
                low_price=round(low_price, 5),
                close_price=round(close_price, 5),
                volume=volume,
                source='sample_data'
            )
            
            db.session.add(market_data)
            current_price = close_price
        
        db.session.commit()
    
    logger.info(f"Created sample market data for {len(symbols)} symbols")

def create_sample_signals(symbols):
    """Create sample trading signals"""
    logger.info("Creating sample trading signals...")
    
    signal_types = ['BUY', 'SELL', 'HOLD']
    outcomes = ['profit', 'loss', 'breakeven']
    statuses = ['active', 'hit_tp', 'hit_sl', 'closed_manual']
    
    for symbol in symbols:
        # Create 20-50 signals per symbol over the last 30 days
        num_signals = random.randint(20, 50)
        
        for i in range(num_signals):
            timestamp = datetime.utcnow() - timedelta(
                hours=random.randint(1, 30*24)
            )
            
            signal_type = random.choice(signal_types)
            entry_price = random.uniform(1.0, 2000.0)  # Simplified for sample
            
            if signal_type != 'HOLD':
                stop_loss = entry_price * random.uniform(0.98, 1.02)
                take_profit = entry_price * random.uniform(0.98, 1.02)
                risk_reward = round(random.uniform(1.0, 3.0), 2)
            else:
                stop_loss = None
                take_profit = None
                risk_reward = None
            
            reasoning = f"Sample {signal_type} signal for {symbol} based on technical analysis confluence."
            confidence = round(random.uniform(60, 95), 1)
            
            status = random.choice(statuses)
            outcome = random.choice(outcomes) if status != 'active' else None
            pnl = round(random.uniform(-100, 200), 2) if outcome else 0.0
            
            signal = TradingSignals(
                symbol=symbol,
                timestamp=timestamp,
                signal_type=signal_type,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=risk_reward,
                reasoning=reasoning,
                confidence_score=confidence,
                rsi_value=random.uniform(20, 80),
                macd_value=random.uniform(-0.01, 0.01),
                trend_direction=random.choice(['bullish', 'bearish', 'neutral']),
                smc_confluence="Sample SMC analysis",
                status=status,
                outcome=outcome,
                pnl=pnl
            )
            
            db.session.add(signal)
    
    db.session.commit()
    logger.info(f"Created sample signals for {len(symbols)} symbols")

def create_sample_performance_data(symbols):
    """Create sample performance data"""
    logger.info("Creating sample performance data...")
    
    for symbol in symbols:
        # Create performance data for last 30 days
        for i in range(30):
            date = datetime.utcnow().date() - timedelta(days=i)
            
            total_signals = random.randint(0, 5)
            winning_signals = random.randint(0, total_signals)
            losing_signals = total_signals - winning_signals
            win_rate = (winning_signals / total_signals * 100) if total_signals > 0 else 0
            
            total_pnl = round(random.uniform(-50, 100), 2)
            average_win = round(random.uniform(10, 50), 2) if winning_signals > 0 else 0
            average_loss = round(random.uniform(-30, -5), 2) if losing_signals > 0 else 0
            
            profit_factor = abs(average_win / average_loss) if average_loss != 0 else 0
            max_drawdown = round(random.uniform(0, 20), 2)
            sharpe_ratio = round(random.uniform(-1, 2), 2)
            
            performance = SystemPerformance(
                date=date,
                symbol=symbol,
                total_signals=total_signals,
                winning_signals=winning_signals,
                losing_signals=losing_signals,
                win_rate=win_rate,
                total_pnl=total_pnl,
                average_win=average_win,
                average_loss=average_loss,
                profit_factor=profit_factor,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio
            )
            
            db.session.add(performance)
    
    db.session.commit()
    logger.info(f"Created sample performance data for {len(symbols)} symbols")

if __name__ == "__main__":
    seed_sample_data()
