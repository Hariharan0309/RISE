# RISE Crop Disease Identification System

## Overview

The RISE Crop Disease Identification System uses Amazon Bedrock's multimodal capabilities (Claude 3 Sonnet) to analyze crop images and identify diseases, providing farmers with instant diagnosis and treatment recommendations.

## Features

### 1. Image Analysis
- **Multimodal AI**: Uses Claude 3 Sonnet for advanced image understanding
- **Disease Detection**: Identifies multiple crop diseases from a single image
- **Confidence Scoring**: Provides confidence levels for each diagnosis
- **Severity Classification**: Categorizes diseases as low, medium, high, or critical

### 2. Image Quality Validation
- **Resolution Check**: Ensures minimum 300x300 pixels
- **Aspect Ratio Validation**: Detects unusual framing
- **Size Validation**: Checks file size constraints
- **Quality Guidance**: Provides specific recommendations for better photos

### 3. Image Compression
- **Automatic Compression**: Reduces image size while maintaining quality
- **Optimized for Upload**: Targets 500KB for fast transmission
- **Quality Preservation**: Uses iterative compression to balance size and quality

### 4. Treatment Recommendations
- **Prioritized Actions**: Recommendations sorted by urgency
- **Chemical Treatments**: Specific fungicides/pesticides with dosages
- **Organic Alternatives**: Natural treatment options
- **Application Timing**: When and how often to apply treatments
- **Safety Precautions**: Protective measures for farmers

### 5. Multiple Issue Detection
- **Simultaneous Diseases**: Detects multiple diseases in one image
- **Priority Ranking**: Ranks issues by urgency and impact
- **Comprehensive Analysis**: Addresses all detected problems

### 6. Diagnosis History
- **DynamoDB Storage**: Persistent storage of all diagnoses
- **S3 Image Archive**: Long-term image storage with lifecycle policies
- **Follow-up Tracking**: Monitor treatment progress
- **Historical Analysis**: Review past diagnoses

## Architecture

### Components

1. **disease_identification_tools.py**
   - Core Python module for disease identification
   - Integrates with Amazon Bedrock, S3, and DynamoDB
   - Handles image processing and analysis

2. **image_analysis_lambda.py**
   - AWS Lambda function for serverless image analysis
   - Handles HTTP requests from frontend
   - Processes images and stores results

3. **image_uploader.py**
   - Streamlit UI component for image upload
   - Provides file upload and camera capture
   - Displays diagnosis results

### AWS Services Used

- **Amazon Bedrock**: Claude 3 Sonnet for multimodal image analysis
- **Amazon S3**: Image storage with lifecycle policies
- **Amazon DynamoDB**: Diagnosis history and metadata
- **AWS Lambda**: Serverless image processing (optional)

### Data Flow

```
User Upload Image
    ↓
Image Quality Validation
    ↓
Image Compression
    ↓
Upload to S3
    ↓
Bedrock Multimodal Analysis
    ↓
Parse Diagnosis Results
    ↓
Store in DynamoDB
    ↓
Display to User
```

## Usage

### Python API

```python
from tools.disease_identification_tools import DiseaseIdentificationTools

# Initialize tools
disease_tools = DiseaseIdentificationTools(region='us-east-1')

# Analyze image
with open('crop_image.jpg', 'rb') as f:
    image_data = f.read()

result = disease_tools.analyze_crop_image(
    image_data=image_data,
    user_id='farmer_123',
    crop_type='wheat',
    additional_context='Leaves turning yellow'
)

if result['success']:
    print(f"Diseases: {result['diseases']}")
    print(f"Severity: {result['severity']}")
    print(f"Confidence: {result['confidence_score']}")
    print(f"Analysis: {result['full_analysis']}")
```

### Streamlit UI

```python
from ui.image_uploader import render_image_uploader

# Render image uploader in Streamlit app
result = render_image_uploader(
    user_id='farmer_123',
    language_code='hi'
)

if result:
    st.success(f"Diagnosis complete: {result['diagnosis_id']}")
```

### Lambda Function

Deploy `image_analysis_lambda.py` as an AWS Lambda function:

```bash
# Package dependencies
pip install -r requirements.txt -t package/
cd package
zip -r ../lambda_function.zip .
cd ..
zip -g lambda_function.zip image_analysis_lambda.py

# Deploy with AWS CLI
aws lambda create-function \
    --function-name rise-image-analysis \
    --runtime python3.11 \
    --handler image_analysis_lambda.lambda_handler \
    --zip-file fileb://lambda_function.zip \
    --role arn:aws:iam::ACCOUNT:role/lambda-bedrock-role \
    --timeout 60 \
    --memory-size 1024 \
    --environment Variables={S3_BUCKET=rise-application-data}
```

## API Reference

### DiseaseIdentificationTools

#### `__init__(region: str = "us-east-1")`
Initialize disease identification tools.

#### `analyze_crop_image(image_data: bytes, user_id: str, crop_type: Optional[str] = None, additional_context: Optional[str] = None) -> Dict[str, Any]`
Analyze crop image for disease identification.

**Parameters:**
- `image_data`: Image bytes (JPEG, PNG)
- `user_id`: User ID for tracking
- `crop_type`: Optional crop type (e.g., 'wheat', 'rice')
- `additional_context`: Optional context from user

**Returns:**
```python
{
    'success': True,
    'diagnosis_id': 'diag_abc123',
    'diseases': ['Leaf Rust', 'Powdery Mildew'],
    'confidence_score': 0.85,
    'severity': 'medium',
    'full_analysis': '...',
    'treatment_recommendations': [...],
    'preventive_measures': [...],
    'multiple_issues': True,
    's3_key': 'images/crop-photos/...'
}
```

#### `validate_image_quality(image_data: bytes) -> Dict[str, Any]`
Validate image quality before analysis.

**Returns:**
```python
{
    'valid': True,
    'issues': [],
    'guidance': [],
    'dimensions': {'width': 1024, 'height': 768},
    'file_size_kb': 245.3
}
```

#### `compress_image(image_data: bytes, max_size_kb: int = 500) -> bytes`
Compress image to reduce size.

#### `get_diagnosis_history(user_id: str, limit: int = 10) -> List[Dict[str, Any]]`
Get diagnosis history for a user.

#### `update_follow_up_status(diagnosis_id: str, status: str, notes: Optional[str] = None) -> bool`
Update follow-up status for a diagnosis.

## Configuration

### Environment Variables

- `AWS_REGION`: AWS region (default: us-east-1)
- `S3_BUCKET`: S3 bucket for image storage (default: rise-application-data)
- `DIAGNOSIS_TABLE`: DynamoDB table name (default: RISE-DiagnosisHistory)
- `MAX_IMAGE_SIZE`: Maximum image size in bytes (default: 5MB)
- `BEDROCK_MODEL_ID`: Bedrock model ID (default: anthropic.claude-3-sonnet-20240229-v1:0)

### DynamoDB Schema

**Table: RISE-DiagnosisHistory**

```json
{
    "diagnosis_id": "diag_abc123",
    "user_id": "farmer_123",
    "image_s3_key": "images/crop-photos/...",
    "diagnosis_result": {
        "diseases": ["Leaf Rust"],
        "confidence_score": 0.85,
        "severity": "medium",
        "full_analysis": "...",
        "treatment_recommendations": [...],
        "preventive_measures": [...]
    },
    "confidence_score": 0.85,
    "severity": "medium",
    "diseases": ["Leaf Rust"],
    "crop_type": "wheat",
    "follow_up_status": "pending",
    "created_timestamp": 1234567890
}
```

**Global Secondary Index: UserDiagnosisIndex**
- Partition Key: `user_id`
- Sort Key: `created_timestamp`

### S3 Storage Structure

```
rise-application-data/
├── images/
│   ├── crop-photos/
│   │   └── {user_id}/
│   │       └── {diagnosis_id}.jpg
│   └── thumbnails/
│       └── {user_id}/
│           └── {diagnosis_id}-thumb.jpg
```

**Lifecycle Policies:**
- Crop images: Move to IA after 90 days, Glacier after 1 year
- Thumbnails: Move to IA after 90 days

## Performance

### Response Times
- Image validation: < 100ms
- Image compression: < 500ms
- Bedrock analysis: 5-10 seconds
- Total end-to-end: < 15 seconds

### Accuracy
- Disease detection accuracy: > 90% (target)
- Confidence scoring: Calibrated to real-world performance
- Multiple issue detection: Handles up to 5 simultaneous diseases

### Scalability
- Serverless architecture scales automatically
- DynamoDB on-demand billing
- S3 handles unlimited storage
- CloudFront CDN for global distribution

## Error Handling

### Common Errors

1. **Poor Image Quality**
   - Error: `poor_image_quality`
   - Solution: Provides specific guidance for better photos

2. **Invalid Image Format**
   - Error: `invalid_image`
   - Solution: Upload JPEG or PNG format

3. **Image Too Large**
   - Error: `file_size_exceeded`
   - Solution: Automatic compression or user guidance

4. **Bedrock API Error**
   - Error: `analysis_failed`
   - Solution: Retry with exponential backoff

5. **S3 Upload Error**
   - Error: `upload_failed`
   - Solution: Check permissions and retry

## Testing

### Unit Tests

```python
# Test image validation
def test_image_validation():
    tools = DiseaseIdentificationTools()
    
    with open('test_image.jpg', 'rb') as f:
        image_data = f.read()
    
    result = tools.validate_image_quality(image_data)
    assert result['valid'] == True

# Test image compression
def test_image_compression():
    tools = DiseaseIdentificationTools()
    
    with open('large_image.jpg', 'rb') as f:
        image_data = f.read()
    
    compressed = tools.compress_image(image_data, max_size_kb=500)
    assert len(compressed) < 500 * 1024
```

### Integration Tests

```python
# Test end-to-end analysis
def test_disease_analysis():
    tools = DiseaseIdentificationTools()
    
    with open('diseased_crop.jpg', 'rb') as f:
        image_data = f.read()
    
    result = tools.analyze_crop_image(
        image_data=image_data,
        user_id='test_user',
        crop_type='wheat'
    )
    
    assert result['success'] == True
    assert 'diseases' in result
    assert 'confidence_score' in result
```

## Best Practices

### For Farmers

1. **Image Quality**
   - Take photos in good lighting (natural daylight preferred)
   - Focus on affected areas (leaves, stems, fruits)
   - Capture close-up details of symptoms
   - Avoid blurry or dark images

2. **Context**
   - Specify crop type for better accuracy
   - Describe observed symptoms
   - Mention recent weather or treatments

3. **Follow-up**
   - Track treatment progress
   - Upload follow-up images
   - Update diagnosis status

### For Developers

1. **Error Handling**
   - Always validate images before analysis
   - Provide clear error messages
   - Implement retry logic for transient failures

2. **Performance**
   - Compress images before upload
   - Use async processing for large batches
   - Cache common diagnoses

3. **Security**
   - Validate user permissions
   - Sanitize file uploads
   - Encrypt sensitive data

## Troubleshooting

### Issue: Analysis takes too long
- **Cause**: Large image size or network latency
- **Solution**: Enable image compression, check network connection

### Issue: Low confidence scores
- **Cause**: Poor image quality or unclear symptoms
- **Solution**: Request better photos with specific guidance

### Issue: Incorrect diagnosis
- **Cause**: Unusual disease or insufficient training data
- **Solution**: Allow user feedback, flag for expert review

### Issue: S3 upload fails
- **Cause**: Permissions or bucket configuration
- **Solution**: Check IAM roles and bucket policies

## Future Enhancements

1. **Advanced Features**
   - Pest identification (separate from diseases)
   - Nutrient deficiency detection
   - Growth stage analysis
   - Yield prediction

2. **Improved Accuracy**
   - Fine-tuned models for specific crops
   - Regional disease databases
   - Seasonal pattern recognition

3. **User Experience**
   - Batch image processing
   - Video analysis
   - AR overlay for real-time diagnosis
   - Voice-guided image capture

4. **Integration**
   - Weather data correlation
   - Treatment tracking
   - Expert consultation
   - Community knowledge sharing

## Support

For issues or questions:
- GitHub Issues: [RISE Repository]
- Documentation: [RISE Docs]
- Email: support@rise-farming.ai

## License

Copyright © 2024 RISE - Rural Innovation and Sustainable Ecosystem
