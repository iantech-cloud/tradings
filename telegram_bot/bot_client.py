"""
Telegram Bot Client for sending trading signals
"""

import logging
import requests
from typing import Dict, Any, Optional, List
import asyncio
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)

class TelegramBotClient:
    """Telegram Bot Client for sending trading notifications"""
    
    def __init__(self, bot_token: str, chat_id: str = None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def send_message(self, message: str, chat_id: str = None, parse_mode: str = 'HTML') -> bool:
        """Send message synchronously"""
        try:
            target_chat_id = chat_id or self.chat_id
            if not target_chat_id:
                logger.error("No chat_id provided")
                return False
            
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': target_chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Message sent successfully to chat {target_chat_id}")
                return True
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
    
    async def send_message_async(self, message: str, chat_id: str = None, parse_mode: str = 'HTML') -> bool:
        """Send message asynchronously"""
        try:
            target_chat_id = chat_id or self.chat_id
            if not target_chat_id:
                logger.error("No chat_id provided")
                return False
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': target_chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            async with self.session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    logger.info(f"Message sent successfully to chat {target_chat_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to send message: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending async message: {str(e)}")
            return False
    
    def send_photo(self, photo_path: str, caption: str = "", chat_id: str = None) -> bool:
        """Send photo with optional caption"""
        try:
            target_chat_id = chat_id or self.chat_id
            if not target_chat_id:
                logger.error("No chat_id provided")
                return False
            
            url = f"{self.base_url}/sendPhoto"
            
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': target_chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f"Photo sent successfully to chat {target_chat_id}")
                    return True
                else:
                    logger.error(f"Failed to send photo: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending photo: {str(e)}")
            return False
    
    def get_chat_info(self, chat_id: str = None) -> Optional[Dict[str, Any]]:
        """Get chat information"""
        try:
            target_chat_id = chat_id or self.chat_id
            if not target_chat_id:
                return None
            
            url = f"{self.base_url}/getChat"
            payload = {'chat_id': target_chat_id}
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return response.json().get('result')
            else:
                logger.error(f"Failed to get chat info: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting chat info: {str(e)}")
            return None
    
    def test_connection(self) -> bool:
        """Test bot connection"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_info = response.json().get('result', {})
                logger.info(f"Bot connection successful: {bot_info.get('username', 'Unknown')}")
                return True
            else:
                logger.error(f"Bot connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing bot connection: {str(e)}")
            return False
