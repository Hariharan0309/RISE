"""
RISE Resource Alert System - Example Usage
Demonstrates how to use the unused equipment alert system
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.resource_alert_tools import ResourceAlertTools
from tools.voice_tools import VoiceProcessingTools
import json


def example_find_unused_resources():
    """Example: Find unused equipment"""
    print("=" * 60)
    print("Example 1: Finding Unused Resources")
    print("=" * 60)
    
    alert_tools = ResourceAlertTools(region='us-east-1')
    
    # Find equipment unused for 30+ days
    result = alert_tools.find_unused_resources(days_threshold=30)
    
    if result['success']:
        print(f"\n✅ Found {result['count']} unused resources")
        
        for resource in result['unused_resources']:
            print(f"\n📦 {resource['equipment_name']}")
            print(f"   Type: {resource['equipment_type']}")
            print(f"   Days Unused: {resource['days_unused']}")
            print(f"   Daily Rate: ₹{resource['daily_rate']:.2f}")
            print(f"   Location: {resource['location']['district']}, {resource['location']['state']}")
    else:
        print(f"\n❌ Error: {result.get('error')}")


def example_calculate_potential_income():
    """Example: Calculate potential income from unused equipment"""
    print("\n" + "=" * 60)
    print("Example 2: Calculating Potential Income")
    print("=" * 60)
    
    alert_tools = ResourceAlertTools(region='us-east-1')
    
    # Sample resource data
    resource = {
        'resource_id': 'res_12345',
        'equipment_name': 'John Deere Tractor',
        'equipment_type': 'tractor',
        'daily_rate': 3000,
        'days_unused': 45
    }
    
    result = alert_tools.calculate_potential_income(resource)
    
    if result['success']:
        print(f"\n💰 Income Analysis for {resource['equipment_name']}")
        print(f"   Daily Rate: ₹{result['daily_rate']:.2f}")
        print(f"   Utilization Rate: {result['utilization_rate'] * 100:.0f}%")
        print(f"   Estimated Monthly Income: ₹{result['estimated_monthly_income']:.2f}")
        print(f"   Estimated Yearly Income: ₹{result['estimated_yearly_income']:.2f}")
        print(f"   Opportunity Cost (Lost Income): ₹{result['opportunity_cost']:.2f}")
        print(f"   Days Unused: {result['days_unused']}")
    else:
        print(f"\n❌ Error: {result.get('error')}")


def example_send_alert():
    """Example: Send alert to equipment owner"""
    print("\n" + "=" * 60)
    print("Example 3: Sending Unused Equipment Alert")
    print("=" * 60)
    
    alert_tools = ResourceAlertTools(region='us-east-1')
    
    # Sample resource data
    resource = {
        'resource_id': 'res_12345',
        'owner_user_id': 'farmer_001',
        'equipment_name': 'John Deere Tractor',
        'equipment_type': 'tractor',
        'daily_rate': 3000,
        'days_unused': 30,
        'location': {
            'state': 'Punjab',
            'district': 'Ludhiana'
        }
    }
    
    result = alert_tools.send_unused_resource_alert(resource, user_language='hi')
    
    if result['success']:
        print(f"\n✅ Alert sent successfully!")
        print(f"   Resource ID: {result['resource_id']}")
        print(f"   Owner: {result['owner_user_id']}")
        print(f"   Potential Monthly Income: ₹{result['potential_monthly_income']:.2f}")
        print(f"   Opportunity Cost: ₹{result['opportunity_cost']:.2f}")
        print(f"\n📱 Alert Message:")
        print(result['alert_message'])
    else:
        print(f"\n❌ Error: {result.get('error')}")


def example_alert_with_voice():
    """Example: Send alert with voice notification"""
    print("\n" + "=" * 60)
    print("Example 4: Alert with Voice Notification")
    print("=" * 60)
    
    alert_tools = ResourceAlertTools(region='us-east-1')
    voice_tools = VoiceProcessingTools(region='us-east-1')
    
    # Sample resource data
    resource = {
        'resource_id': 'res_67890',
        'owner_user_id': 'farmer_002',
        'equipment_name': 'Water Pump',
        'equipment_type': 'pump',
        'daily_rate': 500,
        'days_unused': 45,
        'location': {
            'state': 'Karnataka',
            'district': 'Bangalore Rural'
        }
    }
    
    # Send alert
    alert_result = alert_tools.send_unused_resource_alert(resource, user_language='kn')
    
    if alert_result['success']:
        print(f"\n✅ Alert generated successfully!")
        
        # Generate voice notification
        voice_result = voice_tools.synthesize_speech(
            alert_result['alert_message'],
            language_code='kn'
        )
        
        if voice_result['success']:
            print(f"🔊 Voice notification generated")
            print(f"   Format: {voice_result['audio_format']}")
            print(f"   Language: Kannada")
            print(f"   Audio size: {len(voice_result['audio_data'])} bytes (base64)")
        else:
            print(f"❌ Voice generation error: {voice_result.get('error')}")
    else:
        print(f"\n❌ Error: {alert_result.get('error')}")


def example_batch_alerts():
    """Example: Send batch alerts for all unused equipment"""
    print("\n" + "=" * 60)
    print("Example 5: Sending Batch Alerts")
    print("=" * 60)
    
    alert_tools = ResourceAlertTools(region='us-east-1')
    
    # Send batch alerts
    result = alert_tools.send_batch_alerts(days_threshold=30)
    
    if result['success']:
        print(f"\n✅ Batch alerts completed!")
        print(f"   Total Unused Resources: {result['total_unused']}")
        print(f"   Alerts Sent: {result['alerts_sent']}")
        print(f"   Alerts Failed: {result['alerts_failed']}")
        
        if result['alerts']:
            print(f"\n📊 Alert Summary:")
            for alert in result['alerts'][:3]:  # Show first 3
                print(f"   • {alert['resource_id']}: ₹{alert['potential_monthly_income']:.0f}/month")
    else:
        print(f"\n❌ Error: {result.get('error')}")


def example_alert_preferences():
    """Example: Manage alert preferences"""
    print("\n" + "=" * 60)
    print("Example 6: Managing Alert Preferences")
    print("=" * 60)
    
    alert_tools = ResourceAlertTools(region='us-east-1')
    user_id = 'farmer_001'
    
    # Get current preferences
    print("\n📋 Current Preferences:")
    prefs_result = alert_tools.get_alert_preferences(user_id)
    
    if prefs_result['success']:
        prefs = prefs_result['alert_preferences']
        print(f"   Alerts Enabled: {prefs.get('unused_equipment_alerts', True)}")
        print(f"   Frequency: {prefs.get('alert_frequency', 'weekly')}")
        print(f"   Threshold: {prefs.get('alert_threshold_days', 30)} days")
        print(f"   Channels: {', '.join(prefs.get('alert_channels', ['voice', 'sms']))}")
    
    # Update preferences
    print("\n🔄 Updating Preferences...")
    new_prefs = {
        'alert_frequency': 'daily',
        'alert_threshold_days': 15,
        'alert_channels': ['voice', 'sms', 'push']
    }
    
    update_result = alert_tools.update_alert_preferences(user_id, new_prefs)
    
    if update_result['success']:
        print("✅ Preferences updated successfully!")
        updated_prefs = update_result['alert_preferences']
        print(f"   New Frequency: {updated_prefs['alert_frequency']}")
        print(f"   New Threshold: {updated_prefs['alert_threshold_days']} days")
        print(f"   New Channels: {', '.join(updated_prefs['alert_channels'])}")
    else:
        print(f"❌ Error: {update_result.get('error')}")


def example_multilingual_alerts():
    """Example: Generate alerts in multiple languages"""
    print("\n" + "=" * 60)
    print("Example 7: Multilingual Alert Messages")
    print("=" * 60)
    
    alert_tools = ResourceAlertTools(region='us-east-1')
    
    resource = {
        'equipment_name': 'Tractor',
        'days_unused': 30
    }
    
    income_data = {
        'estimated_monthly_income': 54000.0,
        'opportunity_cost': 54000.0
    }
    
    languages = [
        ('hi', 'Hindi'),
        ('en', 'English'),
        ('ta', 'Tamil'),
        ('te', 'Telugu'),
        ('kn', 'Kannada'),
        ('pa', 'Punjabi')
    ]
    
    for lang_code, lang_name in languages:
        message = alert_tools._generate_alert_message(resource, income_data, lang_code)
        print(f"\n🌐 {lang_name} ({lang_code}):")
        print(message[:150] + "..." if len(message) > 150 else message)


def main():
    """Run all examples"""
    print("\n" + "🚜" * 30)
    print("RISE Resource Alert System - Example Usage")
    print("🚜" * 30)
    
    try:
        # Run examples
        example_find_unused_resources()
        example_calculate_potential_income()
        example_send_alert()
        example_alert_with_voice()
        example_batch_alerts()
        example_alert_preferences()
        example_multilingual_alerts()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
