# RISE Optimal Selling Time Calculator

Advanced tools for calculating optimal selling time with comprehensive perishability analysis, storage cost calculations, and price alert system.

## Overview

The Optimal Selling Time Calculator helps farmers maximize their profits by:
- Analyzing crop perishability factors
- Calculating storage costs including quality degradation
- Determining optimal selling time based on price predictions
- Providing price alerts when target prices are reached

## Features

### 1. Perishability Analysis
Comprehensive database of crop perishability factors:
- **Highly Perishable** (1-14 days): Tomatoes, leafy greens, bananas, mangoes
- **Moderately Perishable** (15-120 days): Potatoes, onions, carrots
- **Non-Perishable** (>120 days): Wheat, rice, pulses

Each crop includes:
- Shelf life in days
- Quality degradation rate
- Optimal storage temperature
- Storage requirements
- Post-harvest loss rate

### 2. Storage Cost Calculator
Calculates comprehensive storage costs:
- **Facility costs** based on storage type (standard, cold, warehouse)
- **Handling costs** for loading/unloading
- **Insurance costs** for stored produce
- **Quality degradation** impact on value

Storage types:
- **Standard**: Basic covered storage
- **Cold**: Temperature-controlled storage for perishables
- **Warehouse**: Professional storage facilities

### 3. Optimal Selling Time Algorithm
Analyzes multiple scenarios to find the best selling time:
- Compares immediate sale vs. waiting for better prices
- Factors in storage costs and quality degradation
- Considers crop perishability and shelf life
- Calculates net profit for each scenario
- Provides confidence levels for recommendations

### 4. Price Alert System
Automated alerts when target prices are reached:
- Set target prices for specific crops and markets
- SMS and email notifications
- Track multiple alerts per user
- Automatic alert triggering when prices match

## Installation

```bash
# Install dependencies
pip install boto3

# Set up AWS credentials
aws configure

# Create required DynamoDB tables
aws dynamodb create-table \
    --table-name RISE-PriceAlerts \
    --attribute-definitions \
        AttributeName=alert_id,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
        AttributeName=status,AttributeType=S \
    --key-schema \
        AttributeName=alert_id,KeyType=HASH \
    --global-secondary-indexes \
        IndexName=user_id-status-index,KeySchema=[{AttributeName=user_id,KeyType=HASH},{AttributeName=status,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5

aws dynamodb create-table \
    --table-name RISE-StorageCosts \
    --attribute-definitions \
        AttributeName=storage_id,AttributeType=S \
    --key-schema \
        AttributeName=storage_id,KeyType=HASH \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5
```

## Usage

### Python API

```python
from tools.selling_time_tools import create_selling_time_tools
from datetime import datetime, timedelta

# Initialize tools
tools = create_selling_time_tools()

# 1. Analyze crop perishability
perish_result = tools.analyze_perishability('tomato')
print(f"Category: {perish_result['category']}")
print(f"Shelf Life: {perish_result['shelf_life_days']} days")

# 2. Calculate storage costs
storage_result = tools.calculate_storage_costs(
    crop_name='wheat',
    quantity_quintals=100,
    storage_days=30,
    storage_type='warehouse'
)
print(f"Total Cost: ₹{storage_result['costs']['total_cost']}")

# 3. Calculate optimal selling time
predicted_prices = [
    {
        'date': (datetime.now() + timedelta(days=i)).isoformat(),
        'predicted_price': 2400 + i * 50
    }
    for i in range(1, 15)
]

optimal_result = tools.calculate_optimal_selling_time(
    crop_name='wheat',
    current_price=2400,
    predicted_prices=predicted_prices,
    quantity_quintals=100,
    storage_capacity=True,
    storage_type='warehouse'
)
print(f"Recommendation: {optimal_result['recommendation']['timing']}")
print(f"Net Profit: ₹{optimal_result['recommendation']['net_profit']}")

# 4. Create price alert
alert_result = tools.create_price_alert(
    user_id='farmer_001',
    crop_name='wheat',
    target_price=2800,
    market_id='MKT001',
    phone_number='+919876543210'
)
print(f"Alert ID: {alert_result['alert_id']}")
```

### Lambda Function

Deploy as AWS Lambda for serverless operation:

```python
# Event structure
event = {
    "action": "calculate_optimal_time",
    "crop_name": "wheat",
    "current_price": 2400,
    "predicted_prices": [...],
    "quantity_quintals": 100,
    "storage_capacity": True,
    "storage_type": "warehouse"
}

# Invoke Lambda
response = lambda_client.invoke(
    FunctionName='RISE-SellingTimeCalculator',
    Payload=json.dumps(event)
)
```

## API Reference

### SellingTimeTools Class

#### `analyze_perishability(crop_name: str)`
Analyze crop perishability factors.

**Parameters:**
- `crop_name`: Name of the crop

**Returns:**
```python
{
    'success': True,
    'crop_name': 'tomato',
    'category': 'highly_perishable',
    'shelf_life_days': 7,
    'quality_degradation_rate': 0.15,
    'optimal_storage_temp': '10-12°C',
    'storage_requirements': 'Cold storage with humidity control',
    'post_harvest_loss_rate': 0.25,
    'recommendation': 'Sell within 7 days...'
}
```

#### `calculate_storage_costs(crop_name, quantity_quintals, storage_days, storage_type)`
Calculate storage costs including quality degradation.

**Parameters:**
- `crop_name`: Name of the crop
- `quantity_quintals`: Quantity in quintals
- `storage_days`: Number of days to store
- `storage_type`: 'standard', 'cold', or 'warehouse'

**Returns:**
```python
{
    'success': True,
    'costs': {
        'facility_cost': 3000.0,
        'handling_cost': 1000.0,
        'insurance_cost': 1500.0,
        'total_cost': 5500.0,
        'cost_per_quintal': 55.0,
        'cost_per_day': 183.33
    },
    'quality_impact': {
        'degradation_percent': 3.0,
        'remaining_quality': 97.0
    }
}
```

#### `calculate_optimal_selling_time(crop_name, current_price, predicted_prices, quantity_quintals, storage_capacity, storage_type)`
Calculate optimal selling time considering all factors.

**Parameters:**
- `crop_name`: Name of the crop
- `current_price`: Current market price per quintal
- `predicted_prices`: List of predicted prices with dates
- `quantity_quintals`: Quantity to sell
- `storage_capacity`: Whether storage is available
- `storage_type`: Type of storage available

**Returns:**
```python
{
    'success': True,
    'recommendation': {
        'timing': 'wait_7_days',
        'days_to_wait': 7,
        'optimal_date': '2024-01-15T00:00:00',
        'reason': 'Waiting 7 days will increase net profit...',
        'expected_price': 2750.0,
        'expected_revenue': 275000.0,
        'storage_cost': 3850.0,
        'net_profit': 271150.0,
        'profit_improvement': 31150.0,
        'improvement_percent': 12.98,
        'confidence': 'high'
    },
    'scenarios': [...],
    'perishability': {...}
}
```

#### `create_price_alert(user_id, crop_name, target_price, market_id, phone_number, email)`
Create price alert for target price.

**Parameters:**
- `user_id`: User identifier
- `crop_name`: Name of the crop
- `target_price`: Target price per quintal
- `market_id`: Market to monitor
- `phone_number`: Optional phone for SMS alerts
- `email`: Optional email for alerts

**Returns:**
```python
{
    'success': True,
    'alert_id': 'farmer_001#wheat#MKT001#1234567890',
    'message': 'Price alert created. You will be notified...'
}
```

## Integration with Market Price Tools

The Selling Time Calculator integrates seamlessly with Market Price Tools:

```python
from tools.market_price_tools import create_market_price_tools
from tools.selling_time_tools import create_selling_time_tools

# Get current prices and predictions
market_tools = create_market_price_tools()
price_result = market_tools.get_current_prices('wheat', 28.6139, 77.2090)
predictions = market_tools.predict_price_trends('wheat', 'MKT001', 14)

# Calculate optimal selling time
selling_tools = create_selling_time_tools()
optimal_result = selling_tools.calculate_optimal_selling_time(
    crop_name='wheat',
    current_price=price_result['statistics']['avg_price'],
    predicted_prices=predictions['predictions'],
    quantity_quintals=100,
    storage_capacity=True
)
```

## Examples

See `examples/selling_time_example.py` for comprehensive examples:
- Perishability analysis for different crops
- Storage cost calculations
- Optimal selling time scenarios
- Price alert management
- Comparison of storage types
- Perishable vs non-perishable crops

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/test_selling_time.py -v

# Run specific test
pytest tests/test_selling_time.py::TestSellingTimeTools::test_analyze_perishability_highly_perishable -v

# Run with coverage
pytest tests/test_selling_time.py --cov=tools.selling_time_tools --cov-report=html
```

## Best Practices

1. **Always check perishability first** - Highly perishable crops should be sold quickly
2. **Consider storage capacity** - Don't recommend waiting if no storage available
3. **Factor in quality degradation** - Quality loss reduces effective price
4. **Use realistic predictions** - Price predictions should be based on historical data
5. **Set reasonable target prices** - Price alerts should be achievable
6. **Monitor alerts regularly** - Check triggered alerts and act promptly

## Troubleshooting

### Common Issues

**Issue: Storage costs seem too high**
- Check storage type - cold storage is more expensive
- Verify quantity and duration inputs
- Consider warehouse storage for non-perishables

**Issue: Always recommends immediate sale**
- Check if crop is highly perishable
- Verify storage_capacity is set to True
- Ensure predicted prices show increase

**Issue: Price alerts not triggering**
- Verify alert is in 'active' status
- Check market_id matches current prices
- Ensure target price is reasonable

## Performance Considerations

- **Caching**: Price data is cached for 6 hours
- **DynamoDB**: Uses on-demand billing for cost efficiency
- **Lambda**: Cold start ~2-3 seconds, warm ~200ms
- **Batch Processing**: Can process multiple scenarios in parallel

## Security

- All data encrypted at rest in DynamoDB
- SNS notifications use encrypted channels
- User data isolated by user_id
- TTL enabled for automatic data cleanup

## Future Enhancements

- Machine learning for better price predictions
- Weather impact on storage costs
- Market demand forecasting
- Multi-crop portfolio optimization
- Real-time price monitoring
- Advanced alert conditions (price ranges, trends)

## Support

For issues or questions:
- Check examples in `examples/selling_time_example.py`
- Review tests in `tests/test_selling_time.py`
- See integration with market price tools
- Contact RISE support team

## License

Part of the RISE Farming Assistant project.
