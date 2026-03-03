# RISE Scheme Discovery Tools

## Overview

The Scheme Discovery Tools provide intelligent government scheme discovery, eligibility checking, and personalized recommendations for farmers. Using Amazon Bedrock AI and Amazon Q, these tools analyze farmer profiles to identify applicable schemes and prioritize them by benefit amount and deadline urgency.

## Features

### 1. Farmer Profile Analysis
- AI-powered profile analysis using Amazon Bedrock
- Automatic farmer category determination (marginal/small/medium/large)
- Identification of relevant scheme categories
- Profile completeness scoring
- Needs assessment and priority area identification

### 2. Eligibility Checking
- Comprehensive eligibility verification
- Multi-criteria evaluation (land size, ownership, state, farmer type)
- Confidence scoring for eligibility determination
- Required documents list generation
- Missing requirements identification
- Next steps guidance

### 3. Scheme Recommendations
- Personalized scheme recommendations based on profile
- Multi-source scheme aggregation (central + state)
- Benefit amount estimation
- Priority-based ranking
- Deadline awareness

### 4. Benefit Calculation
- Accurate benefit amount estimation
- Category-specific calculations (subsidies, loans, insurance, equipment)
- Recurring vs one-time benefit identification
- 5-year total benefit projection
- Land size and farmer category adjustments

### 5. Scheme Prioritization
- Multi-factor priority scoring (0-100 scale)
- Benefit amount weighting (0-40 points)
- Deadline urgency factor (0-30 points)
- Eligibility confidence factor (0-20 points)
- Document availability factor (0-10 points)
- Automatic sorting by priority

## Architecture

### AWS Services Used

1. **Amazon Bedrock (Claude 3 Sonnet)**
   - Farmer profile analysis
   - Scheme category identification
   - Needs assessment

2. **Amazon DynamoDB**
   - Government schemes storage (RISE-GovernmentSchemes table)
   - User profiles storage (RISE-UserProfiles table)
   - Fast querying with GSIs

3. **AWS Lambda**
   - Serverless execution
   - API Gateway integration
   - Event-driven processing

## Installation

```bash
# Install dependencies
pip install boto3 pytest

# Set up AWS credentials
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

## Usage

### Basic Usage

```python
from scheme_discovery_tools import SchemeDiscoveryTools

# Initialize tools
tools = SchemeDiscoveryTools(region='us-east-1')

# Create farmer profile
farmer_profile = {
    'name': 'Ravi Kumar',
    'location': {
        'state': 'uttar pradesh',
        'district': 'lucknow'
    },
    'farm_details': {
        'land_size': 2.0,
        'soil_type': 'loamy',
        'crops': ['wheat', 'rice'],
        'farming_experience': '10 years',
        'land_ownership': True
    },
    'annual_income': 150000
}

# Get scheme recommendations
result = tools.recommend_schemes(farmer_profile)

if result['success']:
    print(f"Found {result['count']} applicable schemes")
    for scheme in result['schemes']:
        print(f"- {scheme['scheme_name']}: ₹{scheme['estimated_benefit']:,.0f}")
```

### Profile Analysis

```python
# Analyze farmer profile
result = tools.analyze_farmer_profile(farmer_profile)

if result['success']:
    analysis = result['analysis']
    print(f"Farmer Category: {result['profile_summary']['farmer_category']}")
    print(f"Relevant Categories: {analysis['relevant_categories']}")
    print(f"Identified Needs: {analysis['farmer_needs']}")
```

### Eligibility Checking

```python
# Check eligibility for specific scheme
result = tools.check_eligibility(farmer_profile, 'SCH_PMKISAN001')

if result['success']:
    if result['eligible']:
        print(f"✅ Eligible for {result['scheme_name']}")
        print(f"Confidence: {result['confidence_score']*100:.0f}%")
        print(f"Required Documents: {result['required_documents']}")
    else:
        print(f"❌ Not eligible: {result['reasons']}")
```

### Benefit Calculation

```python
# Calculate benefit amount
result = tools.calculate_benefit_amount(farmer_profile, 'SCH_PMKISAN001')

if result['success']:
    print(f"Base Benefit: ₹{result['base_benefit']:,.0f}")
    print(f"Estimated Benefit: ₹{result['estimated_benefit']:,.0f}")
    print(f"5-Year Total: ₹{result['total_5year_benefit']:,.0f}")
```

### Scheme Prioritization

```python
# Prioritize schemes
result = tools.prioritize_schemes(schemes_list)

if result['success']:
    for scheme in result['schemes']:
        print(f"{scheme['scheme_name']}: {scheme['priority_score']:.1f}/100")
```

## Tool Functions for Agent Integration

```python
from scheme_discovery_tools import (
    recommend_schemes_tool,
    check_eligibility_tool
)

# Use in agent workflows
recommendations = recommend_schemes_tool(farmer_profile)
eligibility = check_eligibility_tool(farmer_profile, scheme_id)
```

## Lambda Handler

The Lambda function supports multiple actions:

```python
# Analyze profile
event = {
    'action': 'analyze_profile',
    'farmer_profile': {...}
}

# Check eligibility
event = {
    'action': 'check_eligibility',
    'farmer_profile': {...},
    'scheme_id': 'SCH_PMKISAN001'
}

# Recommend schemes
event = {
    'action': 'recommend_schemes',
    'farmer_profile': {...}
}

# Calculate benefits
event = {
    'action': 'calculate_benefits',
    'farmer_profile': {...},
    'scheme_id': 'SCH_PMKISAN001'
}

# Prioritize schemes
event = {
    'action': 'prioritize_schemes',
    'schemes': [...]
}
```

## Priority Scoring System

Schemes are prioritized using a 100-point scale:

- **Benefit Amount (0-40 points)**: Higher benefits score higher
- **Deadline Urgency (0-30 points)**:
  - ≤30 days: 30 points (Very urgent)
  - ≤90 days: 20 points (Urgent)
  - ≤180 days: 10 points (Moderate)
  - >180 days: 5 points (Low urgency)
  - No deadline: 15 points (Ongoing)
- **Eligibility Confidence (0-20 points)**: Based on profile completeness
- **Document Availability (0-10 points)**:
  - ≤3 documents: 10 points
  - ≤5 documents: 7 points
  - >5 documents: 4 points

Priority Levels:
- **High**: Score ≥ 80
- **Medium**: Score 50-79
- **Low**: Score < 50

## Farmer Categories

Based on land size:
- **Marginal**: ≤ 1.0 acres
- **Small**: 1.0 - 2.0 acres
- **Medium**: 2.0 - 10.0 acres
- **Large**: > 10.0 acres

## Scheme Categories

Supported categories:
- `crop_insurance`: Insurance schemes for crop protection
- `subsidies`: Direct financial subsidies and support
- `loans`: Agricultural loans and credit facilities
- `equipment`: Equipment purchase subsidies
- `irrigation`: Irrigation infrastructure support
- `organic_farming`: Organic farming promotion schemes
- `training`: Training and skill development programs
- `market_access`: Market linkage and access programs
- `soil_health`: Soil health management schemes
- `seeds`: Seed distribution and quality programs

## Testing

```bash
# Run tests
pytest tests/test_scheme_discovery.py -v

# Run specific test
pytest tests/test_scheme_discovery.py::TestSchemeDiscoveryTools::test_analyze_farmer_profile -v

# Run with coverage
pytest tests/test_scheme_discovery.py --cov=tools/scheme_discovery_tools --cov-report=html
```

## Examples

See `examples/scheme_discovery_example.py` for comprehensive usage examples:

```bash
# Run examples
cd RISE
python examples/scheme_discovery_example.py
```

## API Response Format

### Analyze Profile Response
```json
{
  "success": true,
  "analysis": {
    "relevant_categories": ["subsidies", "crop_insurance"],
    "farmer_needs": ["Financial support", "Risk protection"],
    "priority_areas": ["Income support", "Crop protection"],
    "estimated_benefits": "High",
    "farmer_category": "small",
    "profile_completeness": 1.0
  },
  "profile_summary": {
    "farmer_category": "small",
    "land_size": 2.0,
    "state": "uttar pradesh",
    "crops_count": 2
  }
}
```

### Check Eligibility Response
```json
{
  "success": true,
  "scheme_id": "SCH_PMKISAN001",
  "scheme_name": "PM-KISAN",
  "eligible": true,
  "confidence_score": 0.9,
  "reasons": ["All eligibility criteria met"],
  "required_documents": ["Aadhaar", "Bank Account", "Land Records"],
  "missing_requirements": [],
  "next_steps": [
    "Gather required documents",
    "Visit official website",
    "Complete online application"
  ]
}
```

### Recommend Schemes Response
```json
{
  "success": true,
  "count": 5,
  "schemes": [
    {
      "scheme_id": "SCH_PMKISAN001",
      "scheme_name": "PM-KISAN",
      "priority_score": 85.5,
      "priority_level": "high",
      "estimated_benefit": 6000,
      "days_to_deadline": null,
      "required_documents": ["Aadhaar", "Bank Account", "Land Records"],
      "next_steps": [...]
    }
  ],
  "total_potential_benefit": 50000,
  "recommendation_summary": {
    "high_priority": 2,
    "medium_priority": 2,
    "low_priority": 1
  }
}
```

## Error Handling

All functions return a consistent error format:

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

## Performance Considerations

- Profile analysis uses AI and may take 2-5 seconds
- Eligibility checking is fast (< 1 second)
- Scheme recommendations involve multiple queries (2-5 seconds)
- Results are optimized for mobile networks
- Consider caching recommendations for 24 hours

## Security

- All farmer data is encrypted at rest and in transit
- PII data is handled according to data protection regulations
- AWS IAM roles control access to DynamoDB and Bedrock
- API Gateway provides authentication and rate limiting

## Future Enhancements

- [ ] Machine learning for benefit prediction
- [ ] Historical success rate tracking
- [ ] Application status tracking
- [ ] Document upload and verification
- [ ] Multi-language support for scheme descriptions
- [ ] Integration with government portals for real-time data
- [ ] Automated application submission
- [ ] Scheme expiry notifications

## Support

For issues or questions:
- Check the examples in `examples/scheme_discovery_example.py`
- Review test cases in `tests/test_scheme_discovery.py`
- Consult the main RISE documentation

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) project.
