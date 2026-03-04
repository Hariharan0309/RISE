# RISE Resource Availability Alert System

## Overview

The Resource Availability Alert System provides intelligent, location-based notifications for farmers about equipment availability, bulk buying opportunities, and seasonal resource demands. It uses AI-powered predictions and automated scheduling to maximize resource utilization and cost savings.

## Features

### 1. Equipment Availability Alerts
- **Location-based notifications** within 25km radius
- Real-time alerts when equipment becomes available
- Customizable equipment type preferences
- Distance and cost calculations
- Multi-language support (Hindi, English, Tamil, Telugu, etc.)

### 2. Bulk Buying Opportunity Alerts
- Notifications for new cooperative buying groups
- Potential savings calculations (15-30% discounts)
- Product interest matching
- Minimum discount threshold filtering
- Group member count and deadline information

### 3. Seasonal Demand Prediction
- AI-powered demand forecasting using Amazon Bedrock
- 90-day advance predictions
- Equipment needs based on crop calendar
- Peak demand period identification
- Booking timeline recommendations
- Cost optimization strategies

### 4. Advance Booking System
- Book equipment 30-90 days in advance
- Automatic equipment matching
- Distance-based search (50km radius)
- Cost estimation
- 7-day advance reminders
- Booking confirmation and tracking

### 5. Optimal Sharing Schedule
- AI-generated utilization schedules
- Revenue projection calculations
- Maintenance window planning
- Demand pattern analysis
- Utilization rate optimization (target: 70%+)

### 6. Alert Customization
- Granular preference controls
- Equipment type filtering
- Alert radius customization (5-50km)
- Frequency settings (immediate, daily, weekly)
- Quiet hours configuration
- Multi-channel delivery (voice, SMS, push, email)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Resource Availability Alert System              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────┐    ┌──────────────────────────┐  │
│  │  EventBridge     │───▶│  Lambda Functions        │  │
│  │  Scheduled Rules │    │  - Equipment alerts      │  │
│  │  - Every 2 hours │    │  - Buying group alerts   │  │
│  │  - Every 6 hours │    │  - Seasonal predictions  │  │
│  │  - Daily         │    │  - Booking reminders     │  │
│  └──────────────────┘    └──────────────────────────┘  │
│           │                         │                   │
│           │                         ▼                   │
│           │              ┌──────────────────────────┐   │
│           │              │  Amazon Bedrock          │   │
│           │              │  - Claude 3 Haiku        │   │
│           │              │  - Demand prediction     │   │
│           │              │  - Schedule optimization │   │
│           │              └──────────────────────────┘   │
│           │                         │                   │
│           ▼                         ▼                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │              DynamoDB Tables                     │   │
│  │  - ResourceSharing                               │   │
│  │  - ResourceBookings                              │   │
│  │  - BuyingGroups                                  │   │
│  │  - UserProfiles (with alert preferences)         │   │
│  └──────────────────────────────────────────────────┘   │
│           │                                             │
│           ▼                                             │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Notification Channels                    │   │
│  │  - Amazon SNS (SMS)                              │   │
│  │  - Amazon Polly (Voice)                          │   │
│  │  - Push Notifications                            │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- Python 3.8+
- AWS Account with configured credentials
- boto3 library
- Access to Amazon Bedrock

### Setup

```bash
# Install dependencies
pip install boto3 streamlit

# Set up AWS credentials
aws configure

# Enable Amazon Bedrock models
aws bedrock list-foundation-models --region us-east-1
```

### DynamoDB Tables

Ensure the following tables exist:
- `RISE-ResourceSharing`
- `RISE-ResourceBookings`
- `RISE-BuyingGroups`
- `RISE-UserProfiles`

## Usage

### 1. Equipment Availability Alerts

```python
from tools.availability_alert_tools import create_availability_alert_tools

tools = create_availability_alert_tools()

# Send alerts for newly available equipment
result = tools.send_equipment_availability_alert(
    resource_id='res_abc123',
    radius_km=25
)

print(f"Alerts sent: {result['alerts_sent']}")
```

### 2. Bulk Buying Opportunity Alerts

```python
# Send alerts for new buying group
result = tools.send_bulk_buying_opportunity_alert(
    group_id='grp_xyz789',
    radius_km=25
)

print(f"Potential members notified: {result['alerts_sent']}")
```

### 3. Seasonal Demand Prediction

```python
# Predict equipment needs based on crop calendar
crop_calendar = {
    'rice': {
        'planting_date': '2024-06-15',
        'harvest_date': '2024-11-15',
        'area_acres': 3
    }
}

result = tools.predict_seasonal_demand(
    user_id='user_123',
    crop_calendar=crop_calendar
)

print("Equipment needs:", result['predictions']['equipment_needs'])
print("Peak periods:", result['predictions']['peak_periods'])
```

### 4. Advance Booking

```python
from datetime import datetime, timedelta

# Create advance booking
booking_data = {
    'equipment_type': 'harvester',
    'booking_date': (datetime.now() + timedelta(days=45)).isoformat(),
    'duration_days': 3,
    'location': {
        'district': 'Meerut',
        'state': 'Uttar Pradesh',
        'latitude': 28.9845,
        'longitude': 77.7064
    }
}

result = tools.create_advance_booking(
    user_id='user_123',
    booking_data=booking_data
)

print(f"Booking ID: {result['advance_booking_id']}")
print(f"Estimated cost: ₹{result['estimated_cost']}")
```

### 5. Optimal Sharing Schedule

```python
# Generate optimal schedule for equipment
result = tools.generate_optimal_sharing_schedule(
    resource_id='res_abc123',
    time_period_days=30
)

print(f"Utilization rate: {result['projected_utilization_rate']*100}%")
print(f"Monthly revenue: ₹{result['projected_monthly_revenue']}")
```

### 6. Customize Alert Preferences

```python
# Set user alert preferences
preferences = {
    'equipment_alerts': {
        'enabled': True,
        'equipment_types': ['tractor', 'harvester'],
        'radius_km': 30,
        'frequency': 'daily_digest'
    },
    'buying_group_alerts': {
        'enabled': True,
        'product_interests': ['seeds', 'fertilizers'],
        'min_discount': 20
    },
    'seasonal_alerts': {
        'enabled': True,
        'advance_notice_days': 45
    },
    'alert_channels': ['voice', 'sms'],
    'quiet_hours': {
        'enabled': True,
        'start': '22:00',
        'end': '06:00'
    }
}

result = tools.customize_alert_preferences(
    user_id='user_123',
    preferences=preferences
)

print("Preferences updated successfully!")
```

## Streamlit UI

Launch the alert customization interface:

```bash
streamlit run ui/alert_customization.py
```

Features:
- **Alert Preferences Tab**: Customize all alert settings
- **Seasonal Demand Tab**: Generate demand predictions
- **Advance Booking Tab**: Create advance equipment bookings

## EventBridge Automation

Set up automated alert rules:

```python
from infrastructure.eventbridge_availability_rules import setup_availability_alert_rules

# Set up all rules
result = setup_availability_alert_rules(region='us-east-1')

print(f"Rules created: {result['successful_rules']}/{result['total_rules']}")
```

### Automated Rules

1. **Equipment Availability** (every 2 hours)
   - Scans for newly listed equipment
   - Sends location-based alerts

2. **Buying Group Opportunities** (every 6 hours)
   - Identifies new buying groups
   - Matches with interested farmers

3. **Seasonal Demand Predictions** (daily)
   - Generates 90-day forecasts
   - Sends advance booking recommendations

4. **Booking Reminders** (every 12 hours)
   - Sends 7-day advance reminders
   - Confirms booking details

## API Endpoints

### Lambda Function Endpoints

```
POST /equipment-availability-alert
Body: {
  "resource_id": "res_abc123",
  "radius_km": 25
}

POST /bulk-buying-alert
Body: {
  "group_id": "grp_xyz789",
  "radius_km": 25
}

POST /seasonal-demand-prediction
Body: {
  "user_id": "user_123",
  "crop_calendar": {...}
}

POST /advance-booking
Body: {
  "user_id": "user_123",
  "booking_data": {...}
}

POST /optimal-schedule
Body: {
  "resource_id": "res_abc123",
  "time_period_days": 30
}

GET /alert-preferences
Body: {
  "user_id": "user_123"
}

POST /alert-preferences
Body: {
  "user_id": "user_123",
  "preferences": {...}
}
```

## Testing

Run unit tests:

```bash
python -m pytest tests/test_availability_alerts.py -v
```

Run example usage:

```bash
python examples/availability_alert_example.py
```

## Configuration

### Alert Preferences Schema

```json
{
  "equipment_alerts": {
    "enabled": true,
    "equipment_types": ["tractor", "harvester", "pump"],
    "radius_km": 25,
    "frequency": "immediate"
  },
  "buying_group_alerts": {
    "enabled": true,
    "product_interests": ["seeds", "fertilizers"],
    "min_discount": 15
  },
  "seasonal_alerts": {
    "enabled": true,
    "advance_notice_days": 30
  },
  "alert_channels": ["voice", "sms", "push"],
  "quiet_hours": {
    "enabled": true,
    "start": "22:00",
    "end": "07:00"
  }
}
```

## Performance Metrics

- **Alert Delivery**: < 5 seconds
- **Demand Prediction**: < 10 seconds
- **Schedule Generation**: < 8 seconds
- **Location Search**: < 3 seconds
- **Preference Update**: < 2 seconds

## Cost Optimization

- **EventBridge Rules**: ~$1/month per rule
- **Lambda Invocations**: ~$0.20 per 1M requests
- **Bedrock API Calls**: ~$0.003 per 1K tokens
- **DynamoDB**: On-demand pricing
- **SNS Notifications**: ~$0.50 per 1K SMS

Estimated monthly cost for 10K farmers: **$50-100**

## Troubleshooting

### Common Issues

1. **No alerts received**
   - Check alert preferences are enabled
   - Verify user location is set
   - Check quiet hours settings

2. **Prediction errors**
   - Ensure Bedrock access is enabled
   - Verify crop calendar format
   - Check AWS credentials

3. **Booking failures**
   - Verify equipment availability
   - Check booking date is in future
   - Ensure location data is valid

## Future Enhancements

- [ ] Machine learning for demand prediction accuracy
- [ ] Real-time equipment tracking integration
- [ ] Weather-based alert optimization
- [ ] Multi-language voice notifications
- [ ] Mobile app push notifications
- [ ] WhatsApp integration
- [ ] Predictive maintenance alerts
- [ ] Dynamic pricing recommendations

## Support

For issues or questions:
- GitHub Issues: [RISE Repository]
- Email: support@rise-farming.in
- Documentation: [Full Docs]

## License

MIT License - See LICENSE file for details

## Contributors

- RISE Development Team
- AWS Bedrock Integration Team
- Community Contributors

---

**Version**: 1.0.0  
**Last Updated**: December 2024  
**Status**: Production Ready
