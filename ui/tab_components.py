"""
Tab-specific UI components for different features
Weather, Market, Schemes, Finance, Community tabs
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


# ============= WEATHER TAB =============

def render_weather_tab_content():
    """Render weather advisory tab with location input and forecast display"""
    st.markdown("### 🌤️ Weather Forecast & Advisory")
    
    # Location input
    col1, col2 = st.columns([3, 1])
    with col1:
        location = st.text_input(
            "Enter your location (Village, District, State)",
            placeholder="e.g., Bangalore, Karnataka",
            key="weather_location"
        )
    with col2:
        days = st.selectbox("Days", [3, 5, 7], index=1, key="weather_days")
    
    if st.button("Get Weather Forecast", type="primary"):
        if location:
            with st.spinner("Fetching weather data..."):
                # Placeholder - will integrate with agent in task 10
                display_weather_forecast(location, days)
        else:
            st.warning("Please enter a location")
    
    # Display farming activity recommendations
    st.markdown("---")
    st.markdown("### 🌾 Farming Activity Recommendations")
    
    activity = st.selectbox(
        "Select farming activity",
        ["Planting", "Spraying", "Harvesting", "Irrigation", "Fertilizing"],
        key="farming_activity"
    )
    
    crop = st.text_input("Crop type", placeholder="e.g., Rice, Wheat, Tomato", key="crop_type")
    
    if st.button("Get Activity Timing Advice"):
        if location and crop:
            st.info(f"Activity timing advice for {activity} {crop} will be integrated in task 10")


def display_weather_forecast(location: str, days: int):
    """Display weather forecast in a user-friendly format"""
    st.success(f"Weather forecast for {location}")
    
    # Mock forecast data
    forecast_data = []
    for i in range(days):
        date = datetime.now() + timedelta(days=i)
        forecast_data.append({
            "Date": date.strftime("%a, %b %d"),
            "Temp (°C)": f"{25 + i}° / {18 + i}°",
            "Rain": f"{i * 10}%",
            "Humidity": f"{60 + i * 5}%",
            "Conditions": ["Sunny", "Partly Cloudy", "Cloudy", "Rainy"][i % 4]
        })
    
    df = pd.DataFrame(forecast_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Weather alerts
    st.warning("⚠️ Heavy rain expected on Day 3. Postpone spraying activities.")


# ============= MARKET TAB =============

def render_market_tab_content():
    """Render market prices tab with comparison table and listing form"""
    st.markdown("### 💰 Market Prices & Marketplace")
    
    # Price comparison section
    st.markdown("#### 📊 Price Comparison")
    
    col1, col2 = st.columns(2)
    with col1:
        crop_query = st.text_input("Crop name", placeholder="e.g., Tomato", key="market_crop")
    with col2:
        radius = st.slider("Search radius (km)", 10, 100, 50, key="market_radius")
    
    if st.button("Search Prices", type="primary"):
        if crop_query:
            display_market_prices(crop_query, radius)
        else:
            st.warning("Please enter a crop name")
    
    # Create listing section
    st.markdown("---")
    st.markdown("#### 📝 Create Listing")
    
    listing_type = st.radio("Listing type", ["Sell Produce", "Buy Inputs"], horizontal=True)
    
    if listing_type == "Sell Produce":
        render_sell_listing_form()
    else:
        render_buy_listing_form()


def display_market_prices(crop: str, radius: int):
    """Display market price comparison table"""
    st.success(f"Prices for {crop} within {radius}km")
    
    # Mock price data
    price_data = [
        {"Market": "APMC Bangalore", "Distance": "15 km", "Price/kg": "₹45", "Quality": "Grade A", "Updated": "2 hours ago"},
        {"Market": "Mandi Mysore", "Distance": "35 km", "Price/kg": "₹42", "Quality": "Grade A", "Updated": "5 hours ago"},
        {"Market": "Local Market", "Distance": "5 km", "Price/kg": "₹38", "Quality": "Grade B", "Updated": "1 hour ago"},
    ]
    
    df = pd.DataFrame(price_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.info("💡 Best price: APMC Bangalore at ₹45/kg")


def render_sell_listing_form():
    """Render form to create a sell listing"""
    with st.form("sell_listing_form"):
        product = st.text_input("Product name", placeholder="e.g., Tomatoes")
        
        col1, col2 = st.columns(2)
        with col1:
            quantity = st.number_input("Quantity (kg)", min_value=1, value=100)
            quality = st.selectbox("Quality", ["Grade A", "Grade B", "Organic"])
        with col2:
            price = st.number_input("Price per kg (₹)", min_value=1, value=40)
            expiry = st.date_input("Expiry/Best before", value=datetime.now() + timedelta(days=7))
        
        sustainable = st.checkbox("Sustainable/Organic product")
        
        submitted = st.form_submit_button("Create Listing", type="primary")
        if submitted:
            st.success(f"✅ Listing created for {quantity}kg of {product} at ₹{price}/kg")


def render_buy_listing_form():
    """Render form to search for inputs to buy"""
    product_type = st.selectbox("Product type", ["Seeds", "Fertilizers", "Pesticides", "Equipment"])
    search_query = st.text_input("Search", placeholder="e.g., Organic fertilizer")
    
    if st.button("Search Products"):
        st.info("Product search will be integrated in task 10")


# ============= SCHEMES TAB =============

def render_schemes_tab_content():
    """Render government schemes tab with scheme cards and eligibility checker"""
    st.markdown("### 📋 Government Schemes")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox(
            "Category",
            ["All", "Subsidy", "Insurance", "Loan", "Training"],
            key="scheme_category"
        )
    with col2:
        state = st.selectbox(
            "State",
            ["All", "Karnataka", "Maharashtra", "Tamil Nadu", "Andhra Pradesh"],
            key="scheme_state"
        )
    
    if st.button("Search Schemes", type="primary"):
        display_scheme_cards(category, state)
    
    # Eligibility checker
    st.markdown("---")
    st.markdown("### ✅ Check Eligibility")
    
    with st.expander("Enter your details"):
        render_eligibility_form()


def display_scheme_cards(category: str, state: str):
    """Display government scheme cards"""
    st.markdown("#### Available Schemes")
    
    # Mock scheme data
    schemes = [
        {
            "name": "PM-KISAN",
            "level": "Central",
            "category": "Subsidy",
            "benefit": "₹6,000 per year in 3 installments",
            "eligibility": "All landholding farmers"
        },
        {
            "name": "Crop Insurance Scheme",
            "level": "Central",
            "category": "Insurance",
            "benefit": "Crop loss coverage up to 90%",
            "eligibility": "Farmers with crop loans"
        },
        {
            "name": "Soil Health Card Scheme",
            "level": "Central",
            "category": "Subsidy",
            "benefit": "Free soil testing and recommendations",
            "eligibility": "All farmers"
        }
    ]
    
    for scheme in schemes:
        render_scheme_card(scheme)


def render_scheme_card(scheme: Dict[str, str]):
    """Render a single scheme card"""
    st.markdown(f"""
    <div class="info-card">
        <h3>{scheme['name']}</h3>
        <p><strong>Level:</strong> {scheme['level']} | <strong>Category:</strong> {scheme['category']}</p>
        <p><strong>Benefit:</strong> {scheme['benefit']}</p>
        <p><strong>Eligibility:</strong> {scheme['eligibility']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"View Details", key=f"details_{scheme['name']}"):
            st.info("Detailed information will be shown in task 10")
    with col2:
        if st.button(f"Check Eligibility", key=f"check_{scheme['name']}"):
            st.info("Eligibility check will be integrated in task 10")


def render_eligibility_form():
    """Render eligibility checker form"""
    land_size = st.number_input("Land size (acres)", min_value=0.0, value=2.0, step=0.5)
    annual_income = st.number_input("Annual income (₹)", min_value=0, value=100000, step=10000)
    crop_types = st.multiselect("Crops grown", ["Rice", "Wheat", "Cotton", "Sugarcane", "Vegetables"])
    
    if st.button("Check My Eligibility"):
        st.success("You are eligible for 3 schemes. Details will be shown in task 10.")


# ============= FINANCE TAB =============

def render_finance_tab_content():
    """Render financial calculator tab with forms and visualizations"""
    st.markdown("### 💵 Financial Calculator")
    
    calc_type = st.radio(
        "Select calculation type",
        ["Profit/Loss", "Cost Estimation", "Crop Comparison"],
        horizontal=True
    )
    
    if calc_type == "Profit/Loss":
        render_profit_calculator()
    elif calc_type == "Cost Estimation":
        render_cost_estimator()
    else:
        render_crop_comparison()


def render_profit_calculator():
    """Render profit/loss calculator"""
    st.markdown("#### 📊 Profit/Loss Calculator")
    
    with st.form("profit_form"):
        crop = st.text_input("Crop name", placeholder="e.g., Rice")
        area = st.number_input("Area (acres)", min_value=0.1, value=2.0, step=0.1)
        
        st.markdown("**Costs**")
        col1, col2 = st.columns(2)
        with col1:
            seeds = st.number_input("Seeds (₹)", min_value=0, value=5000)
            fertilizers = st.number_input("Fertilizers (₹)", min_value=0, value=8000)
            pesticides = st.number_input("Pesticides (₹)", min_value=0, value=3000)
        with col2:
            labor = st.number_input("Labor (₹)", min_value=0, value=15000)
            water = st.number_input("Water/Irrigation (₹)", min_value=0, value=4000)
            other = st.number_input("Other costs (₹)", min_value=0, value=2000)
        
        st.markdown("**Revenue**")
        col3, col4 = st.columns(2)
        with col3:
            yield_kg = st.number_input("Expected yield (kg)", min_value=0, value=2000)
        with col4:
            price_per_kg = st.number_input("Selling price (₹/kg)", min_value=0.0, value=25.0, step=0.5)
        
        submitted = st.form_submit_button("Calculate", type="primary")
        if submitted:
            display_profit_results(seeds + fertilizers + pesticides + labor + water + other, yield_kg * price_per_kg)


def display_profit_results(total_costs: float, total_revenue: float):
    """Display profit calculation results"""
    profit = total_revenue - total_costs
    roi = (profit / total_costs * 100) if total_costs > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Costs", f"₹{total_costs:,.0f}")
    with col2:
        st.metric("Total Revenue", f"₹{total_revenue:,.0f}")
    with col3:
        st.metric("Profit/Loss", f"₹{profit:,.0f}", delta=f"{roi:.1f}% ROI")
    
    if profit > 0:
        st.success(f"✅ Profitable! Expected profit: ₹{profit:,.0f}")
    else:
        st.error(f"⚠️ Loss expected: ₹{abs(profit):,.0f}")


def render_cost_estimator():
    """Render cost estimation tool"""
    st.markdown("#### 💰 Cost Estimation")
    st.info("Cost estimation form will be similar to profit calculator")


def render_crop_comparison():
    """Render crop comparison tool"""
    st.markdown("#### 🔄 Crop Comparison")
    
    num_crops = st.slider("Number of crops to compare", 2, 4, 2)
    
    st.info(f"Comparison form for {num_crops} crops will be implemented")


# ============= COMMUNITY TAB =============

def render_community_tab_content():
    """Render community forum tab with search and post display"""
    st.markdown("### 👥 Community Forum")
    
    # Search section
    st.markdown("#### 🔍 Search Forum")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("Search discussions", placeholder="e.g., tomato disease", key="forum_search")
    with col2:
        topic = st.selectbox("Topic", ["All", "Disease", "Weather", "Market", "Technique"], key="forum_topic")
    
    if st.button("Search", type="primary"):
        if search_query:
            display_forum_posts(search_query, topic)
        else:
            st.warning("Please enter a search query")
    
    # Post experience section
    st.markdown("---")
    st.markdown("#### ✍️ Share Your Experience")
    
    with st.expander("Create a post"):
        render_forum_post_form()


def display_forum_posts(query: str, topic: str):
    """Display forum posts matching search"""
    st.markdown(f"#### Results for '{query}'")
    
    # Mock forum posts
    posts = [
        {
            "title": "Tomato leaf curl - organic solution",
            "author": "Farmer Kumar",
            "location": "Bangalore",
            "date": "2 days ago",
            "content": "I used neem oil spray and it worked well...",
            "helpful": 15
        },
        {
            "title": "Best time for tomato planting",
            "author": "Farmer Lakshmi",
            "location": "Mysore",
            "date": "1 week ago",
            "content": "In our region, October-November is ideal...",
            "helpful": 23
        }
    ]
    
    for post in posts:
        render_forum_post(post)


def render_forum_post(post: Dict[str, Any]):
    """Render a single forum post"""
    st.markdown(f"""
    <div class="info-card">
        <h4>{post['title']}</h4>
        <p><small>By {post['author']} from {post['location']} • {post['date']}</small></p>
        <p>{post['content']}</p>
        <p><small>👍 {post['helpful']} people found this helpful</small></p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("👍 Helpful", key=f"helpful_{post['title']}"):
            st.success("Marked as helpful!")


def render_forum_post_form():
    """Render form to create a forum post"""
    topic = st.selectbox("Topic", ["Disease", "Weather", "Market", "Technique", "Other"])
    title = st.text_input("Title", placeholder="Brief description of your question/experience")
    content = st.text_area("Content", placeholder="Share your experience or ask a question...", height=150)
    
    if st.button("Post to Forum", type="primary"):
        if title and content:
            st.success("✅ Your post has been shared with the community!")
        else:
            st.warning("Please fill in all fields")
