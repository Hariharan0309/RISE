"""
RISE Optimal Selling Time Calculator - Example Usage
Demonstrates how to use the selling time calculator tools
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.selling_time_tools import create_selling_time_tools


def example_perishability_analysis():
    """Example: Analyze crop perishability"""
    print("="*60)
    print("Example 1: Crop Perishability Analysis")
    print("="*60)
    
    tools = create_selling_time_tools()
    
    crops = ['tomato', 'potato', 'wheat']
    
    for crop in crops:
        result = tools.analyze_perishability(crop)
        
        if result['success']:
            print(f"\n{crop.upper()}:")
            print(f"  Category: {result['category']}")
            print(f"  Shelf Life: {result['shelf_life_days']} days")
            print(f"  Quality Degradation: {result['quality_degradation_rate']*100}% per day")
            print(f"  Storage Temp: {result['optimal_storage_temp']}")
            print(f"  Requirements: {result['storage_requirements']}")
            print(f"  Recommendation: {result['recommendation']}")
        else:
            print(f"Error analyzing {crop}: {result.get('error')}")


def example_storage_cost_calculation():
    """Example: Calculate storage costs"""
    print("\n" + "="*60)
    print("Example 2: Storage Cost Calculation")
    print("="*60)
    
    tools = create_selling_time_tools()
    
    # Calculate storage costs for wheat
    result = tools.calculate_storage_costs(
        crop_name='wheat',
        quantity_quintals=100,
        storage_days=30,
        storage_type='warehouse'
    )
    
    if result['success']:
        print(f"\nStorage Costs for {result['crop_name'].upper()}:")
        print(f"  Quantity: {result['quantity_quintals']} quintals")
        print(f"  Storage Period: {result['storage_days']} days")
        print(f"  Storage Type: {result['storage_type']}")
        print(f"\nCost Breakdown:")
        costs = result['costs']
        print(f"  Facility Cost: ₹{costs['facility_cost']:.2f}")
        print(f"  Handling Cost: ₹{costs['handling_cost']:.2f}")
        print(f"  Insurance Cost: ₹{costs['insurance_cost']:.2f}")
        print(f"  Total Cost: ₹{costs['total_cost']:.2f}")
        print(f"  Cost per Quintal: ₹{costs['cost_per_quintal']:.2f}")
        print(f"  Cost per Day: ₹{costs['cost_per_day']:.2f}")
        print(f"\nQuality Impact:")
        quality = result['quality_impact']
        print(f"  Degradation: {quality['degradation_percent']:.2f}%")
        print(f"  Remaining Quality: {quality['remaining_quality']:.2f}%")
    else:
        print(f"Error: {result.get('error')}")


def example_optimal_selling_time():
    """Example: Calculate optimal selling time"""
    print("\n" + "="*60)
    print("Example 3: Optimal Selling Time Calculation")
    print("="*60)
    
    tools = create_selling_time_tools()
    
    # Generate predicted prices (simulating price increase)
    predicted_prices = [
        {
            'date': (datetime.now() + timedelta(days=i)).isoformat(),
            'predicted_price': 2400 + i * 50
        }
        for i in range(1, 15)
    ]
    
    result = tools.calculate_optimal_selling_time(
        crop_name='wheat',
        current_price=2400,
        predicted_prices=predicted_prices,
        quantity_quintals=100,
        storage_capacity=True,
        storage_type='warehouse'
    )
    
    if result['success']:
        rec = result['recommendation']
        print(f"\nOptimal Selling Time for {result['crop_name'].upper()}:")
        print(f"  Quantity: {result['quantity_quintals']} quintals")
        print(f"\nRecommendation:")
        print(f"  Timing: {rec['timing']}")
        print(f"  Days to Wait: {rec['days_to_wait']}")
        print(f"  Reason: {rec['reason']}")
        print(f"\nFinancial Analysis:")
        print(f"  Expected Price: ₹{rec['expected_price']:.2f}/quintal")
        print(f"  Expected Revenue: ₹{rec['expected_revenue']:.2f}")
        print(f"  Storage Cost: ₹{rec['storage_cost']:.2f}")
        print(f"  Net Profit: ₹{rec['net_profit']:.2f}")
        print(f"  Profit Improvement: ₹{rec['profit_improvement']:.2f} ({rec['improvement_percent']:.1f}%)")
        print(f"  Confidence: {rec['confidence']}")
        
        print(f"\nPerishability Info:")
        perish = result['perishability']
        print(f"  Category: {perish['category']}")
        print(f"  Shelf Life: {perish['shelf_life_days']} days")
        
        print(f"\nScenario Analysis (Top 3):")
        scenarios = sorted(result['scenarios'], key=lambda s: s['net_profit'], reverse=True)[:3]
        for i, scenario in enumerate(scenarios, 1):
            print(f"  {i}. Day {scenario['days']}: Net Profit ₹{scenario['net_profit']:.2f}")
    else:
        print(f"Error: {result.get('error')}")


def example_price_alerts():
    """Example: Create and manage price alerts"""
    print("\n" + "="*60)
    print("Example 4: Price Alert System")
    print("="*60)
    
    tools = create_selling_time_tools()
    
    # Create a price alert
    print("\nCreating price alert...")
    result = tools.create_price_alert(
        user_id='farmer_001',
        crop_name='wheat',
        target_price=2800,
        market_id='MKT001',
        phone_number='+919876543210'
    )
    
    if result['success']:
        print(f"✓ Alert created successfully!")
        print(f"  Alert ID: {result['alert_id']}")
        print(f"  Message: {result['message']}")
        
        # Get user alerts
        print("\nRetrieving user alerts...")
        alerts_result = tools.get_user_alerts('farmer_001')
        
        if alerts_result['success']:
            print(f"✓ Found {alerts_result['count']} alert(s)")
            for alert in alerts_result['alerts']:
                print(f"  - {alert['crop_name']} @ ₹{alert['target_price']} ({alert['status']})")
    else:
        print(f"Error: {result.get('error')}")


def example_comparison_scenarios():
    """Example: Compare different storage scenarios"""
    print("\n" + "="*60)
    print("Example 5: Storage Scenario Comparison")
    print("="*60)
    
    tools = create_selling_time_tools()
    
    storage_types = ['standard', 'cold', 'warehouse']
    crop_name = 'potato'
    quantity = 100
    days = 30
    
    print(f"\nComparing storage costs for {crop_name.upper()}:")
    print(f"Quantity: {quantity} quintals, Duration: {days} days\n")
    
    for storage_type in storage_types:
        result = tools.calculate_storage_costs(
            crop_name=crop_name,
            quantity_quintals=quantity,
            storage_days=days,
            storage_type=storage_type
        )
        
        if result['success']:
            costs = result['costs']
            print(f"{storage_type.upper()} Storage:")
            print(f"  Total Cost: ₹{costs['total_cost']:.2f}")
            print(f"  Cost per Quintal: ₹{costs['cost_per_quintal']:.2f}")
            print(f"  Quality Remaining: {result['quality_impact']['remaining_quality']:.1f}%")
            print()


def example_perishable_vs_non_perishable():
    """Example: Compare perishable vs non-perishable crops"""
    print("\n" + "="*60)
    print("Example 6: Perishable vs Non-Perishable Comparison")
    print("="*60)
    
    tools = create_selling_time_tools()
    
    # Predicted prices (same for both)
    predicted_prices = [
        {
            'date': (datetime.now() + timedelta(days=i)).isoformat(),
            'predicted_price': 2500 + i * 100
        }
        for i in range(1, 8)
    ]
    
    crops = [
        ('tomato', 'Highly Perishable'),
        ('wheat', 'Non-Perishable')
    ]
    
    for crop_name, category in crops:
        result = tools.calculate_optimal_selling_time(
            crop_name=crop_name,
            current_price=2500,
            predicted_prices=predicted_prices,
            quantity_quintals=100,
            storage_capacity=True
        )
        
        if result['success']:
            rec = result['recommendation']
            print(f"\n{crop_name.upper()} ({category}):")
            print(f"  Recommendation: {rec['timing']}")
            print(f"  Days to Wait: {rec['days_to_wait']}")
            print(f"  Net Profit: ₹{rec['net_profit']:.2f}")
            print(f"  Reason: {rec['reason']}")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("RISE Optimal Selling Time Calculator - Examples")
    print("="*60)
    
    try:
        example_perishability_analysis()
        example_storage_cost_calculation()
        example_optimal_selling_time()
        example_price_alerts()
        example_comparison_scenarios()
        example_perishable_vs_non_perishable()
        
        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
