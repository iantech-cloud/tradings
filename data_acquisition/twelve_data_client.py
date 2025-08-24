"""
Twelve Data API client for high-frequency real-time data (Gold and Bitcoin)
"""

import logging
from typing import Dict, Any, Optional
from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)

class TwelveDataClient(BaseAPIClient):
    """Twelve Data API client"""
    
    def __init__(self, api_key: str):
        super().__init__(
            api_key=api_key,
            base_url="https://api.twelvedata.com",
            rate_limit=8  # 8 requests per minute for free tier
        )
    
    def _has_api_error(self, data: Dict) -> bool:
        """Check if Twelve Data response contains an error"""
        return 'status' in data and data['status'] == 'error'
    
    def _extract_error_message(self, data: Dict) -> str:
        """Extract error message from Twelve Data response"""
        return data.get('message', 'Unknown API error')
    
    def get_real_time_data(self, symbol: str) -> Optional[Dict]:
        """Get real-time data for Gold and Bitcoin"""
        # Map our symbols to Twelve Data symbols
        symbol_mapping = {
            'XAU/USD': 'XAU/USD',
            'BTC/USD': 'BTC/USD'
        }
        
        if symbol not in symbol_mapping:
            logger.warning(f"Twelve Data doesn't support {symbol}")
            return None
        
        twelve_symbol = symbol_mapping[symbol]
        
        params = {
            'symbol': twelve_symbol,
            'interval': '1min',
            'outputsize': 1
        }
        
        data = self._make_request('/price', params)
        if not data:
            return None
        
        try:
            return {
                'symbol': symbol,
                'timestamp': data.get('datetime', ''),
                'price': float(data['price']),
                'source': 'twelve_data'
            }
            
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing Twelve Data real-time data: {str(e)}")
            return None
    
    def get_historical_data(self, symbol: str, interval: str = '1min', 
                          outputsize: int = 100) -> Optional[Dict]:
        """Get historical data for Gold and Bitcoin"""
        symbol_mapping = {
            'XAU/USD': 'XAU/USD',
            'BTC/USD': 'BTC/USD'
        }
        
        if symbol not in symbol_mapping:
            return None
        
        twelve_symbol = symbol_mapping[symbol]
        
        params = {
            'symbol': twelve_symbol,
            'interval': interval,
            'outputsize': outputsize
        }
        
        data = self._make_request('/time_series', params)
        if not data:
            return None
        
        try:
            values = data['values']
            
            ohlcv_data = []
            for item in values:
                ohlcv_data.append({
                    'timestamp': item['datetime'],
                    'open': float(item['open']),
                    'high': float(item['high']),
                    'low': float(item['low']),
                    'close': float(item['close']),
                    'volume': int(item.get('volume', 0))
                })
            
            return {
                'symbol': symbol,
                'interval': interval,
                'data': sorted(ohlcv_data, key=lambda x: x['timestamp']),
                'source': 'twelve_data'
            }
            
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing Twelve Data historical data: {str(e)}")
            return None
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get detailed quote with bid/ask spread"""
        symbol_mapping = {
            'XAU/USD': 'XAU/USD',
            'BTC/USD': 'BTC/USD'
        }
        
        if symbol not in symbol_mapping:
            return None
        
        twelve_symbol = symbol_mapping[symbol]
        
        params = {
            'symbol': twelve_symbol
        }
        
        data = self._make_request('/quote', params)
        if not data:
            return None
        
        try:
            return {
                'symbol': symbol,
                'timestamp': data.get('datetime', ''),
                'open': float(data['open']),
                'high': float(data['high']),
                'low': float(data['low']),
                'close': float(data['close']),
                'volume': int(data.get('volume', 0)),
                'previous_close': float(data.get('previous_close', 0)),
                'change': float(data.get('change', 0)),
                'percent_change': float(data.get('percent_change', 0)),
                'source': 'twelve_data'
            }
            
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing Twelve Data quote: {str(e)}")
            return None
