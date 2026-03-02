# Diagnosis History and Treatment Tracking

## Overview

The Diagnosis History and Treatment Tracking system provides comprehensive tools for farmers to track their crop diagnoses over time, monitor treatment progress, and generate detailed reports. This system integrates with both disease and pest identification modules to provide a unified view of all diagnoses.

## Features

### 1. Diagnosis History Retrieval
- **Unified View**: Combines disease and pest diagnoses in a single timeline
- **Filtering**: Filter by severity, crop type, follow-up status, diagnosis type, and date range
- **Sorting**: Sort by timestamp, confidence score, or severity
- **Statistics**: Automatic calculation of diagnosis statistics and distributions

### 2. Follow-up Status Tracking
Track the progress of each diagnosis with status updates:
- `pending`: Initial diagnosis, no treatment yet
- `treatment_applied`: Treatment has been applied
- `improving`: Condition is improving
- `worsened`: Condition has worsened
- `resolved`: Issue has been resolved

### 3. Treatment Progress Comparison
- **Multi-Diagnosis Comparison**: Compare 2 or more diagnoses to track treatment effectiveness
- **Progress Metrics**: Automatic calculation of severity changes and improvement trends
- **Timeline View**: Visual timeline showing diagnosis progression
- **Days Elapsed**: Track time between diagnoses

### 4. Comprehensive Reports
Generate detailed diagnosis reports including:
- Diagnosis details (ID, date, crop type, severity)
- Identified diseases or pests
- Full AI analysis
- Treatment recommendations
- Preventive measures
- Follow-up notes and status
- Downloadable text format

## Architecture

### Components

1. **DiagnosisHistoryTools** (`diagnosis_history_tools.py`)
   - Core tools for diagnosis history management
   - Used by Streamlit UI and other application components
   - Direct DynamoDB and S3 integration

2. **DiagnosisHistoryService** (`diagnosis_history_lambda.py`)
   - Lambda function service layer
   - Provides REST API endpoints
   - Handles complex queries and aggregations

3. **Enhanced UI Component** (`ui/image_uploader.py`)
   - Interactive diagnosis history display
   - Filter and search interface
   - Treatment progress comparison view
   - Status update forms

### Data Flow

```
User Request
    ↓
Streamlit UI (image_uploader.py)
    ↓
DiagnosisHistoryTools
    ↓
DynamoDB Tables (RISE-DiagnosisHistory, RISE-PestDiagnosisHistory)
    ↓
Response with diagnosis data
    ↓
UI Display with statistics and comparisons
```

## Usage

### Basic Usage

```python
from tools.diagnosis_history_tools import DiagnosisHistoryTools

# Initialize tools
history_tools = DiagnosisHistoryTools(region='us-east-1')

# Get diagnosis history
history = history_tools.get_diagnosis_history(
    user_id='farmer_123',
    limit=20
)

# Get history with filters
filtered_history = history_tools.get_diagnosis_history(
    user_id='farmer_123',
    filters={
        'severity': 'high',
        'crop_type': 'wheat',
        'follow_up_status': 'pending'
    }
)

# Update follow-up status
success = history_tools.update_follow_up_status(
    diagnosis_id='diag_001',
    status='improving',
    notes='Treatment showing positive results',
    diagnosis_type='disease'
)

# Compare diagnoses for treatment progress
comparison = history_tools.compare_diagnoses(
    diagnosis_ids=['diag_001', 'diag_002', 'diag_003']
)

print(f"Progress Status: {comparison['progress']['status']}")
print(f"Severity Change: {comparison['progress']['severity_change']}")
print(f"Days Elapsed: {comparison['progress']['days_elapsed']}")

# Generate report
report = history_tools.generate_report(
    diagnosis_id='diag_001',
    diagnosis_type='disease'
)

# Get statistics
stats = history_tools.get_statistics(user_id='farmer_123')
print(f"Total Diagnoses: {stats['total_diagnoses']}")
print(f"Severity Distribution: {stats['severity_distribution']}")
```

### Lambda Function Usage

The Lambda function provides a REST API interface:

```python
# Get history
event = {
    'action': 'get_history',
    'user_id': 'farmer_123',
    'limit': 20,
    'filters': {'severity': 'high'},
    'sort_by': 'timestamp',
    'sort_order': 'desc'
}

# Update status
event = {
    'action': 'update_status',
    'diagnosis_id': 'diag_001',
    'status': 'improving',
    'notes': 'Treatment working well',
    'diagnosis_type': 'disease'
}

# Compare diagnoses
event = {
    'action': 'compare',
    'diagnosis_ids': ['diag_001', 'diag_002', 'diag_003']
}

# Generate report
event = {
    'action': 'generate_report',
    'diagnosis_id': 'diag_001',
    'diagnosis_type': 'disease',
    'include_images': True
}
```

### Streamlit UI Usage

The enhanced UI component is automatically integrated into the main app:

1. **View History**: Navigate to the "Diagnosis History" tab
2. **Apply Filters**: Use the filter expander to narrow down results
3. **Update Status**: Click on any diagnosis card to update follow-up status
4. **Compare Progress**: Select multiple diagnoses and click "Generate Progress Report"
5. **Download Reports**: Click "View Full Report" and then "Download Report"

## API Reference

### DiagnosisHistoryTools

#### `get_diagnosis_history(user_id, limit=20, filters=None)`
Retrieve diagnosis history for a user.

**Parameters:**
- `user_id` (str): User ID
- `limit` (int): Maximum number of records (default: 20)
- `filters` (dict, optional): Filter criteria
  - `severity`: Filter by severity level
  - `crop_type`: Filter by crop type
  - `follow_up_status`: Filter by status
  - `diagnosis_type`: Filter by type (disease/pest)

**Returns:** List of diagnosis records

#### `update_follow_up_status(diagnosis_id, status, notes=None, diagnosis_type='disease')`
Update the follow-up status of a diagnosis.

**Parameters:**
- `diagnosis_id` (str): Diagnosis ID
- `status` (str): New status
- `notes` (str, optional): Follow-up notes
- `diagnosis_type` (str): Type of diagnosis

**Returns:** Boolean indicating success

#### `compare_diagnoses(diagnosis_ids)`
Compare multiple diagnoses to track treatment progress.

**Parameters:**
- `diagnosis_ids` (list): List of diagnosis IDs to compare

**Returns:** Dict with comparison data and progress metrics

#### `generate_report(diagnosis_id, diagnosis_type='disease')`
Generate a comprehensive text report for a diagnosis.

**Parameters:**
- `diagnosis_id` (str): Diagnosis ID
- `diagnosis_type` (str): Type of diagnosis

**Returns:** Report text string

#### `get_statistics(user_id)`
Calculate diagnosis statistics for a user.

**Parameters:**
- `user_id` (str): User ID

**Returns:** Dict with statistics

## Database Schema

### RISE-DiagnosisHistory Table

```
diagnosis_id (PK)          - Unique diagnosis identifier
user_id                    - User who owns the diagnosis
crop_type                  - Type of crop
severity                   - Severity level (low/medium/high/critical)
confidence_score           - AI confidence score (0-1)
diseases                   - List of identified diseases
follow_up_status           - Current follow-up status
follow_up_notes            - User notes on treatment progress
created_timestamp          - Creation timestamp
updated_timestamp          - Last update timestamp
image_s3_key              - S3 key for crop image
diagnosis_result          - Full AI analysis and recommendations
```

**Global Secondary Index:**
- `UserDiagnosisIndex`: (user_id, created_timestamp)

### RISE-PestDiagnosisHistory Table

Similar structure to DiagnosisHistory but with `pests` field instead of `diseases`.

## Testing

Run the comprehensive test suite:

```bash
# Run all diagnosis history tests
pytest tests/test_diagnosis_history.py -v

# Run specific test class
pytest tests/test_diagnosis_history.py::TestDiagnosisHistoryTools -v

# Run with coverage
pytest tests/test_diagnosis_history.py --cov=tools.diagnosis_history_tools --cov-report=html
```

### Test Coverage

The test suite covers:
- ✅ Diagnosis history retrieval
- ✅ Filtering by multiple criteria
- ✅ Follow-up status updates
- ✅ Diagnosis comparison and progress tracking
- ✅ Report generation
- ✅ Statistics calculation
- ✅ Lambda handler functions
- ✅ Error handling

## Performance Considerations

### Optimization Strategies

1. **DynamoDB Queries**
   - Uses Global Secondary Index for efficient user-based queries
   - Limits result sets to prevent over-fetching
   - Sorts at database level when possible

2. **Caching**
   - Consider implementing Redis caching for frequently accessed diagnoses
   - Cache statistics for users with many diagnoses

3. **Pagination**
   - Implement pagination for users with >100 diagnoses
   - Use DynamoDB LastEvaluatedKey for efficient pagination

4. **S3 Presigned URLs**
   - Generate presigned URLs on-demand for image access
   - Set appropriate expiration times (1 hour default)

## Security

### Data Protection

1. **Encryption**
   - DynamoDB tables use AWS-managed encryption at rest
   - S3 buckets use server-side encryption
   - TLS 1.2+ for all data in transit

2. **Access Control**
   - User can only access their own diagnoses
   - Lambda execution role has minimal required permissions
   - S3 presigned URLs expire after 1 hour

3. **Data Privacy**
   - PII is encrypted at field level
   - Audit logging for all data access
   - Compliance with data retention policies

## Future Enhancements

### Planned Features

1. **Advanced Analytics**
   - Trend analysis across multiple seasons
   - Predictive modeling for disease recurrence
   - Yield impact correlation

2. **Image Comparison**
   - Side-by-side image comparison in UI
   - Visual progress tracking
   - Automated image quality assessment

3. **Expert Consultation**
   - Share diagnoses with agricultural experts
   - Get second opinions
   - Expert annotations and recommendations

4. **Mobile Notifications**
   - Push notifications for follow-up reminders
   - Treatment schedule alerts
   - Progress milestone notifications

5. **Export Options**
   - PDF report generation with images
   - CSV export for data analysis
   - Integration with farm management systems

## Troubleshooting

### Common Issues

**Issue: History not loading**
- Check AWS credentials are configured
- Verify DynamoDB tables exist
- Check user_id is correct

**Issue: Status update fails**
- Verify diagnosis_id exists
- Check diagnosis_type is correct ('disease' or 'pest')
- Ensure DynamoDB write permissions

**Issue: Comparison shows insufficient data**
- Need at least 2 diagnoses for comparison
- Verify all diagnosis_ids exist
- Check diagnoses belong to same user

## Support

For issues or questions:
1. Check the test suite for usage examples
2. Review the main RISE documentation
3. Check AWS CloudWatch logs for Lambda errors
4. Verify DynamoDB table configuration

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) project.
