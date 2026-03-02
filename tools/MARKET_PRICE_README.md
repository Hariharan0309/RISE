# RISE Market Price Tracking System

## Overview

The Market Price Tracking system provides real-time market intelligence for farmers, enabling them to make informed decisions about when and where to sell their crops. The system integrates with government agricultural market data sources and provides price predictions using basic machine learning.

## Features

### 1. Real-Time Price Information
- Current market prices from multiple markets within configurable radius (default 50km)
- Price statistics: minimum, maximum, and average prices
- Market details: location, distance, arrival quantities
- Automatic caching with 6-hour TTL for performance

### 2. Historical Price Tracking
- 30-day historical price data storage
- Price trend analysis (increasing, decreasing, stable)
- Volatility calculations
- Price range and average calculations

### 3. Price Trend Predictions
- Basic ML-based price forecasting (moving average method)
- 7-14 day price predictions
- Confidence ranges for predictions
- Trend continuation analysis

### 4. Optimal Selling Time Calculator
- Considers crop perishability
- Factors in storage capacity and costs
- Analyzes price trends and predictions
- Provides actionable recommendations with reasoning

### 5. Interactive Dashboard
- Visual price comparisons across markets
- Historical price charts with trend lines
- Prediction visualizations with confidence bands
- Selling advice with detailed breakdowns

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Market Price System                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌──────────────────────────┐   │
│  │   Streamlit  │◄────►│  Market Price Tools      │   │
│  │  Dashboard   │      │  (market_price_tools.py) │   │
│  └──────────────┘      └──────────────────────────┘   │
│                                 │                       │
│                                 ▼                       │
│                        ┌─────────────────┐             │
│                        │  Lambda Handler │             │
│                        │ (market_price_  │             │
│                        │    lambda.py)   │             │
│                        └─────────────────┘             │
│                                 │                       │
│                    ┌────────────┴────────────┐         │
│                    ▼                         ▼         │
│           ┌─────────────────┐      ┌─────────────┐    │
│           │   DynamoDB      │      │  External   │    │
│           │ (Price Cache &  │      │  Market     │    │
│           │    History)     │      │  Data APIs  │    │
│           └─────────────────┘      └─────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- Python 3.8+
- AWS Account with DynamoDB access
- boto3 library
- requests library

### Setup

1. Install required packages:
```bash
pip install boto3 requests python-dotenv
```

2. Configure AWS credentials:
```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
```

3. Create DynamoDB table:
```python
# Table name: RISE-MarketPrices
# Partition key: crop_market_id (String)
# Sort key: timestamp (Number)
# GSI: cache_key (String) for caching
```

## Usage

### Basic Usage

```python
from tools.market_price_tools import create_market_price_tools

# Initialize tools
tools = create_market_price_tools(region='us-east-1')

# Get current prices
result = tools.get_current_prices(
    crop_name='wheat',
    latitude=28.6139,
    longitude=77.2090,
    radius_km=50
)

if result['success']:
    print(f"Average Price: ₹{result['statistics']['avg_price']:.2f}/quintal")
    print(f"Markets Found: {result['statistics']['market_count']}")
```

### Get Price History

```python
# Get 30-day price history
result = tools.get_price_history(
    crop_name='wheat',
    market_id='MKT001',
    days=30
)

if result['success']:
    trends = result['trends']
    print(f"Trend: {trends['trend']}")
    print(f"Change: {trends['change_percent']}%")
```

### Predict Price Trends

```python
# Predict prices for next 7 days
result = tools.predict_price_trends(
    crop_name='wheat',
    market_id='MKT001',
    forecast_days=7
)

if result['success']:
    for pred in result['predictions']:
        print(f"{pred['date']}: ₹{pred['predicted_price']:.2f}")
```

### Calculate Optimal Selling Time

```python
# Get selling recommendation
result = tools.get_optimal_selling_time(
    crop_name='wheat',
    latitude=28.6139,
    longitude=77.2090,
    harvest_date=None,
    storage_capacity=True
)

if result['success']:
    rec = result['recommendation']
    print(f"Timing: {rec['timing']}")
    print(f"Reason: {rec['reason']}")
    print(f"Expected Price: ₹{rec['expected_price']:.2f}")
```

### Streamlit Dashboard

```python
import streamlit as st
from tools.market_price_tools import create_market_price_tools
from ui.market_price_dashboard import render_market_price_dashboard

# Initialize tools
tools = create_market_price_tools()

# User location
user_location = {
    'latitude': 28.6139,
    'longitude': 77.2090
}

# Render dashboard
render_market_price_dashboard(tools, user_location)
```

## API Reference

### MarketPriceTools Class

#### `get_current_prices(crop_name, latitude, longitude, radius_km=50)`
Get current market prices for a crop within specified radius.

**Parameters:**
- `crop_name` (str): Name of the crop
- `latitude` (float): Location latitude
- `longitude` (float): Location longitude
- `radius_km` (int): Search radius in kilometers (default: 50)

**Returns:**
```python
{
    'success': True,
    'crop_name': 'wheat',
    'location': {...},
    'markets': [...],
    'statistics': {
        'min_price': 2400,
        'max_price': 2550,
        'avg_price': 2475,
        'market_count': 3
    },
    'timestamp': '2024-01-15T10:30:00',
    'currency': 'INR',
    'unit': 'quintal'
}
```

#### `get_price_history(crop_name, market_id, days=30)`
Get historical price data for a crop at a specific market.

**Parameters:**
- `crop_name` (str): Name of the crop
- `market_id` (str): Market identifier
- `days` (int): Number of days of history (default: 30)

**Returns:**
```python
{
    'success': True,
    'crop_name': 'wheat',
    'market_id': 'MKT001',
    'period': {...},
    'history': [...],
    'trends': {
        'trend': 'increasing',
        'change_percent': 8.5,
        'volatility': 45.2,
        'avg_price': 2450
    }
}
```

#### `predict_price_trends(crop_name, market_id, forecast_days=7)`
Predict future price trends using basic ML.

**Parameters:**
- `crop_name` (str): Name of the crop
- `market_id` (str): Market identifier
- `forecast_days` (int): Number of days to forecast (default: 7)

**Returns:**
```python
{
    'success': True,
    'crop_name': 'wheat',
    'market_id': 'MKT001',
    'forecast_days': 7,
    'predictions': [
        {
            'date': '2024-01-16T00:00:00',
            'predicted_price': 2480,
            'confidence_range': {
                'low': 2356,
                'high': 2604
            }
        },
        ...
    ],
    'confidence': 'medium',
    'method': 'moving_average'
}
```

#### `get_optimal_selling_time(crop_name, latitude, longitude, harvest_date, storage_capacity)`
Calculate optimal selling time based on multiple factors.

**Parameters:**
- `crop_name` (str): Name of the crop
- `latitude` (float): Location latitude
- `longitude` (float): Location longitude
- `harvest_date` (str, optional): Expected harvest date (ISO format)
- `storage_capacity` (bool): Whether farmer has storage capacity

**Returns:**
```python
{
    'success': True,
    'crop_name': 'wheat',
    'current_best_price': 2500,
    'best_market': {...},
    'recommendation': {
        'timing': 'wait_5_days',
        'reason': 'Price expected to increase...',
        'expected_price': 2580,
        'storage_cost': 10,
        'net_gain': 70,
        'confidence': 'medium'
    },
    'perishability': {
        'category': 'non_perishable',
        'shelf_life_days': 365,
        'storage_cost_per_day': 1
    }
}
```

## Lambda Function

### Deployment

```bash
# Package Lambda function
cd tools
zip -r market_price_lambda.zip market_price_lambda.py market_price_tools.py

# Deploy using AWS CLI
aws lambda create-function \
  --function-name RISE-MarketPriceTracker \
  --runtime python3.9 \
  --handler market_price_lambda.lambda_handler \
  --zip-file fileb://market_price_lambda.zip \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role
```

### API Gateway Integration

```json
{
  "action": "current_prices",
  "crop_name": "wheat",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "radius_km": 50
}
```

## Data Sources

### Government APIs (Production Integration)
- **AgMarkNet**: https://agmarknet.gov.in/ - Agricultural market prices
- **data.gov.in**: Agricultural datasets and market information
- **State Agricultural Marketing Boards**: Regional market data

### Mock Data (Development)
The system includes mock data generators for development and testing purposes.

## Crop Perishability Database

The system includes a comprehensive crop perishability database:

| Crop | Category | Shelf Life | Storage Cost/Day |
|------|----------|------------|------------------|
| Tomato | Highly Perishable | 7 days | ₹5 |
| Banana | Highly Perishable | 5 days | ₹4 |
| Potato | Moderately Perishable | 90 days | ₹2 |
| Onion | Moderately Perishable | 120 days | ₹2 |
| Wheat | Non-Perishable | 365 days | ₹1 |
| Rice | Non-Perishable | 365 days | ₹1 |

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/test_market_price.py -v

# Run specific test
pytest tests/test_market_price.py::TestMarketPriceTools::test_get_current_prices -v

# Run with coverage
pytest tests/test_market_price.py --cov=tools.market_price_tools
```

## Examples

See `examples/market_price_example.py` for comprehensive usage examples:

```bash
python examples/market_price_example.py
```

## Performance Considerations

### Caching Strategy
- Current prices cached for 6 hours
- Historical data cached in DynamoDB
- Cache keys based on crop, location (rounded to 2 decimals), and radius

### Optimization Tips
1. Use appropriate radius (50km default is optimal)
2. Batch requests for multiple crops
3. Leverage caching for repeated queries
4. Use DynamoDB DAX for hot data access

## Limitations

### Current Version
- Mock data for demonstration (production requires API integration)
- Basic ML prediction (moving average method)
- Limited to 50km radius for performance
- 30-day historical data retention

### Future Enhancements
- Integration with real government APIs
- Advanced ML models (LSTM, Prophet)
- Real-time price alerts
- Market sentiment analysis
- Supply-demand forecasting

## Troubleshooting

### Common Issues

**Issue: No markets found**
- Check if radius is sufficient
- Verify coordinates are valid
- Ensure crop name is correct

**Issue: Cache not working**
- Verify DynamoDB table exists
- Check AWS credentials
- Ensure table has correct schema

**Issue: Predictions inaccurate**
- Requires at least 7 days of historical data
- Basic ML has medium confidence
- Consider external factors (weather, festivals)

## Support

For issues and questions:
- Check examples: `examples/market_price_example.py`
- Run tests: `pytest tests/test_market_price.py`
- Review logs: CloudWatch Logs for Lambda function

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) project.
