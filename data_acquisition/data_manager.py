"""
Main data manager that coordinates all API clients and handles data flow
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from app import db
from models import MarketData, APIUsage
from config import Config
from .alpha_vantage_client import AlphaVantageClient
from .currency_layer_client import CurrencyLayerClient
from .twelve_data_client import TwelveDataClient
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)

class DataManager:
    """Main data acquisition coordinator"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Initialize API clients
        self.alpha_vantage = AlphaVantageClient(config.ALPHA_VANTAGE_API_KEY)
        self.currency_layer = CurrencyLayerClient(config.CURRENCY_LAYER_API_KEY)
        self.twelve_data = TwelveDataClient(config.TWELVE_DATA_API_KEY)
        
        # Initialize cache
        self.cache = CacheManager()
        
        # Thread lock for database operations
        self.db_lock = threading.Lock()
        
        # Symbol routing - which API to use for each symbol
        self.symbol_routing = {
            'EUR/USD': ['alpha_vantage', 'currency_layer'],
            'GBP/USD': ['alpha_vantage', 'currency_layer'],
            'USD/JPY': ['alpha_vantage', 'currency_layer'],
            'USD/CAD': ['alpha_vantage', 'currency_layer'],
            'AUD/USD': ['alpha_vantage', 'currency_layer'],
            'XAU/USD': ['twelve_data'],  # Gold
            'BTC/USD': ['twelve_data']   # Bitcoin
        }
    
    def get_real_time_data(self, symbol: str, force_refresh: bool = False) -> Optional[Dict]:
        """Get real-time data for a symbol with caching"""
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cache_key = self.cache.get_cache_key(symbol, 'realtime')
            cached_data = self.cache.get(cache_key)
            
            if cached_data:
                # Determine max age based on symbol type
                max_age = self.config.CRYPTO_UPDATE_INTERVAL if symbol in ['XAU/USD', 'BTC/USD'] else self.config.FOREX_UPDATE_INTERVAL
                
                if self.cache.is_data_fresh(symbol, 'realtime', max_age):
                    logger.debug(f"Using cached data for {symbol}")
                    return cached_data
        
        # Fetch fresh data
        data = self._fetch_real_time_data(symbol)
        
        if data:
            # Cache the data
            cache_key = self.cache.get_cache_key(symbol, 'realtime')
            ttl = self.config.CRYPTO_UPDATE_INTERVAL if symbol in ['XAU/USD', 'BTC/USD'] else self.config.FOREX_UPDATE_INTERVAL
            self.cache.set(cache_key, data, ttl)
            
            # Store in database
            self._store_market_data(data)
        
        return data
    
    def _fetch_real_time_data(self, symbol: str) -> Optional[Dict]:
        """Fetch real-time data from appropriate API"""
        if symbol not in self.symbol_routing:
            logger.error(f"No routing configured for symbol: {symbol}")
            return None
        
        apis = self.symbol_routing[symbol]
        
        # Try each API in order until one succeeds
        for api_name in apis:
            try:
                start_time = datetime.utcnow()
                
                if api_name == 'alpha_vantage':
                    data = self.alpha_vantage.get_real_time_data(symbol)
                elif api_name == 'currency_layer':
                    data = self.currency_layer.get_real_time_data(symbol)
                elif api_name == 'twelve_data':
                    data = self.twelve_data.get_real_time_data(symbol)
                else:
                    continue
                
                # Log API usage
                response_time = (datetime.utcnow() - start_time).total_seconds()
                self._log_api_usage(api_name, 'real_time', response_time, 200 if data else 500)
                
                if data:
                    logger.info(f"Successfully fetched real-time data for {symbol} from {api_name}")
                    return data
                
            except Exception as e:
                logger.error(f"Error fetching data from {api_name} for {symbol}: {str(e)}")
                continue
        
        logger.error(f"Failed to fetch real-time data for {symbol} from all APIs")
        return None
    
    def get_historical_data(self, symbol: str, interval: str = '1min', 
                          limit: int = 100) -> Optional[Dict]:
        """Get historical data for a symbol"""
        
        # Check cache first
        cache_key = self.cache.get_cache_key(symbol, 'historical', interval)
        cached_data = self.cache.get(cache_key)
        
        if cached_data and self.cache.is_data_fresh(symbol, 'historical', 3600):  # 1 hour cache
            logger.debug(f"Using cached historical data for {symbol}")
            return cached_data
        
        # Fetch fresh data
        data = self._fetch_historical_data(symbol, interval, limit)
        
        if data:
            # Cache the data
            self.cache.set(cache_key, data, 3600)  # Cache for 1 hour
        
        return data
    
    def _fetch_historical_data(self, symbol: str, interval: str, limit: int) -> Optional[Dict]:
        """Fetch historical data from appropriate API"""
        if symbol not in self.symbol_routing:
            return None
        
        apis = self.symbol_routing[symbol]
        
        for api_name in apis:
            try:
                start_time = datetime.utcnow()
                
                if api_name == 'alpha_vantage':
                    data = self.alpha_vantage.get_historical_data(symbol, interval)
                elif api_name == 'twelve_data':
                    data = self.twelve_data.get_historical_data(symbol, interval, limit)
                else:
                    continue  # Currency Layer doesn't provide historical intraday data
                
                response_time = (datetime.utcnow() - start_time).total_seconds()
                self._log_api_usage(api_name, 'historical', response_time, 200 if data else 500)
                
                if data:
                    logger.info(f"Successfully fetched historical data for {symbol} from {api_name}")
                    return data
                
            except Exception as e:
                logger.error(f"Error fetching historical data from {api_name}: {str(e)}")
                continue
        
        return None
    
    def update_all_symbols(self) -> Dict[str, bool]:
        """Update all configured symbols concurrently"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit tasks for all symbols
            future_to_symbol = {
                executor.submit(self.get_real_time_data, symbol, True): symbol
                for symbol in self.config.SUPPORTED_PAIRS
            }
            
            # Collect results
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    data = future.result()
                    results[symbol] = data is not None
                    if data:
                        logger.info(f"Updated {symbol}: {data['price']}")
                except Exception as e:
                    logger.error(f"Error updating {symbol}: {str(e)}")
                    results[symbol] = False
        
        return results
    
    def _store_market_data(self, data: Dict):
        """Store market data in database"""
        try:
            with self.db_lock:
                market_data = MarketData(
                    symbol=data['symbol'],
                    timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')) if isinstance(data['timestamp'], str) else datetime.fromtimestamp(data['timestamp']),
                    open_price=data.get('open', data['price']),
                    high_price=data.get('high', data['price']),
                    low_price=data.get('low', data['price']),
                    close_price=data['price'],
                    volume=data.get('volume', 0),
                    source=data['source']
                )
                
                db.session.add(market_data)
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error storing market data: {str(e)}")
            db.session.rollback()
    
    def _log_api_usage(self, provider: str, endpoint: str, response_time: float, status_code: int):
        """Log API usage for monitoring and rate limiting"""
        try:
            with self.db_lock:
                api_usage = APIUsage(
                    api_provider=provider,
                    endpoint=endpoint,
                    response_time=response_time,
                    status_code=status_code
                )
                
                db.session.add(api_usage)
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error logging API usage: {str(e)}")
            db.session.rollback()
    
    def get_api_usage_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get API usage statistics"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            usage_stats = db.session.query(APIUsage).filter(
                APIUsage.timestamp >= cutoff_time
            ).all()
            
            stats = {}
            for usage in usage_stats:
                provider = usage.api_provider
                if provider not in stats:
                    stats[provider] = {
                        'total_requests': 0,
                        'successful_requests': 0,
                        'failed_requests': 0,
                        'average_response_time': 0,
                        'response_times': []
                    }
                
                stats[provider]['total_requests'] += 1
                stats[provider]['response_times'].append(usage.response_time)
                
                if usage.status_code == 200:
                    stats[provider]['successful_requests'] += 1
                else:
                    stats[provider]['failed_requests'] += 1
            
            # Calculate averages
            for provider in stats:
                response_times = stats[provider]['response_times']
                stats[provider]['average_response_time'] = sum(response_times) / len(response_times) if response_times else 0
                del stats[provider]['response_times']  # Remove raw data
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting API usage stats: {str(e)}")
            return {}
