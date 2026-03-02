# RISE Weather Alert System

Comprehensive weather-based alert system providing 48-72 hour advance notice of adverse weather conditions, farming activity recommendations, irrigation timing calculations, and protective measure suggestions.

## Overview

The weather alert system provides:
- **Adverse Weather Alerts**: 48-72 hour advance notice of extreme conditions
- **Farming Activity Recommendations**: Weather-based suggestions for optimal farming activities
- **Irrigation Timing Calculator**: Smart irrigation scheduling based on weather forecast and soil type
- **Protective Measures**: Specific actions to protect crops and livestock from adverse weather
- **Automated Monitoring**: EventBridge-triggered scheduled monitoring every 6 hours
- **Real-time Notifications**: SMS/voice alerts for critical weather conditions

## Features

### 1. Adverse Weather Detection (48-72 Hour Advance Notice)

The system monitors weather forecasts and generates alerts for:

**High Severity Alerts:**
- **Extreme Heat**: Temperature > 40°C
- **Cold Wave**: Temperature < 5°C
- **Heavy Rain**: Rainfall > 50mm

**Medium Severity Alerts:**
- **High Heat**: Temperature > 38°C
- **Cold Weather**: Temperature < 10°C
- **Moderate Rain**: Rainfall > 25mm
- **Drought Risk**: Extended dry period with low humidity

### 2. Farming Activity Recommendations

Daily recommendations for:
- **Spraying Operations**: Pesticide/fungicide application timing
- **Irrigation**: When to water based on weather
- **Field Preparation**: Plowing and land preparation
- **Transplanting**: Optimal conditions for seedling transplant
- **Fertilizer Application**: Best timing to avoid nutrient loss
- **Harvesting**: Ideal conditions for crop harvest

Each recommendation includes:
- Activity name
- Reason for recommendation
- Optimal timing (time of day)

### 3. Irrigation Timing Calculator

Smart irrigation scheduling with:
- **7-Day Schedule**: Daily irrigation recommendations
- **Priority Levels**: High, Medium, Low, Not Needed
- **Irrigation Score**: 0-10 scale based on multiple factors
- **Water Amount**: Specific quantities (mm) needed
- **Optimal Timing**: Best time of day for irrigation
- **Soil Type Adjustment**: Accounts for clay, loam, sandy, silt soils
- **Weather Integration**: Temperature, humidity, rainfall forecast

**Calculation Factors:**
- Current and forecast temperature
- Humidity levels
- Recent and forecast rainfall
- Soil water retention characteristics
- Previous day's weather

### 4. Protective Measures

Specific action items for each weather alert:

**Extreme Heat Protection:**
- Increase irrigation frequency
- Apply mulch for moisture conservation
- Provide shade nets for sensitive crops
- Avoid peak heat activities
- Monitor for heat stress

**Cold Wave Protection:**
- Cover crops with plastic/cloth
- Use smoke method (small fires)
- Irrigate before cold night
- Protect young plants
- Provide livestock shelter

**Heavy Rain Protection:**
- Clear drainage systems
- Harvest mature crops early
- Secure equipment
- Postpone chemical applications
- Monitor for waterlogging and fungal diseases

**Drought Risk Protection:**
- Implement water conservation
- Apply mulch
- Use drip irrigation
- Prioritize critical crops
- Monitor soil moisture

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Weather Alert System                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         EventBridge Scheduled Rules              │  │
│  │  • Every 6 hours (general monitoring)            │  │
│  │  • Every 2 hours (critical checks)               │  │
│  │  • Daily at 6 AM IST (morning summary)           │  │
│  │  • Daily at 6 PM IST (evening update)            │  │
│  └──────────────────┬───────────────────────────────┘  │
│                     │                                   │
│                     ▼                                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │      Weather Alert Lambda Function               │  │
│  │      (weather_alert_lambda.py)                   │  │
│  └──────────────────┬───────────────────────────────┘  │
│                     │                                   │
│                     ▼                                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │      WeatherAlertTools Class                     │  │
│  │      (weather_alert_tools.py)                    │  │
│  │  • Adverse weather detection                     │  │
│  │  • Activity recommendations                      │  │
│  │  • Irrigation calculator                         │  │
│  │  • Protective measures                           │  │
│  └──────────────────┬───────────────────────────────┘  │
│                     │                                   │
│         ┌───────────┴───────────┐                      │
│         ▼                       ▼                      │
│  ┌─────────────┐         ┌─────────────┐              │
│  │  DynamoDB   │         │  Amazon SNS │              │
│  │  (Alerts)   │         │ (Notifications)            │
│  └─────────────┘         └─────────────┘              │
│         │                       │                      │
│         └───────────┬───────────┘                      │
│                     ▼                                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │      Streamlit UI Components                     │  │
│  │      (ui/weather_alerts.py)                      │  │
│  │  • Alerts dashboard                              │  │
│  │  • Activity recommendations                      │  │
│  │  • Irrigation schedule                           │  │
│  │  • Protective measures checklist                 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Setup

### 1. DynamoDB Tables

Create the weather alerts table:

```python
# Table: RISE-WeatherAlerts
# Partition Key: alert_id (String)
# Sort Key: timestamp (String)
# GSI: UserAlertIndex (user_id, timestamp)
# TTL Attribute: ttl (7 days)
```

### 2. Lambda Function

Deploy the weather alert Lambda:

```bash
# Package dependencies
cd RISE/tools
pip install -r requirements.txt -t package/
cp weather_alert_lambda.py package/
cp weather_alert_tools.py package/
cp weather_tools.py package/

# Create deployment package
cd package
zip -r ../weather_alert_lambda.zip .

# Deploy to AWS Lambda
aws lambda create-function \
  --function-name RISE-WeatherAlertLambda \
  --runtime python3.11 \
  --handler weather_alert_lambda.lambda_handler \
  --role arn:aws:iam::ACCOUNT_ID:role/RISE-LambdaRole \
  --zip-file fileb://../weather_alert_lambda.zip \
  --timeout 300 \
  --memory-size 512 \
  --environment Variables="{OPENWEATHER_API_KEY=your_key,AWS_REGION=us-east-1}"
```

### 3. EventBridge Rules

Create scheduled rules:

```bash
# Option 1: Using Python script
cd RISE/infrastructure
python eventbridge_rules.py

# Option 2: Using AWS CLI
aws events put-rule \
  --name RISE-WeatherMonitoring-6Hours \
  --schedule-expression "rate(6 hours)" \
  --state ENABLED

aws events put-targets \
  --rule RISE-WeatherMonitoring-6Hours \
  --targets "Id=1,Arn=arn:aws:lambda:REGION:ACCOUNT:function:RISE-WeatherAlertLambda"
```

### 4. IAM Permissions

Lambda function needs:
- DynamoDB read/write: `RISE-WeatherAlerts`, `RISE-UserProfiles`, `RISE-WeatherForecast`
- SNS publish for notifications
- CloudWatch Logs for logging

## Usage

### Python API

#### Monitor Weather for User

```python
from tools.weather_alert_tools import WeatherAlertTools

# Initialize
alert_tools = WeatherAlertTools(region='us-east-1')

# Monitor weather for a user
result = alert_tools.monitor_weather_conditions(user_id='user_123')

if result['success']:
    # Access alerts
    alerts = result['alerts']
    for alert in alerts:
        print(f"{alert['title']}: {alert['message']}")
    
    # Access recommendations
    recommendations = result['recommendations']
    for day in recommendations:
        print(f"Day {day['day_number']}: {len(day['recommended'])} activities")
    
    # Access irrigation schedule
    irrigation = result['irrigation']
    for day in irrigation['schedule']:
        print(f"{day['date']}: {day['priority']} priority")
    
    # Access protective measures
    measures = result['protective_measures']
    for measure in measures:
        print(f"{measure['alert_type']}: {len(measure['measures'])} actions")
```

#### Get User's Recent Alerts

```python
# Get alerts from last 7 days
result = alert_tools.get_user_alerts(user_id='user_123', days=7)

if result['success']:
    print(f"Found {result['count']} alerts")
    for alert_data in result['alerts']:
        print(f"Timestamp: {alert_data['timestamp']}")
```

### Lambda Function

#### API Gateway Request

```json
POST /api/v1/weather/alerts

{
  "action": "monitor",
  "user_id": "user_123"
}

Response:
{
  "success": true,
  "alerts": [...],
  "recommendations": [...],
  "irrigation": {...},
  "protective_measures": [...],
  "location": {...}
}
```

#### Get Recent Alerts

```json
POST /api/v1/weather/alerts

{
  "action": "get_alerts",
  "user_id": "user_123",
  "days": 7
}

Response:
{
  "success": true,
  "alerts": [...],
  "count": 5
}
```

### Streamlit UI

#### Full Dashboard

```python
from ui.weather_alerts import render_weather_alerts_dashboard

# Render complete dashboard
render_weather_alerts_dashboard(
    user_id='user_123',
    location={'name': 'New Delhi', 'latitude': 28.6139, 'longitude': 77.2090}
)
```

#### Compact Widget

```python
from ui.weather_alerts import render_weather_alerts_widget

# Render compact widget for sidebar
render_weather_alerts_widget(user_id='user_123')
```

## Alert Examples

### Extreme Heat Alert

```json
{
  "type": "extreme_heat",
  "severity": "high",
  "date": "2024-01-15",
  "hours_ahead": 60,
  "title": "Extreme Heat Warning",
  "message": "Extreme heat expected on 2024-01-15: 42°C",
  "details": {
    "max_temp": 42,
    "min_temp": 28
  }
}
```

**Protective Measures:**
- Increase irrigation frequency to prevent heat stress
- Apply mulch to conserve soil moisture
- Provide shade nets for sensitive crops
- Avoid spraying during peak heat hours (11 AM - 3 PM)
- Monitor crops for wilting and heat damage

### Heavy Rain Alert

```json
{
  "type": "heavy_rain",
  "severity": "high",
  "date": "2024-01-16",
  "hours_ahead": 72,
  "title": "Heavy Rainfall Warning",
  "message": "Heavy rainfall expected on 2024-01-16: 65mm",
  "details": {
    "rainfall": 65,
    "humidity": 85
  }
}
```

**Protective Measures:**
- Ensure proper field drainage systems are clear
- Harvest mature crops before rain if possible
- Secure farm equipment and structures
- Postpone fertilizer and pesticide application
- Monitor for waterlogging after rain

## Irrigation Calculator

### Example Schedule

```json
{
  "date": "2024-01-10",
  "day_number": 1,
  "priority": "High",
  "score": 8.5,
  "recommendation": "Irrigation strongly recommended today",
  "water_amount": "Heavy watering (25-30mm)",
  "optimal_time": "Early morning (5-7 AM) or evening (6-8 PM)",
  "weather": {
    "temp_max": 36,
    "humidity": 35,
    "rainfall": 0
  }
}
```

### Soil Type Adjustments

- **Clay Soil**: 0.8x retention factor (holds water well)
- **Loam Soil**: 1.0x retention factor (balanced)
- **Sandy Soil**: 1.3x retention factor (drains quickly)
- **Silt Soil**: 0.9x retention factor (good retention)

## Activity Recommendations

### Example Day Recommendations

```json
{
  "date": "2024-01-10",
  "day_number": 1,
  "recommended": [
    {
      "activity": "Pesticide/Fungicide Spraying",
      "reason": "Ideal conditions: low rain, moderate temperature",
      "timing": "Early morning (6-9 AM) or evening (4-6 PM)"
    },
    {
      "activity": "Field Preparation/Plowing",
      "reason": "Good weather for field work",
      "timing": "Morning to afternoon (7 AM - 4 PM)"
    }
  ],
  "avoid": [
    {
      "activity": "Heavy Manual Labor",
      "reason": "Extreme heat - risk of heat stroke"
    }
  ],
  "optimal_timing": [
    {
      "timing": "Early morning (5-9 AM) only",
      "reason": "Avoid midday heat"
    }
  ]
}
```

## Monitoring Schedule

### EventBridge Rules

1. **General Monitoring**: Every 6 hours
   - Comprehensive weather check for all users
   - Generate alerts and recommendations
   - Update irrigation schedules

2. **Critical Checks**: Every 2 hours
   - Monitor for rapidly developing weather
   - High-priority alert generation
   - Emergency notifications

3. **Morning Summary**: Daily at 6 AM IST
   - Day's weather overview
   - Activity recommendations
   - Irrigation priorities

4. **Evening Update**: Daily at 6 PM IST
   - Next day preparation
   - Overnight weather watch
   - Equipment readiness

## Notifications

### SMS Alerts (via SNS)

Critical weather alerts are sent via SMS:

```
🌾 RISE Weather Alert

⚠️ Extreme Heat Warning
Extreme heat expected on 2024-01-15: 42°C

⚠️ Heavy Rainfall Warning
Heavy rainfall expected on 2024-01-16: 65mm
```

### Voice Alerts

Multilingual voice notifications using:
- Amazon Polly for text-to-speech
- User's preferred language
- Critical alerts only

## Integration with RISE

### Voice Interface

```python
# User: "मौसम की चेतावनी दिखाओ" (Show weather alerts)
# System fetches and speaks alerts in Hindi
```

### Crop Management

```python
# Integrate weather alerts with crop recommendations
weather_alerts = alert_tools.monitor_weather_conditions(user_id)

if any(a['type'] == 'heavy_rain' for a in weather_alerts['alerts']):
    # Adjust crop recommendations
    recommend_rain_resistant_varieties()
```

### Disease Prevention

```python
# High humidity + moderate rain = fungal disease risk
if weather_data['humidity'] > 80 and weather_data['rain'] > 10:
    alert_fungal_disease_risk()
    recommend_preventive_fungicides()
```

## Testing

### Run Unit Tests

```bash
cd RISE
pytest tests/test_weather_alert_tools.py -v
```

### Manual Testing

```bash
# Test weather monitoring
python tools/weather_alert_tools.py

# Test Lambda function
python tools/weather_alert_lambda.py

# Test UI components
streamlit run ui/weather_alerts.py
```

## Cost Optimization

### API Calls
- **OpenWeatherMap**: Free tier (1,000 calls/day)
- **With Caching**: Supports ~4,000 users/day
- **Cost**: $0 (free tier)

### AWS Services
- **Lambda**: ~$0.20 per million requests
- **DynamoDB**: Pay-per-request, ~$0.25 per million
- **EventBridge**: $1.00 per million events
- **SNS**: $0.50 per million SMS (India)

**Estimated Monthly Cost**: < $10 for 10K users

## Best Practices

### 1. Alert Timing
- Focus on 48-72 hour window for actionable alerts
- Avoid alert fatigue with too many notifications
- Prioritize high-severity alerts

### 2. Irrigation Scheduling
- Consider soil type for accurate recommendations
- Account for previous day's weather
- Adjust for crop water requirements

### 3. Activity Recommendations
- Provide specific timing (time of day)
- Explain reasoning for each recommendation
- Include both recommended and avoided activities

### 4. Protective Measures
- Make measures actionable and specific
- Prioritize by urgency
- Provide checklists for easy tracking

## Troubleshooting

### Issue: No Alerts Generated
**Solution**: Check user profile has location data

### Issue: Incorrect Irrigation Recommendations
**Solution**: Verify soil type in user profile

### Issue: EventBridge Not Triggering
**Solution**: Check Lambda permissions and rule status

### Issue: Notifications Not Sent
**Solution**: Verify SNS permissions and phone numbers

## Future Enhancements

- [ ] Machine learning for personalized recommendations
- [ ] Integration with IoT weather stations
- [ ] Crop-specific irrigation calculations
- [ ] Historical weather pattern analysis
- [ ] Frost and heatwave predictions
- [ ] Pest outbreak predictions based on weather
- [ ] Integration with satellite imagery
- [ ] Community weather reporting

## Support

For issues or questions:
1. Check examples in `examples/weather_alert_example.py`
2. Review test cases in `tests/test_weather_alert_tools.py`
3. Consult RISE documentation

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) project.

---

**Last Updated**: 2024
**Version**: 1.0.0
**Status**: Production Ready ✅
