"""
AWS Lambda Function for Crop Image Analysis
Handles image upload and disease identification using Amazon Bedrock
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
DIAGNOSIS_TABLE = os.environ.get('DIAGNOSIS_TABLE', 'RISE-DiagnosisHistory')
MAX_IMAGE_SIZE = int(os.environ.get('MAX_IMAGE_SIZE', 5 * 1024 * 1024))  # 5MB
BEDROCK_MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'

# DynamoDB table
diagnosis_table = dynamodb.Table(DIAGNOSIS_TABLE)


def lambda_handler(event, context):
    """
    Lambda handler for crop image analysis
    
    Expected event structure:
    {
        "body": {
            "image_data": "base64_encoded_image",
            "user_id": "farmer_1234567890",
            "crop_type": "wheat",
            "additional_context": "Leaves turning yellow",
            "language_code": "hi"
        }
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "success": true,
            "diagnosis_id": "diag_abc123",
            "diseases": ["Leaf Rust"],
            "confidence_score": 0.85,
            "severity": "medium",
            "full_analysis": "...",
            "treatment_recommendations": [...]
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
        quality_check = validate_image_quality_comprehensive(image_bytes)
        if not quality_check['valid']:
            return create_response(400, {
                'success': False,
                'error': 'poor_image_quality',
                'validation': quality_check,
                'retry_guidance': generate_retry_guidance(quality_check)
            })
        
        # Generate diagnosis ID
        diagnosis_id = f"diag_{uuid.uuid4().hex[:12]}"
        timestamp = int(datetime.now().timestamp())
        
        # Store image in S3
        s3_key = f"images/crop-photos/{user_id}/{diagnosis_id}.jpg"
        
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
            store_diagnosis(
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
                'diseases': analysis_result.get('diseases', []),
                'confidence_score': analysis_result.get('confidence_score', 0.0),
                'severity': analysis_result.get('severity', 'unknown'),
                'full_analysis': analysis_result.get('full_analysis', ''),
                'treatment_recommendations': analysis_result.get('treatment_recommendations', []),
                'preventive_measures': analysis_result.get('preventive_measures', []),
                'multiple_issues': analysis_result.get('multiple_issues', False),
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


def validate_image_quality_comprehensive(image_bytes: bytes) -> Dict[str, Any]:
    """Comprehensive image quality validation with blur, resolution, and lighting checks"""
    try:
        from PIL import Image, ImageStat, ImageFilter
        import io
        import numpy as np
        
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        
        issues = []
        guidance = []
        metrics = {}
        quality_scores = []
        
        # Resolution check
        if width < 300 or height < 300:
            issues.append('low_resolution')
            guidance.append(f'Image resolution is too low ({width}x{height}). Please take a photo with at least 300x300 pixels')
            guidance.append('Tips: Use your phone camera\'s highest quality setting')
            quality_scores.append(min(width, height) / 300)
        else:
            quality_scores.append(1.0)
        
        metrics['resolution'] = {'width': width, 'height': height}
        
        # Blur detection using Laplacian variance
        try:
            if img.mode != 'L':
                gray_img = img.convert('L')
            else:
                gray_img = img
            
            laplacian = gray_img.filter(ImageFilter.FIND_EDGES)
            laplacian_array = np.array(laplacian)
            blur_score = laplacian_array.var()
            
            metrics['blur_score'] = round(blur_score, 2)
            
            if blur_score < 50:  # Very blurry
                issues.append('very_blurry')
                guidance.append('Image is very blurry. Please retake the photo with better focus')
                guidance.append('Tips: Tap on the crop in your camera app to focus before taking the photo')
                guidance.append('Hold your phone steady or use a stable surface')
                quality_scores.append(0.3)
            elif blur_score < 100:  # Slightly blurry
                issues.append('slightly_blurry')
                guidance.append('Image is slightly blurry. For best results, retake with better focus')
                quality_scores.append(0.6)
            else:
                quality_scores.append(1.0)
            
            metrics['blur_level'] = 'sharp' if blur_score >= 100 else ('slightly_blurry' if blur_score >= 50 else 'very_blurry')
        except:
            quality_scores.append(1.0)  # Don't penalize if blur detection fails
            metrics['blur_score'] = 0
            metrics['blur_level'] = 'unknown'
        
        # Lighting analysis
        try:
            if img.mode != 'RGB':
                rgb_img = img.convert('RGB')
            else:
                rgb_img = img
            
            stat = ImageStat.Stat(rgb_img)
            brightness = sum(stat.mean) / len(stat.mean)
            contrast = sum(stat.stddev) / len(stat.stddev)
            
            metrics['brightness'] = round(brightness, 2)
            metrics['contrast'] = round(contrast, 2)
            
            if brightness < 30:
                issues.append('too_dark')
                guidance.append('Image is too dark. Please take the photo in better lighting')
                guidance.append('Tips: Take photos during daytime or use additional lighting')
                quality_scores.append(brightness / 30)
            elif brightness > 225:
                issues.append('too_bright')
                guidance.append('Image is overexposed (too bright). Please reduce exposure')
                guidance.append('Tips: Avoid direct sunlight, take photos in shade or cloudy conditions')
                quality_scores.append((255 - brightness) / 30)
            else:
                quality_scores.append(1.0)
            
            if contrast < 20:
                issues.append('low_contrast')
                guidance.append('Image has low contrast, making details hard to see')
                quality_scores[-1] *= 0.8
            
            # Check for uneven lighting
            histogram = rgb_img.histogram()
            total_pixels = rgb_img.size[0] * rgb_img.size[1]
            
            r_hist = histogram[0:256]
            g_hist = histogram[256:512]
            b_hist = histogram[512:768]
            avg_hist = [(r + g + b) / 3 for r, g, b in zip(r_hist, g_hist, b_hist)]
            
            dark_pixels = sum(avg_hist[0:86])
            bright_pixels = sum(avg_hist[171:256])
            
            dark_pct = (dark_pixels / total_pixels) * 100
            bright_pct = (bright_pixels / total_pixels) * 100
            
            if dark_pct > 40 or bright_pct > 40:
                issues.append('uneven_lighting')
                guidance.append('Lighting is uneven with harsh shadows or bright spots')
                guidance.append('Tips: Use diffused natural light or take photos on a cloudy day')
                quality_scores[-1] *= 0.85
            
            lighting_quality = 'good' if len([i for i in issues if i in ['too_dark', 'too_bright', 'uneven_lighting']]) == 0 else 'fair' if len([i for i in issues if i in ['too_dark', 'too_bright']]) == 0 else 'poor'
            metrics['lighting_quality'] = lighting_quality
        except:
            quality_scores.append(1.0)  # Don't penalize if lighting analysis fails
            metrics['brightness'] = 0
            metrics['contrast'] = 0
            metrics['lighting_quality'] = 'unknown'
        
        # Check aspect ratio
        aspect_ratio = width / height if height > 0 else 1.0
        if aspect_ratio > 3 or aspect_ratio < 0.33:
            issues.append('unusual_aspect_ratio')
            guidance.append('Image has an unusual aspect ratio. Try to capture the crop in a more balanced frame')
        
        # Calculate overall quality score
        overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Generate summary
        if len(issues) == 0:
            if overall_quality >= 0.9:
                summary = 'Excellent image quality - perfect for accurate diagnosis'
            elif overall_quality >= 0.8:
                summary = 'Good image quality - suitable for diagnosis'
            else:
                summary = 'Acceptable image quality - diagnosis may be less accurate'
        else:
            issue_count = len(issues)
            summary = f'Image has {issue_count} quality issue(s) that should be addressed for accurate diagnosis'
        
        return {
            'valid': len(issues) == 0,
            'quality_score': round(overall_quality, 2),
            'issues': issues,
            'guidance': guidance,
            'metrics': metrics,
            'summary': summary
        }
    
    except Exception as e:
        logger.error(f"Image validation error: {e}")
        return {
            'valid': False,
            'issues': ['invalid_image'],
            'guidance': ['Unable to read image. Please upload a valid JPEG or PNG image'],
            'metrics': {},
            'summary': 'Image file is invalid or corrupted'
        }


def generate_retry_guidance(validation_result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate specific retry guidance based on validation results"""
    
    if validation_result['valid']:
        return {
            'retry_needed': False,
            'message': 'Image quality is good. You can proceed with analysis.'
        }
    
    issues = validation_result.get('issues', [])
    
    # Prioritize guidance by issue severity
    priority_order = [
        'low_resolution',
        'very_blurry',
        'too_dark',
        'too_bright',
        'slightly_blurry',
        'uneven_lighting',
        'low_contrast',
        'unusual_aspect_ratio'
    ]
    
    # Sort issues by priority
    sorted_issues = sorted(issues, key=lambda x: priority_order.index(x) if x in priority_order else 999)
    top_issues = sorted_issues[:3]
    
    # Generate specific guidance
    specific_guidance = []
    for issue in top_issues:
        if issue == 'low_resolution':
            specific_guidance.append({
                'issue': 'Low Resolution',
                'icon': '📐',
                'tips': [
                    'Use your phone camera\'s highest quality setting',
                    'Get closer to the crop for more detail',
                    'Ensure camera is set to maximum resolution'
                ]
            })
        elif issue in ['very_blurry', 'slightly_blurry']:
            specific_guidance.append({
                'issue': 'Blurry Image',
                'icon': '🔍',
                'tips': [
                    'Tap on the crop in your camera app to focus',
                    'Hold your phone steady or rest it on a stable surface',
                    'Ensure good lighting for faster shutter speed',
                    'Clean your camera lens'
                ]
            })
        elif issue == 'too_dark':
            specific_guidance.append({
                'issue': 'Too Dark',
                'icon': '🌙',
                'tips': [
                    'Take photos during daytime',
                    'Move to a brighter location',
                    'Use additional lighting if indoors',
                    'Avoid shadows covering the crop'
                ]
            })
        elif issue == 'too_bright':
            specific_guidance.append({
                'issue': 'Too Bright',
                'icon': '☀️',
                'tips': [
                    'Avoid direct sunlight',
                    'Take photos in shade or on cloudy days',
                    'Adjust camera exposure down if available',
                    'Position yourself to block harsh light'
                ]
            })
        elif issue == 'uneven_lighting':
            specific_guidance.append({
                'issue': 'Uneven Lighting',
                'icon': '💡',
                'tips': [
                    'Use diffused natural light',
                    'Avoid flash photography',
                    'Take photos on cloudy days for even lighting',
                    'Ensure no harsh shadows on the crop'
                ]
            })
    
    return {
        'retry_needed': True,
        'message': f'Please retake the photo to address {len(top_issues)} quality issue(s)',
        'quality_score': validation_result.get('quality_score', 0.0),
        'top_issues': top_issues,
        'specific_guidance': specific_guidance
    }


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
            guidance.append('Try to capture the crop in a more balanced frame')
        
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
        prompt = build_disease_prompt(crop_type, additional_context, language_code)
        
        # Call Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 2000,
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
        diagnosis = parse_diagnosis(analysis_text)
        
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


def build_disease_prompt(crop_type: str, additional_context: str, language_code: str) -> str:
    """Build disease identification prompt"""
    
    prompt = """You are an expert agricultural pathologist. Analyze this crop image and provide a detailed diagnosis.

"""
    
    if crop_type:
        prompt += f"Crop Type: {crop_type}\n"
    
    if additional_context:
        prompt += f"Farmer's Observation: {additional_context}\n"
    
    prompt += """
Provide your analysis in this format:

1. DISEASES DETECTED:
   - Disease Name: [name]
   - Confidence: [percentage]
   - Severity: [low/medium/high/critical]

2. SYMPTOMS OBSERVED:
   - List visible symptoms

3. TREATMENT RECOMMENDATIONS (prioritized):
   - Immediate Actions
   - Chemical Treatment (with dosage)
   - Organic Alternatives
   - Application Timing
   - Safety Precautions

4. PREVENTIVE MEASURES:
   - Prevention steps

5. PROGNOSIS:
   - Expected outcome with treatment

If multiple diseases detected, prioritize by urgency and impact.
"""
    
    return prompt


def parse_diagnosis(analysis_text: str) -> Dict[str, Any]:
    """Parse diagnosis from AI response"""
    
    diseases = []
    confidence_score = 0.75
    severity = 'medium'
    
    # Simple parsing - extract key information
    lines = analysis_text.split('\n')
    
    for line in lines:
        line_lower = line.lower().strip()
        
        if 'disease name:' in line_lower:
            disease_name = line.split(':', 1)[1].strip()
            diseases.append(disease_name)
        
        if 'confidence:' in line_lower:
            try:
                conf_str = line.split(':', 1)[1].strip().replace('%', '')
                confidence_score = float(conf_str) / 100
            except:
                pass
        
        if 'severity:' in line_lower:
            severity_str = line.split(':', 1)[1].strip().lower()
            if severity_str in ['low', 'medium', 'high', 'critical']:
                severity = severity_str
    
    # If no diseases found, assume healthy
    if not diseases or 'none' in analysis_text.lower()[:200]:
        diseases = ['Healthy - No disease detected']
        severity = 'low'
        confidence_score = 0.9
    
    return {
        'diseases': diseases,
        'confidence_score': confidence_score,
        'severity': severity,
        'full_analysis': analysis_text,
        'multiple_issues': len(diseases) > 1,
        'treatment_recommendations': extract_treatments(analysis_text),
        'preventive_measures': extract_prevention(analysis_text)
    }


def extract_treatments(analysis_text: str) -> list:
    """Extract treatment recommendations"""
    treatments = []
    
    if 'chemical treatment' in analysis_text.lower():
        treatments.append({
            'type': 'chemical',
            'description': 'Chemical treatment recommended - see full analysis'
        })
    
    if 'organic' in analysis_text.lower():
        treatments.append({
            'type': 'organic',
            'description': 'Organic alternatives available - see full analysis'
        })
    
    return treatments


def extract_prevention(analysis_text: str) -> list:
    """Extract preventive measures"""
    return ['See full analysis for detailed preventive measures']


def store_diagnosis(diagnosis_id: str,
                   user_id: str,
                   s3_key: str,
                   analysis: Dict[str, Any],
                   crop_type: str,
                   timestamp: int) -> None:
    """Store diagnosis in DynamoDB"""
    
    try:
        item = {
            'diagnosis_id': diagnosis_id,
            'user_id': user_id,
            'image_s3_key': s3_key,
            'diagnosis_result': analysis,
            'confidence_score': analysis.get('confidence_score', 0.0),
            'severity': analysis.get('severity', 'unknown'),
            'diseases': analysis.get('diseases', []),
            'crop_type': crop_type or 'unknown',
            'follow_up_status': 'pending',
            'created_timestamp': timestamp
        }
        
        diagnosis_table.put_item(Item=item)
        logger.info(f"Diagnosis stored: {diagnosis_id}")
    
    except Exception as e:
        logger.error(f"Error storing diagnosis: {e}")


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
            'additional_context': 'Leaves have brown spots',
            'language_code': 'en'
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
