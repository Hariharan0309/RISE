# RISE Soil Analysis System

## Overview

The RISE Soil Analysis System provides comprehensive soil assessment capabilities using Amazon Bedrock's multimodal AI. It supports both image-based analysis and manual soil test data input, delivering actionable recommendations for soil improvement and crop selection.

## Features

### 1. Soil Type Classification
- **Supported Types**: Clay, Loam, Sandy, Silt, Peat, Chalky
- **Analysis Methods**: Visual assessment from images or texture data from tests
- **Accuracy**: High confidence classification with detailed characteristics

### 2. Fertility Assessment
- **Levels**: Low, Medium, High
- **Parameters**: NPK levels, pH, organic matter content
- **Visual Indicators**: Color, texture, structure analysis

### 3. Nutrient Analysis
- **Nitrogen (N)**: Essential for leaf growth and green color
- **Phosphorus (P)**: Critical for root development and flowering
- **Potassium (K)**: Important for overall plant health and disease resistance
- **pH Level**: Acidity/alkalinity measurement (optimal range: 6.0-7.5)
- **Organic Matter**: Percentage of decomposed plant and animal material

### 4. Deficiency Identification
- Automated detection of nutrient deficiencies
- Severity assessment (low/medium/high/critical)
- Impact analysis on crop production
- Visual symptom identification

### 5. Amendment Recommendations
- **Organic Options**: Compost, manure, green manure, vermicompost
- **Chemical Options**: Specific fertilizers with NPK ratios
- **Quantities**: Precise amounts per acre in kg or tons
- **Application Methods**: Detailed instructions for application
- **Timing**: Optimal application schedules
- **Cost Estimates**: Approximate costs in Indian Rupees

### 6. Crop Recommendations
- **Highly Suitable**: Crops that will thrive in current conditions
- **Moderately Suitable**: Crops that need minor amendments
- **Not Recommended**: Crops unsuitable for the soil type
- **Expected Yields**: Estimated production per acre
- **Market Demand**: Current market trends and pricing

## Architecture

### Components

1. **soil_analysis_lambda.py**: AWS Lambda function for serverless processing
2. **soil_analysis_tools.py**: Strands tools for agent integration
3. **test_soil_analysis.py**: Comprehensive unit tests

### AWS Services Used

- **Amazon Bedrock**: Claude 3 Sonnet for multimodal soil analysis
- **Amazon S3**: Storage for soil sample images
- **Amazon DynamoDB**: Storage for analysis results (RISE-FarmData table)
- **AWS Lambda**: Serverless compute for analysis processing

### Data Flow

```
User Input (Image/Test Data)
    ↓
Lambda Handler / Tools
    ↓
Image Validation & Compression
    ↓
Amazon Bedrock Analysis
    ↓
Result Parsing & Structuring
    ↓
S3 Storage (Images) + DynamoDB (Results)
    ↓
Return Structured Analysis
```

## Usage

### 1. Image-Based Analysis

```python
from tools.soil_analysis_tools import SoilAnalysisTools

# Initialize tools
soil_tools = SoilAnalysisTools(region='us-east-1')

# Analyze soil from image
with open('soil_sample.jpg', 'rb') as f:
    image_data = f.read()

result = soil_tools.analyze_soil_from_image(
    image_data=image_data,
    user_id='farmer_123',
    farm_id='farm_456',
    location={
        'state': 'Karnataka',
        'district': 'Bangalore'
    }
)

print(f"Soil Type: {result['soil_type']}")
print(f"Fertility: {result['fertility_level']}")
print(f"pH Level: {result['ph_level']}")
print(f"Deficiencies: {result['deficiencies']}")
print(f"Suitable Crops: {result['suitable_crops']}")
```

### 2. Test Data Analysis

```python
# Analyze soil from test data
test_data = {
    'ph': 6.5,
    'nitrogen': 'low',
    'phosphorus': 'medium',
    'potassium': 'high',
    'organic_matter': 2.5,
    'texture': 'loam'
}

result = soil_tools.analyze_soil_from_test_data(
    test_data=test_data,
    user_id='farmer_123',
    farm_id='farm_456',
    location={
        'state': 'Karnataka',
        'district': 'Bangalore'
    }
)

print(f"Analysis: {result['full_analysis']}")
```

### 3. Crop Recommendations

```python
# Get crop recommendations based on soil conditions
recommendations = soil_tools.get_crop_recommendations(
    soil_type='loam',
    fertility_level='medium',
    location={
        'state': 'Karnataka',
        'district': 'Bangalore'
    },
    climate_data={
        'rainfall': 800,  # mm per year
        'temperature_range': [15, 35]  # Celsius
    }
)

print(f"Highly Suitable: {recommendations['highly_suitable_crops']}")
print(f"Moderately Suitable: {recommendations['moderately_suitable_crops']}")
```

### 4. Deficiency Report

```python
# Generate detailed deficiency report
report = soil_tools.generate_deficiency_report(
    deficiencies=['Nitrogen deficiency', 'Low organic matter'],
    soil_type='loam',
    location={
        'state': 'Karnataka',
        'district': 'Bangalore'
    }
)

print(report['report'])
```

## Lambda Function Usage

### API Gateway Event Format

```json
{
  "body": {
    "analysis_type": "image",
    "image_data": "base64_encoded_image_data",
    "user_id": "farmer_1234567890",
    "farm_id": "farm_abc123",
    "location": {
      "state": "Karnataka",
      "district": "Bangalore"
    },
    "language_code": "hi"
  }
}
```

### Response Format

```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "analysis_id": "soil_abc123def456",
    "s3_key": "images/soil-samples/farmer_123/soil_abc123def456.jpg",
    "soil_type": "loam",
    "fertility_level": "medium",
    "ph_level": 6.5,
    "npk_levels": {
      "nitrogen": "low",
      "phosphorus": "medium",
      "potassium": "high"
    },
    "organic_matter": 2.5,
    "deficiencies": [
      "Nitrogen deficiency",
      "Low organic matter content"
    ],
    "suitable_crops": [
      "Wheat",
      "Rice",
      "Maize",
      "Cotton",
      "Sugarcane"
    ],
    "recommendations": {
      "organic_amendments": [
        "Compost application",
        "Organic manure"
      ],
      "chemical_amendments": [
        "Chemical fertilizer - see full analysis"
      ],
      "water_management": [],
      "soil_improvement": []
    },
    "full_analysis": "Detailed analysis text...",
    "timestamp": 1234567890
  }
}
```

## Image Requirements

### Optimal Image Quality
- **Resolution**: Minimum 300x300 pixels, recommended 800x600 or higher
- **Format**: JPEG or PNG
- **Size**: Maximum 5MB
- **Lighting**: Natural daylight, avoid harsh shadows
- **Focus**: Clear, sharp image of soil sample
- **Angle**: Top-down view of soil surface

### Image Capture Tips
1. Take photos during daytime with good natural light
2. Avoid direct sunlight - use diffused light or shade
3. Ensure soil sample is clean and representative
4. Include a reference object for scale (optional)
5. Capture different angles if possible
6. Avoid blurry or overexposed images

## Soil Test Data Format

### Supported Parameters

```python
{
    # Required
    'ph': 6.5,  # pH value (4.0-9.0)
    
    # NPK Levels (can be numeric or categorical)
    'nitrogen': 'low',  # or numeric value in kg/ha
    'phosphorus': 'medium',  # or numeric value in kg/ha
    'potassium': 'high',  # or numeric value in kg/ha
    
    # Optional
    'organic_matter': 2.5,  # percentage
    'texture': 'loam',  # soil texture
    'electrical_conductivity': 0.5,  # dS/m
    'calcium': 'medium',
    'magnesium': 'medium',
    'sulfur': 'low',
    'zinc': 'low',
    'iron': 'medium',
    'manganese': 'medium',
    'copper': 'low',
    'boron': 'low'
}
```

## Crop Suitability Matrix

### Soil Type Preferences

| Crop | Clay | Loam | Sandy | Silt | pH Range |
|------|------|------|-------|------|----------|
| Wheat | ✓ | ✓✓✓ | ✓ | ✓✓ | 6.0-7.5 |
| Rice | ✓✓✓ | ✓✓ | ✗ | ✓✓ | 5.5-7.0 |
| Maize | ✓ | ✓✓✓ | ✓✓ | ✓✓ | 5.5-7.5 |
| Cotton | ✓✓ | ✓✓✓ | ✓ | ✓✓ | 6.0-8.0 |
| Sugarcane | ✓✓ | ✓✓✓ | ✓ | ✓✓ | 6.0-7.5 |
| Pulses | ✓ | ✓✓✓ | ✓✓ | ✓✓ | 6.0-7.5 |
| Vegetables | ✓✓ | ✓✓✓ | ✓ | ✓✓ | 6.0-7.0 |

✓✓✓ = Highly Suitable, ✓✓ = Suitable, ✓ = Moderately Suitable, ✗ = Not Suitable

## Amendment Guidelines

### Organic Amendments

1. **Compost**
   - Application Rate: 5-10 tons per acre
   - Benefits: Improves soil structure, adds nutrients, increases water retention
   - Cost: ₹10,000-20,000 per acre
   - Application: Spread evenly and incorporate into top 6 inches

2. **Farmyard Manure (FYM)**
   - Application Rate: 10-15 tons per acre
   - Benefits: Rich in NPK, improves soil biology
   - Cost: ₹8,000-15,000 per acre
   - Application: Apply 2-3 weeks before planting

3. **Vermicompost**
   - Application Rate: 2-3 tons per acre
   - Benefits: High nutrient content, excellent soil conditioner
   - Cost: ₹15,000-25,000 per acre
   - Application: Mix with soil or use as top dressing

4. **Green Manure**
   - Crops: Dhaincha, Sunhemp, Cowpea
   - Benefits: Adds nitrogen, improves soil structure
   - Cost: ₹2,000-5,000 per acre (seeds)
   - Application: Grow for 45-60 days, then incorporate

### Chemical Amendments

1. **Nitrogen Deficiency**
   - Urea (46% N): 100-150 kg per acre
   - DAP (18% N): 150-200 kg per acre
   - Cost: ₹2,000-4,000 per acre

2. **Phosphorus Deficiency**
   - Single Super Phosphate (16% P): 200-250 kg per acre
   - DAP (46% P): 100-150 kg per acre
   - Cost: ₹3,000-5,000 per acre

3. **Potassium Deficiency**
   - Muriate of Potash (60% K): 50-100 kg per acre
   - Cost: ₹1,500-3,000 per acre

4. **pH Correction**
   - For Acidic Soil: Agricultural Lime 500-1000 kg per acre
   - For Alkaline Soil: Gypsum 500-1000 kg per acre
   - Cost: ₹2,000-5,000 per acre

## Best Practices

### Soil Sampling
1. Collect samples from multiple locations (5-10 spots per acre)
2. Sample depth: 0-6 inches for most crops
3. Avoid sampling near roads, buildings, or compost piles
4. Mix samples thoroughly before testing
5. Use clean, non-contaminated containers

### Timing
1. **Soil Testing**: Before planting season (2-3 months in advance)
2. **Organic Amendments**: 4-6 weeks before planting
3. **Chemical Fertilizers**: Split application - basal + top dressing
4. **pH Correction**: 3-6 months before planting

### Monitoring
1. Retest soil every 2-3 years
2. Monitor crop health and growth
3. Track yield improvements
4. Adjust amendments based on results
5. Keep records of all applications

## Integration with RISE System

### Agent Integration

The soil analysis tools integrate seamlessly with the RISE agent system:

```python
# In agent code
from tools.soil_analysis_tools import analyze_soil_image, analyze_soil_test_data

# Use as agent tools
@tool
def analyze_farmer_soil(image_path: str, user_id: str, farm_id: str):
    """Analyze soil from farmer's image"""
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    return analyze_soil_image(image_data, user_id, farm_id)
```

### Workflow Integration

1. **Farmer uploads soil image** → Image analysis
2. **Analysis results** → Crop recommendations
3. **Deficiencies identified** → Amendment recommendations
4. **Recommendations provided** → Implementation guidance
5. **Follow-up** → Monitor improvements and retest

## Error Handling

### Common Errors

1. **Invalid Image**: Image too small, corrupted, or wrong format
   - Solution: Provide clear guidance on image requirements

2. **Analysis Failure**: Bedrock API error or timeout
   - Solution: Retry with exponential backoff

3. **Storage Error**: S3 or DynamoDB unavailable
   - Solution: Queue for later processing

4. **Invalid Test Data**: Missing required parameters
   - Solution: Validate input and provide clear error messages

## Performance Considerations

- **Image Compression**: Automatic compression to <500KB
- **Caching**: Cache common soil type recommendations
- **Batch Processing**: Support batch analysis for multiple samples
- **Async Processing**: Use Lambda for scalable processing

## Security

- **Data Encryption**: All data encrypted at rest and in transit
- **Access Control**: IAM roles for Lambda and service access
- **Privacy**: Farmer data isolated by user_id and farm_id
- **Audit Logging**: All analyses logged for traceability

## Cost Optimization

- **Image Compression**: Reduces S3 storage costs
- **DynamoDB On-Demand**: Pay only for actual usage
- **Lambda Optimization**: Efficient code reduces execution time
- **Bedrock Caching**: Cache common analysis patterns

## Future Enhancements

1. **IoT Integration**: Real-time soil sensor data
2. **Historical Tracking**: Track soil health over time
3. **Predictive Analytics**: Predict future soil conditions
4. **Mobile App**: Dedicated mobile interface
5. **Offline Mode**: Basic analysis without internet
6. **Multi-language**: Support for all Indian languages
7. **Expert Consultation**: Connect with soil scientists
8. **Precision Agriculture**: GPS-tagged soil maps

## Support

For issues or questions:
- Check the test suite for usage examples
- Review the Lambda logs in CloudWatch
- Contact the RISE development team

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) project.
