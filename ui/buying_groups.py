"""
RISE Cooperative Buying Groups UI
Streamlit UI component for forming and managing buying groups
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.buying_group_tools import create_buying_group_tools
from datetime import datetime, timedelta
import json


def render_buying_groups():
    """Render the cooperative buying groups interface"""
    
    st.title("🤝 Cooperative Buying Groups")
    st.markdown("Join forces with other farmers to purchase inputs at bulk prices")
    
    # Initialize tools
    if 'buying_group_tools' not in st.session_state:
        st.session_state.buying_group_tools = create_buying_group_tools()
    
    buying_tools = st.session_state.buying_group_tools
    
    # Create tabs for different features
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Find Groups",
        "➕ Create Group",
        "📊 My Groups",
        "💰 Pricing Calculator"
    ])
    
    # Tab 1: Find Groups
    with tab1:
        render_find_groups(buying_tools)
    
    # Tab 2: Create Group
    with tab2:
        render_create_group(buying_tools)
    
    # Tab 3: My Groups
    with tab3:
        render_my_groups(buying_tools)
    
    # Tab 4: Pricing Calculator
    with tab4:
        render_pricing_calculator(buying_tools)


def render_find_groups(buying_tools):
    """Render find matching groups interface"""
    
    st.header("Find Buying Groups")
    st.markdown("Search for groups matching your input requirements")
    
    # Get user ID from session state
    user_id = st.session_state.get('user_id', 'farmer_demo')
    
    col1, col2 = st.columns(2)
    
    with col1:
        state = st.text_input("State", value="Punjab", key="find_state")
        district = st.text_input("District", value="Ludhiana", key="find_district")
    
    with col2:
        st.write("**Select Products You Need:**")
        
        # Product selection
        product_options = [
            "wheat_seeds", "rice_seeds", "maize_seeds",
            "fertilizer_urea", "fertilizer_dap", "fertilizer_potash",
            "pesticide_spray", "herbicide", "fungicide",
            "irrigation_pipes", "drip_irrigation"
        ]
        
        selected_products = st.multiselect(
            "Products",
            product_options,
            default=["wheat_seeds", "fertilizer_urea"],
            help="Select the agricultural inputs you want to purchase"
        )
    
    if st.button("Search Groups", type="primary"):
        if not selected_products:
            st.error("Please select at least one product")
        else:
            requirements = {
                'products': selected_products,
                'state': state,
                'district': district
            }
            
            with st.spinner("Searching for matching groups..."):
                result = buying_tools.find_matching_groups(user_id, requirements)
            
            # Ensure result is a dict (tool may rarely return str on unexpected failure)
            if not isinstance(result, dict):
                st.error(f"Search failed: {result if isinstance(result, str) else 'Unknown error'}")
                return
            if result.get('success'):
                st.success(f"✓ Found {result['count']} matching groups")
                
                if result['groups']:
                    st.subheader("Matching Groups")
                    
                    for group in result['groups']:
                        with st.container():
                            col_a, col_b, col_c = st.columns([3, 2, 1])
                            
                            with col_a:
                                st.markdown(f"### {group['group_name']}")
                                st.write(f"**Status:** {group['status'].upper()}")
                                st.write(f"**Location:** {group['location']['district']}, {group['location']['state']}")
                                st.write(f"**Matching Products:** {', '.join(group['matching_products'])}")
                            
                            with col_b:
                                st.metric("Match Score", f"{group['match_score']}%")
                                st.metric("Members", f"{group['current_members']}/{group['max_members']}")
                                st.write(f"**Discount:** {group['estimated_discount']}")
                            
                            with col_c:
                                st.write("")
                                st.write("")
                                if st.button("View Details", key=f"view_{group['group_id']}"):
                                    st.session_state.selected_group = group
                                    st.rerun()
                            
                            st.divider()
                    
                    # Show selected group details
                    if 'selected_group' in st.session_state:
                        show_group_details(buying_tools, st.session_state.selected_group, user_id)
                else:
                    st.info("No matching groups found. Consider creating a new group!")
            else:
                err = result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)
                st.error(f"Search failed: {err}")


def show_group_details(buying_tools, group, user_id):
    """Show detailed group information and join form"""
    
    st.subheader(f"Group Details: {group['group_name']}")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.write(f"**Group ID:** {group['group_id']}")
        st.write(f"**Status:** {group['status'].upper()}")
        st.write(f"**Members:** {group['current_members']}/{group['max_members']}")
        st.write(f"**Location:** {group['location']['district']}, {group['location']['state']}")
    
    with col_b:
        st.write(f"**Target Products:** {', '.join(group['matching_products'])}")
        st.write(f"**Estimated Discount:** {group['estimated_discount']}")
        st.write(f"**Deadline:** {group.get('deadline', 'Not set')}")
        st.write(f"**Match Score:** {group['match_score']}%")
    
    with st.expander("🤖 AI advice: Should I join this group?"):
        if st.button("Get AI advice", key=f"bg_ai_{group.get('group_id', 'g')}"):
            with st.spinner("Generating advice..."):
                from tools.ai_insights import get_ai_insight
                prompt = f"""You are a cooperative farming advisor. A farmer is considering joining this buying group. In 2 short paragraphs, give clear advice.

Group: {group.get('group_name', '')}. Products: {', '.join(group.get('matching_products', []))}. Members: {group.get('current_members', 0)}/{group.get('max_members', 0)}. Estimated discount: {group.get('estimated_discount', '')}. Match score: {group.get('match_score', 0)}%.

Say: (1) Whether joining is a good idea and why. (2) What to watch out for or confirm before joining. Be practical and supportive."""
                ai = get_ai_insight(prompt)
            if ai.get('success'):
                st.markdown(ai.get('text', ''))
            else:
                st.error(ai.get('error'))
    
    # Join form
    st.subheader("Join This Group")
    
    with st.form("join_group_form"):
        st.write("**Specify Your Requirements:**")
        
        member_requirements = {}
        
        for product in group['matching_products']:
            quantity = st.number_input(
                f"{product.replace('_', ' ').title()} (kg/units)",
                min_value=0,
                max_value=10000,
                value=100,
                step=10,
                key=f"qty_{product}"
            )
            if quantity > 0:
                member_requirements[product] = quantity
        
        if st.form_submit_button("Join Group", type="primary"):
            if not member_requirements:
                st.error("Please specify quantities for at least one product")
            else:
                with st.spinner("Joining group..."):
                    result = buying_tools.join_buying_group(
                        user_id,
                        group['group_id'],
                        member_requirements
                    )
                
                if result['success']:
                    st.success(f"✓ Successfully joined {result['group_name']}!")
                    
                    col_1, col_2 = st.columns(2)
                    
                    with col_1:
                        st.metric("Total Members", result['total_members'])
                        st.metric("Group Status", result['status'].upper())
                    
                    with col_2:
                        st.write("**Total Quantities:**")
                        for product, qty in result['total_quantities'].items():
                            st.write(f"• {product}: {qty} units")
                    
                    if result.get('potential_savings'):
                        st.subheader("Your Potential Savings")
                        total_savings = sum(result['potential_savings'].values())
                        st.metric("Total Estimated Savings", f"₹{total_savings:.2f}")
                        
                        for product, savings in result['potential_savings'].items():
                            st.write(f"• {product}: ₹{savings:.2f}")
                    
                    st.balloons()
                else:
                    st.error(f"Failed to join group: {result.get('error')}")


def render_create_group(buying_tools):
    """Render create buying group form"""
    
    st.header("Create Buying Group")
    st.markdown("Start a new cooperative buying group and invite farmers")
    
    with st.form("create_group_form"):
        group_name = st.text_input(
            "Group Name",
            placeholder="e.g., Ludhiana Seed Buyers Group",
            help="Choose a descriptive name for your buying group"
        )
        
        st.subheader("Target Products")
        st.markdown("Select the agricultural inputs your group will purchase")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Seeds:**")
            wheat_seeds = st.checkbox("Wheat Seeds")
            rice_seeds = st.checkbox("Rice Seeds")
            maize_seeds = st.checkbox("Maize Seeds")
        
        with col2:
            st.write("**Fertilizers:**")
            urea = st.checkbox("Urea")
            dap = st.checkbox("DAP")
            potash = st.checkbox("Potash")
        
        with col3:
            st.write("**Pesticides:**")
            pesticide = st.checkbox("Pesticide Spray")
            herbicide = st.checkbox("Herbicide")
            fungicide = st.checkbox("Fungicide")
        
        # Collect selected products
        target_products = []
        if wheat_seeds: target_products.append("wheat_seeds")
        if rice_seeds: target_products.append("rice_seeds")
        if maize_seeds: target_products.append("maize_seeds")
        if urea: target_products.append("fertilizer_urea")
        if dap: target_products.append("fertilizer_dap")
        if potash: target_products.append("fertilizer_potash")
        if pesticide: target_products.append("pesticide_spray")
        if herbicide: target_products.append("herbicide")
        if fungicide: target_products.append("fungicide")
        
        st.subheader("Location Details")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            state = st.text_input("State", value="Punjab")
            district = st.text_input("District", value="Ludhiana")
        
        with col_b:
            radius_km = st.slider(
                "Search Radius (km)",
                min_value=10,
                max_value=100,
                value=25,
                step=5,
                help="Maximum distance for group members"
            )
        
        st.subheader("Group Settings")
        
        col_x, col_y = st.columns(2)
        
        with col_x:
            min_members = st.number_input(
                "Minimum Members",
                min_value=2,
                max_value=50,
                value=5,
                help="Minimum members needed to activate group"
            )
        
        with col_y:
            max_members = st.number_input(
                "Maximum Members",
                min_value=5,
                max_value=200,
                value=30,
                help="Maximum members allowed in group"
            )
        
        deadline_days = st.slider(
            "Deadline (days from now)",
            min_value=7,
            max_value=60,
            value=14,
            help="Deadline for members to join"
        )
        
        submitted = st.form_submit_button("Create Group", type="primary")
        
        if submitted:
            if not group_name:
                st.error("Group name is required")
            elif not target_products:
                st.error("Please select at least one target product")
            else:
                # Get organizer ID from session state
                organizer_id = st.session_state.get('user_id', 'organizer_demo')
                
                deadline = (datetime.now() + timedelta(days=deadline_days)).isoformat()
                
                group_data = {
                    'group_name': group_name,
                    'target_products': target_products,
                    'location': {
                        'state': state,
                        'district': district,
                        'radius_km': radius_km
                    },
                    'min_members': min_members,
                    'max_members': max_members,
                    'deadline': deadline
                }
                
                with st.spinner("Creating buying group..."):
                    result = buying_tools.create_buying_group(organizer_id, group_data)
                
                if result['success']:
                    st.success(f"✓ Group created successfully!")
                    
                    col_1, col_2 = st.columns(2)
                    
                    with col_1:
                        st.write(f"**Group ID:** {result['group_id']}")
                        st.write(f"**Group Name:** {result['group_name']}")
                        st.write(f"**Status:** {result['status'].upper()}")
                    
                    with col_2:
                        st.write(f"**Target Discount:** {result['target_discount']}")
                        st.write(f"**Deadline:** {result['deadline']}")
                    
                    st.info("Share the Group ID with other farmers to invite them!")
                    st.balloons()
                else:
                    st.error(f"Failed to create group: {result.get('error')}")


def render_my_groups(buying_tools):
    """Render user's buying groups"""
    
    st.header("My Buying Groups")
    
    # Get user ID from session state
    user_id = st.session_state.get('user_id', 'farmer_demo')
    
    with st.spinner("Loading your groups..."):
        result = buying_tools.get_user_groups(user_id)
    
    if result['success']:
        if result['groups']:
            st.markdown(f"**Total Groups:** {result['count']}")
            
            for i, group in enumerate(result['groups'], 1):
                with st.expander(f"{group['group_name']} ({group['status'].upper()})"):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.write(f"**Group ID:** {group['group_id']}")
                        st.write(f"**Status:** {group['status'].upper()}")
                        st.write(f"**Members:** {group['member_count']}")
                        st.write(f"**Role:** {'Organizer' if group['is_organizer'] else 'Member'}")
                    
                    with col_b:
                        st.write(f"**Target Products:**")
                        for product in group['target_products']:
                            st.write(f"• {product.replace('_', ' ').title()}")
                        st.write(f"**Deadline:** {group.get('deadline', 'Not set')}")
                    
                    col_1, col_2 = st.columns(2)
                    
                    with col_1:
                        if st.button("View Full Details", key=f"details_{group['group_id']}"):
                            show_full_group_details(buying_tools, group['group_id'])
                    
                    with col_2:
                        if group['is_organizer'] and group['status'] == 'active':
                            if st.button("Calculate Pricing", key=f"pricing_{group['group_id']}"):
                                calculate_group_pricing(buying_tools, group['group_id'])
        else:
            st.info("You haven't joined any buying groups yet. Search for groups or create a new one!")
    else:
        st.error(f"Failed to load groups: {result.get('error')}")


def show_full_group_details(buying_tools, group_id):
    """Show full details of a buying group"""
    
    with st.spinner("Loading group details..."):
        result = buying_tools.get_group_details(group_id)
    
    if result['success']:
        st.subheader(f"Full Details: {result['group_name']}")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.write(f"**Group ID:** {result['group_id']}")
            st.write(f"**Status:** {result['status'].upper()}")
            st.write(f"**Members:** {result['member_count']}/{result['max_members']}")
            st.write(f"**Organizer:** {result['organizer_user_id']}")
        
        with col_b:
            loc = result.get('location') or {}
            loc_dist = loc.get('district', '') if isinstance(loc, dict) else str(loc)
            loc_state = loc.get('state', '') if isinstance(loc, dict) else ''
            st.write(f"**Location:** {loc_dist}, {loc_state}")
            st.write(f"**Deadline:** {result.get('deadline', 'Not set')}")
            ts = result.get('created_timestamp')
            if ts is not None:
                try:
                    ts_val = int(ts) if not isinstance(ts, (int, float)) else ts
                    st.write(f"**Created:** {datetime.fromtimestamp(ts_val).strftime('%Y-%m-%d')}")
                except (TypeError, OSError):
                    st.write(f"**Created:** {ts}")
            else:
                st.write("**Created:** —")
        
        if result['total_quantities']:
            st.subheader("Total Quantities Needed")
            for product, qty in result['total_quantities'].items():
                st.write(f"• {product.replace('_', ' ').title()}: {qty} units")
        
        if result['bulk_pricing']:
            st.subheader("Bulk Pricing Achieved")
            for product, discount in result['bulk_pricing'].items():
                st.write(f"• {product.replace('_', ' ').title()}: {discount}% discount")
    else:
        st.error(f"Failed to load details: {result.get('error')}")


def calculate_group_pricing(buying_tools, group_id):
    """Calculate and display bulk pricing for group"""
    
    with st.spinner("Calculating bulk pricing..."):
        result = buying_tools.calculate_bulk_pricing(group_id)
    
    if result['success']:
        st.success("✓ Bulk pricing calculated!")
        
        st.metric("Average Discount", f"{result['average_discount']}%")
        
        st.subheader("Pricing Breakdown")
        
        for product, pricing in result['pricing_breakdown'].items():
            with st.container():
                st.write(f"**{product.replace('_', ' ').title()}**")
                
                col_1, col_2, col_3, col_4 = st.columns(4)
                
                with col_1:
                    st.metric("Quantity", f"{pricing['quantity']} units")
                
                with col_2:
                    st.metric("Market Price", f"₹{pricing['market_price_per_unit']}")
                
                with col_3:
                    st.metric("Bulk Price", f"₹{pricing['bulk_price_per_unit']}")
                
                with col_4:
                    st.metric("Discount", f"{pricing['discount_percentage']}%")
                
                st.write(f"**Total Cost:** ₹{pricing['total_cost']:.2f}")
                st.write(f"**Total Savings:** ₹{pricing['total_savings']:.2f}")
                st.divider()
    else:
        st.error(f"Failed to calculate pricing: {result.get('error')}")


def render_pricing_calculator(buying_tools):
    """Render bulk pricing calculator"""
    
    st.header("Bulk Pricing Calculator")
    st.markdown("Estimate savings from cooperative buying")
    
    st.subheader("Enter Your Requirements")
    
    product_options = {
        "Wheat Seeds": 1200,
        "Rice Seeds": 1500,
        "Fertilizer (Urea)": 800,
        "Fertilizer (DAP)": 1200,
        "Pesticide Spray": 2000
    }
    
    total_individual_cost = 0
    total_bulk_cost = 0
    
    for product, market_price in product_options.items():
        col_a, col_b, col_c = st.columns([2, 1, 1])
        
        with col_a:
            st.write(f"**{product}**")
        
        with col_b:
            quantity = st.number_input(
                f"Quantity (kg)",
                min_value=0,
                max_value=1000,
                value=0,
                step=10,
                key=f"calc_{product}",
                label_visibility="collapsed"
            )
        
        with col_c:
            st.write(f"₹{market_price}/kg")
        
        if quantity > 0:
            individual_cost = market_price * quantity
            
            # Estimate bulk discount (simplified)
            if quantity >= 500:
                discount = 25
            elif quantity >= 250:
                discount = 20
            elif quantity >= 100:
                discount = 15
            else:
                discount = 10
            
            bulk_price = market_price * (1 - discount / 100)
            bulk_cost = bulk_price * quantity
            savings = individual_cost - bulk_cost
            
            total_individual_cost += individual_cost
            total_bulk_cost += bulk_cost
            
            st.write(f"Individual: ₹{individual_cost:.2f} | Bulk: ₹{bulk_cost:.2f} | Savings: ₹{savings:.2f} ({discount}%)")
        
        st.divider()
    
    if total_individual_cost > 0:
        st.subheader("Total Savings Estimate")
        
        col_1, col_2, col_3 = st.columns(3)
        
        with col_1:
            st.metric("Individual Cost", f"₹{total_individual_cost:.2f}")
        
        with col_2:
            st.metric("Bulk Cost", f"₹{total_bulk_cost:.2f}")
        
        with col_3:
            total_savings = total_individual_cost - total_bulk_cost
            savings_pct = (total_savings / total_individual_cost) * 100
            st.metric("Total Savings", f"₹{total_savings:.2f}", f"{savings_pct:.1f}%")
        
        st.success(f"💰 You could save ₹{total_savings:.2f} by joining a buying group!")


# Main function for standalone testing
if __name__ == '__main__':
    st.set_page_config(
        page_title="RISE - Buying Groups",
        page_icon="🤝",
        layout="wide"
    )
    
    render_buying_groups()
