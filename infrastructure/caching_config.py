"""
RISE Caching Configuration
Defines caching strategies and TTLs for different data types
"""

from enum import Enum
from typing import Dict, Any


class CacheLayer(Enum):
    """Cache layer types"""
    CLOUDFRONT = "cloudfront"
    API_GATEWAY = "api_gateway"
    REDIS = "redis"
    DAX = "dax"
    BROWSER = "browser"


class CacheTTL:
    """Cache TTL configurations in seconds"""
    
    # CloudFront CDN caching
    STATIC_CONTENT = 365 * 24 * 60 * 60  # 1 year
    IMAGES = 7 * 24 * 60 * 60  # 7 days
    DOCUMENTS = 24 * 60 * 60  # 1 day
    
    # API Gateway caching
    WEATHER_DATA = 6 * 60 * 60  # 6 hours
    MARKET_PRICES = 6 * 60 * 60  # 6 hours
    GOVERNMENT_SCHEMES = 24 * 60 * 60  # 1 day
    
    # Redis caching
    USER_SESSION = 24 * 60 * 60  # 24 hours
    USER_PROFILE = 60 * 60  # 1 hour
    DIAGNOSIS_CACHE = 30 * 60  # 30 minutes
    TEMPORARY_DATA = 5 * 60  # 5 minutes
    
    # Browser caching
    BROWSER_STATIC = 365 * 24 * 60 * 60  # 1 year
    BROWSER_DYNAMIC = 0  # No cache for dynamic content


class CacheHeaders:
    """HTTP cache control headers for browser caching"""
    
    @staticmethod
    def static_content() -> Dict[str, str]:
        """Headers for static content (JS, CSS, fonts)"""
        return {
            'Cache-Control': f'public, max-age={CacheTTL.BROWSER_STATIC}, immutable',
            'Expires': 'Thu, 31 Dec 2099 23:59:59 GMT'
        }
    
    @staticmethod
    def images() -> Dict[str, str]:
        """Headers for images"""
        return {
            'Cache-Control': f'public, max-age={CacheTTL.IMAGES}',
            'Vary': 'Accept'
        }
    
    @staticmethod
    def documents() -> Dict[str, str]:
        """Headers for documents"""
        return {
            'Cache-Control': f'public, max-age={CacheTTL.DOCUMENTS}'
        }
    
    @staticmethod
    def api_cacheable(ttl: int = CacheTTL.WEATHER_DATA) -> Dict[str, str]:
        """Headers for cacheable API responses"""
        return {
            'Cache-Control': f'public, max-age={ttl}',
            'Vary': 'Accept-Encoding, Accept-Language'
        }
    
    @staticmethod
    def api_no_cache() -> Dict[str, str]:
        """Headers for non-cacheable API responses"""
        return {
            'Cache-Control': 'no-store, no-cache, must-revalidate, private',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    
    @staticmethod
    def api_private(ttl: int = 300) -> Dict[str, str]:
        """Headers for user-specific cacheable data"""
        return {
            'Cache-Control': f'private, max-age={ttl}',
            'Vary': 'Authorization'
        }


class CacheKeyStrategy:
    """Cache key generation strategies"""
    
    @staticmethod
    def weather_key(location: str, date: str = None) -> str:
        """Generate cache key for weather data"""
        if date:
            return f"weather:{location}:{date}"
        return f"weather:{location}:current"
    
    @staticmethod
    def market_price_key(crop: str, location: str, date: str = None) -> str:
        """Generate cache key for market prices"""
        if date:
            return f"market:{crop}:{location}:{date}"
        return f"market:{crop}:{location}:current"
    
    @staticmethod
    def user_session_key(user_id: str, session_id: str) -> str:
        """Generate cache key for user session"""
        return f"session:{user_id}:{session_id}"
    
    @staticmethod
    def user_profile_key(user_id: str) -> str:
        """Generate cache key for user profile"""
        return f"profile:{user_id}"
    
    @staticmethod
    def diagnosis_key(diagnosis_id: str) -> str:
        """Generate cache key for diagnosis results"""
        return f"diagnosis:{diagnosis_id}"
    
    @staticmethod
    def scheme_key(state: str, category: str = None) -> str:
        """Generate cache key for government schemes"""
        if category:
            return f"schemes:{state}:{category}"
        return f"schemes:{state}:all"


class CacheInvalidation:
    """Cache invalidation strategies"""
    
    @staticmethod
    def invalidate_weather(location: str) -> list:
        """Get cache keys to invalidate for weather updates"""
        return [
            f"weather:{location}:*",
            f"/api/v1/intelligence/weather/{location}"
        ]
    
    @staticmethod
    def invalidate_market_prices(crop: str, location: str) -> list:
        """Get cache keys to invalidate for market price updates"""
        return [
            f"market:{crop}:{location}:*",
            f"/api/v1/intelligence/market-prices/{crop}/{location}"
        ]
    
    @staticmethod
    def invalidate_user_session(user_id: str) -> list:
        """Get cache keys to invalidate for user logout"""
        return [
            f"session:{user_id}:*",
            f"profile:{user_id}"
        ]
    
    @staticmethod
    def invalidate_cloudfront_paths(paths: list) -> Dict[str, Any]:
        """Generate CloudFront invalidation request"""
        return {
            'Paths': {
                'Quantity': len(paths),
                'Items': paths
            },
            'CallerReference': str(int(time.time()))
        }


class CacheConfig:
    """Main cache configuration"""
    
    # Enable/disable caching per layer
    ENABLED = {
        CacheLayer.CLOUDFRONT: True,
        CacheLayer.API_GATEWAY: True,
        CacheLayer.REDIS: True,
        CacheLayer.DAX: True,
        CacheLayer.BROWSER: True
    }
    
    # Cacheable API endpoints
    CACHEABLE_ENDPOINTS = {
        '/api/v1/intelligence/weather/{location}': CacheTTL.WEATHER_DATA,
        '/api/v1/intelligence/market-prices/{crop}/{location}': CacheTTL.MARKET_PRICES,
        '/api/v1/intelligence/schemes/{user_id}': CacheTTL.GOVERNMENT_SCHEMES,
        '/api/v1/diagnosis/crop-disease': 0,  # Not cacheable (user-specific)
        '/api/v1/voice/transcribe': 0,  # Not cacheable
        '/api/v1/voice/synthesize': CacheTTL.TEMPORARY_DATA,  # Short cache
    }
    
    # Redis connection settings
    REDIS_CONFIG = {
        'decode_responses': True,
        'socket_connect_timeout': 5,
        'socket_timeout': 5,
        'retry_on_timeout': True,
        'max_connections': 50
    }
    
    # DAX client settings
    DAX_CONFIG = {
        'read_timeout': 5000,  # milliseconds
        'write_timeout': 5000,
        'connect_timeout': 5000,
        'request_timeout': 5000
    }


# Export commonly used configurations
__all__ = [
    'CacheLayer',
    'CacheTTL',
    'CacheHeaders',
    'CacheKeyStrategy',
    'CacheInvalidation',
    'CacheConfig'
]
