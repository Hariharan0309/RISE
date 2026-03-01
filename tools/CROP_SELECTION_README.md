# RISE Crop Selection Tools

## Overview

The Crop Selection Tools provide AI-powered crop recommendations, profitability analysis, and seasonal planning for farmers. Using Amazon Bedrock's Claude 3 Sonnet model, these tools analyze soil conditions, climate data, and market trends to suggest the most suitable and profitable crops.

## Features

### 1. Crop Recommendations
- **Soil-based recommendations**: Analyzes soil type, fertility, pH, and NPK levels
- **Climate integration**: Considers temperature, rainfall, and seasonal patterns
- **Market intelligence**: Factors in market demand and price trends
- **Risk assessment**: Evaluates weather, pest, and market risks
- **Experience-based**: Tailors recommendations to farmer's skill level

### 2. Profitability Calculator
- **Comprehensive cost analysis**: Seeds, fertilizers, labor, irrigation, equipment
- **Yield projections**: Average, optimistic, and conservative scenarios
- **Revenue calculations**: Based on current market prices
- **ROI analysis**: Return on investment and profit margins
- **Break-even analysis**: Minimum yield and price requirements
- **Cash flow timeline**: Month-by-month expense and revenue tracking

### 3. Seasonal Calendar
- **Kharif season planning**: Monsoon crops (June-October)
- **Rabi season planning**: Winter crops (November-March)
- **Zaid season planning**: Summer crops (March-June)
- **Perennial crops**: Year-round cultivation options
- **Activity timeline**: Planting, fertilization, irrigation, harvesting schedules
- **Resource planning**: Labor, equipment, and input procurement timing

### 4. Crop Comparison
- **Side-by-side analysis**: Compare multiple crop options
- **Multi-criteria evaluation**: Profitability, water needs, labor, risk
- **Decision matrix**: Scoring system for objective comparison
- **Ranking system**: Prioritized recommendations
- **Scenario analysis**: Best choice for different priorities

## Installation

```bash
# Install required dependencies
pip install boto3 pytest

# Ensure AWS credentials are configured
aws configure
```

## AWS Services Required

- **Amazon Bedrock**: Claude 3 Sonnet model access
- **Amazon DynamoDB**: RISE-FarmData table
- **AWS Lambda**: For serverless deployment (optional)

## Usage

### Basic Crop Recommendations

```python
from tools.crop_selection_tools import recommend_crops

# Soil analysis data
soil_analysis = {
    'soil_type': 'loam',
    'fertility_level': 'medium',
    'ph_level': 6.8,
    'npk_levels': {
        'nitrogen': 'medium',
        'phosphorus': 'low',
        'potassium': 'high'
    },
    'organic_matter': 2.5,
    'deficiencies': ['phosphorus']
}

# Location information
location = {
    'state': 'Punjab',
    'district': 'Ludhiana'
}

# Get recommendations
result = recommend_crops(
    soil_analysis=soil_analysis,
    location=location,
    farm_size_acres=5.0,
    farmer_experience='intermediate'
)

if result['success']:
    print(f"Recommendation ID: {result['recommendation_id']}")
    
    for crop in result['highly_recommended_crops']:
        print(f"Crop: {crop['name']}")
        print(f"Expected Yield: {crop['expected_yield']}")
        print(f"Market Demand: {crop['market_demand']}")
        print(f"Net Profit: {crop['net_profit']}")
```

### Profitability Calculation

```python
from tools.crop_selection_tools import calculate_crop_profitability

# Calculate profitability for wheat
result = calculate_crop_profitability(
    crop_name='Wheat',
    farm_size_acres=5.0,
    location={'state': 'Punjab', 'district': 'Ludhiana'},
    soil_type='loam',
    market_price=2200  # Rs per quintal
)

if result['success']:
    print(f"Input Costs: ₹{result['input_costs_per_acre']}")
    print(f"Expected Yield: {result['expected_yield_per_acre']} quintals")
    print(f"Net Profit: ₹{result['net_profit_per_acre']}")
    print(f"ROI: {result['roi']}%")
```

### Seasonal Calendar Generation

```python
from tools.crop_selection_tools import generate_seasonal_calendar

# Generate calendar for selected crops
result = generate_seasonal_calendar(
    location={'state': 'Punjab', 'district': 'Ludhiana'},
    soil_type='loam',
    farm_size_acres=5.0,
    selected_crops=['Wheat', 'Rice', 'Cotton']
)

if result['success']:
    print("Kharif Crops:", result['kharif_crops'])
    print("Rabi Crops:", result['rabi_crops'])
    print("Zaid Crops:", result['zaid_crops'])
```

### Crop Comparison

```python
from tools.crop_selection_tools import create_crop_selection_tools

tools = create_crop_selection_tools()

# Compare multiple crops
result = tools.compare_crop_options(
    crop_list=['Wheat', 'Rice', 'Maize'],
    soil_analysis=soil_analysis,
    location=location,
    farm_size_acres=5.0,
    comparison_criteria=['profitability', 'water_requirements', 'risk_level']
)

if result['success']:
    print("Recommendation:", result['recommendation'])
```

## AWS Lambda Deployment

### Lambda Handler

The `crop_selection_lambda.py` provides a Lambda handler for serverless deployment:

```python
# Lambda event structure
event = {
    "operation": "recommend_crops",
    "parameters": {
        "soil_analysis": {...},
        "location": {...},
        "farm_size_acres": 5.0
    }
}
```

### Supported Operations

1. **recommend_crops**: Get crop recommendations
2. **calculate_profitability**: Calculate crop profitability
3. **generate_calendar**: Generate seasonal calendar
4. **compare_crops**: Compare multiple crops

### Lambda Configuration

- **Runtime**: Python 3.12
- **Memory**: 512 MB (minimum)
- **Timeout**: 60 seconds
- **IAM Role**: Requires Bedrock and DynamoDB permissions

## Integration with Strands Agents

The tools are designed for integration with AWS Strands Agents framework:

```python
from tools.crop_selection_tools import CropSelectionTools

# Initialize tools
crop_tools = CropSelectionTools(region='us-east-1')

# Use in agent workflow
@tool
def get_crop_recommendations(soil_data, location, farm_size):
    """Tool for Strands Agent to get crop recommendations"""
    return crop_tools.recommend_crops(
        soil_analysis=soil_data,
        location=location,
        farm_size_acres=farm_size
    )
```

## Data Models

### Soil Analysis Input
```python
{
    'soil_type': str,  # clay, loam, sandy, silt, peat, chalky
    'fertility_level': str,  # low, medium, high
    'ph_level': float,  # 0-14
    'npk_levels': {
        'nitrogen': str,  # low, medium, high
        'phosphorus': str,
        'potassium': str
    },
    'organic_matter': float,  # percentage
    'deficiencies': List[str]
}
```

### Location Input
```python
{
    'state': str,
    'district': str
}
```

### Crop Recommendation Output
```python
{
    'success': bool,
    'recommendation_id': str,
    'highly_recommended_crops': List[Dict],
    'moderately_suitable_crops': List[Dict],
    'not_recommended_crops': List[str],
    'full_recommendations': str
}
```

### Profitability Output
```python
{
    'success': bool,
    'crop_name': str,
    'input_costs_per_acre': float,
    'expected_yield_per_acre': float,
    'revenue_per_acre': float,
    'net_profit_per_acre': float,
    'profit_margin': float,
    'roi': float,
    'risk_rating': str,
    'full_analysis': str
}
```

## Testing

Run the test suite:

```bash
# Run all crop selection tests
pytest tests/test_crop_selection.py -v

# Run specific test
pytest tests/test_crop_selection.py::TestCropSelectionTools::test_recommend_crops_success -v

# Run with coverage
pytest tests/test_crop_selection.py --cov=tools.crop_selection_tools
```

## Examples

See `examples/crop_selection_example.py` for comprehensive usage examples:

```bash
python examples/crop_selection_example.py
```

## Best Practices

### 1. Soil Analysis Integration
Always use soil analysis data from `soil_analysis_tools.py` for accurate recommendations:

```python
from tools.soil_analysis_tools import analyze_soil_image
from tools.crop_selection_tools import recommend_crops

# First, analyze soil
soil_result = analyze_soil_image(image_data, user_id, farm_id, location)

# Then, get crop recommendations
if soil_result['success']:
    crop_result = recommend_crops(
        soil_analysis=soil_result,
        location=location,
        farm_size_acres=farm_size
    )
```

### 2. Market Price Updates
For production use, integrate real market price APIs:

```python
# Replace mock prices with real data
def get_real_market_price(crop_name, location):
    # Call market price API
    return api.get_current_price(crop_name, location)

result = calculate_crop_profitability(
    crop_name='Wheat',
    market_price=get_real_market_price('Wheat', location),
    ...
)
```

### 3. Climate Data Integration
Integrate weather APIs for accurate recommendations:

```python
climate_data = {
    'temperature': {'min': 15, 'max': 32},
    'rainfall': 700,  # mm
    'season': 'kharif',
    'forecast': weather_api.get_forecast(location)
}

result = recommend_crops(
    soil_analysis=soil_analysis,
    climate_data=climate_data,
    ...
)
```

### 4. Error Handling
Always check for success and handle errors:

```python
result = recommend_crops(...)

if result['success']:
    # Process recommendations
    process_recommendations(result)
else:
    # Handle error
    logger.error(f"Crop recommendation failed: {result['error']}")
    notify_user(result['error'])
```

## Limitations

1. **Mock Market Data**: Currently uses mock market prices. Integrate real market APIs for production.
2. **Mock Climate Data**: Uses typical regional patterns. Integrate weather APIs for real-time data.
3. **Language**: Recommendations are in English. Use translation_tools for multilingual support.
4. **Regional Coverage**: Optimized for Indian agriculture. May need adjustments for other regions.

## Future Enhancements

- [ ] Real-time market price integration
- [ ] Weather API integration
- [ ] IoT sensor data integration
- [ ] Crop disease risk prediction
- [ ] Water requirement optimization
- [ ] Carbon footprint calculation
- [ ] Organic certification guidance
- [ ] Crop insurance recommendations

## Support

For issues or questions:
- Check the examples in `examples/crop_selection_example.py`
- Review test cases in `tests/test_crop_selection.py`
- Consult the main RISE documentation

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) project.
