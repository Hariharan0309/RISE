"""
RISE Market Price Tracking - Example Usage
Demonstrates how to use market price tracking tools
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.market_price_tools import create_market_price_tools


def example_current_prices():
    """Example: Get current market prices"""
    print("=" * 60)
    print("Example 1: Current Market Prices")
    print("=" * 60)
    
    tools = create_market_price_tools()
    
    # Get current prices for wheat in Delhi region
    result = tools.get_current_prices(
        crop_name='wheat',
        latitude=28.6139,  # Delhi
        longitude=77.2090,
        radius_km=50
    )
    
    if result['success']:
        print(f"\nCrop: {result['crop_name'].title()}")
        print(f"Location: ({result['location']['latitude']}, {result['location']['longitude']})")
        print(f"Search Radius: {result['location']['radius_km']} km")
        print(f"\nPrice Statistics:")
        print(f"  Average: ₹{result['statistics']['avg_price']:.2f}/quintal")
        print(f"  Minimum: ₹{result['statistics']['min_price']:.2f}/quintal")
        print(f"  Maximum: ₹{result['statistics']['max_price']:.2f}/quintal")
        print(f"  Markets Found: {result['statistics']['market_count']}")
        
        print(f"\nTop 3 Markets:")
        for i, market in enumerate(result['markets'][:3], 1):
            print(f"\n{i}. {market['market_name']}")
            print(f"   Price: ₹{market['price']}/quintal")
            print(f"   Distance: {market['distance_km']} km")
            print(f"   Location: {market['location']['district']}, {market['location']['state']}")
    else:
        print(f"Error: {result['error']}")


def example_price_history():
    """Example: Get price history and trends"""
    print("\n" + "=" * 60)
    print("Example 2: Price History and Trends")
    print("=" * 60)
    
    tools = create_market_price_tools()
    
    # Get 30-day price history
    result = tools.get_price_history(
        crop_name='wheat',
        market_id='MKT001',
        days=30
    )
    
    if result['success']:
        print(f"\nCrop: {result['crop_name'].title()}")
        print(f"Market: {result['market_id']}")
        print(f"Period: {result['period']['days']} days")
        
        trends = result['trends']
        print(f"\nPrice Trends:")
        print(f"  Trend: {trends['trend'].upper()}")
        print(f"  Change: {trends['change_percent']:+.2f}%")
        print(f"  Average Price: ₹{trends['avg_price']:.2f}/quintal")
        print(f"  Price Range: ₹{trends['price_range']['min']} - ₹{trends['price_range']['max']}")
        print(f"  Volatility: ₹{trends['volatility']:.2f}")
        
        print(f"\nRecent Price History (last 5 days):")
        for entry in result['history'][-5:]:
            date = datetime.fromisoformat(entry['date']).strftime('%Y-%m-%d')
            print(f"  {date}: ₹{entry['price']:.2f}/quintal (Arrival: {entry['arrival_quantity']} quintals)")
    else:
        print(f"Error: {result['error']}")


def example_price_predictions():
    """Example: Predict future price trends"""
    print("\n" + "=" * 60)
    print("Example 3: Price Predictions")
    print("=" * 60)
    
    tools = create_market_price_tools()
    
    # Predict prices for next 7 days
    result = tools.predict_price_trends(
        crop_name='wheat',
        market_id='MKT001',
        forecast_days=7
    )
    
    if result['success']:
        print(f"\nCrop: {result['crop_name'].title()}")
        print(f"Market: {result['market_id']}")
        print(f"Forecast Period: {result['forecast_days']} days")
        print(f"Method: {result['method'].replace('_', ' ').title()}")
        print(f"Confidence: {result['confidence'].title()}")
        
        print(f"\nPrice Predictions:")
        for pred in result['predictions']:
            date = datetime.fromisoformat(pred['date']).strftime('%Y-%m-%d')
            price = pred['predicted_price']
            low = pred['confidence_range']['low']
            high = pred['confidence_range']['high']
            print(f"  {date}: ₹{price:.2f} (Range: ₹{low:.2f} - ₹{high:.2f})")
        
        # Find best day
        best_day = max(result['predictions'], key=lambda p: p['predicted_price'])
        best_date = datetime.fromisoformat(best_day['date']).strftime('%B %d, %Y')
        print(f"\n🎯 Best predicted price: ₹{best_day['predicted_price']:.2f} on {best_date}")
    else:
        print(f"Error: {result['error']}")


def example_optimal_selling_time():
    """Example: Calculate optimal selling time"""
    print("\n" + "=" * 60)
    print("Example 4: Optimal Selling Time")
    print("=" * 60)
    
    tools = create_market_price_tools()
    
    # Calculate optimal selling time for wheat with storage
    result = tools.get_optimal_selling_time(
        crop_name='wheat',
        latitude=28.6139,
        longitude=77.2090,
        harvest_date=None,
        storage_capacity=True
    )
    
    if result['success']:
        print(f"\nCrop: {result['crop_name'].title()}")
        print(f"Current Best Price: ₹{result['current_best_price']:.2f}/quintal")
        print(f"Best Market: {result['best_market']['market_name']}")
        print(f"Distance: {result['best_market']['distance_km']} km")
        
        rec = result['recommendation']
        print(f"\n💡 Recommendation:")
        print(f"  Timing: {rec['timing'].replace('_', ' ').title()}")
        print(f"  Reason: {rec['reason']}")
        print(f"  Expected Price: ₹{rec['expected_price']:.2f}/quintal")
        
        if 'net_gain' in rec:
            print(f"  Storage Cost: ₹{rec['storage_cost']:.2f}/quintal")
            print(f"  Net Gain: ₹{rec['net_gain']:.2f}/quintal")
        
        perish = result['perishability']
        print(f"\n📦 Crop Storage Info:")
        print(f"  Category: {perish['category'].replace('_', ' ').title()}")
        print(f"  Shelf Life: {perish['shelf_life_days']} days")
        print(f"  Storage Cost: ₹{perish['storage_cost_per_day']}/quintal/day")
    else:
        print(f"Error: {result['error']}")


def example_perishable_crop():
    """Example: Optimal selling time for perishable crop"""
    print("\n" + "=" * 60)
    print("Example 5: Perishable Crop (Tomato)")
    print("=" * 60)
    
    tools = create_market_price_tools()
    
    # Calculate for tomato (highly perishable)
    result = tools.get_optimal_selling_time(
        crop_name='tomato',
        latitude=28.6139,
        longitude=77.2090,
        harvest_date=None,
        storage_capacity=True
    )
    
    if result['success']:
        print(f"\nCrop: {result['crop_name'].title()}")
        print(f"Current Best Price: ₹{result['current_best_price']:.2f}/quintal")
        
        rec = result['recommendation']
        print(f"\n💡 Recommendation:")
        print(f"  Timing: {rec['timing'].replace('_', ' ').title()}")
        print(f"  Reason: {rec['reason']}")
        
        perish = result['perishability']
        print(f"\n📦 Crop Storage Info:")
        print(f"  Category: {perish['category'].replace('_', ' ').title()}")
        print(f"  Shelf Life: {perish['shelf_life_days']} days")
        print(f"  ⚠️ Highly perishable - immediate sale recommended!")
    else:
        print(f"Error: {result['error']}")


def example_comparison():
    """Example: Compare prices across multiple crops"""
    print("\n" + "=" * 60)
    print("Example 6: Multi-Crop Price Comparison")
    print("=" * 60)
    
    tools = create_market_price_tools()
    
    crops = ['wheat', 'rice', 'potato']
    location = {'latitude': 28.6139, 'longitude': 77.2090}
    
    print(f"\nComparing prices for multiple crops:")
    print(f"Location: Delhi region")
    print(f"Radius: 50 km\n")
    
    for crop in crops:
        result = tools.get_current_prices(
            crop_name=crop,
            latitude=location['latitude'],
            longitude=location['longitude'],
            radius_km=50
        )
        
        if result['success']:
            stats = result['statistics']
            print(f"{crop.title():10} - Avg: ₹{stats['avg_price']:7.2f}/quintal  "
                  f"Range: ₹{stats['min_price']:7.2f} - ₹{stats['max_price']:7.2f}  "
                  f"Markets: {stats['market_count']}")
        else:
            print(f"{crop.title():10} - Error: {result['error']}")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("RISE Market Price Tracking - Example Usage")
    print("=" * 60)
    
    try:
        example_current_prices()
        example_price_history()
        example_price_predictions()
        example_optimal_selling_time()
        example_perishable_crop()
        example_comparison()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60 + "\n")
    
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
