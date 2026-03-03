# RISE Weather Integration

Comprehensive weather data integration for the RISE farming assistant, providing location-based weather information, forecasts, and farming-specific insights.

## Overview

The weather integration provides:
- **Current Weather Data**: Real-time weather conditions for any location
- **Weather Forecasts**: Up to 5-day forecasts with 3-hour intervals
- **Farming Insights**: Weather-based recommendations for farming activities
- **Irrigation Advice**: Smart irrigation recommendations based on weather
- **Adverse Weather Alerts**: Early warnings for extreme weather conditions
- **Activity Planning**: Optimal timing suggestions for farming operations
- **Intelligent Caching**: 6-hour TTL cache to optimize API calls and costs

## Features

### 1. Current Weather Retrieval
Get real-time weather data including:
- Temperature (current, feels like, min, max)
- Humidity and pressure
- Wind speed and direction
- Cloud cover and visibility
- Rainfall data
- Sunrise and sunset times

### 2. Weather Forecasting
Access detailed forecasts with:
- 3-hour interval forecasts
- Daily summaries
- Temperature ranges
- Precipitation probability
- Weather conditions

### 3. Farming-Specific Insights
Intelligent analysis providing:
- **Farming Recommendations**: Activity suggestions based on weather
- **Irrigation Advice**: Priority-based irrigation recommendations
- **Adverse Weather Alerts**: Warnings for extreme conditions
- **Optimal Activities**: Best times for specific farming tasks

### 4. Caching System
Efficient caching with:
- 6-hour TTL (Time To Live)
- DynamoDB-based storage
- Automatic cache expiration
- Reduced API costs

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Weather Integration                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌──────────────────────────┐   │
│  │   Lambda     │◄────►│   WeatherTools Class     │   │
│  │   Handler    │      │   (weather_tools.py)     │   │
│  └──────────────┘      └──────────────────────────┘   │
│         │                         │                     │
│         │                         ▼                     │
│         │              ┌──────────────────────┐        │
│         │              │  DynamoDB Cache      │        │
│         │              │  (6-hour TTL)        │        │
│         │              └──────────────────────┘        │
│         │                         │                     │
│         ▼                         ▼                     │
│  ┌──────────────────────────────────────────────┐     │
│  │      OpenWeatherMap API                      │     │
│  │      (Free Tier: 1000 calls/day)             │     │
│  └──────────────────────────────────────────────┘     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Setup

### 1. OpenWeatherMap API Key

Get a free API key from [OpenWeatherMap](https://openweathermap.org/api):

```bash
# Set environment variable
export OPENWEATHER_API_KEY='your_api_key_here'
```

Or add to `.env` file:
```
OPENWEATHER_API_KEY=your_api_key_here
```

### 2. DynamoDB Table

The weather forecast cache table is automatically created by the CDK stack:

```python
# Table: RISE-WeatherForecast
# Partition Key: cache_key (String)
# TTL Attribute: ttl
# Billing: Pay-per-request
```

### 3. IAM Permissions

Lambda functions need:
- DynamoDB read/write access to `RISE-WeatherForecast` table
- Internet access to call OpenWeatherMap API

## Usage

### Python API

#### Get Current Weather

```python
from tools.weather_tools import WeatherTools

# Initialize
weather_tools = WeatherTools(region='us-east-1')

# Get current weather
result = weather_tools.get_current_weather(
    latitude=28.6139,
    longitude=77.2090,
    location_name='New Delhi'
)

if result['success']:
    print(f"Temperature: {result['current']['temperature']}°C")
    print(f"Humidity: {result['current']['humidity']}%")
    print(f"Weather: {result['current']['weather_description']}")
```

#### Get Weather Forecast

```python
# Get 5-day forecast
result = weather_tools.get_forecast(
    latitude=28.6139,
    longitude=77.2090,
    days=5,
    location_name='New Delhi'
)

if result['success']:
    for day in result['daily_summary']:
        print(f"{day['date']}: {day['temp_min']}-{day['temp_max']}°C")
        print(f"  Rain: {day['rain_total']}mm")
```

#### Get Farming Insights

```python
# Get comprehensive farming insights
result = weather_tools.get_farming_weather_insights(
    latitude=28.6139,
    longitude=77.2090,
    location_name='New Delhi'
)

if result['success']:
    # Farming recommendations
    for rec in result['farming_recommendations']:
        print(f"• {rec}")
    
    # Irrigation advice
    irrigation = result['irrigation_advice']
    print(f"Irrigation Priority: {irrigation['priority']}")
    print(f"Advice: {irrigation['advice']}")
    
    # Weather alerts
    for alert in result['adverse_weather_alerts']:
        print(f"Alert for {alert['date']}")
```

### Lambda Function

#### Deploy Lambda

```python
# Lambda handler in weather_lambda.py
# Environment variables:
# - OPENWEATHER_API_KEY: Your API key
# - AWS_REGION: AWS region (default: us-east-1)
```

#### API Request Format

```json
{
  "action": "current|forecast|insights",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "location_name": "New Delhi",
  "days": 5
}
```

#### API Response Format

```json
{
  "success": true,
  "from_cache": false,
  "location": {
    "name": "New Delhi",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "country": "IN"
  },
  "current": {
    "temperature": 28.5,
    "humidity": 65,
    "weather": "Clear",
    "weather_description": "clear sky"
  }
}
```

### API Gateway Integration

```
POST /api/v1/intelligence/weather/{location}

Request Body:
{
  "action": "insights",
  "latitude": 28.6139,
  "longitude": 77.2090
}

Response:
{
  "success": true,
  "farming_recommendations": [...],
  "irrigation_advice": {...},
  "adverse_weather_alerts": [...]
}
```

## Farming Insights

### Irrigation Advice

The system calculates irrigation need based on:
- Current temperature
- Humidity levels
- Recent rainfall
- Forecast for next 48 hours

**Priority Levels:**
- **High (8-10)**: Irrigation strongly recommended
- **Medium (6-7)**: Irrigation recommended if soil is dry
- **Low (4-5)**: Irrigation may not be necessary
- **Not Needed (0-3)**: Adequate moisture expected

### Farming Recommendations

Intelligent recommendations for:
- **Spraying Operations**: Based on wind speed and rain
- **Irrigation Timing**: Optimal times based on temperature
- **Field Activities**: Best conditions for plowing, weeding
- **Transplanting**: Ideal moisture conditions
- **Protective Measures**: For extreme weather

### Adverse Weather Alerts

Early warnings for:
- **Extreme Heat**: Temperature > 40°C
- **Cold Wave**: Temperature < 5°C
- **Heavy Rain**: Rainfall > 50mm
- **Moderate Rain**: Rainfall > 25mm

Each alert includes:
- Severity level (high/medium)
- Specific message
- Recommended protective measures

### Optimal Activities

Daily suggestions for:
- **Recommended Today**: Activities favored by current weather
- **Avoid Today**: Activities to postpone
- **Plan for Tomorrow**: Advance planning based on forecast

## Caching Strategy

### Cache Key Generation
```python
# Cache key format: MD5(latitude:longitude:data_type)
# Coordinates rounded to 2 decimal places
# Example: MD5("28.61:77.21:current")
```

### Cache TTL
- **Duration**: 6 hours
- **Rationale**: Balance between data freshness and API costs
- **Auto-cleanup**: DynamoDB TTL automatically removes expired entries

### Cache Benefits
- **Cost Optimization**: Reduces API calls by ~80%
- **Performance**: Sub-second response for cached data
- **Reliability**: Continues working if API is temporarily unavailable

## Cost Optimization

### OpenWeatherMap Free Tier
- **Limit**: 1,000 calls/day
- **With Caching**: Supports ~4,000 unique location requests/day
- **Cost**: $0 (free tier)

### AWS Costs
- **DynamoDB**: Pay-per-request, ~$0.25 per million requests
- **Lambda**: ~$0.20 per million requests
- **Data Transfer**: Minimal (weather data is small)

**Estimated Monthly Cost**: < $5 for 100K requests

## Error Handling

### API Errors
```python
{
  "success": false,
  "error": "Failed to fetch weather data: API error message"
}
```

### Invalid Input
```python
{
  "success": false,
  "error": "Invalid input: latitude must be a number"
}
```

### Cache Errors
- Gracefully degrades to API calls
- Logs warnings but doesn't fail requests

## Testing

### Run Unit Tests
```bash
cd RISE
pytest tests/test_weather_tools.py -v
```

### Test Coverage
- Current weather retrieval
- Forecast fetching
- Farming insights generation
- Irrigation advice calculation
- Adverse weather detection
- Cache operations
- Lambda handler

### Manual Testing
```bash
# Run example script
python examples/weather_integration_example.py
```

## Integration with RISE

### Voice Interface
```python
# User: "मौसम कैसा है?" (How's the weather?)
# System fetches weather and responds in Hindi
```

### Crop Recommendations
```python
# Integrate weather data with crop selection
soil_analysis = {...}
weather_data = weather_tools.get_farming_weather_insights(lat, lon)

# Use weather in crop recommendations
crop_recommendations = recommend_crops(
    soil_analysis=soil_analysis,
    climate_data=weather_data
)
```

### Fertilizer Application
```python
# Check weather before recommending fertilizer application
weather = weather_tools.get_farming_weather_insights(lat, lon)

if weather['irrigation_advice']['priority'] != 'High':
    # Safe to apply fertilizer
    recommend_fertilizer_application()
```

### Disease Diagnosis
```python
# Consider weather in disease risk assessment
weather = weather_tools.get_current_weather(lat, lon)

if weather['current']['humidity'] > 80:
    # High fungal disease risk
    increase_monitoring_frequency()
```

## Multilingual Support

Weather data can be translated using RISE translation tools:

```python
from tools.translation_tools import TranslationTools

# Get weather in English
weather_result = weather_tools.get_farming_weather_insights(lat, lon)

# Translate recommendations to Hindi
translator = TranslationTools()
for rec in weather_result['farming_recommendations']:
    translated = translator.translate_text(rec, 'hi')
    print(translated['translated_text'])
```

## Best Practices

### 1. Location Accuracy
- Use GPS coordinates when available
- Round to 2 decimal places for cache efficiency
- Provide location names for better UX

### 2. Error Handling
- Always check `success` field in response
- Provide fallback for API failures
- Log errors for monitoring

### 3. Cache Management
- Don't clear cache unnecessarily
- Let TTL handle expiration
- Monitor cache hit rate

### 4. API Usage
- Batch requests when possible
- Use caching effectively
- Monitor daily API call limits

## Troubleshooting

### Issue: API Key Error
```
Error: Failed to fetch weather data: 401 Unauthorized
```
**Solution**: Check OPENWEATHER_API_KEY environment variable

### Issue: Cache Not Working
```
Warning: Cache retrieval error
```
**Solution**: Verify DynamoDB table exists and IAM permissions

### Issue: Slow Response
```
Response time > 5 seconds
```
**Solution**: Check internet connectivity and API status

### Issue: Invalid Coordinates
```
Error: Invalid input: latitude must be between -90 and 90
```
**Solution**: Validate coordinates before calling API

## Future Enhancements

### Planned Features
- [ ] Historical weather data analysis
- [ ] Weather-based crop disease prediction
- [ ] Soil moisture estimation from weather
- [ ] Frost and heatwave predictions
- [ ] Integration with IoT weather stations
- [ ] Hyperlocal weather forecasting
- [ ] Climate change impact analysis

### API Upgrades
- Consider paid tier for more frequent updates
- Add weather radar data
- Include agricultural weather indices
- Add UV index and evapotranspiration data

## Support

### Documentation
- [OpenWeatherMap API Docs](https://openweathermap.org/api)
- [AWS DynamoDB TTL](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html)
- [RISE Project Documentation](../README.md)

### Contact
For issues or questions:
1. Check existing examples in `examples/weather_integration_example.py`
2. Review test cases in `tests/test_weather_tools.py`
3. Consult RISE documentation

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) project.

---

**Last Updated**: 2024
**Version**: 1.0.0
**Status**: Production Ready ✅
