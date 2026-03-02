"""
RISE Image Quality Validation Tools
Tools for validating image quality before disease/pest analysis
Includes blur detection, resolution validation, and lighting condition analysis
"""

import boto3
import logging
import base64
import json
from typing import Dict, Any, Optional, List
from PIL import Image, ImageStat, ImageFilter
import io
import numpy as np

logger = logging.getLogger(__name__)


class ImageQualityTools:
    """Image quality validation tools"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize image quality tools
        
        Args:
            region: AWS region for services
        """
        self.region = region
        
        # Configuration
        self.min_resolution = 300  # 300x300 pixels minimum
        self.max_image_size = 5 * 1024 * 1024  # 5MB
        self.blur_threshold = 100.0  # Laplacian variance threshold
        self.min_brightness = 30  # Too dark threshold
        self.max_brightness = 225  # Too bright threshold
        
        logger.info(f"Image quality tools initialized in region {region}")
    
    def validate_image_quality(self, 
                               image_data: bytes,
                               check_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Comprehensive image quality validation
        
        Args:
            image_data: Image bytes
            check_types: List of checks to perform (blur, resolution, lighting)
        
        Returns:
            Dict with validation results, issues, and guidance
        """
        
        if check_types is None:
            check_types = ['blur', 'resolution', 'lighting']
        
        try:
            # Validate image size
            image_size = len(image_data)
            if image_size > self.max_image_size:
                return {
                    'valid': False,
                    'quality_score': 0.0,
                    'issues': ['file_too_large'],
                    'guidance': [f'Image size ({image_size / (1024*1024):.1f}MB) exceeds maximum ({self.max_image_size / (1024*1024):.1f}MB)'],
                    'metrics': {},
                    'summary': 'Image file is too large'
                }
            
            if image_size == 0:
                return {
                    'valid': False,
                    'quality_score': 0.0,
                    'issues': ['empty_file'],
                    'guidance': ['Image file is empty. Please upload a valid image'],
                    'metrics': {},
                    'summary': 'Image file is empty'
                }
            
            # Open image
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            issues = []
            guidance = []
            metrics = {}
            quality_scores = []
            
            # Resolution check
            if 'resolution' in check_types:
                res_result = self._check_resolution(img)
                metrics['resolution'] = res_result['metrics']
                
                if not res_result['valid']:
                    issues.extend(res_result['issues'])
                    guidance.extend(res_result['guidance'])
                    quality_scores.append(res_result['score'])
                else:
                    quality_scores.append(1.0)
            
            # Blur detection
            if 'blur' in check_types:
                blur_result = self._detect_blur(img)
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
                lighting_result = self._analyze_lighting(img)
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
                'summary': self._generate_summary(is_valid, issues, overall_quality)
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
    
    def _check_resolution(self, img: Image.Image) -> Dict[str, Any]:
        """Check image resolution"""
        
        width, height = img.size
        
        issues = []
        guidance = []
        score = 1.0
        
        # Check minimum resolution
        if width < self.min_resolution or height < self.min_resolution:
            issues.append('low_resolution')
            guidance.append(f'Image resolution is too low ({width}x{height}). Please take a photo with at least {self.min_resolution}x{self.min_resolution} pixels')
            guidance.append('Tips: Use your phone camera\'s highest quality setting')
            score = min(width, height) / self.min_resolution
        
        # Check aspect ratio
        aspect_ratio = width / height if height > 0 else 1.0
        
        if aspect_ratio > 3.0 or aspect_ratio < 0.33:
            issues.append('unusual_aspect_ratio')
            guidance.append('Image has an unusual aspect ratio. Try to capture the crop in a more balanced, square-like frame')
            score *= 0.8
        
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
    
    def _detect_blur(self, img: Image.Image) -> Dict[str, Any]:
        """Detect image blur using Laplacian variance method"""
        
        try:
            # Convert to grayscale for blur detection
            if img.mode != 'L':
                gray_img = img.convert('L')
            else:
                gray_img = img
            
            # Apply Laplacian filter to detect edges
            laplacian = gray_img.filter(ImageFilter.FIND_EDGES)
            
            # Calculate variance of Laplacian
            laplacian_array = np.array(laplacian)
            blur_score = laplacian_array.var()
            
            issues = []
            guidance = []
            score = 1.0
            
            # Determine blur level
            if blur_score < self.blur_threshold * 0.5:
                blur_level = 'very_blurry'
                issues.append('very_blurry')
                guidance.append('Image is very blurry. Please retake the photo with better focus')
                guidance.append('Tips: Tap on the crop in your camera app to focus before taking the photo')
                guidance.append('Hold your phone steady or use a stable surface')
                score = 0.3
            elif blur_score < self.blur_threshold:
                blur_level = 'slightly_blurry'
                issues.append('slightly_blurry')
                guidance.append('Image is slightly blurry. For best results, retake with better focus')
                guidance.append('Tips: Ensure good lighting and hold the camera steady')
                score = 0.6
            else:
                blur_level = 'sharp'
            
            return {
                'valid': blur_score >= self.blur_threshold,
                'issues': issues,
                'guidance': guidance,
                'score': score,
                'metrics': {
                    'blur_score': round(blur_score, 2),
                    'blur_level': blur_level,
                    'threshold': self.blur_threshold
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
    
    def _analyze_lighting(self, img: Image.Image) -> Dict[str, Any]:
        """Analyze lighting conditions"""
        
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
            if brightness < self.min_brightness:
                issues.append('too_dark')
                guidance.append('Image is too dark. Please take the photo in better lighting')
                guidance.append('Tips: Take photos during daytime or use additional lighting')
                guidance.append('Avoid shadows covering the crop')
                score = brightness / self.min_brightness
            
            # Check if too bright (overexposed)
            elif brightness > self.max_brightness:
                issues.append('too_bright')
                guidance.append('Image is overexposed (too bright). Please reduce exposure')
                guidance.append('Tips: Avoid direct sunlight, take photos in shade or cloudy conditions')
                guidance.append('Adjust camera exposure settings if available')
                score = (255 - brightness) / (255 - self.max_brightness)
            
            # Check contrast
            if contrast < 20:
                issues.append('low_contrast')
                guidance.append('Image has low contrast, making details hard to see')
                guidance.append('Tips: Ensure even lighting without harsh shadows')
                score *= 0.8
            
            # Check for uneven lighting
            histogram = rgb_img.histogram()
            total_pixels = rgb_img.size[0] * rgb_img.size[1]
            
            # Average histogram across RGB channels
            r_hist = histogram[0:256]
            g_hist = histogram[256:512]
            b_hist = histogram[512:768]
            avg_hist = [(r + g + b) / 3 for r, g, b in zip(r_hist, g_hist, b_hist)]
            
            # Calculate percentage in dark, mid, bright regions
            dark_pixels = sum(avg_hist[0:86])
            bright_pixels = sum(avg_hist[171:256])
            
            dark_pct = (dark_pixels / total_pixels) * 100
            bright_pct = (bright_pixels / total_pixels) * 100
            
            # Check for uneven lighting
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
                'valid': True,
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
    
    def _generate_summary(self, is_valid: bool, issues: List[str], quality_score: float) -> str:
        """Generate human-readable summary"""
        
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
    
    def get_retry_guidance(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate specific retry guidance based on validation results
        
        Args:
            validation_result: Result from validate_image_quality
        
        Returns:
            Dict with retry guidance and tips
        """
        
        if validation_result['valid']:
            return {
                'retry_needed': False,
                'message': 'Image quality is good. You can proceed with analysis.'
            }
        
        issues = validation_result.get('issues', [])
        guidance = validation_result.get('guidance', [])
        
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
        
        # Get top 3 most important issues
        top_issues = sorted_issues[:3]
        
        # Generate specific guidance for top issues
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
            elif issue == 'very_blurry' or issue == 'slightly_blurry':
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
            'specific_guidance': specific_guidance,
            'all_guidance': guidance
        }


# Tool functions for agent integration

def create_quality_tools(region: str = "us-east-1") -> ImageQualityTools:
    """
    Factory function to create image quality tools instance
    
    Args:
        region: AWS region
    
    Returns:
        ImageQualityTools instance
    """
    return ImageQualityTools(region=region)


def validate_image(image_data: bytes, 
                   check_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Tool function for validating image quality
    
    Args:
        image_data: Image bytes
        check_types: Optional list of checks to perform
    
    Returns:
        Validation results
    """
    tools = create_quality_tools()
    return tools.validate_image_quality(image_data, check_types)
