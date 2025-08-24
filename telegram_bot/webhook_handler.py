"""
Webhook handler for Telegram bot interactions
"""

import logging
from flask import Blueprint, request, jsonify
from typing import Dict, Any
import json

from .notification_manager import NotificationManager

logger = logging.getLogger(__name__)

telegram_bp = Blueprint('telegram', __name__, url_prefix='/telegram')

class WebhookHandler:
    """Handle Telegram webhook requests"""
    
    def __init__(self, notification_manager: NotificationManager):
        self.notification_manager = notification_manager
        self.setup_routes()
    
    def setup_routes(self):
        """Setup webhook routes"""
        
        @telegram_bp.route('/webhook', methods=['POST'])
        def handle_webhook():
            """Handle incoming webhook from Telegram"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'status': 'error', 'message': 'No data received'}), 400
                
                # Process the update
                result = self.process_update(data)
                
                if result:
                    return jsonify({'status': 'ok'})
                else:
                    return jsonify({'status': 'error', 'message': 'Failed to process update'}), 500
                    
            except Exception as e:
                logger.error(f"Error handling webhook: {str(e)}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @telegram_bp.route('/status', methods=['GET'])
        def get_status():
            """Get bot status"""
            try:
                is_connected = self.notification_manager.bot_client.test_connection()
                return jsonify({
                    'status': 'online' if is_connected else 'offline',
                    'connected': is_connected,
                    'queue_size': self.notification_manager.notification_queue.qsize()
                })
            except Exception as e:
                logger.error(f"Error getting status: {str(e)}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
    
    def process_update(self, update: Dict[str, Any]) -> bool:
        """Process incoming Telegram update"""
        try:
            # Handle different types of updates
            if 'message' in update:
                return self.handle_message(update['message'])
            elif 'callback_query' in update:
                return self.handle_callback_query(update['callback_query'])
            else:
                logger.info(f"Unhandled update type: {list(update.keys())}")
                return True
                
        except Exception as e:
            logger.error(f"Error processing update: {str(e)}")
            return False
    
    def handle_message(self, message: Dict[str, Any]) -> bool:
        """Handle incoming message"""
        try:
            chat_id = str(message['chat']['id'])
            text = message.get('text', '').strip()
            
            # Handle commands
            if text.startswith('/'):
                return self.handle_command(text, chat_id)
            else:
                # Handle regular messages
                logger.info(f"Received message from {chat_id}: {text}")
                return True
                
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            return False
    
    def handle_command(self, command: str, chat_id: str) -> bool:
        """Handle bot commands"""
        try:
            command = command.lower().split()[0]
            
            if command == '/start':
                welcome_message = """
🤖 <b>Welcome to Flask Trading System!</b>

I'll send you real-time trading signals with detailed analysis for:
• EUR/USD, GBP/USD, USD/JPY, USD/CAD, AUD/USD
• Gold (XAU/USD)
• Bitcoin (BTC/USD)

<b>Available Commands:</b>
/status - Get system status
/performance - Get recent performance
/settings - View notification settings
/help - Show this help message

Happy trading! 📈
"""
                self.notification_manager.bot_client.send_message(welcome_message, chat_id)
                
            elif command == '/status':
                self.notification_manager.send_system_status(chat_id=chat_id)
                
            elif command == '/performance':
                self.notification_manager.send_performance_update(chat_id=chat_id)
                
            elif command == '/settings':
                settings_message = self._format_settings_message()
                self.notification_manager.bot_client.send_message(settings_message, chat_id)
                
            elif command == '/help':
                help_message = """
<b>🤖 Flask Trading System Commands:</b>

/start - Welcome message and setup
/status - Current system status
/performance - Recent trading performance
/settings - View notification settings
/help - Show this help message

<b>📊 What you'll receive:</b>
• Real-time trading signals with detailed reasoning
• Performance updates every hour
• Market alerts for high volatility or breakouts
• System status updates

<b>🔧 Features:</b>
• Technical indicators analysis
• Smart Money Concepts (SMC)
• Risk management with SL/TP
• Transparent signal reasoning

For support, contact the system administrator.
"""
                self.notification_manager.bot_client.send_message(help_message, chat_id)
                
            else:
                unknown_message = f"Unknown command: {command}\nUse /help to see available commands."
                self.notification_manager.bot_client.send_message(unknown_message, chat_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling command {command}: {str(e)}")
            return False
    
    def handle_callback_query(self, callback_query: Dict[str, Any]) -> bool:
        """Handle callback query from inline keyboards"""
        try:
            # This would handle inline keyboard callbacks
            # For now, just acknowledge the callback
            logger.info(f"Received callback query: {callback_query.get('data')}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling callback query: {str(e)}")
            return False
    
    def _format_settings_message(self) -> str:
        """Format current settings for display"""
        settings = self.notification_manager.settings
        
        message = "<b>🔧 Notification Settings:</b>\n\n"
        
        settings_display = {
            'send_signals': 'Trading Signals',
            'send_performance_updates': 'Performance Updates',
            'send_market_alerts': 'Market Alerts',
            'send_system_status': 'System Status',
            'send_errors': 'Error Notifications'
        }
        
        for key, display_name in settings_display.items():
            status = "✅ Enabled" if settings.get(key, False) else "❌ Disabled"
            message += f"• {display_name}: {status}\n"
        
        message += f"\n<b>⏱️ Update Intervals:</b>\n"
        message += f"• Performance Updates: {settings.get('performance_update_interval', 3600) // 60} minutes\n"
        message += f"• Status Updates: {settings.get('status_update_interval', 21600) // 3600} hours\n"
        
        return message
