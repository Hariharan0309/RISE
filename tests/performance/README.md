# RISE Performance Testing Suite

This directory contains comprehensive performance tests for the RISE farming assistant platform, validating response times, scalability, network optimization, offline functionality, and bundle sizes.

## Performance Requirements

### Response Time Requirements
- **Voice Processing**: <3 seconds end-to-end
- **Image Analysis**: <10 seconds end-to-end
- **API Endpoints**: <1 second for data retrieval
- **Page Load**: <2 seconds on 3G networks

### Scalability Requirements
- **Concurrent Users**: Support 100K concurrent users
- **Peak Load**: Handle 10K requests/second
- **Database**: Sub-100ms query response times
- **Lambda Cold Start**: <1 second

### Network Requirements
- **2G Support**: Core features functional on 2G (50 Kbps)
- **3G Optimization**: Full features on 3G (384 Kbps)
- **Data Usage**: <1MB per typical session
- **Offline Mode**: Core features available offline

## Test Structure

```
tests/performance/
├── README.md                          # This file
├── requirements-performance.txt       # Performance testing dependencies
├── load_testing/
│   ├── locustfile.py                 # Locust load testing scenarios
│   ├── api_load_test.py              # API endpoint load tests
│   ├── voice_load_test.py            # Voice processing load tests
│   └── image_load_test.py            # Image analysis load tests
├── response_time/
│   ├── test_voice_response_time.py   # Voice processing timing tests
│   ├── test_image_response_time.py   # Image analysis timing tests
│   └── test_api_response_time.py     # API endpoint timing tests
├── network_simulation/
│   ├── test_2g_performance.py        # 2G network simulation tests
│   ├── test_3g_performance.py        # 3G network simulation tests
│   └── network_throttle.py           # Network throttling utilities
├── offline_testing/
│   ├── test_offline_functionality.py # Offline mode tests
│   ├── test_sync_performance.py      # Data sync performance tests
│   └── test_cache_performance.py     # Cache performance tests
├── bundle_analysis/
│   ├── analyze_bundle_size.py        # Bundle size analysis
│   ├── test_asset_optimization.py    # Asset optimization tests
│   └── compression_analysis.py       # Compression effectiveness tests
├── run_performance_tests.py          # Main test runner
└── performance_report.py             # Report generator
```

## Running Performance Tests

### Prerequisites

1. Install performance testing dependencies:
```bash
pip install -r tests/performance/requirements-performance.txt
```

2. Set up test environment:
```bash
export AWS_REGION=us-east-1
export PERFORMANCE_TEST_MODE=true
export TEST_DURATION=300  # 5 minutes
```

### Load Testing

Run load tests with Locust:
```bash
# Start Locust web interface
locust -f tests/performance/load_testing/locustfile.py --host=https://api.rise.example.com

# Run headless load test
locust -f tests/performance/load_testing/locustfile.py --host=https://api.rise.example.com \
  --users 100000 --spawn-rate 1000 --run-time 5m --headless
```

Run specific load tests:
```bash
python tests/performance/load_testing/api_load_test.py
python tests/performance/load_testing/voice_load_test.py
python tests/performance/load_testing/image_load_test.py
```

### Response Time Testing

Run response time validation:
```bash
python tests/performance/response_time/test_voice_response_time.py
python tests/performance/response_time/test_image_response_time.py
python tests/performance/response_time/test_api_response_time.py
```

### Network Simulation Testing

Test 2G/3G performance:
```bash
python tests/performance/network_simulation/test_2g_performance.py
python tests/performance/network_simulation/test_3g_performance.py
```

### Offline Testing

Test offline functionality:
```bash
python tests/performance/offline_testing/test_offline_functionality.py
python tests/performance/offline_testing/test_sync_performance.py
python tests/performance/offline_testing/test_cache_performance.py
```

### Bundle Size Analysis

Analyze bundle sizes:
```bash
python tests/performance/bundle_analysis/analyze_bundle_size.py
python tests/performance/bundle_analysis/test_asset_optimization.py
python tests/performance/bundle_analysis/compression_analysis.py
```

### Run All Performance Tests

Execute complete performance test suite:
```bash
python tests/performance/run_performance_tests.py --all
```

Run specific test categories:
```bash
python tests/performance/run_performance_tests.py --load
python tests/performance/run_performance_tests.py --response-time
python tests/performance/run_performance_tests.py --network
python tests/performance/run_performance_tests.py --offline
python tests/performance/run_performance_tests.py --bundle
```

## Performance Metrics

### Key Performance Indicators (KPIs)

1. **Response Time Metrics**
   - P50 (median) response time
   - P95 response time
   - P99 response time
   - Maximum response time

2. **Throughput Metrics**
   - Requests per second
   - Concurrent users supported
   - Data transfer rate
   - Transaction success rate

3. **Resource Utilization**
   - Lambda execution time
   - Memory usage
   - CPU utilization
   - Network bandwidth

4. **User Experience Metrics**
   - Time to first byte (TTFB)
   - First contentful paint (FCP)
   - Time to interactive (TTI)
   - Cumulative layout shift (CLS)

### Performance Targets

| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| Voice Response | <3s | <5s | >5s |
| Image Analysis | <10s | <15s | >15s |
| API Response | <1s | <2s | >2s |
| Page Load (3G) | <2s | <4s | >4s |
| Concurrent Users | 100K | 50K | <50K |
| Data per Session | <1MB | <2MB | >2MB |
| Offline Sync | <30s | <60s | >60s |

## Test Scenarios

### Load Testing Scenarios

1. **Normal Load**: 10K concurrent users, typical usage patterns
2. **Peak Load**: 100K concurrent users, high activity
3. **Stress Test**: 150K concurrent users, beyond capacity
4. **Spike Test**: Sudden increase from 10K to 100K users
5. **Endurance Test**: 50K users for 24 hours

### User Journey Scenarios

1. **Voice Query Journey**
   - Record voice query
   - Transcribe audio
   - Process query with AI
   - Generate response
   - Synthesize voice response

2. **Image Analysis Journey**
   - Capture/upload image
   - Validate image quality
   - Analyze with AI
   - Generate diagnosis
   - Provide recommendations

3. **Market Intelligence Journey**
   - Request market prices
   - Fetch real-time data
   - Calculate trends
   - Display results
   - Update cache

4. **Offline-to-Online Journey**
   - Work offline
   - Queue operations
   - Detect connectivity
   - Sync data
   - Resolve conflicts

## Network Simulation

### Network Profiles

```python
NETWORK_PROFILES = {
    '2G': {
        'download': 50,      # Kbps
        'upload': 20,        # Kbps
        'latency': 500,      # ms
        'packet_loss': 5     # %
    },
    '3G': {
        'download': 384,     # Kbps
        'upload': 128,       # Kbps
        'latency': 200,      # ms
        'packet_loss': 2     # %
    },
    '4G': {
        'download': 10000,   # Kbps
        'upload': 5000,      # Kbps
        'latency': 50,       # ms
        'packet_loss': 0.5   # %
    }
}
```

### Throttling Implementation

Tests use network throttling to simulate rural connectivity:
- Chrome DevTools Protocol for browser testing
- tc (traffic control) for system-level throttling
- Proxy-based throttling for API testing

## Monitoring and Reporting

### Real-time Monitoring

During load tests, monitor:
- CloudWatch metrics (Lambda, API Gateway, DynamoDB)
- Application performance metrics
- Error rates and types
- Resource utilization

### Performance Reports

Generate comprehensive reports:
```bash
python tests/performance/performance_report.py --output reports/performance_$(date +%Y%m%d).html
```

Reports include:
- Executive summary
- Response time analysis
- Throughput metrics
- Resource utilization
- Bottleneck identification
- Optimization recommendations

## Optimization Strategies

### Response Time Optimization

1. **Caching**
   - CloudFront CDN caching
   - API Gateway caching
   - DynamoDB DAX
   - Redis for sessions

2. **Code Optimization**
   - Lambda function optimization
   - Reduce cold starts
   - Optimize AI model calls
   - Batch processing

3. **Database Optimization**
   - Efficient query patterns
   - Proper indexing
   - Connection pooling
   - Read replicas

### Network Optimization

1. **Compression**
   - Gzip/Brotli compression
   - Image optimization (WebP)
   - Minification (JS/CSS)
   - Delta sync

2. **Resource Loading**
   - Lazy loading
   - Code splitting
   - Progressive enhancement
   - Critical CSS inline

3. **Data Efficiency**
   - Batch requests
   - Incremental updates
   - Pagination
   - Field filtering

### Scalability Optimization

1. **Auto-scaling**
   - Lambda concurrency limits
   - DynamoDB auto-scaling
   - API Gateway throttling
   - CloudFront distribution

2. **Load Distribution**
   - Multi-region deployment
   - Edge locations
   - Load balancing
   - Request routing

## Troubleshooting

### Common Performance Issues

1. **High Response Times**
   - Check Lambda cold starts
   - Review database queries
   - Verify caching effectiveness
   - Monitor external API calls

2. **Throughput Bottlenecks**
   - Check Lambda concurrency limits
   - Review DynamoDB capacity
   - Verify API Gateway limits
   - Monitor network bandwidth

3. **Memory Issues**
   - Profile Lambda memory usage
   - Optimize data structures
   - Implement streaming
   - Clear unused resources

4. **Network Problems**
   - Check CDN configuration
   - Verify compression settings
   - Review asset sizes
   - Monitor latency

## Best Practices

### Performance Testing Best Practices

1. **Test Early and Often**: Run performance tests throughout development
2. **Realistic Scenarios**: Use production-like data and usage patterns
3. **Baseline Metrics**: Establish performance baselines for comparison
4. **Continuous Monitoring**: Track performance trends over time
5. **Optimize Iteratively**: Make incremental improvements

### Load Testing Best Practices

1. **Gradual Ramp-up**: Increase load gradually to identify breaking points
2. **Sustained Load**: Test under sustained load to identify memory leaks
3. **Spike Testing**: Test sudden load increases
4. **Geographic Distribution**: Test from multiple regions
5. **Failure Scenarios**: Test behavior under partial failures

## CI/CD Integration

### Automated Performance Testing

```yaml
# .github/workflows/performance-tests.yml
name: Performance Tests
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Performance Tests
        run: |
          pip install -r tests/performance/requirements-performance.txt
          python tests/performance/run_performance_tests.py --all
      - name: Generate Report
        run: python tests/performance/performance_report.py
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: performance-report
          path: reports/
```

### Performance Budgets

Set performance budgets in CI/CD:
```json
{
  "budgets": {
    "voice_response_p95": 3000,
    "image_analysis_p95": 10000,
    "api_response_p95": 1000,
    "bundle_size": 1048576,
    "data_per_session": 1048576
  }
}
```

## Contributing

When adding new performance tests:
1. Follow existing test structure
2. Document test scenarios
3. Set clear performance targets
4. Include monitoring and reporting
5. Update this README

## Support

For performance testing issues:
- Check CloudWatch logs
- Review performance reports
- Consult AWS service limits
- Contact DevOps team
