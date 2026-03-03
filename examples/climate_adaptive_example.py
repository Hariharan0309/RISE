"""
RISE Climate-Adaptive Recommendations Example
Demonstrates usage of climate-adaptive tools for farming recommendations
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.climate_adaptive_tools import create_climate_adaptive_tools
import json


def example_climate_analysis():
    """Example: Analyze climate data and identify trends"""
    print("=" * 80)
    print("Example 1: Climate Data Analysis")
    print("=" * 80)
    
    # Initialize tools
    tools = create_climate_adaptive_tools()
    
    # Sample location
    location = {
        'name': 'Pune, Maharashtra',
        'latitude': 18.5204,
        'longitude': 73.8567
    }
    
    # Sample historical weather data (last 30 days)
    historical_weather = [
        {'date': '2024-01-01', 'temp_avg': 28, 'temp_max': 35, 'temp_min': 22, 'rainfall': 0},
        {'date': '2024-01-02', 'temp_avg': 29, 'temp_max': 36, 'temp_min': 23, 'rainfall': 0},
        {'date': '2024-01-03', 'temp_avg': 30, 'temp_max': 37, 'temp_min': 24, 'rainfall': 2},
        {'date': '2024-01-04', 'temp_avg': 31, 'temp_max': 38, 'temp_min': 25, 'rainfall': 0},
        {'date': '2024-01-05', 'temp_avg': 32, 'temp_max': 39, 'temp_min': 26, 'rainfall': 0},
        {'date': '2024-01-06', 'temp_avg': 33, 'temp_max': 40, 'temp_min': 27, 'rainfall': 0},
        {'date': '2024-01-07', 'temp_avg': 34, 'temp_max': 41, 'temp_min': 28, 'rainfall': 1},
        {'date': '2024-01-08', 'temp_avg': 35, 'temp_max': 42, 'temp_min': 29, 'rainfall': 0},
        {'date': '2024-01-09', 'temp_avg': 36, 'temp_max': 43, 'temp_min': 30, 'rainfall': 0},
        {'date': '2024-01-10', 'temp_avg': 35, 'temp_max': 42, 'temp_min': 29, 'rainfall': 5}
    ]
    
    # Analyze climate data
    result = tools.analyze_climate_data(location, historical_weather, 'Rabi')
    
    if result['success']:
        print(f"\n✓ Climate Analysis Completed")
        print(f"  Analysis ID: {result['analysis_id']}")
        print(f"  Location: {result['location']['name']}")
        print(f"  Season: {result['season']}")
        
        print(f"\n  Temperature Trends:")
        temp = result['trends']['temperature']
        print(f"    - Average: {temp['average']}°C")
        print(f"    - Max: {temp['max']}°C")
        print(f"    - Min: {temp['min']}°C")
        print(f"    - Trend: {temp['trend']}")
        
        print(f"\n  Rainfall Trends:")
        rain = result['trends']['rainfall']
        print(f"    - Total: {rain['total']}mm")
        print(f"    - Average: {rain['average']}mm/day")
        print(f"    - Trend: {rain['trend']}")
        
        print(f"\n  Climate Risks Identified: {len(result['risks'])}")
        for risk in result['risks']:
            print(f"    - {risk['type'].upper()} ({risk['severity']})")
            print(f"      {risk['description']}")
            print(f"      Mitigation: {risk['mitigation']}")
        
        print(f"\n  AI Insights:")
        print(f"    {result['ai_insights']}")
    else:
        print(f"\n✗ Error: {result.get('error')}")
    
    print()


def example_resilient_crop_varieties():
    """Example: Get resilient crop variety recommendations"""
    print("=" * 80)
    print("Example 2: Resilient Crop Variety Recommendations")
    print("=" * 80)
    
    # Initialize tools
    tools = create_climate_adaptive_tools()
    
    # Sample location
    location = {
        'name': 'Nashik, Maharashtra',
        'latitude': 19.9975,
        'longitude': 73.7898
    }
    
    # Climate risks identified
    climate_risks = ['drought', 'heat_stress', 'climate_variability']
    
    # Soil type
    soil_type = 'Black soil (Regur)'
    
    # Get crop variety recommendations
    result = tools.get_resilient_crop_varieties(location, climate_risks, soil_type)
    
    if result['success']:
        print(f"\n✓ Crop Variety Recommendations Generated")
        print(f"  Location: {result['location']['name']}")
        print(f"  Climate Risks: {', '.join(result['climate_risks'])}")
        print(f"  Confidence Score: {result['confidence_score']:.1f}%")
        
        print(f"\n  Recommended Varieties:")
        for i, variety in enumerate(result['recommended_varieties'], 1):
            print(f"\n  {i}. {variety.get('crop_name', 'N/A')} - {variety.get('variety', 'N/A')}")
            print(f"     Resilience: {', '.join(variety.get('resilience_features', []))}")
            print(f"     Expected Yield: {variety.get('expected_yield', 'N/A')}")
            print(f"     Market Demand: {variety.get('market_demand', 'N/A')}")
            print(f"     Confidence: {variety.get('confidence_score', 0)}%")
    else:
        print(f"\n✗ Error: {result.get('error')}")
    
    print()


def example_water_efficient_techniques():
    """Example: Get water-efficient farming technique recommendations"""
    print("=" * 80)
    print("Example 3: Water-Efficient Farming Techniques")
    print("=" * 80)
    
    # Initialize tools
    tools = create_climate_adaptive_tools()
    
    # Sample location
    location = {
        'name': 'Solapur, Maharashtra',
        'latitude': 17.6599,
        'longitude': 75.9064
    }
    
    # Water scarcity level
    water_scarcity_level = 'high'
    
    # Crop type
    crop_type = 'Cotton'
    
    # Get water-efficient techniques
    result = tools.get_water_efficient_techniques(location, water_scarcity_level, crop_type)
    
    if result['success']:
        print(f"\n✓ Water-Efficient Techniques Recommended")
        print(f"  Location: {result['location']['name']}")
        print(f"  Water Scarcity Level: {result['water_scarcity_level'].upper()}")
        
        print(f"\n  Recommended Techniques:")
        for i, technique in enumerate(result['recommended_techniques'], 1):
            print(f"\n  {i}. {technique['name']} (Priority: {technique['priority'].upper()})")
            print(f"     Description: {technique['description']}")
            print(f"     Water Savings: {technique['water_savings']}")
            print(f"     Initial Cost: {technique['initial_cost']}")
            print(f"     Maintenance: {technique['maintenance']}")
            print(f"     Suitability: {technique['suitability']}")
        
        print(f"\n  Cost-Benefit Analysis:")
        cba = result['cost_benefit_analysis']
        print(f"    - Total Initial Investment: {cba['total_initial_investment']}")
        print(f"    - Average Water Savings: {cba['average_water_savings']}")
        print(f"    - Estimated Annual Savings: {cba['estimated_annual_savings']}")
        print(f"    - Payback Period: {cba['payback_period_years']} years")
        print(f"    - 5-Year ROI: {cba['roi_5_years']}")
        
        print(f"\n  Implementation Guide:")
        print(f"    {result['implementation_guide']}")
    else:
        print(f"\n✗ Error: {result.get('error')}")
    
    print()


def example_seasonal_advice():
    """Example: Generate seasonal farming advice"""
    print("=" * 80)
    print("Example 4: Seasonal Farming Advice")
    print("=" * 80)
    
    # Initialize tools
    tools = create_climate_adaptive_tools()
    
    # Sample location
    location = {
        'name': 'Aurangabad, Maharashtra',
        'latitude': 19.8762,
        'longitude': 75.3433
    }
    
    # Season
    season = 'Kharif'
    
    # Climate trends
    climate_trends = {
        'temperature': {
            'average': 32,
            'max': 38,
            'min': 26,
            'trend': 'increasing'
        },
        'rainfall': {
            'total': 150,
            'average': 5,
            'trend': 'decreasing'
        },
        'extreme_events': [
            {'type': 'extreme_heat', 'date': '2024-06-15', 'value': 42}
        ]
    }
    
    # Farmer profile
    farmer_profile = {
        'land_size': 3,  # acres
        'current_crops': ['Cotton', 'Soybean'],
        'irrigation': 'Drip irrigation available',
        'experience': '10 years'
    }
    
    # Generate seasonal advice
    result = tools.generate_seasonal_advice(location, season, climate_trends, farmer_profile)
    
    if result['success']:
        print(f"\n✓ Seasonal Advice Generated")
        print(f"  Location: {result['location']['name']}")
        print(f"  Season: {result['season']}")
        
        print(f"\n  Full Advice:")
        print(f"    {result['advice']['full_advice']}")
        
        if result['advice'].get('key_recommendations'):
            print(f"\n  Key Recommendations:")
            for i, rec in enumerate(result['advice']['key_recommendations'], 1):
                print(f"    {i}. {rec}")
        
        if result['advice'].get('priority_actions'):
            print(f"\n  Priority Actions:")
            for i, action in enumerate(result['advice']['priority_actions'], 1):
                print(f"    {i}. {action}")
    else:
        print(f"\n✗ Error: {result.get('error')}")
    
    print()


def example_complete_workflow():
    """Example: Complete climate-adaptive workflow"""
    print("=" * 80)
    print("Example 5: Complete Climate-Adaptive Workflow")
    print("=" * 80)
    
    # Initialize tools
    tools = create_climate_adaptive_tools()
    
    # Step 1: Analyze climate
    print("\nStep 1: Analyzing climate data...")
    location = {
        'name': 'Ahmednagar, Maharashtra',
        'latitude': 19.0948,
        'longitude': 74.7480
    }
    
    historical_weather = [
        {'date': f'2024-01-{i:02d}', 'temp_avg': 30 + i*0.5, 'temp_max': 36 + i*0.5, 
         'temp_min': 24 + i*0.3, 'rainfall': 0 if i % 5 != 0 else 10}
        for i in range(1, 31)
    ]
    
    climate_result = tools.analyze_climate_data(location, historical_weather, 'Rabi')
    
    if climate_result['success']:
        print(f"  ✓ Climate analysis completed")
        print(f"    Risks identified: {len(climate_result['risks'])}")
        
        # Step 2: Get crop recommendations based on risks
        print("\nStep 2: Getting resilient crop varieties...")
        risk_types = [risk['type'] for risk in climate_result['risks']]
        
        crop_result = tools.get_resilient_crop_varieties(location, risk_types, 'Medium black soil')
        
        if crop_result['success']:
            print(f"  ✓ Crop varieties recommended: {len(crop_result['recommended_varieties'])}")
            
            # Step 3: Get water-efficient techniques
            print("\nStep 3: Getting water-efficient techniques...")
            water_result = tools.get_water_efficient_techniques(location, 'high', 'Wheat')
            
            if water_result['success']:
                print(f"  ✓ Water techniques recommended: {len(water_result['recommended_techniques'])}")
                
                # Step 4: Generate seasonal advice
                print("\nStep 4: Generating seasonal advice...")
                seasonal_result = tools.generate_seasonal_advice(
                    location, 'Rabi', climate_result['trends']
                )
                
                if seasonal_result['success']:
                    print(f"  ✓ Seasonal advice generated")
                    
                    # Summary
                    print("\n" + "=" * 80)
                    print("COMPLETE CLIMATE-ADAPTIVE RECOMMENDATIONS")
                    print("=" * 80)
                    print(f"\nLocation: {location['name']}")
                    print(f"Season: Rabi")
                    print(f"\nClimate Risks: {', '.join(risk_types)}")
                    print(f"Recommended Crops: {len(crop_result['recommended_varieties'])}")
                    print(f"Water Techniques: {len(water_result['recommended_techniques'])}")
                    print(f"Estimated Water Savings: {water_result['cost_benefit_analysis']['average_water_savings']}")
                    print(f"Investment Required: {water_result['cost_benefit_analysis']['total_initial_investment']}")
                    print(f"Payback Period: {water_result['cost_benefit_analysis']['payback_period_years']} years")
    
    print()


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "RISE Climate-Adaptive Recommendations Examples" + " " * 16 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    try:
        # Run examples
        example_climate_analysis()
        example_resilient_crop_varieties()
        example_water_efficient_techniques()
        example_seasonal_advice()
        example_complete_workflow()
        
        print("=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
