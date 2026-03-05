# RISE Caching Strategy Documentation

## Overview

The RISE platform implements a comprehensive multi-layer caching strategy to optimize performance, reduce latency, and minimize costs while supporting 100K+ concurrent users on rural 2G/3G networks.

## Caching Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Multi-Layer Caching                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: Browser Cache (Client-Side)                      │
│  ├─ Static Content: 1 year                                 │
│  ├─ Images: 7 days                                         │
│  └─ Dynamic Content: No cache                              │
│                                                             │
│  Layer 2: CloudFront CDN (Edge Locations)                  │
│  ├─ Static Content: 1 year TTL                            │
│  ├─ Images: 7 days TTL                                     │
│  ├─ Documents: 1 day TTL                                   │
│  └─ Compression: Gzip + Brotli                            │
│                                                             │
│  Layer 3: API Gateway Cache (Regional)                     │
│  ├─ Weather Data: 6 hours TTL                             │
│  ├─ Market Prices: 6 hours TTL                            │
│  ├─ Government Schemes: 1 day TTL                         │
│  └─ Cache Size: 0.5 GB                                     │
│                                                             │
│  Layer 4: Redis Cache (Application Layer)                  │
│  ├─ User Sessions: 24 hours TTL                           │
│  ├─ User Profiles: 1 hour TTL                             │
│  ├─ Diagnosis Results: 30 minutes TTL                     │
│  └─ Temporary Data: 5 minutes TTL                         │
│                                                             │
│  Layer 5: DynamoDB DAX (Database Layer)                    │
│  ├─ User Profiles: Microsecond latency                    │
│  ├─ Farm Data: Microsecond latency                        │
│  ├─ Weather Forecast: Microsecond latency                 │
│  └─ Market Prices: Microsecond latency                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Layer 1: Browser Caching

### Configuration
Browser caching is implemented via HTTP Cache-Control headers in Lambda responses.

### Cache Headers

**Static Content (JS, CSS, Fonts)**
```http
Cache-Control: public, max-age=31536000, immutable
Expires: Thu, 31 Dec 2099 23:59:59 GMT
```

**Images**
```http
Cache-Control: public, max-age=604800
Vary: Accept
```

**API Responses (Cacheable)**
```http
Cache-Control: public, max-age=21600
Vary: Accept-Encoding, Accept-Language
```

**API Responses (Private)**
```http
Cache-Control: private, max-age=300
Vary: Authorization
```

**API Responses (No Cache)**
```http
Cache-Control: no-store, no-cache, must-revalidate, private
Pragma: no-cache
Expires: 0
```

### Implementation
```python
from infrastructure.cache_utils import add_cache_headers

def lambda_handler(event, context):
    response = {
        'statusCode': 200,
        'body': json.dumps(data)
    }
    
    # Add appropriate cache headers
    return add_cache_headers(response, cache_type='api_cacheable')
```

## Layer 2: CloudFront CDN

### Configuration
CloudFront is configured with custom cache policies for different content types.

### Cache Policies

**Static Content Policy**
- Default TTL: 365 days
- Max TTL: 365 days
- Min TTL: 1 day
- Compression: Gzip + Brotli
- Query Strings: None
- Cookies: None

**Images Policy**
- Default TTL: 7 days
- Max TTL: 30 days
- Min TTL: 1 hour
- Compression: Gzip + Brotli
- Headers: Accept (for WebP support)

**Documents Policy**
- Default TTL: 1 day
- Max TTL: 7 days
- Min TTL: 1 hour
- Compression: Gzip + Brotli

### Path Patterns
- `/static-content/*` → Static Content Policy
- `/images/*` → Images Policy
- `/documents/*` → Documents Policy

### Cache Invalidation
```python
import boto3

cloudfront = boto3.client('cloudfront')

# Invalidate specific paths
cloudfront.create_invalidation(
    DistributionId='DISTRIBUTION_ID',
    InvalidationBatch={
        'Paths': {
            'Quantity': 2,
            'Items': [
                '/images/crop-photos/*',
                '/documents/schemes/*'
            ]
        },
        'CallerReference': str(int(time.time()))
    }
)
```

## Layer 3: API Gateway Cache

### Configuration
API Gateway caching is enabled at the stage level with a 0.5 GB cache cluster.

### Cached Endpoints

| Endpoint | TTL | Reason |
|----------|-----|--------|
| `/api/v1/intelligence/weather/{location}` | 6 hours | Weather data updates every 6 hours |
| `/api/v1/intelligence/market-prices/{crop}/{location}` | 6 hours | Market prices update twice daily |
| `/api/v1/intelligence/schemes/{user_id}` | 1 day | Government schemes rarely change |

### Non-Cached Endpoints
- `/api/v1/diagnosis/*` - User-specific, real-time analysis
- `/api/v1/voice/*` - Real-time voice processing
- `/api/v1/auth/*` - Security-sensitive operations

### Cache Key Parameters
API Gateway uses the following for cache keys:
- Path parameters (e.g., `{location}`, `{crop}`)
- Query string parameters
- Request headers (Accept-Language for i18n)

### Implementation
```python
# Lambda function automatically benefits from API Gateway caching
# No code changes required - caching is transparent
```

## Layer 4: Redis Cache (ElastiCache)

### Configuration
- Engine: Redis 7.0
- Node Type: cache.t3.micro
- Replication: 1 primary + 1 replica
- Multi-AZ: Enabled
- Encryption: At-rest and in-transit

### Cache Patterns

**User Sessions**
```python
from infrastructure.cache_utils import cache_user_session, get_cached_user_session

# Store session
cache_user_session(user_id, session_id, session_data, ttl=86400)

# Retrieve session
session = get_cached_user_session(user_id, session_id)
```

**Weather Data**
```python
from infrastructure.cache_utils import cache_weather_data, get_cached_weather

# Check cache first
weather = get_cached_weather(location)
if not weather:
    # Fetch from API
    weather = fetch_weather_from_api(location)
    # Cache for 6 hours
    cache_weather_data(location, weather, ttl=21600)
```

**Market Prices**
```python
from infrastructure.cache_utils import cache_market_prices, get_cached_market_prices

# Check cache first
prices = get_cached_market_prices(crop, location)
if not prices:
    # Fetch from database
    prices = fetch_market_prices(crop, location)
    # Cache for 6 hours
    cache_market_prices(crop, location, prices, ttl=21600)
```

### Cache Keys Strategy
```python
from infrastructure.caching_config import CacheKeyStrategy

# Weather: weather:{location}:current
weather_key = CacheKeyStrategy.weather_key("Delhi")

# Market: market:{crop}:{location}:current
market_key = CacheKeyStrategy.market_price_key("wheat", "Delhi")

# Session: session:{user_id}:{session_id}
session_key = CacheKeyStrategy.user_session_key("user123", "sess456")
```

### Cache Invalidation
```python
from infrastructure.cache_utils import invalidate_cache
from infrastructure.caching_config import CacheInvalidation

# Invalidate weather cache
keys = CacheInvalidation.invalidate_weather("Delhi")
invalidate_cache(keys, cache_type='redis')

# Invalidate market prices
keys = CacheInvalidation.invalidate_market_prices("wheat", "Delhi")
invalidate_cache(keys, cache_type='redis')
```

## Layer 5: DynamoDB DAX

### Configuration
- Cluster Name: rise-dax-cluster
- Node Type: dax.t3.small
- Replication Factor: 2 (1 primary + 1 replica)
- Encryption: Enabled

### Cached Tables
- RISE-UserProfiles
- RISE-FarmData
- RISE-DiagnosisHistory
- RISE-WeatherForecast
- RISE-MarketPrices
- RISE-GovernmentSchemes

### Implementation
```python
from infrastructure.cache_utils import DaxCache

# Initialize DAX client
dax = DaxCache()

# Get item (automatically cached)
user = dax.get_item(
    table_name='RISE-UserProfiles',
    key={'user_id': 'user123'}
)

# Query (automatically cached)
weather = dax.query(
    table_name='RISE-WeatherForecast',
    KeyConditionExpression='cache_key = :key',
    ExpressionAttributeValues={':key': 'weather:Delhi:current'}
)
```

### Benefits
- **Microsecond Latency**: 10x faster than DynamoDB alone
- **Reduced Costs**: Fewer DynamoDB read capacity units
- **Automatic**: No code changes required for caching
- **Consistent**: Eventually consistent reads cached

## Performance Metrics

### Expected Latency Improvements

| Operation | Without Cache | With Cache | Improvement |
|-----------|---------------|------------|-------------|
| Static Content | 500ms | 50ms | 10x faster |
| Weather API | 2000ms | 100ms | 20x faster |
| Market Prices | 1500ms | 100ms | 15x faster |
| User Profile | 50ms | 5ms | 10x faster |
| DynamoDB Query | 10ms | 1ms | 10x faster |

### Cost Savings

**CloudFront**
- Reduces S3 GET requests by 90%
- Estimated savings: $50-100/month

**API Gateway Cache**
- Reduces Lambda invocations by 70%
- Estimated savings: $100-200/month

**Redis Cache**
- Reduces database queries by 60%
- Estimated savings: $50-100/month

**DAX**
- Reduces DynamoDB RCUs by 80%
- Estimated savings: $100-150/month

**Total Estimated Savings**: $300-550/month

## Monitoring and Metrics

### CloudWatch Metrics

**CloudFront**
- `CacheHitRate`: Target > 80%
- `BytesDownloaded`: Monitor bandwidth usage
- `Requests`: Total requests served

**API Gateway**
- `CacheHitCount`: Number of cache hits
- `CacheMissCount`: Number of cache misses
- `Latency`: Response time with caching

**ElastiCache Redis**
- `CacheHits`: Successful cache retrievals
- `CacheMisses`: Cache misses
- `CPUUtilization`: Target < 75%
- `NetworkBytesIn/Out`: Data transfer

**DAX**
- `ItemCacheHits`: Item-level cache hits
- `QueryCacheHits`: Query-level cache hits
- `TotalRequestCount`: Total requests

### Alarms

```python
# CloudWatch alarm for low cache hit rate
alarm = cloudwatch.Alarm(
    alarm_name="RiseApiGatewayCacheHitRate",
    metric=api_gateway.metric_cache_hit_count(),
    threshold=0.7,  # 70% hit rate
    evaluation_periods=2,
    comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD
)
```

## Best Practices

### 1. Cache Warming
Pre-populate cache with frequently accessed data during deployment:
```python
def warm_cache():
    """Warm up cache with popular data"""
    popular_locations = ["Delhi", "Mumbai", "Bangalore"]
    for location in popular_locations:
        weather = fetch_weather_from_api(location)
        cache_weather_data(location, weather)
```

### 2. Cache Stampede Prevention
Use locking to prevent multiple simultaneous cache updates:
```python
import redis

def get_with_lock(key, fetch_func, ttl=300):
    """Get data with cache stampede prevention"""
    redis_client = RedisCache()
    
    # Try to get from cache
    data = redis_client.get(key)
    if data:
        return data
    
    # Acquire lock
    lock_key = f"lock:{key}"
    if redis_client.client.set(lock_key, "1", nx=True, ex=10):
        try:
            # Fetch data
            data = fetch_func()
            # Store in cache
            redis_client.set(key, data, ttl)
            return data
        finally:
            redis_client.delete(lock_key)
    else:
        # Wait for lock holder to populate cache
        time.sleep(0.1)
        return redis_client.get(key) or fetch_func()
```

### 3. Graceful Degradation
Always handle cache failures gracefully:
```python
def get_weather(location):
    """Get weather with graceful cache degradation"""
    try:
        # Try cache first
        weather = get_cached_weather(location)
        if weather:
            return weather
    except Exception as e:
        print(f"Cache error: {e}")
    
    # Fallback to direct API call
    return fetch_weather_from_api(location)
```

### 4. Cache Versioning
Include version in cache keys for easy invalidation:
```python
CACHE_VERSION = "v1"

def versioned_key(base_key):
    return f"{CACHE_VERSION}:{base_key}"

# When schema changes, increment CACHE_VERSION
# Old cache entries automatically become stale
```

## Deployment

### Prerequisites
```bash
# Install dependencies
pip install redis amazondax boto3

# Set environment variables
export REDIS_ENDPOINT="rise-redis-cluster.xxxxx.cache.amazonaws.com"
export DAX_ENDPOINT="rise-dax-cluster.xxxxx.dax-clusters.us-east-1.amazonaws.com"
```

### CDK Deployment
```bash
cd infrastructure
cdk deploy RiseStack
```

### Verify Deployment
```bash
# Test Redis connection
python -c "from cache_utils import RedisCache; r = RedisCache(); print(r.client.ping())"

# Test DAX connection
python -c "from cache_utils import DaxCache; d = DaxCache(); print('DAX connected')"
```

## Troubleshooting

### High Cache Miss Rate
1. Check TTL values - may be too short
2. Verify cache key generation is consistent
3. Monitor cache eviction rate
4. Consider increasing cache size

### Redis Connection Errors
1. Verify security group allows port 6379
2. Check VPC configuration
3. Verify Lambda is in same VPC
4. Check Redis cluster status

### DAX Connection Errors
1. Verify security group allows port 8111
2. Check IAM role permissions
3. Verify subnet configuration
4. Check DAX cluster status

### CloudFront Cache Not Working
1. Verify cache policy configuration
2. Check origin response headers
3. Review CloudFront logs
4. Test with curl -I to see headers

## References

- [AWS CloudFront Caching](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/ConfiguringCaching.html)
- [API Gateway Caching](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-caching.html)
- [ElastiCache Redis](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/WhatIs.html)
- [DynamoDB DAX](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.html)
- [HTTP Caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)
