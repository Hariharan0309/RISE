"""
AWS Lambda Function for Image Quality Validation
Validates image quality before disease/pest analysis using Amazon Bedrock
Includes blur detection, resolution validation, and lighting condition analysis
"""

import json
import boto3
import base64
import logging
import os
import io
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageStat, ImageFilter
import numpy as np

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
MIN_RESOLUTION = int(os.environ.get('MIN_RESOLUTION', 300))  # 300x300 pixels minimum
MAX_IMAGE_SIZE = int(os.environ.get('MAX_IMAGE_SIZE', 5 * 1024 * 1024))  # 5MB
BLUR_THRESHOLD = float(os.environ.get('BLUR_THRESHOLD', 100.0))  # Laplacian variance threshold
MIN_BRIGHTNESS = int(os.environ.get('MIN_BRIGHTNESS', 30))  # Too dark threshold
MAX_BRIGHTNESS = int(os.environ.get('MAX_BRIGHTNESS', 225))  # Too bright threshold


def lambda_handler(event, context):
    """
    Lambda handler for image quality validation
    
    Expected event structure:
    {
        "body": {
            "image_data": "base64_encoded_image",
            "check_types": ["blur", "resolution", "lighting"]  # optional, defaults to all
        }
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "valid": true/false,
            "quality_score": 0.85,
            "issues": [],
            "guidance": [],
            "metrics": {
                "blur_score": 150.5,
                "resolution": {"width": 1024, "height": 768},
                "brightness": 128,
                "contrast": 45
            }
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
        check_types = body.get('check_types', ['blur', 'resolution', 'lighting'])
        
        # Validate required fields
        if not image_data_base64:
            return create_response(400, {
                'valid': False,
                'error': 'Missing image_data in request'
            })
        
        # Decode base64 image
        try:
            image_bytes = base64.b64decode(image_data_base64)
        except Exception as e:
            logger.error(f"Base64 decode error: {e}")
            return create_response(400, {
                'valid': False,
                'error': 'Invalid base64 image data'
            })
        
        # Validate image size
        image_size = len(image_bytes)
        if image_size > MAX_IMAGE_SIZE:
            return create_response(400, {
                'valid': False,
                'error': f'Image size ({image_size} bytes) exceeds maximum ({MAX_IMAGE_SIZE} bytes)',
                'guidance': [f'Please reduce image size to under {MAX_IMAGE_SIZE / (1024*1024):.1f}MB']
            })
        
        if image_size == 0:
            return create_response(400, {
                'valid': False,
                'error': 'Empty image file',
                'guidance': ['Please upload a valid image file']
            })
        
        # Perform quality validation
        validation_result = validate_image_quality(image_bytes, check_types)
        
        return create_response(200, validation_result)
    
    except Exception as e:
        logger.error(f"Lambda handler error: {e}", exc_info=True)
        return create_response(500, {
            'valid': False,
            'error': f'Internal server error: {str(e)}'
        })


def validate_image_quality(image_bytes: bytes, check_types: List[str]) -> Dict[str, Any]:
    """
    Comprehensive image quality validation
    
    Args:
        image_bytes: Image data as bytes
        check_types: List of checks to perform
    
    Returns:
        Validation results with issues and guidance
    """
    
    try:
        # Open image
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        
        issues = []
        guidance = []
        metrics = {}
        quality_scores = []
        
        # Resolution check
        if 'resolution' in check_types:
            res_result = check_resolution(img)
            metrics['resolution'] = res_result['metrics']
            
            if not res_result['valid']:
                issues.extend(res_result['issues'])
                guidance.extend(res_result['guidance'])
                quality_scores.append(res_result['score'])
            else:
                quality_scores.append(1.0)
        
        # Blur detection
        if 'blur' in check_types:
            blur_result = detect_blur(img)
            metrics['blur_score'] = blur_result['metrics']['blur_score']
            metrics['blur_level'] = blur_result['metrics']['blur_level']
            
            if not blur_result['valid']:
                issues.extend(blur_result['issues'])
                guidance.extend(blur_result['guidance'])
                quality_scores.append(blur_result['score'])
            else:
                quality_scores.append(1.0)
        
        # Lighting condition analysis
        if 'lighting' in check_types:
            lighting_result = analyze_lighting(img)
            metrics['brightness'] = lighting_result['metrics']['brightness']
            metrics['contrast'] = lighting_result['metrics']['contrast']
            metrics['lighting_quality'] = lighting_result['metrics']['lighting_quality']
            
            if not lighting_result['valid']:
                issues.extend(lighting_result['issues'])
                guidance.extend(lighting_result['guidance'])
                quality_scores.append(lighting_result['score'])
            else:
                quality_scores.append(1.0)
        
        # Calculate overall quality score
        overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Determine if image is valid
        is_valid = len(issues) == 0
        
        return {
            'valid': is_valid,
            'quality_score': round(overall_quality, 2),
            'issues': issues,
            'guidance': guidance,
            'metrics': metrics,
            'summary': generate_summary(is_valid, issues, overall_quality)
        }
    
    except Exception as e:
        logger.error(f"Image validation error: {e}", exc_info=True)
        return {
            'valid': False,
            'quality_score': 0.0,
            'issues': ['invalid_image'],
            'guidance': ['Unable to read image. Please upload a valid JPEG or PNG image'],
            'metrics': {},
            'summary': 'Image file is invalid or corrupted'
        }


def check_resolution(img: Image.Image) -> Dict[str, Any]:
    """
    Check image resolution
    
    Args:
        img: PIL Image object
    
    Returns:
        Resolution check results
    """
    
    width, height = img.size
    
    issues = []
    guidance = []
    score = 1.0
    
    # Check minimum resolution
    if width < MIN_RESOLUTION or height < MIN_RESOLUTION:
        issues.append('low_resolution')
        guidance.append(f'Image resolution is too low ({width}x{height}). Please take a photo with at least {MIN_RESOLUTION}x{MIN_RESOLUTION} pixels')
        guidance.append('Tips: Use your phone camera\'s highest quality setting')
        score = min(width, height) / MIN_RESOLUTION
    
    # Check aspect ratio
    aspect_ratio = width / height if height > 0 else 1.0
    
    if aspect_ratio > 3.0 or aspect_ratio < 0.33:
        issues.append('unusual_aspect_ratio')
        guidance.append('Image has an unusual aspect ratio. Try to capture the crop in a more balanced, square-like frame')
        score *= 0.8
    
    # Check if resolution is too high (might indicate poor compression)
    if width > 4000 or height > 4000:
        issues.append('very_high_resolution')
        guidance.append('Image resolution is very high. Consider reducing it to improve upload speed')
        # This is not a critical issue, so we don't reduce score
    
    return {
        'valid': len([i for i in issues if i in ['low_resolution', 'unusual_aspect_ratio']]) == 0,
        'issues': issues,
        'guidance': guidance,
        'score': max(0.0, min(1.0, score)),
        'metrics': {
            'width': width,
            'height': height,
            'aspect_ratio': round(aspect_ratio, 2)
        }
    }


def detect_blur(img: Image.Image) -> Dict[str, Any]:
    """
    Detect image blur using Laplacian variance method
    
    Args:
        img: PIL Image object
    
    Returns:
        Blur detection results
    """
    
    try:
        # Convert to grayscale for blur detection
        if img.mode != 'L':
            gray_img = img.convert('L')
        else:
            gray_img = img
        
        # Apply Laplacian filter to detect edges
        # Blurry images have fewer edges and lower variance
        laplacian = gray_img.filter(ImageFilter.FIND_EDGES)
        
        # Calculate variance of Laplacian
        # Convert to numpy for easier calculation
        laplacian_array = np.array(laplacian)
        blur_score = laplacian_array.var()
        
        issues = []
        guidance = []
        score = 1.0
        
        # Determine blur level
        if blur_score < BLUR_THRESHOLD * 0.5:
            blur_level = 'very_blurry'
            issues.append('very_blurry')
            guidance.append('Image is very blurry. Please retake the photo with better focus')
            guidance.append('Tips: Tap on the crop in your camera app to focus before taking the photo')
            guidance.append('Hold your phone steady or use a stable surface')
            score = 0.3
        elif blur_score < BLUR_THRESHOLD:
            blur_level = 'slightly_blurry'
            issues.append('slightly_blurry')
            guidance.append('Image is slightly blurry. For best results, retake with better focus')
            guidance.append('Tips: Ensure good lighting and hold the camera steady')
            score = 0.6
        else:
            blur_level = 'sharp'
        
        return {
            'valid': blur_score >= BLUR_THRESHOLD,
            'issues': issues,
            'guidance': guidance,
            'score': score,
            'metrics': {
                'blur_score': round(blur_score, 2),
                'blur_level': blur_level,
                'threshold': BLUR_THRESHOLD
            }
        }
    
    except Exception as e:
        logger.error(f"Blur detection error: {e}")
        return {
            'valid': True,  # Don't fail on blur detection errors
            'issues': [],
            'guidance': [],
            'score': 1.0,
            'metrics': {
                'blur_score': 0,
                'blur_level': 'unknown',
                'error': str(e)
            }
        }


def analyze_lighting(img: Image.Image) -> Dict[str, Any]:
    """
    Analyze lighting conditions (brightness, contrast, exposure)
    
    Args:
        img: PIL Image object
    
    Returns:
        Lighting analysis results
    """
    
    try:
        # Convert to RGB if not already
        if img.mode != 'RGB':
            rgb_img = img.convert('RGB')
        else:
            rgb_img = img
        
        # Calculate image statistics
        stat = ImageStat.Stat(rgb_img)
        
        # Average brightness across all channels
        brightness = sum(stat.mean) / len(stat.mean)
        
        # Standard deviation as a measure of contrast
        contrast = sum(stat.stddev) / len(stat.stddev)
        
        issues = []
        guidance = []
        score = 1.0
        
        # Check if too dark
        if brightness < MIN_BRIGHTNESS:
            issues.append('too_dark')
            guidance.append('Image is too dark. Please take the photo in better lighting')
            guidance.append('Tips: Take photos during daytime or use additional lighting')
            guidance.append('Avoid shadows covering the crop')
            score = brightness / MIN_BRIGHTNESS
        
        # Check if too bright (overexposed)
        elif brightness > MAX_BRIGHTNESS:
            issues.append('too_bright')
            guidance.append('Image is overexposed (too bright). Please reduce exposure')
            guidance.append('Tips: Avoid direct sunlight, take photos in shade or cloudy conditions')
            guidance.append('Adjust camera exposure settings if available')
            score = (255 - brightness) / (255 - MAX_BRIGHTNESS)
        
        # Check contrast
        if contrast < 20:
            issues.append('low_contrast')
            guidance.append('Image has low contrast, making details hard to see')
            guidance.append('Tips: Ensure even lighting without harsh shadows')
            score *= 0.8
        
        # Check for uneven lighting (using histogram analysis)
        histogram = rgb_img.histogram()
        
        # Analyze distribution of brightness values
        # Split into dark, mid, and bright regions
        total_pixels = rgb_img.size[0] * rgb_img.size[1]
        
        # For RGB, histogram has 256 values per channel
        r_hist = histogram[0:256]
        g_hist = histogram[256:512]
        b_hist = histogram[512:768]
        
        # Average across channels
        avg_hist = [(r + g + b) / 3 for r, g, b in zip(r_hist, g_hist, b_hist)]
        
        # Calculate percentage in dark (0-85), mid (86-170), bright (171-255) regions
        dark_pixels = sum(avg_hist[0:86])
        mid_pixels = sum(avg_hist[86:171])
        bright_pixels = sum(avg_hist[171:256])
        
        dark_pct = (dark_pixels / total_pixels) * 100
        bright_pct = (bright_pixels / total_pixels) * 100
        
        # Check for uneven lighting (too many very dark or very bright pixels)
        if dark_pct > 40 or bright_pct > 40:
            issues.append('uneven_lighting')
            guidance.append('Lighting is uneven with harsh shadows or bright spots')
            guidance.append('Tips: Use diffused natural light or take photos on a cloudy day')
            guidance.append('Avoid flash photography which creates harsh shadows')
            score *= 0.85
        
        # Determine overall lighting quality
        if len(issues) == 0:
            lighting_quality = 'good'
        elif len(issues) == 1:
            lighting_quality = 'fair'
        else:
            lighting_quality = 'poor'
        
        return {
            'valid': 'too_dark' not in issues and 'too_bright' not in issues,
            'issues': issues,
            'guidance': guidance,
            'score': max(0.0, min(1.0, score)),
            'metrics': {
                'brightness': round(brightness, 2),
                'contrast': round(contrast, 2),
                'lighting_quality': lighting_quality,
                'dark_percentage': round(dark_pct, 1),
                'bright_percentage': round(bright_pct, 1)
            }
        }
    
    except Exception as e:
        logger.error(f"Lighting analysis error: {e}")
        return {
            'valid': True,  # Don't fail on lighting analysis errors
            'issues': [],
            'guidance': [],
            'score': 1.0,
            'metrics': {
                'brightness': 0,
                'contrast': 0,
                'lighting_quality': 'unknown',
                'error': str(e)
            }
        }


def generate_summary(is_valid: bool, issues: List[str], quality_score: float) -> str:
    """
    Generate human-readable summary of image quality
    
    Args:
        is_valid: Whether image passes validation
        issues: List of issues found
        quality_score: Overall quality score
    
    Returns:
        Summary string
    """
    
    if is_valid:
        if quality_score >= 0.9:
            return 'Excellent image quality - perfect for accurate diagnosis'
        elif quality_score >= 0.8:
            return 'Good image quality - suitable for diagnosis'
        else:
            return 'Acceptable image quality - diagnosis may be less accurate'
    else:
        issue_count = len(issues)
        if issue_count == 1:
            return f'Image has 1 quality issue that should be addressed for accurate diagnosis'
        else:
            return f'Image has {issue_count} quality issues that should be addressed for accurate diagnosis'


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
    # Test with a sample image
    import sys
    
    if len(sys.argv) > 1:
        # Load image from file
        with open(sys.argv[1], 'rb') as f:
            image_data = f.read()
        
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        test_event = {
            'body': {
                'image_data': image_base64,
                'check_types': ['blur', 'resolution', 'lighting']
            }
        }
        
        result = lambda_handler(test_event, None)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python image_quality_lambda.py <image_file>")
