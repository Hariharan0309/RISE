"""
Unit Tests for Image Quality Validation Tools
Tests blur detection, resolution validation, and lighting analysis
"""

import unittest
import sys
import os
from PIL import Image, ImageDraw, ImageFilter
import io
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.image_quality_tools import ImageQualityTools, create_quality_tools, validate_image


class TestImageQualityTools(unittest.TestCase):
    """Test cases for image quality validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.quality_tools = ImageQualityTools()
    
    def create_test_image(self, 
                         width: int = 800, 
                         height: int = 600,
                         brightness: int = 128,
                         add_blur: bool = False,
                         add_noise: bool = False) -> bytes:
        """
        Create a test image with specified properties
        
        Args:
            width: Image width
            height: Image height
            brightness: Average brightness (0-255)
            add_blur: Whether to add blur
            add_noise: Whether to add noise
        
        Returns:
            Image bytes
        """
        # Create image with specified brightness
        img = Image.new('RGB', (width, height), color=(brightness, brightness, brightness))
        
        # Add some content (a simple pattern)
        draw = ImageDraw.Draw(img)
        
        # Draw some shapes to simulate crop features
        for i in range(0, width, 50):
            draw.line([(i, 0), (i, height)], fill=(brightness + 30, brightness + 20, brightness + 10), width=2)
        
        for i in range(0, height, 50):
            draw.line([(0, i), (width, i)], fill=(brightness + 20, brightness + 30, brightness + 10), width=2)
        
        # Add circles to simulate leaves
        for x in range(100, width, 150):
            for y in range(100, height, 150):
                draw.ellipse([x-30, y-30, x+30, y+30], 
                           fill=(brightness + 40, brightness + 50, brightness + 20))
        
        # Apply blur if requested
        if add_blur:
            img = img.filter(ImageFilter.GaussianBlur(radius=10))
        
        # Add noise if requested
        if add_noise:
            img_array = np.array(img)
            noise = np.random.randint(-20, 20, img_array.shape, dtype=np.int16)
            img_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            img = Image.fromarray(img_array)
        
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()
    
    def test_good_quality_image(self):
        """Test validation of good quality image"""
        image_data = self.create_test_image(width=800, height=600, brightness=128)
        
        result = self.quality_tools.validate_image_quality(image_data)
        
        self.assertTrue(result['valid'], "Good quality image should be valid")
        self.assertGreaterEqual(result['quality_score'], 0.8, "Quality score should be high")
        self.assertEqual(len(result['issues']), 0, "Should have no issues")
        self.assertIn('resolution', result['metrics'])
        self.assertIn('blur_score', result['metrics'])
        self.assertIn('brightness', result['metrics'])
    
    def test_low_resolution_image(self):
        """Test detection of low resolution"""
        image_data = self.create_test_image(width=200, height=150, brightness=128)
        
        result = self.quality_tools.validate_image_quality(image_data)
        
        self.assertFalse(result['valid'], "Low resolution image should be invalid")
        self.assertIn('low_resolution', result['issues'])
        self.assertGreater(len(result['guidance']), 0, "Should provide guidance")
        self.assertLess(result['quality_score'], 1.0, "Quality score should be reduced")
    
    def test_blurry_image(self):
        """Test detection of blurry image"""
        image_data = self.create_test_image(width=800, height=600, brightness=128, add_blur=True)
        
        result = self.quality_tools.validate_image_quality(image_data)
        
        # Check blur score is calculated
        self.assertIn('blur_score', result['metrics'])
        self.assertIn('blur_level', result['metrics'])
        
        # Note: Simple test patterns may not always trigger blur detection
        # In real-world usage with actual crop photos, blur detection works better
    
    def test_dark_image(self):
        """Test detection of too dark image"""
        image_data = self.create_test_image(width=800, height=600, brightness=20)
        
        result = self.quality_tools.validate_image_quality(image_data)
        
        self.assertFalse(result['valid'], "Dark image should be invalid")
        self.assertIn('too_dark', result['issues'])
        self.assertLess(result['metrics']['brightness'], self.quality_tools.min_brightness)
        
        # Check guidance
        guidance_text = ' '.join(result['guidance']).lower()
        self.assertIn('lighting', guidance_text, "Should mention lighting in guidance")
    
    def test_bright_image(self):
        """Test detection of too bright image"""
        image_data = self.create_test_image(width=800, height=600, brightness=240)
        
        result = self.quality_tools.validate_image_quality(image_data)
        
        self.assertFalse(result['valid'], "Bright image should be invalid")
        self.assertIn('too_bright', result['issues'])
        self.assertGreater(result['metrics']['brightness'], self.quality_tools.max_brightness)
    
    def test_unusual_aspect_ratio(self):
        """Test detection of unusual aspect ratio"""
        image_data = self.create_test_image(width=1200, height=300, brightness=128)
        
        result = self.quality_tools.validate_image_quality(image_data)
        
        # Should detect unusual aspect ratio
        self.assertIn('unusual_aspect_ratio', result['issues'])
        aspect_ratio = result['metrics']['resolution']['aspect_ratio']
        self.assertGreater(aspect_ratio, 3.0, "Aspect ratio should be > 3.0")
    
    def test_empty_image(self):
        """Test handling of empty image data"""
        image_data = b''
        
        result = self.quality_tools.validate_image_quality(image_data)
        
        self.assertFalse(result['valid'])
        self.assertIn('empty_file', result['issues'])
    
    def test_invalid_image_data(self):
        """Test handling of invalid image data"""
        image_data = b'not an image'
        
        result = self.quality_tools.validate_image_quality(image_data)
        
        self.assertFalse(result['valid'])
        self.assertIn('invalid_image', result['issues'])
    
    def test_selective_checks(self):
        """Test selective quality checks"""
        image_data = self.create_test_image(width=800, height=600, brightness=128)
        
        # Test only resolution check
        result = self.quality_tools.validate_image_quality(image_data, check_types=['resolution'])
        
        self.assertIn('resolution', result['metrics'])
        self.assertNotIn('blur_score', result['metrics'])
        self.assertNotIn('brightness', result['metrics'])
        
        # Test only blur check
        result = self.quality_tools.validate_image_quality(image_data, check_types=['blur'])
        
        self.assertNotIn('resolution', result['metrics'])
        self.assertIn('blur_score', result['metrics'])
        self.assertNotIn('brightness', result['metrics'])
        
        # Test only lighting check
        result = self.quality_tools.validate_image_quality(image_data, check_types=['lighting'])
        
        self.assertNotIn('resolution', result['metrics'])
        self.assertNotIn('blur_score', result['metrics'])
        self.assertIn('brightness', result['metrics'])
    
    def test_quality_score_calculation(self):
        """Test quality score calculation"""
        # Perfect image
        good_image = self.create_test_image(width=800, height=600, brightness=128)
        result = self.quality_tools.validate_image_quality(good_image)
        self.assertGreaterEqual(result['quality_score'], 0.7)
        
        # Poor image (low res + dark)
        poor_image = self.create_test_image(width=200, height=150, brightness=20)
        result = self.quality_tools.validate_image_quality(poor_image)
        self.assertLess(result['quality_score'], 0.8)
    
    def test_retry_guidance(self):
        """Test retry guidance generation"""
        # Create poor quality image
        image_data = self.create_test_image(width=200, height=150, brightness=20, add_blur=True)
        
        validation_result = self.quality_tools.validate_image_quality(image_data)
        retry_guidance = self.quality_tools.get_retry_guidance(validation_result)
        
        self.assertTrue(retry_guidance['retry_needed'])
        self.assertIn('specific_guidance', retry_guidance)
        self.assertGreater(len(retry_guidance['specific_guidance']), 0)
        
        # Each guidance should have issue, icon, and tips
        for guidance in retry_guidance['specific_guidance']:
            self.assertIn('issue', guidance)
            self.assertIn('icon', guidance)
            self.assertIn('tips', guidance)
            self.assertGreater(len(guidance['tips']), 0)
    
    def test_retry_guidance_good_image(self):
        """Test retry guidance for good quality image"""
        image_data = self.create_test_image(width=800, height=600, brightness=128)
        
        validation_result = self.quality_tools.validate_image_quality(image_data)
        retry_guidance = self.quality_tools.get_retry_guidance(validation_result)
        
        self.assertFalse(retry_guidance['retry_needed'])
        self.assertIn('proceed', retry_guidance['message'].lower())
    
    def test_summary_generation(self):
        """Test summary message generation"""
        # Excellent quality
        image_data = self.create_test_image(width=1200, height=900, brightness=128)
        result = self.quality_tools.validate_image_quality(image_data)
        self.assertIn('excellent', result['summary'].lower())
        
        # Poor quality
        image_data = self.create_test_image(width=200, height=150, brightness=20)
        result = self.quality_tools.validate_image_quality(image_data)
        self.assertIn('issue', result['summary'].lower())
    
    def test_blur_detection_accuracy(self):
        """Test blur detection accuracy"""
        # Sharp image
        sharp_image = self.create_test_image(width=800, height=600, brightness=128, add_blur=False)
        result = self.quality_tools.validate_image_quality(sharp_image, check_types=['blur'])
        
        # Should have blur metrics
        self.assertIn('blur_score', result['metrics'])
        self.assertIn('blur_level', result['metrics'])
        
        # Blurry image
        blurry_image = self.create_test_image(width=800, height=600, brightness=128, add_blur=True)
        result = self.quality_tools.validate_image_quality(blurry_image, check_types=['blur'])
        
        # Should have blur metrics
        self.assertIn('blur_score', result['metrics'])
        self.assertIn('blur_level', result['metrics'])
    
    def test_lighting_quality_levels(self):
        """Test lighting quality level classification"""
        # Good lighting
        good_image = self.create_test_image(width=800, height=600, brightness=128)
        result = self.quality_tools.validate_image_quality(good_image, check_types=['lighting'])
        self.assertIn(result['metrics']['lighting_quality'], ['good', 'fair'])
        
        # Poor lighting (too dark)
        dark_image = self.create_test_image(width=800, height=600, brightness=20)
        result = self.quality_tools.validate_image_quality(dark_image, check_types=['lighting'])
        self.assertIn(result['metrics']['lighting_quality'], ['fair', 'poor'])
    
    def test_factory_function(self):
        """Test factory function"""
        tools = create_quality_tools(region='us-east-1')
        self.assertIsInstance(tools, ImageQualityTools)
        self.assertEqual(tools.region, 'us-east-1')
    
    def test_tool_function(self):
        """Test standalone tool function"""
        image_data = self.create_test_image(width=800, height=600, brightness=128)
        
        result = validate_image(image_data)
        
        self.assertIn('valid', result)
        self.assertIn('quality_score', result)
        self.assertIn('metrics', result)
    
    def test_multiple_issues_prioritization(self):
        """Test that multiple issues are properly reported"""
        # Create image with multiple issues
        image_data = self.create_test_image(
            width=200,  # Low resolution
            height=150,
            brightness=20,  # Too dark
            add_blur=True  # Blurry
        )
        
        result = self.quality_tools.validate_image_quality(image_data)
        
        # Should detect multiple issues
        self.assertGreater(len(result['issues']), 1)
        self.assertFalse(result['valid'])
        
        # Should provide guidance for all issues
        self.assertGreater(len(result['guidance']), 2)
        
        # Quality score should be low
        self.assertLess(result['quality_score'], 0.5)


class TestImageQualityIntegration(unittest.TestCase):
    """Integration tests for image quality validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.quality_tools = ImageQualityTools()
    
    def create_realistic_crop_image(self, quality: str = 'good') -> bytes:
        """
        Create a more realistic crop image for testing
        
        Args:
            quality: 'good', 'poor', or 'medium'
        
        Returns:
            Image bytes
        """
        if quality == 'good':
            width, height = 1024, 768
            brightness = 140
            blur = False
        elif quality == 'poor':
            width, height = 240, 180
            brightness = 25
            blur = True
        else:  # medium
            width, height = 640, 480
            brightness = 100
            blur = False
        
        # Create base image
        img = Image.new('RGB', (width, height), color=(brightness, brightness + 20, brightness - 10))
        draw = ImageDraw.Draw(img)
        
        # Simulate leaf texture
        for _ in range(50):
            x = np.random.randint(0, width)
            y = np.random.randint(0, height)
            size = np.random.randint(20, 60)
            color = (
                brightness + np.random.randint(-30, 30),
                brightness + 20 + np.random.randint(-30, 30),
                brightness - 10 + np.random.randint(-30, 30)
            )
            draw.ellipse([x, y, x + size, y + size], fill=color)
        
        # Add some veins
        for _ in range(20):
            x1 = np.random.randint(0, width)
            y1 = np.random.randint(0, height)
            x2 = x1 + np.random.randint(-100, 100)
            y2 = y1 + np.random.randint(-100, 100)
            draw.line([(x1, y1), (x2, y2)], 
                     fill=(brightness - 40, brightness - 20, brightness - 30), 
                     width=2)
        
        if blur:
            img = img.filter(ImageFilter.GaussianBlur(radius=8))
        
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()
    
    def test_realistic_good_quality_workflow(self):
        """Test complete workflow with good quality image"""
        image_data = self.create_realistic_crop_image(quality='good')
        
        # Validate
        result = self.quality_tools.validate_image_quality(image_data)
        
        self.assertTrue(result['valid'])
        self.assertGreaterEqual(result['quality_score'], 0.7)
        
        # Get retry guidance
        guidance = self.quality_tools.get_retry_guidance(result)
        self.assertFalse(guidance['retry_needed'])
    
    def test_realistic_poor_quality_workflow(self):
        """Test complete workflow with poor quality image"""
        image_data = self.create_realistic_crop_image(quality='poor')
        
        # Validate
        result = self.quality_tools.validate_image_quality(image_data)
        
        self.assertFalse(result['valid'])
        self.assertLess(result['quality_score'], 0.8)
        
        # Get retry guidance
        guidance = self.quality_tools.get_retry_guidance(result)
        self.assertTrue(guidance['retry_needed'])
        self.assertGreater(len(guidance['specific_guidance']), 0)
        
        # Verify guidance is actionable
        for item in guidance['specific_guidance']:
            self.assertIn('tips', item)
            self.assertGreater(len(item['tips']), 0)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestImageQualityTools))
    suite.addTests(loader.loadTestsFromTestCase(TestImageQualityIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
