"""
RISE Market Price Dashboard UI Component
Streamlit component for displaying market prices and trends
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd


def render_market_price_dashboard(market_tools, user_location: Dict[str, float]):
    """
    Render market price dashboard in Streamlit
    
    Args:
        market_tools: MarketPriceTools instance
        user_location: Dict with 'latitude' and 'longitude'
    """
    st.header("📊 Market Price Intelligence")
    
    # Crop selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        crop_name = st.text_input(
            "Enter Crop Name",
            placeholder="e.g., wheat, rice, tomato",
            help="Enter the name of the crop to check market prices"
        )
    
    with col2:
        radius_km = st.slider(
            "Search Radius (km)",
            min_value=10,
            max_value=100,
            value=50,
            step=10
        )
    
    if crop_name:
        # Fetch current prices
        with st.spinner("Fetching market prices..."):
            result = market_tools.get_current_prices(
                crop_name,
                user_location['latitude'],
                user_location['longitude'],
                radius_km
            )
        
        if result['success']:
            render_current_prices(result)
            
            # Market selection for detailed analysis
            if result['markets']:
                st.subheader("📈 Detailed Market Analysis")
                
                market_options = {
                    f"{m['market_name']} (₹{m['price']}/quintal)": m['market_id']
                    for m in result['markets']
                }
                
                selected_market_name = st.selectbox(
                    "Select Market for Detailed Analysis",
                    options=list(market_options.keys())
                )
                
                selected_market_id = market_options[selected_market_name]
                
                # Tabs for different analyses
                tab1, tab2, tab3 = st.tabs(["📊 Price History", "🔮 Price Predictions", "💡 Selling Advice"])
                
                with tab1:
                    render_price_history(market_tools, crop_name, selected_market_id)
                
                with tab2:
                    render_price_predictions(market_tools, crop_name, selected_market_id)
                
                with tab3:
                    render_selling_advice(market_tools, crop_name, user_location)
        else:
            st.error(f"❌ {result.get('error', 'Failed to fetch market prices')}")
    else:
        # Show placeholder
        st.info("👆 Enter a crop name to view market prices and trends")
        
        # Show example crops
        st.markdown("### Popular Crops")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🌾 Wheat"):
                st.session_state['selected_crop'] = 'wheat'
                st.rerun()
        
        with col2:
            if st.button("🍚 Rice"):
                st.session_state['selected_crop'] = 'rice'
                st.rerun()
        
        with col3:
            if st.button("🍅 Tomato"):
                st.session_state['selected_crop'] = 'tomato'
                st.rerun()


def render_current_prices(result: Dict[str, Any]):
    """Render current market prices section"""
    
    st.subheader(f"Current Prices for {result['crop_name'].title()}")
    
    # Statistics cards
    col1, col2, col3, col4 = st.columns(4)
    
    stats = result['statistics']
    
    with col1:
        st.metric(
            "Average Price",
            f"₹{stats['avg_price']:.2f}",
            help="Average price across all markets"
        )
    
    with col2:
        st.metric(
            "Minimum Price",
            f"₹{stats['min_price']:.2f}",
            help="Lowest price found"
        )
    
    with col3:
        st.metric(
            "Maximum Price",
            f"₹{stats['max_price']:.2f}",
            help="Highest price found"
        )
    
    with col4:
        st.metric(
            "Markets Found",
            stats['market_count'],
            help=f"Within {result['location']['radius_km']}km radius"
        )
    
    # Price range indicator
    price_range = stats['max_price'] - stats['min_price']
    price_variation = (price_range / stats['avg_price']) * 100
    
    if price_variation > 15:
        st.warning(f"⚠️ High price variation ({price_variation:.1f}%) across markets. Consider selling at higher-priced markets.")
    elif price_variation > 5:
        st.info(f"ℹ️ Moderate price variation ({price_variation:.1f}%) across markets.")
    else:
        st.success(f"✅ Low price variation ({price_variation:.1f}%) - prices are stable across markets.")
    
    # Markets table
    st.markdown("### 🏪 Nearby Markets")
    
    markets_df = pd.DataFrame([
        {
            'Market Name': m['market_name'],
            'Price (₹/quintal)': m['price'],
            'Distance (km)': m['distance_km'],
            'District': m['location']['district'],
            'State': m['location']['state'],
            'Arrival (quintals)': m.get('arrival_quantity', 'N/A')
        }
        for m in result['markets']
    ])
    
    # Sort by price (descending)
    markets_df = markets_df.sort_values('Price (₹/quintal)', ascending=False)
    
    # Highlight best price
    st.dataframe(
        markets_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Price comparison chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=[m['market_name'] for m in result['markets']],
        y=[m['price'] for m in result['markets']],
        marker_color=['#2ecc71' if m['price'] == stats['max_price'] else '#3498db' for m in result['markets']],
        text=[f"₹{m['price']}" for m in result['markets']],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Price Comparison Across Markets",
        xaxis_title="Market",
        yaxis_title="Price (₹/quintal)",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_price_history(market_tools, crop_name: str, market_id: str):
    """Render price history section"""
    
    days = st.slider("Historical Period (days)", min_value=7, max_value=90, value=30, step=7)
    
    with st.spinner("Loading price history..."):
        result = market_tools.get_price_history(crop_name, market_id, days)
    
    if result['success']:
        history = result['history']
        trends = result['trends']
        
        # Trend indicator
        col1, col2, col3 = st.columns(3)
        
        with col1:
            trend_emoji = "📈" if trends['trend'] == 'increasing' else "📉" if trends['trend'] == 'decreasing' else "➡️"
            st.metric(
                "Price Trend",
                f"{trend_emoji} {trends['trend'].title()}",
                f"{trends['change_percent']:+.2f}%"
            )
        
        with col2:
            st.metric(
                "Average Price",
                f"₹{trends['avg_price']:.2f}",
                help=f"Over last {days} days"
            )
        
        with col3:
            volatility_level = "High" if trends['volatility'] > 100 else "Medium" if trends['volatility'] > 50 else "Low"
            st.metric(
                "Volatility",
                volatility_level,
                f"±₹{trends['volatility']:.2f}"
            )
        
        # Price history chart
        df = pd.DataFrame(history)
        df['date'] = pd.to_datetime(df['date'])
        
        fig = go.Figure()
        
        # Price line
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['price'],
            mode='lines+markers',
            name='Price',
            line=dict(color='#3498db', width=2),
            marker=dict(size=6)
        ))
        
        # Average line
        fig.add_hline(
            y=trends['avg_price'],
            line_dash="dash",
            line_color="orange",
            annotation_text=f"Average: ₹{trends['avg_price']:.2f}",
            annotation_position="right"
        )
        
        fig.update_layout(
            title=f"Price History - Last {days} Days",
            xaxis_title="Date",
            yaxis_title="Price (₹/quintal)",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        st.markdown("### 💡 Insights")
        
        if trends['trend'] == 'increasing':
            st.success(f"✅ Prices have increased by {trends['change_percent']:.1f}% over the last {days} days. Good time to sell if you have stock.")
        elif trends['trend'] == 'decreasing':
            st.warning(f"⚠️ Prices have decreased by {abs(trends['change_percent']):.1f}% over the last {days} days. Consider waiting if possible.")
        else:
            st.info(f"ℹ️ Prices have been stable over the last {days} days. Market conditions are predictable.")
        
        if trends['volatility'] > 100:
            st.warning("⚠️ High price volatility detected. Market is unpredictable - consider selling soon to avoid risk.")
    
    else:
        st.error(f"❌ {result.get('error', 'Failed to fetch price history')}")


def render_price_predictions(market_tools, crop_name: str, market_id: str):
    """Render price predictions section"""
    
    forecast_days = st.slider("Forecast Period (days)", min_value=3, max_value=14, value=7, step=1)
    
    with st.spinner("Generating price predictions..."):
        result = market_tools.predict_price_trends(crop_name, market_id, forecast_days)
    
    if result['success']:
        predictions = result['predictions']
        
        st.info(f"🔮 Predictions based on {result['method'].replace('_', ' ').title()} method with {result['confidence']} confidence")
        
        # Predictions chart
        df = pd.DataFrame(predictions)
        df['date'] = pd.to_datetime(df['date'])
        
        fig = go.Figure()
        
        # Predicted price line
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['predicted_price'],
            mode='lines+markers',
            name='Predicted Price',
            line=dict(color='#9b59b6', width=2),
            marker=dict(size=8)
        ))
        
        # Confidence range
        fig.add_trace(go.Scatter(
            x=df['date'].tolist() + df['date'].tolist()[::-1],
            y=df['confidence_range'].apply(lambda x: x['high']).tolist() + 
              df['confidence_range'].apply(lambda x: x['low']).tolist()[::-1],
            fill='toself',
            fillcolor='rgba(155, 89, 182, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Confidence Range',
            showlegend=True
        ))
        
        fig.update_layout(
            title=f"Price Predictions - Next {forecast_days} Days",
            xaxis_title="Date",
            yaxis_title="Price (₹/quintal)",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Predictions table
        st.markdown("### 📅 Detailed Predictions")
        
        pred_df = pd.DataFrame([
            {
                'Date': datetime.fromisoformat(p['date']).strftime('%Y-%m-%d'),
                'Predicted Price': f"₹{p['predicted_price']:.2f}",
                'Low Estimate': f"₹{p['confidence_range']['low']:.2f}",
                'High Estimate': f"₹{p['confidence_range']['high']:.2f}"
            }
            for p in predictions
        ])
        
        st.dataframe(pred_df, use_container_width=True, hide_index=True)
        
        # Best day to sell
        best_day = max(predictions, key=lambda p: p['predicted_price'])
        best_date = datetime.fromisoformat(best_day['date']).strftime('%B %d, %Y')
        
        st.success(f"🎯 Best predicted price: ₹{best_day['predicted_price']:.2f} on {best_date}")
    
    else:
        st.error(f"❌ {result.get('error', 'Failed to generate predictions')}")


def render_selling_advice(market_tools, crop_name: str, user_location: Dict[str, float]):
    """Render selling advice section with enhanced selling time calculator"""
    
    st.markdown("### 🎯 Optimal Selling Time Calculator")
    
    # Import selling time tools
    try:
        from tools.selling_time_tools import create_selling_time_tools
        selling_tools = create_selling_time_tools()
    except ImportError:
        st.error("Selling time tools not available")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        storage_capacity = st.radio(
            "Do you have storage capacity?",
            options=["Yes", "No"],
            help="Storage capacity affects optimal selling time"
        )
    
    with col2:
        storage_type = st.selectbox(
            "Storage Type",
            options=["standard", "cold", "warehouse"],
            help="Type of storage available"
        )
    
    with col3:
        quantity_quintals = st.number_input(
            "Quantity (quintals)",
            min_value=1,
            max_value=10000,
            value=100,
            help="Quantity to sell"
        )
    
    if st.button("Calculate Optimal Selling Time", type="primary"):
        with st.spinner("Calculating optimal selling time..."):
            # Get current prices
            price_result = market_tools.get_current_prices(
                crop_name,
                user_location['latitude'],
                user_location['longitude']
            )
            
            if not price_result['success']:
                st.error(f"Failed to fetch prices: {price_result.get('error')}")
                return
            
            # Get best market
            best_market = max(price_result['markets'], key=lambda m: m['price'])
            current_price = best_market['price']
            
            # Get price predictions
            predictions_result = market_tools.predict_price_trends(
                crop_name,
                best_market['market_id'],
                14
            )
            
            predicted_prices = predictions_result.get('predictions', []) if predictions_result['success'] else []
            
            # Calculate optimal selling time
            result = selling_tools.calculate_optimal_selling_time(
                crop_name=crop_name,
                current_price=current_price,
                predicted_prices=predicted_prices,
                quantity_quintals=quantity_quintals,
                storage_capacity=(storage_capacity == "Yes"),
                storage_type=storage_type
            )
        
        if result['success']:
            rec = result['recommendation']
            
            # Recommendation card
            st.markdown("---")
            st.markdown("### 💡 Recommendation")
            
            timing_display = rec['timing'].replace('_', ' ').title()
            
            if rec['timing'] == 'immediate':
                st.warning(f"⏰ **{timing_display}**")
            else:
                st.success(f"⏰ **{timing_display}**")
            
            st.markdown(f"**Reason:** {rec['reason']}")
            
            # Financial metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Expected Price",
                    f"₹{rec['expected_price']:.2f}",
                    help="Price per quintal"
                )
            
            with col2:
                st.metric(
                    "Expected Revenue",
                    f"₹{rec['expected_revenue']:,.0f}",
                    help="Total revenue"
                )
            
            with col3:
                st.metric(
                    "Storage Cost",
                    f"₹{rec['storage_cost']:,.0f}",
                    help="Total storage cost"
                )
            
            with col4:
                st.metric(
                    "Net Profit",
                    f"₹{rec['net_profit']:,.0f}",
                    f"+{rec['improvement_percent']:.1f}%",
                    help="Profit after costs"
                )
            
            # Scenario comparison chart
            if 'scenarios' in result and len(result['scenarios']) > 1:
                st.markdown("### 📊 Scenario Analysis")
                
                scenarios_df = pd.DataFrame(result['scenarios'])
                
                fig = go.Figure()
                
                # Net profit line
                fig.add_trace(go.Scatter(
                    x=scenarios_df['days'],
                    y=scenarios_df['net_profit'],
                    mode='lines+markers',
                    name='Net Profit',
                    line=dict(color='#2ecc71', width=3),
                    marker=dict(size=8)
                ))
                
                # Mark optimal point
                optimal_idx = scenarios_df['net_profit'].idxmax()
                fig.add_trace(go.Scatter(
                    x=[scenarios_df.loc[optimal_idx, 'days']],
                    y=[scenarios_df.loc[optimal_idx, 'net_profit']],
                    mode='markers',
                    name='Optimal',
                    marker=dict(size=15, color='gold', symbol='star')
                ))
                
                fig.update_layout(
                    title="Net Profit by Waiting Days",
                    xaxis_title="Days to Wait",
                    yaxis_title="Net Profit (₹)",
                    height=400,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Perishability info
            perish = result['perishability']
            st.markdown("### 📦 Crop Storage Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                category_emoji = "🔴" if perish['category'] == 'highly_perishable' else "🟡" if perish['category'] == 'moderately_perishable' else "🟢"
                
                st.markdown(f"""
                {category_emoji} **{perish['category'].replace('_', ' ').title()}**
                - Shelf Life: {perish['shelf_life_days']} days
                - Quality Degradation: {perish['quality_degradation_rate']*100:.1f}% per day
                - Storage Temp: {perish['optimal_storage_temp']}
                """)
            
            with col2:
                st.markdown(f"""
                **Storage Requirements:**
                {perish['storage_requirements']}
                
                **Post-Harvest Loss Rate:**
                {perish['post_harvest_loss_rate']*100:.0f}%
                """)
            
            # Price alert section
            st.markdown("### 🔔 Set Price Alert")
            
            col1, col2 = st.columns(2)
            
            with col1:
                target_price = st.number_input(
                    "Target Price (₹/quintal)",
                    min_value=0.0,
                    value=float(rec['expected_price']),
                    step=10.0
                )
            
            with col2:
                phone_number = st.text_input(
                    "Phone Number (optional)",
                    placeholder="+919876543210"
                )
            
            if st.button("Create Price Alert"):
                alert_result = selling_tools.create_price_alert(
                    user_id=st.session_state.get('user_id', 'default_user'),
                    crop_name=crop_name,
                    target_price=target_price,
                    market_id=best_market['market_id'],
                    phone_number=phone_number if phone_number else None
                )
                
                if alert_result['success']:
                    st.success(f"✓ {alert_result['message']}")
                else:
                    st.error(f"Failed to create alert: {alert_result.get('error')}")
        
        else:
            st.error(f"❌ {result.get('error', 'Failed to calculate optimal selling time')}")


def render_market_price_widget(market_tools, crop_name: str, user_location: Dict[str, float]):
    """
    Render compact market price widget for sidebar or dashboard
    
    Args:
        market_tools: MarketPriceTools instance
        crop_name: Name of the crop
        user_location: Dict with 'latitude' and 'longitude'
    """
    with st.spinner("Loading prices..."):
        result = market_tools.get_current_prices(
            crop_name,
            user_location['latitude'],
            user_location['longitude'],
            50
        )
    
    if result['success']:
        stats = result['statistics']
        
        st.metric(
            f"{crop_name.title()} Price",
            f"₹{stats['avg_price']:.2f}",
            help=f"Average across {stats['market_count']} markets"
        )
        
        st.caption(f"Range: ₹{stats['min_price']} - ₹{stats['max_price']}")
    else:
        st.error("Failed to load prices")
