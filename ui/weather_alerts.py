"""
RISE Weather Alerts UI Components
Streamlit components for displaying weather alerts and recommendations
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.weather_alert_tools import WeatherAlertTools


def render_weather_alerts_dashboard(user_id: str, location: Optional[Dict[str, Any]] = None):
    """
    Render complete weather alerts dashboard
    
    Args:
        user_id: User identifier
        location: Optional location data
    """
    st.markdown("## 🌤️ Weather Alerts & Recommendations")
    
    # Initialize weather alert tools
    if 'weather_alert_tools' not in st.session_state:
        st.session_state.weather_alert_tools = WeatherAlertTools()
    
    tools = st.session_state.weather_alert_tools
    
    # Add refresh button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh Weather", use_container_width=True):
            with st.spinner("Fetching latest weather data..."):
                result = tools.monitor_weather_conditions(user_id)
                if result['success']:
                    st.session_state.weather_alert_data = result
                    st.success("Weather data updated!")
                else:
                    st.error(f"Failed to fetch weather: {result.get('error')}")
    
    # Get weather alert data
    if 'weather_alert_data' not in st.session_state:
        with st.spinner("Loading weather alerts..."):
            result = tools.monitor_weather_conditions(user_id)
            if result['success']:
                st.session_state.weather_alert_data = result
            else:
                st.error(f"Failed to load weather alerts: {result.get('error')}")
                return
    
    data = st.session_state.weather_alert_data
    
    # Display location
    if location or data.get('location'):
        loc = location or data['location']
        st.info(f"📍 Location: {loc.get('name', 'Unknown')}")
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "⚠️ Alerts",
        "📋 Activities",
        "💧 Irrigation",
        "🛡️ Protection"
    ])
    
    with tab1:
        render_alerts_section(data.get('alerts', []))
    
    with tab2:
        render_activities_section(data.get('recommendations', []))
    
    with tab3:
        render_irrigation_section(data.get('irrigation', {}))
    
    with tab4:
        render_protective_measures_section(data.get('protective_measures', []))


def render_alerts_section(alerts: List[Dict[str, Any]]):
    """Render weather alerts section"""
    st.markdown("### Weather Alerts (48-72 Hour Advance Notice)")
    
    if not alerts:
        st.success("✅ No adverse weather alerts for the next 48-72 hours")
        st.info("We monitor weather conditions and will alert you 2-3 days in advance of any adverse weather.")
        return
    
    # Separate by severity
    high_severity = [a for a in alerts if a.get('severity') == 'high']
    medium_severity = [a for a in alerts if a.get('severity') == 'medium']
    
    # Display high severity alerts
    if high_severity:
        st.error(f"🚨 {len(high_severity)} Critical Weather Alert(s)")
        for alert in high_severity:
            render_alert_card(alert, 'high')
    
    # Display medium severity alerts
    if medium_severity:
        st.warning(f"⚠️ {len(medium_severity)} Weather Advisory(ies)")
        for alert in medium_severity:
            render_alert_card(alert, 'medium')


def render_alert_card(alert: Dict[str, Any], severity: str):
    """Render individual alert card"""
    # Choose color based on severity
    if severity == 'high':
        border_color = "#D32F2F"
        bg_color = "#FFEBEE"
        icon = "🚨"
    else:
        border_color = "#F57C00"
        bg_color = "#FFF3E0"
        icon = "⚠️"
    
    # Calculate days ahead
    hours_ahead = alert.get('hours_ahead', 0)
    days_ahead = hours_ahead // 24
    
    st.markdown(f"""
    <div style="
        border-left: 4px solid {border_color};
        background-color: {bg_color};
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    ">
        <h4 style="margin: 0; color: {border_color};">{icon} {alert['title']}</h4>
        <p style="margin: 0.5rem 0;"><strong>Date:</strong> {alert['date']} ({days_ahead} days ahead)</p>
        <p style="margin: 0.5rem 0;">{alert['message']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show details in expander
    with st.expander("View Details"):
        details = alert.get('details', {})
        for key, value in details.items():
            st.write(f"**{key.replace('_', ' ').title()}:** {value}")


def render_activities_section(recommendations: List[Dict[str, Any]]):
    """Render farming activities recommendations section"""
    st.markdown("### Recommended Farming Activities")
    
    if not recommendations:
        st.info("No activity recommendations available")
        return
    
    # Display recommendations for each day
    for day_rec in recommendations:
        day_num = day_rec['day_number']
        date = day_rec['date']
        
        # Create expander for each day
        with st.expander(f"📅 Day {day_num} - {date}", expanded=(day_num == 1)):
            # Recommended activities
            if day_rec['recommended']:
                st.markdown("#### ✅ Recommended Activities")
                for activity in day_rec['recommended']:
                    st.markdown(f"""
                    <div style="
                        background-color: #E8F5E9;
                        padding: 0.8rem;
                        margin: 0.5rem 0;
                        border-radius: 5px;
                        border-left: 3px solid #2E7D32;
                    ">
                        <strong>{activity['activity']}</strong><br/>
                        <em>Reason:</em> {activity['reason']}<br/>
                        <em>Best Time:</em> {activity['timing']}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Activities to avoid
            if day_rec['avoid']:
                st.markdown("#### ❌ Activities to Avoid")
                for activity in day_rec['avoid']:
                    st.markdown(f"""
                    <div style="
                        background-color: #FFEBEE;
                        padding: 0.8rem;
                        margin: 0.5rem 0;
                        border-radius: 5px;
                        border-left: 3px solid #D32F2F;
                    ">
                        <strong>{activity['activity']}</strong><br/>
                        <em>Reason:</em> {activity['reason']}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Optimal timing suggestions
            if day_rec['optimal_timing']:
                st.markdown("#### ⏰ Optimal Timing")
                for timing in day_rec['optimal_timing']:
                    st.info(f"**{timing['timing']}** - {timing['reason']}")


def render_irrigation_section(irrigation_data: Dict[str, Any]):
    """Render irrigation schedule and recommendations section"""
    st.markdown("### Irrigation Schedule & Calculator")
    
    if not irrigation_data:
        st.info("No irrigation data available")
        return
    
    # Display soil type and summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Soil Type",
            irrigation_data.get('soil_type', 'Unknown').title()
        )
    
    with col2:
        st.metric(
            "Weekly Water Need",
            f"{irrigation_data.get('total_water_week', 0)} mm"
        )
    
    with col3:
        retention = irrigation_data.get('retention_factor', 1.0)
        st.metric(
            "Water Retention",
            f"{retention:.1f}x"
        )
    
    st.markdown("---")
    
    # Display irrigation schedule
    schedule = irrigation_data.get('schedule', [])
    
    if schedule:
        st.markdown("#### 📅 7-Day Irrigation Schedule")
        
        for day in schedule:
            priority = day['priority']
            
            # Choose color based on priority
            if priority == 'High':
                color = "#D32F2F"
                bg_color = "#FFEBEE"
                icon = "🔴"
            elif priority == 'Medium':
                color = "#F57C00"
                bg_color = "#FFF3E0"
                icon = "🟡"
            elif priority == 'Low':
                color = "#1976D2"
                bg_color = "#E3F2FD"
                icon = "🔵"
            else:
                color = "#4CAF50"
                bg_color = "#E8F5E9"
                icon = "🟢"
            
            st.markdown(f"""
            <div style="
                border-left: 4px solid {color};
                background-color: {bg_color};
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 5px;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0;">{icon} {day['date']} (Day {day['day_number']})</h4>
                        <p style="margin: 0.3rem 0;"><strong>Priority:</strong> {priority} (Score: {day['score']}/10)</p>
                        <p style="margin: 0.3rem 0;">{day['recommendation']}</p>
                        <p style="margin: 0.3rem 0;"><strong>Amount:</strong> {day['water_amount']}</p>
                        <p style="margin: 0.3rem 0;"><strong>Best Time:</strong> {day['optimal_time']}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show weather details in expander
            with st.expander("Weather Details"):
                weather = day['weather']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Max Temp", f"{weather['temp_max']}°C")
                with col2:
                    st.metric("Humidity", f"{weather['humidity']}%")
                with col3:
                    st.metric("Rainfall", f"{weather['rainfall']} mm")
    
    # Display water-saving tips
    tips = irrigation_data.get('water_saving_tips', [])
    if tips:
        st.markdown("---")
        st.markdown("#### 💡 Water-Saving Tips")
        for tip in tips:
            st.info(f"• {tip}")


def render_protective_measures_section(measures: List[Dict[str, Any]]):
    """Render protective measures recommendations section"""
    st.markdown("### Protective Measures")
    
    if not measures:
        st.success("✅ No protective measures needed at this time")
        return
    
    # Separate by urgency
    high_urgency = [m for m in measures if m.get('urgency') == 'high']
    medium_urgency = [m for m in measures if m.get('urgency') == 'medium']
    
    # Display high urgency measures
    if high_urgency:
        st.error(f"🚨 {len(high_urgency)} Urgent Protective Measure(s) Required")
        for measure in high_urgency:
            render_protective_measure_card(measure, 'high')
    
    # Display medium urgency measures
    if medium_urgency:
        st.warning(f"⚠️ {len(medium_urgency)} Protective Measure(s) Recommended")
        for measure in medium_urgency:
            render_protective_measure_card(measure, 'medium')


def render_protective_measure_card(measure: Dict[str, Any], urgency: str):
    """Render individual protective measure card"""
    # Choose color based on urgency
    if urgency == 'high':
        border_color = "#D32F2F"
        bg_color = "#FFEBEE"
        icon = "🚨"
    else:
        border_color = "#F57C00"
        bg_color = "#FFF3E0"
        icon = "⚠️"
    
    alert_type = measure['alert_type'].replace('_', ' ').title()
    date = measure['date']
    
    st.markdown(f"""
    <div style="
        border-left: 4px solid {border_color};
        background-color: {bg_color};
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    ">
        <h4 style="margin: 0; color: {border_color};">{icon} {alert_type}</h4>
        <p style="margin: 0.5rem 0;"><strong>Date:</strong> {date}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display measures as checklist
    st.markdown("**Action Items:**")
    for i, action in enumerate(measure['measures'], 1):
        st.checkbox(action, key=f"{measure['alert_type']}_{date}_{i}")


def render_weather_alerts_widget(user_id: str):
    """
    Render compact weather alerts widget for sidebar or main page
    
    Args:
        user_id: User identifier
    """
    st.markdown("### 🌤️ Weather Alerts")
    
    # Initialize tools
    if 'weather_alert_tools' not in st.session_state:
        st.session_state.weather_alert_tools = WeatherAlertTools()
    
    tools = st.session_state.weather_alert_tools
    
    # Get recent alerts
    result = tools.get_user_alerts(user_id, days=3)
    
    if result['success'] and result['alerts']:
        latest_alert = result['alerts'][0]
        alert_count = len(latest_alert.get('alerts', []))
        
        if alert_count > 0:
            st.warning(f"⚠️ {alert_count} active weather alert(s)")
            
            # Show most critical alert
            alerts = latest_alert.get('alerts', [])
            critical = [a for a in alerts if a.get('severity') == 'high']
            
            if critical:
                st.error(f"🚨 {critical[0]['title']}")
                st.caption(critical[0]['message'])
            
            if st.button("View All Alerts", use_container_width=True):
                st.session_state.show_weather_dashboard = True
        else:
            st.success("✅ No weather alerts")
    else:
        st.info("No recent weather data")
    
    # Last updated
    if result['success'] and result['alerts']:
        timestamp = result['alerts'][0].get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                st.caption(f"Updated: {dt.strftime('%Y-%m-%d %H:%M')}")
            except:
                pass


# Example usage
if __name__ == "__main__":
    st.set_page_config(page_title="Weather Alerts Demo", layout="wide")
    
    # Demo user ID
    demo_user_id = "demo_user_123"
    
    # Render dashboard
    render_weather_alerts_dashboard(demo_user_id)
