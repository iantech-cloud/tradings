"""
Cache manager for storing recent market data to reduce API calls
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import redis
from config import Config

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis-based cache manager for market data"""
    
    def __init__(self, redis_url: str = None):
        try:
            self.redis_client = redis.from_url(
                redis_url or 'redis://localhost:6379/0',
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory cache: {str(e)}")
            self.enabled = False
            self.memory_cache = {}
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached data"""
        try:
            if self.enabled:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            else:
                # Use in-memory cache
                cache_item = self.memory_cache.get(key)
                if cache_item and cache_item['expires'] > datetime.utcnow():
                    return cache_item['data']
                elif cache_item:
                    # Remove expired item
                    del self.memory_cache[key]
            
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    def set(self, key: str, data: Dict, ttl_seconds: int = 300) -> bool:
        """Set cached data with TTL"""
        try:
            if self.enabled:
                return self.redis_client.setex(
                    key, 
                    ttl_seconds, 
                    json.dumps(data, default=str)
                )
            else:
                # Use in-memory cache
                self.memory_cache[key] = {
                    'data': data,
                    'expires': datetime.utcnow() + timedelta(seconds=ttl_seconds)
                }
                return True
                
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete cached data"""
        try:
            if self.enabled:
                return bool(self.redis_client.delete(key))
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
    
    def get_cache_key(self, symbol: str, data_type: str, interval: str = None) -> str:
        """Generate standardized cache key"""
        key_parts = ['market_data', symbol.replace('/', '_'), data_type]
        if interval:
            key_parts.append(interval)
        return ':'.join(key_parts)
    
    def is_data_fresh(self, symbol: str, data_type: str, max_age_seconds: int) -> bool:
        """Check if cached data is still fresh"""
        cache_key = self.get_cache_key(symbol, data_type)
        cached_data = self.get(cache_key)
        
        if not cached_data or 'timestamp' not in cached_data:
            return False
        
        try:
            # Parse timestamp
            if isinstance(cached_data['timestamp'], str):
                cached_time = datetime.fromisoformat(cached_data['timestamp'].replace('Z', '+00:00'))
            else:
                cached_time = datetime.fromtimestamp(cached_data['timestamp'])
            
            age = (datetime.utcnow() - cached_time.replace(tzinfo=None)).total_seconds()
            return age < max_age_seconds
            
        except Exception as e:
            logger.error(f"Error checking data freshness: {str(e)}")
            return False
    
    def cleanup_expired(self):
        """Clean up expired in-memory cache entries"""
        if not self.enabled:
            current_time = datetime.utcnow()
            expired_keys = [
                key for key, item in self.memory_cache.items()
                if item['expires'] <= current_time
            ]
            for key in expired_keys:
                del self.memory_cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
