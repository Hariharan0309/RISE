

# RISE Application Monitoring System

Comprehensive monitoring solution for the RISE farming assistant platform, providing real-time insights into application performance, agricultural metrics, errors, and costs.

## Overview

The RISE monitoring system provides:

- **CloudWatch Alarms** for all Lambda functions, API Gateway, and DynamoDB
- **Custom Agricultural Metrics** tracking diagnosis accuracy, user engagement, yield improvements, and cost savings
- **Error Tracking** with CloudWatch Logs Insights and automated alerting
- **Cost Monitoring** with budget alerts and optimization recommendations
- **Interactive Dashboards** for visualizing all metrics and KPIs

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  RISE Monitoring System                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │  CloudWatch      │  │  Custom          │               │
│  │  Alarms          │  │  Metrics         │               │
│  │  - Lambda        │  │  - Diagnosis     │               │
│  │  - API Gateway   │  │  - Engagement    │               │
│  │  - DynamoDB      │  │  - Yield         │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │  Error           │  │  Cost            │               │
│  │  Tracking        │  │  Monitoring      │               │
│  │  - Log Groups    │  │  - Budgets       │               │
│  │  - Metric        │  │  - Forecasts     │               │
│  │    Filters       │  │  - Optimization  │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                             │
│  ┌─────────────────────────────────────────┐               │
│  │         CloudWatch Dashboards           │               │
│  │  - Lambda Overview                      │               │
│  │  - Agricultural Metrics                 │               │
│  │  - API Gateway Performance              │               │
│  │  - DynamoDB Capacity                    │               │
│  │  - Cost Analysis                        │               │
│  └─────────────────────────────────────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Monitoring Configuration (`monitoring_config.py`)

Centralized configuration for all monitoring components.

**Key Features:**
- Lambda function monitoring configurations with thresholds
- Custom agricultural metrics definitions
- API Gateway and DynamoDB monitoring settings
- Cost monitoring budgets and thresholds
- Error tracking patterns

**Usage:**
```python
from infrastructure.monitoring_config import get_lambda_config, get_all_lambda_functions

# Get configuration for a specific function
config = get_lambda_config('image_analysis')
print(f"Function: {config.function_name}")
print(f"Error threshold: {config.error_threshold}%")
print(f"Duration threshold: {config.duration_threshold_ms}ms")

# Get all Lambda functions
functions = get_all_lambda_functions()
print(f"Monitoring {len(functions)} Lambda functions")
```

### 2. CloudWatch Alarms (`cloudwatch_alarms.py`)

Creates and manages CloudWatch alarms for all services.

**Alarm Types:**
- **Lambda Alarms:**
  - Error rate (percentage threshold)
  - Duration (milliseconds threshold)
  - Throttles (count threshold)
  - Concurrent executions (count threshold)
  - Low invocations (monitoring for issues)

- **API Gateway Alarms:**
  - Latency (milliseconds threshold)
  - 4XX errors (count threshold)
  - 5XX errors (count threshold)

- **DynamoDB Alarms:**
  - Read throttles
  - Write throttles
  - System errors

**Usage:**
```python
from infrastructure.cloudwatch_alarms import CloudWatchAlarmsManager

# Initialize manager
sns_topic_arn = "arn:aws:sns:us-east-1:123456789012:rise-alerts"
manager = CloudWatchAlarmsManager(sns_topic_arn)

# Create alarms for a Lambda function
alarms = manager.create_lambda_alarms('image_analysis')
print(f"Created {len(alarms)} alarms")

# Create API Gateway alarms
api_alarms = manager.create_api_gateway_alarms()

# Create DynamoDB alarms
db_alarms = manager.create_dynamodb_alarms('RISE-DiagnosisHistory')

# Create all alarms at once
all_alarms = manager.create_all_alarms()
```

### 3. Custom Metrics (`custom_metrics.py`)

Tracks custom agricultural and business metrics.

**Agricultural Metrics:**
- **Diagnosis Accuracy:** Crop disease identification accuracy rate
- **Pest Identification Accuracy:** Pest identification accuracy rate
- **User Engagement:** Active users, session duration, features used
- **Yield Improvement:** Percentage yield increase for farmers
- **Cost Savings:** Total cost savings achieved (in INR)
- **Equipment Utilization:** Resource sharing utilization rate
- **Bulk Purchase Savings:** Cooperative buying savings percentage
- **Scheme Application Success:** Government scheme approval rate

**Usage:**
```python
from infrastructure.custom_metrics import CustomMetricsTracker

tracker = CustomMetricsTracker()

# Track diagnosis accuracy
tracker.track_diagnosis_accuracy(
    diagnosis_id="diag_12345",
    predicted_disease="Late Blight",
    actual_disease="Late Blight",
    confidence_score=92.5,
    user_feedback="helpful"
)

# Track user engagement
tracker.track_user_engagement(
    user_id="user_67890",
    session_duration_seconds=1200,
    features_used=["crop_diagnosis", "weather_alerts"],
    language="hi"
)

# Track yield improvement
tracker.track_yield_improvement(
    user_id="user_67890",
    crop_type="wheat",
    baseline_yield=2.5,
    current_yield=3.2,
    season="rabi_2024"
)

# Track cost savings
tracker.track_cost_savings(
    user_id="user_67890",
    savings_type="fertilizer",
    amount_saved_inr=5000,
    category="precision_agriculture"
)
```

### 4. Error Tracking (`error_tracking.py`)

Comprehensive error tracking with CloudWatch Logs Insights.

**Features:**
- Automatic log group creation with retention policies
- Metric filters for error patterns
- Error trend analysis
- Top errors by frequency
- Real-time error alerting

**Usage:**
```python
from infrastructure.error_tracking import ErrorTracker

tracker = ErrorTracker()

# Create log groups for Lambda functions
function_names = ['rise-image-analysis', 'rise-pest-analysis']
tracker.create_log_groups(function_names)

# Create metric filters for error patterns
tracker.create_metric_filters('rise-image-analysis')

# Analyze error trends
trends = tracker.analyze_error_trends(
    function_name="rise-image-analysis",
    hours=24
)
print(f"Total errors: {trends['total_errors']}")
print(f"Average errors per 5min: {trends['average_errors_per_5min']}")

# Get top errors
top_errors = tracker.get_top_errors(
    function_name="rise-image-analysis",
    hours=24,
    limit=10
)
for error in top_errors:
    print(f"Count: {error['count']}, Message: {error['error_message']}")
```

### 5. Cost Monitoring (`cost_monitoring.py`)

Tracks AWS costs and provides optimization recommendations.

**Features:**
- Monthly budget creation with alerts
- Current month cost tracking
- Cost forecasting
- Service-specific cost breakdown
- Cost anomaly detection
- Optimization recommendations

**Usage:**
```python
from infrastructure.cost_monitoring import CostMonitor

account_id = "123456789012"
monitor = CostMonitor(account_id)

# Create monthly budget
monitor.create_monthly_budget(
    budget_name="RISE-Monthly-Budget",
    amount_usd=1000,
    sns_topic_arn="arn:aws:sns:us-east-1:123456789012:rise-alerts",
    alert_thresholds=[50, 75, 90, 100]
)

# Get current month cost
current_cost = monitor.get_current_month_cost()
print(f"Total cost: ${current_cost['total_cost_usd']:.2f}")
for service, cost in current_cost['service_costs'].items():
    print(f"  {service}: ${cost:.2f}")

# Get cost forecast
forecast = monitor.get_cost_forecast(30)
print(f"30-day forecast: ${forecast['forecast_cost_usd']:.2f}")

# Get optimization recommendations
recommendations = monitor.get_cost_optimization_recommendations()
for rec in recommendations:
    print(f"{rec['service']}: {rec['recommendation']}")
    print(f"  Potential savings: {rec['potential_savings_percent']}%")

# Generate comprehensive report
report = monitor.generate_cost_report()
```

### 6. Monitoring Dashboards (`monitoring_dashboard.py`)

Creates interactive CloudWatch dashboards.

**Dashboards:**
- **Lambda Overview:** Invocations, errors, duration, throttles
- **Agricultural Metrics:** Diagnosis accuracy, yield improvement, cost savings
- **API Gateway:** Request count, latency, errors, cache performance
- **DynamoDB:** Read/write capacity, throttles
- **Cost Monitoring:** Total cost, service breakdown

**Usage:**
```python
from infrastructure.monitoring_dashboard import MonitoringDashboard

dashboard = MonitoringDashboard()

# Create individual dashboards
dashboard.create_lambda_overview_dashboard()
dashboard.create_agricultural_metrics_dashboard()
dashboard.create_api_gateway_dashboard()
dashboard.create_dynamodb_dashboard()
dashboard.create_cost_dashboard()

# Create all dashboards at once
dashboard.create_all_dashboards()

# List existing dashboards
dashboards = dashboard.list_dashboards()
print(f"Existing dashboards: {dashboards}")
```

## Setup Instructions

### 1. Prerequisites

- AWS account with appropriate permissions
- AWS CLI configured
- Python 3.8+
- boto3 installed

### 2. Install Dependencies

```bash
pip install boto3
```

### 3. Configure AWS Credentials

```bash
aws configure
```

### 4. Create SNS Topic for Alerts

```bash
aws sns create-topic --name rise-alerts
aws sns subscribe --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:rise-alerts \
    --protocol email --notification-endpoint your-email@example.com
```

### 5. Set Up Monitoring

```python
from infrastructure.cloudwatch_alarms import CloudWatchAlarmsManager
from infrastructure.error_tracking import ErrorTracker
from infrastructure.cost_monitoring import CostMonitor
from infrastructure.monitoring_dashboard import MonitoringDashboard

# Configuration
sns_topic_arn = "arn:aws:sns:us-east-1:ACCOUNT_ID:rise-alerts"
account_id = "ACCOUNT_ID"

# Create alarms
alarm_manager = CloudWatchAlarmsManager(sns_topic_arn)
alarm_manager.create_all_alarms()

# Set up error tracking
error_tracker = ErrorTracker()
function_names = get_all_lambda_functions()
error_tracker.create_log_groups(function_names)

# Create budget
cost_monitor = CostMonitor(account_id)
cost_monitor.create_monthly_budget(
    budget_name="RISE-Monthly-Budget",
    amount_usd=1000,
    sns_topic_arn=sns_topic_arn
)

# Create dashboards
dashboard = MonitoringDashboard()
dashboard.create_all_dashboards()
```

## Monitoring Best Practices

### 1. Alarm Configuration

- **Critical Functions:** Set aggressive thresholds (low error rates, fast response times)
- **Non-Critical Functions:** Set more relaxed thresholds
- **Review Regularly:** Adjust thresholds based on actual usage patterns

### 2. Custom Metrics

- **Track Consistently:** Emit metrics for every relevant operation
- **Use Dimensions:** Add dimensions for filtering and grouping
- **Aggregate Wisely:** Use appropriate statistics (Average, Sum, Max)

### 3. Error Tracking

- **Log Structured Data:** Use JSON for easier querying
- **Include Context:** Add user ID, request ID, timestamps
- **Set Retention:** Balance cost vs. compliance requirements

### 4. Cost Optimization

- **Monitor Daily:** Check costs daily during initial deployment
- **Set Budgets:** Create budgets with multiple alert thresholds
- **Review Recommendations:** Act on optimization recommendations

### 5. Dashboard Usage

- **Check Daily:** Review dashboards daily for anomalies
- **Share with Team:** Make dashboards accessible to all team members
- **Customize Views:** Create role-specific dashboards

## Troubleshooting

### High Error Rates

1. Check error tracking dashboard
2. Query CloudWatch Logs for specific errors
3. Review recent deployments
4. Check service dependencies

### High Costs

1. Review cost monitoring dashboard
2. Check service-specific costs
3. Review optimization recommendations
4. Analyze usage patterns

### Missing Metrics

1. Verify metric emission in code
2. Check CloudWatch namespace and dimensions
3. Verify IAM permissions
4. Check metric retention period

## Integration with Lambda Functions

Add monitoring to your Lambda functions:

```python
from infrastructure.custom_metrics import CustomMetricsTracker

def lambda_handler(event, context):
    tracker = CustomMetricsTracker()
    
    try:
        # Your function logic
        result = process_diagnosis(event)
        
        # Track success metrics
        tracker.track_diagnosis_accuracy(
            diagnosis_id=result['diagnosis_id'],
            predicted_disease=result['disease'],
            confidence_score=result['confidence']
        )
        
        tracker.track_feature_usage(
            feature_name='crop_diagnosis',
            user_id=event['user_id'],
            success=True,
            duration_ms=context.get_remaining_time_in_millis()
        )
        
        return result
        
    except Exception as e:
        # Track failure
        tracker.track_feature_usage(
            feature_name='crop_diagnosis',
            user_id=event.get('user_id', 'unknown'),
            success=False
        )
        raise
```

## Monitoring Costs

The monitoring system itself incurs costs:

- **CloudWatch Alarms:** $0.10 per alarm per month
- **CloudWatch Logs:** $0.50 per GB ingested
- **CloudWatch Dashboards:** $3.00 per dashboard per month
- **Custom Metrics:** $0.30 per metric per month

**Estimated Monthly Cost:** $50-100 for comprehensive monitoring

## Support

For issues or questions:
- Check CloudWatch Logs for error details
- Review alarm history in CloudWatch console
- Consult AWS documentation for service-specific issues

## License

Part of the RISE platform - AI for Bharat Hackathon submission
