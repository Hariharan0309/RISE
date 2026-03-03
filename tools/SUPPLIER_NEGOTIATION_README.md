# RISE AI-Powered Supplier Negotiation System

## Overview

The AI-Powered Supplier Negotiation system enables farmers and buying groups to efficiently negotiate with agricultural input suppliers, compare quotes, verify quality, and manage orders. The system uses Amazon Bedrock AI to generate professional negotiation messages and provide intelligent quote analysis.

## Features

### 1. Supplier Database Management
- Register and verify suppliers
- Maintain supplier profiles with certifications
- Track supplier ratings and reviews
- Manage product catalogs and pricing tiers
- Define delivery areas and payment terms

### 2. Intelligent Supplier Matching
- Find suppliers based on product requirements
- Location-based supplier search
- Match score calculation considering:
  - Product availability (40%)
  - Location proximity (30%)
  - Supplier ratings (20%)
  - Certifications (10%)
- Minimum order quantity verification
- Bulk discount availability checking

### 3. AI-Powered Bulk Pricing Requests
- Generate professional negotiation messages using Amazon Bedrock
- Bilingual support (Hindi and English)
- Include specific product requirements and quantities
- Request bulk pricing with 15-30% discount targets
- Specify quality assurance requirements
- Define delivery and payment terms

### 4. Quote Management
- Receive and store supplier quotes
- Track quote submission status
- Manage quote validity periods
- Store detailed pricing breakdowns

### 5. AI-Powered Quote Comparison
- Intelligent quote analysis using Amazon Bedrock
- Multi-criteria evaluation:
  - Total cost and discount percentage (40%)
  - Quality certifications (25%)
  - Delivery timeline (20%)
  - Payment terms (10%)
  - Supplier reputation (5%)
- Automated ranking of quotes
- Detailed pros/cons analysis
- Clear recommendations with reasoning

### 6. Quality Assurance Verification
- Verify supplier certifications
- Check compliance with industry standards
- Product-specific quality requirements
- Certification validation:
  - Seeds: Seed Certification, Quality Assurance, Phytosanitary Certificate
  - Fertilizers: FCO License, Quality Certification, ISO 9001
  - Pesticides: CIB Registration, Quality Certification, Safety Standards
  - Equipment: Quality Certification, Warranty, Safety Standards
- Compliance score calculation

### 7. Delivery Coordination
- Schedule deliveries with suppliers
- Generate tracking numbers
- Manage delivery contacts and instructions
- Track delivery status
- Coordinate rural location deliveries

### 8. Payment Management
- Setup payment terms and methods
- Manage group payment collection
- Track member contributions
- Handle payment distribution
- Support multiple payment methods:
  - Bank transfer
  - UPI
  - Cash on delivery
  - Cheque
- Flexible payment terms:
  - Full payment on delivery
  - Advance payment options
  - Credit terms

## Architecture

### AWS Services Used

1. **Amazon DynamoDB**
   - RISE-Suppliers: Supplier database
   - RISE-Negotiations: Negotiation tracking
   - RISE-SupplierQuotes: Quote storage

2. **Amazon Bedrock**
   - Claude 3 Haiku model for AI generation
   - Negotiation message generation
   - Quote analysis and recommendations

3. **Amazon SNS**
   - Notification delivery
   - Status updates

### DynamoDB Schema

#### RISE-Suppliers Table
```
{
  supplier_id: String (PK),
  business_name: String,
  contact_person: String,
  phone_number: String,
  email: String,
  supplier_type: String,
  location: Map,
  products_offered: List,
  certifications: List,
  quality_standards: Map,
  delivery_areas: List,
  payment_terms: List,
  minimum_order_quantity: Map,
  bulk_discount_tiers: Map,
  ratings: Map,
  verification_status: String,
  active: Boolean,
  created_timestamp: Number,
  updated_timestamp: Number
}
```

#### RISE-Negotiations Table
```
{
  negotiation_id: String (PK),
  buyer_id: String,
  product_requirements: Map,
  supplier_ids: List,
  delivery_location: Map,
  request_message: String,
  status: String,
  quotes_received: List,
  selected_quote_id: String,
  delivery_id: String,
  payment_id: String,
  created_timestamp: Number,
  updated_timestamp: Number,
  deadline: String
}
```

#### RISE-SupplierQuotes Table
```
{
  quote_id: String (PK),
  negotiation_id: String,
  supplier_id: String,
  product_pricing: Map,
  discount_percentage: Number,
  total_amount: Number,
  payment_terms: String,
  delivery_timeline: String,
  quality_certifications: List,
  warranty_terms: String,
  valid_until: String,
  status: String,
  created_timestamp: Number
}
```

## API Reference

### SupplierNegotiationTools Class

#### `register_supplier(supplier_data: Dict) -> Dict`
Register a new supplier in the database.

**Parameters:**
- `supplier_data`: Supplier information including:
  - `business_name`: Company name
  - `contact_person`: Contact person name
  - `phone_number`: Contact phone
  - `email`: Contact email (optional)
  - `supplier_type`: Type (seeds, fertilizers, pesticides, equipment)
  - `location`: Location details with state, district, coordinates
  - `products_offered`: List of products
  - `certifications`: List of certifications
  - `quality_standards`: Quality standards by product
  - `delivery_areas`: List of delivery areas
  - `payment_terms`: Available payment terms
  - `minimum_order_quantity`: MOQ by product
  - `bulk_discount_tiers`: Discount tiers

**Returns:**
```python
{
  'success': True,
  'supplier_id': 'sup_12345678',
  'verification_status': 'pending',
  'message': 'Supplier registered successfully'
}
```

#### `find_suppliers(product_requirements: Dict, location: Dict) -> Dict`
Find suppliers matching product requirements and location.

**Parameters:**
- `product_requirements`: Dict of product -> quantity
- `location`: Location with state and district

**Returns:**
```python
{
  'success': True,
  'count': 5,
  'suppliers': [
    {
      'supplier_id': 'sup_12345678',
      'business_name': 'Punjab Agro',
      'supplier_type': 'seeds',
      'matching_products': ['wheat_seeds', 'fertilizer_urea'],
      'match_score': 0.85,
      'meets_moq': True,
      'bulk_discount_available': True,
      'ratings': {'average': 4.5, 'count': 10},
      'certifications': ['ISO 9001', 'Quality Assurance'],
      'payment_terms': ['on_delivery', 'advance_50']
    }
  ]
}
```

#### `generate_bulk_pricing_request(buyer_id: str, product_requirements: Dict, supplier_ids: List, delivery_location: Dict) -> Dict`
Generate AI-powered bulk pricing request.

**Parameters:**
- `buyer_id`: Buyer or group ID
- `product_requirements`: Products and quantities needed
- `supplier_ids`: List of supplier IDs to contact
- `delivery_location`: Delivery location details

**Returns:**
```python
{
  'success': True,
  'negotiation_id': 'neg_12345678',
  'request_message': 'AI-generated professional message...',
  'suppliers_contacted': 3,
  'status': 'pending_quotes',
  'deadline': '2024-01-31T00:00:00',
  'next_steps': [...]
}
```

#### `submit_supplier_quote(negotiation_id: str, supplier_id: str, quote_data: Dict) -> Dict`
Submit a supplier quote for a negotiation.

**Parameters:**
- `negotiation_id`: Negotiation ID
- `supplier_id`: Supplier ID
- `quote_data`: Quote details including:
  - `product_pricing`: Price per unit by product
  - `discount_percentage`: Discount offered
  - `total_amount`: Total quote amount
  - `payment_terms`: Payment terms
  - `delivery_timeline`: Delivery timeline
  - `quality_certifications`: List of certifications
  - `warranty_terms`: Warranty details

**Returns:**
```python
{
  'success': True,
  'quote_id': 'quote_12345678',
  'negotiation_id': 'neg_12345678',
  'status': 'submitted',
  'quotes_received': 2,
  'total_suppliers': 3
}
```

#### `compare_quotes(negotiation_id: str) -> Dict`
Compare all quotes using AI analysis.

**Parameters:**
- `negotiation_id`: Negotiation ID

**Returns:**
```python
{
  'success': True,
  'negotiation_id': 'neg_12345678',
  'quotes_count': 3,
  'quotes': [...],
  'ranked_quotes': [...],
  'ai_analysis': 'Detailed AI analysis...',
  'recommended_quote': {...},
  'best_price': 29100,
  'best_discount': 25,
  'average_price': 30000
}
```

#### `verify_quality_assurance(supplier_id: str, product_name: str) -> Dict`
Verify supplier's quality assurance and certifications.

**Parameters:**
- `supplier_id`: Supplier ID
- `product_name`: Product to verify

**Returns:**
```python
{
  'success': True,
  'supplier_id': 'sup_12345678',
  'supplier_name': 'Punjab Agro',
  'product_name': 'wheat_seeds',
  'certifications': ['ISO 9001', 'Seed Certification'],
  'verification_checks': [
    {
      'certification': 'Seed Certification',
      'required': True,
      'verified': True,
      'status': 'pass'
    }
  ],
  'overall_status': 'verified',
  'compliance_score': 100.0
}
```

#### `coordinate_delivery(negotiation_id: str, selected_quote_id: str, delivery_details: Dict) -> Dict`
Coordinate delivery logistics.

**Parameters:**
- `negotiation_id`: Negotiation ID
- `selected_quote_id`: Selected quote ID
- `delivery_details`: Delivery details including:
  - `delivery_date`: Delivery date
  - `delivery_time_slot`: Time slot
  - `delivery_contact`: Contact information
  - `special_instructions`: Special instructions

**Returns:**
```python
{
  'success': True,
  'delivery_id': 'del_12345678',
  'tracking_number': 'TRK123456789ABC',
  'delivery_date': '2024-01-15',
  'delivery_status': 'scheduled',
  'next_steps': [...]
}
```

#### `manage_payment(negotiation_id: str, payment_data: Dict) -> Dict`
Manage payment collection and distribution.

**Parameters:**
- `negotiation_id`: Negotiation ID
- `payment_data`: Payment details including:
  - `payment_method`: Payment method
  - `payment_schedule`: Payment schedule (optional)
  - `member_contributions`: Member contributions for group purchases

**Returns:**
```python
{
  'success': True,
  'payment_id': 'pay_12345678',
  'total_amount': 30000,
  'payment_status': 'pending',
  'payment_method': 'bank_transfer',
  'payment_terms': 'advance_50',
  'member_count': 5,
  'next_steps': [...]
}
```

#### `get_negotiation_status(negotiation_id: str) -> Dict`
Get detailed status of a negotiation.

**Parameters:**
- `negotiation_id`: Negotiation ID

**Returns:**
```python
{
  'success': True,
  'negotiation_id': 'neg_12345678',
  'buyer_id': 'buyer_12345',
  'status': 'delivery_scheduled',
  'product_requirements': {...},
  'suppliers_contacted': 3,
  'quotes_received': 3,
  'selected_quote_id': 'quote_12345678',
  'delivery_id': 'del_12345678',
  'payment_id': 'pay_12345678',
  'deadline': '2024-01-31'
}
```

## Lambda Handler

### Event Structure

```python
{
  "body": {
    "operation": "find_suppliers",  # Operation name
    "product_requirements": {...},   # Operation-specific parameters
    "location": {...}
  }
}
```

### Supported Operations

1. `register_supplier` - Register new supplier
2. `find_suppliers` - Search for suppliers
3. `generate_request` - Generate pricing request
4. `submit_quote` - Submit supplier quote
5. `compare_quotes` - Compare all quotes
6. `verify_quality` - Verify quality assurance
7. `coordinate_delivery` - Coordinate delivery
8. `manage_payment` - Manage payment
9. `get_status` - Get negotiation status

## Usage Examples

### Example 1: Find Suppliers and Generate Request

```python
from tools.supplier_negotiation_tools import create_supplier_negotiation_tools

# Initialize tools
tools = create_supplier_negotiation_tools()

# Find suppliers
result = tools.find_suppliers(
    product_requirements={
        'wheat_seeds': 500,
        'fertilizer_urea': 300
    },
    location={
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
)

# Select top suppliers
supplier_ids = [s['supplier_id'] for s in result['suppliers'][:3]]

# Generate AI-powered request
request = tools.generate_bulk_pricing_request(
    buyer_id="buyer_12345",
    product_requirements={
        'wheat_seeds': 500,
        'fertilizer_urea': 300
    },
    supplier_ids=supplier_ids,
    delivery_location={
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
)

print(f"Negotiation ID: {request['negotiation_id']}")
print(f"Request Message:\n{request['request_message']}")
```

### Example 2: Compare Quotes and Select Supplier

```python
# Compare quotes
comparison = tools.compare_quotes(negotiation_id)

print(f"Best Price: ₹{comparison['best_price']}")
print(f"Best Discount: {comparison['best_discount']}%")
print(f"\nAI Analysis:\n{comparison['ai_analysis']}")

# Get recommended quote
recommended = comparison['recommended_quote']
print(f"\nRecommended: {recommended['supplier_name']}")
print(f"Total: ₹{recommended['total_amount']}")
```

### Example 3: Complete Order Workflow

```python
# Verify quality
quality = tools.verify_quality_assurance(
    supplier_id=recommended['supplier_id'],
    product_name='wheat_seeds'
)

print(f"Quality Status: {quality['overall_status']}")
print(f"Compliance Score: {quality['compliance_score']}%")

# Coordinate delivery
delivery = tools.coordinate_delivery(
    negotiation_id=negotiation_id,
    selected_quote_id=recommended['quote_id'],
    delivery_details={
        'delivery_date': '2024-01-15',
        'delivery_time_slot': 'Morning (8AM-12PM)',
        'delivery_contact': {
            'name': 'Harpreet Singh',
            'phone': '+91-9876543210'
        }
    }
)

print(f"Tracking Number: {delivery['tracking_number']}")

# Setup payment
payment = tools.manage_payment(
    negotiation_id=negotiation_id,
    payment_data={
        'payment_method': 'bank_transfer',
        'member_contributions': {
            'farmer_001': 6000,
            'farmer_002': 6000,
            'farmer_003': 6000,
            'farmer_004': 6000,
            'farmer_005': 6000
        }
    }
)

print(f"Payment ID: {payment['payment_id']}")
print(f"Total Amount: ₹{payment['total_amount']}")
```

## Streamlit UI

The system includes a comprehensive Streamlit interface with 5 tabs:

### 1. Find Suppliers Tab
- Search for suppliers by product and location
- View match scores and supplier details
- Select suppliers for negotiation
- View certifications and ratings

### 2. Generate Request Tab
- Create bulk pricing requests
- AI-generated professional messages
- Bilingual support (Hindi/English)
- Download request messages

### 3. Compare Quotes Tab
- View all received quotes
- AI-powered analysis and ranking
- Detailed comparison metrics
- Select best supplier

### 4. Quality Verification Tab
- Verify supplier certifications
- Check compliance scores
- View quality standards
- Validate product-specific requirements

### 5. Manage Orders Tab
- Schedule deliveries
- Track shipments
- Manage group payments
- Collect member contributions

## Testing

Run the test suite:

```bash
pytest tests/test_supplier_negotiation.py -v
```

Test coverage includes:
- Supplier registration
- Supplier search and matching
- Bulk pricing request generation
- Quote submission and comparison
- Quality verification
- Delivery coordination
- Payment management
- Error handling

## Benefits

### For Farmers
- **Cost Savings**: Achieve 15-30% discounts through bulk purchasing
- **Time Savings**: AI-generated professional negotiation messages
- **Quality Assurance**: Verified suppliers with certifications
- **Transparent Pricing**: Clear quote comparison and analysis
- **Flexible Payment**: Multiple payment options and terms
- **Reliable Delivery**: Coordinated logistics to rural areas

### For Buying Groups
- **Collective Bargaining**: Leverage group purchasing power
- **Fair Distribution**: Transparent cost sharing among members
- **Payment Management**: Automated collection and distribution
- **Group Coordination**: Centralized order management

### For Suppliers
- **Market Access**: Reach more farmers and buying groups
- **Bulk Orders**: Larger order volumes
- **Efficient Communication**: Standardized quote submission
- **Quality Recognition**: Showcase certifications and standards

## Integration Points

The supplier negotiation system integrates with:
- **Buying Groups** (Task 32): Leverage group purchasing power
- **Market Intelligence** (Task 18): Price benchmarking
- **Buyer Connections** (Task 20): Supplier-buyer matching
- **User Profiles**: Location and preference data
- **Payment Systems**: Payment processing integration

## Future Enhancements

1. **Advanced Analytics**
   - Supplier performance tracking
   - Price trend analysis
   - Savings reports

2. **Mobile Integration**
   - Mobile app for suppliers
   - SMS notifications
   - WhatsApp integration

3. **Automated Matching**
   - ML-based supplier recommendations
   - Predictive pricing
   - Demand forecasting

4. **Quality Tracking**
   - Post-delivery quality ratings
   - Complaint management
   - Supplier scorecards

5. **Financial Services**
   - Integrated payment gateway
   - Credit facilities
   - Insurance options

## Conclusion

The AI-Powered Supplier Negotiation system transforms how farmers interact with agricultural input suppliers, providing professional negotiation tools, intelligent quote analysis, and comprehensive order management. By leveraging Amazon Bedrock AI, the system helps farmers achieve better prices, ensure quality, and manage complex procurement processes efficiently.

