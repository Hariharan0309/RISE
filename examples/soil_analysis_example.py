"""
RISE Soil Analysis System - Usage Examples

This module demonstrates how to use the soil analysis tools for:
1. Image-based soil analysis
2. Manual soil test data analysis
3. Crop recommendations
4. Deficiency reports
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.soil_analysis_tools import SoilAnalysisTools
import json


def example_1_image_analysis():
    """
    Example 1: Analyze soil from an image
    
    This example shows how to:
    - Load a soil sample image
    - Analyze it using Bedrock multimodal
    - Get soil type, fertility, and recommendations
    """
    print("=" * 80)
    print("EXAMPLE 1: Image-Based Soil Analysis")
    print("=" * 80)
    
    # Initialize tools
    soil_tools = SoilAnalysisTools(region='us-east-1')
    
    # In a real scenario, you would load an actual image
    # For this example, we'll create a dummy image
    from PIL import Image
    import io
    
    # Create a sample soil image (brown color)
    img = Image.new('RGB', (800, 600), color=(139, 90, 43))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    image_data = img_bytes.read()
    
    print("\n📸 Analyzing soil image...")
    print(f"Image size: {len(image_data)} bytes")
    
    # Analyze soil
    result = soil_tools.analyze_soil_from_image(
        image_data=image_data,
        user_id='farmer_ravi_001',
        farm_id='farm_up_bangalore_001',
        location={
            'state': 'Karnataka',
            'district': 'Bangalore Rural'
        }
    )
    
    if result['success']:
        print("\n✅ Analysis Complete!")
        print(f"\n🌱 Soil Type: {result['soil_type'].title()}")
        print(f"📊 Fertility Level: {result['fertility_level'].title()}")
        
        if result.get('ph_level'):
            print(f"🧪 pH Level: {result['ph_level']}")
        
        if result.get('npk_levels'):
            print(f"\n💊 NPK Levels:")
            print(f"  - Nitrogen (N): {result['npk_levels'].get('nitrogen', 'unknown').title()}")
            print(f"  - Phosphorus (P): {result['npk_levels'].get('phosphorus', 'unknown').title()}")
            print(f"  - Potassium (K): {result['npk_levels'].get('potassium', 'unknown').title()}")
        
        if result.get('organic_matter'):
            print(f"\n🍂 Organic Matter: {result['organic_matter']}%")
        
        if result.get('deficiencies'):
            print(f"\n⚠️  Deficiencies Identified:")
            for deficiency in result['deficiencies']:
                print(f"  - {deficiency}")
        
        if result.get('suitable_crops'):
            print(f"\n🌾 Suitable Crops:")
            for crop in result['suitable_crops'][:5]:
                print(f"  - {crop}")
        
        print(f"\n📝 Analysis ID: {result['analysis_id']}")
        print(f"💾 Stored in S3: {result.get('s3_key', 'N/A')}")
    else:
        print(f"\n❌ Analysis failed: {result.get('error')}")
    
    print("\n" + "=" * 80 + "\n")


def example_2_test_data_analysis():
    """
    Example 2: Analyze soil from manual test data
    
    This example shows how to:
    - Input soil test results manually
    - Get comprehensive analysis and recommendations
    - Understand nutrient levels and deficiencies
    """
    print("=" * 80)
    print("EXAMPLE 2: Soil Test Data Analysis")
    print("=" * 80)
    
    # Initialize tools
    soil_tools = SoilAnalysisTools(region='us-east-1')
    
    # Sample soil test data (from laboratory)
    test_data = {
        'ph': 6.5,
        'nitrogen': 'low',  # Can also be numeric (e.g., 150 kg/ha)
        'phosphorus': 'medium',
        'potassium': 'high',
        'organic_matter': 2.5,  # percentage
        'texture': 'loam',
        'electrical_conductivity': 0.4,  # dS/m
        'calcium': 'medium',
        'magnesium': 'medium',
        'sulfur': 'low',
        'zinc': 'low',
        'iron': 'medium'
    }
    
    print("\n📋 Soil Test Data:")
    print(json.dumps(test_data, indent=2))
    
    print("\n🔬 Analyzing test data...")
    
    # Analyze test data
    result = soil_tools.analyze_soil_from_test_data(
        test_data=test_data,
        user_id='farmer_lakshmi_002',
        farm_id='farm_karnataka_002',
        location={
            'state': 'Karnataka',
            'district': 'Mysore'
        }
    )
    
    if result['success']:
        print("\n✅ Analysis Complete!")
        print(f"\n🌱 Soil Type: {result['soil_type'].title()}")
        print(f"📊 Fertility Level: {result['fertility_level'].title()}")
        
        if result.get('ph_level'):
            ph = result['ph_level']
            if ph < 6.0:
                ph_status = "Acidic"
            elif ph > 7.5:
                ph_status = "Alkaline"
            else:
                ph_status = "Neutral (Optimal)"
            print(f"🧪 pH Level: {ph} ({ph_status})")
        
        if result.get('deficiencies'):
            print(f"\n⚠️  Deficiencies Identified:")
            for deficiency in result['deficiencies']:
                print(f"  - {deficiency}")
        
        if result.get('recommendations'):
            recs = result['recommendations']
            
            if recs.get('organic_amendments'):
                print(f"\n🌿 Organic Amendment Recommendations:")
                for rec in recs['organic_amendments']:
                    print(f"  - {rec}")
            
            if recs.get('chemical_amendments'):
                print(f"\n💊 Chemical Amendment Recommendations:")
                for rec in recs['chemical_amendments']:
                    print(f"  - {rec}")
        
        print(f"\n📝 Analysis ID: {result['analysis_id']}")
    else:
        print(f"\n❌ Analysis failed: {result.get('error')}")
    
    print("\n" + "=" * 80 + "\n")


def example_3_crop_recommendations():
    """
    Example 3: Get crop recommendations based on soil conditions
    
    This example shows how to:
    - Get crop recommendations for specific soil type
    - Consider climate and market factors
    - Understand expected yields and profitability
    """
    print("=" * 80)
    print("EXAMPLE 3: Crop Recommendations")
    print("=" * 80)
    
    # Initialize tools
    soil_tools = SoilAnalysisTools(region='us-east-1')
    
    # Soil conditions
    soil_type = 'loam'
    fertility_level = 'medium'
    location = {
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
    
    # Optional climate data
    climate_data = {
        'annual_rainfall': 700,  # mm
        'temperature_range': [5, 40],  # Celsius (min, max)
        'season': 'kharif'  # or 'rabi'
    }
    
    print(f"\n🌱 Soil Type: {soil_type.title()}")
    print(f"📊 Fertility Level: {fertility_level.title()}")
    print(f"📍 Location: {location['district']}, {location['state']}")
    print(f"🌦️  Climate: {climate_data['annual_rainfall']}mm rainfall, {climate_data['temperature_range'][0]}-{climate_data['temperature_range'][1]}°C")
    
    print("\n🔍 Getting crop recommendations...")
    
    # Get recommendations
    result = soil_tools.get_crop_recommendations(
        soil_type=soil_type,
        fertility_level=fertility_level,
        location=location,
        climate_data=climate_data
    )
    
    if result['success']:
        print("\n✅ Recommendations Ready!")
        
        if result.get('highly_suitable_crops'):
            print(f"\n🌾 Highly Suitable Crops:")
            for crop in result['highly_suitable_crops']:
                print(f"  ✓ {crop}")
        
        if result.get('moderately_suitable_crops'):
            print(f"\n🌿 Moderately Suitable Crops:")
            for crop in result['moderately_suitable_crops']:
                print(f"  ~ {crop}")
        
        if result.get('not_recommended_crops'):
            print(f"\n❌ Not Recommended Crops:")
            for crop in result['not_recommended_crops']:
                print(f"  ✗ {crop}")
        
        print(f"\n📄 Full recommendations available in result['full_recommendations']")
    else:
        print(f"\n❌ Failed to get recommendations: {result.get('error')}")
    
    print("\n" + "=" * 80 + "\n")


def example_4_deficiency_report():
    """
    Example 4: Generate detailed deficiency report
    
    This example shows how to:
    - Generate comprehensive deficiency analysis
    - Get specific amendment recommendations
    - Understand costs and application methods
    """
    print("=" * 80)
    print("EXAMPLE 4: Soil Deficiency Report")
    print("=" * 80)
    
    # Initialize tools
    soil_tools = SoilAnalysisTools(region='us-east-1')
    
    # Identified deficiencies
    deficiencies = [
        'Nitrogen deficiency',
        'Low organic matter content',
        'Zinc deficiency'
    ]
    
    soil_type = 'clay'
    location = {
        'state': 'Uttar Pradesh',
        'district': 'Meerut'
    }
    
    print(f"\n⚠️  Identified Deficiencies:")
    for deficiency in deficiencies:
        print(f"  - {deficiency}")
    
    print(f"\n🌱 Soil Type: {soil_type.title()}")
    print(f"📍 Location: {location['district']}, {location['state']}")
    
    print("\n📊 Generating comprehensive deficiency report...")
    
    # Generate report
    result = soil_tools.generate_deficiency_report(
        deficiencies=deficiencies,
        soil_type=soil_type,
        location=location
    )
    
    if result['success']:
        print("\n✅ Report Generated!")
        print("\n" + "=" * 80)
        print("DEFICIENCY REPORT")
        print("=" * 80)
        print(result['report'])
        print("=" * 80)
    else:
        print(f"\n❌ Failed to generate report: {result.get('error')}")
    
    print("\n" + "=" * 80 + "\n")


def example_5_complete_workflow():
    """
    Example 5: Complete soil analysis workflow
    
    This example demonstrates a complete workflow:
    1. Analyze soil (image or test data)
    2. Identify deficiencies
    3. Get crop recommendations
    4. Generate amendment plan
    """
    print("=" * 80)
    print("EXAMPLE 5: Complete Soil Analysis Workflow")
    print("=" * 80)
    
    # Initialize tools
    soil_tools = SoilAnalysisTools(region='us-east-1')
    
    # Step 1: Analyze soil from test data
    print("\n📋 STEP 1: Soil Analysis")
    print("-" * 80)
    
    test_data = {
        'ph': 5.8,  # Slightly acidic
        'nitrogen': 'low',
        'phosphorus': 'low',
        'potassium': 'medium',
        'organic_matter': 1.5,  # Low
        'texture': 'sandy loam'
    }
    
    print("Test Data:", json.dumps(test_data, indent=2))
    
    analysis = soil_tools.analyze_soil_from_test_data(
        test_data=test_data,
        user_id='farmer_arjun_003',
        farm_id='farm_punjab_003',
        location={
            'state': 'Punjab',
            'district': 'Amritsar'
        }
    )
    
    if not analysis['success']:
        print(f"❌ Analysis failed: {analysis.get('error')}")
        return
    
    print(f"✅ Soil Type: {analysis['soil_type'].title()}")
    print(f"✅ Fertility: {analysis['fertility_level'].title()}")
    print(f"✅ pH: {analysis.get('ph_level', 'N/A')}")
    
    # Step 2: Identify deficiencies
    print("\n⚠️  STEP 2: Deficiency Identification")
    print("-" * 80)
    
    deficiencies = analysis.get('deficiencies', [])
    if deficiencies:
        for i, deficiency in enumerate(deficiencies, 1):
            print(f"{i}. {deficiency}")
    else:
        print("No major deficiencies identified")
    
    # Step 3: Get crop recommendations
    print("\n🌾 STEP 3: Crop Recommendations")
    print("-" * 80)
    
    crop_recs = soil_tools.get_crop_recommendations(
        soil_type=analysis['soil_type'],
        fertility_level=analysis['fertility_level'],
        location={'state': 'Punjab', 'district': 'Amritsar'}
    )
    
    if crop_recs['success']:
        print("Highly Suitable Crops:")
        for crop in crop_recs.get('highly_suitable_crops', [])[:3]:
            print(f"  ✓ {crop}")
    
    # Step 4: Generate amendment plan
    if deficiencies:
        print("\n💊 STEP 4: Amendment Plan")
        print("-" * 80)
        
        report = soil_tools.generate_deficiency_report(
            deficiencies=deficiencies,
            soil_type=analysis['soil_type'],
            location={'state': 'Punjab', 'district': 'Amritsar'}
        )
        
        if report['success']:
            print("✅ Comprehensive amendment plan generated")
            print("📄 See full report for detailed recommendations")
    
    # Step 5: Summary
    print("\n📊 STEP 5: Summary & Next Steps")
    print("-" * 80)
    print(f"✓ Soil analyzed and classified as {analysis['soil_type']}")
    print(f"✓ {len(deficiencies)} deficiencies identified")
    print(f"✓ Crop recommendations provided")
    print(f"✓ Amendment plan generated")
    print("\nNext Steps:")
    print("1. Review full analysis and recommendations")
    print("2. Procure recommended amendments")
    print("3. Apply amendments as per schedule")
    print("4. Select suitable crops for planting")
    print("5. Monitor soil health and retest in 6 months")
    
    print("\n" + "=" * 80 + "\n")


def example_6_image_quality_tips():
    """
    Example 6: Image quality validation and tips
    
    This example shows:
    - How to validate image quality
    - Common issues and solutions
    - Best practices for soil photography
    """
    print("=" * 80)
    print("EXAMPLE 6: Image Quality Validation")
    print("=" * 80)
    
    # Initialize tools
    soil_tools = SoilAnalysisTools(region='us-east-1')
    
    print("\n📸 Image Quality Requirements:")
    print("-" * 80)
    print("✓ Minimum Resolution: 300x300 pixels (recommended: 800x600+)")
    print("✓ Format: JPEG or PNG")
    print("✓ Maximum Size: 5MB")
    print("✓ Lighting: Natural daylight, avoid harsh shadows")
    print("✓ Focus: Clear, sharp image")
    print("✓ Angle: Top-down view of soil surface")
    
    print("\n📋 Best Practices:")
    print("-" * 80)
    print("1. Take photos during daytime with good natural light")
    print("2. Avoid direct sunlight - use diffused light or shade")
    print("3. Ensure soil sample is clean and representative")
    print("4. Capture from directly above the soil sample")
    print("5. Avoid blurry or overexposed images")
    print("6. Include multiple samples from different areas")
    
    # Test with a low-resolution image
    print("\n🔍 Testing Image Validation:")
    print("-" * 80)
    
    from PIL import Image
    import io
    
    # Create a low-resolution image
    small_img = Image.new('RGB', (200, 150), color=(139, 90, 43))
    small_bytes = io.BytesIO()
    small_img.save(small_bytes, format='JPEG')
    small_bytes.seek(0)
    
    validation = soil_tools._validate_image(small_bytes.read())
    
    if validation['valid']:
        print("✅ Image quality is acceptable")
    else:
        print("❌ Image quality issues detected:")
        for issue in validation['issues']:
            print(f"  - {issue}")
        print("\n💡 Recommendations:")
        print("  - Use a higher resolution camera or phone")
        print("  - Ensure camera settings are at maximum quality")
        print("  - Get closer to the soil sample for more detail")
    
    print("\n" + "=" * 80 + "\n")


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "RISE SOIL ANALYSIS SYSTEM" + " " * 33 + "║")
    print("║" + " " * 25 + "Usage Examples" + " " * 38 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    examples = [
        ("Image-Based Analysis", example_1_image_analysis),
        ("Test Data Analysis", example_2_test_data_analysis),
        ("Crop Recommendations", example_3_crop_recommendations),
        ("Deficiency Report", example_4_deficiency_report),
        ("Complete Workflow", example_5_complete_workflow),
        ("Image Quality Tips", example_6_image_quality_tips)
    ]
    
    print("Available Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nRunning all examples...\n")
    
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 28 + "Examples Complete!" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")


if __name__ == "__main__":
    # Note: These examples use mock data and may not work without proper AWS credentials
    # and Bedrock access. They demonstrate the API usage patterns.
    
    print("\n⚠️  NOTE: These examples require AWS credentials and Bedrock access.")
    print("They demonstrate API usage patterns with mock data.\n")
    
    # Uncomment to run examples
    # main()
    
    # Or run individual examples
    print("To run examples, uncomment the main() call or run individual examples:")
    print("  example_1_image_analysis()")
    print("  example_2_test_data_analysis()")
    print("  example_3_crop_recommendations()")
    print("  example_4_deficiency_report()")
    print("  example_5_complete_workflow()")
    print("  example_6_image_quality_tips()")
