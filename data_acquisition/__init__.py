"""
Data Acquisition Layer
Handles fetching data from multiple APIs with rate limiting and caching
"""

from .data_manager import DataManager
from .alpha_vantage_client import AlphaVantageClient
from .currency_layer_client import CurrencyLayerClient
from .twelve_data_client import TwelveDataClient
from .rate_limiter import RateLimiter
from .cache_manager import CacheManager

__all__ = [
    'DataManager',
    'AlphaVantageClient', 
    'CurrencyLayerClient',
    'TwelveDataClient',
    'RateLimiter',
    'CacheManager'
]
