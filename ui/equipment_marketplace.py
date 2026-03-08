"""
RISE Equipment Sharing Marketplace UI
Streamlit UI component for equipment listing, search, and booking
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.equipment_sharing_tools import create_equipment_sharing_tools
from datetime import datetime, timedelta
import json


def render_equipment_marketplace():
    """Render the equipment sharing marketplace"""
    
    st.title("🚜 Equipment Sharing Marketplace")
    st.markdown("Share or rent agricultural equipment with nearby farmers")
    
    # Initialize tools
    if 'equipment_tools' not in st.session_state:
        st.session_state.equipment_tools = create_equipment_sharing_tools()
    
    equipment_tools = st.session_state.equipment_tools
    
    # Create tabs for different features
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Search Equipment",
        "📝 List Your Equipment",
        "📅 My Bookings",
        "⭐ Rate & Review"
    ])
    
    # Tab 1: Search Equipment
    with tab1:
        render_equipment_search(equipment_tools)
    
    # Tab 2: List Equipment
    with tab2:
        render_equipment_listing(equipment_tools)
    
    # Tab 3: My Bookings
    with tab3:
        render_my_bookings(equipment_tools)
    
    # Tab 4: Rate & Review
    with tab4:
        render_rating_review(equipment_tools)


def render_equipment_search(equipment_tools):
    """Render equipment search interface"""
    
    st.header("Search Available Equipment")
    st.markdown("Find equipment within 25km radius")
    
    # AI: suggest equipment for my farm
    with st.expander("🤖 Suggest equipment for my farm (AI)"):
        farm_crops = st.text_input("Crops you grow (comma-separated)", value="wheat, rice", key="eq_crops")
        farm_acres = st.number_input("Farm size (acres)", min_value=0.5, value=5.0, step=0.5, key="eq_acres")
        if st.button("Get AI suggestion", key="eq_ai_btn"):
            with st.spinner("Getting AI suggestion..."):
                from tools.ai_insights import get_ai_insight
                prompt = f"""You are an agricultural equipment advisor for Indian farmers. In 2 short paragraphs, suggest which types of equipment would be most useful for this farm and why.

Farm: {farm_acres} acres. Crops: {farm_crops}.

Suggest 3-5 equipment types (e.g. tractor, pump, harvester, sprayer, drone) and briefly say what each helps with. Keep it practical and simple."""
                ai = get_ai_insight(prompt)
            if ai.get('success'):
                st.markdown(ai.get('text', ''))
            else:
                st.error(ai.get('error', 'Failed to get suggestion'))
    
    col1, col2 = st.columns(2)
    
    with col1:
        equipment_type = st.selectbox(
            "Equipment Type",
            ["All Types", "tractor", "pump", "drone", "harvester", "plough", "sprayer"],
            help="Select type of equipment you need"
        )
        
        radius_km = st.slider(
            "Search Radius (km)",
            min_value=5,
            max_value=50,
            value=25,
            step=5,
            help="Maximum distance from your location"
        )
    
    with col2:
        state = st.text_input("State", value="Punjab")
        district = st.text_input("District", value="Ludhiana")
    
    col3, col4 = st.columns(2)
    
    with col3:
        latitude = st.number_input("Latitude", value=30.9010, format="%.4f")
    
    with col4:
        longitude = st.number_input("Longitude", value=75.8573, format="%.4f")
    
    # Date range filter
    st.subheader("Availability Filter (Optional)")
    
    use_date_filter = st.checkbox("Filter by availability dates")
    
    date_range = None
    if use_date_filter:
        col_a, col_b = st.columns(2)
        
        with col_a:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now(),
                min_value=datetime.now()
            )
        
        with col_b:
            end_date = st.date_input(
                "End Date",
                value=datetime.now() + timedelta(days=3),
                min_value=datetime.now()
            )
        
        date_range = {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        }
    
    if st.button("Search Equipment", type="primary"):
        location = {
            'state': state,
            'district': district,
            'latitude': latitude,
            'longitude': longitude
        }
        
        equipment_type_filter = None if equipment_type == "All Types" else equipment_type
        
        with st.spinner("Searching for equipment..."):
            result = equipment_tools.search_equipment(
                location,
                equipment_type_filter,
                date_range,
                radius_km
            )
        
        if result['success']:
            st.success(f"✓ Found {result['count']} equipment available")
            
            if result['equipment']:
                st.subheader("Available Equipment")
                
                for equipment in result['equipment']:
                    with st.container():
                        col_1, col_2, col_3 = st.columns([3, 2, 1])
                        
                        with col_1:
                            st.markdown(f"### {equipment['name']}")
                            st.write(f"**Type:** {equipment['type'].title()}")
                            st.write(f"**Model:** {equipment.get('model', 'N/A')}")
                            st.write(f"**Condition:** {equipment['condition'].title()}")
                            st.write(f"**Location:** {equipment['location']['district']}, {equipment['location']['state']}")
                        
                        with col_2:
                            st.metric("Distance", f"{equipment['distance_km']} km")
                            st.metric("Daily Rate", f"₹{equipment['daily_rate']}")
                            st.metric("Rating", f"{equipment['ratings'].get('average', 0):.1f}/5")
                        
                        with col_3:
                            st.write("")
                            st.write("")
                            if st.button("View Details", key=f"view_{equipment['resource_id']}"):
                                st.session_state.selected_equipment = equipment
                                st.rerun()
                        
                        st.divider()
                
                # Show selected equipment details
                if 'selected_equipment' in st.session_state:
                    show_equipment_details(equipment_tools, st.session_state.selected_equipment)
            else:
                st.info("No equipment found matching your criteria. Try increasing the search radius.")
        else:
            st.error(f"Search failed: {result.get('error')}")


def show_equipment_details(equipment_tools, equipment):
    """Show detailed equipment information and booking form"""
    
    st.subheader(f"Equipment Details: {equipment['name']}")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.write(f"**Type:** {equipment['type'].title()}")
        st.write(f"**Model:** {equipment.get('model', 'N/A')}")
        st.write(f"**Condition:** {equipment['condition'].title()}")
        st.write(f"**Distance:** {equipment['distance_km']} km")
    
    with col_b:
        st.write(f"**Hourly Rate:** ₹{equipment['hourly_rate']}")
        st.write(f"**Daily Rate:** ₹{equipment['daily_rate']}")
        st.write(f"**Rating:** {equipment['ratings'].get('average', 0):.1f}/5 ({equipment['ratings'].get('count', 0)} reviews)")
        st.write(f"**Transport Cost:** ₹{equipment['estimated_transport_cost']}")
    
    # Specifications
    if equipment.get('specifications'):
        st.subheader("Specifications")
        specs = equipment['specifications']
        for key, value in specs.items():
            st.write(f"• **{key.replace('_', ' ').title()}:** {value}")
    
    # Booking form
    st.subheader("Book This Equipment")
    
    with st.form("booking_form"):
        col_1, col_2 = st.columns(2)
        
        with col_1:
            start_datetime = st.date_input(
                "Start Date",
                value=datetime.now() + timedelta(days=1),
                min_value=datetime.now()
            )
            start_time = st.time_input("Start Time", value=datetime.now().time())
        
        with col_2:
            end_datetime = st.date_input(
                "End Date",
                value=datetime.now() + timedelta(days=2),
                min_value=datetime.now()
            )
            end_time = st.time_input("End Time", value=datetime.now().time())
        
        # Combine date and time
        start_dt = datetime.combine(start_datetime, start_time)
        end_dt = datetime.combine(end_datetime, end_time)
        
        # Calculate estimated cost
        duration_hours = (end_dt - start_dt).total_seconds() / 3600
        duration_days = duration_hours / 24
        
        if duration_days >= 1 and duration_hours % 24 == 0:
            estimated_cost = equipment['daily_rate'] * duration_days
            cost_breakdown = f"{duration_days:.0f} days × ₹{equipment['daily_rate']}"
        else:
            estimated_cost = equipment['hourly_rate'] * duration_hours
            cost_breakdown = f"{duration_hours:.1f} hours × ₹{equipment['hourly_rate']}"
        
        insurance_cost = estimated_cost * 0.05
        total_cost = estimated_cost + insurance_cost
        
        st.info(f"""
**Cost Breakdown:**
- Equipment: {cost_breakdown} = ₹{estimated_cost:.2f}
- Insurance (5%): ₹{insurance_cost:.2f}
- Transport: ₹{equipment['estimated_transport_cost']}
- **Total: ₹{total_cost + equipment['estimated_transport_cost']:.2f}**
""")
        
        notes = st.text_area(
            "Additional Notes (Optional)",
            placeholder="Any special requirements or instructions"
        )
        
        if st.form_submit_button("Book Equipment", type="primary"):
            # Get renter ID from session state
            renter_id = st.session_state.get('user_id', 'renter_demo')
            
            booking_details = {
                'start_time': start_dt.isoformat(),
                'end_time': end_dt.isoformat(),
                'notes': notes
            }
            
            with st.spinner("Processing booking..."):
                result = equipment_tools.book_equipment(
                    renter_id,
                    equipment['resource_id'],
                    booking_details
                )
            
            if result['success']:
                st.success(f"✓ Equipment booked successfully! (Booking ID: {result['booking_id']})")
                st.info(f"Total Cost: ₹{result['total_cost']:.2f} + Insurance: ₹{result['insurance_premium']:.2f}")
                
                st.subheader("Pickup Instructions")
                st.text(result['pickup_instructions'])
                
                st.subheader("Next Steps")
                for i, step in enumerate(result['next_steps'], 1):
                    st.write(f"{i}. {step}")
                
                # Store booking in session state
                if 'my_bookings' not in st.session_state:
                    st.session_state.my_bookings = []
                st.session_state.my_bookings.append(result)
            else:
                st.error(f"Booking failed: {result.get('error')}")


def render_equipment_listing(equipment_tools):
    """Render equipment listing form"""
    
    st.header("List Your Equipment")
    st.markdown("Share your equipment and earn extra income")
    
    with st.form("equipment_listing_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            equipment_name = st.text_input(
                "Equipment Name",
                placeholder="e.g., John Deere Tractor",
                help="Name or brand of your equipment"
            )
            
            equipment_type = st.selectbox(
                "Equipment Type",
                ["tractor", "pump", "drone", "harvester", "plough", "sprayer", "thresher"],
                help="Type of agricultural equipment"
            )
            
            model = st.text_input(
                "Model (Optional)",
                placeholder="e.g., 5075E"
            )
            
            condition = st.selectbox(
                "Condition",
                ["excellent", "good", "fair"],
                help="Current condition of equipment"
            )
        
        with col2:
            hourly_rate = st.number_input(
                "Hourly Rate (₹)",
                min_value=0,
                max_value=10000,
                value=500,
                step=50,
                help="Rental rate per hour"
            )
            
            daily_rate = st.number_input(
                "Daily Rate (₹)",
                min_value=0,
                max_value=100000,
                value=3000,
                step=100,
                help="Rental rate per day"
            )
            
            year = st.text_input(
                "Year of Purchase (Optional)",
                placeholder="e.g., 2020"
            )
            
            capacity = st.text_input(
                "Capacity/Power (Optional)",
                placeholder="e.g., 75 HP"
            )
        
        st.subheader("Location Details")
        
        col3, col4 = st.columns(2)
        
        with col3:
            state = st.text_input("State", value="Punjab")
            district = st.text_input("District", value="Ludhiana")
            address = st.text_input("Address/Village", placeholder="Village name or landmark")
        
        with col4:
            latitude = st.number_input("Latitude", value=30.9010, format="%.4f")
            longitude = st.number_input("Longitude", value=75.8573, format="%.4f")
        
        st.subheader("Additional Details")
        
        specifications = st.text_area(
            "Specifications (Optional)",
            placeholder="Enter specifications in JSON format, e.g., {\"engine\": \"4-cylinder diesel\", \"transmission\": \"manual\"}",
            help="Technical specifications of the equipment"
        )
        
        pickup_instructions = st.text_area(
            "Pickup Instructions",
            placeholder="Contact details, timing, special instructions, etc.",
            help="Instructions for renters to pickup the equipment"
        )
        
        submitted = st.form_submit_button("List Equipment", type="primary")
        
        if submitted:
            if not equipment_name or not equipment_type:
                st.error("Equipment name and type are required")
            else:
                # Get owner ID from session state
                owner_id = st.session_state.get('user_id', 'owner_demo')
                
                # Parse specifications
                specs = {}
                if specifications:
                    try:
                        specs = json.loads(specifications)
                    except:
                        st.warning("Invalid specifications format, using empty specifications")
                
                equipment_data = {
                    'name': equipment_name,
                    'type': equipment_type,
                    'model': model,
                    'condition': condition,
                    'hourly_rate': hourly_rate,
                    'daily_rate': daily_rate,
                    'year': year,
                    'capacity': capacity,
                    'location': {
                        'state': state,
                        'district': district,
                        'address': address,
                        'latitude': latitude,
                        'longitude': longitude
                    },
                    'specifications': specs,
                    'pickup_instructions': pickup_instructions
                }
                
                with st.spinner("Listing equipment..."):
                    result = equipment_tools.list_equipment(owner_id, equipment_data)
                
                if result['success']:
                    st.success(f"✓ Equipment listed successfully! (ID: {result['resource_id']})")
                    st.info(f"Estimated Monthly Income: ₹{result['estimated_monthly_income']:.2f}")
                    st.balloons()
                else:
                    st.error(f"Failed to list equipment: {result.get('error')}")


def render_my_bookings(equipment_tools):
    """Render user's bookings"""
    
    st.header("My Bookings")
    
    if 'my_bookings' in st.session_state and st.session_state.my_bookings:
        st.markdown(f"Total Bookings: {len(st.session_state.my_bookings)}")
        
        for i, booking in enumerate(st.session_state.my_bookings, 1):
            with st.expander(f"Booking {i}: {booking['booking_id']}"):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.write(f"**Booking ID:** {booking['booking_id']}")
                    st.write(f"**Status:** {booking['status'].upper()}")
                    st.write(f"**Payment Status:** {booking['payment_status'].upper()}")
                
                with col_b:
                    st.write(f"**Total Cost:** ₹{booking['total_cost']:.2f}")
                    st.write(f"**Insurance:** ₹{booking['insurance_premium']:.2f}")
                
                if st.button(f"View Details {i}", key=f"booking_details_{i}"):
                    st.json(booking)
    else:
        st.info("No bookings yet. Search and book equipment to get started!")


def render_rating_review(equipment_tools):
    """Render rating and review interface"""
    
    st.header("Rate & Review Equipment")
    st.markdown("Share your experience to help other farmers")
    
    if 'my_bookings' in st.session_state and st.session_state.my_bookings:
        booking_options = [f"{b['booking_id']} - {b['status']}" for b in st.session_state.my_bookings]
        
        selected_booking = st.selectbox(
            "Select Booking to Rate",
            booking_options,
            help="Choose a completed booking to rate"
        )
        
        booking_id = selected_booking.split(' - ')[0]
        
        with st.form("rating_form"):
            equipment_rating = st.slider(
                "Equipment Rating",
                min_value=1,
                max_value=5,
                value=4,
                help="Rate the equipment quality and performance"
            )
            
            owner_rating = st.slider(
                "Owner Rating",
                min_value=1,
                max_value=5,
                value=4,
                help="Rate the owner's service and cooperation"
            )
            
            review = st.text_area(
                "Review (Optional)",
                placeholder="Share your experience with this equipment...",
                help="Your review will help other farmers make informed decisions"
            )
            
            if st.form_submit_button("Submit Rating", type="primary"):
                rating_data = {
                    'equipment_rating': equipment_rating,
                    'owner_rating': owner_rating,
                    'review': review
                }
                
                with st.spinner("Submitting rating..."):
                    result = equipment_tools.rate_equipment(booking_id, rating_data)
                
                if result['success']:
                    st.success("✓ Rating submitted successfully!")
                    st.info(f"New Average Rating: {result['new_average_rating']:.1f}/5 ({result['total_ratings']} ratings)")
                else:
                    st.error(f"Failed to submit rating: {result.get('error')}")
    else:
        st.info("No bookings available to rate. Complete a booking first!")


# Main function for standalone testing
if __name__ == '__main__':
    st.set_page_config(
        page_title="RISE - Equipment Marketplace",
        page_icon="🚜",
        layout="wide"
    )
    
    render_equipment_marketplace()
