# RISE Resource Alert System

## Overview

The Resource Alert System proactively monitors unused agricultural equipment and sends intelligent notifications to equipment owners about potential income opportunities. This system helps maximize equipment utilization and generates additional income for farmers through the equipment sharing marketplace.

## Features

### 🔍 Unused Equipment Detection
- Automatically identifies equipment that hasn't been used or booked for 30+ days
- Excludes newly listed equipment to avoid false alerts
- Tracks last usage timestamp and booking history
- Configurable inactivity thresholds

### 💰 Income Calculation
- Calculates potential monthly and yearly income from equipment sharing
- Equipment-specific utilization rates based on market data:
  - Tractors: 60% utilization
  - Harvesters: 50% utilization
  - Pumps: 40% utilization
  - Drones: 30% utilization
- Computes opportunity cost (lost income due to non-sharing)
- Provides realistic income estimates

### 🔔 Proactive Alerts
- Multilingual alert messages (9 Indic languages + English)
- Voice notifications using Amazon Polly
- SMS and push notification support
- Personalized messages with income estimates
- Quiet hours support to avoid disturbing farmers

### ⚙️ Alert Preferences Management
- Enable/disable alerts
- Configure alert frequency (daily, weekly, monthly)
- Set custom inactivity thresholds
- Choose notification channels (voice, SMS, push)
- Set quiet hours for no disturbances

### 📅 Automated Scheduling
- Daily checks at 9 AM IST
- Weekly comprehensive analysis every Monday
- Monthly deep analysis on 1st of each month
- Seasonal checks during Kharif and Rabi seasons
- EventBridge-powered automation

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Resource Alert System Architecture            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │   EventBridge    │─────▶│  Alert Lambda    │        │
│  │   Schedulers     │      │    Function      │        │
│  └──────────────────┘      └──────────────────┘        │
│                                     │                   │
│                                     ▼                   │
│  ┌──────────────────────────────────────────────┐      │
│  │        Resource Alert Tools                  │      │
│  │  • Find Unused Resources                     │      │
│  │  • Calculate Potential Income                │      │
│  │  • Generate Multilingual Alerts              │      │
│  │  • Manage Alert Preferences                  │      │
│  └──────────────────────────────────────────────┘      │
│                     │                                   │
│         ┌───────────┼───────────┐                       │
│         ▼           ▼           ▼                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │ Resource │ │ Bookings │ │   User   │               │
│  │  Table   │ │  Table   │ │  Table   │               │
│  └──────────┘ └──────────┘ └──────────┘               │
│                                                          │
│  ┌──────────────────────────────────────────────┐      │
│  │        Voice Tools Integration               │      │
│  │  • Amazon Polly (Text-to-Speech)             │      │
│  │  • Multilingual Voice Synthesis              │      │
│  └──────────────────────────────────────────────┘      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- Python 3.8+
- AWS Account with configured credentials
- DynamoDB tables: RISE-ResourceSharing, RISE-ResourceBookings, RISE-UserProfiles
- Amazon Polly access for voice notifications

### Setup

```bash
# Install dependencies
pip install boto3

# Set AWS credentials
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

## Usage

### 1. Find Unused Resources

```python
from tools.resource_alert_tools import ResourceAlertTools

alert_tools = ResourceAlertTools(region='us-east-1')

# Find equipment unused for 30+ days
result = alert_tools.find_unused_resources(days_threshold=30)

if result['success']:
    print(f"Found {result['count']} unused resources")
    for resource in result['unused_resources']:
        print(f"{resource['equipment_name']}: {resource['days_unused']} days unused")
```

### 2. Calculate Potential Income

```python
resource = {
    'equipment_name': 'John Deere Tractor',
    'equipment_type': 'tractor',
    'daily_rate': 3000,
    'days_unused': 30
}

income_result = alert_tools.calculate_potential_income(resource)

if income_result['success']:
    print(f"Monthly Income: ₹{income_result['estimated_monthly_income']:.2f}")
    print(f"Yearly Income: ₹{income_result['estimated_yearly_income']:.2f}")
    print(f"Opportunity Cost: ₹{income_result['opportunity_cost']:.2f}")
```

### 3. Send Alert to Owner

```python
resource = {
    'resource_id': 'res_12345',
    'owner_user_id': 'farmer_001',
    'equipment_name': 'Tractor',
    'equipment_type': 'tractor',
    'daily_rate': 3000,
    'days_unused': 30,
    'location': {
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
}

alert_result = alert_tools.send_unused_resource_alert(resource, user_language='hi')

if alert_result['success']:
    print(f"Alert sent! Message: {alert_result['alert_message']}")
```

### 4. Send Batch Alerts

```python
# Send alerts for all unused equipment
batch_result = alert_tools.send_batch_alerts(days_threshold=30)

if batch_result['success']:
    print(f"Alerts sent: {batch_result['alerts_sent']}")
    print(f"Alerts failed: {batch_result['alerts_failed']}")
```

### 5. Manage Alert Preferences

```python
# Get current preferences
prefs = alert_tools.get_alert_preferences('farmer_001')

# Update preferences
new_prefs = {
    'alert_frequency': 'daily',
    'alert_threshold_days': 15,
    'alert_channels': ['voice', 'sms', 'push'],
    'quiet_hours': {
        'enabled': True,
        'start': '22:00',
        'end': '07:00'
    }
}

update_result = alert_tools.update_alert_preferences('farmer_001', new_prefs)
```

## Lambda Function

### Deployment

```python
# Deploy using AWS CDK
from aws_cdk import aws_lambda as lambda_

alert_lambda = lambda_.Function(
    self, "ResourceAlertFunction",
    runtime=lambda_.Runtime.PYTHON_3_9,
    handler="resource_alert_lambda.lambda_handler",
    code=lambda_.Code.from_asset("tools"),
    timeout=Duration.seconds(60),
    memory_size=512,
    environment={
        'AWS_REGION': 'us-east-1'
    }
)
```

### API Gateway Integration

```bash
# Find unused resources
POST /api/v1/community/resource-alerts/{user_id}
{
    "action": "find_unused",
    "days_threshold": 30
}

# Send alert
POST /api/v1/community/resource-alerts/{user_id}
{
    "action": "send_alert",
    "resource": {...},
    "user_language": "hi"
}

# Get preferences
POST /api/v1/community/resource-alerts/{user_id}
{
    "action": "get_preferences",
    "user_id": "farmer_001"
}

# Update preferences
POST /api/v1/community/resource-alerts/{user_id}
{
    "action": "update_preferences",
    "user_id": "farmer_001",
    "preferences": {...}
}
```

## EventBridge Scheduling

### Automated Alert Schedules

```python
from infrastructure.eventbridge_alert_rules import create_alert_rules

# Create EventBridge rules
alert_rules = create_alert_rules(scope, alert_lambda)

# Schedules:
# - Daily: 9 AM IST (3:30 AM UTC)
# - Weekly: Monday 10 AM IST (4:30 AM UTC)
# - Monthly: 1st of month, 11 AM IST (5:30 AM UTC)
# - Seasonal: During Kharif (June-July) and Rabi (Oct-Nov) seasons
```

## Multilingual Support

### Supported Languages

| Language | Code | Voice Support |
|----------|------|---------------|
| Hindi | hi | ✅ |
| English | en | ✅ |
| Tamil | ta | ✅ |
| Telugu | te | ✅ |
| Kannada | kn | ✅ |
| Bengali | bn | ✅ |
| Gujarati | gu | ✅ |
| Marathi | mr | ✅ |
| Punjabi | pa | ✅ |

### Alert Message Example (Hindi)

```
🚜 उपकरण साझाकरण अवसर!

आपका John Deere Tractor पिछले 30 दिनों से उपयोग नहीं हुआ है।

💰 संभावित आय:
• मासिक आय: ₹54000
• खोई हुई आय: ₹54000

क्या आप इसे साझा करना चाहेंगे और अतिरिक्त आय अर्जित करना चाहेंगे?

अभी सूचीबद्ध करें और अपने समुदाय की मदद करें!
```

## Testing

### Run Unit Tests

```bash
# Run all tests
python -m pytest tests/test_resource_alerts.py -v

# Run specific test
python -m pytest tests/test_resource_alerts.py::TestResourceAlertTools::test_find_unused_resources_success -v

# Run with coverage
python -m pytest tests/test_resource_alerts.py --cov=tools.resource_alert_tools --cov-report=html
```

### Test Coverage

- ✅ Find unused resources
- ✅ Calculate potential income
- ✅ Generate multilingual alerts
- ✅ Send individual alerts
- ✅ Send batch alerts
- ✅ Get alert preferences
- ✅ Update alert preferences
- ✅ Voice notification integration

## UI Components

### Streamlit Interface

```python
from ui.alert_preferences import render_alert_preferences, render_unused_equipment_dashboard

# Render alert preferences
render_alert_preferences(user_id='farmer_001')

# Render unused equipment dashboard
render_unused_equipment_dashboard(user_id='farmer_001')
```

### Features
- Interactive preference management
- Real-time unused equipment dashboard
- Income opportunity visualization
- One-click equipment listing
- Alert dismissal

## Performance Considerations

### Optimization Strategies

1. **Batch Processing**: Process alerts in batches to reduce API calls
2. **Caching**: Cache user preferences to minimize DynamoDB reads
3. **Parallel Processing**: Send alerts concurrently using threading
4. **Throttling**: Respect AWS service limits (Polly: 100 TPS)
5. **Pagination**: Handle large result sets with DynamoDB pagination

### Cost Optimization

- **DynamoDB**: Use on-demand billing for unpredictable traffic
- **Lambda**: Optimize memory and timeout settings
- **Polly**: Cache generated audio for repeated messages
- **EventBridge**: Use appropriate scheduling frequency

## Monitoring

### CloudWatch Metrics

```python
# Custom metrics to track
- UnusedResourcesFound
- AlertsSent
- AlertsFailed
- VoiceNotificationsGenerated
- PreferencesUpdated
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Log levels:
# INFO: Normal operations
# WARNING: Recoverable errors
# ERROR: Critical failures
```

## Troubleshooting

### Common Issues

**Issue**: No unused resources found
- **Solution**: Check `days_threshold` parameter and verify equipment has `last_used_timestamp`

**Issue**: Voice notification fails
- **Solution**: Verify Amazon Polly permissions and language code validity

**Issue**: Alert preferences not saving
- **Solution**: Check DynamoDB table permissions and user_id validity

**Issue**: EventBridge not triggering
- **Solution**: Verify Lambda permissions and EventBridge rule status

## Best Practices

1. **Set Appropriate Thresholds**: Use 30 days for general alerts, 15 days during peak seasons
2. **Respect Quiet Hours**: Don't send alerts during farmer rest times (10 PM - 7 AM)
3. **Personalize Messages**: Use farmer's preferred language and include local context
4. **Provide Value**: Always include income estimates to motivate action
5. **Enable Opt-Out**: Allow farmers to disable or customize alerts
6. **Monitor Performance**: Track alert open rates and equipment listing conversions

## Future Enhancements

- 🔮 Predictive analytics for seasonal demand
- 📊 Equipment utilization trends and insights
- 🤝 Peer comparison (how others are earning)
- 💬 Two-way communication for alert responses
- 📱 Mobile app push notifications
- 🎯 Targeted alerts based on nearby demand

## Support

For issues or questions:
- GitHub Issues: [RISE Repository](https://github.com/your-org/rise)
- Email: support@rise-farming.com
- Documentation: [RISE Docs](https://docs.rise-farming.com)

## License

Copyright © 2024 RISE - Rural Innovation and Sustainable Ecosystem
