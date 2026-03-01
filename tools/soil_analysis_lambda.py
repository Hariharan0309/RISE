"""
AWS Lambda Function for Soil Analysis
Handles soil image analysis and test data parsing using Amazon Bedrock
"""

import json
import boto3
import base64
import uuid
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

# Configuration from environment variables
S3_BUCKET = os.environ.get('S3_BUCKET', 'rise-application-data')
FARM_DATA_TABLE = os.environ.get('FARM_DATA_TABLE', 'RISE-FarmData')
MAX_IMAGE_SIZE = int(os.environ.get('MAX_IMAGE_SIZE', 5 * 1024 * 1024))  # 5MB
BEDROCK_MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'

# DynamoDB table
farm_data_table = dynamodb.Table(FARM_DATA_TABLE)


def lambda_handler(event, context):
    """
    Lambda handler for soil analysis
    
    Expected event structure:
    {
        "body": {
            "analysis_type": "image" | "test_data",
            "image_data": "base64_encoded_image",  # For image analysis
            "test_data": {...},  # For manual test data
            "user_id": "farmer_1234567890",
            "farm_id": "farm_abc123",
            "location": {"state": "...", "district": "..."},
            "language_code": "hi"
        }
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "success": true,
            "analysis_id": "soil_abc123",
            "soil_type": "loam",
            "fertility_level": "medium",
            "ph_level": 6.5,
            "npk_levels": {...},
            "deficiencies": [...],
            "recommendations": {...}
        }
    }
    """
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract parameters
        analysis_type = body.get('analysis_type', 'image')
        user_id = body.get('user_id')
        farm_id = body.get('farm_id')
        location = body.get('location', {})
        language_code = body.get('language_code', 'en')
        
        # Validate required fields
        if not user_id:
            return create_response(400, {
                'success': False,
                'error': 'Missing user_id in request'
            })
        
        if not farm_id:
            return create_response(400, {
                'success': False,
                'error': 'Missing farm_id in request'
            })
        
        # Generate analysis ID
        analysis_id = f"soil_{uuid.uuid4().hex[:12]}"
        timestamp = int(datetime.now().timestamp())
        
        # Process based on analysis type
        if analysis_type == 'image':
            image_data_base64 = body.get('image_data')
            
            if not image_data_base64:
                return create_response(400, {
                    'success': False,
                    'error': 'Missing image_data for image analysis'
                })
            
            # Decode base64 image
            try:
                image_bytes = base64.b64decode(image_data_base64)
            except Exception as e:
                logger.error(f"Base64 decode error: {e}")
                return create_response(400, {
                    'success': False,
                    'error': 'Invalid base64 image data'
                })
            
            # Validate image size
            image_size = len(image_bytes)
            if image_size > MAX_IMAGE_SIZE:
                return create_response(400, {
                    'success': False,
                    'error': f'Image size ({image_size} bytes) exceeds maximum ({MAX_IMAGE_SIZE} bytes)'
                })
            
            if image_size == 0:
                return create_response(400, {
                    'success': False,
                    'error': 'Empty image file'
                })
            
            # Store image in S3
            s3_key = f"images/soil-samples/{user_id}/{analysis_id}.jpg"
            
            try:
                s3_client.put_object(
                    Bucket=S3_BUCKET,
                    Key=s3_key,
                    Body=image_bytes,
                    ContentType='image/jpeg',
                    Metadata={
                        'user_id': user_id,
                        'farm_id': farm_id,
                        'analysis_id': analysis_id,
                        'timestamp': str(timestamp)
                    }
                )
                logger.info(f"Soil image uploaded to S3: {s3_key}")
            except Exception as e:
                logger.error(f"S3 upload error: {e}")
                return create_response(500, {
                    'success': False,
                    'error': f'Failed to upload image: {str(e)}'
                })
            
            # Analyze image with Bedrock
            analysis_result = analyze_soil_from_image(
                image_bytes=image_bytes,
                location=location,
                language_code=language_code
            )
        
        elif analysis_type == 'test_data':
            test_data = body.get('test_data')
            
            if not test_data:
                return create_response(400, {
                    'success': False,
                    'error': 'Missing test_data for test data analysis'
                })
            
            # Parse and analyze test data
            analysis_result = analyze_soil_from_test_data(
                test_data=test_data,
                location=location,
                language_code=language_code
            )
            
            s3_key = None
        
        else:
            return create_response(400, {
                'success': False,
                'error': f'Invalid analysis_type: {analysis_type}'
            })
        
        if not analysis_result['success']:
            return create_response(500, {
                'success': False,
                'error': analysis_result.get('error', 'Analysis failed')
            })
        
        # Store analysis in DynamoDB
        store_soil_analysis(
            analysis_id=analysis_id,
            farm_id=farm_id,
            user_id=user_id,
            s3_key=s3_key,
            analysis=analysis_result,
            location=location,
            timestamp=timestamp
        )
        
        # Return results
        return create_response(200, {
            'success': True,
            'analysis_id': analysis_id,
            's3_key': s3_key,
            'soil_type': analysis_result.get('soil_type', 'unknown'),
            'fertility_level': analysis_result.get('fertility_level', 'unknown'),
            'ph_level': analysis_result.get('ph_level'),
            'npk_levels': analysis_result.get('npk_levels', {}),
            'organic_matter': analysis_result.get('organic_matter'),
            'deficiencies': analysis_result.get('deficiencies', []),
            'recommendations': analysis_result.get('recommendations', {}),
            'suitable_crops': analysis_result.get('suitable_crops', []),
            'full_analysis': analysis_result.get('full_analysis', ''),
            'timestamp': timestamp
        })
    
    except Exception as e:
        logger.error(f"Lambda handler error: {e}", exc_info=True)
        return create_response(500, {
            'success': False,
            'error': f'Internal server error: {str(e)}'
        })


def analyze_soil_from_image(image_bytes: bytes,
                            location: Dict[str, str],
                            language_code: str) -> Dict[str, Any]:
    """Analyze soil from image using Amazon Bedrock multimodal"""
    
    try:
        # Encode image to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Build prompt
        prompt = build_soil_image_analysis_prompt(location, language_code)
        
        # Call Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 2500,
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'image',
                                'source': {
                                    'type': 'base64',
                                    'media_type': 'image/jpeg',
                                    'data': image_base64
                                }
                            },
                            {
                                'type': 'text',
                                'text': prompt
                            }
                        ]
                    }
                ],
                'temperature': 0.3
            })
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        analysis_text = response_body['content'][0]['text']
        
        # Parse structured analysis
        analysis = parse_soil_analysis(analysis_text)
        
        return {
            'success': True,
            **analysis
        }
    
    except Exception as e:
        logger.error(f"Bedrock soil image analysis error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def analyze_soil_from_test_data(test_data: Dict[str, Any],
                                location: Dict[str, str],
                                language_code: str) -> Dict[str, Any]:
    """Analyze soil from manual test data using Amazon Bedrock"""
    
    try:
        # Build prompt with test data
        prompt = build_soil_test_data_prompt(test_data, location, language_code)
        
        # Call Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 2500,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.3
            })
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        analysis_text = response_body['content'][0]['text']
        
        # Parse structured analysis
        analysis = parse_soil_analysis(analysis_text)
        
        # Merge test data into analysis
        analysis['test_data_provided'] = test_data
        
        return {
            'success': True,
            **analysis
        }
    
    except Exception as e:
        logger.error(f"Bedrock soil test data analysis error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def build_soil_image_analysis_prompt(location: Dict[str, str], language_code: str) -> str:
    """Build prompt for soil image analysis"""
    
    prompt = """You are an expert soil scientist specializing in agricultural soil analysis.
Analyze this soil sample image and provide a comprehensive assessment.

"""
    
    if location:
        prompt += f"Location: {location.get('state', 'Unknown')}, {location.get('district', 'Unknown')}\n"
    
    prompt += """
Provide your analysis in the following structured format:

1. SOIL TYPE CLASSIFICATION:
   - Primary Type: [clay/loam/sandy/silt/peat/chalky]
   - Texture: [description]
   - Color: [description and what it indicates]
   - Structure: [description]

2. FERTILITY ASSESSMENT:
   - Overall Fertility Level: [low/medium/high]
   - Visual Indicators: [what you observe]
   - Estimated Organic Matter: [percentage if possible]

3. ESTIMATED NPK LEVELS:
   - Nitrogen (N): [low/medium/high]
   - Phosphorus (P): [low/medium/high]
   - Potassium (K): [low/medium/high]
   - Rationale: [explain visual indicators]

4. pH ESTIMATION:
   - Estimated pH: [range, e.g., 6.0-7.0]
   - Acidity/Alkalinity: [acidic/neutral/alkaline]
   - Visual Indicators: [color, vegetation if visible]

5. DEFICIENCIES IDENTIFIED:
   - List any visible nutrient deficiencies
   - Signs of poor drainage or compaction
   - Other issues observed

6. AMENDMENT RECOMMENDATIONS:
   For each deficiency:
   - Organic Amendments: [compost, manure, etc. with quantities per acre]
   - Chemical Amendments: [specific fertilizers with NPK ratios and quantities]
   - Application Method: [how to apply]
   - Timing: [when to apply]

7. SUITABLE CROPS:
   - Highly Suitable: [list crops]
   - Moderately Suitable: [list crops]
   - Not Recommended: [list crops and why]

8. SOIL IMPROVEMENT PLAN:
   - Short-term actions (1-3 months)
   - Medium-term actions (3-6 months)
   - Long-term actions (6-12 months)

9. ADDITIONAL RECOMMENDATIONS:
   - Water management advice
   - Tillage recommendations
   - Cover crop suggestions
   - Soil testing recommendations

Note: This is a visual assessment. For precise nutrient levels, recommend laboratory soil testing.
"""
    
    return prompt


def build_soil_test_data_prompt(test_data: Dict[str, Any],
                                location: Dict[str, str],
                                language_code: str) -> str:
    """Build prompt for soil test data analysis"""
    
    prompt = """You are an expert soil scientist specializing in agricultural soil analysis.
Analyze the following soil test data and provide comprehensive recommendations.

"""
    
    if location:
        prompt += f"Location: {location.get('state', 'Unknown')}, {location.get('district', 'Unknown')}\n"
    
    prompt += f"""
SOIL TEST DATA:
{json.dumps(test_data, indent=2)}

Provide your analysis in the following structured format:

1. SOIL TYPE CLASSIFICATION:
   - Primary Type: [based on texture data if available]
   - Characteristics: [description]

2. FERTILITY ASSESSMENT:
   - Overall Fertility Level: [low/medium/high]
   - Analysis: [detailed assessment]

3. NPK LEVELS ANALYSIS:
   - Nitrogen (N): [value and status]
   - Phosphorus (P): [value and status]
   - Potassium (K): [value and status]
   - Interpretation: [what these levels mean]

4. pH ANALYSIS:
   - pH Value: [from test data]
   - Status: [acidic/neutral/alkaline]
   - Impact: [how this affects crop growth]

5. DEFICIENCIES IDENTIFIED:
   - List all nutrient deficiencies
   - Severity of each deficiency
   - Impact on crop production

6. AMENDMENT RECOMMENDATIONS:
   For each deficiency:
   - Organic Amendments: [specific types with quantities per acre]
   - Chemical Amendments: [specific fertilizers with NPK ratios and quantities]
   - Application Method: [detailed instructions]
   - Timing: [optimal application schedule]
   - Expected Results: [timeline for improvement]

7. SUITABLE CROPS:
   Based on current soil conditions:
   - Highly Suitable: [list crops with expected yields]
   - Moderately Suitable: [list crops with amendments needed]
   - Not Recommended: [list crops and reasons]

8. SOIL IMPROVEMENT PLAN:
   - Immediate Actions: [0-1 month]
   - Short-term Actions: [1-3 months]
   - Medium-term Actions: [3-6 months]
   - Long-term Actions: [6-12 months]

9. COST-BENEFIT ANALYSIS:
   - Estimated amendment costs
   - Expected yield improvements
   - Return on investment timeline

10. MONITORING RECOMMENDATIONS:
    - When to retest soil
    - Parameters to monitor
    - Success indicators

Provide specific, actionable recommendations with quantities and costs where possible.
"""
    
    return prompt


def parse_soil_analysis(analysis_text: str) -> Dict[str, Any]:
    """Parse soil analysis from AI response"""
    
    soil_type = 'unknown'
    fertility_level = 'medium'
    ph_level = None
    npk_levels = {}
    organic_matter = None
    deficiencies = []
    suitable_crops = []
    
    # Parse key information from response
    lines = analysis_text.split('\n')
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        
        # Extract soil type
        if 'primary type:' in line_lower:
            soil_type = line.split(':', 1)[1].strip().lower()
            # Extract just the type name
            for soil_name in ['clay', 'loam', 'sandy', 'silt', 'peat', 'chalky']:
                if soil_name in soil_type:
                    soil_type = soil_name
                    break
        
        # Extract fertility level
        if 'fertility level:' in line_lower or 'overall fertility:' in line_lower:
            fertility_str = line.split(':', 1)[1].strip().lower()
            if 'low' in fertility_str:
                fertility_level = 'low'
            elif 'high' in fertility_str:
                fertility_level = 'high'
            else:
                fertility_level = 'medium'
        
        # Extract pH
        if 'ph' in line_lower and ':' in line:
            try:
                ph_str = line.split(':', 1)[1].strip()
                # Extract numeric pH value
                import re
                ph_match = re.search(r'(\d+\.?\d*)', ph_str)
                if ph_match:
                    ph_level = float(ph_match.group(1))
            except:
                pass
        
        # Extract NPK levels
        if 'nitrogen' in line_lower and ':' in line:
            npk_levels['nitrogen'] = extract_nutrient_level(line)
        if 'phosphorus' in line_lower and ':' in line:
            npk_levels['phosphorus'] = extract_nutrient_level(line)
        if 'potassium' in line_lower and ':' in line:
            npk_levels['potassium'] = extract_nutrient_level(line)
        
        # Extract organic matter
        if 'organic matter' in line_lower and ':' in line:
            try:
                om_str = line.split(':', 1)[1].strip()
                import re
                om_match = re.search(r'(\d+\.?\d*)', om_str)
                if om_match:
                    organic_matter = float(om_match.group(1))
            except:
                pass
        
        # Extract deficiencies
        if 'deficiencies identified' in line_lower:
            # Look at next few lines for deficiency list
            for j in range(i+1, min(i+10, len(lines))):
                if lines[j].strip().startswith('-'):
                    deficiency = lines[j].strip()[1:].strip()
                    if deficiency and len(deficiency) > 3:
                        deficiencies.append(deficiency)
        
        # Extract suitable crops
        if 'highly suitable:' in line_lower:
            crops_str = line.split(':', 1)[1].strip()
            crops = [c.strip() for c in crops_str.split(',') if c.strip()]
            suitable_crops.extend(crops)
    
    # Extract recommendations
    recommendations = extract_recommendations(analysis_text)
    
    return {
        'soil_type': soil_type,
        'fertility_level': fertility_level,
        'ph_level': ph_level,
        'npk_levels': npk_levels,
        'organic_matter': organic_matter,
        'deficiencies': deficiencies,
        'suitable_crops': suitable_crops,
        'recommendations': recommendations,
        'full_analysis': analysis_text
    }


def extract_nutrient_level(line: str) -> str:
    """Extract nutrient level from line"""
    line_lower = line.lower()
    
    if 'low' in line_lower:
        return 'low'
    elif 'high' in line_lower:
        return 'high'
    elif 'medium' in line_lower or 'moderate' in line_lower:
        return 'medium'
    else:
        return 'unknown'


def extract_recommendations(analysis_text: str) -> Dict[str, Any]:
    """Extract recommendations from analysis"""
    
    recommendations = {
        'organic_amendments': [],
        'chemical_amendments': [],
        'water_management': [],
        'soil_improvement': []
    }
    
    # Simplified extraction - in production, use more sophisticated parsing
    if 'compost' in analysis_text.lower():
        recommendations['organic_amendments'].append('Compost application recommended')
    
    if 'manure' in analysis_text.lower():
        recommendations['organic_amendments'].append('Organic manure recommended')
    
    if 'fertilizer' in analysis_text.lower() or 'npk' in analysis_text.lower():
        recommendations['chemical_amendments'].append('Chemical fertilizer application recommended - see full analysis')
    
    return recommendations


def store_soil_analysis(analysis_id: str,
                       farm_id: str,
                       user_id: str,
                       s3_key: Optional[str],
                       analysis: Dict[str, Any],
                       location: Dict[str, str],
                       timestamp: int) -> None:
    """Store soil analysis in DynamoDB"""
    
    try:
        item = {
            'farm_id': farm_id,
            'timestamp': timestamp,
            'analysis_id': analysis_id,
            'user_id': user_id,
            'data_type': 'soil_analysis',
            'soil_analysis': {
                'soil_type': analysis.get('soil_type', 'unknown'),
                'fertility_level': analysis.get('fertility_level', 'unknown'),
                'ph_level': analysis.get('ph_level'),
                'npk_levels': analysis.get('npk_levels', {}),
                'organic_matter': analysis.get('organic_matter'),
                'deficiencies': analysis.get('deficiencies', []),
                'suitable_crops': analysis.get('suitable_crops', []),
                'recommendations': analysis.get('recommendations', {}),
                'full_analysis': analysis.get('full_analysis', '')
            },
            'location': location,
            'image_s3_key': s3_key
        }
        
        farm_data_table.put_item(Item=item)
        logger.info(f"Soil analysis stored: {analysis_id}")
    
    except Exception as e:
        logger.error(f"Error storing soil analysis: {e}")


def create_response(status_code: int, body: dict) -> dict:
    """Create Lambda response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        },
        'body': json.dumps(body)
    }


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'body': json.dumps({
            'analysis_type': 'test_data',
            'test_data': {
                'ph': 6.5,
                'nitrogen': 'low',
                'phosphorus': 'medium',
                'potassium': 'high',
                'organic_matter': 2.5
            },
            'user_id': 'test_farmer_001',
            'farm_id': 'farm_test_001',
            'location': {'state': 'Karnataka', 'district': 'Bangalore'},
            'language_code': 'en'
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
