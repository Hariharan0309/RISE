"""
Example Lambda Function with Caching Implementation
Demonstrates how to use the RISE caching strategy in Lambda functions
"""

import json
import os
from typing import Dict, Any

# Import caching utilities
from cache_utils import (
    RedisCache,
    add_cache_headers,
    get_cached_weather,
    cache_weather_data,
    get_cached_market_prices,
    cache_market_prices
)
from caching_config import CacheTTL


def weather_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for weather API with Redis caching
    
    Endpoint: GET /api/v1/intelligence/weather/{location}
    Cache: Redis (6 hours) + API Gateway (6 hours)
    """
    # Extract location from path parameters
    location = event['pathParameters']['location']
    
    # Try to get from Redis cache first
    cached_weather = get_cached_weather(location)
    if cached_weather:
        print(f"Cache HIT for weather: {location}")
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'location': location,
                'data': cached_weather,
                'cached': True
            })
        }
        # Add cache headers for browser caching
        return add_cache_headers(response, cache_type='api_cacheable')
    
    # Cache MISS - fetch from external API
    print(f"Cache MISS for weather: {location}")
    
    try:
        # Simulate fetching from weather API
        weather_data = fetch_weather_from_external_api(location)
        
        # Store in Redis cache for 6 hours
        cache_weather_data(location, weather_data, ttl=CacheTTL.WEATHER_DATA)
        
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'location': location,
                'data': weather_data,
                'cached': False
            })
        }
        
        # Add cache headers
        return add_cache_headers(response, cache_type='api_cacheable')
        
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to fetch weather data'})
        }


def market_prices_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for market prices API with Redis caching
    
    Endpoint: GET /api/v1/intelligence/market-prices/{crop}/{location}
    Cache: Redis (6 hours) + API Gateway (6 hours)
    """
    # Extract parameters
    crop = event['pathParameters']['crop']
    location = event['pathParameters']['location']
    
    # Try to get from Redis cache first
    cached_prices = get_cached_market_prices(crop, location)
    if cached_prices:
        print(f"Cache HIT for market prices: {crop} in {location}")
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'crop': crop,
                'location': location,
                'prices': cached_prices,
                'cached': True
            })
        }
        return add_cache_headers(response, cache_type='api_cacheable')
    
    # Cache MISS - fetch from database
    print(f"Cache MISS for market prices: {crop} in {location}")
    
    try:
        # Fetch from DynamoDB (via DAX for additional caching)
        prices = fetch_market_prices_from_db(crop, location)
        
        # Store in Redis cache for 6 hours
        cache_market_prices(crop, location, prices, ttl=CacheTTL.MARKET_PRICES)
        
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'crop': crop,
                'location': location,
                'prices': prices,
                'cached': False
            })
        }
        
        return add_cache_headers(response, cache_type='api_cacheable')
        
    except Exception as e:
        print(f"Error fetching market prices: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to fetch market prices'})
        }


def user_session_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for user session management with Redis caching
    
    Endpoint: GET /api/v1/auth/session
    Cache: Redis (24 hours)
    """
    # Extract user info from authorization header
    user_id = extract_user_id_from_token(event['headers'].get('Authorization'))
    session_id = event['queryStringParameters'].get('session_id')
    
    if not user_id or not session_id:
        return {
            'statusCode': 401,
            'body': json.dumps({'error': 'Unauthorized'})
        }
    
    # Try to get session from Redis
    redis_client = RedisCache()
    session_key = f"session:{user_id}:{session_id}"
    
    session_data = redis_client.get(session_key)
    if session_data:
        print(f"Session found in cache: {session_key}")
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'session': session_data,
                'cached': True
            })
        }
        # Private cache for user-specific data
        return add_cache_headers(response, cache_type='api_private')
    
    # Session not found or expired
    return {
        'statusCode': 404,
        'body': json.dumps({'error': 'Session not found or expired'})
    }


def static_content_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for serving static content with aggressive caching
    
    Endpoint: GET /static-content/*
    Cache: CloudFront (1 year) + Browser (1 year)
    """
    # Extract file path
    file_path = event['pathParameters']['proxy']
    
    try:
        # Fetch from S3 (CloudFront will cache this)
        content = fetch_from_s3(file_path)
        
        response = {
            'statusCode': 200,
            'body': content,
            'isBase64Encoded': True
        }
        
        # Add aggressive cache headers for static content
        return add_cache_headers(response, cache_type='static')
        
    except Exception as e:
        print(f"Error fetching static content: {e}")
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'File not found'})
        }


def diagnosis_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for crop diagnosis - NO CACHING
    
    Endpoint: POST /api/v1/diagnosis/crop-disease
    Cache: None (user-specific, real-time analysis)
    """
    # Extract image data
    image_data = json.loads(event['body'])
    
    try:
        # Perform AI analysis (not cached - always fresh)
        diagnosis = perform_crop_diagnosis(image_data)
        
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'diagnosis': diagnosis,
                'timestamp': int(time.time())
            })
        }
        
        # No cache headers - always fresh
        return add_cache_headers(response, cache_type='no_cache')
        
    except Exception as e:
        print(f"Error performing diagnosis: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Diagnosis failed'})
        }


# Helper functions (simulated)

def fetch_weather_from_external_api(location: str) -> Dict[str, Any]:
    """Simulate fetching weather from external API"""
    # In production, this would call OpenWeatherMap or similar
    return {
        'temperature': 28,
        'humidity': 65,
        'conditions': 'Partly Cloudy',
        'forecast': [
            {'day': 'Tomorrow', 'temp': 29, 'rain': 20},
            {'day': 'Day 2', 'temp': 27, 'rain': 40}
        ]
    }


def fetch_market_prices_from_db(crop: str, location: str) -> Dict[str, Any]:
    """Simulate fetching market prices from DynamoDB via DAX"""
    # In production, this would query DynamoDB
    return {
        'crop': crop,
        'location': location,
        'current_price': 2500,
        'min_price': 2300,
        'max_price': 2700,
        'trend': 'rising',
        'markets': [
            {'name': 'Main Market', 'price': 2500},
            {'name': 'Wholesale Market', 'price': 2450}
        ]
    }


def extract_user_id_from_token(auth_header: str) -> str:
    """Extract user ID from JWT token"""
    # In production, this would validate and decode JWT
    if auth_header and auth_header.startswith('Bearer '):
        return 'user123'  # Simulated
    return None


def fetch_from_s3(file_path: str) -> str:
    """Fetch file from S3"""
    # In production, this would use boto3 to fetch from S3
    return "file_content_base64_encoded"


def perform_crop_diagnosis(image_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform AI-powered crop diagnosis"""
    # In production, this would call Amazon Bedrock
    return {
        'disease': 'Leaf Blight',
        'confidence': 0.92,
        'severity': 'Moderate',
        'treatment': 'Apply fungicide within 48 hours'
    }


# Example: Using cache decorator

from cache_utils import cache_response
from caching_config import CacheKeyStrategy

@cache_response(
    cache_key_func=lambda location: CacheKeyStrategy.weather_key(location),
    ttl=CacheTTL.WEATHER_DATA,
    cache_type='redis'
)
def get_weather_cached(location: str) -> Dict[str, Any]:
    """
    Get weather data with automatic caching via decorator
    """
    return fetch_weather_from_external_api(location)


# Example usage:
# weather = get_weather_cached("Delhi")  # First call - cache MISS
# weather = get_weather_cached("Delhi")  # Second call - cache HIT


if __name__ == "__main__":
    # Test the caching functions
    print("Testing caching implementation...")
    
    # Test weather caching
    test_event = {
        'pathParameters': {'location': 'Delhi'},
        'headers': {}
    }
    result = weather_handler(test_event, None)
    print(f"Weather result: {result}")
    
    # Test market prices caching
    test_event = {
        'pathParameters': {'crop': 'wheat', 'location': 'Delhi'},
        'headers': {}
    }
    result = market_prices_handler(test_event, None)
    print(f"Market prices result: {result}")
