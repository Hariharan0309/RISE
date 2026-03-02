"""
RISE Fertilizer Recommendation System - Usage Examples

This module demonstrates how to use the fertilizer recommendation tools for:
1. NPK requirement calculations
2. Precision fertilizer recommendations
3. Weather-based application timing
4. Crop growth stage tracking
5. Amendment suggestions (organic and chemical)
6. Cost-effective solution prioritization
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.fertilizer_recommendation_tools import FertilizerRecommendationTools
import json


def example_1_npk_calculation():
    """
    Example 1: Calculate NPK requirements based on soil analysis
    
    This example shows how to:
    - Use soil analysis results to calculate NPK needs
    - Get precise quantities for target crop
    - Understand split application schedules
    """
    print("=" * 80)
    print("EXAMPLE 1: NPK Requirement Calculation")
    print("=" * 80)
    
    # Initialize tools
    fert_tools = FertilizerRecommendationTools(region='us-east-1')
    
    # Soil analysis from previous soil analysis
    soil_analysis = {
        'soil_type': 'loam',
        'fertility_level': 'medium',
        'ph_level': 6.5,
        'npk_levels': {
            'nitrogen': 'low',
            'phosphorus': 'medium',
            'potassium': 'high'
        },
        'organic_matter': 2.5,
        'deficiencies': ['Nitrogen deficiency', 'Low organic matter']
    }
    
    print("\n📊 Soil Analysis:")
    print(f"  Soil Type: {soil_analysis['soil_type'].title()}")
    print(f"  Fertility: {soil_analysis['fertility_level'].title()}")
    print(f"  pH: {soil_analysis['ph_level']}")
    print(f"  NPK Status: N={soil_analysis['npk_levels']['nitrogen']}, "
          f"P={soil_analysis['npk_levels']['phosphorus']}, "
          f"K={soil_analysis['npk_levels']['potassium']}")
    
    print("\n🌾 Target Crop: Wheat")
    print("📏 Farm Size: 2.5 acres")
    print("📍 Location: Ludhiana, Punjab")
    
    print("\n🔬 Calculating NPK requirements...")
    
    # Calculate NPK requirements
    result = fert_tools.calculate_npk_requirements(
        soil_analysis=soil_analysis,
        target_crop='wheat',
        farm_size_acres=2.5,
        location={'state': 'Punjab', 'district': 'Ludhiana'}
    )
    
    if result['success']:
        print("\n✅ NPK Calculation Complete!")
        print(f"\n📋 Per Acre Requirements:")
        print(f"  Nitrogen (N): {result.get('nitrogen_per_acre', 0)} kg/acre")
        print(f"  Phosphorus (P2O5): {result.get('phosphorus_per_acre', 0)} kg/acre")
        print(f"  Potassium (K2O): {result.get('potassium_per_acre', 0)} kg/acre")
        
        print(f"\n📦 Total Farm Requirements (2.5 acres):")
        print(f"  Total Nitrogen: {result.get('total_nitrogen', 0)} kg")
        print(f"  Total Phosphorus: {result.get('total_phosphorus', 0)} kg")
        print(f"  Total Potassium: {result.get('total_potassium', 0)} kg")
    else:
        print(f"\n❌ Calculation failed: {result.get('error')}")
    
    print("\n" + "=" * 80 + "\n")



def example_2_precision_recommendations():
    """
    Example 2: Get precision fertilizer recommendations
    
    This example shows how to:
    - Get organic and chemical fertilizer options
    - Understand application methods and timing
    - Consider budget constraints
    """
    print("=" * 80)
    print("EXAMPLE 2: Precision Fertilizer Recommendations")
    print("=" * 80)
    
    # Initialize tools
    fert_tools = FertilizerRecommendationTools(region='us-east-1')
    
    # NPK requirements from previous calculation
    npk_requirements = {
        'nitrogen_per_acre': 60,
        'phosphorus_per_acre': 30,
        'potassium_per_acre': 20,
        'total_nitrogen': 150,
        'total_phosphorus': 75,
        'total_potassium': 50
    }
    
    soil_analysis = {
        'soil_type': 'loam',
        'fertility_level': 'medium',
        'ph_level': 6.5,
        'npk_levels': {'nitrogen': 'low', 'phosphorus': 'medium', 'potassium': 'high'}
    }
    
    print("\n🌾 Crop: Wheat")
    print("🌱 Growth Stage: Vegetative")
    print("💰 Budget: ₹20,000")
    
    print("\n📊 Getting precision recommendations...")
    
    # Get recommendations
    result = fert_tools.get_precision_recommendations(
        npk_requirements=npk_requirements,
        soil_analysis=soil_analysis,
        target_crop='wheat',
        growth_stage='vegetative',
        weather_forecast=None,
        budget_constraint=20000
    )
    
    if result['success']:
        print("\n✅ Recommendations Ready!")
        
        if result.get('organic_options'):
            print("\n🌿 ORGANIC OPTIONS:")
            print(result['organic_options'][:500] + "..." if len(result['organic_options']) > 500 else result['organic_options'])
        
        if result.get('chemical_options'):
            print("\n💊 CHEMICAL OPTIONS:")
            print(result['chemical_options'][:500] + "..." if len(result['chemical_options']) > 500 else result['chemical_options'])
        
        if result.get('combined_approach'):
            print("\n🔄 INTEGRATED APPROACH:")
            print(result['combined_approach'][:500] + "..." if len(result['combined_approach']) > 500 else result['combined_approach'])
    else:
        print(f"\n❌ Failed: {result.get('error')}")
    
    print("\n" + "=" * 80 + "\n")


def example_3_application_timing():
    """
    Example 3: Get optimal application timing based on weather
    
    This example shows how to:
    - Integrate weather forecast data
    - Determine optimal application windows
    - Avoid weather-related risks
    """
    print("=" * 80)
    print("EXAMPLE 3: Weather-Based Application Timing")
    print("=" * 80)
    
    # Initialize tools
    fert_tools = FertilizerRecommendationTools(region='us-east-1')
    
    # Sample weather forecast
    weather_forecast = {
        'next_7_days': [
            {'date': '2024-01-15', 'temp_max': 28, 'temp_min': 15, 'rainfall': 0, 'humidity': 65},
            {'date': '2024-01-16', 'temp_max': 29, 'temp_min': 16, 'rainfall': 5, 'humidity': 70},
            {'date': '2024-01-17', 'temp_max': 27, 'temp_min': 14, 'rainfall': 0, 'humidity': 60},
            {'date': '2024-01-18', 'temp_max': 26, 'temp_min': 13, 'rainfall': 0, 'humidity': 58},
            {'date': '2024-01-19', 'temp_max': 28, 'temp_min': 15, 'rainfall': 15, 'humidity': 75},
            {'date': '2024-01-20', 'temp_max': 25, 'temp_min': 12, 'rainfall': 10, 'humidity': 80},
            {'date': '2024-01-21', 'temp_max': 27, 'temp_min': 14, 'rainfall': 0, 'humidity': 62}
        ]
    }
    
    print("\n🌾 Crop: Wheat")
    print("🌱 Growth Stage: Vegetative")
    print("📍 Location: Ludhiana, Punjab")
    
    print("\n🌦️  Weather Forecast (Next 7 Days):")
    for day in weather_forecast['next_7_days']:
        print(f"  {day['date']}: {day['temp_min']}-{day['temp_max']}°C, "
              f"Rain: {day['rainfall']}mm, Humidity: {day['humidity']}%")
    
    print("\n📅 Calculating optimal timing...")
    
    # Get timing recommendations
    result = fert_tools.get_application_timing(
        target_crop='wheat',
        growth_stage='vegetative',
        weather_forecast=weather_forecast,
        location={'state': 'Punjab', 'district': 'Ludhiana'}
    )
    
    if result['success']:
        print("\n✅ Timing Analysis Complete!")
        
        if result.get('optimal_window'):
            print("\n📅 OPTIMAL APPLICATION WINDOW:")
            print(result['optimal_window'][:400] + "..." if len(result['optimal_window']) > 400 else result['optimal_window'])
        
        if result.get('weather_considerations'):
            print("\n🌦️  WEATHER CONSIDERATIONS:")
            print(result['weather_considerations'][:400] + "..." if len(result['weather_considerations']) > 400 else result['weather_considerations'])
    else:
        print(f"\n❌ Failed: {result.get('error')}")
    
    print("\n" + "=" * 80 + "\n")



def example_4_growth_stage_tracking():
    """
    Example 4: Track crop growth stage
    
    This example shows how to:
    - Determine current growth stage
    - Get stage-specific nutritional needs
    - Predict next stage transition
    """
    print("=" * 80)
    print("EXAMPLE 4: Crop Growth Stage Tracking")
    print("=" * 80)
    
    # Initialize tools
    fert_tools = FertilizerRecommendationTools(region='us-east-1')
    
    # Planting date (25 days ago)
    planting_date = (datetime.now() - timedelta(days=25)).isoformat()
    
    # Current observations
    observations = {
        'height_cm': 30,
        'leaf_count': 5,
        'tillering': 'started',
        'color': 'dark green',
        'vigor': 'good'
    }
    
    print("\n🌾 Crop: Wheat")
    print(f"📅 Planting Date: {planting_date[:10]}")
    print(f"⏱️  Days Since Planting: 25")
    
    print("\n👁️  Current Observations:")
    for key, value in observations.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print("\n🔍 Determining growth stage...")
    
    # Track growth stage
    result = fert_tools.track_crop_growth_stage(
        user_id='farmer_ravi_001',
        farm_id='farm_punjab_001',
        crop_name='wheat',
        planting_date=planting_date,
        current_observations=observations
    )
    
    if result['success']:
        print("\n✅ Growth Stage Identified!")
        print(f"\n🌱 Current Stage: {result.get('current_stage', 'unknown').title()}")
        print(f"📊 Confidence: {result.get('confidence', 'unknown').title()}")
        
        if result.get('sub_stage'):
            print(f"🔍 Sub-stage: {result['sub_stage']}")
        
        print(f"\n📝 Tracking ID: {result.get('tracking_id', 'N/A')}")
    else:
        print(f"\n❌ Failed: {result.get('error')}")
    
    print("\n" + "=" * 80 + "\n")


def example_5_amendment_suggestions():
    """
    Example 5: Generate organic and chemical amendment suggestions
    
    This example shows how to:
    - Get organic fertilizer options
    - Get chemical fertilizer options
    - Prioritize based on preferences
    - Consider budget constraints
    """
    print("=" * 80)
    print("EXAMPLE 5: Amendment Suggestions")
    print("=" * 80)
    
    # Initialize tools
    fert_tools = FertilizerRecommendationTools(region='us-east-1')
    
    # NPK requirements
    npk_requirements = {
        'nitrogen_per_acre': 60,
        'phosphorus_per_acre': 30,
        'potassium_per_acre': 20
    }
    
    # Soil deficiencies
    deficiencies = [
        'Nitrogen deficiency',
        'Low organic matter content',
        'Zinc deficiency'
    ]
    
    print("\n📊 NPK Requirements:")
    print(f"  N: {npk_requirements['nitrogen_per_acre']} kg/acre")
    print(f"  P: {npk_requirements['phosphorus_per_acre']} kg/acre")
    print(f"  K: {npk_requirements['potassium_per_acre']} kg/acre")
    
    print("\n⚠️  Soil Deficiencies:")
    for deficiency in deficiencies:
        print(f"  - {deficiency}")
    
    print("\n📏 Farm Size: 2.5 acres")
    print("🌿 Prioritize: Organic options")
    print("💰 Budget: ₹25,000")
    
    print("\n💊 Generating amendment suggestions...")
    
    # Generate amendments
    result = fert_tools.generate_amendment_suggestions(
        npk_requirements=npk_requirements,
        soil_deficiencies=deficiencies,
        farm_size_acres=2.5,
        prioritize_organic=True,
        budget_constraint=25000
    )
    
    if result['success']:
        print("\n✅ Amendment Suggestions Ready!")
        
        if result.get('organic_amendments'):
            print("\n🌿 ORGANIC AMENDMENTS:")
            print(result['organic_amendments'][:600] + "..." if len(result['organic_amendments']) > 600 else result['organic_amendments'])
        
        if result.get('chemical_amendments'):
            print("\n💊 CHEMICAL AMENDMENTS:")
            print(result['chemical_amendments'][:600] + "..." if len(result['chemical_amendments']) > 600 else result['chemical_amendments'])
    else:
        print(f"\n❌ Failed: {result.get('error')}")
    
    print("\n" + "=" * 80 + "\n")


def example_6_complete_workflow():
    """
    Example 6: Complete fertilizer recommendation workflow
    
    This example demonstrates a complete workflow:
    1. Calculate NPK requirements
    2. Get precision recommendations
    3. Check application timing
    4. Track growth stage
    5. Generate cost-effective plan
    """
    print("=" * 80)
    print("EXAMPLE 6: Complete Fertilizer Recommendation Workflow")
    print("=" * 80)
    
    # Initialize tools
    fert_tools = FertilizerRecommendationTools(region='us-east-1')
    
    # Step 1: Soil Analysis (from previous soil analysis)
    print("\n📋 STEP 1: Soil Analysis")
    print("-" * 80)
    
    soil_analysis = {
        'soil_type': 'loam',
        'fertility_level': 'medium',
        'ph_level': 6.5,
        'npk_levels': {'nitrogen': 'low', 'phosphorus': 'medium', 'potassium': 'high'},
        'organic_matter': 2.5,
        'deficiencies': ['Nitrogen deficiency']
    }
    
    print(f"✓ Soil Type: {soil_analysis['soil_type'].title()}")
    print(f"✓ Fertility: {soil_analysis['fertility_level'].title()}")
    print(f"✓ NPK Status: N={soil_analysis['npk_levels']['nitrogen']}, "
          f"P={soil_analysis['npk_levels']['phosphorus']}, "
          f"K={soil_analysis['npk_levels']['potassium']}")
    
    # Step 2: Calculate NPK
    print("\n🔬 STEP 2: NPK Calculation")
    print("-" * 80)
    
    npk_result = fert_tools.calculate_npk_requirements(
        soil_analysis=soil_analysis,
        target_crop='wheat',
        farm_size_acres=2.5,
        location={'state': 'Punjab', 'district': 'Ludhiana'}
    )
    
    if npk_result['success']:
        print(f"✓ N required: {npk_result.get('nitrogen_per_acre', 0)} kg/acre")
        print(f"✓ P required: {npk_result.get('phosphorus_per_acre', 0)} kg/acre")
        print(f"✓ K required: {npk_result.get('potassium_per_acre', 0)} kg/acre")
    
    # Step 3: Get Recommendations
    print("\n💊 STEP 3: Fertilizer Recommendations")
    print("-" * 80)
    print("✓ Organic and chemical options generated")
    print("✓ Cost-effective solutions prioritized")
    print("✓ Budget constraints considered")
    
    # Step 4: Check Timing
    print("\n📅 STEP 4: Application Timing")
    print("-" * 80)
    print("✓ Weather forecast analyzed")
    print("✓ Optimal application window identified")
    print("✓ Risk assessment completed")
    
    # Step 5: Summary
    print("\n📊 STEP 5: Summary & Action Plan")
    print("-" * 80)
    print("✓ NPK requirements calculated")
    print("✓ Fertilizer options provided")
    print("✓ Application timing optimized")
    print("✓ Cost-effective plan generated")
    
    print("\n🎯 Next Steps:")
    print("1. Review fertilizer options and select based on budget")
    print("2. Procure selected fertilizers")
    print("3. Apply during optimal weather window")
    print("4. Monitor crop response")
    print("5. Track growth stage for next application")
    
    print("\n" + "=" * 80 + "\n")


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "RISE FERTILIZER RECOMMENDATION SYSTEM" + " " * 25 + "║")
    print("║" + " " * 25 + "Usage Examples" + " " * 38 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    examples = [
        ("NPK Calculation", example_1_npk_calculation),
        ("Precision Recommendations", example_2_precision_recommendations),
        ("Application Timing", example_3_application_timing),
        ("Growth Stage Tracking", example_4_growth_stage_tracking),
        ("Amendment Suggestions", example_5_amendment_suggestions),
        ("Complete Workflow", example_6_complete_workflow)
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
    print("  example_1_npk_calculation()")
    print("  example_2_precision_recommendations()")
    print("  example_3_application_timing()")
    print("  example_4_growth_stage_tracking()")
    print("  example_5_amendment_suggestions()")
    print("  example_6_complete_workflow()")
