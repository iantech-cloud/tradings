"""
Database initialization script
Creates all tables and sets up initial data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import *
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database with all tables"""
    try:
        with app.app_context():
            logger.info("Creating database tables...")
            
            # Drop all tables (be careful in production!)
            db.drop_all()
            
            # Create all tables
            db.create_all()
            
            logger.info("Database tables created successfully!")
            
            # Create initial performance records for each symbol
            create_initial_performance_records()
            
            logger.info("Database initialization completed!")
            
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

def create_initial_performance_records():
    """Create initial performance tracking records"""
    try:
        from config import Config
        config = Config()
        
        for symbol in config.SUPPORTED_PAIRS:
            # Create initial performance record
            performance = SystemPerformance(
                date=datetime.utcnow().date(),
                symbol=symbol,
                total_signals=0,
                winning_signals=0,
                losing_signals=0,
                win_rate=0.0,
                total_pnl=0.0,
                average_win=0.0,
                average_loss=0.0,
                profit_factor=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0
            )
            
            db.session.add(performance)
        
        db.session.commit()
        logger.info(f"Created initial performance records for {len(config.SUPPORTED_PAIRS)} symbols")
        
    except Exception as e:
        logger.error(f"Error creating initial performance records: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    init_database()
