# RISE Fertilizer Recommendation System

## Overview

The Fertilizer Recommendation System provides precision agriculture capabilities for calculating NPK requirements, generating fertilizer recommendations, optimizing application timing based on weather, and tracking crop growth stages.

## Features

### 1. NPK Requirement Calculation
- Calculate precise Nitrogen, Phosphorus, and Potassium requirements
- Based on soil analysis and target crop
- Accounts for current soil nutrient levels
- Provides split application schedules
- Calculates total farm requirements

### 2. Precision Fertilizer Recommendations
- Organic fertilizer options (FYM, compost, vermicompost)
- Chemical fertilizer options (Urea, DAP, MOP, NPK blends)
- Integrated organic + chemical approaches
- Application methods and timing
- Cost-benefit analysis
- Budget-constrained recommendations

### 3. Weather-Based Application Timing
- Integrates 7-14 day weather forecasts
- Identifies optimal application windows
- Considers rainfall, temperature, humidity
- Risk assessment for weather-related issues
- Time-of-day recommendations
- Alternative dates if primary window missed

### 4. Crop Growth Stage Tracking
- Determines current growth stage
- Stage-specific nutritional needs
- Predicts next stage transition
- Monitoring recommendations
- Historical tracking in DynamoDB

### 5. Amendment Suggestions
- Organic amendment options with quantities
- Chemical amendment options with NPK ratios
- Micronutrient recommendations
- Cost comparison (organic vs chemical vs integrated)
- Long-term soil health strategies
- Prioritization based on preferences

### 6. Cost-Effective Solutions
- Budget-constrained recommendations
- ROI calculations
- Phased application approaches
- Bulk purchasing strategies
- Cooperative buying opportunities
- Government subsidy information

## Architecture

### Components

1. **fertilizer_recommendation_tools.py**
   - Core Python class with all recommendation logic
   - Uses Amazon Bedrock for AI-powered analysis
   - Stores data in DynamoDB

2. **fertilizer_recommendation_lambda.py**
   - AWS Lambda function for serverless execution
   - Handles API requests
   - Routes to appropriate handlers

3. **Tests**
   - Comprehensive unit tests
   - Integration tests with real Bedrock API
   - Mock-based testing for CI/CD

4. **Examples**
   - Usage examples for all features
   - Complete workflow demonstrations
   - Best practices

## Usage

### Basic NPK Calculation

```python
from tools.fertilizer_recommendation_tools import FertilizerRecommendationTools

# Initialize tools
fert_tools = FertilizerRecommendationTools(region='us-east-1')

# Soil analysis from previous analysis
soil_analysis = {
    'soil_type': 'loam',
    'fertility_level': 'medium',
    'ph_level': 6.5,
    'npk_levels': {
        'nitrogen': 'low',
        'phosphorus': 'medium',
        'potassium': 'high'
    },
    'organic_matter': 2.5
}

# Calculate NPK requirements
result = fert_tools.calculate_npk_requirements(
    soil_analysis=soil_analysis,
    target_crop='wheat',
    farm_size_acres=2.5,
    location={'state': 'Punjab', 'district': 'Ludhiana'}
)

print(f"Nitrogen needed: {result['nitrogen_per_acre']} kg/acre")
print(f"Phosphorus needed: {result['phosphorus_per_acre']} kg/acre")
print(f"Potassium needed: {result['potassium_per_acre']} kg/acre")
```

### Get Precision Recommendations

```python
# Get detailed fertilizer recommendations
recommendations = fert_tools.get_precision_recommendations(
    npk_requirements=result,
    soil_analysis=soil_analysis,
    target_crop='wheat',
    growth_stage='vegetative',
    weather_forecast=weather_data,
    budget_constraint=20000  # INR
)

print("Organic options:", recommendations['organic_options'])
print("Chemical options:", recommendations['chemical_options'])
print("Combined approach:", recommendations['combined_approach'])
```

### Check Application Timing

```python
# Weather forecast data
weather_forecast = {
    'next_7_days': [
        {'date': '2024-01-15', 'temp_max': 28, 'temp_min': 15, 
         'rainfall': 0, 'humidity': 65},
        # ... more days
    ]
}

# Get optimal timing
timing = fert_tools.get_application_timing(
    target_crop='wheat',
    growth_stage='vegetative',
    weather_forecast=weather_forecast,
    location={'state': 'Punjab', 'district': 'Ludhiana'}
)

print("Optimal window:", timing['optimal_window'])
print("Weather considerations:", timing['weather_considerations'])
```

### Track Growth Stage

```python
from datetime import datetime, timedelta

# Planting date
planting_date = (datetime.now() - timedelta(days=25)).isoformat()

# Current observations
observations = {
    'height_cm': 30,
    'leaf_count': 5,
    'tillering': 'started'
}

# Track growth stage
stage = fert_tools.track_crop_growth_stage(
    user_id='farmer_001',
    farm_id='farm_001',
    crop_name='wheat',
    planting_date=planting_date,
    current_observations=observations
)

print(f"Current stage: {stage['current_stage']}")
print(f"Confidence: {stage['confidence']}")
```

### Generate Amendment Suggestions

```python
# Generate organic and chemical amendments
amendments = fert_tools.generate_amendment_suggestions(
    npk_requirements=result,
    soil_deficiencies=['Nitrogen deficiency', 'Low organic matter'],
    farm_size_acres=2.5,
    prioritize_organic=True,
    budget_constraint=25000
)

print("Organic amendments:", amendments['organic_amendments'])
print("Chemical amendments:", amendments['chemical_amendments'])
print("Integrated approach:", amendments['integrated_approach'])
```

## Lambda Function API

### Endpoint: `/api/v1/fertilizer`

### Actions

#### 1. Calculate NPK

```json
{
  "action": "calculate_npk",
  "soil_analysis": {
    "soil_type": "loam",
    "fertility_level": "medium",
    "ph_level": 6.5,
    "npk_levels": {
      "nitrogen": "low",
      "phosphorus": "medium",
      "potassium": "high"
    }
  },
  "target_crop": "wheat",
  "farm_size_acres": 2.5,
  "user_id": "farmer_001",
  "farm_id": "farm_001",
  "location": {
    "state": "Punjab",
    "district": "Ludhiana"
  }
}
```

#### 2. Get Recommendations

```json
{
  "action": "get_recommendations",
  "npk_requirements": {
    "nitrogen_per_acre": 60,
    "phosphorus_per_acre": 30,
    "potassium_per_acre": 20
  },
  "soil_analysis": {...},
  "target_crop": "wheat",
  "growth_stage": "vegetative",
  "weather_forecast": {...},
  "budget_constraint": 20000,
  "user_id": "farmer_001",
  "farm_id": "farm_001",
  "location": {...}
}
```

#### 3. Get Timing

```json
{
  "action": "get_timing",
  "target_crop": "wheat",
  "growth_stage": "vegetative",
  "weather_forecast": {
    "next_7_days": [...]
  },
  "user_id": "farmer_001",
  "farm_id": "farm_001",
  "location": {...}
}
```

#### 4. Track Growth

```json
{
  "action": "track_growth",
  "crop_name": "wheat",
  "planting_date": "2024-01-01",
  "current_observations": {
    "height_cm": 30,
    "leaf_count": 5
  },
  "user_id": "farmer_001",
  "farm_id": "farm_001",
  "location": {...}
}
```

## Data Storage

### DynamoDB Schema

All fertilizer recommendation data is stored in the `RISE-FarmData` table:

```python
{
  'farm_id': 'farm_001',  # Partition key
  'timestamp': 1234567890,  # Sort key
  'data_type': 'npk_calculation' | 'fertilizer_recommendation' | 'growth_tracking',
  'user_id': 'farmer_001',
  'target_crop': 'wheat',
  # ... type-specific data
}
```

## Integration with Soil Analysis

The fertilizer recommendation system integrates seamlessly with the soil analysis system:

1. Run soil analysis to get soil conditions
2. Use soil analysis results as input for NPK calculation
3. Get precision fertilizer recommendations
4. Apply fertilizers based on timing recommendations
5. Track growth stage for next application

## Cost Optimization

The system prioritizes cost-effective solutions:

- **Organic-only**: Higher upfront cost, long-term soil health benefits
- **Chemical-only**: Lower cost, immediate results
- **Integrated**: Balanced approach, optimal cost-benefit ratio

Budget constraints are respected, with phased application plans if needed.

## Weather Integration

Weather data should include:
- Temperature (min/max)
- Rainfall forecast
- Humidity levels
- Wind conditions (optional)

The system analyzes weather patterns to:
- Avoid fertilizer application before heavy rain
- Optimize for soil moisture conditions
- Minimize nutrient loss through leaching or volatilization

## Growth Stage Tracking

Supported growth stages:
- **Seedling**: Initial growth, root establishment
- **Vegetative**: Rapid leaf and stem growth
- **Flowering**: Reproductive stage begins
- **Fruiting**: Grain/fruit development
- **Maturity**: Harvest readiness

Each stage has specific nutritional requirements that the system accounts for.

## Best Practices

1. **Always start with soil analysis** - Accurate soil data is crucial
2. **Update growth stage regularly** - Track every 7-14 days
3. **Check weather before application** - Avoid rain within 24-48 hours
4. **Follow split application schedules** - Better nutrient uptake
5. **Monitor crop response** - Adjust based on observations
6. **Consider organic options** - Long-term soil health
7. **Stay within budget** - Use phased approaches if needed
8. **Document applications** - Track what works for your farm

## Testing

Run tests:
```bash
# Unit tests
pytest tests/test_fertilizer_recommendation.py -v

# Integration tests (requires AWS credentials)
pytest tests/test_fertilizer_recommendation.py -v -m integration

# All tests
pytest tests/test_fertilizer_recommendation.py -v --cov
```

## Examples

See `examples/fertilizer_recommendation_example.py` for comprehensive usage examples.

## Requirements

- Python 3.8+
- boto3
- Amazon Bedrock access
- DynamoDB table: RISE-FarmData

## Environment Variables

```bash
FARM_DATA_TABLE=RISE-FarmData
AWS_REGION=us-east-1
```

## Support

For issues or questions, refer to the main RISE documentation or contact the development team.

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) project.
