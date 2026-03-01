"""
RISE Disease Identification Integration Example
Demonstrates how to use the crop disease identification tools
"""

import sys
import os
from PIL import Image
import io

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.disease_identification_tools import DiseaseIdentificationTools


def create_sample_image():
    """Create a sample test image"""
    # Create a simple green image (simulating a crop)
    img = Image.new('RGB', (800, 600), color=(34, 139, 34))  # Forest green
    
    # Add some brown spots (simulating disease)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Draw some circular spots
    draw.ellipse([100, 100, 150, 150], fill=(139, 69, 19))  # Brown spot
    draw.ellipse([300, 200, 360, 260], fill=(139, 69, 19))
    draw.ellipse([500, 400, 570, 470], fill=(139, 69, 19))
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes.read()


def example_basic_analysis():
    """Example: Basic disease analysis"""
    print("=" * 60)
    print("Example 1: Basic Disease Analysis")
    print("=" * 60)
    
    # Initialize tools
    tools = DiseaseIdentificationTools(region='us-east-1')
    
    # Create sample image
    image_data = create_sample_image()
    
    print(f"Image size: {len(image_data) / 1024:.1f} KB")
    
    # Analyze image
    print("\nAnalyzing image...")
    result = tools.analyze_crop_image(
        image_data=image_data,
        user_id='example_farmer_001',
        crop_type='wheat',
        additional_context='Noticed brown spots on leaves'
    )
    
    # Display results
    if result['success']:
        print("\n✅ Analysis successful!")
        print(f"\nDiagnosis ID: {result['diagnosis_id']}")
        print(f"Diseases: {', '.join(result['diseases'])}")
        print(f"Severity: {result['severity']}")
        print(f"Confidence: {result['confidence_score']*100:.1f}%")
        print(f"Multiple Issues: {result['multiple_issues']}")
        print(f"\nStored in S3: {result['s3_key']}")
        
        print("\n" + "=" * 60)
        print("Full Analysis:")
        print("=" * 60)
        print(result['full_analysis'])
    else:
        print(f"\n❌ Analysis failed: {result.get('error')}")
        if 'validation' in result:
            print(f"Validation issues: {result['validation']}")


def example_image_validation():
    """Example: Image quality validation"""
    print("\n" + "=" * 60)
    print("Example 2: Image Quality Validation")
    print("=" * 60)
    
    tools = DiseaseIdentificationTools(region='us-east-1')
    
    # Test with good quality image
    good_image = create_sample_image()
    
    print("\nValidating good quality image...")
    validation = tools.validate_image_quality(good_image)
    
    print(f"Valid: {validation['valid']}")
    print(f"Dimensions: {validation['dimensions']}")
    print(f"File size: {validation['file_size_kb']:.1f} KB")
    
    if validation['issues']:
        print(f"Issues: {validation['issues']}")
        print(f"Guidance: {validation['guidance']}")
    else:
        print("✅ No quality issues detected")
    
    # Test with low resolution image
    print("\n" + "-" * 60)
    print("Validating low resolution image...")
    
    small_img = Image.new('RGB', (200, 150), color='green')
    small_bytes = io.BytesIO()
    small_img.save(small_bytes, format='JPEG')
    small_bytes.seek(0)
    
    validation = tools.validate_image_quality(small_bytes.read())
    
    print(f"Valid: {validation['valid']}")
    print(f"Dimensions: {validation['dimensions']}")
    
    if validation['issues']:
        print(f"Issues: {validation['issues']}")
        print("Guidance:")
        for guide in validation['guidance']:
            print(f"  - {guide}")


def example_image_compression():
    """Example: Image compression"""
    print("\n" + "=" * 60)
    print("Example 3: Image Compression")
    print("=" * 60)
    
    tools = DiseaseIdentificationTools(region='us-east-1')
    
    # Create a large image
    large_img = Image.new('RGB', (2000, 1500), color='green')
    large_bytes = io.BytesIO()
    large_img.save(large_bytes, format='JPEG', quality=95)
    large_bytes.seek(0)
    original_data = large_bytes.read()
    
    print(f"Original size: {len(original_data) / 1024:.1f} KB")
    
    # Compress to 500KB
    print("\nCompressing to 500KB...")
    compressed = tools.compress_image(original_data, max_size_kb=500)
    
    print(f"Compressed size: {len(compressed) / 1024:.1f} KB")
    print(f"Compression ratio: {len(compressed) / len(original_data) * 100:.1f}%")
    
    # Verify compressed image is still valid
    compressed_img = Image.open(io.BytesIO(compressed))
    print(f"Compressed dimensions: {compressed_img.size}")
    print(f"Format: {compressed_img.format}")


def example_diagnosis_history():
    """Example: Retrieve diagnosis history"""
    print("\n" + "=" * 60)
    print("Example 4: Diagnosis History")
    print("=" * 60)
    
    tools = DiseaseIdentificationTools(region='us-east-1')
    
    user_id = 'example_farmer_001'
    
    print(f"\nRetrieving diagnosis history for {user_id}...")
    history = tools.get_diagnosis_history(user_id, limit=5)
    
    if history:
        print(f"\nFound {len(history)} diagnoses:")
        
        for i, diagnosis in enumerate(history, 1):
            print(f"\n{i}. Diagnosis ID: {diagnosis.get('diagnosis_id')}")
            print(f"   Crop: {diagnosis.get('crop_type')}")
            print(f"   Diseases: {', '.join(diagnosis.get('diseases', []))}")
            print(f"   Severity: {diagnosis.get('severity')}")
            print(f"   Confidence: {diagnosis.get('confidence_score', 0)*100:.0f}%")
            print(f"   Status: {diagnosis.get('follow_up_status')}")
            print(f"   Date: {diagnosis.get('created_timestamp')}")
    else:
        print("No diagnosis history found")


def example_follow_up_update():
    """Example: Update follow-up status"""
    print("\n" + "=" * 60)
    print("Example 5: Update Follow-up Status")
    print("=" * 60)
    
    tools = DiseaseIdentificationTools(region='us-east-1')
    
    # First, create a diagnosis
    image_data = create_sample_image()
    
    print("Creating initial diagnosis...")
    result = tools.analyze_crop_image(
        image_data=image_data,
        user_id='example_farmer_001',
        crop_type='wheat'
    )
    
    if result['success']:
        diagnosis_id = result['diagnosis_id']
        print(f"Diagnosis created: {diagnosis_id}")
        
        # Update follow-up status
        print("\nUpdating follow-up status...")
        success = tools.update_follow_up_status(
            diagnosis_id=diagnosis_id,
            status='treated',
            notes='Applied recommended fungicide. Symptoms improving after 3 days.'
        )
        
        if success:
            print("✅ Follow-up status updated successfully")
        else:
            print("❌ Failed to update follow-up status")
    else:
        print(f"Failed to create diagnosis: {result.get('error')}")


def example_multilingual_analysis():
    """Example: Analysis with different languages"""
    print("\n" + "=" * 60)
    print("Example 6: Multilingual Analysis")
    print("=" * 60)
    
    tools = DiseaseIdentificationTools(region='us-east-1')
    
    image_data = create_sample_image()
    
    languages = [
        ('en', 'English'),
        ('hi', 'Hindi'),
        ('ta', 'Tamil')
    ]
    
    for lang_code, lang_name in languages:
        print(f"\nAnalyzing in {lang_name} ({lang_code})...")
        
        # Note: The actual translation would happen in the prompt
        # This example shows how to pass language preference
        result = tools.analyze_crop_image(
            image_data=image_data,
            user_id=f'example_farmer_{lang_code}',
            crop_type='wheat',
            additional_context=f'Analysis requested in {lang_name}'
        )
        
        if result['success']:
            print(f"✅ Analysis completed")
            print(f"   Diagnosis ID: {result['diagnosis_id']}")
            print(f"   Diseases: {', '.join(result['diseases'])}")
        else:
            print(f"❌ Analysis failed: {result.get('error')}")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("RISE Disease Identification Examples")
    print("=" * 60)
    
    try:
        # Run examples
        example_basic_analysis()
        example_image_validation()
        example_image_compression()
        example_diagnosis_history()
        example_follow_up_update()
        example_multilingual_analysis()
        
        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
