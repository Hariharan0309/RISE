# RISE Crop Profitability Calculator

Comprehensive crop profitability analysis system with cost estimation, yield prediction, and risk assessment for informed farming decisions.

## Features

### 1. Comprehensive Profitability Analysis
- **Multi-scenario projections**: Conservative, average, and optimistic scenarios
- **Real-time market price integration**: Fetches current market prices from multiple sources
- **Complete cost breakdown**: Seeds, fertilizers, labor, water, equipment, and more
- **ROI and profit margin calculations**: Detailed financial metrics
- **Risk-adjusted projections**: Accounts for weather, pest, and market risks

### 2. Cost Estimation Engine
- **14 cost categories tracked**:
  - Seeds/Seedlings
  - Fertilizers (NPK)
  - Organic Manure
  - Pesticides
  - Fungicides
  - Irrigation
  - Labor (Planting, Maintenance, Harvesting)
  - Equipment Rental
  - Transportation
  - Storage
  - Miscellaneous

- **Location-based adjustments**: State-specific cost variations
- **Soil-type adjustments**: Different soil types require different inputs
- **Season-specific costs**: Costs vary by growing season

### 3. Yield Prediction Model
- **Historical data integration**: Uses past yields for better accuracy
- **Multi-factor analysis**:
  - Soil type factor
  - Location/state factor
  - Season suitability factor
  - Weather impact factor
- **Confidence scoring**: High confidence with historical data, medium without
- **Three yield scenarios**: Conservative, average, and optimistic predictions

### 4. Risk Assessment
- **Weather risk analysis**: Based on forecasts and seasonal patterns
- **Pest and disease risk**: Crop-specific vulnerability assessment
- **Market volatility risk**: Price fluctuation analysis
- **Yield variability risk**: Based on historical patterns
- **Overall risk scoring**: 1-10 scale with mitigation strategies

### 5. Crop Comparison
- **Side-by-side analysis**: Compare up to 5 crops simultaneously
- **Multiple ranking criteria**:
  - By profit
  - By ROI
  - By low risk
- **Best overall recommendation**: Data-driven crop selection
- **Detailed comparison tables**: All metrics in one view

## Installation

```bash
# Install required dependencies
pip install boto3 plotly pandas streamlit

# Set up AWS credentials
aws configure

# Set environment variables (optional)
export AWS_REGION=us-east-1
export OPENWEATHER_API_KEY=your_api_key_here
```

## Usage

### Python API

#### 1. Calculate Single Crop Profitability

```python
from tools.profitability_calculator_tools import ProfitabilityCalculatorTools

tools = ProfitabilityCalculatorTools()

location = {
    'state': 'Punjab',
    'district': 'Ludhiana',
    'latitude': 30.9010,
    'longitude': 75.8573
}

result = tools.calculate_comprehensive_profitability(
    crop_name='wheat',
    farm_size_acres=5.0,
    location=location,
    soil_type='loamy',
    season='rabi'
)

if result['success']:
    avg_scenario = result['profitability_scenarios']['average']
    print(f"Net Profit: ₹{avg_scenario['net_profit']:,.2f}")
    print(f"ROI: {avg_scenario['roi_percent']:.2f}%")
    print(f"Risk Level: {result['risk_assessment']['overall_risk_level']}")
```

#### 2. Compare Multiple Crops

```python
result = tools.compare_crop_profitability(
    crop_list=['wheat', 'rice', 'maize'],
    farm_size_acres=5.0,
    location=location,
    soil_type='loamy',
    season='rabi'
)

if result['success']:
    print(f"Best Overall: {result['best_overall']}")
    print(f"By Profit: {result['rankings']['by_profit']}")
    print(f"By ROI: {result['rankings']['by_roi']}")
```

#### 3. Estimate Input Costs

```python
result = tools.estimate_input_costs(
    crop_name='cotton',
    farm_size_acres=10.0,
    location=location,
    soil_type='black',
    season='kharif'
)

if result['success']:
    print(f"Cost Per Acre: ₹{result['total_cost_per_acre']:,.2f}")
    print(f"Total Farm Cost: ₹{result['total_farm_cost']:,.2f}")
    
    for category, amount in result['cost_categories'].items():
        print(f"{category}: ₹{amount:,.2f}")
```

#### 4. Predict Crop Yield

```python
historical_data = {
    'past_yields': [18.5, 19.2, 17.8, 20.1, 18.9]
}

result = tools.predict_crop_yield(
    crop_name='rice',
    location=location,
    soil_type='alluvial',
    season='kharif',
    historical_data=historical_data
)

if result['success']:
    yields = result['yield_per_acre_quintals']
    print(f"Average Yield: {yields['average']:.2f} quintals/acre")
    print(f"Range: {yields['conservative']:.2f} - {yields['optimistic']:.2f}")
```

### Lambda Function

#### Event Structure

```json
{
  "action": "calculate_profitability",
  "crop_name": "wheat",
  "farm_size_acres": 5.0,
  "location": {
    "state": "Punjab",
    "district": "Ludhiana",
    "latitude": 30.9010,
    "longitude": 75.8573
  },
  "soil_type": "loamy",
  "season": "rabi"
}
```

#### Supported Actions

- `calculate_profitability`: Comprehensive profitability analysis
- `compare_crops`: Compare multiple crops (requires `crop_list`)
- `estimate_costs`: Cost estimation only
- `predict_yield`: Yield prediction only

### Streamlit UI

```bash
# Run the profitability calculator UI
streamlit run ui/profitability_calculator.py
```

The UI provides three main tabs:
1. **Single Crop Analysis**: Detailed profitability analysis with charts
2. **Compare Crops**: Side-by-side comparison of multiple crops
3. **Cost Estimator**: Detailed cost breakdown and estimation

## Data Models

### Profitability Result

```python
{
    'success': True,
    'analysis_id': 'prof_abc123',
    'crop_name': 'wheat',
    'farm_size_acres': 5.0,
    'market_price_per_quintal': 2200,
    'cost_breakdown': {
        'costs_per_acre': {...},
        'total_cost_per_acre': 18500,
        'total_farm_cost': 92500,
        'cost_categories': {...}
    },
    'yield_prediction': {
        'yield_per_acre_quintals': {
            'average': 18.0,
            'optimistic': 22.5,
            'conservative': 13.5
        },
        'factors_applied': {...},
        'confidence': 'medium'
    },
    'profitability_scenarios': {
        'average': {
            'total_yield_quintals': 90.0,
            'total_revenue': 198000,
            'total_cost': 92500,
            'net_profit': 105500,
            'roi_percent': 114.05,
            'profit_margin_percent': 53.28
        },
        'optimistic': {...},
        'conservative': {...}
    },
    'risk_assessment': {
        'risk_factors': [...],
        'overall_risk_score': 4.5,
        'overall_risk_level': 'medium',
        'recommendation': '...'
    },
    'projections': {
        'expected_profit': 98750,
        'break_even_price': 1027.78,
        'break_even_yield': 42.05
    }
}
```

## Supported Crops

The system has detailed cost and yield data for:
- **Cereals**: Wheat, Rice, Maize, Bajra, Jowar, Barley
- **Cash Crops**: Cotton, Sugarcane, Sunflower, Mustard
- **Pulses**: Chickpea, Pigeon Pea, Lentil
- **Vegetables**: Potato, Tomato, Onion
- **Oilseeds**: Soybean, Groundnut

For crops not in the database, the system uses average values.

## Soil Types Supported

- Loamy (baseline)
- Clay
- Sandy
- Black (cotton soil)
- Red
- Alluvial
- Laterite
- Silt

## Seasons

- **Kharif**: Monsoon season (June-October)
- **Rabi**: Winter season (November-March)
- **Zaid**: Summer season (March-June)
- **Perennial**: Year-round crops

## Integration with Other RISE Tools

### Market Price Tools
- Fetches real-time market prices for revenue calculations
- Uses price history for trend analysis
- Integrates optimal selling time recommendations

### Weather Tools
- Assesses weather impact on yield predictions
- Provides weather risk assessment
- Factors current conditions into profitability

### Crop Selection Tools
- Complements crop recommendation system
- Provides financial validation for crop choices
- Enables data-driven decision making

## Cost Database

The system maintains comprehensive cost databases with:
- **Per-acre costs** for all major crops
- **Regional variations** across Indian states
- **Soil-type adjustments** for input requirements
- **Seasonal variations** in costs

Costs are regularly updated based on:
- Government agricultural statistics
- Market surveys
- Farmer feedback
- Input price trends

## Yield Database

Yield predictions are based on:
- **National average yields** by crop
- **State-wise productivity** factors
- **Soil suitability** multipliers
- **Season optimization** factors
- **Weather impact** adjustments

## Risk Assessment Methodology

### Weather Risk (Score: 1-10)
- Based on forecast data and seasonal patterns
- Considers extreme temperature, rainfall, and adverse events
- Provides specific mitigation strategies

### Pest/Disease Risk (Score: 1-10)
- Crop-specific vulnerability assessment
- Season-based risk variations
- Integrated pest management recommendations

### Market Risk (Score: 1-10)
- Historical price volatility analysis
- Government support (MSP) consideration
- Market demand trends

### Yield Variability Risk (Score: 1-10)
- Based on yield prediction range
- Historical yield stability
- Environmental factors

## Examples

See `examples/profitability_calculator_example.py` for comprehensive usage examples including:
1. Single crop profitability analysis
2. Multi-crop comparison
3. Cost estimation
4. Yield prediction with historical data
5. Custom input costs

## Testing

```bash
# Run unit tests
python -m pytest tests/test_profitability_calculator.py -v

# Run specific test
python -m pytest tests/test_profitability_calculator.py::TestProfitabilityCalculatorTools::test_calculate_comprehensive_profitability -v
```

## AWS Resources

### DynamoDB Tables

**RISE-ProfitabilityData**
- Stores profitability analysis results
- 90-day TTL for automatic cleanup
- Indexed by analysis_id and timestamp

### Lambda Function

**RISE-ProfitabilityCalculator**
- Handles profitability calculation requests
- Integrates with market price and weather services
- Returns comprehensive analysis results

## Performance

- **Cost estimation**: < 100ms
- **Yield prediction**: < 150ms
- **Comprehensive analysis**: < 500ms (without external API calls)
- **Crop comparison (3 crops)**: < 1.5s

## Limitations

1. **Market prices**: Fallback to mock data if real-time API unavailable
2. **Weather data**: Requires OpenWeatherMap API key for real-time data
3. **Historical data**: Optional but improves prediction accuracy
4. **Crop database**: Limited to major Indian crops

## Future Enhancements

- [ ] Machine learning models for yield prediction
- [ ] Integration with satellite imagery for crop health
- [ ] Real-time commodity market data feeds
- [ ] Crop insurance premium calculations
- [ ] Carbon credit potential assessment
- [ ] Water footprint analysis
- [ ] Sustainability scoring

## Support

For issues, questions, or contributions:
- Check the examples directory for usage patterns
- Review test cases for expected behavior
- Consult the main RISE documentation

## License

Part of the RISE (Rural India Support Engine) project.
