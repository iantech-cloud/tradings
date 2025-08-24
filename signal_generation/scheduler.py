"""
Scheduler for automated signal generation
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from .signal_engine import SignalEngine
from config import Config

logger = logging.getLogger(__name__)

class SignalScheduler:
    """Scheduler for automated signal generation"""
    
    def __init__(self, signal_engine: SignalEngine, config: Config):
        self.signal_engine = signal_engine
        self.config = config
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def start(self):
        """Start the signal generation scheduler"""
        if self.is_running:
            logger.warning("Signal scheduler is already running")
            return
        
        # Schedule signal generation for forex pairs (every 5 minutes)
        forex_pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CAD', 'AUD/USD']
        self.scheduler.add_job(
            func=self._generate_forex_signals,
            trigger=IntervalTrigger(seconds=self.config.FOREX_UPDATE_INTERVAL),
            id='forex_signals',
            name='Generate Forex Signals',
            args=[forex_pairs]
        )
        
        # Schedule signal generation for crypto/gold (every 2 minutes)
        crypto_symbols = ['XAU/USD', 'BTC/USD']
        self.scheduler.add_job(
            func=self._generate_crypto_signals,
            trigger=IntervalTrigger(seconds=120),  # 2 minutes for more frequent crypto signals
            id='crypto_signals',
            name='Generate Crypto/Gold Signals',
            args=[crypto_symbols]
        )
        
        # Schedule performance summary updates (every hour)
        self.scheduler.add_job(
            func=self._update_performance_summary,
            trigger=IntervalTrigger(hours=1),
            id='performance_update',
            name='Update Performance Summary'
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("Signal generation scheduler started successfully")
    
    def stop(self):
        """Stop the signal generation scheduler"""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Signal generation scheduler stopped")
    
    def _generate_forex_signals(self, symbols):
        """Generate signals for forex pairs"""
        logger.info(f"Generating signals for {len(symbols)} forex pairs")
        
        for symbol in symbols:
            try:
                signal = self.signal_engine.generate_signal(symbol)
                if signal and signal['signal'] != 'HOLD':
                    logger.info(f"Generated {signal['signal']} signal for {symbol}")
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {str(e)}")
    
    def _generate_crypto_signals(self, symbols):
        """Generate signals for crypto/gold"""
        logger.info(f"Generating signals for {len(symbols)} crypto/gold symbols")
        
        for symbol in symbols:
            try:
                signal = self.signal_engine.generate_signal(symbol)
                if signal and signal['signal'] != 'HOLD':
                    logger.info(f"Generated {signal['signal']} signal for {symbol}")
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {str(e)}")
    
    def _update_performance_summary(self):
        """Update performance summary"""
        logger.info("Updating signal performance summary")
        try:
            summary = self.signal_engine.get_signal_performance_summary()
            logger.info(f"Performance summary: {summary.get('total_signals', 0)} signals, "
                       f"{summary.get('win_rate', 0):.1f}% win rate")
        except Exception as e:
            logger.error(f"Error updating performance summary: {str(e)}")
    
    def get_scheduler_status(self):
        """Get status of signal generation scheduler"""
        if not self.is_running:
            return {"status": "stopped", "jobs": []}
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "status": "running",
            "jobs": jobs
        }
