# RISE Local Economy Tracking

## Overview

The Local Economy Tracking system provides comprehensive analytics on the economic impact of resource sharing and cooperative buying in local farming communities. It tracks cost savings, additional income generation, resource utilization, and sustainability metrics to demonstrate the value of community collaboration.

## Features

### 1. Economic Impact Analytics
- **Total Economic Benefit**: Aggregate cost savings and income generation
- **Farmer Participation**: Track unique farmers benefiting from resource sharing
- **Transaction Metrics**: Monitor resource sharing activity levels
- **Community Engagement**: Score community participation and collaboration

### 2. Cost Savings Tracking
- **Equipment Rental Savings**: Calculate savings from renting vs purchasing equipment
- **Cooperative Buying Savings**: Track bulk purchasing discounts (15-30%)
- **Individual Farmer Tracking**: Personal savings breakdown by category
- **Comparison Metrics**: Rental costs vs purchase costs, bulk vs retail prices

### 3. Additional Income Calculator
- **Equipment Sharing Income**: Track income from sharing equipment with other farmers
- **Income by Equipment Type**: Breakdown by tractor, pump, drone, harvester, etc.
- **Income Projections**: Monthly and annual income forecasts
- **Booking Analytics**: Completed vs pending bookings

### 4. Resource Utilization Metrics
- **Overall Utilization Rate**: Percentage of equipment actively being shared
- **Utilization by Type**: Equipment-specific utilization rates
- **Idle Equipment Identification**: Find underutilized resources
- **Optimization Opportunities**: Suggest ways to improve utilization

### 5. Sustainability Metrics
- **Equipment Purchases Avoided**: Number of purchases prevented through sharing
- **CO₂ Emissions Savings**: Environmental impact of reduced manufacturing
- **Resource Efficiency Score**: Overall efficiency of resource utilization
- **Sustainability Level**: Classification from "Needs Improvement" to "Highly Sustainable"

### 6. Community Network Visualization
- **Network Nodes**: All farmers in the community
- **Connection Types**: Equipment sharing and buying group relationships
- **Network Statistics**: Participants, connections, and activity levels
- **Visualization Data**: Ready for graph/network visualization tools

## Architecture

### Components

1. **LocalEconomyTools** (`local_economy_tools.py`)
   - Core business logic for economic calculations
   - DynamoDB integration for data retrieval
   - Metric aggregation and analysis

2. **Lambda Handler** (`local_economy_lambda.py`)
   - AWS Lambda function for serverless execution
   - API Gateway integration
   - Request routing and error handling

3. **Streamlit Dashboard** (`ui/local_economy_dashboard.py`)
   - Interactive web dashboard
   - Real-time metric visualization
   - Export functionality

4. **Unit Tests** (`tests/test_local_economy.py`)
   - Comprehensive test coverage
   - Mock DynamoDB interactions
   - Edge case validation

## API Reference

### Calculate Economic Impact

Calculate comprehensive economic metrics for a location.

**Request:**
```json
{
  "action": "calculate_impact",
  "location": {
    "state": "Punjab",
    "district": "Ludhiana"
  },
  "time_period": {
    "start": "2024-01-01T00:00:00",
    "end": "2024-01-31T23:59:59"
  }
}
```

**Response:**
```json
{
  "success": true,
  "location": {...},
  "time_period": {...},
  "metrics": {
    "equipment_utilization_rate": {
      "overall_rate": 75.5,
      "by_type": {...},
      "total_equipment": 20
    },
    "cost_savings": {
      "total": 150000,
      "from_equipment_sharing": 150000,
      "transaction_count": 45
    },
    "additional_income": {
      "total": 120000,
      "from_equipment_sharing": 120000,
      "transaction_count": 45
    },
    "cooperative_buying_savings": {
      "total": 80000,
      "from_bulk_buying": 80000,
      "group_count": 5
    },
    "transaction_count": {
      "total": 45,
      "unique_farmers": 30,
      "equipment_sharing": 45
    },
    "community_engagement_score": 72.5,
    "sustainability_metrics": {
      "equipment_purchases_avoided": 15,
      "estimated_co2_savings_kg": 75000,
      "resource_efficiency_score": 75.5,
      "shared_equipment_count": 20,
      "sustainability_level": "Sustainable"
    },
    "total_economic_benefit": 350000
  },
  "summary": {
    "total_farmers_benefited": 30,
    "total_transactions": 45,
    "average_savings_per_farmer": 11666.67,
    "engagement_level": "Good"
  }
}
```

### Track Cost Savings

Track cost savings for a specific farmer.

**Request:**
```json
{
  "action": "track_savings",
  "user_id": "farmer_12345",
  "time_period": {
    "start": "2024-01-01T00:00:00",
    "end": "2024-01-31T23:59:59"
  }
}
```

**Response:**
```json
{
  "success": true,
  "user_id": "farmer_12345",
  "time_period": {...},
  "savings_breakdown": {
    "equipment_rental_savings": {
      "total": 45000,
      "rental_cost": 3000,
      "vs_purchase": 150000,
      "booking_count": 3
    },
    "cooperative_buying_savings": {
      "total": 15000,
      "vs_retail": 75000,
      "group_count": 2
    },
    "total_savings": 60000
  },
  "comparison": {
    "vs_equipment_purchase": 150000,
    "vs_retail_prices": 75000
  }
}
```

### Track Additional Income

Track additional income generated from resource sharing.

**Request:**
```json
{
  "action": "track_income",
  "user_id": "farmer_12345",
  "time_period": {
    "start": "2024-01-01T00:00:00",
    "end": "2024-01-31T23:59:59"
  }
}
```

**Response:**
```json
{
  "success": true,
  "user_id": "farmer_12345",
  "time_period": {...},
  "income_breakdown": {
    "by_equipment_type": {
      "tractor": {
        "count": 5,
        "total": 15000
      },
      "pump": {
        "count": 3,
        "total": 4500
      }
    },
    "total_income": 19500,
    "total_bookings": 8,
    "completed_bookings": 8
  },
  "projections": {
    "monthly": 19500,
    "annual": 234000
  }
}
```

### Calculate Resource Utilization

Calculate resource utilization rates for a location.

**Request:**
```json
{
  "action": "resource_utilization",
  "location": {
    "state": "Punjab",
    "district": "Ludhiana"
  },
  "time_period": {
    "start": "2024-01-01T00:00:00",
    "end": "2024-01-31T23:59:59"
  }
}
```

**Response:**
```json
{
  "success": true,
  "location": {...},
  "time_period": {...},
  "utilization_metrics": {
    "overall_rate": 75.5,
    "by_type": {
      "tractor": {
        "rate": 80.0,
        "total": 10,
        "utilized": 8
      },
      "pump": {
        "rate": 70.0,
        "total": 10,
        "utilized": 7
      }
    },
    "total_equipment": 20
  }
}
```

### Generate Sustainability Metrics

Generate sustainability impact metrics.

**Request:**
```json
{
  "action": "sustainability",
  "location": {
    "state": "Punjab",
    "district": "Ludhiana"
  },
  "time_period": {
    "start": "2024-01-01T00:00:00",
    "end": "2024-01-31T23:59:59"
  }
}
```

**Response:**
```json
{
  "success": true,
  "location": {...},
  "time_period": {...},
  "sustainability_metrics": {
    "equipment_purchases_avoided": 15,
    "estimated_co2_savings_kg": 75000,
    "resource_efficiency_score": 75.5,
    "shared_equipment_count": 20,
    "sustainability_level": "Sustainable"
  }
}
```

### Get Community Network Data

Get community network visualization data.

**Request:**
```json
{
  "action": "network_data",
  "location": {
    "state": "Punjab",
    "district": "Ludhiana"
  }
}
```

**Response:**
```json
{
  "success": true,
  "location": {...},
  "network": {
    "nodes": [
      {
        "id": "farmer_1",
        "name": "Farmer One"
      },
      {
        "id": "farmer_2",
        "name": "Farmer Two"
      }
    ],
    "connections": [
      {
        "source": "farmer_1",
        "target": "farmer_2",
        "type": "equipment_sharing",
        "value": 3000
      }
    ]
  },
  "statistics": {
    "total_users": 30,
    "active_participants": 25,
    "total_connections": 45,
    "equipment_sharing_connections": 30,
    "buying_group_connections": 15
  }
}
```

## Usage Examples

### Python SDK

```python
from tools.local_economy_tools import LocalEconomyTools

# Initialize tools
economy_tools = LocalEconomyTools(region='us-east-1')

# Calculate economic impact for a location
location = {'state': 'Punjab', 'district': 'Ludhiana'}
time_period = {
    'start': '2024-01-01T00:00:00',
    'end': '2024-01-31T23:59:59'
}

result = economy_tools.calculate_economic_impact(location, time_period)
print(f"Total Economic Benefit: ₹{result['metrics']['total_economic_benefit']:,.2f}")

# Track cost savings for a farmer
user_id = 'farmer_12345'
savings = economy_tools.track_cost_savings(user_id, time_period)
print(f"Total Savings: ₹{savings['savings_breakdown']['total_savings']:,.2f}")

# Track additional income
income = economy_tools.track_additional_income(user_id, time_period)
print(f"Total Income: ₹{income['income_breakdown']['total_income']:,.2f}")
```

### AWS Lambda

```python
import json
from local_economy_lambda import lambda_handler

# Calculate economic impact
event = {
    'action': 'calculate_impact',
    'location': {
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
}

response = lambda_handler(event, None)
result = json.loads(response['body'])
```

### Streamlit Dashboard

```bash
# Run the dashboard
streamlit run ui/local_economy_dashboard.py
```

## Metrics Explained

### Economic Benefit Calculation

**Total Economic Benefit** = Cost Savings + Additional Income + Cooperative Savings

- **Cost Savings**: Money saved by renting equipment instead of purchasing
- **Additional Income**: Money earned by sharing equipment with others
- **Cooperative Savings**: Money saved through bulk purchasing in groups

### Engagement Score (0-100)

The engagement score is calculated based on:
- **Transaction Score** (30 points): Number of resource sharing transactions
- **Utilization Score** (40 points): Equipment utilization rate
- **Participation Score** (30 points): Number of unique farmers participating

**Engagement Levels:**
- 80-100: Excellent
- 60-79: Good
- 40-59: Moderate
- 20-39: Low
- 0-19: Very Low

### Sustainability Score

**Resource Efficiency Score** = Equipment Utilization Rate

**Sustainability Levels:**
- 80-100: Highly Sustainable
- 60-79: Sustainable
- 40-59: Moderately Sustainable
- 0-39: Needs Improvement

## Database Schema

### Required DynamoDB Tables

1. **RISE-ResourceSharing**: Equipment listings
2. **RISE-ResourceBookings**: Equipment bookings and transactions
3. **RISE-BuyingGroups**: Cooperative buying groups
4. **RISE-UserProfiles**: Farmer profiles and locations

## Testing

Run unit tests:

```bash
python -m pytest tests/test_local_economy.py -v
```

Run with coverage:

```bash
python -m pytest tests/test_local_economy.py --cov=tools.local_economy_tools --cov-report=html
```

## Deployment

### AWS Lambda Deployment

1. Package dependencies:
```bash
pip install -r requirements.txt -t package/
cp tools/local_economy_tools.py package/
cp tools/local_economy_lambda.py package/
cd package && zip -r ../local_economy_lambda.zip .
```

2. Deploy to Lambda:
```bash
aws lambda create-function \
  --function-name rise-local-economy \
  --runtime python3.9 \
  --handler local_economy_lambda.lambda_handler \
  --zip-file fileb://local_economy_lambda.zip \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role
```

3. Configure API Gateway trigger

### Environment Variables

- `AWS_REGION`: AWS region (default: us-east-1)

## Performance Considerations

- **Caching**: Implement caching for frequently accessed metrics
- **Batch Processing**: Use DynamoDB batch operations for large datasets
- **Pagination**: Implement pagination for large result sets
- **Indexes**: Use GSIs for efficient location-based queries

## Security

- All API endpoints require authentication
- User data is encrypted at rest and in transit
- Access control via IAM roles and policies
- Audit logging for all data access

## Troubleshooting

### Common Issues

1. **No data returned**: Check if DynamoDB tables have data for the specified location/time period
2. **High latency**: Consider implementing caching or using DynamoDB DAX
3. **Calculation errors**: Verify data types (Decimal vs float) in DynamoDB

## Future Enhancements

- Real-time metric updates using DynamoDB Streams
- Advanced analytics with machine learning predictions
- Comparative analysis across multiple locations
- Export to PDF/Excel formats
- Integration with external economic databases

## Support

For issues or questions:
- Check the example scripts in `examples/local_economy_example.py`
- Review unit tests in `tests/test_local_economy.py`
- Consult the main RISE documentation

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) project.
