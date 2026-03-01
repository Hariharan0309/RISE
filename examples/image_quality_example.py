"""
Example: Image Quality Validation
Demonstrates how to use the image quality validation system
"""

import sys
import os
from PIL import Image, ImageDraw, ImageFilter
import io

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.image_quality_tools import ImageQualityTools, validate_image


def create_sample_images():
    """Create sample images with different quality levels"""
    
    samples = {}
    
    # 1. Good quality image
    print("Creating good quality image...")
    img = Image.new('RGB', (1024, 768), color=(140, 160, 120))
    draw = ImageDraw.Draw(img)
    
    # Add leaf-like patterns
    for i in range(20):
        x = 100 + i * 40
        y = 100 + (i % 5) * 120
        draw.ellipse([x, y, x+80, y+60], fill=(100, 180, 80))
        draw.line([(x+40, y), (x+40, y+60)], fill=(80, 140, 60), width=3)
    
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=90)
    samples['good'] = buffer.getvalue()
    
    # 2. Low resolution image
    print("Creating low resolution image...")
    img_small = Image.new('RGB', (200, 150), color=(140, 160, 120))
    draw = ImageDraw.Draw(img_small)
    draw.ellipse([50, 50, 150, 100], fill=(100, 180, 80))
    
    buffer = io.BytesIO()
    img_small.save(buffer, format='JPEG', quality=90)
    samples['low_res'] = buffer.getvalue()
    
    # 3. Blurry image
    print("Creating blurry image...")
    img_blur = Image.new('RGB', (800, 600), color=(140, 160, 120))
    draw = ImageDraw.Draw(img_blur)
    
    for i in range(15):
        x = 80 + i * 50
        y = 80 + (i % 4) * 120
        draw.ellipse([x, y, x+70, y+50], fill=(100, 180, 80))
    
    img_blur = img_blur.filter(ImageFilter.GaussianBlur(radius=10))
    
    buffer = io.BytesIO()
    img_blur.save(buffer, format='JPEG', quality=90)
    samples['blurry'] = buffer.getvalue()
    
    # 4. Dark image
    print("Creating dark image...")
    img_dark = Image.new('RGB', (800, 600), color=(20, 25, 18))
    draw = ImageDraw.Draw(img_dark)
    
    for i in range(10):
        x = 100 + i * 60
        y = 100 + (i % 3) * 150
        draw.ellipse([x, y, x+60, y+50], fill=(40, 50, 35))
    
    buffer = io.BytesIO()
    img_dark.save(buffer, format='JPEG', quality=90)
    samples['dark'] = buffer.getvalue()
    
    # 5. Bright image
    print("Creating bright image...")
    img_bright = Image.new('RGB', (800, 600), color=(240, 245, 235))
    draw = ImageDraw.Draw(img_bright)
    
    for i in range(10):
        x = 100 + i * 60
        y = 100 + (i % 3) * 150
        draw.ellipse([x, y, x+60, y+50], fill=(220, 230, 210))
    
    buffer = io.BytesIO()
    img_bright.save(buffer, format='JPEG', quality=90)
    samples['bright'] = buffer.getvalue()
    
    return samples


def example_basic_validation():
    """Example 1: Basic image quality validation"""
    
    print("\n" + "="*60)
    print("Example 1: Basic Image Quality Validation")
    print("="*60)
    
    # Create sample images
    samples = create_sample_images()
    
    # Initialize quality tools
    quality_tools = ImageQualityTools()
    
    # Validate each sample
    for name, image_data in samples.items():
        print(f"\n--- Validating {name} image ---")
        
        result = quality_tools.validate_image_quality(image_data)
        
        print(f"Valid: {result['valid']}")
        print(f"Quality Score: {result['quality_score']}")
        print(f"Summary: {result['summary']}")
        
        if result['issues']:
            print(f"Issues: {', '.join(result['issues'])}")
        
        if result['metrics']:
            print(f"Metrics:")
            for key, value in result['metrics'].items():
                print(f"  - {key}: {value}")


def example_selective_checks():
    """Example 2: Selective quality checks"""
    
    print("\n" + "="*60)
    print("Example 2: Selective Quality Checks")
    print("="*60)
    
    samples = create_sample_images()
    quality_tools = ImageQualityTools()
    
    image_data = samples['good']
    
    # Check only resolution
    print("\n--- Resolution check only ---")
    result = quality_tools.validate_image_quality(image_data, check_types=['resolution'])
    print(f"Valid: {result['valid']}")
    print(f"Metrics: {result['metrics']}")
    
    # Check only blur
    print("\n--- Blur check only ---")
    result = quality_tools.validate_image_quality(image_data, check_types=['blur'])
    print(f"Valid: {result['valid']}")
    print(f"Blur Score: {result['metrics'].get('blur_score', 'N/A')}")
    print(f"Blur Level: {result['metrics'].get('blur_level', 'N/A')}")
    
    # Check only lighting
    print("\n--- Lighting check only ---")
    result = quality_tools.validate_image_quality(image_data, check_types=['lighting'])
    print(f"Valid: {result['valid']}")
    print(f"Brightness: {result['metrics'].get('brightness', 'N/A')}")
    print(f"Contrast: {result['metrics'].get('contrast', 'N/A')}")
    print(f"Lighting Quality: {result['metrics'].get('lighting_quality', 'N/A')}")


def example_retry_guidance():
    """Example 3: Retry guidance for poor quality images"""
    
    print("\n" + "="*60)
    print("Example 3: Retry Guidance")
    print("="*60)
    
    samples = create_sample_images()
    quality_tools = ImageQualityTools()
    
    # Test with poor quality images
    for name in ['low_res', 'blurry', 'dark']:
        print(f"\n--- Retry guidance for {name} image ---")
        
        image_data = samples[name]
        
        # Validate
        result = quality_tools.validate_image_quality(image_data)
        
        # Get retry guidance
        guidance = quality_tools.get_retry_guidance(result)
        
        print(f"Retry Needed: {guidance['retry_needed']}")
        print(f"Message: {guidance['message']}")
        
        if guidance['retry_needed']:
            print(f"\nTop Issues: {', '.join(guidance['top_issues'])}")
            print(f"\nSpecific Guidance:")
            
            for item in guidance['specific_guidance']:
                print(f"\n{item['icon']} {item['issue']}:")
                for tip in item['tips']:
                    print(f"  • {tip}")


def example_custom_thresholds():
    """Example 4: Custom quality thresholds"""
    
    print("\n" + "="*60)
    print("Example 4: Custom Quality Thresholds")
    print("="*60)
    
    samples = create_sample_images()
    
    # Default thresholds
    print("\n--- With default thresholds ---")
    quality_tools_default = ImageQualityTools()
    result = quality_tools_default.validate_image_quality(samples['dark'])
    print(f"Dark image valid: {result['valid']}")
    print(f"Issues: {result['issues']}")
    
    # Relaxed thresholds (more permissive)
    print("\n--- With relaxed thresholds ---")
    quality_tools_relaxed = ImageQualityTools()
    quality_tools_relaxed.min_brightness = 15  # Lower threshold
    quality_tools_relaxed.blur_threshold = 50.0  # Lower threshold
    
    result = quality_tools_relaxed.validate_image_quality(samples['dark'])
    print(f"Dark image valid: {result['valid']}")
    print(f"Issues: {result['issues']}")
    
    # Strict thresholds (more restrictive)
    print("\n--- With strict thresholds ---")
    quality_tools_strict = ImageQualityTools()
    quality_tools_strict.min_resolution = 500  # Higher threshold
    quality_tools_strict.blur_threshold = 150.0  # Higher threshold
    
    result = quality_tools_strict.validate_image_quality(samples['good'])
    print(f"Good image valid: {result['valid']}")
    print(f"Issues: {result['issues']}")


def example_workflow_integration():
    """Example 5: Integration with disease identification workflow"""
    
    print("\n" + "="*60)
    print("Example 5: Workflow Integration")
    print("="*60)
    
    samples = create_sample_images()
    quality_tools = ImageQualityTools()
    
    def process_crop_image(image_data, crop_type="wheat"):
        """Simulate disease identification workflow"""
        
        print(f"\n--- Processing {crop_type} image ---")
        
        # Step 1: Validate image quality
        print("Step 1: Validating image quality...")
        validation = quality_tools.validate_image_quality(image_data)
        
        if not validation['valid']:
            print(f"❌ Image quality check failed!")
            print(f"Quality Score: {validation['quality_score']}")
            
            # Get retry guidance
            guidance = quality_tools.get_retry_guidance(validation)
            print(f"\n{guidance['message']}")
            
            if guidance['specific_guidance']:
                print("\nPlease address these issues:")
                for item in guidance['specific_guidance']:
                    print(f"  {item['icon']} {item['issue']}")
            
            return None
        
        print(f"✅ Image quality check passed!")
        print(f"Quality Score: {validation['quality_score']}")
        
        # Step 2: Proceed with disease identification
        print("\nStep 2: Analyzing with Amazon Bedrock...")
        print("(Simulated - would call Bedrock here)")
        
        # Step 3: Return results
        print("\nStep 3: Returning diagnosis results...")
        return {
            'diagnosis_id': 'diag_example_123',
            'diseases': ['Leaf Rust'],
            'confidence': 0.87,
            'quality_score': validation['quality_score']
        }
    
    # Test with different quality images
    for name in ['good', 'low_res', 'dark']:
        result = process_crop_image(samples[name])
        
        if result:
            print(f"\n✅ Diagnosis completed: {result['diseases']}")
        else:
            print(f"\n❌ Diagnosis aborted due to poor image quality")


def example_standalone_function():
    """Example 6: Using standalone validation function"""
    
    print("\n" + "="*60)
    print("Example 6: Standalone Validation Function")
    print("="*60)
    
    samples = create_sample_images()
    
    # Use standalone function (simpler API)
    print("\n--- Using validate_image() function ---")
    
    result = validate_image(samples['good'])
    
    print(f"Valid: {result['valid']}")
    print(f"Quality Score: {result['quality_score']}")
    print(f"Summary: {result['summary']}")


def main():
    """Run all examples"""
    
    print("\n" + "="*60)
    print("RISE Image Quality Validation Examples")
    print("="*60)
    
    try:
        # Run examples
        example_basic_validation()
        example_selective_checks()
        example_retry_guidance()
        example_custom_thresholds()
        example_workflow_integration()
        example_standalone_function()
        
        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
