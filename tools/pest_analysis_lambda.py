"""
AWS Lambda Function for Pest Image Analysis
Handles image upload and pest identification using Amazon Bedrock
"""

import json
import boto3
import base64
import uuid
import logging
import os
from datetime import datetime
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

# Configuration from environment variables
S3_BUCKET = os.environ.get('S3_BUCKET', 'rise-application-data')
PEST_DIAGNOSIS_TABLE = os.environ.get('PEST_DIAGNOSIS_TABLE', 'RISE-PestDiagnosisHistory')
MAX_IMAGE_SIZE = int(os.environ.get('MAX_IMAGE_SIZE', 5 * 1024 * 1024))  # 5MB
BEDROCK_MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'

# DynamoDB table
pest_diagnosis_table = dynamodb.Table(PEST_DIAGNOSIS_TABLE)


def lambda_handler(event, context):
    """
    Lambda handler for pest image analysis
    
    Expected event structure:
    {
        "body": {
            "image_data": "base64_encoded_image",
            "user_id": "farmer_1234567890",
            "crop_type": "wheat",
            "additional_context": "Small insects on leaves",
            "language_code": "hi"
        }
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "success": true,
            "diagnosis_id": "pest_abc123",
            "pests": ["Aphids"],
            "confidence_score": 0.85,
            "severity": "medium",
            "lifecycle_stage": "adult",
            "population_density": "high",
            "full_analysis": "...",
            "biological_controls": [...],
            "chemical_treatments": [...]
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
        image_data_base64 = body.get('image_data')
        user_id = body.get('user_id')
        crop_type = body.get('crop_type')
        additional_context = body.get('additional_context')
        language_code = body.get('language_code', 'en')
        
        # Validate required fields
        if not image_data_base64:
            return create_response(400, {
                'success': False,
                'error': 'Missing image_data in request'
            })
        
        if not user_id:
            return create_response(400, {
                'success': False,
                'error': 'Missing user_id in request'
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
        
        # Validate image quality
        quality_check = validate_image_quality(image_bytes)
        if not quality_check['valid']:
            return create_response(400, {
                'success': False,
                'error': 'poor_image_quality',
                'validation': quality_check
            })
        
        # Generate diagnosis ID
        diagnosis_id = f"pest_{uuid.uuid4().hex[:12]}"
        timestamp = int(datetime.now().timestamp())
        
        # Store image in S3
        s3_key = f"images/pest-photos/{user_id}/{diagnosis_id}.jpg"
        
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=image_bytes,
                ContentType='image/jpeg',
                Metadata={
                    'user_id': user_id,
                    'diagnosis_id': diagnosis_id,
                    'crop_type': crop_type or 'unknown',
                    'timestamp': str(timestamp)
                }
            )
            logger.info(f"Image uploaded to S3: {s3_key}")
        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            return create_response(500, {
                'success': False,
                'error': f'Failed to upload image: {str(e)}'
            })
        
        # Analyze image with Bedrock
        try:
            analysis_result = analyze_with_bedrock(
                image_bytes=image_bytes,
                crop_type=crop_type,
                additional_context=additional_context,
                language_code=language_code
            )
            
            if not analysis_result['success']:
                return create_response(500, {
                    'success': False,
                    'error': analysis_result.get('error', 'Analysis failed')
                })
            
            # Store diagnosis in DynamoDB
            store_pest_diagnosis(
                diagnosis_id=diagnosis_id,
                user_id=user_id,
                s3_key=s3_key,
                analysis=analysis_result,
                crop_type=crop_type,
                timestamp=timestamp
            )
            
            # Return results
            return create_response(200, {
                'success': True,
                'diagnosis_id': diagnosis_id,
                's3_key': s3_key,
                'pests': analysis_result.get('pests', []),
                'confidence_score': analysis_result.get('confidence_score', 0.0),
                'severity': analysis_result.get('severity', 'unknown'),
                'lifecycle_stage': analysis_result.get('lifecycle_stage', 'unknown'),
                'population_density': analysis_result.get('population_density', 'unknown'),
                'full_analysis': analysis_result.get('full_analysis', ''),
                'biological_controls': analysis_result.get('biological_controls', []),
                'cultural_controls': analysis_result.get('cultural_controls', []),
                'chemical_treatments': analysis_result.get('chemical_treatments', []),
                'preventive_measures': analysis_result.get('preventive_measures', []),
                'multiple_pests': analysis_result.get('multiple_pests', False),
                'timestamp': timestamp
            })
        
        except Exception as e:
            logger.error(f"Bedrock analysis error: {e}", exc_info=True)
            return create_response(500, {
                'success': False,
                'error': f'Analysis failed: {str(e)}'
            })
    
    except Exception as e:
        logger.error(f"Lambda handler error: {e}", exc_info=True)
        return create_response(500, {
            'success': False,
            'error': f'Internal server error: {str(e)}'
        })


def validate_image_quality(image_bytes: bytes) -> Dict[str, Any]:
    """Validate image quality"""
    try:
        from PIL import Image
        import io
        
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        
        issues = []
        guidance = []
        
        # Check resolution
        if width < 300 or height < 300:
            issues.append('low_resolution')
            guidance.append('Take a higher resolution photo (at least 300x300 pixels)')
        
        # Check aspect ratio
        aspect_ratio = width / height
        if aspect_ratio > 3 or aspect_ratio < 0.33:
            issues.append('unusual_aspect_ratio')
            guidance.append('Try to capture the pest in a more balanced frame')
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'guidance': guidance,
            'dimensions': {'width': width, 'height': height}
        }
    
    except Exception as e:
        logger.error(f"Image validation error: {e}")
        return {
            'valid': False,
            'issues': ['invalid_image'],
            'guidance': ['Unable to read image. Please upload a valid JPEG or PNG image']
        }


def analyze_with_bedrock(image_bytes: bytes,
                        crop_type: str,
                        additional_context: str,
                        language_code: str) -> Dict[str, Any]:
    """Analyze image using Amazon Bedrock multimodal"""
    
    try:
        # Encode image to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Build prompt
        prompt = build_pest_prompt(crop_type, additional_context, language_code)
        
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
        
        # Parse structured diagnosis
        diagnosis = parse_pest_diagnosis(analysis_text)
        
        return {
            'success': True,
            **diagnosis
        }
    
    except Exception as e:
        logger.error(f"Bedrock analysis error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def build_pest_prompt(crop_type: str, additional_context: str, language_code: str) -> str:
    """Build pest identification prompt"""
    
    prompt = """You are an expert agricultural entomologist. Analyze this image and provide a detailed pest diagnosis with integrated pest management recommendations.

"""
    
    if crop_type:
        prompt += f"Crop Type: {crop_type}\n"
    
    if additional_context:
        prompt += f"Farmer's Observation: {additional_context}\n"
    
    prompt += """
Provide your analysis in this format:

1. PESTS IDENTIFIED:
   - Pest Species: [common and scientific name]
   - Confidence: [percentage]
   - Lifecycle Stage: [egg/larva/pupa/nymph/adult]
   - Population Density: [low/medium/high]
   - Severity: [low/medium/high/critical]

2. INTEGRATED PEST MANAGEMENT (IPM) RECOMMENDATIONS:
   
   A. BIOLOGICAL CONTROLS (Priority 1):
      - Natural predators and beneficial insects
      - Biological pesticides (Bt, neem, etc.)
   
   B. CULTURAL CONTROLS (Priority 2):
      - Crop rotation, sanitation, trap crops
   
   C. CHEMICAL TREATMENTS (Last Resort):
      - Pesticide Name: [specific product]
      - Dosage: [exact amount per liter/hectare]
      - Application Timing: [when to apply]
      - Safety Precautions: [PPE, handling]
      - Pre-Harvest Interval: [days]

3. LIFECYCLE AND TIMING:
   - Current stage implications
   - Optimal timing for control

4. PREVENTIVE MEASURES:
   - Prevention steps for future

Prioritize biological and cultural controls over chemical treatments.
"""
    
    return prompt


def parse_pest_diagnosis(analysis_text: str) -> Dict[str, Any]:
    """Parse pest diagnosis from AI response"""
    
    pests = []
    confidence_score = 0.75
    severity = 'medium'
    lifecycle_stage = 'unknown'
    population_density = 'unknown'
    
    # Simple parsing - extract key information
    lines = analysis_text.split('\n')
    
    for line in lines:
        line_lower = line.lower().strip()
        
        if 'pest species:' in line_lower:
            pest_name = line.split(':', 1)[1].strip()
            pests.append(pest_name)
        
        if 'confidence:' in line_lower:
            try:
                conf_str = line.split(':', 1)[1].strip().replace('%', '')
                confidence_score = float(conf_str) / 100
            except:
                pass
        
        if 'lifecycle stage:' in line_lower:
            stage_str = line.split(':', 1)[1].strip().lower()
            lifecycle_stage = stage_str
        
        if 'population density:' in line_lower:
            density_str = line.split(':', 1)[1].strip().lower()
            if density_str in ['low', 'medium', 'high']:
                population_density = density_str
        
        if 'severity:' in line_lower:
            severity_str = line.split(':', 1)[1].strip().lower()
            if severity_str in ['low', 'medium', 'high', 'critical']:
                severity = severity_str
    
    # If no pests found, assume no infestation
    if not pests or 'none' in analysis_text.lower()[:200]:
        pests = ['No pests detected']
        severity = 'low'
        confidence_score = 0.9
        lifecycle_stage = 'N/A'
        population_density = 'none'
    
    return {
        'pests': pests,
        'confidence_score': confidence_score,
        'severity': severity,
        'lifecycle_stage': lifecycle_stage,
        'population_density': population_density,
        'full_analysis': analysis_text,
        'multiple_pests': len(pests) > 1,
        'biological_controls': extract_biological_controls(analysis_text),
        'cultural_controls': extract_cultural_controls(analysis_text),
        'chemical_treatments': extract_chemical_treatments(analysis_text),
        'preventive_measures': extract_prevention(analysis_text)
    }


def extract_biological_controls(analysis_text: str) -> list:
    """Extract biological control recommendations"""
    controls = []
    
    if 'biological controls' in analysis_text.lower() or 'natural predators' in analysis_text.lower():
        controls.append({
            'type': 'biological',
            'description': 'Biological control methods recommended - see full analysis'
        })
    
    if 'neem' in analysis_text.lower() or 'bt' in analysis_text.lower():
        controls.append({
            'type': 'biopesticide',
            'description': 'Biological pesticides available - see full analysis'
        })
    
    return controls


def extract_cultural_controls(analysis_text: str) -> list:
    """Extract cultural control recommendations"""
    controls = []
    
    if 'crop rotation' in analysis_text.lower() or 'sanitation' in analysis_text.lower():
        controls.append({
            'type': 'cultural',
            'description': 'Cultural control methods recommended - see full analysis'
        })
    
    return controls


def extract_chemical_treatments(analysis_text: str) -> list:
    """Extract chemical treatment recommendations"""
    treatments = []
    
    if 'chemical treatment' in analysis_text.lower() or 'pesticide' in analysis_text.lower():
        treatments.append({
            'type': 'chemical',
            'description': 'Chemical treatment available as last resort - see full analysis for dosage and safety'
        })
    
    return treatments


def extract_prevention(analysis_text: str) -> list:
    """Extract preventive measures"""
    return ['See full analysis for detailed preventive measures']


def store_pest_diagnosis(diagnosis_id: str,
                        user_id: str,
                        s3_key: str,
                        analysis: Dict[str, Any],
                        crop_type: str,
                        timestamp: int) -> None:
    """Store pest diagnosis in DynamoDB"""
    
    try:
        item = {
            'diagnosis_id': diagnosis_id,
            'user_id': user_id,
            'image_s3_key': s3_key,
            'diagnosis_result': analysis,
            'confidence_score': analysis.get('confidence_score', 0.0),
            'severity': analysis.get('severity', 'unknown'),
            'pests': analysis.get('pests', []),
            'lifecycle_stage': analysis.get('lifecycle_stage', 'unknown'),
            'population_density': analysis.get('population_density', 'unknown'),
            'crop_type': crop_type or 'unknown',
            'follow_up_status': 'pending',
            'created_timestamp': timestamp
        }
        
        pest_diagnosis_table.put_item(Item=item)
        logger.info(f"Pest diagnosis stored: {diagnosis_id}")
    
    except Exception as e:
        logger.error(f"Error storing pest diagnosis: {e}")


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
            'image_data': 'base64_test_data',
            'user_id': 'test_farmer_001',
            'crop_type': 'wheat',
            'additional_context': 'Small insects on leaves',
            'language_code': 'en'
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
