"""
RISE Scheme Application UI Component
Streamlit interface for scheme application assistance and tracking
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.scheme_application_tools import SchemeApplicationTools


def render_scheme_application():
    """Render the scheme application interface"""
    st.header("📝 Scheme Application Assistant")
    st.markdown("Voice-guided application assistance with document validation and status tracking")
    
    # Initialize tools
    if 'application_tools' not in st.session_state:
        st.session_state.application_tools = SchemeApplicationTools()
    
    tools = st.session_state.application_tools
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧭 Application Wizard", 
        "📄 Document Validation", 
        "📤 Submit Application",
        "📊 Track Status"
    ])
    
    with tab1:
        render_application_wizard(tools)
    
    with tab2:
        render_document_validation(tools)
    
    with tab3:
        render_application_submission(tools)
    
    with tab4:
        render_status_tracking(tools)


def render_application_wizard(tools: SchemeApplicationTools):
    """Render application wizard section"""
    st.subheader("Voice-Guided Application Wizard")
    st.markdown("Step-by-step guidance for completing your scheme application")
    
    # Check if scheme is selected
    if 'selected_scheme_id' not in st.session_state:
        st.info("💡 Please select a scheme from the Scheme Discovery page first")
        
        # Manual scheme ID input
        scheme_id = st.text_input("Or enter Scheme ID manually", placeholder="SCH_XXXXXXXXXXXX")
        
        if scheme_id:
            st.session_state.selected_scheme_id = scheme_id
    else:
        scheme_id = st.session_state.selected_scheme_id
    
    # User ID input
    user_id = st.text_input("User ID", value=st.session_state.get('user_id', 'user_12345'))
    
    # Language selection
    language = st.selectbox(
        "Preferred Language for Voice Guidance",
        ["Hindi (हिंदी)", "English", "Tamil (தமிழ்)", "Telugu (తెలుగు)", 
         "Kannada (ಕನ್ನಡ)", "Bengali (বাংলা)", "Gujarati (ગુજરાતી)", 
         "Marathi (मराठी)", "Punjabi (ਪੰਜਾਬੀ)"]
    )
    
    language_codes = {
        "Hindi (हिंदी)": "hi",
        "English": "en",
        "Tamil (தமிழ்)": "ta",
        "Telugu (తెలుగు)": "te",
        "Kannada (ಕನ್ನಡ)": "kn",
        "Bengali (বাংলা)": "bn",
        "Gujarati (ગુજરાતી)": "gu",
        "Marathi (मराठी)": "mr",
        "Punjabi (ਪੰਜਾਬੀ)": "pa"
    }
    
    lang_code = language_codes[language]
    
    if st.button("🚀 Start Application Wizard", type="primary"):
        if not scheme_id:
            st.error("Please select or enter a scheme ID")
            return
        
        with st.spinner("Generating personalized application wizard..."):
            result = tools.generate_application_wizard(user_id, scheme_id, lang_code)
            
            if result['success']:
                st.success(f"✅ Wizard generated for {result['scheme_name']}")
                
                # Display wizard overview
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Steps", result['total_steps'])
                
                with col2:
                    st.metric("Estimated Time", f"{result['estimated_time_minutes']} min")
                
                with col3:
                    st.metric("Language", language)
                
                st.markdown("---")
                
                # Display wizard steps
                wizard_steps = result['wizard_steps']
                
                # Progress tracker
                if 'current_step' not in st.session_state:
                    st.session_state.current_step = 0
                
                current_step = st.session_state.current_step
                
                # Progress bar
                progress = (current_step + 1) / len(wizard_steps)
                st.progress(progress)
                st.caption(f"Step {current_step + 1} of {len(wizard_steps)}")
                
                # Display current step
                step = wizard_steps[current_step]
                
                st.markdown(f"### Step {step['step_number']}: {step['title']}")
                st.markdown(f"**{step['description']}**")
                
                st.markdown("#### 📋 Instructions:")
                for instruction in step['instructions']:
                    st.markdown(f"- {instruction}")
                
                st.info(f"⏱️ Estimated time: {step['estimated_time_minutes']} minutes")
                
                # Voice instruction
                if result['voice_instructions'][current_step]:
                    st.markdown("#### 🔊 Voice Guidance:")
                    st.audio(result['voice_instructions'][current_step])
                
                # Required documents for this step
                if 'required_documents' in step:
                    st.markdown("#### 📄 Required Documents:")
                    for doc in step['required_documents']:
                        st.markdown(f"- {doc}")
                
                # Navigation buttons
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    if current_step > 0:
                        if st.button("⬅️ Previous Step"):
                            st.session_state.current_step -= 1
                            st.rerun()
                
                with col2:
                    if st.button("✅ Mark Complete"):
                        st.success(f"Step {step['step_number']} completed!")
                
                with col3:
                    if current_step < len(wizard_steps) - 1:
                        if st.button("Next Step ➡️"):
                            st.session_state.current_step += 1
                            st.rerun()
                    else:
                        if st.button("🎉 Finish Wizard"):
                            st.success("🎉 Wizard completed! Proceed to document validation.")
                            st.session_state.current_step = 0
                
                # Store wizard data
                st.session_state.wizard_data = result
            
            else:
                st.error(f"❌ Error: {result.get('error', 'Wizard generation failed')}")


def render_document_validation(tools: SchemeApplicationTools):
    """Render document validation section"""
    st.subheader("Document Format Validator")
    st.markdown("Validate your documents before submission")
    
    # Scheme ID
    scheme_id = st.text_input(
        "Scheme ID",
        value=st.session_state.get('selected_scheme_id', ''),
        key="doc_scheme_id"
    )
    
    if not scheme_id:
        st.warning("Please enter a scheme ID")
        return
    
    # Document upload section
    st.markdown("### 📤 Upload Documents")
    
    # Number of documents
    num_docs = st.number_input("Number of documents to upload", min_value=1, max_value=10, value=3)
    
    documents = []
    
    for i in range(num_docs):
        with st.expander(f"Document {i+1}", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                doc_name = st.selectbox(
                    "Document Type",
                    ["Aadhaar Card", "Land Records", "Bank Passbook", 
                     "Income Certificate", "Caste Certificate", "Passport Photo"],
                    key=f"doc_name_{i}"
                )
            
            with col2:
                doc_format = st.selectbox(
                    "Format",
                    ["pdf", "jpg", "jpeg", "png"],
                    key=f"doc_format_{i}"
                )
            
            doc_size = st.slider(
                "File Size (MB)",
                min_value=0.1,
                max_value=10.0,
                value=1.5,
                step=0.1,
                key=f"doc_size_{i}"
            )
            
            uploaded_file = st.file_uploader(
                "Upload file",
                type=["pdf", "jpg", "jpeg", "png"],
                key=f"upload_{i}"
            )
            
            documents.append({
                'name': doc_name,
                'format': doc_format,
                'size_mb': doc_size,
                's3_key': f"documents/{doc_name.replace(' ', '_')}_{i}.{doc_format}",
                'uploaded': uploaded_file is not None
            })
    
    if st.button("🔍 Validate Documents", type="primary"):
        with st.spinner("Validating documents..."):
            result = tools.validate_documents(documents, scheme_id)
            
            if result['success']:
                # Overall status
                if result['all_valid']:
                    st.success("✅ All documents validated successfully!")
                else:
                    st.warning("⚠️ Some documents need attention")
                
                # Summary
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Documents", result['total_documents'])
                
                with col2:
                    st.metric("Required", result['required_documents'])
                
                with col3:
                    valid_count = sum(1 for v in result['validation_results'] if v['valid'])
                    st.metric("Valid", valid_count)
                
                st.markdown("---")
                
                # Validation results
                st.markdown("### 📊 Validation Results")
                
                for validation in result['validation_results']:
                    if validation['valid']:
                        st.success(f"✅ {validation['document_name']} - Valid")
                    else:
                        st.error(f"❌ {validation['document_name']} - Invalid")
                        for issue in validation['issues']:
                            st.markdown(f"  - {issue}")
                
                # Missing documents
                if result['missing_documents']:
                    st.error("❌ Missing Documents:")
                    for doc in result['missing_documents']:
                        st.markdown(f"- {doc}")
                
                # Extra documents
                if result['extra_documents']:
                    st.info("ℹ️ Extra Documents (not required):")
                    for doc in result['extra_documents']:
                        st.markdown(f"- {doc}")
                
                # Summary
                st.info(f"📝 {result['validation_summary']}")
                
                # Store validation results
                st.session_state.validation_results = result
            
            else:
                st.error(f"❌ Error: {result.get('error', 'Validation failed')}")


def render_application_submission(tools: SchemeApplicationTools):
    """Render application submission section"""
    st.subheader("Submit Application")
    st.markdown("Complete and submit your scheme application")
    
    # Check if documents are validated
    if 'validation_results' not in st.session_state:
        st.warning("⚠️ Please validate your documents first")
    
    # User and scheme info
    col1, col2 = st.columns(2)
    
    with col1:
        user_id = st.text_input("User ID", value=st.session_state.get('user_id', 'user_12345'))
    
    with col2:
        scheme_id = st.text_input(
            "Scheme ID",
            value=st.session_state.get('selected_scheme_id', ''),
            key="submit_scheme_id"
        )
    
    # Application form
    st.markdown("### 📝 Application Form")
    
    with st.form("application_form"):
        # Personal information
        st.markdown("#### Personal Information")
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name", value="Ravi Kumar")
            father_name = st.text_input("Father's Name", value="Ram Kumar")
        
        with col2:
            date_of_birth = st.date_input("Date of Birth")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        
        # Contact information
        st.markdown("#### Contact Information")
        col1, col2 = st.columns(2)
        
        with col1:
            mobile = st.text_input("Mobile Number", value="+91 9876543210")
            email = st.text_input("Email", value="ravi.kumar@example.com")
        
        with col2:
            address = st.text_area("Address", value="Village Rampur, District Lucknow")
        
        # Bank details
        st.markdown("#### Bank Details")
        col1, col2 = st.columns(2)
        
        with col1:
            bank_name = st.text_input("Bank Name", value="State Bank of India")
            account_number = st.text_input("Account Number", value="1234567890")
        
        with col2:
            ifsc_code = st.text_input("IFSC Code", value="SBIN0001234")
            account_holder = st.text_input("Account Holder Name", value="Ravi Kumar")
        
        # Declaration
        st.markdown("#### Declaration")
        declaration = st.checkbox(
            "I declare that all information provided is true and correct to the best of my knowledge"
        )
        
        # Submit button
        submit_button = st.form_submit_button("📤 Submit Application", type="primary")
        
        if submit_button:
            if not declaration:
                st.error("Please accept the declaration to proceed")
            elif not user_id or not scheme_id:
                st.error("Please provide User ID and Scheme ID")
            else:
                # Prepare application data
                application_data = {
                    'personal_info': {
                        'full_name': full_name,
                        'father_name': father_name,
                        'date_of_birth': str(date_of_birth),
                        'gender': gender
                    },
                    'contact_info': {
                        'mobile': mobile,
                        'email': email,
                        'address': address
                    },
                    'bank_details': {
                        'bank_name': bank_name,
                        'account_number': account_number,
                        'ifsc_code': ifsc_code,
                        'account_holder': account_holder
                    },
                    'documents': st.session_state.get('validation_results', {}).get('validation_results', []),
                    'declaration': declaration
                }
                
                with st.spinner("Submitting application..."):
                    result = tools.submit_application(user_id, scheme_id, application_data)
                    
                    if result['success']:
                        st.success("🎉 Application submitted successfully!")
                        
                        # Display receipt
                        st.markdown("### 📄 Submission Receipt")
                        
                        receipt = result['receipt']
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Application ID", result['application_id'])
                            st.metric("Tracking Number", result['tracking_number'])
                        
                        with col2:
                            st.metric("Status", result['status'].upper())
                            st.metric("Submission Date", receipt['submission_date'])
                        
                        st.info(receipt['receipt_message'])
                        
                        # Next steps
                        st.markdown("### 📝 Next Steps")
                        for i, step in enumerate(result['next_steps'], 1):
                            st.markdown(f"{i}. {step}")
                        
                        # Store application ID
                        st.session_state.submitted_application_id = result['application_id']
                        
                        # Download receipt button
                        if st.button("💾 Download Receipt"):
                            st.info("Receipt download feature coming soon!")
                    
                    else:
                        st.error(f"❌ Error: {result.get('error', 'Submission failed')}")
                        
                        if 'validation_results' in result:
                            st.warning("Document validation issues detected. Please fix and try again.")


def render_status_tracking(tools: SchemeApplicationTools):
    """Render status tracking section"""
    st.subheader("Track Application Status")
    st.markdown("Monitor your application progress in real-time")
    
    # Application ID input
    application_id = st.text_input(
        "Application ID or Tracking Number",
        value=st.session_state.get('submitted_application_id', ''),
        placeholder="APP_XXXXXXXXXXXX or RISE-XXXX-XXXX"
    )
    
    if st.button("🔍 Track Status", type="primary"):
        if not application_id:
            st.error("Please enter an Application ID")
            return
        
        with st.spinner("Fetching application status..."):
            result = tools.track_application_status(application_id)
            
            if result['success']:
                st.success("✅ Application found!")
                
                # Status overview
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Application ID", result['application_id'])
                
                with col2:
                    st.metric("Tracking Number", result['tracking_number'])
                
                with col3:
                    status_emoji = {
                        'submitted': '📝',
                        'under_review': '🔍',
                        'documents_verified': '✅',
                        'approved': '🎉',
                        'disbursed': '💰',
                        'rejected': '❌'
                    }
                    emoji = status_emoji.get(result['current_status'], '📋')
                    st.metric("Status", f"{emoji} {result['current_status'].replace('_', ' ').title()}")
                
                with col4:
                    st.metric("Progress", f"{result['progress_percentage']}%")
                
                # Progress bar
                st.progress(result['progress_percentage'] / 100)
                
                st.markdown("---")
                
                # Scheme info
                st.markdown(f"**Scheme:** {result['scheme_name']}")
                st.markdown(f"**Submission Date:** {result['submission_date']}")
                st.markdown(f"**Last Updated:** {result['last_updated']}")
                st.markdown(f"**Estimated Completion:** {result['estimated_completion']}")
                
                st.markdown("---")
                
                # Status timeline
                st.markdown("### 📅 Status Timeline")
                
                timeline = result['status_timeline']
                
                for entry in timeline:
                    status_icon = "✅" if entry['completed'] else "⏳"
                    st.markdown(f"{status_icon} **{entry['status'].replace('_', ' ').title()}**")
                    st.markdown(f"   📅 {entry['date']} at {entry['time']}")
                    if entry['notes']:
                        st.markdown(f"   📝 {entry['notes']}")
                    st.markdown("")
                
                # Next action
                st.info(f"📌 Next Action: {result['next_action']}")
                
                # Notification preferences
                st.markdown("### 🔔 Notification Preferences")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    sms_notifications = st.checkbox("SMS Notifications", value=True)
                
                with col2:
                    voice_notifications = st.checkbox("Voice Notifications", value=True)
                
                if st.button("💾 Save Preferences"):
                    st.success("Notification preferences saved!")
            
            else:
                st.error(f"❌ Error: {result.get('error', 'Application not found')}")


# Main function for standalone testing
if __name__ == "__main__":
    st.set_page_config(
        page_title="RISE - Scheme Application",
        page_icon="📝",
        layout="wide"
    )
    
    render_scheme_application()
