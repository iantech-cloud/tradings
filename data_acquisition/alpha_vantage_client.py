"""
Alpha Vantage API client for forex and technical indicators
"""

import logging
from typing import Dict, Any, Optional
from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)

class AlphaVantageClient(BaseAPIClient):
    """Alpha Vantage API client"""
    
    def __init__(self, api_key: str):
        super().__init__(
            api_key=api_key,
            base_url="https://www.alphavantage.co/query",
            rate_limit=5  # 5 requests per minute for free tier
        )
    
    def _has_api_error(self, data: Dict) -> bool:
        """Check if Alpha Vantage response contains an error"""
        return (
            'Error Message' in data or 
            'Note' in data or
            'Information' in data
        )
    
    def _extract_error_message(self, data: Dict) -> str:
        """Extract error message from Alpha Vantage response"""
        if 'Error Message' in data:
            return data['Error Message']
        elif 'Note' in data:
            return data['Note']
        elif 'Information' in data:
            return data['Information']
        return "Unknown API error"
    
    def get_real_time_data(self, symbol: str) -> Optional[Dict]:
        """Get real-time forex data"""
        # Convert symbol format (EUR/USD -> EURUSD)
        formatted_symbol = symbol.replace('/', '')
        
        params = {
            'function': 'CURRENCY_EXCHANGE_RATE',
            'from_currency': formatted_symbol[:3],
            'to_currency': formatted_symbol[3:]
        }
        
        data = self._make_request('', params)
        if not data:
            return None
        
        try:
            exchange_rate = data['Realtime Currency Exchange Rate']
            
            return {
                'symbol': symbol,
                'timestamp': exchange_rate['6. Last Refreshed'],
                'price': float(exchange_rate['5. Exchange Rate']),
                'bid': float(exchange_rate.get('8. Bid Price', exchange_rate['5. Exchange Rate'])),
                'ask': float(exchange_rate.get('9. Ask Price', exchange_rate['5. Exchange Rate'])),
                'source': 'alpha_vantage'
            }
            
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing Alpha Vantage real-time data: {str(e)}")
            return None
    
    def get_historical_data(self, symbol: str, interval: str = '1min', 
                          outputsize: str = 'compact') -> Optional[Dict]:
        """Get historical forex data"""
        formatted_symbol = symbol.replace('/', '')
        
        params = {
            'function': 'FX_INTRADAY',
            'from_symbol': formatted_symbol[:3],
            'to_symbol': formatted_symbol[3:],
            'interval': interval,
            'outputsize': outputsize
        }
        
        data = self._make_request('', params)
        if not data:
            return None
        
        try:
            time_series_key = f'Time Series FX ({interval})'
            time_series = data[time_series_key]
            
            ohlcv_data = []
            for timestamp, values in time_series.items():
                ohlcv_data.append({
                    'timestamp': timestamp,
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': 0  # Forex doesn't have volume
                })
            
            return {
                'symbol': symbol,
                'interval': interval,
                'data': sorted(ohlcv_data, key=lambda x: x['timestamp']),
                'source': 'alpha_vantage'
            }
            
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing Alpha Vantage historical data: {str(e)}")
            return None
    
    def get_technical_indicator(self, symbol: str, indicator: str, 
                              interval: str = '1min', **kwargs) -> Optional[Dict]:
        """Get technical indicator data"""
        formatted_symbol = symbol.replace('/', '')
        
        params = {
            'function': indicator.upper(),
            'symbol': f"{formatted_symbol[:3]}{formatted_symbol[3:]}",
            'interval': interval,
            **kwargs
        }
        
        data = self._make_request('', params)
        if not data:
            return None
        
        try:
            # Find the technical analysis key (varies by indicator)
            tech_key = None
            for key in data.keys():
                if 'Technical Analysis' in key:
                    tech_key = key
                    break
            
            if not tech_key:
                logger.error(f"No technical analysis data found for {indicator}")
                return None
            
            indicator_data = []
            for timestamp, values in data[tech_key].items():
                indicator_data.append({
                    'timestamp': timestamp,
                    'values': {k.split('. ')[-1]: float(v) for k, v in values.items()}
                })
            
            return {
                'symbol': symbol,
                'indicator': indicator,
                'interval': interval,
                'data': sorted(indicator_data, key=lambda x: x['timestamp']),
                'source': 'alpha_vantage'
            }
            
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing technical indicator data: {str(e)}")
            return None
