"""
RISE Weather Integration Example
Demonstrates how to use weather tools for farming insights
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.weather_tools import WeatherTools


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def example_current_weather():
    """Example: Get current weather for a location"""
    print_section("Example 1: Current Weather")
    
    # Initialize weather tools
    # Note: Set OPENWEATHER_API_KEY environment variable
    weather_tools = WeatherTools(region='us-east-1')
    
    # Get current weather for New Delhi
    result = weather_tools.get_current_weather(
        latitude=28.6139,
        longitude=77.2090,
        location_name='New Delhi'
    )
    
    if result['success']:
        print(f"Location: {result['location']['name']}")
        print(f"From Cache: {result.get('from_cache', False)}")
        print(f"\nCurrent Conditions:")
        print(f"  Temperature: {result['current']['temperature']}°C")
        print(f"  Feels Like: {result['current']['feels_like']}°C")
        print(f"  Weather: {result['current']['weather_description']}")
        print(f"  Humidity: {result['current']['humidity']}%")
        print(f"  Wind Speed: {result['current']['wind_speed']} m/s")
        print(f"  Rain (1h): {result['current']['rain_1h']}mm")
        print(f"  Visibility: {result['current']['visibility']}m")
    else:
        print(f"Error: {result.get('error')}")


def example_weather_forecast():
    """Example: Get weather forecast"""
    print_section("Example 2: Weather Forecast")
    
    weather_tools = WeatherTools(region='us-east-1')
    
    # Get 5-day forecast for Bangalore
    result = weather_tools.get_forecast(
        latitude=12.9716,
        longitude=77.5946,
        days=5,
        location_name='Bangalore'
    )
    
    if result['success']:
        print(f"Location: {result['location']['name']}")
        print(f"Forecast Days: {result['forecast_days']}")
        print(f"From Cache: {result.get('from_cache', False)}")
        print(f"\nDaily Summary:")
        
        for day in result['daily_summary']:
            print(f"\n  {day['date']}:")
            print(f"    Temperature: {day['temp_min']}°C - {day['temp_max']}°C")
            print(f"    Weather: {day['weather']}")
            print(f"    Humidity: {day['humidity_avg']}%")
            print(f"    Rain: {day['rain_total']}mm")
    else:
        print(f"Error: {result.get('error')}")


def example_farming_insights():
    """Example: Get farming-specific weather insights"""
    print_section("Example 3: Farming Weather Insights")
    
    weather_tools = WeatherTools(region='us-east-1')
    
    # Get farming insights for Punjab (wheat belt)
    result = weather_tools.get_farming_weather_insights(
        latitude=30.9010,
        longitude=75.8573,
        location_name='Ludhiana, Punjab'
    )
    
    if result['success']:
        print(f"Location: {result['location']['name']}")
        
        print(f"\nCurrent Conditions:")
        print(f"  Temperature: {result['current_conditions']['temperature']}°C")
        print(f"  Humidity: {result['current_conditions']['humidity']}%")
        print(f"  Weather: {result['current_conditions']['weather_description']}")
        
        print(f"\nFarming Recommendations:")
        for i, rec in enumerate(result['farming_recommendations'][:5], 1):
            print(f"  {i}. {rec}")
        
        print(f"\nIrrigation Advice:")
        irrigation = result['irrigation_advice']
        print(f"  Priority: {irrigation['priority']}")
        print(f"  Score: {irrigation['score']}/10")
        print(f"  Advice: {irrigation['advice']}")
        print(f"  Optimal Timing: {irrigation['optimal_timing']}")
        print(f"  Expected Rain (48h): {irrigation['expected_rain_48h']}mm")
        
        if result['adverse_weather_alerts']:
            print(f"\nWeather Alerts:")
            for alert in result['adverse_weather_alerts']:
                print(f"  {alert['date']} (Day {alert['day_number']}):")
                for a in alert['alerts']:
                    print(f"    [{a['severity'].upper()}] {a['type']}: {a['message']}")
        
        print(f"\nOptimal Activities:")
        activities = result['optimal_activities']
        
        if activities['recommended_today']:
            print(f"  Recommended Today:")
            for activity in activities['recommended_today']:
                print(f"    ✓ {activity}")
        
        if activities['avoid_today']:
            print(f"  Avoid Today:")
            for activity in activities['avoid_today']:
                print(f"    ✗ {activity}")
        
        if activities['plan_for_tomorrow']:
            print(f"  Plan for Tomorrow:")
            for activity in activities['plan_for_tomorrow']:
                print(f"    → {activity}")
    else:
        print(f"Error: {result.get('error')}")


def example_multiple_locations():
    """Example: Compare weather across multiple farming regions"""
    print_section("Example 4: Multi-Location Weather Comparison")
    
    weather_tools = WeatherTools(region='us-east-1')
    
    # Major agricultural regions in India
    locations = [
        {'name': 'Punjab (Wheat)', 'lat': 30.9010, 'lon': 75.8573},
        {'name': 'Maharashtra (Cotton)', 'lat': 19.7515, 'lon': 75.7139},
        {'name': 'Tamil Nadu (Rice)', 'lat': 11.1271, 'lon': 78.6569},
        {'name': 'Gujarat (Cotton)', 'lat': 22.2587, 'lon': 71.1924}
    ]
    
    print("Current Weather Comparison:\n")
    print(f"{'Location':<25} {'Temp (°C)':<12} {'Humidity':<12} {'Rain (mm)':<12} {'Irrigation'}")
    print("-" * 80)
    
    for loc in locations:
        result = weather_tools.get_farming_weather_insights(
            latitude=loc['lat'],
            longitude=loc['lon'],
            location_name=loc['name']
        )
        
        if result['success']:
            temp = result['current_conditions']['temperature']
            humidity = result['current_conditions']['humidity']
            rain = result['current_conditions']['rain_1h']
            irrigation = result['irrigation_advice']['priority']
            
            print(f"{loc['name']:<25} {temp:<12.1f} {humidity:<12}% {rain:<12.1f} {irrigation}")


def example_irrigation_planning():
    """Example: Detailed irrigation planning"""
    print_section("Example 5: Irrigation Planning")
    
    weather_tools = WeatherTools(region='us-east-1')
    
    # Get insights for a location
    result = weather_tools.get_farming_weather_insights(
        latitude=17.3850,
        longitude=78.4867,
        location_name='Hyderabad'
    )
    
    if result['success']:
        print(f"Irrigation Planning for {result['location']['name']}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        irrigation = result['irrigation_advice']
        
        print(f"\n📊 Irrigation Need Assessment:")
        print(f"   Score: {irrigation['score']}/10")
        print(f"   Priority: {irrigation['priority']}")
        
        print(f"\n💧 Recommendation:")
        print(f"   {irrigation['advice']}")
        
        print(f"\n⏰ Optimal Timing:")
        print(f"   {irrigation['optimal_timing']}")
        
        print(f"\n🌧️ Weather Forecast:")
        print(f"   Expected rain (next 48h): {irrigation['expected_rain_48h']}mm")
        
        print(f"\n📅 Next 48 Hours:")
        for day in result['next_48_hours']:
            print(f"   {day['date']}: {day['temp_min']}-{day['temp_max']}°C, "
                  f"Rain: {day['rain_total']}mm")
        
        # Decision tree
        print(f"\n✅ Decision:")
        if irrigation['priority'] == 'High':
            print("   → Irrigate today during optimal timing")
            print("   → Monitor soil moisture after irrigation")
        elif irrigation['priority'] == 'Medium':
            print("   → Check soil moisture manually")
            print("   → Irrigate if soil appears dry")
        elif irrigation['priority'] == 'Low':
            print("   → Irrigation can be postponed")
            print("   → Continue monitoring weather")
        else:
            print("   → No irrigation needed")
            print("   → Wait for soil to dry before next irrigation")


def example_adverse_weather_monitoring():
    """Example: Monitor for adverse weather conditions"""
    print_section("Example 6: Adverse Weather Monitoring")
    
    weather_tools = WeatherTools(region='us-east-1')
    
    # Get forecast for a location
    result = weather_tools.get_farming_weather_insights(
        latitude=26.8467,
        longitude=80.9462,
        location_name='Lucknow'
    )
    
    if result['success']:
        print(f"Adverse Weather Monitoring for {result['location']['name']}")
        
        alerts = result['adverse_weather_alerts']
        
        if alerts:
            print(f"\n⚠️  {len(alerts)} Weather Alert(s) Found:\n")
            
            for alert in alerts:
                print(f"📅 {alert['date']} (Day {alert['day_number']}):")
                
                for a in alert['alerts']:
                    severity_icon = '🔴' if a['severity'] == 'high' else '🟡'
                    print(f"   {severity_icon} {a['message']}")
                    
                    # Provide protective measures
                    if a['type'] == 'extreme_heat':
                        print(f"      → Increase irrigation frequency")
                        print(f"      → Avoid field work during peak heat")
                    elif a['type'] == 'cold_wave':
                        print(f"      → Cover sensitive crops")
                        print(f"      → Protect young plants")
                    elif a['type'] == 'heavy_rain':
                        print(f"      → Ensure proper drainage")
                        print(f"      → Postpone fertilizer application")
                    elif a['type'] == 'moderate_rain':
                        print(f"      → Plan field activities accordingly")
                
                print()
        else:
            print("\n✅ No adverse weather alerts for the next 5 days")
            print("   Weather conditions are favorable for farming activities")


def example_cache_management():
    """Example: Cache management"""
    print_section("Example 7: Cache Management")
    
    weather_tools = WeatherTools(region='us-east-1')
    
    print("Fetching weather data (first call - from API)...")
    result1 = weather_tools.get_current_weather(28.6139, 77.2090, 'New Delhi')
    print(f"From Cache: {result1.get('from_cache', False)}")
    
    print("\nFetching same location again (should be from cache)...")
    result2 = weather_tools.get_current_weather(28.6139, 77.2090, 'New Delhi')
    print(f"From Cache: {result2.get('from_cache', False)}")
    
    print("\nCache benefits:")
    print("  ✓ Faster response time")
    print("  ✓ Reduced API calls")
    print("  ✓ Cost optimization")
    print("  ✓ 6-hour TTL ensures fresh data")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("  RISE Weather Integration Examples")
    print("="*60)
    
    try:
        # Check for API key
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            print("\n⚠️  Warning: OPENWEATHER_API_KEY not set in environment")
            print("   Set it with: export OPENWEATHER_API_KEY='your_api_key'")
            print("   Get free API key from: https://openweathermap.org/api\n")
            return
        
        # Run examples
        example_current_weather()
        example_weather_forecast()
        example_farming_insights()
        example_multiple_locations()
        example_irrigation_planning()
        example_adverse_weather_monitoring()
        example_cache_management()
        
        print_section("Examples Complete")
        print("Weather integration is ready for use in RISE!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
