"""
RISE Resource Availability Alert System - Example Usage
Demonstrates how to use the availability alert tools
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.availability_alert_tools import create_availability_alert_tools


def example_equipment_availability_alert():
    """Example: Send equipment availability alerts"""
    print("\n" + "="*60)
    print("Example 1: Equipment Availability Alert")
    print("="*60)
    
    tools = create_availability_alert_tools()
    
    # Send alert for newly available equipment
    result = tools.send_equipment_availability_alert(
        resource_id='res_demo123',
        radius_km=25
    )
    
    if result['success']:
        print(f"✅ Alerts sent: {result['alerts_sent']}")
        print(f"Equipment: {result['equipment_name']} ({result['equipment_type']})")
        
        if result['alerts']:
            print("\nAlert details:")
            for alert in result['alerts'][:3]:  # Show first 3
                print(f"  - User: {alert['user_id']}")
                print(f"    Distance: {alert['distance_km']} km")
                print(f"    Message: {alert['alert_message'][:100]}...")
    else:
        print(f"❌ Error: {result.get('error')}")


def example_bulk_buying_opportunity_alert():
    """Example: Send bulk buying opportunity alerts"""
    print("\n" + "="*60)
    print("Example 2: Bulk Buying Opportunity Alert")
    print("="*60)
    
    tools = create_availability_alert_tools()
    
    # Send alert for new buying group
    result = tools.send_bulk_buying_opportunity_alert(
        group_id='grp_demo123',
        radius_km=25
    )
    
    if result['success']:
        print(f"✅ Alerts sent: {result['alerts_sent']}")
        print(f"Group: {result['group_name']}")
        print(f"Products: {', '.join(result['target_products'])}")
        
        if result['alerts']:
            print("\nAlert details:")
            for alert in result['alerts'][:3]:
                print(f"  - User: {alert['user_id']}")
                print(f"    Potential savings: ₹{alert['potential_savings']:.2f}")
    else:
        print(f"❌ Error: {result.get('error')}")


def example_seasonal_demand_prediction():
    """Example: Predict seasonal equipment demand"""
    print("\n" + "="*60)
    print("Example 3: Seasonal Demand Prediction")
    print("="*60)
    
    tools = create_availability_alert_tools()
    
    # Define crop calendar
    crop_calendar = {
        'rice': {
            'planting_date': '2024-06-15',
            'harvest_date': '2024-11-15',
            'area_acres': 3
        },
        'wheat': {
            'planting_date': '2024-11-20',
            'harvest_date': '2025-04-20',
            'area_acres': 2
        }
    }
    
    # Predict demand
    result = tools.predict_seasonal_demand(
        user_id='demo_user_001',
        crop_calendar=crop_calendar
    )
    
    if result['success']:
        print(f"✅ Prediction generated for user: {result['user_id']}")
        
        predictions = result['predictions']
        
        print("\n📋 Equipment Needs:")
        for need in predictions.get('equipment_needs', [])[:5]:
            print(f"  • {need}")
        
        print("\n📈 Peak Demand Periods:")
        for period in predictions.get('peak_periods', [])[:3]:
            print(f"  • {period}")
        
        print("\n⏰ Booking Timeline:")
        for timeline in predictions.get('booking_timeline', [])[:3]:
            print(f"  • {timeline}")
        
        print("\n💡 Recommendations:")
        for rec in predictions.get('recommendations', [])[:3]:
            print(f"  • {rec}")
    else:
        print(f"❌ Error: {result.get('error')}")


def example_advance_booking():
    """Example: Create advance booking"""
    print("\n" + "="*60)
    print("Example 4: Advance Booking")
    print("="*60)
    
    tools = create_availability_alert_tools()
    
    # Create advance booking for future date
    booking_date = (datetime.now() + timedelta(days=45)).isoformat()
    
    booking_data = {
        'equipment_type': 'harvester',
        'booking_date': booking_date,
        'duration_days': 3,
        'location': {
            'district': 'Meerut',
            'state': 'Uttar Pradesh',
            'latitude': 28.9845,
            'longitude': 77.7064
        }
    }
    
    result = tools.create_advance_booking(
        user_id='demo_user_001',
        booking_data=booking_data
    )
    
    if result['success']:
        print(f"✅ Advance booking created!")
        print(f"Booking ID: {result['advance_booking_id']}")
        print(f"Equipment: {result['equipment_name']}")
        print(f"Date: {booking_date[:10]}")
        print(f"Duration: {booking_data['duration_days']} days")
        print(f"Estimated cost: ₹{result['estimated_cost']:.2f}")
        print(f"Reminder date: {result['reminder_date'][:10]}")
        print(f"\n{result['message']}")
    else:
        print(f"❌ Error: {result.get('error')}")
        if 'recommendation' in result:
            print(f"💡 {result['recommendation']}")


def example_optimal_sharing_schedule():
    """Example: Generate optimal sharing schedule"""
    print("\n" + "="*60)
    print("Example 5: Optimal Sharing Schedule")
    print("="*60)
    
    tools = create_availability_alert_tools()
    
    # Generate schedule for 30 days
    result = tools.generate_optimal_sharing_schedule(
        resource_id='res_demo123',
        time_period_days=30
    )
    
    if result['success']:
        print(f"✅ Optimal schedule generated!")
        print(f"Resource ID: {result['resource_id']}")
        print(f"Projected utilization: {result['projected_utilization_rate']*100:.1f}%")
        print(f"Projected monthly revenue: ₹{result['projected_monthly_revenue']:.2f}")
        print(f"Existing bookings: {result['existing_bookings']}")
        
        print("\n📋 Recommendations:")
        for rec in result.get('recommendations', [])[:5]:
            print(f"  • {rec}")
    else:
        print(f"❌ Error: {result.get('error')}")


def example_customize_alert_preferences():
    """Example: Customize alert preferences"""
    print("\n" + "="*60)
    print("Example 6: Customize Alert Preferences")
    print("="*60)
    
    tools = create_availability_alert_tools()
    
    # Define custom preferences
    preferences = {
        'equipment_alerts': {
            'enabled': True,
            'equipment_types': ['tractor', 'harvester', 'pump'],
            'radius_km': 30,
            'frequency': 'daily_digest'
        },
        'buying_group_alerts': {
            'enabled': True,
            'product_interests': ['seeds', 'fertilizers', 'organic_inputs'],
            'min_discount': 20
        },
        'seasonal_alerts': {
            'enabled': True,
            'advance_notice_days': 45
        },
        'alert_channels': ['voice', 'sms', 'push'],
        'quiet_hours': {
            'enabled': True,
            'start': '22:00',
            'end': '06:00'
        }
    }
    
    # Update preferences
    result = tools.customize_alert_preferences(
        user_id='demo_user_001',
        preferences=preferences
    )
    
    if result['success']:
        print(f"✅ Preferences updated for user: {result['user_id']}")
        print(f"\n{result['message']}")
        
        prefs = result['alert_preferences']
        
        print("\n📱 Equipment Alerts:")
        eq_alerts = prefs.get('equipment_alerts', {})
        print(f"  Enabled: {eq_alerts.get('enabled')}")
        print(f"  Types: {', '.join(eq_alerts.get('equipment_types', []))}")
        print(f"  Radius: {eq_alerts.get('radius_km')} km")
        print(f"  Frequency: {eq_alerts.get('frequency')}")
        
        print("\n💰 Buying Group Alerts:")
        bg_alerts = prefs.get('buying_group_alerts', {})
        print(f"  Enabled: {bg_alerts.get('enabled')}")
        print(f"  Products: {', '.join(bg_alerts.get('product_interests', []))}")
        print(f"  Min discount: {bg_alerts.get('min_discount')}%")
        
        print("\n📅 Seasonal Alerts:")
        s_alerts = prefs.get('seasonal_alerts', {})
        print(f"  Enabled: {s_alerts.get('enabled')}")
        print(f"  Advance notice: {s_alerts.get('advance_notice_days')} days")
        
        print("\n🔔 Alert Channels:")
        print(f"  {', '.join(prefs.get('alert_channels', []))}")
        
        print("\n🌙 Quiet Hours:")
        quiet = prefs.get('quiet_hours', {})
        print(f"  Enabled: {quiet.get('enabled')}")
        print(f"  Hours: {quiet.get('start')} - {quiet.get('end')}")
    else:
        print(f"❌ Error: {result.get('error')}")


def example_get_alert_preferences():
    """Example: Get current alert preferences"""
    print("\n" + "="*60)
    print("Example 7: Get Alert Preferences")
    print("="*60)
    
    tools = create_availability_alert_tools()
    
    # Get current preferences
    result = tools.get_alert_preferences(user_id='demo_user_001')
    
    if result['success']:
        print(f"✅ Preferences retrieved for user: {result['user_id']}")
        
        prefs = result['alert_preferences']
        
        print("\nCurrent Alert Preferences:")
        print(f"  Equipment alerts: {prefs.get('equipment_alerts', {}).get('enabled')}")
        print(f"  Buying group alerts: {prefs.get('buying_group_alerts', {}).get('enabled')}")
        print(f"  Seasonal alerts: {prefs.get('seasonal_alerts', {}).get('enabled')}")
        print(f"  Alert channels: {', '.join(prefs.get('alert_channels', []))}")
    else:
        print(f"❌ Error: {result.get('error')}")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("RISE Resource Availability Alert System - Examples")
    print("="*60)
    
    try:
        # Run examples
        example_equipment_availability_alert()
        example_bulk_buying_opportunity_alert()
        example_seasonal_demand_prediction()
        example_advance_booking()
        example_optimal_sharing_schedule()
        example_customize_alert_preferences()
        example_get_alert_preferences()
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
