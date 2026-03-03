"""
RISE Weather Alert System Example
Demonstrates weather monitoring, alerts, irrigation calculator, and protective measures
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.weather_alert_tools import WeatherAlertTools


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def example_monitor_weather():
    """Example: Monitor weather for a user"""
    print_section("Example 1: Monitor Weather Conditions")
    
    # Initialize tools
    tools = WeatherAlertTools(region='us-east-1')
    
    # Monitor weather for a user
    # Note: This requires a user profile with location in DynamoDB
    user_id = 'demo_user_123'
    
    print(f"Monitoring weather for user: {user_id}")
    print("Fetching weather data and generating alerts...\n")
    
    result = tools.monitor_weather_conditions(user_id)
    
    if result['success']:
        print("✅ Weather monitoring successful!\n")
        
        # Display location
        location = result['location']
        print(f"📍 Location: {location.get('name', 'Unknown')}")
        print(f"   Coordinates: {location.get('latitude')}, {location.get('longitude')}\n")
        
        # Display alerts
        alerts = result['alerts']
        print(f"⚠️  Weather Alerts: {len(alerts)}")
        if alerts:
            for alert in alerts:
                print(f"\n   {alert['title']}")
                print(f"   Date: {alert['date']} ({alert['hours_ahead']} hours ahead)")
                print(f"   Severity: {alert['severity'].upper()}")
                print(f"   Message: {alert['message']}")
        else:
            print("   No adverse weather alerts")
        
        # Display recommendations summary
        recommendations = result['recommendations']
        print(f"\n📋 Activity Recommendations: {len(recommendations)} days")
        for day in recommendations:
            print(f"\n   Day {day['day_number']} ({day['date']}):")
            print(f"   - Recommended: {len(day['recommended'])} activities")
            print(f"   - Avoid: {len(day['avoid'])} activities")
        
        # Display irrigation summary
        irrigation = result['irrigation']
        print(f"\n💧 Irrigation Schedule:")
        print(f"   Soil Type: {irrigation['soil_type'].title()}")
        print(f"   Weekly Water Need: {irrigation['total_water_week']} mm")
        print(f"   Days Scheduled: {len(irrigation['schedule'])}")
        
        # Display protective measures
        measures = result['protective_measures']
        print(f"\n🛡️  Protective Measures: {len(measures)} required")
        for measure in measures:
            print(f"   - {measure['alert_type'].replace('_', ' ').title()} ({measure['urgency']} urgency)")
    
    else:
        print(f"❌ Error: {result.get('error')}")
        print("\nNote: This example requires:")
        print("  1. User profile in DynamoDB with location data")
        print("  2. OpenWeatherMap API key configured")
        print("  3. AWS credentials configured")


def example_detailed_alerts():
    """Example: Display detailed weather alerts"""
    print_section("Example 2: Detailed Weather Alerts")
    
    tools = WeatherAlertTools()
    user_id = 'demo_user_123'
    
    result = tools.monitor_weather_conditions(user_id)
    
    if result['success'] and result['alerts']:
        print("Detailed Weather Alerts:\n")
        
        for i, alert in enumerate(result['alerts'], 1):
            print(f"{i}. {alert['title']}")
            print(f"   Type: {alert['type']}")
            print(f"   Severity: {alert['severity'].upper()}")
            print(f"   Date: {alert['date']}")
            print(f"   Advance Notice: {alert['hours_ahead']} hours ({alert['hours_ahead']//24} days)")
            print(f"   Message: {alert['message']}")
            
            if 'details' in alert:
                print("   Details:")
                for key, value in alert['details'].items():
                    print(f"     - {key.replace('_', ' ').title()}: {value}")
            print()
    else:
        print("No alerts to display or error occurred")


def example_activity_recommendations():
    """Example: Display farming activity recommendations"""
    print_section("Example 3: Farming Activity Recommendations")
    
    tools = WeatherAlertTools()
    user_id = 'demo_user_123'
    
    result = tools.monitor_weather_conditions(user_id)
    
    if result['success']:
        recommendations = result['recommendations']
        
        for day_rec in recommendations:
            print(f"\n📅 Day {day_rec['day_number']} - {day_rec['date']}")
            print("-" * 60)
            
            # Recommended activities
            if day_rec['recommended']:
                print("\n✅ RECOMMENDED ACTIVITIES:")
                for activity in day_rec['recommended']:
                    print(f"\n   • {activity['activity']}")
                    print(f"     Reason: {activity['reason']}")
                    print(f"     Best Time: {activity['timing']}")
            
            # Activities to avoid
            if day_rec['avoid']:
                print("\n❌ ACTIVITIES TO AVOID:")
                for activity in day_rec['avoid']:
                    print(f"\n   • {activity['activity']}")
                    print(f"     Reason: {activity['reason']}")
            
            # Optimal timing
            if day_rec['optimal_timing']:
                print("\n⏰ OPTIMAL TIMING:")
                for timing in day_rec['optimal_timing']:
                    print(f"\n   • {timing['timing']}")
                    print(f"     Reason: {timing['reason']}")
            
            print()
    else:
        print("No recommendations available")


def example_irrigation_schedule():
    """Example: Display irrigation schedule"""
    print_section("Example 4: Irrigation Schedule & Calculator")
    
    tools = WeatherAlertTools()
    user_id = 'demo_user_123'
    
    result = tools.monitor_weather_conditions(user_id)
    
    if result['success']:
        irrigation = result['irrigation']
        
        print(f"Soil Type: {irrigation['soil_type'].title()}")
        print(f"Water Retention Factor: {irrigation['retention_factor']}x")
        print(f"Total Weekly Water Need: {irrigation['total_water_week']} mm\n")
        
        print("7-Day Irrigation Schedule:")
        print("-" * 80)
        
        for day in irrigation['schedule']:
            priority_icon = {
                'High': '🔴',
                'Medium': '🟡',
                'Low': '🔵',
                'Not Needed': '🟢'
            }.get(day['priority'], '⚪')
            
            print(f"\n{priority_icon} Day {day['day_number']} - {day['date']}")
            print(f"   Priority: {day['priority']} (Score: {day['score']}/10)")
            print(f"   Recommendation: {day['recommendation']}")
            print(f"   Water Amount: {day['water_amount']}")
            print(f"   Best Time: {day['optimal_time']}")
            print(f"   Weather: {day['weather']['temp_max']}°C, "
                  f"{day['weather']['humidity']}% humidity, "
                  f"{day['weather']['rainfall']}mm rain")
        
        print("\n💡 Water-Saving Tips:")
        for tip in irrigation['water_saving_tips']:
            print(f"   • {tip}")
    else:
        print("No irrigation data available")


def example_protective_measures():
    """Example: Display protective measures"""
    print_section("Example 5: Protective Measures")
    
    tools = WeatherAlertTools()
    user_id = 'demo_user_123'
    
    result = tools.monitor_weather_conditions(user_id)
    
    if result['success'] and result['protective_measures']:
        print("Protective Measures Required:\n")
        
        for measure in result['protective_measures']:
            urgency_icon = '🚨' if measure['urgency'] == 'high' else '⚠️'
            
            print(f"{urgency_icon} {measure['alert_type'].replace('_', ' ').title()}")
            print(f"   Date: {measure['date']}")
            print(f"   Urgency: {measure['urgency'].upper()}")
            print("\n   Action Items:")
            
            for i, action in enumerate(measure['measures'], 1):
                print(f"   {i}. {action}")
            
            print()
    else:
        print("✅ No protective measures needed at this time")


def example_get_recent_alerts():
    """Example: Get user's recent alerts"""
    print_section("Example 6: Get Recent Alerts")
    
    tools = WeatherAlertTools()
    user_id = 'demo_user_123'
    
    print(f"Fetching alerts from last 7 days for user: {user_id}\n")
    
    result = tools.get_user_alerts(user_id, days=7)
    
    if result['success']:
        print(f"✅ Found {result['count']} alert record(s)\n")
        
        for i, alert_data in enumerate(result['alerts'], 1):
            print(f"Alert Record {i}:")
            print(f"  Timestamp: {alert_data.get('timestamp', 'Unknown')}")
            print(f"  Location: {alert_data.get('location', {}).get('name', 'Unknown')}")
            print(f"  Alerts: {len(alert_data.get('alerts', []))}")
            print(f"  Recommendations: {len(alert_data.get('recommendations', []))} days")
            print()
    else:
        print(f"❌ Error: {result.get('error')}")


def example_simulated_weather():
    """Example: Simulate weather monitoring with sample data"""
    print_section("Example 7: Simulated Weather Monitoring")
    
    print("This example simulates weather monitoring with sample data\n")
    
    tools = WeatherAlertTools()
    
    # Simulate daily summary data
    daily_summary = [
        {
            'date': '2024-01-10',
            'temp_min': 15,
            'temp_max': 28,
            'humidity_avg': 60,
            'rain_total': 0,
            'weather': 'Clear'
        },
        {
            'date': '2024-01-11',
            'temp_min': 16,
            'temp_max': 30,
            'humidity_avg': 55,
            'rain_total': 2,
            'weather': 'Clear'
        },
        {
            'date': '2024-01-12',
            'temp_min': 18,
            'temp_max': 42,  # Extreme heat
            'humidity_avg': 35,
            'rain_total': 0,
            'weather': 'Clear'
        },
        {
            'date': '2024-01-13',
            'temp_min': 20,
            'temp_max': 32,
            'humidity_avg': 70,
            'rain_total': 60,  # Heavy rain
            'weather': 'Rain'
        },
        {
            'date': '2024-01-14',
            'temp_min': 3,  # Cold wave
            'temp_max': 15,
            'humidity_avg': 80,
            'rain_total': 5,
            'weather': 'Clouds'
        }
    ]
    
    # Detect adverse weather
    print("Detecting adverse weather conditions...\n")
    alerts = tools._detect_adverse_weather(daily_summary, [])
    
    print(f"Found {len(alerts)} weather alert(s):\n")
    for alert in alerts:
        print(f"⚠️  {alert['title']}")
        print(f"   Date: {alert['date']} ({alert['hours_ahead']//24} days ahead)")
        print(f"   Severity: {alert['severity'].upper()}")
        print(f"   Message: {alert['message']}\n")
    
    # Generate activity recommendations
    print("\nGenerating activity recommendations...\n")
    recommendations = tools._generate_activity_recommendations(daily_summary[:3], ['wheat'])
    
    for day in recommendations:
        print(f"Day {day['day_number']} ({day['date']}):")
        print(f"  Recommended: {len(day['recommended'])} activities")
        print(f"  Avoid: {len(day['avoid'])} activities\n")
    
    # Calculate irrigation
    print("Calculating irrigation schedule...\n")
    irrigation = tools._calculate_irrigation_timing(daily_summary, {'soil_type': 'loam'})
    
    print(f"Soil Type: {irrigation['soil_type'].title()}")
    print(f"Weekly Water Need: {irrigation['total_water_week']} mm\n")
    
    for day in irrigation['schedule'][:3]:
        print(f"{day['date']}: {day['priority']} priority (Score: {day['score']}/10)")
    
    # Generate protective measures
    print("\n\nGenerating protective measures...\n")
    measures = tools._generate_protective_measures(alerts)
    
    print(f"Found {len(measures)} protective measure set(s):\n")
    for measure in measures:
        print(f"🛡️  {measure['alert_type'].replace('_', ' ').title()}")
        print(f"   Urgency: {measure['urgency'].upper()}")
        print(f"   Actions: {len(measure['measures'])} items\n")


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("  RISE Weather Alert System - Examples")
    print("=" * 80)
    
    print("\nThese examples demonstrate the weather alert system capabilities.")
    print("Some examples require AWS resources and user data to be set up.\n")
    
    # Run simulated example (works without AWS setup)
    example_simulated_weather()
    
    print("\n" + "=" * 80)
    print("  Additional Examples (require AWS setup)")
    print("=" * 80)
    print("\nTo run the full examples, ensure you have:")
    print("  1. AWS credentials configured")
    print("  2. DynamoDB tables created (RISE-UserProfiles, RISE-WeatherAlerts)")
    print("  3. OpenWeatherMap API key set in environment")
    print("  4. User profile with location data in DynamoDB")
    print("\nUncomment the examples below to run them:\n")
    
    # Uncomment these to run with real AWS resources
    # example_monitor_weather()
    # example_detailed_alerts()
    # example_activity_recommendations()
    # example_irrigation_schedule()
    # example_protective_measures()
    # example_get_recent_alerts()


if __name__ == '__main__':
    main()
