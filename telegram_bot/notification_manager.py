"""
Notification Manager for coordinating Telegram notifications
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import threading
from queue import Queue, Empty
import time

from .bot_client import TelegramBotClient
from .message_formatter import MessageFormatter
from app import db
from models import TradingSignals, SystemPerformance

logger = logging.getLogger(__name__)

class NotificationManager:
    """Manages all Telegram notifications for the trading system"""
    
    def __init__(self, bot_token: str, default_chat_id: str = None):
        self.bot_client = TelegramBotClient(bot_token, default_chat_id)
        self.formatter = MessageFormatter()
        self.notification_queue = Queue()
        self.is_running = False
        self.worker_thread = None
        self.rate_limit_delay = 1  # seconds between messages
        self.last_message_time = 0
        
        # Notification settings
        self.settings = {
            'send_signals': True,
            'send_performance_updates': True,
            'send_market_alerts': True,
            'send_system_status': True,
            'send_errors': True,
            'performance_update_interval': 3600,  # 1 hour
            'status_update_interval': 21600,  # 6 hours
        }
        
        # Track last notifications to avoid spam
        self.last_notifications = {
            'performance_update': None,
            'status_update': None,
        }
    
    def start(self):
        """Start the notification manager"""
        if self.is_running:
            logger.warning("Notification manager is already running")
            return
        
        # Test bot connection
        if not self.bot_client.test_connection():
            logger.error("Failed to connect to Telegram bot")
            return False
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        logger.info("Notification manager started successfully")
        return True
    
    def stop(self):
        """Stop the notification manager"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Notification manager stopped")
    
    def send_trading_signal(self, signal_data: Dict[str, Any], chat_id: str = None) -> bool:
        """Send trading signal notification"""
        if not self.settings['send_signals']:
            return True
        
        try:
            message = self.formatter.format_trading_signal(signal_data)
            return self._queue_notification('signal', message, chat_id)
        except Exception as e:
            logger.error(f"Error sending trading signal: {str(e)}")
            return False
    
    def send_performance_update(self, performance_data: Dict[str, Any] = None, chat_id: str = None) -> bool:
        """Send performance update notification"""
        if not self.settings['send_performance_updates']:
            return True
        
        # Check if enough time has passed since last update
        now = datetime.utcnow()
        last_update = self.last_notifications.get('performance_update')
        if last_update and (now - last_update).seconds < self.settings['performance_update_interval']:
            return True
        
        try:
            if not performance_data:
                performance_data = self._get_recent_performance()
            
            message = self.formatter.format_performance_update(performance_data)
            success = self._queue_notification('performance', message, chat_id)
            
            if success:
                self.last_notifications['performance_update'] = now
            
            return success
        except Exception as e:
            logger.error(f"Error sending performance update: {str(e)}")
            return False
    
    def send_market_alert(self, alert_data: Dict[str, Any], chat_id: str = None) -> bool:
        """Send market alert notification"""
        if not self.settings['send_market_alerts']:
            return True
        
        try:
            message = self.formatter.format_market_alert(alert_data)
            return self._queue_notification('alert', message, chat_id, priority=True)
        except Exception as e:
            logger.error(f"Error sending market alert: {str(e)}")
            return False
    
    def send_system_status(self, status_data: Dict[str, Any] = None, chat_id: str = None) -> bool:
        """Send system status notification"""
        if not self.settings['send_system_status']:
            return True
        
        # Check if enough time has passed since last update
        now = datetime.utcnow()
        last_update = self.last_notifications.get('status_update')
        if last_update and (now - last_update).seconds < self.settings['status_update_interval']:
            return True
        
        try:
            if not status_data:
                status_data = self._get_system_status()
            
            message = self.formatter.format_system_status(status_data)
            success = self._queue_notification('status', message, chat_id)
            
            if success:
                self.last_notifications['status_update'] = now
            
            return success
        except Exception as e:
            logger.error(f"Error sending system status: {str(e)}")
            return False
    
    def send_error_notification(self, error_data: Dict[str, Any], chat_id: str = None) -> bool:
        """Send error notification"""
        if not self.settings['send_errors']:
            return True
        
        try:
            message = self.formatter.format_error_notification(error_data)
            return self._queue_notification('error', message, chat_id, priority=True)
        except Exception as e:
            logger.error(f"Error sending error notification: {str(e)}")
            return False
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """Update notification settings"""
        self.settings.update(new_settings)
        logger.info(f"Notification settings updated: {new_settings}")
    
    def _queue_notification(self, notification_type: str, message: str, chat_id: str = None, priority: bool = False) -> bool:
        """Queue a notification for sending"""
        try:
            notification = {
                'type': notification_type,
                'message': message,
                'chat_id': chat_id,
                'timestamp': datetime.utcnow(),
                'priority': priority
            }
            
            if priority:
                # For priority messages, add to front of queue
                temp_queue = Queue()
                temp_queue.put(notification)
                while not self.notification_queue.empty():
                    try:
                        temp_queue.put(self.notification_queue.get_nowait())
                    except Empty:
                        break
                self.notification_queue = temp_queue
            else:
                self.notification_queue.put(notification)
            
            return True
        except Exception as e:
            logger.error(f"Error queuing notification: {str(e)}")
            return False
    
    def _worker_loop(self):
        """Main worker loop for processing notifications"""
        logger.info("Notification worker loop started")
        
        while self.is_running:
            try:
                # Get notification from queue with timeout
                try:
                    notification = self.notification_queue.get(timeout=1)
                except Empty:
                    continue
                
                # Rate limiting
                current_time = time.time()
                time_since_last = current_time - self.last_message_time
                if time_since_last < self.rate_limit_delay:
                    time.sleep(self.rate_limit_delay - time_since_last)
                
                # Send notification
                success = self.bot_client.send_message(
                    notification['message'],
                    notification['chat_id']
                )
                
                if success:
                    logger.info(f"Sent {notification['type']} notification successfully")
                else:
                    logger.error(f"Failed to send {notification['type']} notification")
                
                self.last_message_time = time.time()
                self.notification_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in notification worker loop: {str(e)}")
                time.sleep(1)
        
        logger.info("Notification worker loop stopped")
    
    def _get_recent_performance(self) -> Dict[str, Any]:
        """Get recent performance data"""
        try:
            # Get signals from last 24 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            recent_signals = TradingSignals.query.filter(
                TradingSignals.timestamp >= cutoff_time,
                TradingSignals.outcome.isnot(None)
            ).all()
            
            if not recent_signals:
                return {
                    'period': '24h',
                    'win_rate': 0,
                    'total_signals': 0,
                    'total_pnl': 0,
                    'best_performing_pair': 'N/A'
                }
            
            # Calculate metrics
            wins = [s for s in recent_signals if (s.pnl or 0) > 0]
            win_rate = len(wins) / len(recent_signals) * 100
            total_pnl = sum([s.pnl or 0 for s in recent_signals])
            
            # Find best performing pair
            pair_performance = {}
            for signal in recent_signals:
                if signal.symbol not in pair_performance:
                    pair_performance[signal.symbol] = 0
                pair_performance[signal.symbol] += signal.pnl or 0
            
            best_pair = max(pair_performance.items(), key=lambda x: x[1])[0] if pair_performance else 'N/A'
            
            return {
                'period': '24h',
                'win_rate': win_rate,
                'total_signals': len(recent_signals),
                'total_pnl': total_pnl,
                'best_performing_pair': best_pair
            }
            
        except Exception as e:
            logger.error(f"Error getting recent performance: {str(e)}")
            return {}
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        try:
            # This would be implemented based on your system monitoring
            return {
                'status': 'ONLINE',
                'uptime': '24h 15m',
                'active_pairs': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CAD', 'AUD/USD', 'XAU/USD', 'BTC/USD'],
                'last_signal_time': '5 minutes ago',
                'api_status': {
                    'Alpha Vantage': {'status': 'OK'},
                    'Currency Layer': {'status': 'OK'},
                    'Twelve Data': {'status': 'OK'}
                }
            }
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {}
