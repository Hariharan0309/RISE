"""
RISE Direct Buyer Connection Dashboard
Streamlit UI component for farmer-buyer connections
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.buyer_connection_tools import create_buyer_connection_tools
from datetime import datetime, timedelta
import json


def render_buyer_connection_dashboard():
    """Render the buyer connection dashboard"""
    
    st.title("🤝 Direct Buyer Connection")
    st.markdown("Connect directly with verified buyers for fair prices and reduced middleman costs")
    
    # Initialize tools
    if 'buyer_tools' not in st.session_state:
        st.session_state.buyer_tools = create_buyer_connection_tools()
    
    buyer_tools = st.session_state.buyer_tools
    
    # Create tabs for different features
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 List Your Crop",
        "🔍 View Matches",
        "📊 Price Benchmarks",
        "✅ Quality Standards"
    ])
    
    # Tab 1: Create Crop Listing
    with tab1:
        render_crop_listing_form(buyer_tools)
    
    # Tab 2: View Buyer Matches
    with tab2:
        render_buyer_matches(buyer_tools)
    
    # Tab 3: Price Benchmarks
    with tab3:
        render_price_benchmarks(buyer_tools)
    
    # Tab 4: Quality Standards
    with tab4:
        render_quality_standards(buyer_tools)


def render_crop_listing_form(buyer_tools):
    """Render crop listing creation form"""
    
    st.header("List Your Crop for Sale")
    st.markdown("Create a listing to connect with verified buyers")
    
    with st.form("crop_listing_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            crop_name = st.selectbox(
                "Crop Name",
                ["wheat", "rice", "potato", "onion", "tomato", "sugarcane", "cotton", "maize"],
                help="Select the crop you want to sell"
            )
            
            quantity = st.number_input(
                "Quantity (quintal)",
                min_value=1,
                max_value=10000,
                value=100,
                help="Total quantity available for sale"
            )
            
            quality_grade = st.selectbox(
                "Quality Grade",
                ["premium", "grade_a", "grade_b", "standard"],
                help="Quality grade of your crop"
            )
        
        with col2:
            expected_price = st.number_input(
                "Expected Price (₹/quintal)",
                min_value=100,
                max_value=100000,
                value=2500,
                help="Your expected selling price"
            )
            
            harvest_date = st.date_input(
                "Harvest Date",
                value=datetime.now(),
                help="When was/will the crop be harvested"
            )
            
            available_from = st.date_input(
                "Available From",
                value=datetime.now() + timedelta(days=3),
                help="When will the crop be available for delivery"
            )
        
        st.subheader("Location Details")
        
        col3, col4 = st.columns(2)
        
        with col3:
            state = st.text_input("State", value="Uttar Pradesh")
            district = st.text_input("District", value="Ghaziabad")
        
        with col4:
            latitude = st.number_input("Latitude", value=28.6692, format="%.4f")
            longitude = st.number_input("Longitude", value=77.4538, format="%.4f")
        
        description = st.text_area(
            "Description (Optional)",
            placeholder="Describe your crop quality, farming practices, certifications, etc.",
            help="Provide additional details to attract buyers"
        )
        
        certifications = st.multiselect(
            "Certifications (Optional)",
            ["organic_certified", "fair_trade", "gmp_certified", "iso_certified"],
            help="Select any certifications you have"
        )
        
        submitted = st.form_submit_button("Create Listing", type="primary")
        
        if submitted:
            # Get farmer ID from session state
            farmer_id = st.session_state.get('user_id', 'farmer_demo')
            
            listing_data = {
                'crop_name': crop_name,
                'quantity': quantity,
                'unit': 'quintal',
                'quality_grade': quality_grade,
                'expected_price': expected_price,
                'harvest_date': harvest_date.isoformat(),
                'available_from': available_from.isoformat(),
                'location': {
                    'state': state,
                    'district': district,
                    'latitude': latitude,
                    'longitude': longitude
                },
                'description': description,
                'certifications': certifications
            }
            
            with st.spinner("Creating listing and finding buyers..."):
                result = buyer_tools.create_crop_listing(farmer_id, listing_data)
            
            if result['success']:
                st.success(f"✓ Listing created successfully! (ID: {result['listing_id']})")
                st.info(f"Found {result['potential_matches']} potential buyers")
                
                # Store listing in session state
                if 'current_listing' not in st.session_state:
                    st.session_state.current_listing = {}
                st.session_state.current_listing = result
                
                # Show top matches
                if result['matches']:
                    st.subheader("Top Matched Buyers")
                    
                    for i, match in enumerate(result['matches'][:3], 1):
                        with st.expander(f"{i}. {match['business_name']} - Match Score: {match['match_score']}"):
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                st.write(f"**Type:** {match['business_type'].title()}")
                                st.write(f"**Distance:** {match['distance_km']:.1f} km")
                                st.write(f"**Rating:** {match['ratings'].get('average', 0):.1f}/5.0")
                            
                            with col_b:
                                st.write(f"**Location:** {match['location']['district']}, {match['location']['state']}")
                                st.write(f"**Payment Terms:** {match['payment_terms'].replace('_', ' ').title()}")
                            
                            if st.button(f"Contact Buyer {i}", key=f"contact_{i}"):
                                st.info(f"Contact details will be shared after verification")
            else:
                st.error(f"Failed to create listing: {result.get('error')}")


def render_buyer_matches(buyer_tools):
    """Render buyer matches view"""
    
    st.header("Your Buyer Matches")
    
    if 'current_listing' in st.session_state and st.session_state.current_listing:
        listing = st.session_state.current_listing
        
        st.markdown(f"""
        **Listing ID:** {listing['listing_id']}  
        **Status:** {listing['status'].upper()}  
        **Potential Matches:** {listing['potential_matches']}
        """)
        
        if listing['matches']:
            st.subheader(f"Matched Buyers ({len(listing['matches'])})")
            
            for match in listing['matches']:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"### {match['business_name']}")
                        st.write(f"**Type:** {match['business_type'].title()}")
                        st.write(f"**Location:** {match['location']['district']}, {match['location']['state']}")
                    
                    with col2:
                        st.metric("Match Score", f"{match['match_score']}")
                        st.metric("Distance", f"{match['distance_km']:.1f} km")
                        st.metric("Rating", f"{match['ratings'].get('average', 0):.1f}/5")
                    
                    with col3:
                        st.write("")
                        st.write("")
                        if st.button("View Details", key=f"view_{match['buyer_id']}"):
                            st.session_state.selected_buyer = match
                            st.rerun()
                    
                    st.divider()
            
            # Show selected buyer details
            if 'selected_buyer' in st.session_state:
                buyer = st.session_state.selected_buyer
                
                st.subheader(f"Buyer Details: {buyer['business_name']}")
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.write(f"**Business Type:** {buyer['business_type'].title()}")
                    st.write(f"**Payment Terms:** {buyer['payment_terms'].replace('_', ' ').title()}")
                    st.write(f"**Distance:** {buyer['distance_km']:.1f} km from your location")
                
                with col_b:
                    st.write(f"**Rating:** {buyer['ratings'].get('average', 0):.1f}/5.0")
                    st.write(f"**Reviews:** {buyer['ratings'].get('count', 0)} reviews")
                    st.write(f"**Match Score:** {buyer['match_score']}")
                
                st.subheader("Initiate Transaction")
                
                with st.form("transaction_form"):
                    agreed_price = st.number_input(
                        "Agreed Price (₹/quintal)",
                        min_value=100,
                        value=int(listing.get('expected_price', 2500)),
                        help="Negotiated price per quintal"
                    )
                    
                    delivery_date = st.date_input(
                        "Delivery Date",
                        value=datetime.now() + timedelta(days=7)
                    )
                    
                    payment_terms = st.selectbox(
                        "Payment Terms",
                        ["on_delivery", "advance_50_percent", "advance_30_percent", "credit_15_days"]
                    )
                    
                    if st.form_submit_button("Initiate Transaction", type="primary"):
                        negotiation_data = {
                            'agreed_price': agreed_price,
                            'quantity': listing.get('quantity', 100),
                            'payment_terms': payment_terms,
                            'delivery_date': delivery_date.isoformat()
                        }
                        
                        with st.spinner("Initiating transaction..."):
                            result = buyer_tools.initiate_transaction(
                                listing['listing_id'],
                                buyer['buyer_id'],
                                negotiation_data
                            )
                        
                        if result['success']:
                            st.success(f"✓ Transaction initiated! (ID: {result['transaction_id']})")
                            st.info("Next steps:")
                            for step in result['next_steps']:
                                st.write(f"• {step}")
                        else:
                            st.error(f"Failed to initiate transaction: {result.get('error')}")
        else:
            st.info("No buyer matches found yet. Try adjusting your listing details.")
    else:
        st.info("Create a crop listing first to see buyer matches")


def render_price_benchmarks(buyer_tools):
    """Render price benchmarks view"""
    
    st.header("Price Benchmarks for Negotiation")
    st.markdown("Get current market prices to negotiate fair deals")
    
    col1, col2 = st.columns(2)
    
    with col1:
        crop_name = st.selectbox(
            "Select Crop",
            ["wheat", "rice", "potato", "onion", "tomato", "sugarcane", "cotton", "maize"],
            key="benchmark_crop"
        )
    
    with col2:
        state = st.text_input("State", value="Uttar Pradesh", key="benchmark_state")
    
    col3, col4 = st.columns(2)
    
    with col3:
        latitude = st.number_input("Latitude", value=28.6692, format="%.4f", key="benchmark_lat")
    
    with col4:
        longitude = st.number_input("Longitude", value=77.4538, format="%.4f", key="benchmark_lon")
    
    if st.button("Get Price Benchmarks", type="primary"):
        location = {
            'state': state,
            'latitude': latitude,
            'longitude': longitude
        }
        
        with st.spinner("Fetching price benchmarks..."):
            result = buyer_tools.get_price_benchmarks(crop_name, location)
        
        if result['success']:
            st.success("✓ Price benchmarks retrieved")
            
            # Display metrics
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.metric(
                    "Market Average",
                    f"₹{result['market_average']:.2f}",
                    help="Average market price"
                )
            
            with col_b:
                st.metric(
                    "Market Min",
                    f"₹{result['market_range']['min']:.2f}",
                    help="Minimum market price"
                )
            
            with col_c:
                st.metric(
                    "Market Max",
                    f"₹{result['market_range']['max']:.2f}",
                    help="Maximum market price"
                )
            
            st.subheader("Fair Price Range for Negotiation")
            
            fair_range = result['fair_price_range']
            
            st.markdown(f"""
            - **Minimum Fair Price:** ₹{fair_range['min']}/{result['unit']}
            - **Recommended Price:** ₹{fair_range['recommended']}/{result['unit']}
            - **Maximum Fair Price:** ₹{fair_range['max']}/{result['unit']}
            """)
            
            st.info(f"Last Updated: {result['last_updated']}")
            
            # Price range visualization
            import pandas as pd
            
            price_data = pd.DataFrame({
                'Price Type': ['Market Min', 'Fair Min', 'Recommended', 'Fair Max', 'Market Max'],
                'Price (₹)': [
                    result['market_range']['min'],
                    fair_range['min'],
                    fair_range['recommended'],
                    fair_range['max'],
                    result['market_range']['max']
                ]
            })
            
            st.bar_chart(price_data.set_index('Price Type'))
            
            with st.expander("🤖 AI tips to get better prices"):
                if st.button("Get AI tips", key="buyer_price_ai_btn"):
                    with st.spinner("Generating tips..."):
                        from tools.ai_insights import get_ai_insight
                        prompt = f"""You are a farm produce marketing advisor. In 2 short paragraphs, give the farmer 3-5 practical tips to get a better price when selling {crop_name}. Market average ₹{result['market_average']:.2f}, range ₹{result['market_range']['min']}-₹{result['market_range']['max']}. Recommended fair price ₹{fair_range['recommended']}. Be specific and actionable."""
                        ai = get_ai_insight(prompt)
                    if ai.get('success'):
                        st.markdown(ai.get('text', ''))
                    else:
                        st.error(ai.get('error'))
        else:
            st.error(f"Failed to fetch benchmarks: {result.get('error')}")


def render_quality_standards(buyer_tools):
    """Render quality standards view"""
    
    st.header("Quality Standards & Benchmarks")
    st.markdown("Understand quality requirements for better prices")
    
    crop_name = st.selectbox(
        "Select Crop",
        ["wheat", "rice", "potato", "onion", "tomato", "sugarcane", "cotton", "maize"],
        key="standards_crop"
    )
    
    if st.button("Get Quality Standards", type="primary"):
        with st.spinner("Fetching quality standards..."):
            result = buyer_tools.get_quality_standards(crop_name)
        
        if result['success']:
            standards = result['standards']
            
            st.success(f"✓ Quality standards for {crop_name.title()}")
            
            # Available grades
            st.subheader("Available Grades")
            grade_cols = st.columns(len(standards['grades']))
            for i, grade in enumerate(standards['grades']):
                with grade_cols[i]:
                    st.info(grade.replace('_', ' ').title())
            
            # Quality parameters
            st.subheader("Quality Parameters")
            
            params_data = []
            for param, values in standards['parameters'].items():
                param_name = param.replace('_', ' ').title()
                
                if 'max' in values:
                    value_str = f"Max {values['max']}{values.get('unit', '')}"
                elif 'min' in values:
                    value_str = f"Min {values['min']}{values.get('unit', '')}"
                elif 'requirement' in values:
                    value_str = values['requirement'].replace('_', ' ').title()
                else:
                    value_str = "N/A"
                
                params_data.append({
                    'Parameter': param_name,
                    'Requirement': value_str
                })
            
            import pandas as pd
            params_df = pd.DataFrame(params_data)
            st.table(params_df)
            
            # Premium criteria
            st.subheader("Premium Grade Criteria")
            st.markdown("Meet these criteria to achieve premium grade and higher prices:")
            
            for param, values in standards['premium_criteria'].items():
                param_name = param.replace('_', ' ').title()
                
                if 'max' in values:
                    st.write(f"✓ {param_name}: Maximum {values['max']}")
                elif 'min' in values:
                    st.write(f"✓ {param_name}: Minimum {values['min']}")
            
            st.info("💡 Tip: Premium grade crops can fetch 10-20% higher prices in the market!")
            
            with st.expander("🤖 AI tips to meet quality standards"):
                if st.button("Get AI tips", key="buyer_quality_ai_btn"):
                    with st.spinner("Generating tips..."):
                        from tools.ai_insights import get_ai_insight
                        params_str = "; ".join(f"{k}: {v}" for k, v in standards['parameters'].items())
                        prompt = f"""You are an agricultural quality advisor. For {crop_name}, the buyer quality parameters are: {params_str}. In 2 short paragraphs, give the farmer 3-5 practical, actionable tips to improve their produce to meet these standards and achieve premium grade. Be specific (e.g. storage, sorting, timing)."""
                        ai = get_ai_insight(prompt)
                    if ai.get('success'):
                        st.markdown(ai.get('text', ''))
                    else:
                        st.error(ai.get('error'))
        else:
            st.error(f"Failed to fetch standards: {result.get('error')}")


# Main function for standalone testing
if __name__ == '__main__':
    st.set_page_config(
        page_title="RISE - Buyer Connection",
        page_icon="🤝",
        layout="wide"
    )
    
    render_buyer_connection_dashboard()
