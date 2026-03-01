"""
Example usage of RISE Crop Selection Tools
Demonstrates crop recommendation, profitability analysis, and seasonal calendar generation
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.crop_selection_tools import (
    create_crop_selection_tools,
    recommend_crops,
    calculate_crop_profitability,
    generate_seasonal_calendar
)


def example_crop_recommendations():
    """Example: Get crop recommendations based on soil analysis"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Crop Recommendations")
    print("="*80)
    
    # Sample soil analysis data
    soil_analysis = {
        'soil_type': 'loam',
        'fertility_level': 'medium',
        'ph_level': 6.8,
        'npk_levels': {
            'nitrogen': 'medium',
            'phosphorus': 'low',
            'potassium': 'high'
        },
        'organic_matter': 2.5,
        'deficiencies': ['phosphorus'],
        'suitable_crops': ['wheat', 'rice', 'cotton']
    }
    
    location = {
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
    
    farm_size_acres = 5.0
    
    # Optional climate data
    climate_data = {
        'temperature': {'min': 15, 'max': 32},
        'rainfall': 700,
        'season': 'kharif'
    }
    
    # Optional market preferences
    market_preferences = {
        'priority': 'profitability',
        'risk_tolerance': 'medium'
    }
    
    print(f"\nFarm Location: {location['district']}, {location['state']}")
    print(f"Farm Size: {farm_size_acres} acres")
    print(f"Soil Type: {soil_analysis['soil_type']}")
    print(f"Fertility: {soil_analysis['fertility_level']}")
    
    try:
        # Get crop recommendations
        result = recommend_crops(
            soil_analysis=soil_analysis,
            location=location,
            farm_size_acres=farm_size_acres,
            climate_data=climate_data,
            market_preferences=market_preferences,
            farmer_experience='intermediate'
        )
        
        if result['success']:
            print(f"\n✓ Recommendation ID: {result['recommendation_id']}")
            
            print("\n--- HIGHLY RECOMMENDED CROPS ---")
            for crop in result.get('highly_recommended_crops', []):
                print(f"\n• {crop.get('name', 'Unknown')}")
                if 'expected_yield' in crop:
                    print(f"  Expected Yield: {crop['expected_yield']}")
                if 'market_demand' in crop:
                    print(f"  Market Demand: {crop['market_demand']}")
                if 'net_profit' in crop:
                    print(f"  Net Profit: {crop['net_profit']}")
                if 'risk_level' in crop:
                    print(f"  Risk Level: {crop['risk_level']}")
            
            print("\n--- MODERATELY SUITABLE CROPS ---")
            for crop in result.get('moderately_suitable_crops', []):
                print(f"• {crop.get('name', 'Unknown')}")
        else:
            print(f"\n✗ Error: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"\n✗ Exception: {e}")


def example_profitability_calculation():
    """Example: Calculate crop profitability"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Crop Profitability Calculation")
    print("="*80)
    
    crop_name = 'Wheat'
    farm_size_acres = 5.0
    location = {
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
    soil_type = 'loam'
    
    # Optional custom input costs
    input_costs = {
        'seeds': 3000,
        'fertilizers': 8000,
        'pesticides': 2000,
        'labor': 12000,
        'irrigation': 5000,
        'equipment': 3000
    }
    
    # Optional market price (if not provided, mock data will be used)
    market_price = 2200  # Rs per quintal
    
    print(f"\nCrop: {crop_name}")
    print(f"Farm Size: {farm_size_acres} acres")
    print(f"Location: {location['district']}, {location['state']}")
    print(f"Soil Type: {soil_type}")
    print(f"Market Price: ₹{market_price} per quintal")
    
    try:
        # Calculate profitability
        result = calculate_crop_profitability(
            crop_name=crop_name,
            farm_size_acres=farm_size_acres,
            location=location,
            soil_type=soil_type,
            input_costs=input_costs,
            market_price=market_price
        )
        
        if result['success']:
            print("\n--- PROFITABILITY ANALYSIS ---")
            print(f"Input Costs per Acre: ₹{result.get('input_costs_per_acre', 0):,.2f}")
            print(f"Expected Yield per Acre: {result.get('expected_yield_per_acre', 0)} quintals")
            print(f"Revenue per Acre: ₹{result.get('revenue_per_acre', 0):,.2f}")
            print(f"Net Profit per Acre: ₹{result.get('net_profit_per_acre', 0):,.2f}")
            print(f"Profit Margin: {result.get('profit_margin', 0):.1f}%")
            print(f"ROI: {result.get('roi', 0):.1f}%")
            print(f"Risk Rating: {result.get('risk_rating', 'unknown')}")
            
            print(f"\n--- TOTAL FARM ({farm_size_acres} acres) ---")
            total_investment = result.get('input_costs_per_acre', 0) * farm_size_acres
            total_profit = result.get('net_profit_per_acre', 0) * farm_size_acres
            print(f"Total Investment: ₹{total_investment:,.2f}")
            print(f"Total Net Profit: ₹{total_profit:,.2f}")
        else:
            print(f"\n✗ Error: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"\n✗ Exception: {e}")


def example_seasonal_calendar():
    """Example: Generate seasonal crop calendar"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Seasonal Crop Calendar")
    print("="*80)
    
    location = {
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
    soil_type = 'loam'
    farm_size_acres = 5.0
    
    # Optional: specify crops to include in calendar
    selected_crops = ['Wheat', 'Rice', 'Cotton']
    
    print(f"\nLocation: {location['district']}, {location['state']}")
    print(f"Soil Type: {soil_type}")
    print(f"Farm Size: {farm_size_acres} acres")
    if selected_crops:
        print(f"Selected Crops: {', '.join(selected_crops)}")
    
    try:
        # Generate seasonal calendar
        result = generate_seasonal_calendar(
            location=location,
            soil_type=soil_type,
            farm_size_acres=farm_size_acres,
            selected_crops=selected_crops
        )
        
        if result['success']:
            print("\n--- SEASONAL CROP CALENDAR ---")
            
            print("\nKHARIF SEASON (Monsoon - June to October):")
            for crop in result.get('kharif_crops', []):
                print(f"  • {crop}")
            
            print("\nRABI SEASON (Winter - November to March):")
            for crop in result.get('rabi_crops', []):
                print(f"  • {crop}")
            
            print("\nZAID SEASON (Summer - March to June):")
            for crop in result.get('zaid_crops', []):
                print(f"  • {crop}")
            
            if result.get('perennial_crops'):
                print("\nPERENNIAL CROPS:")
                for crop in result.get('perennial_crops', []):
                    print(f"  • {crop}")
            
            print("\n--- MONTHLY ACTIVITIES ---")
            for month, activities in result.get('monthly_activities', {}).items():
                print(f"\n{month}:")
                if isinstance(activities, list):
                    for activity in activities:
                        print(f"  • {activity}")
                else:
                    print(f"  • {activities}")
        else:
            print(f"\n✗ Error: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"\n✗ Exception: {e}")


def example_crop_comparison():
    """Example: Compare multiple crop options"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Crop Comparison")
    print("="*80)
    
    # Create tools instance
    tools = create_crop_selection_tools()
    
    crop_list = ['Wheat', 'Rice', 'Maize']
    
    soil_analysis = {
        'soil_type': 'loam',
        'fertility_level': 'medium',
        'ph_level': 6.8,
        'npk_levels': {
            'nitrogen': 'medium',
            'phosphorus': 'medium',
            'potassium': 'high'
        }
    }
    
    location = {
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
    
    farm_size_acres = 5.0
    
    comparison_criteria = [
        'profitability',
        'water_requirements',
        'labor_needs',
        'market_demand',
        'risk_level'
    ]
    
    print(f"\nComparing Crops: {', '.join(crop_list)}")
    print(f"Location: {location['district']}, {location['state']}")
    print(f"Comparison Criteria: {', '.join(comparison_criteria)}")
    
    try:
        # Compare crops
        result = tools.compare_crop_options(
            crop_list=crop_list,
            soil_analysis=soil_analysis,
            location=location,
            farm_size_acres=farm_size_acres,
            comparison_criteria=comparison_criteria
        )
        
        if result['success']:
            print("\n--- CROP COMPARISON RESULTS ---")
            print(f"Crops Compared: {', '.join(result['crops_compared'])}")
            
            if result.get('recommendation'):
                print(f"\nRecommendation: {result['recommendation']}")
            
            print("\nSee full comparison for detailed analysis.")
        else:
            print(f"\n✗ Error: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"\n✗ Exception: {e}")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("RISE CROP SELECTION TOOLS - EXAMPLES")
    print("="*80)
    print("\nThese examples demonstrate the crop selection and recommendation features.")
    print("Note: Requires AWS credentials and Bedrock access.")
    
    # Run examples
    example_crop_recommendations()
    example_profitability_calculation()
    example_seasonal_calendar()
    example_crop_comparison()
    
    print("\n" + "="*80)
    print("Examples completed!")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
