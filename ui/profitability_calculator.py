"""
RISE Crop Profitability Calculator UI
Streamlit component for comparing crop profitability
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.profitability_calculator_tools import ProfitabilityCalculatorTools
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def render_profitability_calculator():
    """Render the crop profitability calculator UI"""
    
    st.title("🌾 Crop Profitability Calculator")
    st.markdown("Calculate and compare potential profits for different crops")
    
    # Initialize tools
    if 'profitability_tools' not in st.session_state:
        st.session_state.profitability_tools = ProfitabilityCalculatorTools()
    
    tools = st.session_state.profitability_tools
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("Farm Details")
        
        farm_size = st.number_input(
            "Farm Size (acres)",
            min_value=0.5,
            max_value=1000.0,
            value=5.0,
            step=0.5
        )
        
        st.subheader("Location")
        state = st.selectbox(
            "State",
            ["Punjab", "Haryana", "Uttar Pradesh", "Bihar", "Maharashtra", 
             "Karnataka", "Tamil Nadu", "Gujarat", "Rajasthan", "Madhya Pradesh"]
        )
        
        district = st.text_input("District", "Ludhiana")
        
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.number_input("Latitude", value=30.9010, format="%.4f")
        with col2:
            longitude = st.number_input("Longitude", value=75.8573, format="%.4f")
        
        soil_type = st.selectbox(
            "Soil Type",
            ["Loamy", "Clay", "Sandy", "Black", "Red", "Alluvial", "Laterite"]
        )
        
        season = st.selectbox(
            "Season",
            ["Kharif (Monsoon)", "Rabi (Winter)", "Zaid (Summer)", "Perennial"],
            index=1
        )
        
        season_map = {
            "Kharif (Monsoon)": "kharif",
            "Rabi (Winter)": "rabi",
            "Zaid (Summer)": "zaid",
            "Perennial": "perennial"
        }
        season_value = season_map[season]
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["Single Crop Analysis", "Compare Crops", "Cost Estimator"])
    
    # Tab 1: Single Crop Analysis
    with tab1:
        st.header("Detailed Profitability Analysis")
        
        crop_name = st.text_input("Crop Name", "wheat", key="single_crop")
        
        if st.button("Calculate Profitability", key="calc_single"):
            with st.spinner("Analyzing profitability..."):
                location = {
                    'state': state,
                    'district': district,
                    'latitude': latitude,
                    'longitude': longitude
                }
                
                result = tools.calculate_comprehensive_profitability(
                    crop_name=crop_name,
                    farm_size_acres=farm_size,
                    location=location,
                    soil_type=soil_type.lower(),
                    season=season_value
                )
                
                if result['success']:
                    st.session_state.single_result = result
                else:
                    st.error(f"Error: {result.get('error')}")
        
        # Display results
        if 'single_result' in st.session_state:
            result = st.session_state.single_result
            
            # Key metrics
            st.subheader("📊 Key Metrics")
            col1, col2, col3, col4 = st.columns(4)
            
            avg_scenario = result['profitability_scenarios']['average']
            
            with col1:
                st.metric(
                    "Total Investment",
                    f"₹{avg_scenario['total_cost']:,.0f}"
                )
            
            with col2:
                st.metric(
                    "Expected Revenue",
                    f"₹{avg_scenario['total_revenue']:,.0f}"
                )
            
            with col3:
                st.metric(
                    "Net Profit",
                    f"₹{avg_scenario['net_profit']:,.0f}",
                    delta=f"{avg_scenario['roi_percent']:.1f}% ROI"
                )
            
            with col4:
                risk_color = {
                    'low': '🟢',
                    'medium': '🟡',
                    'high': '🔴'
                }
                risk_level = result['risk_assessment']['overall_risk_level']
                st.metric(
                    "Risk Level",
                    f"{risk_color.get(risk_level, '⚪')} {risk_level.upper()}"
                )
            
            # Scenario comparison chart
            st.subheader("💰 Profit Scenarios")
            scenarios = result['profitability_scenarios']
            
            scenario_df = pd.DataFrame({
                'Scenario': ['Conservative', 'Average', 'Optimistic'],
                'Net Profit': [
                    scenarios['conservative']['net_profit'],
                    scenarios['average']['net_profit'],
                    scenarios['optimistic']['net_profit']
                ],
                'ROI %': [
                    scenarios['conservative']['roi_percent'],
                    scenarios['average']['roi_percent'],
                    scenarios['optimistic']['roi_percent']
                ]
            })
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=scenario_df['Scenario'],
                y=scenario_df['Net Profit'],
                text=[f"₹{v:,.0f}" for v in scenario_df['Net Profit']],
                textposition='auto',
                marker_color=['#ff6b6b', '#4ecdc4', '#95e1d3']
            ))
            fig.update_layout(
                title="Profit Scenarios",
                xaxis_title="Scenario",
                yaxis_title="Net Profit (₹)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Cost breakdown
            st.subheader("💵 Cost Breakdown")
            cost_categories = result['cost_breakdown']['cost_categories']
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=list(cost_categories.keys()),
                values=list(cost_categories.values()),
                hole=.3
            )])
            fig_pie.update_layout(title="Cost Distribution", height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Detailed costs
            with st.expander("View Detailed Cost Breakdown"):
                costs_df = pd.DataFrame([
                    {'Category': k.replace('_', ' ').title(), 'Cost (₹)': v}
                    for k, v in result['cost_breakdown']['costs_per_acre'].items()
                ])
                st.dataframe(costs_df, use_container_width=True)
            
            # Risk assessment
            st.subheader("⚠️ Risk Assessment")
            risk_data = result['risk_assessment']
            
            for factor in risk_data['risk_factors']:
                risk_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}
                st.markdown(f"""
                **{factor['factor'].replace('_', ' ').title()}** {risk_emoji.get(factor['risk_level'], '⚪')}
                - {factor['description']}
                - *Mitigation:* {factor['mitigation']}
                """)
            
            st.info(f"**Recommendation:** {risk_data['recommendation']}")
            
            # AI analysis
            if st.button("🤖 Get AI Insights", key="ai_insights_single"):
                with st.spinner("Generating AI analysis..."):
                    ai_result = tools.get_ai_profitability_analysis(result)
                if ai_result.get('success'):
                    st.subheader("🤖 AI Insights")
                    st.markdown(ai_result.get('analysis', ''))
                else:
                    st.error(ai_result.get('error', 'Could not generate AI insights'))
            
            # Projections
            st.subheader("📈 Profit Projections")
            projections = result['projections']
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Expected Profit (Risk-Adjusted)",
                    f"₹{projections['expected_profit']:,.0f}"
                )
                st.metric(
                    "Break-even Price",
                    f"₹{projections['break_even_price']:,.2f}/quintal"
                )
            
            with col2:
                st.metric(
                    "Break-even Yield",
                    f"{projections['break_even_yield']:,.2f} quintals"
                )

    
    # Tab 2: Compare Crops
    with tab2:
        st.header("Compare Crop Profitability")
        
        st.markdown("Select multiple crops to compare their profitability")
        
        available_crops = [
            "Wheat", "Rice", "Maize", "Cotton", "Sugarcane",
            "Potato", "Tomato", "Onion", "Soybean", "Groundnut"
        ]
        
        selected_crops = st.multiselect(
            "Select Crops to Compare (2-5 crops)",
            available_crops,
            default=["Wheat", "Rice"]
        )
        
        if st.button("Compare Crops", key="compare_btn"):
            if len(selected_crops) < 2:
                st.warning("Please select at least 2 crops to compare")
            elif len(selected_crops) > 5:
                st.warning("Please select maximum 5 crops to compare")
            else:
                with st.spinner("Comparing crops..."):
                    location = {
                        'state': state,
                        'district': district,
                        'latitude': latitude,
                        'longitude': longitude
                    }
                    
                    crop_list = [c.lower() for c in selected_crops]
                    
                    result = tools.compare_crop_profitability(
                        crop_list=crop_list,
                        farm_size_acres=farm_size,
                        location=location,
                        soil_type=soil_type.lower(),
                        season=season_value
                    )
                    
                    if result['success']:
                        st.session_state.comparison_result = result
                    else:
                        st.error(f"Error: {result.get('error')}")
        
        # Display comparison results
        if 'comparison_result' in st.session_state:
            result = st.session_state.comparison_result
            
            st.subheader("🏆 Rankings")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**By Profit**")
                for i, crop in enumerate(result['rankings']['by_profit'], 1):
                    st.write(f"{i}. {crop.title()}")
            
            with col2:
                st.markdown("**By ROI**")
                for i, crop in enumerate(result['rankings']['by_roi'], 1):
                    st.write(f"{i}. {crop.title()}")
            
            with col3:
                st.markdown("**By Low Risk**")
                for i, crop in enumerate(result['rankings']['by_low_risk'], 1):
                    st.write(f"{i}. {crop.title()}")
            
            st.success(f"**Best Overall Choice:** {result['best_overall'].title()}")
            
            # Comparison chart
            st.subheader("📊 Profitability Comparison")
            
            comp_df = pd.DataFrame(result['comparisons'])
            comp_df['crop_name'] = comp_df['crop_name'].str.title()
            
            # Profit comparison
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=comp_df['crop_name'],
                y=comp_df['average_profit'],
                text=[f"₹{v:,.0f}" for v in comp_df['average_profit']],
                textposition='auto',
                name='Net Profit',
                marker_color='#4ecdc4'
            ))
            fig.update_layout(
                title="Net Profit Comparison",
                xaxis_title="Crop",
                yaxis_title="Net Profit (₹)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # ROI comparison
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=comp_df['crop_name'],
                y=comp_df['roi'],
                text=[f"{v:.1f}%" for v in comp_df['roi']],
                textposition='auto',
                name='ROI',
                marker_color='#95e1d3'
            ))
            fig2.update_layout(
                title="Return on Investment (ROI) Comparison",
                xaxis_title="Crop",
                yaxis_title="ROI (%)",
                height=400
            )
            st.plotly_chart(fig2, use_container_width=True)
            
            # Detailed comparison table
            st.subheader("📋 Detailed Comparison")
            
            display_df = comp_df[[
                'crop_name', 'total_cost', 'average_yield', 
                'market_price', 'average_revenue', 'average_profit', 'roi'
            ]].copy()
            
            display_df.columns = [
                'Crop', 'Total Cost (₹)', 'Yield (quintals)', 
                'Price (₹/quintal)', 'Revenue (₹)', 'Profit (₹)', 'ROI (%)'
            ]
            
            # Format numbers
            for col in ['Total Cost (₹)', 'Revenue (₹)', 'Profit (₹)']:
                display_df[col] = display_df[col].apply(lambda x: f"₹{x:,.0f}")
            
            display_df['Yield (quintals)'] = display_df['Yield (quintals)'].apply(lambda x: f"{x:.2f}")
            display_df['Price (₹/quintal)'] = display_df['Price (₹/quintal)'].apply(lambda x: f"₹{x:,.0f}")
            display_df['ROI (%)'] = display_df['ROI (%)'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(display_df, use_container_width=True)
            
            # Risk comparison
            st.subheader("⚠️ Risk Comparison")
            
            risk_df = comp_df[['crop_name', 'risk_score']].copy()
            risk_df.columns = ['Crop', 'Risk Score']
            
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                x=risk_df['Crop'],
                y=risk_df['Risk Score'],
                text=[f"{v:.1f}" for v in risk_df['Risk Score']],
                textposition='auto',
                marker_color=['#95e1d3' if v < 5 else '#ffd93d' if v < 7 else '#ff6b6b' 
                             for v in risk_df['Risk Score']]
            ))
            fig3.update_layout(
                title="Risk Score Comparison (Lower is Better)",
                xaxis_title="Crop",
                yaxis_title="Risk Score (1-10)",
                height=400
            )
            st.plotly_chart(fig3, use_container_width=True)
    
    # Tab 3: Cost Estimator
    with tab3:
        st.header("Input Cost Estimator")
        
        crop_name_cost = st.text_input("Crop Name", "wheat", key="cost_crop")
        
        if st.button("Estimate Costs", key="estimate_btn"):
            with st.spinner("Estimating costs..."):
                location = {
                    'state': state,
                    'district': district,
                    'latitude': latitude,
                    'longitude': longitude
                }
                
                result = tools.estimate_input_costs(
                    crop_name=crop_name_cost,
                    farm_size_acres=farm_size,
                    location=location,
                    soil_type=soil_type.lower(),
                    season=season_value
                )
                
                if result['success']:
                    st.session_state.cost_result = result
                else:
                    st.error(f"Error: {result.get('error')}")
        
        # Display cost estimation
        if 'cost_result' in st.session_state:
            result = st.session_state.cost_result
            
            st.subheader("💰 Total Cost Summary")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Cost Per Acre",
                    f"₹{result['total_cost_per_acre']:,.2f}"
                )
            
            with col2:
                st.metric(
                    f"Total Cost ({farm_size} acres)",
                    f"₹{result['total_farm_cost']:,.2f}"
                )
            
            # Category breakdown
            st.subheader("📊 Cost by Category")
            
            categories = result['cost_categories']
            cat_df = pd.DataFrame([
                {'Category': k.title(), 'Amount (₹)': v}
                for k, v in categories.items()
            ])
            
            fig = go.Figure(data=[go.Pie(
                labels=cat_df['Category'],
                values=cat_df['Amount (₹)'],
                hole=.4
            )])
            fig.update_layout(title="Cost Distribution by Category", height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed breakdown
            st.subheader("📋 Detailed Cost Breakdown (Per Acre)")
            
            costs_df = pd.DataFrame([
                {
                    'Item': k.replace('_', ' ').title(),
                    'Cost (₹)': f"₹{v:,.2f}",
                    'Total for Farm (₹)': f"₹{v * farm_size:,.2f}"
                }
                for k, v in result['costs_per_acre'].items()
            ])
            
            st.dataframe(costs_df, use_container_width=True)
            
            # Download option
            csv = costs_df.to_csv(index=False)
            st.download_button(
                label="Download Cost Breakdown (CSV)",
                data=csv,
                file_name=f"{crop_name_cost}_cost_breakdown.csv",
                mime="text/csv"
            )


if __name__ == "__main__":
    render_profitability_calculator()
