# RISE Pest Identification System

## Overview

The RISE Pest Identification System provides AI-powered pest detection and integrated pest management (IPM) recommendations for farmers. Using Amazon Bedrock's multimodal capabilities with Claude 3 Sonnet, the system analyzes crop images to identify pest species, lifecycle stages, and provides comprehensive control strategies prioritizing biological and cultural methods over chemical treatments.

## Features

### Core Capabilities

- **Pest Species Identification**: Identifies common agricultural pests with scientific names
- **Lifecycle Stage Detection**: Determines current lifecycle stage (egg, larva, pupa, nymph, adult)
- **Population Density Assessment**: Evaluates infestation severity (low, medium, high)
- **Integrated Pest Management (IPM)**: Provides prioritized control recommendations
- **Image Quality Validation**: Ensures images meet minimum quality standards
- **Diagnosis History Tracking**: Maintains records of all pest identifications
- **Pest Knowledge Base**: Stores detailed information about pest species

### IPM Recommendation Priorities

1. **Biological Controls (Priority 1)**
   - Natural predators and parasitoids
   - Beneficial insects
   - Biological pesticides (Bt, neem oil, etc.)

2. **Cultural Controls (Priority 2)**
   - Crop rotation
   - Sanitation practices
   - Trap crops and companion planting
   - Physical barriers

3. **Chemical Treatments (Last Resort)**
   - Specific pesticide recommendations
   - Exact dosages and application methods
   - Safety precautions and PPE requirements
   - Pre-harvest intervals
   - Environmental precautions

## Architecture

### Components

```
pest_identification_tools.py    # Core pest identification logic
pest_analysis_lambda.py         # AWS Lambda function for API
test_pest_identification.py     # Comprehensive unit tests
pest_identification_example.py  # Integration examples
```

### AWS Services Used

- **Amazon Bedrock**: Multimodal AI analysis (Claude 3 Sonnet)
- **Amazon S3**: Image storage with lifecycle policies
- **Amazon DynamoDB**: Diagnosis history and pest knowledge base
- **AWS Lambda**: Serverless API endpoint

### DynamoDB Tables

#### RISE-PestDiagnosisHistory
Stores pest diagnosis records with user tracking.

```python
{
    'diagnosis_id': 'pest_abc123',           # Primary Key
    'user_id': 'farmer_001',
    'image_s3_key': 'images/pest-photos/...',
    'diagnosis_result': {
        'pests': ['Aphids (Aphis gossypii)'],
        'confidence_score': 0.85,
        'severity': 'medium',
        'lifecycle_stage': 'adult',
        'population_density': 'high',
        'biological_controls': [...],
        'chemical_treatments': [...]
    },
    'crop_type': 'wheat',
    'follow_up_status': 'pending',
    'created_timestamp': 1234567890
}
```

**Global Secondary Index**: `UserPestDiagnosisIndex` on `user_id`

#### RISE-PestKnowledgeBase
Stores detailed pest information for reference.

```python
{
    'pest_id': 'pest_aphids',               # Primary Key
    'pest_name': 'Aphids',
    'scientific_name': 'Aphis gossypii',
    'common_hosts': ['cotton', 'wheat', 'vegetables'],
    'lifecycle_info': {
        'egg_duration': '4-10 days',
        'nymph_duration': '7-10 days',
        'adult_lifespan': '20-30 days'
    },
    'control_methods': {
        'biological': ['ladybugs', 'lacewings'],
        'cultural': ['crop rotation'],
        'chemical': ['neem oil']
    }
}
```

## Installation

### Prerequisites

```bash
# Python 3.8+
pip install boto3 pillow pytest

# AWS credentials configured
aws configure
```

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up DynamoDB tables (using AWS CDK or CloudFormation)
cdk deploy RISEStack

# Configure environment variables
export AWS_REGION=us-east-1
export S3_BUCKET=rise-application-data
export PEST_DIAGNOSIS_TABLE=RISE-PestDiagnosisHistory
```

## Usage

### Basic Pest Identification

```python
from tools.pest_identification_tools import PestIdentificationTools

# Initialize tools
pest_tools = PestIdentificationTools(region='us-east-1')

# Load image
with open('pest_image.jpg', 'rb') as f:
    image_data = f.read()

# Analyze pest
result = pest_tools.analyze_pest_image(
    image_data=image_data,
    user_id='farmer_001',
    crop_type='wheat',
    additional_context='Small green insects on leaves'
)

# Check results
if result['success']:
    print(f"Pests: {result['pests']}")
    print(f"Severity: {result['severity']}")
    print(f"Lifecycle Stage: {result['lifecycle_stage']}")
    print(f"Population Density: {result['population_density']}")
    
    # IPM recommendations
    print("\nBiological Controls:")
    for control in result['biological_controls']:
        print(f"  - {control['description']}")
    
    print("\nChemical Treatments (Last Resort):")
    for treatment in result['chemical_treatments']:
        print(f"  - {treatment['description']}")
```

### Image Quality Validation

```python
# Validate before analysis
validation = pest_tools.validate_image_quality(image_data)

if not validation['valid']:
    print("Image quality issues:")
    for issue in validation['issues']:
        print(f"  - {issue}")
    
    print("\nGuidance:")
    for guide in validation['guidance']:
        print(f"  - {guide}")
```

### Diagnosis History

```python
# Get user's pest diagnosis history
history = pest_tools.get_pest_diagnosis_history('farmer_001', limit=10)

for record in history:
    print(f"Date: {record['created_timestamp']}")
    print(f"Pests: {record['pests']}")
    print(f"Severity: {record['severity']}")
    print(f"Status: {record['follow_up_status']}")
```

### Follow-up Updates

```python
# Update treatment status
pest_tools.update_follow_up_status(
    diagnosis_id='pest_abc123',
    status='controlled',
    notes='Applied neem oil for 3 days. Population reduced by 80%.'
)
```

### Pest Knowledge Base

```python
# Add pest information
pest_tools.add_pest_knowledge(
    pest_name='Aphids',
    scientific_name='Aphis gossypii',
    common_hosts=['cotton', 'wheat', 'vegetables'],
    lifecycle_info={
        'egg_duration': '4-10 days',
        'nymph_duration': '7-10 days',
        'adult_lifespan': '20-30 days'
    },
    control_methods={
        'biological': ['ladybugs', 'lacewings'],
        'cultural': ['crop rotation', 'remove weeds'],
        'chemical': ['neem oil', 'insecticidal soap']
    }
)

# Retrieve pest information
knowledge = pest_tools.get_pest_knowledge('Aphids')
```

## Lambda Function API

### Endpoint

```
POST /api/v1/diagnosis/pest-identification
```

### Request Format

```json
{
  "image_data": "base64_encoded_image_string",
  "user_id": "farmer_1234567890",
  "crop_type": "wheat",
  "additional_context": "Small insects on leaves, sticky residue",
  "language_code": "hi"
}
```

### Response Format

```json
{
  "success": true,
  "diagnosis_id": "pest_abc123def456",
  "s3_key": "images/pest-photos/farmer_001/pest_abc123def456.jpg",
  "pests": ["Aphids (Aphis gossypii)"],
  "confidence_score": 0.85,
  "severity": "medium",
  "lifecycle_stage": "adult",
  "population_density": "high",
  "full_analysis": "Detailed analysis text...",
  "biological_controls": [
    {
      "type": "biological",
      "description": "Biological control methods recommended - see full analysis"
    }
  ],
  "cultural_controls": [
    {
      "type": "cultural",
      "description": "Cultural control methods recommended - see full analysis"
    }
  ],
  "chemical_treatments": [
    {
      "type": "chemical",
      "description": "Chemical treatment available as last resort - see full analysis"
    }
  ],
  "preventive_measures": ["See full analysis for detailed preventive measures"],
  "multiple_pests": false,
  "timestamp": 1234567890
}
```

### Error Response

```json
{
  "success": false,
  "error": "poor_image_quality",
  "validation": {
    "valid": false,
    "issues": ["low_resolution"],
    "guidance": ["Take a higher resolution photo (at least 300x300 pixels)"]
  }
}
```

## Testing

### Run Unit Tests

```bash
# Run all tests
pytest tests/test_pest_identification.py -v

# Run specific test
pytest tests/test_pest_identification.py::TestPestIdentificationTools::test_analyze_pest_image_success -v

# Run with coverage
pytest tests/test_pest_identification.py --cov=tools.pest_identification_tools --cov-report=html
```

### Run Integration Examples

```bash
# Run all examples
python examples/pest_identification_example.py

# Note: Requires AWS credentials and DynamoDB tables
```

## Best Practices

### Image Quality Guidelines

For best pest identification results:

1. **Resolution**: Minimum 300x300 pixels, recommended 800x600 or higher
2. **Focus**: Ensure pests are clearly visible and in focus
3. **Lighting**: Good natural lighting, avoid harsh shadows
4. **Distance**: Close enough to see pest details, but show context
5. **Background**: Include affected plant parts for context
6. **Multiple Angles**: Take several photos from different angles

### IPM Implementation

Follow the IPM hierarchy:

1. **Monitor First**: Regular scouting to detect pests early
2. **Identify Accurately**: Use the system to confirm pest species
3. **Assess Threshold**: Determine if action is needed based on population
4. **Try Biological**: Start with natural predators and biopesticides
5. **Cultural Methods**: Implement sanitation and crop management
6. **Chemical Last**: Use only when other methods are insufficient
7. **Follow-up**: Monitor effectiveness and adjust strategy

### Safety Considerations

When using chemical treatments:

- Always follow label instructions exactly
- Wear appropriate PPE (gloves, mask, protective clothing)
- Respect pre-harvest intervals
- Protect beneficial insects and pollinators
- Avoid contaminating water sources
- Store pesticides safely away from children and animals
- Dispose of containers properly

## Supported Pests

The system can identify a wide range of agricultural pests including:

### Insects
- Aphids (various species)
- Whiteflies
- Thrips
- Leafhoppers
- Caterpillars (various)
- Beetles (various)
- Mealybugs
- Scale insects

### Mites
- Spider mites
- Rust mites

### Other Arthropods
- Grasshoppers
- Locusts

*Note: The AI model can identify many more pests. This is not an exhaustive list.*

## Lifecycle Stages

The system recognizes these lifecycle stages:

- **Egg**: Pest eggs on plants or soil
- **Larva**: Immature stage (caterpillars, grubs, maggots)
- **Pupa**: Transformation stage (cocoons, pupae)
- **Nymph**: Immature stage for incomplete metamorphosis
- **Adult**: Mature reproductive stage

## Troubleshooting

### Common Issues

**Issue**: "poor_image_quality" error
- **Solution**: Retake photo with better resolution and lighting

**Issue**: Low confidence score (<70%)
- **Solution**: Take clearer photos showing pest details

**Issue**: "No pests detected" when pests are present
- **Solution**: Ensure pests are clearly visible, try closer photos

**Issue**: DynamoDB access errors
- **Solution**: Check AWS credentials and table permissions

**Issue**: S3 upload failures
- **Solution**: Verify bucket exists and has correct permissions

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

pest_tools = PestIdentificationTools(region='us-east-1')
```

## Performance Optimization

### Image Compression

Images are automatically compressed to reduce storage and processing time:

```python
# Adjust compression settings
compressed = pest_tools.compress_image(image_data, max_size_kb=500)
```

### Caching

Consider caching pest knowledge base queries:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_pest_knowledge(pest_name):
    return pest_tools.get_pest_knowledge(pest_name)
```

## Cost Optimization

### AWS Service Costs

- **Bedrock**: ~$0.003 per image analysis (Claude 3 Sonnet)
- **S3**: ~$0.023 per GB storage + $0.0004 per 1000 requests
- **DynamoDB**: On-demand pricing, ~$0.25 per million writes
- **Lambda**: Free tier covers most usage, then $0.20 per million requests

### Optimization Tips

1. Compress images before upload (done automatically)
2. Use S3 lifecycle policies to archive old images
3. Implement DynamoDB TTL for temporary data
4. Cache frequently accessed pest knowledge
5. Use Lambda reserved concurrency for predictable costs

## Multilingual Support

The system supports responses in 9 Indic languages:

- Hindi (hi)
- Tamil (ta)
- Telugu (te)
- Kannada (kn)
- Bengali (bn)
- Gujarati (gu)
- Marathi (mr)
- Punjabi (pa)
- English (en)

Specify language in API requests:

```json
{
  "language_code": "hi"
}
```

## Contributing

### Adding New Pest Species

To add a new pest to the knowledge base:

```python
pest_tools.add_pest_knowledge(
    pest_name='New Pest Name',
    scientific_name='Scientific name',
    common_hosts=['crop1', 'crop2'],
    lifecycle_info={...},
    control_methods={...}
)
```

### Improving Detection Accuracy

1. Collect diverse pest images
2. Test with real-world scenarios
3. Provide feedback on misidentifications
4. Update prompts for better guidance

## References

### Integrated Pest Management
- [FAO IPM Guidelines](http://www.fao.org/agriculture/crops/thematic-sitemap/theme/pests/ipm/en/)
- [EPA IPM Principles](https://www.epa.gov/safepestcontrol/integrated-pest-management-ipm-principles)

### Pest Identification
- [CABI Crop Protection Compendium](https://www.cabi.org/cpc/)
- [Indian Agricultural Research Institute](https://www.iari.res.in/)

### Biological Control
- [Biocontrol Network](https://www.biocontrol.entomology.cornell.edu/)
- [ICAR-NBAIR](https://nbair.res.in/)

## License

This project is part of the RISE (Rural Innovation and Sustainable Ecosystem) platform developed for the AI for Bharat Hackathon.

## Support

For issues, questions, or contributions:
- GitHub Issues: [RISE Repository]
- Email: support@rise-farming.ai
- Documentation: [RISE Docs]

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Maintainer**: RISE Development Team
