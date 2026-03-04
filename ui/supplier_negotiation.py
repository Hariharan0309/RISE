"""
Streamlit UI for AI-Powered Supplier Negotiation
Provides interface for finding suppliers, generating requests, comparing quotes, and managing orders
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.supplier_negotiation_tools import create_supplier_negotiation_tools


def render_supplier_negotiation_ui():
    """Render the supplier negotiation interface"""
    st.title("🤝 AI-Powered Supplier Negotiation")
    st.markdown("Find suppliers, negotiate bulk pricing, and manage orders with AI assistance")
    
    # Initialize tools
    if 'supplier_tools' not in st.session_state:
        st.session_state.supplier_tools = create_supplier_negotiation_tools()
    
    tools = st.session_state.supplier_tools
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Find Suppliers",
        "📝 Generate Request",
        "💰 Compare Quotes",
        "✅ Quality Verification",
        "📦 Manage Orders"
    ])
    
    with tab1:
        render_find_suppliers_tab(tools)
    
    with tab2:
        render_generate_request_tab(tools)
    
    with tab3:
        render_compare_quotes_tab(tools)
    
    with tab4:
        render_quality_verification_tab(tools)
    
    with tab5:
        render_manage_orders_tab(tools)


def render_find_suppliers_tab(tools):
    """Render supplier search interface"""
    st.header("Find Suppliers")
    st.markdown("Search for verified suppliers based on your requirements")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Product Requirements")
        
        # Product selection
        product_type = st.selectbox(
            "Product Category",
            ["Seeds", "Fertilizers", "Pesticides", "Equipment", "Other"]
        )
        
        # Dynamic product input
        num_products = st.number_input("Number of products", min_value=1, max_value=10, value=1)
        
        product_requirements = {}
        for i in range(num_products):
            col_a, col_b = st.columns(2)
            with col_a:
                product_name = st.text_input(f"Product {i+1} Name", key=f"prod_name_{i}")
            with col_b:
                quantity = st.number_input(f"Quantity (kg/units)", min_value=1, value=100, key=f"prod_qty_{i}")
            
            if product_name:
                product_requirements[product_name.lower().replace(' ', '_')] = quantity
    
    with col2:
        st.subheader("Location")
        
        state = st.text_input("State", value="Punjab")
        district = st.text_input("District", value="Ludhiana")
        
        location = {
            'state': state,
            'district': district
        }
    
    if st.button("🔍 Search Suppliers", type="primary"):
        if not product_requirements:
            st.error("Please specify at least one product")
        else:
            with st.spinner("Searching for suppliers..."):
                result = tools.find_suppliers(product_requirements, location)
                
                if result['success']:
                    st.success(f"Found {result['count']} matching suppliers!")
                    
                    if result['suppliers']:
                        st.subheader("Matching Suppliers")
                        
                        for supplier in result['suppliers']:
                            with st.expander(
                                f"⭐ {supplier['business_name']} - Match Score: {supplier['match_score']}"
                            ):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write(f"**Supplier ID:** {supplier['supplier_id']}")
                                    st.write(f"**Type:** {supplier['supplier_type']}")
                                    st.write(f"**Contact:** {supplier['contact_person']}")
                                    st.write(f"**Phone:** {supplier['phone_number']}")
                                    if supplier['email']:
                                        st.write(f"**Email:** {supplier['email']}")
                                
                                with col2:
                                    st.write(f"**Location:** {supplier['location']['district']}, {supplier['location']['state']}")
                                    st.write(f"**Rating:** {supplier['ratings']['average']:.1f}/5.0 ({supplier['ratings']['count']} reviews)")
                                    st.write(f"**Meets MOQ:** {'✅ Yes' if supplier['meets_moq'] else '❌ No'}")
                                    st.write(f"**Bulk Discount:** {'✅ Available' if supplier['bulk_discount_available'] else '❌ Not Available'}")
                                
                                st.write(f"**Matching Products:** {', '.join(supplier['matching_products'])}")
                                
                                if supplier['certifications']:
                                    st.write(f"**Certifications:** {', '.join(supplier['certifications'])}")
                                
                                if supplier['payment_terms']:
                                    st.write(f"**Payment Terms:** {', '.join(supplier['payment_terms'])}")
                                
                                # Store supplier ID for later use
                                if st.button(f"Select {supplier['business_name']}", key=f"select_{supplier['supplier_id']}"):
                                    if 'selected_suppliers' not in st.session_state:
                                        st.session_state.selected_suppliers = []
                                    if supplier['supplier_id'] not in st.session_state.selected_suppliers:
                                        st.session_state.selected_suppliers.append(supplier['supplier_id'])
                                        st.success(f"Added {supplier['business_name']} to selection")
                    else:
                        st.info("No suppliers found matching your criteria")
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")


def render_generate_request_tab(tools):
    """Render bulk pricing request generation interface"""
    st.header("Generate Bulk Pricing Request")
    st.markdown("Use AI to generate professional pricing requests for suppliers")
    
    # Check if suppliers are selected
    if 'selected_suppliers' not in st.session_state or not st.session_state.selected_suppliers:
        st.warning("⚠️ Please select suppliers from the 'Find Suppliers' tab first")
        return
    
    st.success(f"✅ {len(st.session_state.selected_suppliers)} supplier(s) selected")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Buyer Information")
        buyer_id = st.text_input("Buyer/Group ID", value="buyer_12345")
        
        st.subheader("Product Requirements")
        num_products = st.number_input("Number of products", min_value=1, max_value=10, value=2, key="gen_num_prod")
        
        product_requirements = {}
        for i in range(num_products):
            col_a, col_b = st.columns(2)
            with col_a:
                product_name = st.text_input(f"Product {i+1}", key=f"gen_prod_{i}", value=f"wheat_seeds" if i == 0 else "fertilizer_urea")
            with col_b:
                quantity = st.number_input(f"Quantity", min_value=1, value=500 if i == 0 else 300, key=f"gen_qty_{i}")
            
            if product_name:
                product_requirements[product_name] = quantity
    
    with col2:
        st.subheader("Delivery Location")
        del_state = st.text_input("State", value="Punjab", key="del_state")
        del_district = st.text_input("District", value="Ludhiana", key="del_district")
        del_address = st.text_area("Detailed Address (Optional)", key="del_address")
        
        delivery_location = {
            'state': del_state,
            'district': del_district,
            'address': del_address
        }
    
    if st.button("🤖 Generate AI Request", type="primary"):
        if not buyer_id or not product_requirements:
            st.error("Please fill in all required fields")
        else:
            with st.spinner("Generating AI-powered pricing request..."):
                result = tools.generate_bulk_pricing_request(
                    buyer_id,
                    product_requirements,
                    st.session_state.selected_suppliers,
                    delivery_location
                )
                
                if result['success']:
                    st.success("✅ Bulk pricing request generated successfully!")
                    
                    # Store negotiation ID
                    st.session_state.current_negotiation_id = result['negotiation_id']
                    
                    st.info(f"**Negotiation ID:** {result['negotiation_id']}")
                    st.info(f"**Suppliers Contacted:** {result['suppliers_contacted']}")
                    st.info(f"**Status:** {result['status']}")
                    st.info(f"**Deadline:** {result['deadline']}")
                    
                    st.subheader("📧 Generated Request Message")
                    st.text_area(
                        "Request Message (Ready to send)",
                        value=result['request_message'],
                        height=400,
                        key="generated_message"
                    )
                    
                    st.subheader("Next Steps")
                    for i, step in enumerate(result['next_steps'], 1):
                        st.write(f"{i}. {step}")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Request Message",
                        data=result['request_message'],
                        file_name=f"pricing_request_{result['negotiation_id']}.txt",
                        mime="text/plain"
                    )
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")


def render_compare_quotes_tab(tools):
    """Render quote comparison interface"""
    st.header("Compare Supplier Quotes")
    st.markdown("AI-powered analysis to help you select the best supplier")
    
    # Check if negotiation exists
    if 'current_negotiation_id' not in st.session_state:
        st.warning("⚠️ Please generate a pricing request first")
        
        # Allow manual entry
        st.subheader("Or enter Negotiation ID manually")
        manual_neg_id = st.text_input("Negotiation ID")
        if st.button("Load Negotiation"):
            st.session_state.current_negotiation_id = manual_neg_id
            st.rerun()
        return
    
    negotiation_id = st.session_state.current_negotiation_id
    st.info(f"**Current Negotiation:** {negotiation_id}")
    
    # Simulate quote submission for demo
    with st.expander("📝 Simulate Quote Submission (For Testing)"):
        st.markdown("*In production, suppliers would submit quotes through their portal*")
        
        supplier_id = st.text_input("Supplier ID", value="sup_12345678")
        
        col1, col2 = st.columns(2)
        with col1:
            product1_price = st.number_input("Wheat Seeds Price (per kg)", value=45.0)
            product2_price = st.number_input("Fertilizer Price (per kg)", value=25.0)
        
        with col2:
            discount_pct = st.number_input("Discount %", value=20.0)
            total_amount = st.number_input("Total Amount", value=35000.0)
        
        delivery_timeline = st.text_input("Delivery Timeline", value="7-10 days")
        payment_terms = st.selectbox("Payment Terms", ["on_delivery", "advance_50", "credit_30_days"])
        
        if st.button("Submit Test Quote"):
            quote_data = {
                'product_pricing': {
                    'wheat_seeds': product1_price,
                    'fertilizer_urea': product2_price
                },
                'discount_percentage': discount_pct,
                'total_amount': total_amount,
                'delivery_timeline': delivery_timeline,
                'payment_terms': payment_terms,
                'quality_certifications': ['ISO 9001', 'Quality Assurance']
            }
            
            result = tools.submit_supplier_quote(negotiation_id, supplier_id, quote_data)
            if result['success']:
                st.success(f"Quote submitted! ({result['quotes_received']}/{result['total_suppliers']} received)")
    
    st.divider()
    
    if st.button("🔍 Compare All Quotes", type="primary"):
        with st.spinner("Analyzing quotes with AI..."):
            result = tools.compare_quotes(negotiation_id)
            
            if result['success']:
                st.success(f"✅ Analyzed {result['quotes_count']} quotes")
                
                # Display statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Best Price", f"₹{result['best_price']:,.2f}")
                with col2:
                    st.metric("Best Discount", f"{result['best_discount']}%")
                with col3:
                    st.metric("Average Price", f"₹{result['average_price']:,.2f}")
                
                # Display recommended quote
                if result['recommended_quote']:
                    st.subheader("🏆 Recommended Supplier")
                    rec = result['recommended_quote']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Supplier:** {rec['supplier_name']}")
                        st.write(f"**Total Amount:** ₹{rec['total_amount']:,.2f}")
                        st.write(f"**Discount:** {rec['discount_percentage']}%")
                        st.write(f"**Rating:** {rec['supplier_rating']:.1f}/5.0")
                    
                    with col2:
                        st.write(f"**Payment Terms:** {rec['payment_terms']}")
                        st.write(f"**Delivery:** {rec['delivery_timeline']}")
                        st.write(f"**Certifications:** {', '.join(rec['quality_certifications'])}")
                    
                    if st.button("✅ Select This Supplier", type="primary"):
                        st.session_state.selected_quote_id = rec['quote_id']
                        st.success("Supplier selected! Proceed to delivery coordination.")
                
                # Display AI analysis
                st.subheader("🤖 AI Analysis")
                st.markdown(result['ai_analysis'])
                
                # Display all quotes
                st.subheader("All Quotes Received")
                for i, quote in enumerate(result['ranked_quotes'], 1):
                    with st.expander(f"#{i} - {quote['supplier_name']} - ₹{quote['total_amount']:,.2f}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Total Amount:** ₹{quote['total_amount']:,.2f}")
                            st.write(f"**Discount:** {quote['discount_percentage']}%")
                            st.write(f"**Payment Terms:** {quote['payment_terms']}")
                        
                        with col2:
                            st.write(f"**Delivery:** {quote['delivery_timeline']}")
                            st.write(f"**Rating:** {quote['supplier_rating']:.1f}/5.0")
                            st.write(f"**Certifications:** {', '.join(quote['quality_certifications'])}")
                        
                        st.write("**Product Pricing:**")
                        for product, price in quote['product_pricing'].items():
                            st.write(f"  • {product}: ₹{price}/unit")
            else:
                st.error(f"Error: {result.get('error', 'Unknown error')}")


def render_quality_verification_tab(tools):
    """Render quality verification interface"""
    st.header("Quality Assurance Verification")
    st.markdown("Verify supplier certifications and quality standards")
    
    col1, col2 = st.columns(2)
    
    with col1:
        supplier_id = st.text_input("Supplier ID", value="sup_12345678")
    
    with col2:
        product_name = st.text_input("Product Name", value="wheat_seeds")
    
    if st.button("🔍 Verify Quality", type="primary"):
        with st.spinner("Verifying quality standards..."):
            result = tools.verify_quality_assurance(supplier_id, product_name)
            
            if result['success']:
                st.success("✅ Quality verification completed")
                
                # Display overall status
                status_color = "🟢" if result['overall_status'] == 'verified' else "🟡"
                st.subheader(f"{status_color} Overall Status: {result['overall_status'].upper()}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Compliance Score", f"{result['compliance_score']}%")
                
                with col2:
                    st.write(f"**Supplier:** {result['supplier_name']}")
                    st.write(f"**Product:** {result['product_name']}")
                
                # Display certifications
                st.subheader("Certifications")
                if result['certifications']:
                    for cert in result['certifications']:
                        st.write(f"✅ {cert}")
                else:
                    st.warning("No certifications on file")
                
                # Display verification checks
                st.subheader("Verification Checks")
                for check in result['verification_checks']:
                    status_icon = "✅" if check['status'] == 'pass' else "❌"
                    required_text = " (Required)" if check['required'] else ""
                    st.write(f"{status_icon} {check['certification']}{required_text}")
                
                # Display quality standards
                if result['quality_standards']:
                    st.subheader("Quality Standards")
                    st.json(result['quality_standards'])
            else:
                st.error(f"Error: {result.get('error', 'Unknown error')}")


def render_manage_orders_tab(tools):
    """Render order management interface"""
    st.header("Manage Orders")
    st.markdown("Coordinate delivery and manage payments")
    
    # Check if quote is selected
    if 'selected_quote_id' not in st.session_state:
        st.warning("⚠️ Please select a supplier quote from the 'Compare Quotes' tab first")
        return
    
    if 'current_negotiation_id' not in st.session_state:
        st.warning("⚠️ No active negotiation found")
        return
    
    negotiation_id = st.session_state.current_negotiation_id
    selected_quote_id = st.session_state.selected_quote_id
    
    st.success(f"✅ Quote selected: {selected_quote_id}")
    
    # Delivery coordination
    st.subheader("📦 Delivery Coordination")
    
    col1, col2 = st.columns(2)
    
    with col1:
        delivery_date = st.date_input(
            "Delivery Date",
            value=datetime.now() + timedelta(days=7)
        )
        delivery_time = st.selectbox(
            "Time Slot",
            ["Morning (8AM-12PM)", "Afternoon (12PM-4PM)", "Evening (4PM-8PM)"]
        )
    
    with col2:
        contact_name = st.text_input("Contact Person", value="Farmer Name")
        contact_phone = st.text_input("Contact Phone", value="+91-9876543210")
    
    special_instructions = st.text_area(
        "Special Instructions",
        placeholder="Any specific delivery instructions..."
    )
    
    if st.button("📦 Schedule Delivery", type="primary"):
        delivery_details = {
            'delivery_date': delivery_date.isoformat(),
            'delivery_time_slot': delivery_time,
            'delivery_contact': {
                'name': contact_name,
                'phone': contact_phone
            },
            'special_instructions': special_instructions
        }
        
        with st.spinner("Coordinating delivery..."):
            result = tools.coordinate_delivery(negotiation_id, selected_quote_id, delivery_details)
            
            if result['success']:
                st.success("✅ Delivery scheduled successfully!")
                
                st.info(f"**Delivery ID:** {result['delivery_id']}")
                st.info(f"**Tracking Number:** {result['tracking_number']}")
                st.info(f"**Delivery Date:** {result['delivery_date']}")
                st.info(f"**Status:** {result['delivery_status']}")
                
                st.subheader("Next Steps")
                for i, step in enumerate(result['next_steps'], 1):
                    st.write(f"{i}. {step}")
                
                # Store delivery ID
                st.session_state.delivery_id = result['delivery_id']
            else:
                st.error(f"Error: {result.get('error', 'Unknown error')}")
    
    st.divider()
    
    # Payment management
    st.subheader("💰 Payment Management")
    
    payment_method = st.selectbox(
        "Payment Method",
        ["Bank Transfer", "UPI", "Cash on Delivery", "Cheque"]
    )
    
    payment_terms = st.selectbox(
        "Payment Terms",
        ["Full payment on delivery", "50% advance, 50% on delivery", "30 days credit"]
    )
    
    # Group payment option
    is_group_purchase = st.checkbox("This is a group purchase")
    
    member_contributions = {}
    if is_group_purchase:
        st.subheader("Member Contributions")
        num_members = st.number_input("Number of members", min_value=1, max_value=50, value=5)
        
        for i in range(num_members):
            col_a, col_b = st.columns(2)
            with col_a:
                member_id = st.text_input(f"Member {i+1} ID", key=f"mem_id_{i}", value=f"farmer_{i+1}")
            with col_b:
                amount = st.number_input(f"Amount (₹)", min_value=0.0, value=7000.0, key=f"mem_amt_{i}")
            
            if member_id:
                member_contributions[member_id] = amount
    
    if st.button("💳 Setup Payment", type="primary"):
        payment_data = {
            'payment_method': payment_method.lower().replace(' ', '_'),
            'payment_terms': payment_terms
        }
        
        if is_group_purchase and member_contributions:
            payment_data['member_contributions'] = member_contributions
        
        with st.spinner("Setting up payment..."):
            result = tools.manage_payment(negotiation_id, payment_data)
            
            if result['success']:
                st.success("✅ Payment setup completed!")
                
                st.info(f"**Payment ID:** {result['payment_id']}")
                st.info(f"**Total Amount:** ₹{result['total_amount']:,.2f}")
                st.info(f"**Payment Status:** {result['payment_status']}")
                st.info(f"**Payment Method:** {result['payment_method']}")
                
                if result.get('member_count', 0) > 0:
                    st.info(f"**Group Members:** {result['member_count']}")
                
                st.subheader("Next Steps")
                for i, step in enumerate(result['next_steps'], 1):
                    st.write(f"{i}. {step}")
            else:
                st.error(f"Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    render_supplier_negotiation_ui()
