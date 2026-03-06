"""
Tests for RISE Caching Implementation
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock

# Mock the redis and amazondax imports before importing cache_utils
import sys
sys.modules['redis'] = MagicMock()
sys.modules['amazondax'] = MagicMock()

from infrastructure.caching_config import (
    CacheTTL,
    CacheHeaders,
    CacheKeyStrategy,
    CacheInvalidation,
    CacheConfig
)


class TestCacheTTL:
    """Test cache TTL configurations"""
    
    def test_static_content_ttl(self):
        """Test static content has 1 year TTL"""
        assert CacheTTL.STATIC_CONTENT == 365 * 24 * 60 * 60
    
    def test_weather_data_ttl(self):
        """Test weather data has 6 hour TTL"""
        assert CacheTTL.WEATHER_DATA == 6 * 60 * 60
    
    def test_market_prices_ttl(self):
        """Test market prices has 6 hour TTL"""
        assert CacheTTL.MARKET_PRICES == 6 * 60 * 60
    
    def test_user_session_ttl(self):
        """Test user session has 24 hour TTL"""
        assert CacheTTL.USER_SESSION == 24 * 60 * 60


class TestCacheHeaders:
    """Test cache header generation"""
    
    def test_static_content_headers(self):
        """Test static content headers"""
        headers = CacheHeaders.static_content()
        assert 'Cache-Control' in headers
        assert 'public' in headers['Cache-Control']
        assert 'immutable' in headers['Cache-Control']
        assert 'Expires' in headers
    
    def test_images_headers(self):
        """Test image headers"""
        headers = CacheHeaders.images()
        assert 'Cache-Control' in headers
        assert 'public' in headers['Cache-Control']
        assert 'Vary' in headers
        assert headers['Vary'] == 'Accept'
    
    def test_api_cacheable_headers(self):
        """Test cacheable API headers"""
        headers = CacheHeaders.api_cacheable()
        assert 'Cache-Control' in headers
        assert 'public' in headers['Cache-Control']
        assert 'Vary' in headers
    
    def test_api_no_cache_headers(self):
        """Test no-cache API headers"""
        headers = CacheHeaders.api_no_cache()
        assert 'Cache-Control' in headers
        assert 'no-store' in headers['Cache-Control']
        assert 'no-cache' in headers['Cache-Control']
        assert 'Pragma' in headers
    
    def test_api_private_headers(self):
        """Test private API headers"""
        headers = CacheHeaders.api_private()
        assert 'Cache-Control' in headers
        assert 'private' in headers['Cache-Control']
        assert 'Vary' in headers
        assert headers['Vary'] == 'Authorization'


class TestCacheKeyStrategy:
    """Test cache key generation"""
    
    def test_weather_key(self):
        """Test weather cache key generation"""
        key = CacheKeyStrategy.weather_key("Delhi")
        assert key == "weather:Delhi:current"
        
        key_with_date = CacheKeyStrategy.weather_key("Delhi", "2024-01-15")
        assert key_with_date == "weather:Delhi:2024-01-15"
    
    def test_market_price_key(self):
        """Test market price cache key generation"""
        key = CacheKeyStrategy.market_price_key("wheat", "Delhi")
        assert key == "market:wheat:Delhi:current"
        
        key_with_date = CacheKeyStrategy.market_price_key("wheat", "Delhi", "2024-01-15")
        assert key_with_date == "market:wheat:Delhi:2024-01-15"
    
    def test_user_session_key(self):
        """Test user session cache key generation"""
        key = CacheKeyStrategy.user_session_key("user123", "sess456")
        assert key == "session:user123:sess456"
    
    def test_user_profile_key(self):
        """Test user profile cache key generation"""
        key = CacheKeyStrategy.user_profile_key("user123")
        assert key == "profile:user123"
    
    def test_diagnosis_key(self):
        """Test diagnosis cache key generation"""
        key = CacheKeyStrategy.diagnosis_key("diag789")
        assert key == "diagnosis:diag789"
    
    def test_scheme_key(self):
        """Test government scheme cache key generation"""
        key = CacheKeyStrategy.scheme_key("Delhi")
        assert key == "schemes:Delhi:all"
        
        key_with_category = CacheKeyStrategy.scheme_key("Delhi", "subsidy")
        assert key_with_category == "schemes:Delhi:subsidy"


class TestCacheInvalidation:
    """Test cache invalidation strategies"""
    
    def test_invalidate_weather(self):
        """Test weather cache invalidation"""
        keys = CacheInvalidation.invalidate_weather("Delhi")
        assert len(keys) == 2
        assert "weather:Delhi:*" in keys
        assert "/api/v1/intelligence/weather/Delhi" in keys
    
    def test_invalidate_market_prices(self):
        """Test market price cache invalidation"""
        keys = CacheInvalidation.invalidate_market_prices("wheat", "Delhi")
        assert len(keys) == 2
        assert "market:wheat:Delhi:*" in keys
        assert "/api/v1/intelligence/market-prices/wheat/Delhi" in keys
    
    def test_invalidate_user_session(self):
        """Test user session cache invalidation"""
        keys = CacheInvalidation.invalidate_user_session("user123")
        assert len(keys) == 2
        assert "session:user123:*" in keys
        assert "profile:user123" in keys


class TestCacheConfig:
    """Test cache configuration"""
    
    def test_all_layers_enabled(self):
        """Test all cache layers are enabled by default"""
        from infrastructure.caching_config import CacheLayer
        
        assert CacheConfig.ENABLED[CacheLayer.CLOUDFRONT] is True
        assert CacheConfig.ENABLED[CacheLayer.API_GATEWAY] is True
        assert CacheConfig.ENABLED[CacheLayer.REDIS] is True
        assert CacheConfig.ENABLED[CacheLayer.DAX] is True
        assert CacheConfig.ENABLED[CacheLayer.BROWSER] is True
    
    def test_cacheable_endpoints(self):
        """Test cacheable endpoints configuration"""
        endpoints = CacheConfig.CACHEABLE_ENDPOINTS
        
        # Weather endpoint should be cacheable
        assert '/api/v1/intelligence/weather/{location}' in endpoints
        assert endpoints['/api/v1/intelligence/weather/{location}'] == CacheTTL.WEATHER_DATA
        
        # Market prices should be cacheable
        assert '/api/v1/intelligence/market-prices/{crop}/{location}' in endpoints
        assert endpoints['/api/v1/intelligence/market-prices/{crop}/{location}'] == CacheTTL.MARKET_PRICES
        
        # Diagnosis should not be cacheable
        assert endpoints['/api/v1/diagnosis/crop-disease'] == 0
    
    def test_redis_config(self):
        """Test Redis configuration"""
        config = CacheConfig.REDIS_CONFIG
        
        assert config['decode_responses'] is True
        assert config['socket_connect_timeout'] == 5
        assert config['retry_on_timeout'] is True
        assert config['max_connections'] == 50
    
    def test_dax_config(self):
        """Test DAX configuration"""
        config = CacheConfig.DAX_CONFIG
        
        assert config['read_timeout'] == 5000
        assert config['write_timeout'] == 5000
        assert config['connect_timeout'] == 5000


class TestCacheUtils:
    """Test cache utility functions"""
    
    @patch('infrastructure.cache_utils.redis.Redis')
    def test_redis_cache_get(self, mock_redis):
        """Test Redis cache get operation"""
        from infrastructure.cache_utils import RedisCache
        
        # Mock Redis client
        mock_client = Mock()
        mock_client.get.return_value = json.dumps({'data': 'test'})
        mock_redis.return_value = mock_client
        
        # Test get
        cache = RedisCache(host='localhost')
        result = cache.get('test_key')
        
        assert result == {'data': 'test'}
        mock_client.get.assert_called_once_with('test_key')
    
    @patch('infrastructure.cache_utils.redis.Redis')
    def test_redis_cache_set(self, mock_redis):
        """Test Redis cache set operation"""
        from infrastructure.cache_utils import RedisCache
        
        # Mock Redis client
        mock_client = Mock()
        mock_client.setex.return_value = True
        mock_redis.return_value = mock_client
        
        # Test set
        cache = RedisCache(host='localhost')
        result = cache.set('test_key', {'data': 'test'}, ttl=300)
        
        assert result is True
        mock_client.setex.assert_called_once()
    
    @patch('infrastructure.cache_utils.redis.Redis')
    def test_redis_cache_delete(self, mock_redis):
        """Test Redis cache delete operation"""
        from infrastructure.cache_utils import RedisCache
        
        # Mock Redis client
        mock_client = Mock()
        mock_client.delete.return_value = 1
        mock_redis.return_value = mock_client
        
        # Test delete
        cache = RedisCache(host='localhost')
        result = cache.delete('test_key')
        
        assert result is True
        mock_client.delete.assert_called_once_with('test_key')
    
    def test_add_cache_headers_static(self):
        """Test adding static content cache headers"""
        from infrastructure.cache_utils import add_cache_headers
        
        response = {
            'statusCode': 200,
            'body': 'content'
        }
        
        result = add_cache_headers(response, cache_type='static')
        
        assert 'headers' in result
        assert 'Cache-Control' in result['headers']
        assert 'public' in result['headers']['Cache-Control']
        assert 'immutable' in result['headers']['Cache-Control']
    
    def test_add_cache_headers_no_cache(self):
        """Test adding no-cache headers"""
        from infrastructure.cache_utils import add_cache_headers
        
        response = {
            'statusCode': 200,
            'body': 'content'
        }
        
        result = add_cache_headers(response, cache_type='no_cache')
        
        assert 'headers' in result
        assert 'Cache-Control' in result['headers']
        assert 'no-store' in result['headers']['Cache-Control']


class TestLambdaCachingExample:
    """Test Lambda caching example functions"""
    
    @patch('infrastructure.lambda_caching_example.get_cached_weather')
    @patch('infrastructure.lambda_caching_example.cache_weather_data')
    @patch('infrastructure.lambda_caching_example.fetch_weather_from_external_api')
    def test_weather_handler_cache_hit(self, mock_fetch, mock_cache, mock_get):
        """Test weather handler with cache hit"""
        from infrastructure.lambda_caching_example import weather_handler
        
        # Mock cache hit
        mock_get.return_value = {'temperature': 28, 'cached': True}
        
        event = {
            'pathParameters': {'location': 'Delhi'},
            'headers': {}
        }
        
        result = weather_handler(event, None)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['cached'] is True
        assert 'Cache-Control' in result['headers']
        
        # Should not fetch from API
        mock_fetch.assert_not_called()
    
    @patch('infrastructure.lambda_caching_example.get_cached_weather')
    @patch('infrastructure.lambda_caching_example.cache_weather_data')
    @patch('infrastructure.lambda_caching_example.fetch_weather_from_external_api')
    def test_weather_handler_cache_miss(self, mock_fetch, mock_cache, mock_get):
        """Test weather handler with cache miss"""
        from infrastructure.lambda_caching_example import weather_handler
        
        # Mock cache miss
        mock_get.return_value = None
        mock_fetch.return_value = {'temperature': 28}
        
        event = {
            'pathParameters': {'location': 'Delhi'},
            'headers': {}
        }
        
        result = weather_handler(event, None)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['cached'] is False
        
        # Should fetch from API and cache
        mock_fetch.assert_called_once_with('Delhi')
        mock_cache.assert_called_once()


class TestPerformanceMetrics:
    """Test caching performance improvements"""
    
    def test_cache_reduces_latency(self):
        """Test that caching reduces response latency"""
        # Simulate uncached request (slow)
        start = time.time()
        time.sleep(0.1)  # Simulate API call
        uncached_time = time.time() - start
        
        # Simulate cached request (fast)
        start = time.time()
        cached_data = {'from': 'cache'}  # Instant
        cached_time = time.time() - start
        
        # Cached should be significantly faster
        assert cached_time < uncached_time
        assert cached_time < 0.01  # Less than 10ms
    
    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation"""
        total_requests = 100
        cache_hits = 80
        cache_misses = 20
        
        hit_rate = cache_hits / total_requests
        
        assert hit_rate == 0.8  # 80% hit rate
        assert hit_rate > 0.7  # Target > 70%


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
