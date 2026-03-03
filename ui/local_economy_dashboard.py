"""
RISE Local Economy Dashboard UI Component
Streamlit component for visualizing local economy metrics and community impact
"""

import streamlit as st
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from tools.local_economy_tools import LocalEconomyTools
except ImportError:
    st.error("Unable to import local economy tools. Please ensure the tools module is available.")
    LocalEconomyTools = None


def render_local_economy_dashboard():
    """Render the local economy dashboard interface"""
    st.header("🌾 Local Economy Dashboard")
    st.markdown("Track economic impact and community benefits from resource sharing")
    
    # Initialize tools
    if LocalEconomyTools is None:
        st.error("Local economy tools not available")
        return
    
    economy_tools = LocalEconomyTools()
    
    # Location selection
    st.subheader("📍 Select Location")
    col1, col2 = st.columns(2)
    
    with col1:
        state = st.selectbox(
            "State",
            ["Punjab", "Haryana", "Uttar Pradesh", "Maharashtra", "Karnataka", "Tamil Nadu"],
            key="economy_state"
        )
    
    with col2:
        # District options based on state
        district_options = {
            "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala"],
            "Haryana": ["Karnal", "Hisar", "Panipat", "Ambala"],
            "Uttar Pradesh": ["Meerut", "Agra", "Lucknow", "Varanasi"],
            "Maharashtra": ["Pune", "Nashik", "Nagpur", "Aurangabad"],
            "Karnataka": ["Bangalore Rural", "Mysore", "Belgaum", "Hubli"],
            "Tamil Nadu": ["Coimbatore", "Salem", "Madurai", "Tiruchirappalli"]
        }
        
        district = st.selectbox(
            "District",
            district_options.get(state, ["Select State First"]),
            key="economy_district"
        )
    
    # Time period selection
    st.subheader("📅 Time Period")
    col1, col2 = st.columns(2)
    
    with col1:
        period_option = st.selectbox(
            "Select Period",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom Range"],
            key="economy_period"
        )
    
    with col2:
        if period_option == "Custom Range":
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
            end_date = st.date_input("End Date", datetime.now())
        else:
            days_map = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90}
            days = days_map.get(period_option, 30)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
    
    # Calculate button
    if st.button("📊 Calculate Economic Impact", type="primary", use_container_width=True):
        with st.spinner("Calculating economic metrics..."):
            location = {
                'state': state,
                'district': district
            }
            
            time_period = {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
            
            # Calculate economic impact
            result = economy_tools.calculate_economic_impact(location, time_period)
            
            if result.get('success'):
                display_economic_impact(result)
            else:
                st.error(f"Error calculating economic impact: {result.get('error')}")


def display_economic_impact(result: Dict[str, Any]):
    """Display economic impact metrics"""
    metrics = result.get('metrics', {})
    summary = result.get('summary', {})
    
    # Summary metrics
    st.subheader("📈 Economic Impact Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Economic Benefit",
            f"₹{metrics.get('total_economic_benefit', 0):,.2f}",
            help="Total cost savings + additional income + cooperative savings"
        )
    
    with col2:
        st.metric(
            "Farmers Benefited",
            summary.get('total_farmers_benefited', 0),
            help="Unique farmers participating in resource sharing"
        )
    
    with col3:
        st.metric(
            "Total Transactions",
            summary.get('total_transactions', 0),
            help="Total resource sharing transactions"
        )
    
    with col4:
        st.metric(
            "Avg Savings/Farmer",
            f"₹{summary.get('average_savings_per_farmer', 0):,.2f}",
            help="Average economic benefit per farmer"
        )
    
    # Detailed metrics
    st.markdown("---")
    
    # Equipment utilization
    st.subheader("🚜 Equipment Utilization")
    utilization = metrics.get('equipment_utilization_rate', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Overall Utilization Rate",
            f"{utilization.get('overall_rate', 0)}%",
            help="Percentage of equipment actively being shared"
        )
        st.metric(
            "Total Equipment",
            utilization.get('total_equipment', 0),
            help="Total equipment available for sharing"
        )
    
    with col2:
        st.markdown("**Utilization by Equipment Type:**")
        by_type = utilization.get('by_type', {})
        if by_type:
            for equipment_type, data in by_type.items():
                st.write(f"- **{equipment_type.title()}**: {data['rate']}% ({data['utilized']}/{data['total']})")
        else:
            st.info("No equipment utilization data available")
    
    # Cost savings
    st.markdown("---")
    st.subheader("💰 Cost Savings")
    
    cost_savings = metrics.get('cost_savings', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Total Cost Savings",
            f"₹{cost_savings.get('total', 0):,.2f}",
            help="Total savings from equipment sharing vs purchasing"
        )
    
    with col2:
        st.metric(
            "Equipment Sharing Savings",
            f"₹{cost_savings.get('from_equipment_sharing', 0):,.2f}",
            help="Savings from renting equipment instead of buying"
        )
    
    # Additional income
    st.markdown("---")
    st.subheader("💵 Additional Income Generated")
    
    additional_income = metrics.get('additional_income', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Total Additional Income",
            f"₹{additional_income.get('total', 0):,.2f}",
            help="Total income generated from sharing equipment"
        )
    
    with col2:
        st.metric(
            "Equipment Sharing Income",
            f"₹{additional_income.get('from_equipment_sharing', 0):,.2f}",
            help="Income from equipment rental transactions"
        )
    
    # Cooperative buying savings
    st.markdown("---")
    st.subheader("🤝 Cooperative Buying Savings")
    
    coop_savings = metrics.get('cooperative_buying_savings', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Total Cooperative Savings",
            f"₹{coop_savings.get('total', 0):,.2f}",
            help="Total savings from bulk purchasing"
        )
    
    with col2:
        st.metric(
            "Active Buying Groups",
            coop_savings.get('group_count', 0),
            help="Number of active cooperative buying groups"
        )
    
    # Community engagement
    st.markdown("---")
    st.subheader("👥 Community Engagement")
    
    engagement_score = metrics.get('community_engagement_score', 0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Engagement Score",
            f"{engagement_score}/100",
            help="Community engagement level (0-100)"
        )
        
        # Engagement level indicator
        engagement_level = summary.get('engagement_level', 'Unknown')
        if engagement_level == 'Excellent':
            st.success(f"🌟 {engagement_level} Engagement")
        elif engagement_level == 'Good':
            st.info(f"✅ {engagement_level} Engagement")
        elif engagement_level == 'Moderate':
            st.warning(f"⚠️ {engagement_level} Engagement")
        else:
            st.error(f"📉 {engagement_level} Engagement")
    
    with col2:
        transaction_count = metrics.get('transaction_count', {})
        st.metric(
            "Unique Participants",
            transaction_count.get('unique_farmers', 0),
            help="Number of unique farmers participating"
        )
        st.metric(
            "Total Transactions",
            transaction_count.get('total', 0),
            help="Total resource sharing transactions"
        )
    
    # Sustainability metrics
    st.markdown("---")
    st.subheader("🌱 Sustainability Impact")
    
    sustainability = metrics.get('sustainability_metrics', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Equipment Purchases Avoided",
            sustainability.get('equipment_purchases_avoided', 0),
            help="Number of equipment purchases avoided through sharing"
        )
    
    with col2:
        st.metric(
            "CO₂ Savings (kg)",
            f"{sustainability.get('estimated_co2_savings_kg', 0):,.0f}",
            help="Estimated CO₂ emissions saved"
        )
    
    with col3:
        st.metric(
            "Resource Efficiency",
            f"{sustainability.get('resource_efficiency_score', 0)}%",
            help="Resource utilization efficiency score"
        )
    
    sustainability_level = sustainability.get('sustainability_level', 'Unknown')
    if sustainability_level == 'Highly Sustainable':
        st.success(f"🌟 {sustainability_level}")
    elif sustainability_level == 'Sustainable':
        st.info(f"✅ {sustainability_level}")
    elif sustainability_level == 'Moderately Sustainable':
        st.warning(f"⚠️ {sustainability_level}")
    else:
        st.error(f"📉 {sustainability_level}")
    
    # Export data option
    st.markdown("---")
    if st.button("📥 Export Report as JSON"):
        report_json = json.dumps(result, indent=2, default=str)
        st.download_button(
            label="Download JSON Report",
            data=report_json,
            file_name=f"economy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )


def render_user_economy_tracker():
    """Render individual user economy tracking"""
    st.header("👤 My Economic Impact")
    st.markdown("Track your personal savings and income from resource sharing")
    
    # Initialize tools
    if LocalEconomyTools is None:
        st.error("Local economy tools not available")
        return
    
    economy_tools = LocalEconomyTools()
    
    # User ID input
    user_id = st.text_input(
        "User ID",
        value=st.session_state.get('user_id', 'farmer_12345'),
        help="Enter your user ID"
    )
    
    # Time period selection
    period_option = st.selectbox(
        "Select Period",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days"],
        key="user_economy_period"
    )
    
    days_map = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90}
    days = days_map.get(period_option, 30)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    time_period = {
        'start': start_date.isoformat(),
        'end': end_date.isoformat()
    }
    
    # Track metrics
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💰 Track My Savings", use_container_width=True):
            with st.spinner("Calculating your savings..."):
                result = economy_tools.track_cost_savings(user_id, time_period)
                
                if result.get('success'):
                    display_user_savings(result)
                else:
                    st.error(f"Error: {result.get('error')}")
    
    with col2:
        if st.button("💵 Track My Income", use_container_width=True):
            with st.spinner("Calculating your income..."):
                result = economy_tools.track_additional_income(user_id, time_period)
                
                if result.get('success'):
                    display_user_income(result)
                else:
                    st.error(f"Error: {result.get('error')}")


def display_user_savings(result: Dict[str, Any]):
    """Display user savings breakdown"""
    st.subheader("💰 Your Cost Savings")
    
    savings = result.get('savings_breakdown', {})
    
    # Total savings
    st.metric(
        "Total Savings",
        f"₹{savings.get('total_savings', 0):,.2f}",
        help="Total cost savings from resource sharing"
    )
    
    # Equipment rental savings
    rental_savings = savings.get('equipment_rental_savings', {})
    st.markdown("**Equipment Rental Savings:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Rental Cost", f"₹{rental_savings.get('rental_cost', 0):,.2f}")
        st.metric("Bookings", rental_savings.get('booking_count', 0))
    
    with col2:
        st.metric("vs Purchase Cost", f"₹{rental_savings.get('vs_purchase', 0):,.2f}")
        st.metric("Savings", f"₹{rental_savings.get('total', 0):,.2f}")
    
    # Cooperative buying savings
    buying_savings = savings.get('cooperative_buying_savings', {})
    st.markdown("**Cooperative Buying Savings:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Groups Joined", buying_savings.get('group_count', 0))
    
    with col2:
        st.metric("Savings", f"₹{buying_savings.get('total', 0):,.2f}")


def display_user_income(result: Dict[str, Any]):
    """Display user income breakdown"""
    st.subheader("💵 Your Additional Income")
    
    income = result.get('income_breakdown', {})
    projections = result.get('projections', {})
    
    # Total income
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Total Income",
            f"₹{income.get('total_income', 0):,.2f}",
            help="Total income from equipment sharing"
        )
    
    with col2:
        st.metric(
            "Completed Bookings",
            f"{income.get('completed_bookings', 0)}/{income.get('total_bookings', 0)}",
            help="Completed vs total bookings"
        )
    
    # Income by equipment type
    st.markdown("**Income by Equipment Type:**")
    by_type = income.get('by_equipment_type', {})
    if by_type:
        for equipment_type, data in by_type.items():
            st.write(f"- **{equipment_type.title()}**: ₹{data['total']:,.2f} ({data['count']} bookings)")
    else:
        st.info("No income data available")
    
    # Projections
    st.markdown("**Income Projections:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Monthly Projection", f"₹{projections.get('monthly', 0):,.2f}")
    
    with col2:
        st.metric("Annual Projection", f"₹{projections.get('annual', 0):,.2f}")


# Main function to run the dashboard
if __name__ == "__main__":
    st.set_page_config(
        page_title="RISE Local Economy Dashboard",
        page_icon="🌾",
        layout="wide"
    )
    
    tab1, tab2 = st.tabs(["📊 Community Dashboard", "👤 My Impact"])
    
    with tab1:
        render_local_economy_dashboard()
    
    with tab2:
        render_user_economy_tracker()
