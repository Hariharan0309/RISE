# RISE Direct Buyer Connection System

## Overview

The Direct Buyer Connection System enables farmers to connect directly with verified buyers, eliminating middlemen and ensuring fair prices. The system provides intelligent buyer-farmer matching, quality standards, price benchmarks, and secure transaction facilitation.

## Features

### 1. Buyer Registration & Verification
- Register buyers with business details and verification documents
- Support for multiple buyer types: wholesalers, retailers, processors, exporters
- Verification status tracking
- Rating and review system

### 2. Crop Listing
- Create detailed crop listings with quality grades
- Upload images and certifications
- Specify quantity, expected price, and availability
- Location-based listing management

### 3. AI-Powered Buyer Matching
- Intelligent matching algorithm based on:
  - Crop interests
  - Location proximity (within 50-200km)
  - Quality requirements
  - Buyer ratings
  - Business type preferences
- Match score calculation (0-1 scale)
- Ranked buyer recommendations

### 4. Quality Standards & Benchmarks
- Comprehensive quality standards for major crops
- Grade classifications: Premium, Grade A, Grade B, Standard
- Quality parameters and testing criteria
- Premium grade requirements for higher prices

### 5. Price Benchmarks
- Real-time market price integration
- Fair price range calculation
- Negotiation guidelines
- Market average and range display

### 6. Transaction Facilitation
- Secure transaction initiation
- Payment terms negotiation
- Delivery coordination
- Transaction status tracking

## Architecture

### Components

```
buyer_connection_tools.py    # Core business logic and AWS integration
buyer_connection_lambda.py   # AWS Lambda handler for API requests
buyer_connection_dashboard.py # Streamlit UI components
test_buyer_connection.py     # Comprehensive test suite
buyer_connection_example.py  # Usage examples
```

### AWS Services Used

- **DynamoDB Tables:**
  - `RISE-Buyers`: Buyer profiles and verification
  - `RISE-CropListings`: Farmer crop listings
  - `RISE-Transactions`: Transaction records

- **Amazon Bedrock:** AI-powered matching and recommendations
- **AWS Lambda:** Serverless API processing
- **Amazon S3:** Image and document storage

## Installation

```bash
# Install dependencies
pip install boto3 streamlit

# Set up AWS credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
```

## Usage

### 1. Initialize Tools

```python
from tools.buyer_connection_tools import create_buyer_connection_tools

buyer_tools = create_buyer_connection_tools(region='us-east-1')
```

### 2. Register a Buyer

```python
buyer_data = {
    'business_name': 'Fresh Produce Traders',
    'contact_person': 'Rajesh Kumar',
    'phone_number': '+919876543210',
    'business_type': 'wholesaler',
    'location': {
        'state': 'Delhi',
        'district': 'Central Delhi',
        'latitude': 28.7041,
        'longitude': 77.1025
    },
    'crop_interests': ['wheat', 'rice', 'potato'],
    'payment_terms': 'advance_50_percent'
}

result = buyer_tools.register_buyer(buyer_data)
print(f"Buyer ID: {result['buyer_id']}")
```

### 3. Create a Crop Listing

```python
listing_data = {
    'crop_name': 'wheat',
    'quantity': 150,
    'unit': 'quintal',
    'quality_grade': 'grade_a',
    'expected_price': 2500,
    'harvest_date': '2024-04-15',
    'location': {
        'state': 'Uttar Pradesh',
        'district': 'Ghaziabad',
        'latitude': 28.6692,
        'longitude': 77.4538
    },
    'description': 'High quality wheat from organic farm'
}

result = buyer_tools.create_crop_listing('farmer_12345', listing_data)
print(f"Listing ID: {result['listing_id']}")
print(f"Potential Matches: {result['potential_matches']}")

# View matched buyers
for match in result['matches']:
    print(f"- {match['business_name']}: Score {match['match_score']}")
```

### 4. Get Quality Standards

```python
result = buyer_tools.get_quality_standards('wheat')

standards = result['standards']
print(f"Grades: {standards['grades']}")
print(f"Parameters: {standards['parameters']}")
```

### 5. Get Price Benchmarks

```python
location = {
    'state': 'Uttar Pradesh',
    'latitude': 28.6692,
    'longitude': 77.4538
}

result = buyer_tools.get_price_benchmarks('wheat', location)

print(f"Market Average: ₹{result['market_average']}/quintal")
print(f"Fair Range: ₹{result['fair_price_range']['min']} - ₹{result['fair_price_range']['max']}")
```

### 6. Initiate Transaction

```python
negotiation_data = {
    'agreed_price': 2550,
    'quantity': 150,
    'payment_terms': 'advance_50_percent',
    'delivery_date': '2024-04-25'
}

result = buyer_tools.initiate_transaction(
    listing_id='listing_abc123',
    buyer_id='buyer_xyz789',
    negotiation_data=negotiation_data
)

print(f"Transaction ID: {result['transaction_id']}")
print(f"Status: {result['status']}")
```

## Lambda Function Usage

### API Endpoints

The Lambda function supports the following actions:

#### 1. Register Buyer
```json
{
  "action": "register_buyer",
  "buyer_data": {
    "business_name": "Fresh Produce Traders",
    "contact_person": "Rajesh Kumar",
    "phone_number": "+919876543210",
    "business_type": "wholesaler",
    "location": {...},
    "crop_interests": ["wheat", "rice"]
  }
}
```

#### 2. Create Listing
```json
{
  "action": "create_listing",
  "farmer_id": "farmer_12345",
  "listing_data": {
    "crop_name": "wheat",
    "quantity": 150,
    "quality_grade": "grade_a",
    "expected_price": 2500,
    "location": {...}
  }
}
```

#### 3. Get Quality Standards
```json
{
  "action": "get_quality_standards",
  "crop_name": "wheat"
}
```

#### 4. Get Price Benchmarks
```json
{
  "action": "get_price_benchmarks",
  "crop_name": "wheat",
  "location": {
    "state": "Uttar Pradesh",
    "latitude": 28.6692,
    "longitude": 77.4538
  }
}
```

#### 5. Initiate Transaction
```json
{
  "action": "initiate_transaction",
  "listing_id": "listing_abc123",
  "buyer_id": "buyer_xyz789",
  "negotiation_data": {
    "agreed_price": 2550,
    "quantity": 150,
    "payment_terms": "advance_50_percent"
  }
}
```

## Streamlit Dashboard

Run the interactive dashboard:

```bash
streamlit run ui/buyer_connection_dashboard.py
```

### Dashboard Features

1. **List Your Crop Tab**
   - Create new crop listings
   - Specify quality, quantity, and price
   - View instant buyer matches

2. **View Matches Tab**
   - See all matched buyers
   - View match scores and ratings
   - Initiate transactions

3. **Price Benchmarks Tab**
   - Get current market prices
   - View fair price ranges
   - Visualize price data

4. **Quality Standards Tab**
   - View quality parameters
   - Understand grade requirements
   - Learn premium criteria

## Matching Algorithm

The buyer-farmer matching algorithm calculates scores based on:

### Scoring Components

1. **Crop Interest Match (30%)**
   - Buyer must be interested in the crop
   - Exact match required for score

2. **Location Proximity (25%)**
   - ≤50km: Full 25% score
   - 51-100km: 15% score
   - 101-200km: 5% score
   - >200km: 0% score

3. **Quality Requirements (20%)**
   - Listing quality meets buyer requirements
   - Grade matching validation

4. **Buyer Rating (15%)**
   - Based on buyer's average rating (0-5)
   - Higher ratings get better scores

5. **Business Type (10%)**
   - Preference order: Processor > Exporter > Wholesaler > Retailer
   - Encourages value-added partnerships

### Match Threshold

- Minimum match score: 0.5 (50%)
- Matches sorted by score and distance
- Top matches displayed to farmer

## Quality Standards

### Supported Crops

- Wheat
- Rice
- Tomato
- Potato
- Onion
- Sugarcane
- Cotton
- Maize

### Grade Classifications

1. **Premium**: Highest quality, 10-20% price premium
2. **Grade A**: High quality, standard market price
3. **Grade B**: Good quality, slight discount
4. **Standard**: Basic quality, lower price

### Quality Parameters

#### Wheat
- Moisture content: Max 12%
- Foreign matter: Max 2%
- Damaged grains: Max 3%
- Shriveled grains: Max 6%

#### Rice
- Moisture content: Max 14%
- Broken grains: Max 5%
- Foreign matter: Max 1%
- Chalky grains: Max 6%

#### Tomato
- Size: Min 50mm
- Color: Uniform red
- Firmness: Firm
- Defects: Max 5%

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/test_buyer_connection.py -v

# Run specific test
pytest tests/test_buyer_connection.py::TestBuyerConnectionTools::test_register_buyer -v

# Run with coverage
pytest tests/test_buyer_connection.py --cov=tools.buyer_connection_tools
```

### Test Coverage

- Buyer registration and validation
- Crop listing creation
- Buyer matching algorithm
- Quality standards retrieval
- Price benchmarks calculation
- Transaction initiation
- Distance calculation
- Match score calculation

## Examples

Run the example script:

```bash
python examples/buyer_connection_example.py
```

The example demonstrates:
1. Buyer registration
2. Crop listing creation
3. Quality standards retrieval
4. Price benchmarks
5. Transaction initiation
6. Multiple crop listings

## Best Practices

### For Farmers

1. **Accurate Information**: Provide accurate crop details and quality grades
2. **Quality Images**: Upload clear images of your crop
3. **Realistic Pricing**: Use price benchmarks for fair pricing
4. **Certifications**: Include organic or quality certifications
5. **Timely Updates**: Update availability and quantity regularly

### For Buyers

1. **Complete Profile**: Provide complete business information
2. **Verification**: Submit verification documents promptly
3. **Fair Terms**: Offer fair payment terms
4. **Ratings**: Maintain good ratings through reliable transactions
5. **Communication**: Respond quickly to farmer inquiries

## Security Considerations

1. **Data Encryption**: All data encrypted at rest and in transit
2. **Verification**: Buyer verification before matching
3. **Privacy**: Farmer contact details shared only after mutual agreement
4. **Secure Transactions**: Payment processing through secure channels
5. **Audit Logging**: All transactions logged for accountability

## Performance Optimization

1. **Caching**: Price data cached for 6 hours
2. **Efficient Queries**: DynamoDB GSI for fast lookups
3. **Batch Processing**: Bulk buyer matching
4. **Lazy Loading**: Load match details on demand
5. **CDN**: Static content served via CloudFront

## Troubleshooting

### Common Issues

1. **No Buyer Matches**
   - Check if buyers exist for your crop
   - Verify location coordinates
   - Adjust quality grade or price

2. **Price Benchmarks Not Loading**
   - Check internet connectivity
   - Verify location data
   - Try different crop name

3. **Transaction Failed**
   - Verify listing is still active
   - Check buyer verification status
   - Ensure all required fields provided

## Future Enhancements

1. **Payment Integration**: Integrate with payment gateways
2. **Logistics Coordination**: Partner with logistics providers
3. **Quality Inspection**: Third-party quality verification
4. **Contract Farming**: Long-term buyer-farmer contracts
5. **Mobile App**: Native mobile applications
6. **Blockchain**: Transparent transaction records
7. **Insurance**: Crop and transaction insurance

## Support

For issues or questions:
- Email: support@rise-farming.com
- Documentation: https://docs.rise-farming.com
- GitHub: https://github.com/rise-farming/buyer-connection

## License

Copyright © 2024 RISE - Rural Innovation and Sustainable Ecosystem
