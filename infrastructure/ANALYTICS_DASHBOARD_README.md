# RISE Analytics Dashboard

## Overview

The RISE Analytics Dashboard provides comprehensive monitoring and reporting for the RISE farming assistant platform. It tracks user adoption, impact metrics, technical performance, feature adoption, and resource sharing metrics to measure platform success against defined KPIs.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Analytics Dashboard System                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐         ┌──────────────────────┐     │
│  │   Streamlit UI   │◄────────┤  Analytics Lambda    │     │
│  │   (Dashboard)    │         │    (Aggregator)      │     │
│  └──────────────────┘         └──────────────────────┘     │
│           │                              │                 │
│           │                              │                 │
│           ▼                              ▼                 │
│  ┌──────────────────┐         ┌──────────────────────┐     │
│  │   CloudWatch     │         │     DynamoDB         │     │
│  │    Metrics       │         │   (Farm Data)        │     │
│  └──────────────────┘         └──────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Analytics Aggregator (`infrastructure/analytics_aggregator.py`)

Lambda function that aggregates metrics from CloudWatch and DynamoDB.

**Key Features:**
- User adoption metrics collection
- Impact metrics calculation
- Technical performance monitoring
- Feature adoption tracking
- Resource sharing analytics
- Comprehensive report generation

**Metrics Collected:**

#### User Adoption Metrics
- Active users count
- Average session duration
- Return rate
- Language distribution

#### Impact Metrics
- Yield improvement (average, max, min)
- Cost reduction (total savings in INR)
- Market access (users and percentage)
- Scheme adoption (users and percentage)

#### Technical Performance Metrics
- Response time (average and P99)
- Diagnosis accuracy
- Pest identification accuracy
- System uptime

#### Feature Adoption Metrics
- Usage count per feature
- Success rate per feature
- Features tracked:
  - Crop diagnosis
  - Pest identification
  - Soil analysis
  - Weather alerts
  - Market prices
  - Buyer connection
  - Government schemes
  - Profitability calculator
  - Equipment sharing
  - Cooperative buying

#### Resource Sharing Metrics
- Equipment utilization rate
- Cooperative buying savings
- Total savings from bulk purchases

### 2. Streamlit Dashboard (`ui/analytics_dashboard.py`)

Interactive web-based admin dashboard for visualizing analytics.

**Features:**
- Time period selection (24 hours, 7 days, 30 days, custom)
- Overview metrics cards
- Interactive charts and visualizations
- Multiple tabs for different metric categories
- Real-time data refresh
- Mock data support for development

**Dashboard Tabs:**
1. **User Adoption** - Session metrics and language distribution
2. **Impact Metrics** - Yield, cost, market, and scheme metrics
3. **Performance** - Response time, accuracy, and uptime
4. **Feature Adoption** - Usage and success rates by feature
5. **Resource Sharing** - Equipment and cooperative buying metrics

## Setup and Deployment

### Prerequisites

```bash
# Install required packages
pip install boto3 streamlit plotly
```

### AWS Configuration

1. **Deploy Analytics Lambda Function:**

```bash
# Package Lambda function
cd infrastructure
zip -r analytics_aggregator.zip analytics_aggregator.py

# Deploy using AWS CLI
aws lambda create-function \
  --function-name rise-analytics-aggregator \
  --runtime python3.9 \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role \
  --handler analytics_aggregator.lambda_handler \
  --zip-file fileb://analytics_aggregator.zip \
  --timeout 60 \
  --memory-size 512
```

2. **Configure IAM Permissions:**

The Lambda function needs the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/RISE-*"
      ]
    }
  ]
}
```

### Running the Dashboard

#### Local Development

```bash
# Run Streamlit dashboard
streamlit run ui/analytics_dashboard.py
```

The dashboard will open at `http://localhost:8501`

#### Production Deployment

Deploy to AWS using:
- **EC2 instance** with Streamlit
- **ECS/Fargate** container
- **App Runner** for serverless deployment

Example App Runner deployment:

```bash
# Create Dockerfile
cat > Dockerfile << EOF
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "ui/analytics_dashboard.py", "--server.port=8501"]
EOF

# Deploy to App Runner
aws apprunner create-service \
  --service-name rise-analytics-dashboard \
  --source-configuration file://apprunner-config.json
```

## Usage Examples

### 1. Generate Comprehensive Report

```python
from infrastructure.analytics_aggregator import AnalyticsAggregator
from datetime import datetime, timedelta

aggregator = AnalyticsAggregator()

end_time = datetime.now()
start_time = end_time - timedelta(days=30)

report = aggregator.generate_comprehensive_report(start_time, end_time)

print(f"Active Users: {report['user_adoption']['active_users']}")
print(f"Yield Improvement: {report['impact_metrics']['yield_improvement']['average_percent']}%")
print(f"System Uptime: {report['technical_performance']['uptime']['percent']}%")
```

### 2. Get User Adoption Metrics

```python
metrics = aggregator.get_user_adoption_metrics(start_time, end_time)

print(f"Active Users: {metrics['active_users']}")
print(f"Avg Session Duration: {metrics['avg_session_duration_minutes']} min")
print(f"Return Rate: {metrics['return_rate_percent']}%")

for lang, count in metrics['language_distribution'].items():
    print(f"{lang}: {count} users")
```

### 3. Get Impact Metrics

```python
impact = aggregator.get_impact_metrics(start_time, end_time)

yield_data = impact['yield_improvement']
print(f"Yield Improvement: {yield_data['average_percent']}%")
print(f"Target Met: {yield_data['meets_target']}")

cost_data = impact['cost_reduction']
print(f"Total Savings: ₹{cost_data['total_savings_inr']:,.2f}")
```

### 4. Invoke Lambda Function

```python
import boto3
import json

lambda_client = boto3.client('lambda')

payload = {
    'action': 'generate_report',
    'start_time': '2024-01-01T00:00:00Z',
    'end_time': '2024-01-31T23:59:59Z'
}

response = lambda_client.invoke(
    FunctionName='rise-analytics-aggregator',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

result = json.loads(response['Payload'].read())
report = json.loads(result['body'])
```

### 5. Run Streamlit Dashboard

```bash
# Basic usage
streamlit run ui/analytics_dashboard.py

# With custom port
streamlit run ui/analytics_dashboard.py --server.port=8080

# With custom configuration
streamlit run ui/analytics_dashboard.py --server.headless=true
```

## Success Metrics and KPIs

### User Adoption Targets

| Metric | Target | Current Status |
|--------|--------|----------------|
| Active Users | 10,000+ | Tracked |
| Avg Session Duration | 15+ minutes | Tracked |
| Return Rate | 70%+ | Tracked |
| Language Coverage | 9 languages | Tracked |

### Impact Targets

| Metric | Target | Current Status |
|--------|--------|----------------|
| Yield Improvement | 15-25% | Tracked |
| Cost Reduction | 20-30% | Tracked |
| Market Access | 40%+ | Tracked |
| Scheme Adoption | 60%+ | Tracked |

### Technical Performance Targets

| Metric | Target | Current Status |
|--------|--------|----------------|
| Response Time | <3 seconds | Tracked |
| Diagnosis Accuracy | >90% | Tracked |
| Pest ID Accuracy | >85% | Tracked |
| System Uptime | 99.5%+ | Tracked |

## Dashboard Features

### Overview Metrics

The dashboard displays key metrics at a glance:
- Active users count
- Average yield improvement
- Total cost savings
- System uptime

### Interactive Visualizations

- **Pie Charts** - Language distribution
- **Bar Charts** - Feature usage and success rates
- **Gauge Charts** - Equipment utilization
- **Progress Bars** - Target achievement tracking
- **Metric Cards** - Key performance indicators

### Time Period Selection

Users can select different time periods:
- Last 24 Hours
- Last 7 Days
- Last 30 Days
- Custom Range (date picker)

### Data Refresh

- Manual refresh button in sidebar
- Automatic data fetching on time period change
- Loading indicators during data fetch

## API Reference

### AnalyticsAggregator Class

#### `__init__(region: str = "us-east-1")`
Initialize the analytics aggregator.

#### `get_user_adoption_metrics(start_time: datetime, end_time: datetime) -> Dict`
Get user adoption metrics for the specified time period.

**Returns:**
```python
{
    'active_users': int,
    'avg_session_duration_seconds': int,
    'avg_session_duration_minutes': float,
    'return_rate_percent': float,
    'language_distribution': Dict[str, int]
}
```

#### `get_impact_metrics(start_time: datetime, end_time: datetime) -> Dict`
Get impact metrics for the specified time period.

**Returns:**
```python
{
    'yield_improvement': {
        'average_percent': float,
        'maximum_percent': float,
        'minimum_percent': float,
        'target_range': str,
        'meets_target': bool
    },
    'cost_reduction': {
        'total_savings_inr': float,
        'target_range': str
    },
    'market_access': {
        'users_count': int,
        'percent': float,
        'target': str,
        'meets_target': bool
    },
    'scheme_adoption': {
        'users_count': int,
        'percent': float,
        'target': str,
        'meets_target': bool
    }
}
```

#### `get_technical_performance_metrics(start_time: datetime, end_time: datetime) -> Dict`
Get technical performance metrics.

#### `get_feature_adoption_metrics(start_time: datetime, end_time: datetime) -> Dict`
Get feature adoption metrics for all major features.

#### `get_resource_sharing_metrics(start_time: datetime, end_time: datetime) -> Dict`
Get resource sharing and cooperative buying metrics.

#### `generate_comprehensive_report(start_time: datetime, end_time: datetime) -> Dict`
Generate a comprehensive analytics report with all metrics.

### Lambda Handler

#### `lambda_handler(event, context)`
AWS Lambda handler for analytics aggregation.

**Event Format:**
```python
{
    'action': 'generate_report' | 'user_adoption' | 'impact_metrics' | 'technical_performance',
    'start_time': 'ISO 8601 timestamp',
    'end_time': 'ISO 8601 timestamp'
}
```

**Response Format:**
```python
{
    'statusCode': 200,
    'body': JSON string with metrics
}
```

## Testing

### Run Unit Tests

```bash
# Run all analytics tests
pytest tests/test_analytics_dashboard.py -v

# Run specific test class
pytest tests/test_analytics_dashboard.py::TestAnalyticsAggregator -v

# Run with coverage
pytest tests/test_analytics_dashboard.py --cov=infrastructure.analytics_aggregator --cov-report=html
```

### Test Coverage

The test suite includes:
- Analytics aggregator initialization
- User adoption metrics retrieval
- Impact metrics calculation
- Technical performance tracking
- Feature adoption monitoring
- Resource sharing analytics
- Lambda handler testing
- Dashboard UI testing
- Mock data generation

## Troubleshooting

### Common Issues

#### 1. Lambda Function Not Found

**Error:** `Function not found: rise-analytics-aggregator`

**Solution:**
- Verify Lambda function is deployed
- Check function name matches exactly
- Ensure AWS credentials have Lambda invoke permissions

#### 2. CloudWatch Metrics Not Available

**Error:** `No datapoints returned from CloudWatch`

**Solution:**
- Verify custom metrics are being emitted
- Check time range includes data
- Ensure CloudWatch permissions are configured
- Wait for metrics to propagate (up to 5 minutes)

#### 3. Dashboard Shows Mock Data

**Issue:** Dashboard always shows mock data instead of real metrics

**Solution:**
- Check AWS credentials are configured
- Verify Lambda function is accessible
- Check network connectivity to AWS
- Review CloudWatch Logs for errors

#### 4. Slow Dashboard Performance

**Issue:** Dashboard takes long time to load

**Solution:**
- Reduce time range for queries
- Use caching for frequently accessed data
- Optimize CloudWatch queries
- Consider pre-aggregating metrics

## Cost Estimation

### Monthly Costs

| Service | Usage | Estimated Cost |
|---------|-------|----------------|
| Lambda (Analytics) | 10,000 invocations/month | $0.20 |
| CloudWatch Metrics | 30 custom metrics | $9.00 |
| CloudWatch API Calls | 100,000 calls/month | $0.01 |
| DynamoDB Reads | 1M reads/month | $0.25 |
| Streamlit Hosting (EC2 t3.small) | 730 hours/month | $15.00 |

**Total Estimated Cost: ~$25/month**

## Best Practices

### 1. Data Aggregation

- Aggregate metrics at appropriate intervals (hourly for most metrics)
- Use CloudWatch metric math for complex calculations
- Cache frequently accessed metrics
- Pre-aggregate data for common time ranges

### 2. Performance Optimization

- Limit CloudWatch API calls with caching
- Use batch operations for DynamoDB queries
- Implement pagination for large datasets
- Optimize dashboard rendering with lazy loading

### 3. Security

- Use IAM roles with least privilege
- Enable CloudWatch Logs encryption
- Implement authentication for dashboard access
- Audit dashboard access logs

### 4. Monitoring

- Set up alarms for analytics Lambda errors
- Monitor dashboard access patterns
- Track metric collection failures
- Alert on missing data

## Future Enhancements

### Planned Features

1. **Automated Reports**
   - Scheduled email reports
   - PDF report generation
   - Custom report templates

2. **Advanced Analytics**
   - Predictive analytics
   - Trend analysis
   - Anomaly detection
   - Cohort analysis

3. **Export Capabilities**
   - CSV export
   - Excel export
   - API for external tools

4. **Custom Dashboards**
   - User-configurable widgets
   - Saved dashboard layouts
   - Role-based views

5. **Real-time Updates**
   - WebSocket integration
   - Live metric streaming
   - Push notifications

## Support

For issues or questions:
- Check CloudWatch Logs for Lambda errors
- Review Streamlit logs for dashboard issues
- Consult AWS documentation for service-specific problems
- Contact the RISE development team

## References

- [AWS CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Documentation](https://plotly.com/python/)
- [RISE Monitoring README](./MONITORING_README.md)

---

**Last Updated:** 2024
**Version:** 1.0.0
**Maintainer:** RISE Development Team
