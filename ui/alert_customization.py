"""
RISE Alert Customization UI
Streamlit interface for customizing resource availability alerts
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.availability_alert_tools import create_availability_alert_tools


def render_alert_customization():
    """Render alert customization interface"""
    st.header("🔔 Alert Customization")
    st.write("Customize your resource availability alerts")
    
    # Initialize tools
    if 'alert_tools' not in st.session_state:
        st.session_state.alert_tools = create_availability_alert_tools()
    
    tools = st.session_state.alert_tools
    
    # Get user ID from session
    user_id = st.session_state.get('user_id', 'demo_user_001')
    
    # Load current preferences
    if st.button("Load Current Preferences"):
        with st.spinner("Loading preferences..."):
            result = tools.get_alert_preferences(user_id)
            
            if result['success']:
                st.session_state.current_prefs = result['alert_preferences']
                st.success("Preferences loaded successfully!")
            else:
                st.error(f"Error: {result.get('error', 'Unknown error')}")
    
    # Display current preferences or defaults
    current_prefs = st.session_state.get('current_prefs', {
        'equipment_alerts': {
            'enabled': True,
            'equipment_types': [],
            'radius_km': 25,
            'frequency': 'immediate'
        },
        'buying_group_alerts': {
            'enabled': True,
            'product_interests': [],
            'min_discount': 15
        },
        'seasonal_alerts': {
            'enabled': True,
            'advance_notice_days': 30
        },
        'alert_channels': ['voice', 'sms'],
        'quiet_hours': {
            'enabled': True,
            'start': '22:00',
            'end': '07:00'
        }
    })
    
    # Equipment Availability Alerts
    st.subheader("🚜 Equipment Availability Alerts")
    
    equipment_enabled = st.checkbox(
        "Enable equipment availability alerts",
        value=current_prefs.get('equipment_alerts', {}).get('enabled', True),
        key='equipment_enabled'
    )
    
    if equipment_enabled:
        col1, col2 = st.columns(2)
        
        with col1:
            equipment_types = st.multiselect(
                "Equipment types of interest",
                options=['tractor', 'harvester', 'pump', 'drone', 'sprayer', 'cultivator'],
                default=current_prefs.get('equipment_alerts', {}).get('equipment_types', []),
                help="Leave empty to receive alerts for all equipment types"
            )
        
        with col2:
            radius_km = st.slider(
                "Alert radius (km)",
                min_value=5,
                max_value=50,
                value=current_prefs.get('equipment_alerts', {}).get('radius_km', 25),
                step=5
            )
        
        frequency = st.selectbox(
            "Alert frequency",
            options=['immediate', 'daily_digest', 'weekly_digest'],
            index=['immediate', 'daily_digest', 'weekly_digest'].index(
                current_prefs.get('equipment_alerts', {}).get('frequency', 'immediate')
            )
        )
    
    st.divider()
    
    # Bulk Buying Alerts
    st.subheader("💰 Bulk Buying Opportunity Alerts")
    
    buying_enabled = st.checkbox(
        "Enable bulk buying opportunity alerts",
        value=current_prefs.get('buying_group_alerts', {}).get('enabled', True),
        key='buying_enabled'
    )
    
    if buying_enabled:
        col1, col2 = st.columns(2)
        
        with col1:
            product_interests = st.multiselect(
                "Product interests",
                options=['seeds', 'fertilizers', 'pesticides', 'organic_inputs', 'tools', 'irrigation'],
                default=current_prefs.get('buying_group_alerts', {}).get('product_interests', []),
                help="Leave empty to receive alerts for all products"
            )
        
        with col2:
            min_discount = st.slider(
                "Minimum discount (%)",
                min_value=5,
                max_value=40,
                value=current_prefs.get('buying_group_alerts', {}).get('min_discount', 15),
                step=5,
                help="Only receive alerts for groups achieving this minimum discount"
            )
    
    st.divider()
    
    # Seasonal Demand Alerts
    st.subheader("📅 Seasonal Demand Alerts")
    
    seasonal_enabled = st.checkbox(
        "Enable seasonal demand prediction alerts",
        value=current_prefs.get('seasonal_alerts', {}).get('enabled', True),
        key='seasonal_enabled'
    )
    
    if seasonal_enabled:
        advance_notice_days = st.slider(
            "Advance notice (days)",
            min_value=7,
            max_value=90,
            value=current_prefs.get('seasonal_alerts', {}).get('advance_notice_days', 30),
            step=7,
            help="How many days in advance to receive seasonal demand predictions"
        )
    
    st.divider()
    
    # Alert Channels
    st.subheader("📱 Alert Channels")
    
    alert_channels = st.multiselect(
        "How would you like to receive alerts?",
        options=['voice', 'sms', 'push', 'email'],
        default=current_prefs.get('alert_channels', ['voice', 'sms'])
    )
    
    st.divider()
    
    # Quiet Hours
    st.subheader("🌙 Quiet Hours")
    
    quiet_hours_enabled = st.checkbox(
        "Enable quiet hours",
        value=current_prefs.get('quiet_hours', {}).get('enabled', True),
        help="Suppress non-urgent alerts during specified hours"
    )
    
    if quiet_hours_enabled:
        col1, col2 = st.columns(2)
        
        with col1:
            quiet_start = st.time_input(
                "Quiet hours start",
                value=None,
                help="Start time for quiet hours (e.g., 22:00)"
            )
        
        with col2:
            quiet_end = st.time_input(
                "Quiet hours end",
                value=None,
                help="End time for quiet hours (e.g., 07:00)"
            )
    
    st.divider()
    
    # Save preferences
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 Save Preferences", type="primary"):
            # Prepare preferences data
            preferences = {
                'equipment_alerts': {
                    'enabled': equipment_enabled,
                    'equipment_types': equipment_types if equipment_enabled else [],
                    'radius_km': radius_km if equipment_enabled else 25,
                    'frequency': frequency if equipment_enabled else 'immediate'
                },
                'buying_group_alerts': {
                    'enabled': buying_enabled,
                    'product_interests': product_interests if buying_enabled else [],
                    'min_discount': min_discount if buying_enabled else 15
                },
                'seasonal_alerts': {
                    'enabled': seasonal_enabled,
                    'advance_notice_days': advance_notice_days if seasonal_enabled else 30
                },
                'alert_channels': alert_channels,
                'quiet_hours': {
                    'enabled': quiet_hours_enabled,
                    'start': quiet_start.strftime('%H:%M') if quiet_hours_enabled and quiet_start else '22:00',
                    'end': quiet_end.strftime('%H:%M') if quiet_hours_enabled and quiet_end else '07:00'
                }
            }
            
            with st.spinner("Saving preferences..."):
                result = tools.customize_alert_preferences(user_id, preferences)
                
                if result['success']:
                    st.success("✅ Preferences saved successfully!")
                    st.session_state.current_prefs = result['alert_preferences']
                else:
                    st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    with col2:
        if st.button("🔄 Reset to Defaults"):
            st.session_state.current_prefs = {
                'equipment_alerts': {
                    'enabled': True,
                    'equipment_types': [],
                    'radius_km': 25,
                    'frequency': 'immediate'
                },
                'buying_group_alerts': {
                    'enabled': True,
                    'product_interests': [],
                    'min_discount': 15
                },
                'seasonal_alerts': {
                    'enabled': True,
                    'advance_notice_days': 30
                },
                'alert_channels': ['voice', 'sms'],
                'quiet_hours': {
                    'enabled': True,
                    'start': '22:00',
                    'end': '07:00'
                }
            }
            st.rerun()


def render_seasonal_demand_predictor():
    """Render seasonal demand prediction interface"""
    st.header("📊 Seasonal Demand Predictor")
    st.write("Predict your equipment and resource needs based on crop calendar")
    
    # Initialize tools
    if 'alert_tools' not in st.session_state:
        st.session_state.alert_tools = create_availability_alert_tools()
    
    tools = st.session_state.alert_tools
    user_id = st.session_state.get('user_id', 'demo_user_001')
    
    # Crop calendar input
    st.subheader("🌾 Your Crop Calendar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        crop_name = st.text_input("Crop name", placeholder="e.g., Rice, Wheat")
        planting_date = st.date_input("Planting date")
    
    with col2:
        crop_area = st.number_input("Area (acres)", min_value=0.1, value=2.0, step=0.1)
        harvest_date = st.date_input("Expected harvest date")
    
    if st.button("🔮 Predict Seasonal Demand", type="primary"):
        if crop_name:
            crop_calendar = {
                crop_name: {
                    'planting_date': planting_date.isoformat(),
                    'harvest_date': harvest_date.isoformat(),
                    'area_acres': crop_area
                }
            }
            
            with st.spinner("Analyzing seasonal demand patterns..."):
                result = tools.predict_seasonal_demand(user_id, crop_calendar)
                
                if result['success']:
                    st.success("✅ Demand prediction generated!")
                    
                    predictions = result['predictions']
                    
                    # Display predictions
                    st.subheader("📋 Predicted Equipment Needs")
                    if predictions.get('equipment_needs'):
                        for need in predictions['equipment_needs']:
                            st.write(f"• {need}")
                    else:
                        st.info("No specific equipment needs identified")
                    
                    st.subheader("📈 Peak Demand Periods")
                    if predictions.get('peak_periods'):
                        for period in predictions['peak_periods']:
                            st.write(f"• {period}")
                    else:
                        st.info("No peak periods identified")
                    
                    st.subheader("⏰ Recommended Booking Timeline")
                    if predictions.get('booking_timeline'):
                        for timeline in predictions['booking_timeline']:
                            st.write(f"• {timeline}")
                    else:
                        st.info("No specific timeline recommendations")
                    
                    st.subheader("💡 Cost Optimization Strategies")
                    if predictions.get('cost_optimization'):
                        for strategy in predictions['cost_optimization']:
                            st.write(f"• {strategy}")
                    
                    st.subheader("🎯 Recommendations")
                    if predictions.get('recommendations'):
                        for rec in predictions['recommendations']:
                            st.write(f"• {rec}")
                    
                    # Show full AI response in expander
                    with st.expander("View Full AI Analysis"):
                        st.text(result['prediction_text'])
                
                else:
                    st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
        else:
            st.warning("Please enter crop name")


def render_advance_booking():
    """Render advance booking interface"""
    st.header("📅 Advance Booking System")
    st.write("Book equipment in advance based on seasonal predictions")
    
    # Initialize tools
    if 'alert_tools' not in st.session_state:
        st.session_state.alert_tools = create_availability_alert_tools()
    
    tools = st.session_state.alert_tools
    user_id = st.session_state.get('user_id', 'demo_user_001')
    
    col1, col2 = st.columns(2)
    
    with col1:
        equipment_type = st.selectbox(
            "Equipment type",
            options=['tractor', 'harvester', 'pump', 'drone', 'sprayer', 'cultivator']
        )
        
        booking_date = st.date_input(
            "Booking date",
            min_value=st.session_state.get('today', None)
        )
    
    with col2:
        duration_days = st.number_input(
            "Duration (days)",
            min_value=1,
            max_value=30,
            value=1
        )
        
        # Location (simplified)
        district = st.text_input("District", value="Demo District")
    
    if st.button("🔍 Find & Book Equipment", type="primary"):
        booking_data = {
            'equipment_type': equipment_type,
            'booking_date': booking_date.isoformat(),
            'duration_days': duration_days,
            'location': {
                'district': district,
                'state': 'Demo State',
                'latitude': 28.6139,
                'longitude': 77.2090
            }
        }
        
        with st.spinner("Searching for available equipment..."):
            result = tools.create_advance_booking(user_id, booking_data)
            
            if result['success']:
                st.success("✅ Advance booking created successfully!")
                
                st.info(f"""
                **Booking Details:**
                - Booking ID: {result['advance_booking_id']}
                - Equipment: {result['equipment_name']}
                - Date: {booking_date.strftime('%d %B %Y')}
                - Duration: {duration_days} day(s)
                - Estimated Cost: ₹{result['estimated_cost']:.2f}
                - Reminder: {result['reminder_date']}
                """)
                
                st.write(result['message'])
            else:
                st.error(f"❌ {result.get('error', 'Unknown error')}")
                if 'recommendation' in result:
                    st.info(f"💡 {result['recommendation']}")


if __name__ == "__main__":
    st.set_page_config(
        page_title="RISE - Alert Customization",
        page_icon="🔔",
        layout="wide"
    )
    
    # Tabs for different features
    tab1, tab2, tab3 = st.tabs([
        "🔔 Alert Preferences",
        "📊 Seasonal Demand",
        "📅 Advance Booking"
    ])
    
    with tab1:
        render_alert_customization()
    
    with tab2:
        render_seasonal_demand_predictor()
    
    with tab3:
        render_advance_booking()
