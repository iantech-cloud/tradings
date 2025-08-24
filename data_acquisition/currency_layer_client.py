"""
Currency Layer API client for live forex validation
"""

import logging
from typing import Dict, Any, Optional
from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)

class CurrencyLayerClient(BaseAPIClient):
    """Currency Layer API client"""
    
    def __init__(self, api_key: str):
        super().__init__(
            api_key=api_key,
            base_url="http://api.currencylayer.com",
            rate_limit=1000  # 1000 requests per month for free tier
        )
    
    def _has_api_error(self, data: Dict) -> bool:
        """Check if Currency Layer response contains an error"""
        return not data.get('success', True) or 'error' in data
    
    def _extract_error_message(self, data: Dict) -> str:
        """Extract error message from Currency Layer response"""
        if 'error' in data:
            return f"{data['error'].get('code', 'Unknown')}: {data['error'].get('info', 'Unknown error')}"
        return "API request failed"
    
    def get_real_time_data(self, symbol: str) -> Optional[Dict]:
        """Get real-time forex rates (USD-based pairs only)"""
        if not symbol.startswith('USD/') and not symbol.endswith('/USD'):
            logger.warning(f"Currency Layer only supports USD-based pairs, skipping {symbol}")
            return None
        
        params = {
            'access_key': self.api_key,  # Currency Layer uses access_key instead of apikey
            'currencies': self._extract_currencies(symbol),
            'format': 1
        }
        
        # Remove apikey from params since Currency Layer uses access_key
        data = self.session.get(f"{self.base_url}/live", params=params, timeout=30)
        
        try:
            data = data.json()
            
            if self._has_api_error(data):
                error_msg = self._extract_error_message(data)
                logger.error(f"Currency Layer API error: {error_msg}")
                return None
            
            # Extract the rate for our symbol
            rate_key = self._get_rate_key(symbol)
            if rate_key not in data['quotes']:
                logger.error(f"Rate not found for {symbol}")
                return None
            
            rate = data['quotes'][rate_key]
            
            return {
                'symbol': symbol,
                'timestamp': data['timestamp'],
                'price': rate,
                'source': 'currency_layer'
            }
            
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing Currency Layer data: {str(e)}")
            return None
    
    def get_historical_data(self, symbol: str, date: str) -> Optional[Dict]:
        """Get historical forex rates for a specific date"""
        if not symbol.startswith('USD/') and not symbol.endswith('/USD'):
            return None
        
        params = {
            'access_key': self.api_key,
            'currencies': self._extract_currencies(symbol),
            'date': date,
            'format': 1
        }
        
        data = self.session.get(f"{self.base_url}/historical", params=params, timeout=30)
        
        try:
            data = data.json()
            
            if self._has_api_error(data):
                return None
            
            rate_key = self._get_rate_key(symbol)
            if rate_key not in data['quotes']:
                return None
            
            return {
                'symbol': symbol,
                'date': date,
                'price': data['quotes'][rate_key],
                'source': 'currency_layer'
            }
            
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing Currency Layer historical data: {str(e)}")
            return None
    
    def _extract_currencies(self, symbol: str) -> str:
        """Extract non-USD currency from symbol"""
        if symbol.startswith('USD/'):
            return symbol[4:]
        else:  # ends with /USD
            return symbol[:3]
    
    def _get_rate_key(self, symbol: str) -> str:
        """Get the rate key used by Currency Layer API"""
        if symbol.startswith('USD/'):
            return f"USD{symbol[4:]}"
        else:  # ends with /USD
            return f"{symbol[:3]}USD"
