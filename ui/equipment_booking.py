"""
RISE Equipment Booking Management UI
Streamlit UI component for comprehensive booking management
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.equipment_sharing_tools import create_equipment_sharing_tools
from datetime import datetime, timedelta
import json


def render_equipment_booking_management():
    """Render the equipment booking management interface"""
    
    st.title("📅 Equipment Booking Management")
    st.markdown("Manage your equipment bookings, payments, and usage tracking")
    
    # Initialize tools
    if 'equipment_tools' not in st.session_state:
        st.session_state.equipment_tools = create_equipment_sharing_tools()
    
    equipment_tools = st.session_state.equipment_tools
    
    # Create tabs for different features
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 My Bookings",
        "💳 Payment Processing",
        "📊 Usage Tracking",
        "🔍 Booking Details",
        "❌ Cancel Booking"
    ])
    
    # Tab 1: My Bookings
    with tab1:
        render_my_bookings(equipment_tools)
    
    # Tab 2: Payment Processing
    with tab2:
        render_payment_processing(equipment_tools)
    
    # Tab 3: Usage Tracking
    with tab3:
        render_usage_tracking(equipment_tools)
    
    # Tab 4: Booking Details
    with tab4:
        render_booking_details(equipment_tools)
    
    # Tab 5: Cancel Booking
    with tab5:
        render_cancel_booking(equipment_tools)


def render_my_bookings(equipment_tools):
    """Render user's bookings list"""
    
    st.header("My Bookings")
    
    # User selection
    col1, col2 = st.columns(2)
    
    with col1:
        user_id = st.text_input(
            "User ID",
            value=st.session_state.get('user_id', 'farmer_12345'),
            help="Enter your user ID"
        )
    
    with col2:
        booking_type = st.selectbox(
            "Booking Type",
            ["renter", "owner"],
            help="View bookings as renter or equipment owner"
        )
    
    if st.button("Load My Bookings", type="primary"):
        with st.spinner("Loading bookings..."):
            result = equipment_tools.get_user_bookings(user_id, booking_type)
        
        if result['success']:
            st.success(f"✓ Found {result['count']} bookings")
            
            if result['bookings']:
                # Store in session state
                st.session_state.user_bookings = result['bookings']
                st.session_state.current_user_id = user_id
                st.session_state.current_booking_type = booking_type
            else:
                st.info("No bookings found")
        else:
            st.error(f"Failed to load bookings: {result.get('error')}")
    
    # Display bookings
    if 'user_bookings' in st.session_state and st.session_state.user_bookings:
        st.subheader(f"Bookings ({len(st.session_state.user_bookings)})")
        
        # Filter options
        status_filter = st.multiselect(
            "Filter by Status",
            ["confirmed", "paid", "in_use", "completed", "cancelled"],
            default=["confirmed", "paid", "in_use"]
        )
        
        filtered_bookings = [
            b for b in st.session_state.user_bookings
            if b['status'] in status_filter
        ]
        
        if filtered_bookings:
            for booking in filtered_bookings:
                with st.expander(
                    f"🚜 {booking['equipment_name']} - {booking['status'].upper()}",
                    expanded=False
                ):
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.write(f"**Booking ID:** {booking['booking_id']}")
                        st.write(f"**Equipment:** {booking['equipment_name']}")
                        st.write(f"**Type:** {booking['equipment_type'].title()}")
                    
                    with col_b:
                        start_date = datetime.fromisoformat(booking['booking_start'])
                        end_date = datetime.fromisoformat(booking['booking_end'])
                        st.write(f"**Start:** {start_date.strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"**End:** {end_date.strftime('%Y-%m-%d %H:%M')}")
                        duration = (end_date - start_date).total_seconds() / 3600
                        st.write(f"**Duration:** {duration:.1f} hours")
                    
                    with col_c:
                        st.write(f"**Total Cost:** ₹{booking['total_cost']:.2f}")
                        st.write(f"**Final Amount:** ₹{booking['final_amount']:.2f}")
                        st.write(f"**Payment:** {booking['payment_status'].upper()}")
                    
                    st.write(f"**Status:** {booking['status'].upper()}")
                    st.write(f"**Delivery:** {booking['delivery_status'].upper()}")
                    
                    # Action buttons
                    col_1, col_2, col_3 = st.columns(3)
                    
                    with col_1:
                        if booking['payment_status'] == 'pending':
                            if st.button("💳 Pay Now", key=f"pay_{booking['booking_id']}"):
                                st.session_state.payment_booking_id = booking['booking_id']
                                st.session_state.payment_amount = booking['final_amount']
                                st.info("Switch to 'Payment Processing' tab to complete payment")
                    
                    with col_2:
                        if booking['status'] in ['paid', 'in_use']:
                            if st.button("📊 Track Usage", key=f"track_{booking['booking_id']}"):
                                st.session_state.tracking_booking_id = booking['booking_id']
                                st.info("Switch to 'Usage Tracking' tab to update usage")
                    
                    with col_3:
                        if booking['status'] not in ['completed', 'cancelled']:
                            if st.button("❌ Cancel", key=f"cancel_{booking['booking_id']}"):
                                st.session_state.cancel_booking_id = booking['booking_id']
                                st.info("Switch to 'Cancel Booking' tab to proceed")
        else:
            st.info("No bookings match the selected filters")


def render_payment_processing(equipment_tools):
    """Render payment processing interface"""
    
    st.header("Payment Processing")
    st.markdown("Complete payment for your equipment booking")
    
    # Pre-fill from session state if available
    default_booking_id = st.session_state.get('payment_booking_id', '')
    default_amount = st.session_state.get('payment_amount', 0)
    
    with st.form("payment_form"):
        booking_id = st.text_input(
            "Booking ID",
            value=default_booking_id,
            help="Enter the booking ID to process payment"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            payment_method = st.selectbox(
                "Payment Method",
                ["upi", "card", "netbanking", "wallet"],
                help="Select your preferred payment method"
            )
            
            amount = st.number_input(
                "Amount (₹)",
                min_value=0.0,
                value=float(default_amount),
                step=100.0,
                help="Enter the payment amount"
            )
        
        with col2:
            payment_reference = st.text_input(
                "Payment Reference (Optional)",
                placeholder="e.g., UPI transaction ID",
                help="Enter payment reference for tracking"
            )
            
            st.write("")
            st.write("")
            st.info(f"**Amount to Pay:** ₹{amount:.2f}")
        
        submitted = st.form_submit_button("Process Payment", type="primary")
        
        if submitted:
            if not booking_id:
                st.error("Booking ID is required")
            elif amount <= 0:
                st.error("Amount must be greater than 0")
            else:
                payment_details = {
                    'amount': amount,
                    'payment_method': payment_method,
                    'reference': payment_reference
                }
                
                with st.spinner("Processing payment..."):
                    result = equipment_tools.process_payment(booking_id, payment_details)
                
                if result['success']:
                    st.success("✓ Payment processed successfully!")
                    
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.info(f"**Transaction ID:** {result['transaction_id']}")
                        st.info(f"**Booking ID:** {result['booking_id']}")
                    
                    with col_b:
                        st.info(f"**Amount Paid:** ₹{result['amount_paid']:.2f}")
                        st.info(f"**Payment Method:** {result['payment_method'].upper()}")
                    
                    st.balloons()
                    
                    # Clear session state
                    if 'payment_booking_id' in st.session_state:
                        del st.session_state.payment_booking_id
                    if 'payment_amount' in st.session_state:
                        del st.session_state.payment_amount
                else:
                    st.error(f"Payment failed: {result.get('error')}")


def render_usage_tracking(equipment_tools):
    """Render usage tracking interface"""
    
    st.header("Usage Tracking")
    st.markdown("Track equipment usage with meter readings")
    
    # Pre-fill from session state if available
    default_booking_id = st.session_state.get('tracking_booking_id', '')
    
    with st.form("usage_tracking_form"):
        booking_id = st.text_input(
            "Booking ID",
            value=default_booking_id,
            help="Enter the booking ID to track usage"
        )
        
        st.subheader("Update Readings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Start of Usage**")
            
            update_start = st.checkbox("Update Start Reading")
            
            start_reading = 0
            actual_start_time = None
            
            if update_start:
                start_reading = st.number_input(
                    "Start Reading (hours/km)",
                    min_value=0,
                    value=0,
                    step=1,
                    help="Enter the meter reading at start"
                )
                
                actual_start_time = st.datetime_input(
                    "Actual Start Time",
                    value=datetime.now(),
                    help="When did you actually start using the equipment?"
                )
        
        with col2:
            st.markdown("**End of Usage**")
            
            update_end = st.checkbox("Update End Reading")
            
            end_reading = 0
            actual_end_time = None
            
            if update_end:
                end_reading = st.number_input(
                    "End Reading (hours/km)",
                    min_value=0,
                    value=0,
                    step=1,
                    help="Enter the meter reading at end"
                )
                
                actual_end_time = st.datetime_input(
                    "Actual End Time",
                    value=datetime.now(),
                    help="When did you finish using the equipment?"
                )
        
        submitted = st.form_submit_button("Update Usage Tracking", type="primary")
        
        if submitted:
            if not booking_id:
                st.error("Booking ID is required")
            elif not update_start and not update_end:
                st.error("Please select at least one reading to update")
            else:
                usage_data = {}
                
                if update_start:
                    usage_data['start_reading'] = start_reading
                    if actual_start_time:
                        usage_data['actual_start_time'] = actual_start_time.isoformat()
                
                if update_end:
                    usage_data['end_reading'] = end_reading
                    if actual_end_time:
                        usage_data['actual_end_time'] = actual_end_time.isoformat()
                
                with st.spinner("Updating usage tracking..."):
                    result = equipment_tools.update_usage_tracking(booking_id, usage_data)
                
                if result['success']:
                    st.success("✓ Usage tracking updated successfully!")
                    
                    tracking = result['usage_tracking']
                    
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.metric("Start Reading", tracking.get('start_reading', 0))
                    
                    with col_b:
                        st.metric("End Reading", tracking.get('end_reading', 0))
                    
                    with col_c:
                        hours_used = tracking.get('hours_used', 0)
                        st.metric("Hours Used", f"{hours_used:.1f}")
                    
                    # Clear session state
                    if 'tracking_booking_id' in st.session_state:
                        del st.session_state.tracking_booking_id
                else:
                    st.error(f"Update failed: {result.get('error')}")


def render_booking_details(equipment_tools):
    """Render detailed booking information"""
    
    st.header("Booking Details")
    st.markdown("View comprehensive booking information")
    
    booking_id = st.text_input(
        "Booking ID",
        placeholder="e.g., book_abc12345",
        help="Enter the booking ID to view details"
    )
    
    if st.button("Get Booking Details", type="primary"):
        if not booking_id:
            st.error("Booking ID is required")
        else:
            with st.spinner("Fetching booking details..."):
                result = equipment_tools.get_booking_details(booking_id)
            
            if result['success']:
                st.success("✓ Booking details retrieved")
                
                booking = result['booking']
                equipment = result['equipment']
                
                # Equipment Information
                st.subheader("🚜 Equipment Information")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Name:** {equipment['name']}")
                    st.write(f"**Type:** {equipment['type'].title()}")
                    st.write(f"**Model:** {equipment.get('model', 'N/A')}")
                
                with col2:
                    location = equipment.get('location', {})
                    st.write(f"**Location:** {location.get('district', 'N/A')}, {location.get('state', 'N/A')}")
                
                st.divider()
                
                # Booking Information
                st.subheader("📅 Booking Information")
                
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.write(f"**Booking ID:** {booking['booking_id']}")
                    st.write(f"**Resource ID:** {booking['resource_id']}")
                    st.write(f"**Renter ID:** {booking['renter_user_id']}")
                    st.write(f"**Owner ID:** {booking['owner_user_id']}")
                
                with col_b:
                    start_dt = datetime.fromisoformat(booking['booking_start'])
                    end_dt = datetime.fromisoformat(booking['booking_end'])
                    st.write(f"**Start:** {start_dt.strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**End:** {end_dt.strftime('%Y-%m-%d %H:%M')}")
                    duration = (end_dt - start_dt).total_seconds() / 3600
                    st.write(f"**Duration:** {duration:.1f} hours")
                
                with col_c:
                    st.write(f"**Status:** {booking['status'].upper()}")
                    st.write(f"**Payment Status:** {booking['payment_status'].upper()}")
                    st.write(f"**Delivery Status:** {booking['delivery_status'].upper()}")
                
                st.divider()
                
                # Cost Breakdown
                st.subheader("💰 Cost Breakdown")
                
                col_1, col_2, col_3, col_4 = st.columns(4)
                
                with col_1:
                    st.metric("Equipment Cost", f"₹{booking['total_cost']:.2f}")
                
                with col_2:
                    st.metric("Insurance", f"₹{booking['insurance_premium']:.2f}")
                
                with col_3:
                    st.metric("Transport", f"₹{booking['transport_cost']:.2f}")
                
                with col_4:
                    st.metric("Final Amount", f"₹{booking['final_amount']:.2f}", delta=None)
                
                st.divider()
                
                # Payment Details
                if booking['payment_details']:
                    st.subheader("💳 Payment Details")
                    
                    payment = booking['payment_details']
                    
                    col_x, col_y = st.columns(2)
                    
                    with col_x:
                        st.write(f"**Transaction ID:** {payment.get('transaction_id', 'N/A')}")
                        st.write(f"**Payment Method:** {payment.get('payment_method', 'N/A').upper()}")
                    
                    with col_y:
                        if payment.get('payment_timestamp'):
                            payment_time = datetime.fromtimestamp(payment['payment_timestamp'])
                            st.write(f"**Payment Time:** {payment_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"**Amount Paid:** ₹{float(payment.get('amount_paid', 0)):.2f}")
                    
                    st.divider()
                
                # Usage Tracking
                st.subheader("📊 Usage Tracking")
                
                usage = booking['usage_tracking']
                
                col_i, col_ii, col_iii = st.columns(3)
                
                with col_i:
                    st.metric("Start Reading", usage.get('start_reading', 0))
                
                with col_ii:
                    st.metric("End Reading", usage.get('end_reading', 0))
                
                with col_iii:
                    st.metric("Hours Used", f"{usage.get('hours_used', 0):.1f}")
                
                if usage.get('actual_start_time'):
                    st.write(f"**Actual Start:** {usage['actual_start_time']}")
                
                if usage.get('actual_end_time'):
                    st.write(f"**Actual End:** {usage['actual_end_time']}")
                
                st.divider()
                
                # Insurance Details
                st.subheader("🛡️ Insurance Details")
                
                insurance = booking['insurance_details']
                
                col_p, col_q = st.columns(2)
                
                with col_p:
                    st.write(f"**Policy Number:** {insurance.get('policy_number', 'N/A')}")
                    st.write(f"**Coverage Amount:** ₹{float(insurance.get('coverage_amount', 0)):.2f}")
                
                with col_q:
                    st.write(f"**Premium:** ₹{float(insurance.get('premium', 0)):.2f}")
                    st.write(f"**Verified:** {'✓ Yes' if insurance.get('verified') else '✗ No'}")
                
                # Raw JSON view
                with st.expander("View Raw JSON"):
                    st.json(result)
            else:
                st.error(f"Failed to fetch details: {result.get('error')}")


def render_cancel_booking(equipment_tools):
    """Render booking cancellation interface"""
    
    st.header("Cancel Booking")
    st.markdown("Cancel your equipment booking and process refund")
    
    # Pre-fill from session state if available
    default_booking_id = st.session_state.get('cancel_booking_id', '')
    
    st.warning("⚠️ Cancellation Policy:")
    st.markdown("""
    - **24+ hours before start:** Full refund
    - **12-24 hours before start:** 50% refund
    - **Less than 12 hours:** No refund
    """)
    
    with st.form("cancellation_form"):
        booking_id = st.text_input(
            "Booking ID",
            value=default_booking_id,
            help="Enter the booking ID to cancel"
        )
        
        cancellation_reason = st.text_area(
            "Cancellation Reason",
            placeholder="Please provide a reason for cancellation...",
            help="Explain why you're cancelling this booking"
        )
        
        confirm_cancel = st.checkbox(
            "I understand the cancellation policy and want to proceed",
            help="Check this box to confirm cancellation"
        )
        
        submitted = st.form_submit_button("Cancel Booking", type="primary")
        
        if submitted:
            if not booking_id:
                st.error("Booking ID is required")
            elif not confirm_cancel:
                st.error("Please confirm that you understand the cancellation policy")
            else:
                with st.spinner("Processing cancellation..."):
                    result = equipment_tools.cancel_booking(booking_id, cancellation_reason)
                
                if result['success']:
                    st.success("✓ Booking cancelled successfully!")
                    
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.info(f"**Booking ID:** {result['booking_id']}")
                        st.info(f"**Status:** {result['status'].upper()}")
                    
                    with col_b:
                        st.info(f"**Refund Amount:** ₹{result['refund_amount']:.2f}")
                    
                    st.info(result['message'])
                    
                    # Clear session state
                    if 'cancel_booking_id' in st.session_state:
                        del st.session_state.cancel_booking_id
                else:
                    st.error(f"Cancellation failed: {result.get('error')}")


# Main function for standalone testing
if __name__ == '__main__':
    st.set_page_config(
        page_title="RISE - Booking Management",
        page_icon="📅",
        layout="wide"
    )
    
    render_equipment_booking_management()
