# RISE Scheme Application Assistance System

## Overview

The Scheme Application Assistance System provides comprehensive support for farmers applying to government schemes. It offers voice-guided wizards, document validation, digital submission helpers, and real-time status tracking with multilingual notifications.

## Features

### 1. Voice-Guided Application Wizard
- **Step-by-step guidance** through the application process
- **Multilingual voice instructions** in 9 Indic languages
- **Estimated time** for each step
- **Progress tracking** throughout the application journey

### 2. Document Format Validator
- **Automatic format validation** (PDF, JPG, PNG)
- **File size checking** against scheme requirements
- **Missing document detection**
- **Clear error messages** with remediation guidance

### 3. Digital Submission Helper
- **Pre-submission validation** of all documents
- **Automatic form filling** from user profile
- **Submission confirmation** with tracking number
- **Receipt generation** for record-keeping

### 4. Application Status Tracking
- **Real-time status updates** with progress percentage
- **Visual timeline** of application journey
- **Estimated completion dates**
- **Next action recommendations**

### 5. Notification System
- **SMS notifications** for status updates
- **Voice notifications** in preferred language
- **Configurable preferences** for notification types
- **Proactive alerts** for required actions

## Architecture

### Components

```
scheme_application_lambda.py    # AWS Lambda handler
scheme_application_tools.py     # Core business logic
scheme_application.py           # Streamlit UI component
test_scheme_application.py      # Unit tests
scheme_application_example.py   # Usage examples
```

### AWS Services Used

- **Amazon Bedrock**: AI-powered wizard generation
- **Amazon Translate**: Multilingual support
- **Amazon Polly**: Voice instruction synthesis
- **Amazon SNS**: SMS notifications
- **Amazon S3**: Document storage
- **Amazon DynamoDB**: Application data storage

### DynamoDB Tables

#### RISE-SchemeApplications
```json
{
  "application_id": "APP_XXXXXXXXXXXX",
  "user_id": "user_12345",
  "scheme_id": "SCH_PM_KISAN",
  "scheme_name": "PM-KISAN",
  "application_data": {...},
  "documents": [...],
  "status": "submitted",
  "submission_timestamp": 1700000000,
  "last_updated": 1700000000,
  "status_history": [...],
  "tracking_number": "RISE-1234-5678"
}
```

## Usage

### 1. Generate Application Wizard

```python
from tools.scheme_application_tools import SchemeApplicationTools

tools = SchemeApplicationTools(region='us-east-1')

# Generate wizard
result = tools.generate_application_wizard(
    user_id='user_12345',
    scheme_id='SCH_PM_KISAN',
    language='hi'  # Hindi
)

if result['success']:
    print(f"Wizard generated with {result['total_steps']} steps")
    print(f"Estimated time: {result['estimated_time_minutes']} minutes")
    
    for step in result['wizard_steps']:
        print(f"Step {step['step_number']}: {step['title']}")
        print(f"Instructions: {step['instructions']}")
```

### 2. Validate Documents

```python
# Prepare documents
documents = [
    {
        'name': 'Aadhaar Card',
        'format': 'pdf',
        'size_mb': 1.5,
        's3_key': 'documents/aadhaar_123.pdf'
    },
    {
        'name': 'Land Records',
        'format': 'pdf',
        'size_mb': 3.2,
        's3_key': 'documents/land_records_123.pdf'
    }
]

# Validate
result = tools.validate_documents(documents, 'SCH_PM_KISAN')

if result['success']:
    if result['all_valid']:
        print("✅ All documents validated successfully")
    else:
        print("⚠️ Validation issues found:")
        for validation in result['validation_results']:
            if not validation['valid']:
                print(f"  - {validation['document_name']}: {validation['issues']}")
```

### 3. Submit Application

```python
# Prepare application data
application_data = {
    'personal_info': {
        'full_name': 'Ravi Kumar',
        'father_name': 'Ram Kumar',
        'date_of_birth': '1985-05-15',
        'gender': 'Male'
    },
    'contact_info': {
        'mobile': '+91 9876543210',
        'email': 'ravi.kumar@example.com',
        'address': 'Village Rampur, District Lucknow'
    },
    'bank_details': {
        'bank_name': 'State Bank of India',
        'account_number': '1234567890',
        'ifsc_code': 'SBIN0001234',
        'account_holder': 'Ravi Kumar'
    },
    'documents': documents,
    'declaration': True
}

# Submit
result = tools.submit_application(
    user_id='user_12345',
    scheme_id='SCH_PM_KISAN',
    application_data=application_data
)

if result['success']:
    print(f"✅ Application submitted!")
    print(f"Application ID: {result['application_id']}")
    print(f"Tracking Number: {result['tracking_number']}")
    print(f"Status: {result['status']}")
```

### 4. Track Application Status

```python
# Track status
result = tools.track_application_status('APP_ABC123DEF456')

if result['success']:
    print(f"Current Status: {result['current_status']}")
    print(f"Progress: {result['progress_percentage']}%")
    print(f"Last Updated: {result['last_updated']}")
    
    print("\nStatus Timeline:")
    for entry in result['status_timeline']:
        print(f"  {entry['status']} - {entry['date']} at {entry['time']}")
    
    print(f"\nNext Action: {result['next_action']}")
```

### 5. Send Notifications

```python
# Send notification
result = tools.send_application_notification(
    user_id='user_12345',
    application_id='APP_ABC123DEF456',
    notification_type='submission_confirmation'
)

if result['success']:
    print(f"✅ Notification sent")
    print(f"Message: {result['message']}")
    print(f"Voice Audio: {result['voice_audio_url']}")
```

## Document Format Requirements

### Supported Formats and Size Limits

| Document Type | Formats | Max Size |
|--------------|---------|----------|
| Aadhaar Card | PDF, JPG, JPEG, PNG | 2 MB |
| Land Records | PDF | 5 MB |
| Bank Passbook | PDF, JPG, JPEG, PNG | 2 MB |
| Income Certificate | PDF | 3 MB |
| Caste Certificate | PDF | 3 MB |
| Passport Photo | JPG, JPEG, PNG | 1 MB |

## Application Status Flow

```
submitted → under_review → documents_verified → approved → disbursed
                                                    ↓
                                                rejected
```

### Status Descriptions

- **submitted** (20%): Application received and queued for review
- **under_review** (40%): Officials reviewing application details
- **documents_verified** (60%): All documents verified successfully
- **approved** (80%): Application approved, awaiting disbursement
- **disbursed** (100%): Benefit amount transferred to account
- **rejected** (0%): Application rejected (contact local office)

## Notification Types

### Available Notification Types

1. **submission_confirmation**: Sent immediately after submission
2. **status_update**: Sent when status changes
3. **document_required**: Sent when additional documents needed
4. **approved**: Sent when application is approved
5. **rejected**: Sent when application is rejected

### Notification Channels

- **SMS**: Text message to registered mobile number
- **Voice**: Audio message in preferred language
- **In-App**: Push notification in mobile app

## Multilingual Support

### Supported Languages

| Language | Code | Voice ID |
|----------|------|----------|
| Hindi | hi | Aditi |
| English | en | Joanna |
| Tamil | ta | Aditi |
| Telugu | te | Aditi |
| Kannada | kn | Aditi |
| Bengali | bn | Aditi |
| Gujarati | gu | Aditi |
| Marathi | mr | Aditi |
| Punjabi | pa | Aditi |

## API Reference

### SchemeApplicationTools Class

#### Methods

##### `generate_application_wizard(user_id, scheme_id, language='hi')`
Generate voice-guided step-by-step application wizard.

**Parameters:**
- `user_id` (str): User identifier
- `scheme_id` (str): Scheme identifier
- `language` (str): Language code (default: 'hi')

**Returns:**
- `dict`: Wizard steps with voice instructions

##### `validate_documents(documents, scheme_id)`
Validate document formats and completeness.

**Parameters:**
- `documents` (list): List of document objects
- `scheme_id` (str): Scheme identifier

**Returns:**
- `dict`: Validation results with issues

##### `submit_application(user_id, scheme_id, application_data)`
Submit application with digital helper.

**Parameters:**
- `user_id` (str): User identifier
- `scheme_id` (str): Scheme identifier
- `application_data` (dict): Application form data

**Returns:**
- `dict`: Submission confirmation with tracking number

##### `track_application_status(application_id)`
Track application status with detailed timeline.

**Parameters:**
- `application_id` (str): Application identifier

**Returns:**
- `dict`: Current status and history

##### `send_application_notification(user_id, application_id, notification_type)`
Send notification for application updates.

**Parameters:**
- `user_id` (str): User identifier
- `application_id` (str): Application identifier
- `notification_type` (str): Type of notification

**Returns:**
- `dict`: Notification status

## Testing

### Run Unit Tests

```bash
cd RISE
python -m pytest tests/test_scheme_application.py -v
```

### Run Example Script

```bash
cd RISE
python examples/scheme_application_example.py
```

## UI Component

### Streamlit Interface

The system includes a comprehensive Streamlit UI with four main sections:

1. **Application Wizard**: Interactive step-by-step guidance
2. **Document Validation**: Upload and validate documents
3. **Submit Application**: Complete form and submit
4. **Track Status**: Monitor application progress

### Launch UI

```bash
cd RISE
streamlit run ui/scheme_application.py
```

## Integration with Other Systems

### Scheme Discovery Integration

The application system integrates seamlessly with the Scheme Discovery system:

```python
# Discover schemes
from tools.scheme_discovery_tools import SchemeDiscoveryTools

discovery_tools = SchemeDiscoveryTools()
schemes = discovery_tools.recommend_schemes(farmer_profile)

# Apply to recommended scheme
application_tools = SchemeApplicationTools()
wizard = application_tools.generate_application_wizard(
    user_id=user_id,
    scheme_id=schemes['schemes'][0]['scheme_id'],
    language='hi'
)
```

## Best Practices

### 1. Document Preparation
- Scan documents in high resolution (300 DPI minimum)
- Ensure documents are clear and readable
- Use PDF format for official documents
- Keep file sizes within limits

### 2. Form Filling
- Double-check all information before submission
- Use exact names as per official documents
- Verify bank account details carefully
- Keep copies of all submitted documents

### 3. Status Tracking
- Save your application ID and tracking number
- Check status regularly (weekly)
- Respond promptly to document requests
- Contact local office if status unchanged for 30+ days

### 4. Notification Management
- Keep mobile number updated
- Enable both SMS and voice notifications
- Check notifications daily during application period
- Save important notification messages

## Troubleshooting

### Common Issues

#### Document Validation Fails
- **Issue**: Document format not accepted
- **Solution**: Convert to PDF or JPG format
- **Issue**: File size too large
- **Solution**: Compress file or reduce image quality

#### Application Submission Fails
- **Issue**: Missing required documents
- **Solution**: Upload all documents listed in wizard
- **Issue**: Invalid bank details
- **Solution**: Verify IFSC code and account number

#### Status Not Updating
- **Issue**: Status stuck at "submitted" for 7+ days
- **Solution**: Contact local agriculture office
- **Issue**: Application ID not found
- **Solution**: Verify application ID format (APP_XXXXXXXXXXXX)

## Performance Metrics

### Expected Response Times

- Wizard generation: < 3 seconds
- Document validation: < 2 seconds
- Application submission: < 5 seconds
- Status tracking: < 1 second
- Notification delivery: < 10 seconds

### Success Rates

- Document validation accuracy: > 95%
- Application submission success: > 98%
- Notification delivery: > 99%
- Status tracking availability: > 99.5%

## Security and Privacy

### Data Protection

- All documents encrypted at rest (AES-256)
- Secure transmission using TLS 1.2+
- Access control via AWS IAM
- Audit logging for all operations

### Privacy Compliance

- Explicit consent for data collection
- Granular privacy controls
- Right to data deletion
- Compliance with Indian data protection laws

## Future Enhancements

### Planned Features

1. **Offline Mode**: Complete applications without internet
2. **OCR Integration**: Auto-fill forms from document scans
3. **Video KYC**: Remote identity verification
4. **Chatbot Support**: 24/7 assistance for queries
5. **Bulk Applications**: Apply to multiple schemes simultaneously

## Support

### Getting Help

- **Documentation**: See this README and code comments
- **Examples**: Run `scheme_application_example.py`
- **Tests**: Check `test_scheme_application.py` for usage patterns
- **Issues**: Contact RISE support team

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) project for AI for Bharat Hackathon.

---

**Last Updated**: 2024
**Version**: 1.0.0
**Maintainer**: RISE Development Team
