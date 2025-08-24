"""
Scheduler for automated data updates
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from .data_manager import DataManager
from config import Config

logger = logging.getLogger(__name__)

class DataScheduler:
    """Scheduler for automated data collection"""
    
    def __init__(self, data_manager: DataManager, config: Config):
        self.data_manager = data_manager
        self.config = config
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Schedule forex updates (every 5 minutes)
        forex_pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CAD', 'AUD/USD']
        self.scheduler.add_job(
            func=self._update_forex_data,
            trigger=IntervalTrigger(seconds=self.config.FOREX_UPDATE_INTERVAL),
            id='forex_updates',
            name='Update Forex Data',
            args=[forex_pairs]
        )
        
        # Schedule crypto/gold updates (every 30 seconds)
        crypto_symbols = ['XAU/USD', 'BTC/USD']
        self.scheduler.add_job(
            func=self._update_crypto_data,
            trigger=IntervalTrigger(seconds=self.config.CRYPTO_UPDATE_INTERVAL),
            id='crypto_updates',
            name='Update Crypto/Gold Data',
            args=[crypto_symbols]
        )
        
        # Schedule cache cleanup (every hour)
        self.scheduler.add_job(
            func=self._cleanup_cache,
            trigger=IntervalTrigger(hours=1),
            id='cache_cleanup',
            name='Cache Cleanup'
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("Data scheduler started successfully")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Data scheduler stopped")
    
    def _update_forex_data(self, symbols):
        """Update forex data"""
        logger.info(f"Updating forex data for {len(symbols)} symbols")
        
        for symbol in symbols:
            try:
                data = self.data_manager.get_real_time_data(symbol, force_refresh=True)
                if data:
                    logger.debug(f"Updated {symbol}: {data['price']}")
                else:
                    logger.warning(f"Failed to update {symbol}")
            except Exception as e:
                logger.error(f"Error updating {symbol}: {str(e)}")
    
    def _update_crypto_data(self, symbols):
        """Update crypto/gold data"""
        logger.info(f"Updating crypto/gold data for {len(symbols)} symbols")
        
        for symbol in symbols:
            try:
                data = self.data_manager.get_real_time_data(symbol, force_refresh=True)
                if data:
                    logger.debug(f"Updated {symbol}: {data['price']}")
                else:
                    logger.warning(f"Failed to update {symbol}")
            except Exception as e:
                logger.error(f"Error updating {symbol}: {str(e)}")
    
    def _cleanup_cache(self):
        """Clean up expired cache entries"""
        logger.info("Running cache cleanup")
        try:
            self.data_manager.cache.cleanup_expired()
        except Exception as e:
            logger.error(f"Error during cache cleanup: {str(e)}")
    
    def get_job_status(self):
        """Get status of scheduled jobs"""
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
