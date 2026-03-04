# RISE Equipment Sharing Marketplace

## Overview

The Equipment Sharing Marketplace enables farmers to share or rent agricultural equipment with nearby farmers, reducing costs and maximizing equipment utilization. This system facilitates secure transactions, insurance verification, and usage tracking while building a collaborative farming community.

## Features

### 1. Equipment Listing
- List tractors, pumps, drones, harvesters, and other machinery
- Specify availability schedules and pricing (hourly/daily rates)
- Upload photos and detailed specifications
- Set pickup instructions and insurance details
- Calculate potential monthly income

### 2. Location-Based Search
- Find equipment within 25km radius (configurable up to 50km)
- Filter by equipment type
- Filter by availability dates
- Sort results by distance and rating
- View detailed equipment information

### 3. Equipment Booking
- Book equipment for specific time periods
- Automatic cost calculation (hourly/daily rates)
- Insurance verification (5% premium)
- Secure transaction processing
- Pickup instructions generation
- Usage tracking

### 4. Rating & Review System
- Rate equipment quality (1-5 stars)
- Rate owner service (1-5 stars)
- Write detailed reviews
- Average rating calculation
- Review history tracking

### 5. Proactive Alerts
- Unused equipment alerts (30-day threshold)
- Potential income notifications
- Availability reminders
- Booking confirmations

## Architecture

### DynamoDB Tables

#### RISE-ResourceSharing
```
Partition Key: resource_id
Sort Key: availability_date

Attributes:
- resource_id: String (PK)
- availability_date: String (SK)
- owner_user_id: String
- resource_type: String (tractor, pump, drone, harvester)
- equipment_details: Map
  - name: String
  - model: String
  - condition: String
  - hourly_rate: Number
  - daily_rate: Number
  - specifications: Map
  - year: String
  - capacity: String
- location: Map
  - state: String
  - district: String
  - address: String
  - latitude: Number
  - longitude: Number
- availability_status: String
- availability_calendar: Map
- booking_history: List
- ratings: Map
  - average: Number
  - count: Number
  - reviews: List
- photos: List
- insurance_details: Map
- pickup_instructions: String
- created_timestamp: Number
- updated_timestamp: Number
- last_used_timestamp: Number

Global Secondary Indexes:
- LocationResourceIndex: location + resource_type
- OwnerResourceIndex: owner_user_id + created_timestamp
```

#### RISE-ResourceBookings
```
Partition Key: booking_id

Attributes:
- booking_id: String (PK)
- resource_id: String
- renter_user_id: String
- owner_user_id: String
- booking_start: String (ISO datetime)
- booking_end: String (ISO datetime)
- total_cost: Number
- payment_status: String
- usage_tracking: Map
  - start_reading: Number
  - end_reading: Number
  - hours_used: Number
- insurance_details: Map
  - coverage_amount: Number
  - premium: Number
  - policy_number: String
  - verified: Boolean
- rating_given: Map
  - equipment_rating: Number
  - owner_rating: Number
  - review: String
  - timestamp: Number
- status: String
- delivery_status: String
- created_timestamp: Number
- updated_timestamp: Number

Global Secondary Indexes:
- RenterBookingIndex: renter_user_id + created_timestamp
- OwnerBookingIndex: owner_user_id + created_timestamp
- ResourceBookingIndex: resource_id + booking_start
```

## API Reference

### EquipmentSharingTools Class

#### `list_equipment(owner_id, equipment_data)`
List equipment for sharing.

**Parameters:**
- `owner_id` (str): Equipment owner's user ID
- `equipment_data` (dict): Equipment details
  - `name` (str): Equipment name
  - `type` (str): Equipment type (tractor, pump, drone, harvester)
  - `model` (str, optional): Model number
  - `condition` (str): Condition (excellent, good, fair)
  - `hourly_rate` (float): Hourly rental rate
  - `daily_rate` (float): Daily rental rate
  - `year` (str, optional): Year of purchase
  - `capacity` (str, optional): Capacity/power
  - `specifications` (dict, optional): Technical specifications
  - `location` (dict): Location details
    - `state` (str): State name
    - `district` (str): District name
    - `address` (str, optional): Full address
    - `latitude` (float): Latitude coordinate
    - `longitude` (float): Longitude coordinate
  - `photos` (list, optional): Photo URLs
  - `insurance_details` (dict, optional): Insurance information
  - `pickup_instructions` (str, optional): Pickup instructions

**Returns:**
```python
{
    'success': True,
    'resource_id': 'res_abc123',
    'status': 'listed_successfully',
    'estimated_monthly_income': 45000.0,
    'message': 'Equipment listed successfully. Potential monthly income: ₹45000'
}
```

#### `search_equipment(location, equipment_type=None, date_range=None, radius_km=25)`
Search for available equipment within radius.

**Parameters:**
- `location` (dict): Search location
  - `state` (str): State name
  - `district` (str): District name
  - `latitude` (float): Latitude coordinate
  - `longitude` (float): Longitude coordinate
- `equipment_type` (str, optional): Filter by type
- `date_range` (dict, optional): Availability filter
  - `start` (str): Start date (ISO format)
  - `end` (str): End date (ISO format)
- `radius_km` (int): Search radius in kilometers (default: 25)

**Returns:**
```python
{
    'success': True,
    'count': 5,
    'equipment': [
        {
            'resource_id': 'res_abc123',
            'owner_user_id': 'farmer_12345',
            'type': 'tractor',
            'name': 'John Deere Tractor',
            'model': '5075E',
            'condition': 'excellent',
            'hourly_rate': 500.0,
            'daily_rate': 3000.0,
            'specifications': {...},
            'location': {...},
            'distance_km': 12.5,
            'estimated_transport_cost': 25.0,
            'ratings': {'average': 4.5, 'count': 10},
            'photos': [...],
            'availability_status': 'available'
        },
        ...
    ],
    'search_params': {...}
}
```

#### `book_equipment(renter_id, resource_id, booking_details)`
Book equipment for specified period.

**Parameters:**
- `renter_id` (str): Renter's user ID
- `resource_id` (str): Equipment resource ID
- `booking_details` (dict): Booking information
  - `start_time` (str): Start datetime (ISO format)
  - `end_time` (str): End datetime (ISO format)
  - `notes` (str, optional): Additional notes

**Returns:**
```python
{
    'success': True,
    'booking_id': 'book_xyz789',
    'status': 'confirmed',
    'total_cost': 6000.0,
    'insurance_premium': 300.0,
    'payment_status': 'pending',
    'pickup_instructions': '...',
    'next_steps': [
        'Complete payment processing',
        'Verify insurance coverage',
        'Coordinate pickup with owner',
        'Inspect equipment before use'
    ]
}
```

#### `get_equipment_details(resource_id)`
Get detailed information about equipment.

**Parameters:**
- `resource_id` (str): Equipment resource ID

**Returns:**
```python
{
    'success': True,
    'resource_id': 'res_abc123',
    'equipment': {...},
    'pricing': {...},
    'location': {...},
    'availability_status': 'available',
    'availability_calendar': {...},
    'ratings': {...},
    'photos': [...],
    'insurance_details': {...},
    'pickup_instructions': '...',
    'total_bookings': 15,
    'owner_user_id': 'farmer_12345'
}
```

#### `rate_equipment(booking_id, rating_data)`
Rate equipment after use.

**Parameters:**
- `booking_id` (str): Booking ID
- `rating_data` (dict): Rating information
  - `equipment_rating` (int): Equipment rating (1-5)
  - `owner_rating` (int, optional): Owner rating (1-5)
  - `review` (str, optional): Review text

**Returns:**
```python
{
    'success': True,
    'message': 'Rating submitted successfully',
    'new_average_rating': 4.5,
    'total_ratings': 11
}
```

#### `send_unused_equipment_alerts(days_threshold=30)`
Send alerts for unused equipment.

**Parameters:**
- `days_threshold` (int): Days of inactivity threshold (default: 30)

**Returns:**
```python
{
    'success': True,
    'alerts_sent': 3,
    'message': 'Sent 3 unused equipment alerts'
}
```

## Lambda Handler

### Event Structure

```python
{
    "action": "list_equipment" | "search_equipment" | "book_equipment" | "get_details" | "rate_equipment" | "send_alerts",
    
    # For list_equipment
    "owner_id": "farmer_12345",
    "equipment_data": {...},
    
    # For search_equipment
    "location": {...},
    "equipment_type": "tractor",  # optional
    "date_range": {...},  # optional
    "radius_km": 25,  # optional
    
    # For book_equipment
    "renter_id": "farmer_67890",
    "resource_id": "res_abc123",
    "booking_details": {...},
    
    # For get_details
    "resource_id": "res_abc123",
    
    # For rate_equipment
    "booking_id": "book_xyz789",
    "rating_data": {...},
    
    # For send_alerts
    "days_threshold": 30  # optional
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

### Example 1: List Equipment

```python
from tools.equipment_sharing_tools import create_equipment_sharing_tools

equipment_tools = create_equipment_sharing_tools()

equipment_data = {
    'name': 'John Deere Tractor',
    'type': 'tractor',
    'model': '5075E',
    'condition': 'excellent',
    'hourly_rate': 500,
    'daily_rate': 3000,
    'location': {
        'state': 'Punjab',
        'district': 'Ludhiana',
        'latitude': 30.9010,
        'longitude': 75.8573
    }
}

result = equipment_tools.list_equipment('farmer_12345', equipment_data)
print(f"Resource ID: {result['resource_id']}")
print(f"Potential Income: ₹{result['estimated_monthly_income']}")
```

### Example 2: Search Equipment

```python
location = {
    'state': 'Punjab',
    'district': 'Jalandhar',
    'latitude': 31.3260,
    'longitude': 75.5762
}

result = equipment_tools.search_equipment(
    location,
    equipment_type='tractor',
    radius_km=50
)

print(f"Found {result['count']} tractors")
for equipment in result['equipment']:
    print(f"- {equipment['name']}: ₹{equipment['daily_rate']}/day, {equipment['distance_km']}km away")
```

### Example 3: Book Equipment

```python
from datetime import datetime, timedelta

booking_details = {
    'start_time': (datetime.now() + timedelta(days=1)).isoformat(),
    'end_time': (datetime.now() + timedelta(days=3)).isoformat(),
    'notes': 'Need for wheat harvesting'
}

result = equipment_tools.book_equipment(
    'farmer_67890',
    'res_abc123',
    booking_details
)

print(f"Booking ID: {result['booking_id']}")
print(f"Total Cost: ₹{result['total_cost']}")
print(f"Insurance: ₹{result['insurance_premium']}")
```

### Example 4: Rate Equipment

```python
rating_data = {
    'equipment_rating': 5,
    'owner_rating': 5,
    'review': 'Excellent tractor! Well-maintained and powerful.'
}

result = equipment_tools.rate_equipment('book_xyz789', rating_data)
print(f"New Average: {result['new_average_rating']}/5")
```

## Streamlit UI

The equipment marketplace includes a comprehensive Streamlit UI with four main tabs:

1. **Search Equipment**: Find and book equipment
2. **List Your Equipment**: Create equipment listings
3. **My Bookings**: View and manage bookings
4. **Rate & Review**: Rate equipment after use

### Running the UI

```bash
cd RISE
streamlit run ui/equipment_marketplace.py
```

## Testing

Run the test suite:

```bash
cd RISE
pytest tests/test_equipment_sharing.py -v
```

Run the example script:

```bash
cd RISE
python examples/equipment_sharing_example.py
```

## Key Benefits

### For Equipment Owners
- **Extra Income**: Earn ₹30,000-50,000/month from idle equipment
- **Maximized Utilization**: Reduce equipment idle time by 50%
- **Community Building**: Build reputation through ratings
- **Proactive Alerts**: Get notified about unused equipment

### For Renters
- **Cost Savings**: Save 60-70% compared to buying new equipment
- **Access to Quality Equipment**: Rent well-maintained machinery
- **Flexible Rental**: Hourly or daily rates
- **Verified Owners**: Rating and review system ensures quality

### For Community
- **Resource Optimization**: Better utilization of agricultural equipment
- **Reduced Capital Investment**: Lower barrier to entry for small farmers
- **Collaborative Economy**: Strengthen local farming community
- **Sustainable Practices**: Reduce equipment waste and redundancy

## Integration with RISE

The equipment sharing marketplace integrates seamlessly with other RISE features:

- **Voice Interface**: List and search equipment using voice commands
- **Translation**: Multilingual support for diverse farmers
- **Location Services**: GPS-based equipment discovery
- **Payment Integration**: Secure transaction processing
- **Notification System**: Real-time alerts and updates

## Future Enhancements

1. **IoT Integration**: Real-time equipment tracking and usage monitoring
2. **Smart Contracts**: Blockchain-based secure transactions
3. **Predictive Analytics**: Demand forecasting for equipment
4. **Maintenance Tracking**: Equipment service history and reminders
5. **Group Bookings**: Cooperative equipment sharing for large projects
6. **Insurance Marketplace**: Integrated insurance options
7. **Equipment Financing**: Loan options for equipment purchase

## Support

For issues or questions:
- Check the example scripts in `examples/equipment_sharing_example.py`
- Review test cases in `tests/test_equipment_sharing.py`
- Refer to the main RISE documentation

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) project.


## Booking Management Features

### Payment Processing

Process secure payments for equipment bookings:

```python
from tools.equipment_sharing_tools import create_equipment_sharing_tools

equipment_tools = create_equipment_sharing_tools()

# Process payment
payment_details = {
    'amount': 6000.00,
    'payment_method': 'upi',  # upi, card, netbanking, wallet
    'reference': 'UPI123456789'
}

result = equipment_tools.process_payment('book_abc12345', payment_details)

if result['success']:
    print(f"Transaction ID: {result['transaction_id']}")
    print(f"Payment Status: {result['payment_status']}")
    print(f"Amount Paid: ₹{result['amount_paid']:.2f}")
```

**Features:**
- Secure transaction processing
- Multiple payment methods (UPI, Card, Net Banking, Wallet)
- Amount verification
- Transaction ID generation
- Payment reference tracking

### Usage Tracking

Track equipment usage with meter readings:

```python
# Record start of usage
start_usage = {
    'start_reading': 1000,
    'actual_start_time': '2024-01-15T08:00:00'
}

result = equipment_tools.update_usage_tracking('book_abc12345', start_usage)

# Record end of usage
end_usage = {
    'end_reading': 1048,
    'actual_end_time': '2024-01-17T18:00:00'
}

result = equipment_tools.update_usage_tracking('book_abc12345', end_usage)

if result['success']:
    print(f"Hours Used: {result['usage_tracking']['hours_used']:.1f}")
```

**Features:**
- Start and end meter readings
- Actual usage time tracking
- Automatic hours calculation
- Delivery status updates

### Get Booking Details

Retrieve comprehensive booking information:

```python
result = equipment_tools.get_booking_details('book_abc12345')

if result['success']:
    booking = result['booking']
    equipment = result['equipment']
    
    print(f"Equipment: {equipment['name']}")
    print(f"Status: {booking['status']}")
    print(f"Total Cost: ₹{booking['total_cost']:.2f}")
    print(f"Insurance: ₹{booking['insurance_premium']:.2f}")
    print(f"Payment Status: {booking['payment_status']}")
```

**Returns:**
- Complete booking information
- Equipment details
- Cost breakdown
- Payment details
- Usage tracking data
- Insurance information

### Get User Bookings

Retrieve all bookings for a user:

```python
# Get bookings as renter
result = equipment_tools.get_user_bookings('farmer_12345', 'renter')

if result['success']:
    print(f"Total Bookings: {result['count']}")
    
    for booking in result['bookings']:
        print(f"- {booking['equipment_name']}: {booking['status']}")
        print(f"  Cost: ₹{booking['final_amount']:.2f}")

# Get bookings as equipment owner
owner_result = equipment_tools.get_user_bookings('farmer_12345', 'owner')
```

**Features:**
- View bookings as renter or owner
- Sorted by creation date (newest first)
- Includes equipment details
- Shows payment and delivery status

### Cancel Booking

Cancel bookings with automatic refund calculation:

```python
result = equipment_tools.cancel_booking(
    'book_abc12345',
    'Plans changed due to weather'
)

if result['success']:
    print(f"Status: {result['status']}")
    print(f"Refund Amount: ₹{result['refund_amount']:.2f}")
```

**Cancellation Policy:**
- **24+ hours before start:** Full refund
- **12-24 hours before start:** 50% refund
- **Less than 12 hours:** No refund
- Cannot cancel completed or already cancelled bookings

## Insurance Verification

All bookings include automatic insurance:

- **Coverage Amount:** 2x equipment cost
- **Premium:** 5% of equipment cost
- **Policy Number:** Auto-generated (INS_bookingid)
- **Verification:** Automatic verification on booking
- **Tracking:** Verification timestamp recorded

## Cost Calculator

Booking costs are automatically calculated:

```python
# Hourly rate for partial days
# Daily rate for full days
# Insurance premium (5% of cost)
# Transport cost (optional)
# Final amount = Equipment + Insurance + Transport
```

**Example:**
- Equipment: 2 days × ₹3000 = ₹6000
- Insurance: 5% = ₹300
- Transport: ₹100
- **Final Amount: ₹6400**

## Pickup Instructions

Automatically generated for each booking:

```
Equipment Pickup Instructions:

Equipment: John Deere Tractor (5075E)
Location: Village Khanna, Ludhiana, Punjab

Pickup Details:
1. Contact owner before pickup
2. Inspect equipment condition
3. Verify insurance coverage
4. Take photos before use
5. Follow safety guidelines

Contact owner 1 day before pickup.
Equipment available 8 AM - 6 PM.
Fuel not included in rental.
```

## Booking Management UI

Use the Streamlit UI for comprehensive booking management:

```bash
streamlit run ui/equipment_booking.py
```

**Features:**
- View all bookings (as renter or owner)
- Process payments with multiple methods
- Track equipment usage
- View detailed booking information
- Cancel bookings with refund calculation
- Filter bookings by status
- Real-time status updates

## API Integration

### Lambda Function

The equipment sharing Lambda supports all booking operations:

```python
# Process payment
event = {
    'action': 'process_payment',
    'booking_id': 'book_abc12345',
    'payment_details': {
        'amount': 6000.00,
        'payment_method': 'upi',
        'reference': 'UPI123456789'
    }
}

# Update usage
event = {
    'action': 'update_usage',
    'booking_id': 'book_abc12345',
    'usage_data': {
        'start_reading': 1000,
        'actual_start_time': '2024-01-15T08:00:00'
    }
}

# Get booking details
event = {
    'action': 'get_booking',
    'booking_id': 'book_abc12345'
}

# Get user bookings
event = {
    'action': 'get_user_bookings',
    'user_id': 'farmer_12345',
    'booking_type': 'renter'  # or 'owner'
}

# Cancel booking
event = {
    'action': 'cancel_booking',
    'booking_id': 'book_abc12345',
    'cancellation_reason': 'Plans changed'
}
```

## Testing

Run comprehensive tests:

```bash
pytest tests/test_equipment_sharing.py -v
```

**Test Coverage:**
- Payment processing
- Usage tracking
- Booking details retrieval
- User bookings
- Booking cancellation
- Refund calculation
- Insurance verification
- Cost calculation with transport

## Security Features

- **Payment Verification:** Amount validation before processing
- **Transaction IDs:** Unique, secure transaction identifiers
- **Insurance Tracking:** Automatic verification and policy generation
- **Usage Validation:** Meter reading validation
- **Cancellation Policy:** Automated refund calculation
- **Status Management:** Prevents invalid state transitions

## Best Practices

1. **Always verify payment amount** before processing
2. **Record usage readings** at start and end
3. **Check cancellation policy** before cancelling
4. **Verify insurance coverage** before equipment use
5. **Keep transaction references** for tracking
6. **Update delivery status** as equipment moves
7. **Provide clear pickup instructions** to renters
8. **Track actual usage times** for accurate billing

## Troubleshooting

### Payment Amount Mismatch
```python
# Ensure payment amount matches booking final_amount
booking_details = equipment_tools.get_booking_details(booking_id)
correct_amount = booking_details['booking']['final_amount']
```

### Cannot Cancel Booking
```python
# Check booking status - only confirmed/paid bookings can be cancelled
# Completed or already cancelled bookings cannot be cancelled
```

### Usage Tracking Not Updating
```python
# Ensure booking is in paid status before tracking usage
# Provide both start_reading and end_reading for hours calculation
```

## Support

For issues or questions:
- Check the examples in `examples/equipment_sharing_example.py`
- Review test cases in `tests/test_equipment_sharing.py`
- Refer to the design document in `.kiro/specs/rise-farming-assistant/design.md`

## Future Enhancements

- Real-time GPS tracking
- Automated damage assessment
- Dynamic pricing based on demand
- Equipment maintenance scheduling
- Multi-currency support
- Escrow payment system
- Dispute resolution workflow
