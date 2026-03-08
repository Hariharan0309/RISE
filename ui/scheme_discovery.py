"""
RISE Scheme Discovery UI Component
Streamlit interface for government scheme discovery and eligibility checking
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.scheme_discovery_tools import SchemeDiscoveryTools
from datetime import datetime


def render_scheme_discovery():
    """Render the scheme discovery interface"""
    st.header("🏛️ Government Scheme Discovery")
    st.markdown("Find and apply for government schemes tailored to your farm profile")
    
    # Initialize tools
    if 'discovery_tools' not in st.session_state:
        st.session_state.discovery_tools = SchemeDiscoveryTools()
    
    tools = st.session_state.discovery_tools
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📋 Profile Analysis", "🔍 Scheme Recommendations", "✅ Eligibility Check"])
    
    with tab1:
        render_profile_analysis(tools)
    
    with tab2:
        render_scheme_recommendations(tools)
    
    with tab3:
        render_eligibility_check(tools)


def render_profile_analysis(tools: SchemeDiscoveryTools):
    """Render farmer profile analysis section"""
    st.subheader("Farmer Profile Analysis")
    st.markdown("Enter your farm details to analyze applicable scheme categories")
    
    col1, col2 = st.columns(2)
    
    with col1:
        farmer_name = st.text_input("Farmer Name", value="Ravi Kumar")
        state = st.selectbox(
            "State",
            ["Uttar Pradesh", "Maharashtra", "Punjab", "Karnataka", "Tamil Nadu", 
             "Andhra Pradesh", "Rajasthan", "Madhya Pradesh", "Gujarat", "West Bengal"]
        )
        district = st.text_input("District", value="Lucknow")
        land_size = st.number_input("Land Size (acres)", min_value=0.1, max_value=100.0, value=2.0, step=0.1)
    
    with col2:
        soil_type = st.selectbox("Soil Type", ["Loamy", "Clay", "Sandy", "Black", "Red", "Alluvial"])
        crops = st.multiselect(
            "Crops Grown",
            ["Wheat", "Rice", "Cotton", "Sugarcane", "Maize", "Pulses", "Vegetables", "Fruits"],
            default=["Wheat", "Rice"]
        )
        farming_experience = st.selectbox("Farming Experience", ["< 5 years", "5-10 years", "10-20 years", "> 20 years"])
        annual_income = st.number_input("Annual Income (₹)", min_value=0, max_value=10000000, value=150000, step=10000)
    
    if st.button("🔍 Analyze Profile", type="primary"):
        with st.spinner("Analyzing your profile with AI..."):
            # Build farmer profile
            farmer_profile = {
                'name': farmer_name,
                'location': {
                    'state': state.lower(),
                    'district': district.lower()
                },
                'farm_details': {
                    'land_size': land_size,
                    'soil_type': soil_type.lower(),
                    'crops': [c.lower() for c in crops],
                    'farming_experience': farming_experience,
                    'land_ownership': True
                },
                'annual_income': annual_income
            }
            
            # Store in session state
            st.session_state.farmer_profile = farmer_profile
            
            # Analyze profile
            result = tools.analyze_farmer_profile(farmer_profile)
            
            if result['success']:
                st.success("✅ Profile analysis completed!")
                
                analysis = result['analysis']
                profile_summary = result['profile_summary']
                
                # Display profile summary
                st.markdown("### 📊 Profile Summary")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Farmer Category", profile_summary['farmer_category'].title())
                
                with col2:
                    st.metric("Land Size", f"{profile_summary['land_size']} acres")
                
                with col3:
                    st.metric("State", profile_summary['state'].title())
                
                with col4:
                    st.metric("Crops", profile_summary['crops_count'])
                
                # Display AI analysis
                st.markdown("### 🤖 AI Analysis")
                
                def _display_value(v):
                    """Handle both string and dict items from analysis."""
                    if isinstance(v, str):
                        return v.replace('_', ' ').title()
                    if isinstance(v, dict):
                        raw = v.get('name') or v.get('category') or v.get('title') or next(iter(v.values()), '')
                        return str(raw).replace('_', ' ').title()
                    return str(v)

                st.markdown("**Relevant Scheme Categories:**")
                for category in analysis.get('relevant_categories', []):
                    st.markdown(f"- {_display_value(category)}")
                
                st.markdown("**Identified Needs:**")
                for need in analysis.get('farmer_needs', []):
                    st.markdown(f"- {_display_value(need)}")
                
                st.markdown("**Priority Areas:**")
                for area in analysis.get('priority_areas', []):
                    st.markdown(f"- {_display_value(area)}")
                
                st.info(f"💰 Estimated Benefits: {analysis.get('estimated_benefits', 'Moderate')}")
                
                # Profile completeness
                completeness = analysis.get('profile_completeness', 0.8) * 100
                st.progress(completeness / 100)
                st.caption(f"Profile Completeness: {completeness:.0f}%")
            
            else:
                st.error(f"❌ Error: {result.get('error', 'Analysis failed')}")


def render_scheme_recommendations(tools: SchemeDiscoveryTools):
    """Render scheme recommendations section"""
    st.subheader("Personalized Scheme Recommendations")
    
    # Check if profile exists
    if 'farmer_profile' not in st.session_state:
        st.warning("⚠️ Please complete the Profile Analysis first")
        return
    
    farmer_profile = st.session_state.farmer_profile
    
    st.markdown(f"**Farmer:** {farmer_profile['name']}")
    st.markdown(f"**Location:** {farmer_profile['location']['district'].title()}, {farmer_profile['location']['state'].title()}")
    st.markdown(f"**Land Size:** {farmer_profile['farm_details']['land_size']} acres")
    
    if st.button("🎯 Get Scheme Recommendations", type="primary"):
        with st.spinner("Finding applicable schemes..."):
            result = tools.recommend_schemes(farmer_profile)
            
            if result['success']:
                st.success(f"✅ Found {result['count']} applicable schemes!")
                
                # Display summary
                summary = result['recommendation_summary']
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Schemes", result['count'])
                
                with col2:
                    st.metric("High Priority", summary['high_priority'], delta="Urgent")
                
                with col3:
                    st.metric("Medium Priority", summary['medium_priority'])
                
                with col4:
                    st.metric("Total Benefit", f"₹{result['total_potential_benefit']:,.0f}")
                
                st.markdown("---")
                
                # Display schemes
                schemes = result['schemes']
                
                # Filter options
                priority_filter = st.selectbox(
                    "Filter by Priority",
                    ["All", "High", "Medium", "Low"]
                )
                
                filtered_schemes = schemes
                if priority_filter != "All":
                    filtered_schemes = [s for s in schemes if s['priority_level'] == priority_filter.lower()]
                
                # Display each scheme
                for i, scheme in enumerate(filtered_schemes, 1):
                    render_scheme_card(scheme, i)
                
                # Store recommendations in session state
                st.session_state.recommended_schemes = schemes
            
            else:
                st.error(f"❌ Error: {result.get('error', 'Recommendation failed')}")


def render_scheme_card(scheme: dict, index: int):
    """Render a scheme card"""
    # Priority color coding
    priority_colors = {
        'high': '🔴',
        'medium': '🟡',
        'low': '🟢'
    }
    
    priority_icon = priority_colors.get(scheme['priority_level'], '⚪')
    
    with st.expander(f"{priority_icon} {index}. {scheme['scheme_name']} - Priority: {scheme['priority_score']:.1f}/100"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Type:** {scheme['scheme_type'].title()}")
            st.markdown(f"**Category:** {scheme['category'].replace('_', ' ').title()}")
            st.markdown(f"**Description:** {scheme.get('description', 'No description available')}")
            
            # Deadline info
            if scheme.get('days_to_deadline'):
                days = scheme['days_to_deadline']
                if days <= 30:
                    st.error(f"⏰ URGENT: {days} days remaining to apply!")
                elif days <= 90:
                    st.warning(f"⏰ {days} days remaining to apply")
                else:
                    st.info(f"⏰ {days} days remaining to apply")
            else:
                st.info("📅 No deadline - Ongoing scheme")
        
        with col2:
            st.metric("Estimated Benefit", f"₹{scheme.get('estimated_benefit', 0):,.0f}")
            st.metric("Eligibility", f"{scheme.get('eligibility_confidence', 0)*100:.0f}%")
            st.metric("Priority Level", scheme['priority_level'].upper())
        
        # Required documents
        st.markdown("**📄 Required Documents:**")
        docs = scheme.get('required_documents', [])
        for doc in docs:
            st.markdown(f"- {doc}")
        
        # Next steps
        st.markdown("**📝 Next Steps:**")
        steps = scheme.get('next_steps', [])
        for step in steps:
            st.markdown(f"- {step}")
        
        # Application link
        if scheme.get('official_website'):
            st.markdown(f"**🔗 Official Website:** [{scheme['official_website']}]({scheme['official_website']})")
        # AI: explain in simple terms
        if st.button("🤖 Explain in simple terms", key=f"scheme_ai_{scheme.get('scheme_id', index)}"):
            with st.spinner("Generating simple explanation..."):
                from tools.ai_insights import get_ai_insight
                prompt = f"""Explain this government scheme for farmers in 2 short, simple paragraphs. Use everyday language.

Scheme: {scheme.get('scheme_name', '')}. Category: {scheme.get('category', '')}. Description: {scheme.get('description', 'No description')}. Benefit: ₹{scheme.get('estimated_benefit', 0):,.0f}. Documents needed: {scheme.get('required_documents', [])}.

Say: (1) What the scheme is and who it is for. (2) What the farmer needs to do to apply and what they get. No jargon."""
                ai = get_ai_insight(prompt)
            if ai.get('success'):
                st.markdown(ai.get('text', ''))
            else:
                st.error(ai.get('error', 'Failed to generate explanation'))


def render_eligibility_check(tools: SchemeDiscoveryTools):
    """Render eligibility checking section"""
    st.subheader("Check Scheme Eligibility")
    
    # Check if profile exists
    if 'farmer_profile' not in st.session_state:
        st.warning("⚠️ Please complete the Profile Analysis first")
        return
    
    farmer_profile = st.session_state.farmer_profile
    
    # Check if recommendations exist
    scheme_id = None
    if 'recommended_schemes' in st.session_state:
        schemes = st.session_state.recommended_schemes
        scheme_options = {f"{s['scheme_name']} ({s['scheme_id']})": s['scheme_id'] for s in (schemes or [])}
        if scheme_options:
            options_list = list(scheme_options.keys())
            selected_scheme = st.selectbox(
                "Select a scheme to check eligibility",
                options=options_list,
                index=0,
                key="eligibility_scheme_select"
            )
            scheme_id = scheme_options.get(selected_scheme) if selected_scheme else (list(scheme_options.values())[0] if scheme_options else None)
        else:
            scheme_id = st.text_input("Enter Scheme ID", placeholder="SCH_XXXXXXXXXXXX", key="eligibility_scheme_id_manual")
    else:
        scheme_id = st.text_input("Enter Scheme ID", placeholder="SCH_XXXXXXXXXXXX", key="eligibility_scheme_id_manual")
    if scheme_id is None:
        scheme_id = ""
    
    if st.button("✅ Check Eligibility", type="primary"):
        if not scheme_id:
            st.error("Please select or enter a scheme ID")
            return
        
        with st.spinner("Checking eligibility..."):
            result = tools.check_eligibility(farmer_profile, scheme_id)
            
            if result['success']:
                # Display eligibility status
                if result['eligible']:
                    st.success(f"✅ You are ELIGIBLE for {result['scheme_name']}!")
                else:
                    st.error(f"❌ You are NOT ELIGIBLE for {result['scheme_name']}")
                
                # Confidence score
                confidence = result['confidence_score'] * 100
                st.progress(confidence / 100)
                st.caption(f"Confidence Score: {confidence:.0f}%")
                
                # Reasons
                st.markdown("### 📋 Eligibility Details")
                for reason in result['reasons']:
                    if result['eligible']:
                        st.success(f"✓ {reason}")
                    else:
                        st.error(f"✗ {reason}")
                
                if result['eligible']:
                    # Required documents
                    st.markdown("### 📄 Required Documents")
                    for doc in result['required_documents']:
                        st.markdown(f"- {doc}")
                    
                    # Missing requirements
                    if result.get('missing_requirements'):
                        st.warning("⚠️ Missing Requirements:")
                        for req in result['missing_requirements']:
                            st.markdown(f"- {req}")
                    
                    # Next steps
                    st.markdown("### 📝 Next Steps")
                    for i, step in enumerate(result['next_steps'], 1):
                        st.markdown(f"{i}. {step}")
                    
                    # Action button
                    st.markdown("---")
                    if st.button("📤 Start Application Process"):
                        st.info("Application process guidance will be available in the next update!")
                
                else:
                    st.info("💡 Tip: Explore other schemes that match your profile better")
            
            else:
                st.error(f"❌ Error: {result.get('error', 'Eligibility check failed')}")


# Main function for standalone testing
if __name__ == "__main__":
    st.set_page_config(
        page_title="RISE - Scheme Discovery",
        page_icon="🏛️",
        layout="wide"
    )
    
    render_scheme_discovery()
