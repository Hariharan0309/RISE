# Government Scheme Database - RISE

## Overview

The Government Scheme Database module provides comprehensive tools for managing, searching, and analyzing government agricultural schemes for Indian farmers. It supports both central and state-level schemes with features for data ingestion, categorization, eligibility checking, and automated monitoring.

## Features

### Core Capabilities

1. **Scheme Data Ingestion**
   - Ingest scheme data from multiple sources
   - Automatic data validation and enrichment
   - Support for central and state schemes
   - Flexible schema for diverse scheme types

2. **Advanced Search**
   - Search by state, category, and scheme type
   - Filter by active/inactive status
   - Sort by benefit amount and deadline
   - Full-text search capabilities

3. **Scheme Categorization**
   - AI-powered automatic categorization
   - 10 predefined categories
   - Tag generation for improved searchability
   - Target beneficiary identification

4. **Data Scraping & Integration**
   - Web scraping from government portals
   - API integration with official sources
   - Scheduled data updates
   - Error handling and retry logic

5. **Monitoring System**
   - Automatic expiration detection
   - Status update notifications
   - Change tracking and versioning
   - Deadline alerts

## Architecture

### DynamoDB Table Structure

**Table Name:** `RISE-GovernmentSchemes`

**Primary Key:**
- Partition Key: `scheme_id` (String)

**Global Secondary Indexes:**

1. **StateSchemeIndex**
   - Partition Key: `state`
   - Sort Key: `scheme_type`
   - Use: Search schemes by state and type

2. **CategorySchemeIndex**
   - Partition Key: `category`
   - Sort Key: `benefit_amount`
   - Use: Search schemes by category, sorted by benefit

3. **DeadlineSchemeIndex**
   - Partition Key: `active_status`
   - Sort Key: `application_deadline`
   - Use: Monitor active schemes by deadline

### Scheme Data Model

```json
{
  "scheme_id": "SCH_ABC123",
  "scheme_name": "PM-KISAN",
  "scheme_type": "central",
  "state": "central",
  "category": "subsidies",
  "description": "Direct income support scheme",
  "benefit_amount": 6000,
  "eligibility_criteria": {
    "land_ownership": "required",
    "land_size": "any",
    "farmer_type": "all"
  },
  "application_process": "Online through portal",
  "required_documents": ["Aadhaar", "Bank Account", "Land Records"],
  "application_deadline": 1735689600,
  "official_website": "https://pmkisan.gov.in",
  "active_status": "active",
  "tags": ["subsidy", "central", "income_support"],
  "created_at": 1704067200,
  "last_updated": 1704067200
}
```

## Scheme Categories

1. **crop_insurance** - Insurance schemes for crop protection
2. **subsidies** - Direct financial subsidies and support
3. **loans** - Agricultural loans and credit facilities
4. **equipment** - Equipment purchase subsidies
5. **irrigation** - Irrigation infrastructure support
6. **organic_farming** - Organic farming promotion schemes
7. **training** - Training and skill development programs
8. **market_access** - Market linkage and access programs
9. **soil_health** - Soil health management schemes
10. **seeds** - Seed distribution and quality programs

## Usage Examples

### 1. Search for Schemes

```python
from government_scheme_tools import GovernmentSchemeTools

tools = GovernmentSchemeTools(region='us-east-1')

# Search for central subsidy schemes
result = tools.search_schemes(
    state='central',
    category='subsidies',
    scheme_type='central',
    active_only=True
)

if result['success']:
    print(f"Found {result['count']} schemes")
    for scheme in result['schemes']:
        print(f"- {scheme['scheme_name']}: ₹{scheme['benefit_amount']}")
```

### 2. Ingest New Scheme

```python
from datetime import datetime, timedelta

new_scheme = {
    'scheme_name': 'State Organic Farming Scheme',
    'scheme_type': 'state',
    'state': 'punjab',
    'category': 'organic_farming',
    'description': 'Support for organic farming transition',
    'benefit_amount': 25000,
    'eligibility_criteria': {
        'land_ownership': 'required',
        'land_size': 'minimum 1 acre'
    },
    'application_deadline': (datetime.now() + timedelta(days=90)).isoformat(),
    'active_status': 'active'
}

result = tools.ingest_scheme_data(new_scheme)
print(f"Scheme ID: {result['scheme_id']}")
```

### 3. Get Scheme Details

```python
# Get detailed information about a specific scheme
result = tools.get_scheme_details('SCH_ABC123')

if result['success']:
    scheme = result['scheme']
    print(f"Name: {scheme['scheme_name']}")
    print(f"Benefit: ₹{scheme['benefit_amount']}")
    print(f"Eligibility: {scheme['eligibility_criteria']}")
```

### 4. Monitor Schemes

```python
# Check for expired schemes and updates
result = tools.monitor_scheme_updates()

print(f"Monitored: {result['total_schemes_monitored']} schemes")
print(f"Expired: {result['expired_schemes']} schemes")
```

### 5. AI-Powered Categorization

```python
description = "Scheme providing subsidies for drip irrigation systems"

result = tools.categorize_scheme(description)

if result['success']:
    cat = result['categorization']
    print(f"Category: {cat['primary_category']}")
    print(f"Tags: {cat['tags']}")
```

## Lambda Function Integration

### Event Structure

```json
{
  "action": "search",
  "state": "punjab",
  "category": "subsidies",
  "active_only": true
}
```

### Supported Actions

- `search` - Search for schemes
- `get_details` - Get scheme details
- `ingest` - Ingest new scheme data
- `update_status` - Update scheme status
- `scrape` - Scrape government data sources
- `monitor` - Monitor for updates

### Example Lambda Invocation

```python
import boto3
import json

lambda_client = boto3.client('lambda')

event = {
    'action': 'search',
    'category': 'crop_insurance',
    'active_only': True
}

response = lambda_client.invoke(
    FunctionName='government-scheme-lambda',
    InvocationType='RequestResponse',
    Payload=json.dumps(event)
)

result = json.loads(response['Payload'].read())
print(result)
```

## Agent Tool Integration

### Tool Functions

The module provides ready-to-use tool functions for agent integration:

```python
from government_scheme_tools import (
    search_schemes_tool,
    get_scheme_details_tool,
    ingest_scheme_tool
)

# Use in agent workflows
schemes_info = search_schemes_tool(category='subsidies')
details = get_scheme_details_tool('SCH_ABC123')
```

## Data Sources

### Government APIs (Production Integration)

1. **PM-KISAN Portal** - https://pmkisan.gov.in
2. **PMFBY Portal** - https://pmfby.gov.in
3. **Data.gov.in** - https://data.gov.in
4. **AgMarkNet** - https://agmarknet.gov.in
5. **State Agriculture Portals** - Various state-specific portals

### Mock Data (Development)

The module includes comprehensive mock data for development and testing:
- PM-KISAN (Income Support)
- PMFBY (Crop Insurance)
- Kisan Credit Card (Loans)
- Soil Health Card Scheme
- Paramparagat Krishi Vikas Yojana (Organic Farming)

## Monitoring & Maintenance

### Automated Monitoring

Set up EventBridge rules for automated monitoring:

```python
# Schedule daily monitoring
{
  "schedule": "rate(1 day)",
  "target": "government-scheme-lambda",
  "input": {
    "action": "monitor"
  }
}
```

### Data Freshness

- Schemes are monitored daily for expiration
- External sources checked weekly for updates
- Cache TTL: No caching (real-time data)
- Historical data retained indefinitely

## Error Handling

The module implements comprehensive error handling:

```python
try:
    result = tools.search_schemes(category='invalid')
    if not result['success']:
        print(f"Error: {result['error']}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

## Testing

### Run Unit Tests

```bash
cd RISE
python -m pytest tests/test_government_scheme.py -v
```

### Test Coverage

- Scheme ingestion (success and failure cases)
- Search functionality (all query types)
- Status updates
- Monitoring system
- AI categorization
- Data enrichment
- Tool functions

## Performance Considerations

### DynamoDB Optimization

- Use GSIs for efficient queries
- Batch operations for bulk ingestion
- Conditional writes to prevent duplicates
- TTL for automatic cleanup (if needed)

### Caching Strategy

- No caching for scheme data (always fresh)
- Cache AI categorization results
- Cache search results for common queries (optional)

## Security

### Data Protection

- Encryption at rest (AWS managed keys)
- Encryption in transit (TLS 1.2+)
- IAM role-based access control
- Audit logging enabled

### Access Control

```python
# Required IAM permissions
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:GetItem",
    "dynamodb:PutItem",
    "dynamodb:Query",
    "dynamodb:Scan",
    "dynamodb:UpdateItem"
  ],
  "Resource": "arn:aws:dynamodb:*:*:table/RISE-GovernmentSchemes"
}
```

## Future Enhancements

1. **Multi-language Support**
   - Scheme descriptions in regional languages
   - Automatic translation of scheme details

2. **Eligibility Checker**
   - AI-powered eligibility determination
   - Farmer profile matching

3. **Application Assistance**
   - Step-by-step application guidance
   - Document preparation help

4. **Notification System**
   - Deadline reminders
   - New scheme alerts
   - Status update notifications

5. **Analytics Dashboard**
   - Scheme adoption rates
   - Benefit distribution analysis
   - Geographic coverage maps

## Support & Documentation

- **Example Code**: `examples/government_scheme_example.py`
- **Unit Tests**: `tests/test_government_scheme.py`
- **Lambda Function**: `tools/government_scheme_lambda.py`
- **Core Module**: `tools/government_scheme_tools.py`

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) platform.

## Contact

For issues or questions, please refer to the main RISE documentation.
