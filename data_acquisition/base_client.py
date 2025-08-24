"""
Base API client with common functionality
"""

import requests
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BaseAPIClient(ABC):
    """Base class for all API clients"""
    
    def __init__(self, api_key: str, base_url: str, rate_limit: int = 5):
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limit = rate_limit  # requests per minute
        self.last_request_time = 0
        self.request_count = 0
        self.session = requests.Session()
        
        # Set common headers
        self.session.headers.update({
            'User-Agent': 'Flask-Trading-System/1.0',
            'Accept': 'application/json'
        })
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Reset counter every minute
        if time_since_last >= 60:
            self.request_count = 0
        
        # Check if we've exceeded rate limit
        if self.request_count >= self.rate_limit:
            sleep_time = 60 - time_since_last
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self.request_count = 0
        
        self.last_request_time = current_time
        self.request_count += 1
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make HTTP request with error handling and rate limiting"""
        self._enforce_rate_limit()
        
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            params['apikey'] = self.api_key
            
            logger.debug(f"Making request to {url} with params: {params}")
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API-specific error messages
            if self._has_api_error(data):
                error_msg = self._extract_error_message(data)
                logger.error(f"API error: {error_msg}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return None
        except ValueError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return None
    
    @abstractmethod
    def _has_api_error(self, data: Dict) -> bool:
        """Check if API response contains an error"""
        pass
    
    @abstractmethod
    def _extract_error_message(self, data: Dict) -> str:
        """Extract error message from API response"""
        pass
    
    @abstractmethod
    def get_real_time_data(self, symbol: str) -> Optional[Dict]:
        """Get real-time data for a symbol"""
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, interval: str = '1min', 
                          outputsize: str = 'compact') -> Optional[Dict]:
        """Get historical data for a symbol"""
        pass
