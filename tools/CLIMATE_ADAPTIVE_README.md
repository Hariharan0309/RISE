# RISE Climate-Adaptive Recommendations

## Overview

The Climate-Adaptive Recommendations module provides AI-powered tools for analyzing climate data, identifying risks, and generating adaptive farming recommendations. This module helps farmers adapt to changing weather patterns through resilient crop varieties, water-efficient techniques, and seasonal advice.

## Features

### 1. Climate Data Analysis
- **Long-term trend analysis**: Temperature, rainfall, and extreme events
- **Climate risk identification**: Drought, flood, heat stress, climate variability
- **AI-powered insights**: Bedrock-generated analysis of climate patterns
- **Historical data processing**: 30-90 day weather pattern analysis

### 2. Resilient Crop Variety Recommendations
- **Climate-specific varieties**: Crops suited to identified climate risks
- **Soil type consideration**: Recommendations based on soil characteristics
- **Economic viability**: Market demand and yield expectations
- **Confidence scoring**: AI-generated confidence levels for each recommendation

### 3. Water-Efficient Farming Techniques
- **Technique recommendations**: Drip irrigation, mulching, rainwater harvesting, etc.
- **Cost-benefit analysis**: Investment requirements and ROI calculations
- **Implementation guidance**: Step-by-step practical instructions
- **Water scarcity adaptation**: Techniques prioritized by scarcity level

### 4. Seasonal Farming Advice
- **Season-specific guidance**: Kharif, Rabi, and Zaid season recommendations
- **Climate-integrated advice**: Incorporates current climate trends
- **Farmer profile customization**: Tailored to land size, crops, and experience
- **Priority action identification**: Key actions for immediate implementation

## Architecture

### Components

```
climate_adaptive_tools.py       # Core tools and business logic
climate_adaptive_lambda.py      # AWS Lambda handler
test_climate_adaptive.py        # Comprehensive test suite
climate_adaptive_example.py     # Usage examples
CLIMATE_ADAPTIVE_README.md      # This documentation
```

### AWS Services Integration

- **Amazon Bedrock**: AI-powered climate analysis and recommendations (Claude 3 Sonnet)
- **Amazon DynamoDB**: Climate analysis storage (RISE-ClimateAnalysis table)
- **AWS Lambda**: Serverless compute for API endpoints
- **Amazon API Gateway**: RESTful API management

### Data Flow

```
User Request → API Gateway → Lambda Handler → Climate Tools → Bedrock AI
                                                    ↓
                                              DynamoDB Storage
                                                    ↓
                                              Response to User
```

## API Reference

### Lambda Handler Actions

#### 1. Analyze Climate Data

**Action**: `analyze_climate`

**Request**:
```json
{
  "action": "analyze_climate",
  "location": {
    "name": "Pune, Maharashtra",
    "latitude": 18.5204,
    "longitude": 73.8567
  },
  "historical_weather": [
    {
      "date": "2024-01-01",
      "temp_avg": 28,
      "temp_max": 35,
      "temp_min": 22,
      "rainfall": 0
    }
  ],
  "current_season": "Rabi"
}
```

**Response**:
```json
{
  "success": true,
  "analysis_id": "climate_pune_1234567890",
  "location": {...},
  "trends": {
    "temperature": {
      "average": 30.5,
      "max": 42,
      "min": 22,
      "trend": "increasing"
    },
    "rainfall": {
      "total": 150,
      "average": 5,
      "trend": "decreasing"
    },
    "extreme_events": [...]
  },
  "risks": [
    {
      "type": "heat_stress",
      "severity": "high",
      "description": "Prolonged high temperatures...",
      "mitigation": "Consider heat-tolerant varieties..."
    }
  ],
  "ai_insights": "Climate analysis shows...",
  "season": "Rabi",
  "analyzed_at": "2024-01-15T10:30:00"
}
```

#### 2. Get Resilient Crop Varieties

**Action**: `crop_varieties`

**Request**:
```json
{
  "action": "crop_varieties",
  "location": {
    "name": "Nashik, Maharashtra",
    "latitude": 19.9975,
    "longitude": 73.7898
  },
  "climate_risks": ["drought", "heat_stress"],
  "soil_type": "Black soil (Regur)"
}
```

**Response**:
```json
{
  "success": true,
  "location": {...},
  "climate_risks": ["drought", "heat_stress"],
  "recommended_varieties": [
    {
      "crop_name": "Pearl Millet",
      "variety": "HHB 67",
      "resilience_features": ["Drought tolerant", "Heat resistant"],
      "expected_yield": "2-3 tons/hectare",
      "market_demand": "High",
      "confidence_score": 85
    }
  ],
  "confidence_score": 85.0
}
```

#### 3. Get Water-Efficient Techniques

**Action**: `water_techniques`

**Request**:
```json
{
  "action": "water_techniques",
  "location": {
    "name": "Solapur, Maharashtra",
    "latitude": 17.6599,
    "longitude": 75.9064
  },
  "water_scarcity_level": "high",
  "crop_type": "Cotton"
}
```

**Response**:
```json
{
  "success": true,
  "location": {...},
  "water_scarcity_level": "high",
  "recommended_techniques": [
    {
      "name": "Drip Irrigation",
      "description": "Delivers water directly to plant roots...",
      "water_savings": "30-50%",
      "initial_cost": "Medium (₹25,000-50,000 per acre)",
      "maintenance": "Low",
      "suitability": "All crops, especially vegetables and fruits",
      "priority": "high"
    }
  ],
  "implementation_guide": "Step-by-step guidance...",
  "cost_benefit_analysis": {
    "total_initial_investment": "₹45,000",
    "average_water_savings": "35%",
    "estimated_annual_savings": "₹5,250",
    "payback_period_years": 8.6,
    "roi_5_years": "-42%"
  }
}
```

#### 4. Generate Seasonal Advice

**Action**: `seasonal_advice`

**Request**:
```json
{
  "action": "seasonal_advice",
  "location": {
    "name": "Aurangabad, Maharashtra",
    "latitude": 19.8762,
    "longitude": 75.3433
  },
  "current_season": "Kharif",
  "climate_trends": {
    "temperature": {"average": 32, "trend": "increasing"},
    "rainfall": {"average": 5, "trend": "decreasing"}
  },
  "farmer_profile": {
    "land_size": 3,
    "current_crops": ["Cotton", "Soybean"],
    "irrigation": "Drip irrigation available"
  }
}
```

**Response**:
```json
{
  "success": true,
  "location": {...},
  "season": "Kharif",
  "advice": {
    "full_advice": "Comprehensive seasonal advice...",
    "key_recommendations": [
      "Plant drought-resistant varieties",
      "Implement drip irrigation"
    ],
    "priority_actions": [
      "Farmers should implement drip irrigation immediately"
    ]
  },
  "generated_at": "2024-01-15T10:30:00"
}
```

## Usage Examples

### Python SDK Usage

```python
from tools.climate_adaptive_tools import create_climate_adaptive_tools

# Initialize tools
tools = create_climate_adaptive_tools(region='us-east-1')

# Analyze climate data
location = {
    'name': 'Pune, Maharashtra',
    'latitude': 18.5204,
    'longitude': 73.8567
}

historical_weather = [
    {'date': '2024-01-01', 'temp_avg': 28, 'temp_max': 35, 'temp_min': 22, 'rainfall': 0},
    # ... more data
]

result = tools.analyze_climate_data(location, historical_weather, 'Rabi')

if result['success']:
    print(f"Climate risks: {len(result['risks'])}")
    for risk in result['risks']:
        print(f"- {risk['type']}: {risk['description']}")
```

### Lambda Invocation

```python
import boto3
import json

lambda_client = boto3.client('lambda')

# Invoke climate analysis
response = lambda_client.invoke(
    FunctionName='rise-climate-adaptive-lambda',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'action': 'analyze_climate',
        'location': {'name': 'Pune', 'latitude': 18.5204, 'longitude': 73.8567},
        'historical_weather': [...],
        'current_season': 'Rabi'
    })
)

result = json.loads(response['Payload'].read())
print(result)
```

### API Gateway Request

```bash
curl -X POST https://api.rise-farming.com/v1/climate/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "action": "analyze_climate",
    "location": {"name": "Pune", "latitude": 18.5204, "longitude": 73.8567},
    "historical_weather": [...],
    "current_season": "Rabi"
  }'
```

## Climate Risk Types

### Identified Risks

1. **Heat Stress**: Prolonged high temperatures (>35°C average)
2. **Extreme Heat**: Critical heat events (>42°C)
3. **Drought**: Low rainfall patterns (<1mm/day average)
4. **Climate Variability**: High frequency of extreme events (>5 events)

### Risk Severity Levels

- **Critical**: Immediate action required
- **High**: Significant impact expected
- **Medium**: Moderate impact, plan mitigation
- **Low**: Monitor situation

## Water Scarcity Levels

- **Low**: Adequate water availability
- **Medium**: Some water stress expected
- **High**: Significant water scarcity
- **Severe**: Critical water shortage

## Farming Seasons (India)

- **Kharif**: June-October (Monsoon season)
- **Rabi**: October-March (Winter season)
- **Zaid**: March-June (Summer season)

## Water-Efficient Techniques

### Available Techniques

1. **Drip Irrigation**
   - Water savings: 30-50%
   - Cost: ₹25,000-50,000/acre
   - Best for: All crops, especially vegetables

2. **Mulching**
   - Water savings: 20-30%
   - Cost: ₹2,000-5,000/acre
   - Best for: All crops

3. **Rainwater Harvesting**
   - Water savings: 40-60%
   - Cost: ₹50,000-1,50,000
   - Best for: All crops

4. **Sprinkler Irrigation**
   - Water savings: 20-40%
   - Cost: ₹30,000-60,000/acre
   - Best for: Field crops, vegetables

5. **Conservation Tillage**
   - Water savings: 15-25%
   - Cost: ₹5,000-10,000
   - Best for: All crops

## DynamoDB Schema

### RISE-ClimateAnalysis Table

```
{
  "analysis_id": "climate_pune_1234567890",  // Partition Key
  "location": "{...}",                       // JSON string
  "trends": "{...}",                         // JSON string
  "risks": "[...]",                          // JSON string
  "ai_analysis": "Climate analysis text...",
  "created_at": "2024-01-15T10:30:00",
  "ttl": 1234567890                          // 90 days expiration
}
```

## Testing

### Run Tests

```bash
# Run all tests
pytest tests/test_climate_adaptive.py -v

# Run specific test
pytest tests/test_climate_adaptive.py::TestClimateAdaptiveTools::test_analyze_climate_data_success -v

# Run with coverage
pytest tests/test_climate_adaptive.py --cov=tools.climate_adaptive_tools --cov-report=html
```

### Test Coverage

- Climate data analysis
- Trend calculation
- Risk identification
- Crop variety recommendations
- Water-efficient techniques
- Seasonal advice generation
- Lambda handler functions
- Error handling

## Performance Considerations

### Caching Strategy

- Climate analysis results cached for 24 hours
- DynamoDB TTL set to 90 days for historical data
- Bedrock responses cached when possible

### Optimization Tips

1. **Batch Processing**: Analyze multiple locations in parallel
2. **Data Aggregation**: Pre-aggregate historical weather data
3. **Prompt Optimization**: Use concise prompts for faster Bedrock responses
4. **Regional Deployment**: Deploy Lambda in regions close to users

## Cost Optimization

### AWS Service Costs

- **Bedrock**: ~$0.003 per 1K input tokens, ~$0.015 per 1K output tokens
- **Lambda**: ~$0.20 per 1M requests + compute time
- **DynamoDB**: On-demand pricing, ~$1.25 per million writes
- **API Gateway**: ~$3.50 per million requests

### Cost Reduction Strategies

1. Cache Bedrock responses aggressively
2. Use DynamoDB on-demand for unpredictable traffic
3. Implement request throttling
4. Optimize prompt lengths

## Multilingual Support

The module supports 9 Indic languages through integration with translation tools:
- Hindi (हिंदी)
- Tamil (தமிழ்)
- Telugu (తెలుగు)
- Kannada (ಕನ್ನಡ)
- Bengali (বাংলা)
- Gujarati (ગુજરાતી)
- Marathi (मराठी)
- Punjabi (ਪੰਜਾਬੀ)
- English

## Error Handling

### Common Errors

1. **Missing Required Fields**: Returns 400 with error message
2. **Bedrock API Errors**: Graceful fallback with generic advice
3. **DynamoDB Errors**: Continues without storage, logs error
4. **Invalid Input**: Validates and returns specific error messages

### Error Response Format

```json
{
  "success": false,
  "error": "Detailed error message"
}
```

## Security Considerations

1. **Data Encryption**: All data encrypted at rest and in transit
2. **IAM Roles**: Lambda uses least-privilege IAM roles
3. **API Authentication**: API Gateway with Cognito authentication
4. **Input Validation**: All inputs validated before processing
5. **PII Protection**: No personally identifiable information stored

## Future Enhancements

1. **IoT Integration**: Real-time sensor data for climate monitoring
2. **Satellite Imagery**: Crop health monitoring from space
3. **Machine Learning**: Predictive models for climate trends
4. **Community Data**: Crowdsourced climate observations
5. **Government Integration**: Official weather and climate data sources

## Support and Documentation

- **Examples**: See `examples/climate_adaptive_example.py`
- **Tests**: See `tests/test_climate_adaptive.py`
- **API Docs**: See API Reference section above
- **AWS Documentation**: [Amazon Bedrock](https://docs.aws.amazon.com/bedrock/)

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) project.

## Contributing

For contributions, please follow the established patterns in the codebase and ensure all tests pass.

---

**Last Updated**: January 2024  
**Version**: 1.0.0  
**Maintainer**: RISE Development Team
