"""
RISE Cache Utilities
Helper functions for interacting with different cache layers
"""

import json
import time
import os
from typing import Any, Optional, Dict, Callable
from functools import wraps

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import amazondax
    DAX_AVAILABLE = True
except ImportError:
    DAX_AVAILABLE = False

from caching_config import CacheTTL, CacheKeyStrategy, CacheHeaders


class RedisCache:
    """Redis cache client wrapper"""
    
    def __init__(self, host: str = None, port: int = 6379, **kwargs):
        """Initialize Redis client"""
        if not REDIS_AVAILABLE:
            raise ImportError("redis-py is not installed")
        
        self.host = host or os.environ.get('REDIS_ENDPOINT')
        self.port = port
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            decode_responses=True,
            **kwargs
        )
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis GET error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = CacheTTL.TEMPORARY_DATA) -> bool:
        """Set value in cache with TTL"""
        try:
            serialized = json.dumps(value)
            return self.client.setex(key, ttl, serialized)
        except Exception as e:
            print(f"Redis SET error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return self.client.delete(key) > 0
        except Exception as e:
            print(f"Redis DELETE error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Redis DELETE PATTERN error: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            print(f"Redis EXISTS error: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get remaining TTL for key"""
        try:
            return self.client.ttl(key)
        except Exception as e:
            print(f"Redis TTL error: {e}")
            return -1


class DaxCache:
    """DynamoDB DAX cache client wrapper"""
    
    def __init__(self, endpoint: str = None):
        """Initialize DAX client"""
        if not DAX_AVAILABLE:
            raise ImportError("amazon-dax-client is not installed")
        
        self.endpoint = endpoint or os.environ.get('DAX_ENDPOINT')
        self.client = amazondax.AmazonDaxClient(
            endpoint_url=self.endpoint
        )
    
    def get_item(self, table_name: str, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get item from DynamoDB via DAX"""
        try:
            response = self.client.get_item(
                TableName=table_name,
                Key=key
            )
            return response.get('Item')
        except Exception as e:
            print(f"DAX GET error: {e}")
            return None
    
    def query(self, table_name: str, **kwargs) -> list:
        """Query DynamoDB via DAX"""
        try:
            response = self.client.query(
                TableName=table_name,
                **kwargs
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"DAX QUERY error: {e}")
            return []


def cache_response(
    cache_key_func: Callable,
    ttl: int = CacheTTL.TEMPORARY_DATA,
    cache_type: str = 'redis'
):
    """
    Decorator to cache function responses
    
    Args:
        cache_key_func: Function to generate cache key from function args
        ttl: Time to live in seconds
        cache_type: 'redis' or 'dax'
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_key_func(*args, **kwargs)
            
            # Try to get from cache
            if cache_type == 'redis' and REDIS_AVAILABLE:
                try:
                    redis_client = RedisCache()
                    cached_value = redis_client.get(cache_key)
                    if cached_value is not None:
                        print(f"Cache HIT: {cache_key}")
                        return cached_value
                except Exception as e:
                    print(f"Cache error: {e}")
            
            # Cache miss - execute function
            print(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)
            
            # Store in cache
            if cache_type == 'redis' and REDIS_AVAILABLE:
                try:
                    redis_client = RedisCache()
                    redis_client.set(cache_key, result, ttl)
                except Exception as e:
                    print(f"Cache store error: {e}")
            
            return result
        
        return wrapper
    return decorator


def add_cache_headers(response: Dict[str, Any], cache_type: str = 'no_cache') -> Dict[str, Any]:
    """
    Add appropriate cache headers to Lambda response
    
    Args:
        response: Lambda response dict
        cache_type: Type of caching ('static', 'images', 'api_cacheable', 'no_cache', etc.)
    
    Returns:
        Response with cache headers added
    """
    if 'headers' not in response:
        response['headers'] = {}
    
    # Get appropriate headers based on cache type
    if cache_type == 'static':
        headers = CacheHeaders.static_content()
    elif cache_type == 'images':
        headers = CacheHeaders.images()
    elif cache_type == 'documents':
        headers = CacheHeaders.documents()
    elif cache_type == 'api_cacheable':
        headers = CacheHeaders.api_cacheable()
    elif cache_type == 'api_private':
        headers = CacheHeaders.api_private()
    else:
        headers = CacheHeaders.api_no_cache()
    
    response['headers'].update(headers)
    return response


def invalidate_cache(keys: list, cache_type: str = 'redis') -> bool:
    """
    Invalidate cache entries
    
    Args:
        keys: List of cache keys or patterns to invalidate
        cache_type: 'redis' or 'cloudfront'
    
    Returns:
        True if successful
    """
    if cache_type == 'redis' and REDIS_AVAILABLE:
        try:
            redis_client = RedisCache()
            for key in keys:
                if '*' in key:
                    redis_client.delete_pattern(key)
                else:
                    redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Cache invalidation error: {e}")
            return False
    
    return False


# Example usage functions

def cache_weather_data(location: str, data: Dict[str, Any], ttl: int = CacheTTL.WEATHER_DATA):
    """Cache weather data"""
    cache_key = CacheKeyStrategy.weather_key(location)
    redis_client = RedisCache()
    return redis_client.set(cache_key, data, ttl)


def get_cached_weather(location: str) -> Optional[Dict[str, Any]]:
    """Get cached weather data"""
    cache_key = CacheKeyStrategy.weather_key(location)
    redis_client = RedisCache()
    return redis_client.get(cache_key)


def cache_market_prices(crop: str, location: str, data: Dict[str, Any], ttl: int = CacheTTL.MARKET_PRICES):
    """Cache market price data"""
    cache_key = CacheKeyStrategy.market_price_key(crop, location)
    redis_client = RedisCache()
    return redis_client.set(cache_key, data, ttl)


def get_cached_market_prices(crop: str, location: str) -> Optional[Dict[str, Any]]:
    """Get cached market price data"""
    cache_key = CacheKeyStrategy.market_price_key(crop, location)
    redis_client = RedisCache()
    return redis_client.get(cache_key)


def cache_user_session(user_id: str, session_id: str, data: Dict[str, Any], ttl: int = CacheTTL.USER_SESSION):
    """Cache user session data"""
    cache_key = CacheKeyStrategy.user_session_key(user_id, session_id)
    redis_client = RedisCache()
    return redis_client.set(cache_key, data, ttl)


def get_cached_user_session(user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    """Get cached user session data"""
    cache_key = CacheKeyStrategy.user_session_key(user_id, session_id)
    redis_client = RedisCache()
    return redis_client.get(cache_key)


# Export commonly used functions
__all__ = [
    'RedisCache',
    'DaxCache',
    'cache_response',
    'add_cache_headers',
    'invalidate_cache',
    'cache_weather_data',
    'get_cached_weather',
    'cache_market_prices',
    'get_cached_market_prices',
    'cache_user_session',
    'get_cached_user_session'
]
