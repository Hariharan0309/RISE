"""
RISE Crop Profitability Calculator - Example Usage
Demonstrates how to use the profitability calculator tools
"""

import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.profitability_calculator_tools import ProfitabilityCalculatorTools


def example_1_single_crop_profitability():
    """Example 1: Calculate profitability for a single crop"""
    print("=" * 80)
    print("Example 1: Single Crop Profitability Analysis")
    print("=" * 80)
    
    tools = ProfitabilityCalculatorTools()
    
    location = {
        'state': 'Punjab',
        'district': 'Ludhiana',
        'latitude': 30.9010,
        'longitude': 75.8573
    }
    
    result = tools.calculate_comprehensive_profitability(
        crop_name='wheat',
        farm_size_acres=5.0,
        location=location,
        soil_type='loamy',
        season='rabi'
    )
    
    if result['success']:
        print(f"\n✓ Profitability Analysis for {result['crop_name'].title()}")
        print(f"  Farm Size: {result['farm_size_acres']} acres")
        print(f"  Location: {location['district']}, {location['state']}")
        
        avg_scenario = result['profitability_scenarios']['average']
        print(f"\n💰 Financial Summary (Average Scenario):")
        print(f"  Total Investment: ₹{avg_scenario['total_cost']:,.2f}")
        print(f"  Expected Yield: {avg_scenario['total_yield_quintals']:.2f} quintals")
        print(f"  Market Price: ₹{avg_scenario['price_per_quintal']}/quintal")
        print(f"  Total Revenue: ₹{avg_scenario['total_revenue']:,.2f}")
        print(f"  Net Profit: ₹{avg_scenario['net_profit']:,.2f}")
        print(f"  ROI: {avg_scenario['roi_percent']:.2f}%")
        print(f"  Profit Margin: {avg_scenario['profit_margin_percent']:.2f}%")
        
        print(f"\n📊 Scenario Analysis:")
        for scenario_name in ['conservative', 'average', 'optimistic']:
            scenario = result['profitability_scenarios'][scenario_name]
            print(f"  {scenario_name.title()}: ₹{scenario['net_profit']:,.2f} profit "
                  f"({scenario['roi_percent']:.1f}% ROI)")
        
        print(f"\n⚠️ Risk Assessment:")
        risk = result['risk_assessment']
        print(f"  Overall Risk: {risk['overall_risk_level'].upper()} "
              f"(Score: {risk['overall_risk_score']}/10)")
        print(f"  Recommendation: {risk['recommendation']}")
        
        print(f"\n📈 Projections:")
        proj = result['projections']
        print(f"  Expected Profit (Risk-Adjusted): ₹{proj['expected_profit']:,.2f}")
        print(f"  Break-even Price: ₹{proj['break_even_price']:.2f}/quintal")
        print(f"  Break-even Yield: {proj['break_even_yield']:.2f} quintals")
    else:
        print(f"✗ Error: {result.get('error')}")
    
    print()


def example_2_compare_crops():
    """Example 2: Compare profitability of multiple crops"""
    print("=" * 80)
    print("Example 2: Compare Crop Profitability")
    print("=" * 80)
    
    tools = ProfitabilityCalculatorTools()
    
    location = {
        'state': 'Punjab',
        'district': 'Ludhiana',
        'latitude': 30.9010,
        'longitude': 75.8573
    }
    
    crop_list = ['wheat', 'rice', 'maize', 'cotton']
    
    result = tools.compare_crop_profitability(
        crop_list=crop_list,
        farm_size_acres=5.0,
        location=location,
        soil_type='loamy',
        season='rabi'
    )
    
    if result['success']:
        print(f"\n✓ Comparing {len(crop_list)} crops for {result['farm_size_acres']} acres")
        print(f"  Location: {location['district']}, {location['state']}")
        
        print(f"\n🏆 Rankings:")
        print(f"  By Profit: {', '.join([c.title() for c in result['rankings']['by_profit']])}")
        print(f"  By ROI: {', '.join([c.title() for c in result['rankings']['by_roi']])}")
        print(f"  By Low Risk: {', '.join([c.title() for c in result['rankings']['by_low_risk']])}")
        
        print(f"\n✨ Best Overall Choice: {result['best_overall'].title()}")
        
        print(f"\n📊 Detailed Comparison:")
        print(f"  {'Crop':<12} {'Cost':<12} {'Yield':<10} {'Revenue':<12} {'Profit':<12} {'ROI':<8} {'Risk':<6}")
        print(f"  {'-'*12} {'-'*12} {'-'*10} {'-'*12} {'-'*12} {'-'*8} {'-'*6}")
        
        for comp in result['comparisons']:
            print(f"  {comp['crop_name'].title():<12} "
                  f"₹{comp['total_cost']:>10,.0f} "
                  f"{comp['average_yield']:>8.1f}q "
                  f"₹{comp['average_revenue']:>10,.0f} "
                  f"₹{comp['average_profit']:>10,.0f} "
                  f"{comp['roi']:>6.1f}% "
                  f"{comp['risk_score']:>5.1f}")
    else:
        print(f"✗ Error: {result.get('error')}")
    
    print()


def example_3_cost_estimation():
    """Example 3: Estimate input costs for a crop"""
    print("=" * 80)
    print("Example 3: Input Cost Estimation")
    print("=" * 80)
    
    tools = ProfitabilityCalculatorTools()
    
    location = {
        'state': 'Maharashtra',
        'district': 'Nashik',
        'latitude': 19.9975,
        'longitude': 73.7898
    }
    
    result = tools.estimate_input_costs(
        crop_name='cotton',
        farm_size_acres=10.0,
        location=location,
        soil_type='black',
        season='kharif'
    )
    
    if result['success']:
        print(f"\n✓ Cost Estimation for {result['crop_name'].title()}")
        print(f"  Farm Size: {result['farm_size_acres']} acres")
        print(f"  Location: {location['district']}, {location['state']}")
        print(f"  Season: {result['season']}")
        
        print(f"\n💵 Cost Summary:")
        print(f"  Cost Per Acre: ₹{result['total_cost_per_acre']:,.2f}")
        print(f"  Total Farm Cost: ₹{result['total_farm_cost']:,.2f}")
        
        print(f"\n📊 Cost by Category:")
        for category, amount in result['cost_categories'].items():
            percentage = (amount / result['total_cost_per_acre']) * 100
            print(f"  {category.title():<20} ₹{amount:>10,.2f} ({percentage:>5.1f}%)")
        
        print(f"\n📋 Detailed Cost Breakdown (Per Acre):")
        for item, cost in result['costs_per_acre'].items():
            print(f"  {item.replace('_', ' ').title():<25} ₹{cost:>10,.2f}")
    else:
        print(f"✗ Error: {result.get('error')}")
    
    print()


def example_4_yield_prediction():
    """Example 4: Predict crop yield with historical data"""
    print("=" * 80)
    print("Example 4: Yield Prediction with Historical Data")
    print("=" * 80)
    
    tools = ProfitabilityCalculatorTools()
    
    location = {
        'state': 'Haryana',
        'district': 'Karnal',
        'latitude': 29.6857,
        'longitude': 76.9905
    }
    
    # Historical yield data from past 5 years
    historical_data = {
        'past_yields': [19.5, 20.2, 18.8, 21.0, 19.7]
    }
    
    result = tools.predict_crop_yield(
        crop_name='rice',
        location=location,
        soil_type='alluvial',
        season='kharif',
        historical_data=historical_data
    )
    
    if result['success']:
        print(f"\n✓ Yield Prediction for {result['crop_name'].title()}")
        print(f"  Location: {location['district']}, {location['state']}")
        print(f"  Confidence: {result['confidence'].upper()}")
        
        print(f"\n📊 Predicted Yield (quintals per acre):")
        yields = result['yield_per_acre_quintals']
        print(f"  Conservative: {yields['conservative']:.2f}")
        print(f"  Average: {yields['average']:.2f}")
        print(f"  Optimistic: {yields['optimistic']:.2f}")
        
        print(f"\n🔍 Factors Applied:")
        factors = result['factors_applied']
        for factor_name, factor_value in factors.items():
            print(f"  {factor_name.replace('_', ' ').title():<20} {factor_value:.2f}x")
        
        if historical_data:
            hist_avg = sum(historical_data['past_yields']) / len(historical_data['past_yields'])
            print(f"\n📈 Historical Data:")
            print(f"  Past Yields: {', '.join([f'{y:.1f}' for y in historical_data['past_yields']])} quintals/acre")
            print(f"  Historical Average: {hist_avg:.2f} quintals/acre")
            print(f"  Predicted Average: {yields['average']:.2f} quintals/acre")
    else:
        print(f"✗ Error: {result.get('error')}")
    
    print()


def example_5_custom_costs():
    """Example 5: Profitability with custom input costs"""
    print("=" * 80)
    print("Example 5: Profitability with Custom Input Costs")
    print("=" * 80)
    
    tools = ProfitabilityCalculatorTools()
    
    location = {
        'state': 'Gujarat',
        'district': 'Ahmedabad',
        'latitude': 23.0225,
        'longitude': 72.5714
    }
    
    # Custom input costs (farmer has negotiated better prices)
    custom_costs = {
        'seeds': 1000,  # Got seeds at discount
        'fertilizers_npk': 3000,  # Bulk purchase discount
        'pesticides': 600  # Using organic alternatives
    }
    
    result = tools.calculate_comprehensive_profitability(
        crop_name='potato',
        farm_size_acres=3.0,
        location=location,
        soil_type='sandy',
        season='rabi',
        custom_input_costs=custom_costs
    )
    
    if result['success']:
        print(f"\n✓ Profitability with Custom Costs for {result['crop_name'].title()}")
        print(f"  Farm Size: {result['farm_size_acres']} acres")
        
        print(f"\n💰 Custom Input Costs Applied:")
        for item, cost in custom_costs.items():
            print(f"  {item.replace('_', ' ').title()}: ₹{cost:,.2f}")
        
        avg_scenario = result['profitability_scenarios']['average']
        print(f"\n📊 Financial Results:")
        print(f"  Total Cost: ₹{avg_scenario['total_cost']:,.2f}")
        print(f"  Total Revenue: ₹{avg_scenario['total_revenue']:,.2f}")
        print(f"  Net Profit: ₹{avg_scenario['net_profit']:,.2f}")
        print(f"  ROI: {avg_scenario['roi_percent']:.2f}%")
        
        print(f"\n💡 Cost Savings:")
        print(f"  By using custom negotiated prices, you can optimize your input costs")
        print(f"  and potentially increase your profit margins.")
    else:
        print(f"✗ Error: {result.get('error')}")
    
    print()


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "RISE Crop Profitability Calculator Examples" + " " * 20 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    try:
        example_1_single_crop_profitability()
        example_2_compare_crops()
        example_3_cost_estimation()
        example_4_yield_prediction()
        example_5_custom_costs()
        
        print("=" * 80)
        print("✓ All examples completed successfully!")
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
