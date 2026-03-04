"""
RISE Alert Preferences Management UI
Streamlit component for managing unused equipment alert preferences
"""

import streamlit as st
import requests
import json
from typing import Dict, Any


def render_alert_preferences(user_id: str, api_base_url: str = "http://localhost:8000"):
    """
    Render alert preferences management interface
    
    Args:
        user_id: Current user ID
        api_base_url: Base URL for API calls
    """
    st.header("🔔 Alert Preferences")
    st.write("Manage your unused equipment alert settings")
    
    # Fetch current preferences
    with st.spinner("Loading preferences..."):
        prefs_result = get_alert_preferences(user_id, api_base_url)
    
    if not prefs_result.get('success'):
        st.error(f"Error loading preferences: {prefs_result.get('error', 'Unknown error')}")
        return
    
    current_prefs = prefs_result.get('alert_preferences', {})
    
    # Alert Settings Section
    st.subheader("Alert Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Enable/disable alerts
        alerts_enabled = st.checkbox(
            "Enable unused equipment alerts",
            value=current_prefs.get('unused_equipment_alerts', True),
            help="Receive notifications when your equipment is unused"
        )
        
        # Alert frequency
        frequency = st.selectbox(
            "Alert Frequency",
            options=['daily', 'weekly', 'monthly'],
            index=['daily', 'weekly', 'monthly'].index(
                current_prefs.get('alert_frequency', 'weekly')
            ),
            help="How often you want to receive alerts"
        )
    
    with col2:
        # Threshold days
        threshold_days = st.number_input(
            "Alert Threshold (days)",
            min_value=7,
            max_value=90,
            value=current_prefs.get('alert_threshold_days', 30),
            step=7,
            help="Number of days of inactivity before alert"
        )
        
        # Alert channels
        st.write("Alert Channels:")
        voice_alerts = st.checkbox(
            "Voice notifications",
            value='voice' in current_prefs.get('alert_channels', ['voice', 'sms'])
        )
        sms_alerts = st.checkbox(
            "SMS notifications",
            value='sms' in current_prefs.get('alert_channels', ['voice', 'sms'])
        )
        push_alerts = st.checkbox(
            "Push notifications",
            value='push' in current_prefs.get('alert_channels', ['voice', 'sms'])
        )
    
    # Quiet Hours Section
    st.subheader("Quiet Hours")
    st.write("Set times when you don't want to receive alerts")
    
    quiet_hours = current_prefs.get('quiet_hours', {})
    
    col3, col4, col5 = st.columns(3)
    
    with col3:
        quiet_enabled = st.checkbox(
            "Enable quiet hours",
            value=quiet_hours.get('enabled', True)
        )
    
    with col4:
        quiet_start = st.time_input(
            "Start time",
            value=_parse_time(quiet_hours.get('start', '22:00')),
            disabled=not quiet_enabled
        )
    
    with col5:
        quiet_end = st.time_input(
            "End time",
            value=_parse_time(quiet_hours.get('end', '07:00')),
            disabled=not quiet_enabled
        )
    
    # Save button
    st.write("")
    if st.button("💾 Save Preferences", type="primary", use_container_width=True):
        # Build alert channels list
        alert_channels = []
        if voice_alerts:
            alert_channels.append('voice')
        if sms_alerts:
            alert_channels.append('sms')
        if push_alerts:
            alert_channels.append('push')
        
        # Build preferences object
        new_prefs = {
            'unused_equipment_alerts': alerts_enabled,
            'alert_frequency': frequency,
            'alert_threshold_days': threshold_days,
            'alert_channels': alert_channels,
            'quiet_hours': {
                'enabled': quiet_enabled,
                'start': quiet_start.strftime('%H:%M'),
                'end': quiet_end.strftime('%H:%M')
            }
        }
        
        # Save preferences
        with st.spinner("Saving preferences..."):
            save_result = update_alert_preferences(user_id, new_prefs, api_base_url)
        
        if save_result.get('success'):
            st.success("✅ Preferences saved successfully!")
            st.balloons()
        else:
            st.error(f"❌ Error saving preferences: {save_result.get('error', 'Unknown error')}")
    
    # Preview Section
    st.write("---")
    st.subheader("📊 Alert Preview")
    
    if alerts_enabled:
        st.info(f"""
        **Your Alert Settings:**
        - Frequency: {frequency.capitalize()}
        - Threshold: {threshold_days} days of inactivity
        - Channels: {', '.join(alert_channels) if alert_channels else 'None selected'}
        - Quiet Hours: {'Enabled' if quiet_enabled else 'Disabled'} 
          {f'({quiet_start.strftime("%H:%M")} - {quiet_end.strftime("%H:%M")})' if quiet_enabled else ''}
        """)
    else:
        st.warning("⚠️ Alerts are currently disabled. You won't receive any notifications.")


def render_unused_equipment_dashboard(user_id: str, api_base_url: str = "http://localhost:8000"):
    """
    Render dashboard showing unused equipment
    
    Args:
        user_id: Current user ID
        api_base_url: Base URL for API calls
    """
    st.header("📦 Unused Equipment Dashboard")
    
    # Fetch unused resources
    with st.spinner("Loading unused equipment..."):
        unused_result = get_unused_resources(user_id, api_base_url)
    
    if not unused_result.get('success'):
        st.error(f"Error loading data: {unused_result.get('error', 'Unknown error')}")
        return
    
    unused_resources = unused_result.get('unused_resources', [])
    
    if not unused_resources:
        st.success("🎉 Great! All your equipment is being utilized.")
        return
    
    st.warning(f"⚠️ You have {len(unused_resources)} unused equipment items")
    
    # Display each unused resource
    for resource in unused_resources:
        with st.expander(f"🚜 {resource['equipment_name']} - {resource['days_unused']} days unused"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Type:** {resource['equipment_type'].capitalize()}")
                st.write(f"**Daily Rate:** ₹{resource['daily_rate']:.2f}")
                st.write(f"**Location:** {resource['location']['district']}, {resource['location']['state']}")
                st.write(f"**Days Unused:** {resource['days_unused']} days")
            
            with col2:
                # Calculate potential income
                income_result = calculate_potential_income(resource, api_base_url)
                
                if income_result.get('success'):
                    st.metric(
                        "Potential Monthly Income",
                        f"₹{income_result['estimated_monthly_income']:.0f}"
                    )
                    st.metric(
                        "Lost Income",
                        f"₹{income_result['opportunity_cost']:.0f}",
                        delta=f"-{income_result['opportunity_cost']:.0f}",
                        delta_color="inverse"
                    )
            
            # Action buttons
            col3, col4 = st.columns(2)
            
            with col3:
                if st.button(f"📝 List for Sharing", key=f"list_{resource['resource_id']}"):
                    st.info("Redirecting to equipment listing page...")
                    # In production, this would navigate to the listing page
            
            with col4:
                if st.button(f"🔕 Dismiss Alert", key=f"dismiss_{resource['resource_id']}"):
                    st.success("Alert dismissed")


def get_alert_preferences(user_id: str, api_base_url: str) -> Dict[str, Any]:
    """Fetch alert preferences from API"""
    try:
        response = requests.post(
            f"{api_base_url}/api/v1/community/resource-alerts/{user_id}",
            json={
                'action': 'get_preferences',
                'user_id': user_id
            },
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def update_alert_preferences(user_id: str, preferences: Dict[str, Any], 
                            api_base_url: str) -> Dict[str, Any]:
    """Update alert preferences via API"""
    try:
        response = requests.post(
            f"{api_base_url}/api/v1/community/resource-alerts/{user_id}",
            json={
                'action': 'update_preferences',
                'user_id': user_id,
                'preferences': preferences
            },
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_unused_resources(user_id: str, api_base_url: str) -> Dict[str, Any]:
    """Fetch unused resources from API"""
    try:
        response = requests.post(
            f"{api_base_url}/api/v1/community/resource-alerts/{user_id}",
            json={
                'action': 'find_unused',
                'days_threshold': 30
            },
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def calculate_potential_income(resource: Dict[str, Any], 
                               api_base_url: str) -> Dict[str, Any]:
    """Calculate potential income for resource"""
    try:
        response = requests.post(
            f"{api_base_url}/api/v1/community/resource-alerts/calculate",
            json={
                'action': 'calculate_income',
                'resource': resource
            },
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def _parse_time(time_str: str):
    """Parse time string to time object"""
    from datetime import datetime
    try:
        return datetime.strptime(time_str, '%H:%M').time()
    except:
        return datetime.strptime('09:00', '%H:%M').time()


# Main app for testing
if __name__ == "__main__":
    st.set_page_config(
        page_title="RISE - Alert Preferences",
        page_icon="🔔",
        layout="wide"
    )
    
    # Sidebar
    with st.sidebar:
        st.title("RISE")
        st.write("Rural Innovation & Sustainable Ecosystem")
        
        # Mock user selection for testing
        test_user = st.selectbox(
            "Select User",
            ["farmer_12345", "farmer_67890"]
        )
    
    # Main content
    tab1, tab2 = st.tabs(["Alert Preferences", "Unused Equipment"])
    
    with tab1:
        render_alert_preferences(test_user)
    
    with tab2:
        render_unused_equipment_dashboard(test_user)
