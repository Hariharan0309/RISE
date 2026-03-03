# RISE Cooperative Buying Groups System

## Overview

The Cooperative Buying Groups system enables farmers to join forces and purchase agricultural inputs (seeds, fertilizers, pesticides) at bulk prices, achieving discounts of 15-30%. This system matches farmers by location, crop type, and input requirements, aggregates quantities, and facilitates vendor negotiations.

## Features

### 1. Group Formation
- Create cooperative buying groups for specific products
- Set member limits and deadlines
- Define target products and location radius
- Automatic status management (forming → active → negotiating → completed)

### 2. Farmer Matching
- Match farmers by location (district/state)
- Match by crop type and input requirements
- Calculate match scores based on product overlap
- Filter by group capacity and status

### 3. Quantity Aggregation
- Automatically aggregate member requirements
- Calculate total quantities needed per product
- Track individual member contributions
- Update totals as members join

### 4. Bulk Pricing Calculator
- Calculate discounts based on quantity tiers:
  - 1000+ units: 30% discount
  - 500-999 units: 25% discount
  - 250-499 units: 20% discount
  - 100-249 units: 15% discount
  - <100 units: 10% discount
- Calculate per-member costs
- Estimate potential savings

### 5. AI-Powered Vendor Negotiation
- Generate professional negotiation messages
- Include group details and quantities
- Propose payment terms and delivery requirements
- Support for multiple vendors

### 6. Group Management
- View group details and member lists
- Track group status and progress
- Monitor total quantities and pricing
- Manage payment and delivery coordination

## Architecture

### DynamoDB Table: RISE-BuyingGroups

**Partition Key:** `group_id` (String)

**Attributes:**
- `group_name`: Name of the buying group
- `organizer_user_id`: Group organizer's user ID
- `members`: List of member user IDs
- `target_products`: List of products to purchase
- `location_area`: Location key (district_state)
- `location`: Location details (state, district, radius_km)
- `group_status`: Status (forming, active, negotiating, completed, closed)
- `total_quantity_needed`: Aggregated quantities per product
- `bulk_pricing_achieved`: Discount percentages per product
- `vendor_details`: Vendor negotiation information
- `delivery_schedule`: Delivery coordination details
- `payment_status`: Payment tracking per member
- `member_requirements`: Individual member requirements
- `target_discount_min`: Minimum target discount (15%)
- `target_discount_max`: Maximum target discount (30%)
- `max_members`: Maximum group size
- `min_members`: Minimum members to activate
- `deadline`: Deadline for joining
- `created_timestamp`: Creation timestamp
- `updated_timestamp`: Last update timestamp

**Global Secondary Indexes:**
1. `LocationGroupIndex`: Partition key `location_area`
2. `StatusGroupIndex`: Partition key `group_status`

## API Reference

### BuyingGroupTools Class

#### `create_buying_group(organizer_id, group_data)`
Create a new cooperative buying group.

**Parameters:**
- `organizer_id` (str): Group organizer's user ID
- `group_data` (dict): Group configuration
  - `group_name` (str): Name of the group
  - `target_products` (list): List of products to purchase
  - `location` (dict): Location details
    - `state` (str): State name
    - `district` (str): District name
    - `radius_km` (int): Search radius in kilometers
  - `max_members` (int, optional): Maximum members (default: 50)
  - `min_members` (int, optional): Minimum members (default: 5)
  - `deadline` (str, optional): ISO format deadline

**Returns:**
```python
{
    'success': True,
    'group_id': 'grp_abc123',
    'group_name': 'Ludhiana Seed Buyers',
    'status': 'forming',
    'target_discount': '15-30%',
    'deadline': '2024-01-15T00:00:00'
}
```

#### `find_matching_groups(user_id, requirements)`
Find buying groups matching farmer's requirements.

**Parameters:**
- `user_id` (str): Farmer's user ID
- `requirements` (dict): Search criteria
  - `products` (list): Required products
  - `state` (str, optional): State name
  - `district` (str, optional): District name

**Returns:**
```python
{
    'success': True,
    'count': 3,
    'groups': [
        {
            'group_id': 'grp_abc123',
            'group_name': 'Ludhiana Seed Buyers',
            'matching_products': ['wheat_seeds', 'fertilizer_urea'],
            'match_score': 100.0,
            'current_members': 8,
            'max_members': 30,
            'status': 'active',
            'estimated_discount': '15-30%'
        }
    ]
}
```

#### `join_buying_group(user_id, group_id, member_requirements)`
Join an existing buying group.

**Parameters:**
- `user_id` (str): Farmer's user ID
- `group_id` (str): Group ID to join
- `member_requirements` (dict): Product quantities needed
  - Key: product name (str)
  - Value: quantity (int/float)

**Returns:**
```python
{
    'success': True,
    'group_id': 'grp_abc123',
    'group_name': 'Ludhiana Seed Buyers',
    'status': 'active',
    'total_members': 9,
    'total_quantities': {
        'wheat_seeds': 1200.0,
        'fertilizer_urea': 600.0
    },
    'potential_savings': {
        'wheat_seeds': 30000.0,
        'fertilizer_urea': 15000.0
    }
}
```

#### `calculate_bulk_pricing(group_id, vendor_quotes=None)`
Calculate bulk pricing discounts for group orders.

**Parameters:**
- `group_id` (str): Group ID
- `vendor_quotes` (dict, optional): Vendor price quotes

**Returns:**
```python
{
    'success': True,
    'group_id': 'grp_abc123',
    'pricing_breakdown': {
        'wheat_seeds': {
            'quantity': 1200.0,
            'market_price_per_unit': 1000,
            'bulk_price_per_unit': 700.0,
            'discount_percentage': 30.0,
            'total_cost': 840000.0,
            'total_savings': 360000.0
        }
    },
    'member_costs': {
        'farmer_12345': {
            'total_cost': 105000.0,
            'breakdown': {...}
        }
    },
    'average_discount': 27.5
}
```

#### `negotiate_with_vendors(group_id, vendor_list=None)`
Use AI to negotiate with suppliers for bulk pricing.

**Parameters:**
- `group_id` (str): Group ID
- `vendor_list` (list, optional): List of vendor names/contacts

**Returns:**
```python
{
    'success': True,
    'group_id': 'grp_abc123',
    'negotiation_message': 'Dear Supplier, We are a cooperative...',
    'vendors_contacted': 3,
    'status': 'negotiating',
    'next_steps': [
        'Send negotiation message to vendors',
        'Wait for vendor quotes',
        'Compare quotes and select best offer',
        'Finalize order with selected vendor'
    ]
}
```

#### `get_group_details(group_id)`
Get detailed information about a buying group.

**Parameters:**
- `group_id` (str): Group ID

**Returns:**
```python
{
    'success': True,
    'group_id': 'grp_abc123',
    'group_name': 'Ludhiana Seed Buyers',
    'organizer_user_id': 'farmer_12345',
    'members': ['farmer_12345', 'farmer_67890', ...],
    'member_count': 9,
    'target_products': ['wheat_seeds', 'fertilizer_urea'],
    'location': {...},
    'status': 'active',
    'total_quantities': {...},
    'bulk_pricing': {...},
    'vendor_details': {...}
}
```

#### `get_user_groups(user_id)`
Get all buying groups a user is part of.

**Parameters:**
- `user_id` (str): User ID

**Returns:**
```python
{
    'success': True,
    'count': 2,
    'groups': [
        {
            'group_id': 'grp_abc123',
            'group_name': 'Ludhiana Seed Buyers',
            'status': 'active',
            'member_count': 9,
            'target_products': ['wheat_seeds', 'fertilizer_urea'],
            'is_organizer': True
        }
    ]
}
```

## Lambda Handler

### Event Structure

```python
{
    "action": "create_group" | "find_groups" | "join_group" | 
              "calculate_pricing" | "negotiate" | "get_details" | 
              "get_user_groups",
    
    # For create_group
    "organizer_id": "farmer_12345",
    "group_data": {...},
    
    # For find_groups
    "user_id": "farmer_67890",
    "requirements": {...},
    
    # For join_group
    "user_id": "farmer_67890",
    "group_id": "grp_abc123",
    "member_requirements": {...},
    
    # For calculate_pricing
    "group_id": "grp_abc123",
    "vendor_quotes": {...},  # optional
    
    # For negotiate
    "group_id": "grp_abc123",
    "vendor_list": [...],  # optional
    
    # For get_details
    "group_id": "grp_abc123",
    
    # For get_user_groups
    "user_id": "farmer_67890"
}
```

### Response Structure

```python
{
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
    },
    "body": "{...}"  # JSON string of result
}
```

## Usage Examples

### Example 1: Create a Buying Group

```python
from tools.buying_group_tools import create_buying_group_tools

buying_tools = create_buying_group_tools()

result = buying_tools.create_buying_group(
    organizer_id="farmer_12345",
    group_data={
        'group_name': 'Ludhiana Seed Buyers Cooperative',
        'target_products': ['wheat_seeds', 'fertilizer_urea'],
        'location': {
            'state': 'Punjab',
            'district': 'Ludhiana',
            'radius_km': 25
        },
        'max_members': 30,
        'min_members': 5
    }
)

print(f"Group created: {result['group_id']}")
```

### Example 2: Find and Join a Group

```python
# Find matching groups
result = buying_tools.find_matching_groups(
    user_id="farmer_67890",
    requirements={
        'products': ['wheat_seeds', 'fertilizer_urea'],
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
)

# Join the best match
if result['groups']:
    best_group = result['groups'][0]
    
    join_result = buying_tools.join_buying_group(
        user_id="farmer_67890",
        group_id=best_group['group_id'],
        member_requirements={
            'wheat_seeds': 150,
            'fertilizer_urea': 75
        }
    )
    
    print(f"Potential savings: ₹{sum(join_result['potential_savings'].values())}")
```

### Example 3: Calculate Bulk Pricing

```python
result = buying_tools.calculate_bulk_pricing(group_id="grp_abc123")

for product, pricing in result['pricing_breakdown'].items():
    print(f"{product}:")
    print(f"  Discount: {pricing['discount_percentage']}%")
    print(f"  Savings: ₹{pricing['total_savings']}")
```

## Streamlit UI

The `ui/buying_groups.py` module provides a complete user interface with:

1. **Find Groups Tab**: Search for matching buying groups
2. **Create Group Tab**: Form new cooperative buying groups
3. **My Groups Tab**: View and manage user's groups
4. **Pricing Calculator Tab**: Estimate savings from bulk buying

### Running the UI

```bash
streamlit run ui/buying_groups.py
```

## Testing

Run the unit tests:

```bash
pytest tests/test_buying_groups.py -v
```

Run the example:

```bash
python examples/buying_group_example.py
```

## Benefits

### For Farmers
- **Cost Savings**: 15-30% discounts on agricultural inputs
- **Bulk Access**: Access to bulk pricing typically unavailable to small farmers
- **Transparent Pricing**: Clear cost breakdown and equitable sharing
- **Reduced Risk**: Shared negotiation and vendor management
- **Community Building**: Strengthen farmer networks and cooperation

### For Communities
- **Economic Impact**: Keep more money in local farming communities
- **Collective Bargaining**: Increased negotiating power with suppliers
- **Knowledge Sharing**: Learn from other farmers' experiences
- **Resource Optimization**: Efficient use of transportation and logistics

### For the Agricultural Sector
- **Market Efficiency**: Better demand aggregation and forecasting
- **Supply Chain Optimization**: Reduced transaction costs
- **Farmer Empowerment**: Improved bargaining position for small farmers
- **Sustainability**: Reduced waste through coordinated purchasing

## Integration with RISE Platform

The buying groups system integrates with:

- **User Profiles**: Location and crop information for matching
- **Market Prices**: Real-time pricing data for savings calculations
- **Government Schemes**: Subsidies and support programs
- **Equipment Sharing**: Coordinated resource sharing
- **Farmer Forums**: Communication and coordination

## Future Enhancements

1. **Payment Integration**: Direct payment processing and escrow
2. **Delivery Tracking**: Real-time delivery status updates
3. **Quality Assurance**: Product quality verification and ratings
4. **Insurance**: Group insurance for bulk purchases
5. **Credit Facilities**: Group credit and financing options
6. **Mobile App**: Dedicated mobile application for group management
7. **Analytics Dashboard**: Insights on savings and group performance
8. **Multi-language Support**: Regional language interfaces

## Support

For issues or questions:
- Check the example code in `examples/buying_group_example.py`
- Review test cases in `tests/test_buying_groups.py`
- Consult the main RISE documentation

## License

Part of the RISE (Rural India Support Engine) platform.
