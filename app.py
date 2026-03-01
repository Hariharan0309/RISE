"""
RISE - Rural Innovation and Sustainable Ecosystem
Main Streamlit Application Entry Point
"""

import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="RISE - Farming Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application entry point"""
    
    # Header
    st.title("🌾 RISE - Rural Innovation and Sustainable Ecosystem")
    st.markdown("### AI-Powered Farming Assistant")
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        
        # Language selector
        language = st.selectbox(
            "Select Language / भाषा चुनें",
            [
                "English",
                "हिंदी (Hindi)",
                "தமிழ் (Tamil)",
                "తెలుగు (Telugu)",
                "ಕನ್ನಡ (Kannada)",
                "বাংলা (Bengali)",
                "ગુજરાતી (Gujarati)",
                "मराठी (Marathi)",
                "ਪੰਜਾਬੀ (Punjabi)"
            ]
        )
        
        st.divider()
        
        # User profile section
        st.subheader("User Profile")
        st.info("Login functionality will be implemented in Phase 1")
        
        st.divider()
        
        # AWS Configuration status
        st.subheader("System Status")
        aws_configured = os.getenv("AWS_ACCESS_KEY_ID") is not None
        bedrock_configured = os.getenv("BEDROCK_MODEL_ID") is not None
        
        if aws_configured:
            st.success("✅ AWS Configured")
        else:
            st.warning("⚠️ AWS Not Configured")
            
        if bedrock_configured:
            st.success("✅ Bedrock Model Set")
        else:
            st.warning("⚠️ Bedrock Model Not Set")
    
    # Main content area
    st.markdown("---")
    
    # Welcome message
    st.info("""
    **Welcome to RISE!** 🌱
    
    This is the initial setup of your AI-powered farming assistant. 
    
    **Current Status:** Foundation Setup Complete
    
    **Next Steps:**
    1. Configure AWS credentials in `.env` file
    2. Set up Amazon Bedrock access
    3. Initialize core AWS services
    4. Implement voice and multilingual features
    
    **Features Coming Soon:**
    - 🎤 Voice-first multilingual interface
    - 🌿 AI-powered crop diagnosis
    - 🌍 Soil analysis and recommendations
    - ☁️ Weather-integrated farming alerts
    - 💰 Market intelligence and pricing
    - 🤝 Community resource sharing
    - 📋 Government scheme navigation
    """)
    
    # Placeholder for chat interface
    st.markdown("### Chat Interface")
    st.text_input("Ask me anything about farming...", disabled=True, 
                  placeholder="Chat will be enabled after agent setup")
    
    # Footer
    st.markdown("---")
    st.caption("RISE v0.1.0 - Built with Strands Agents & Streamlit")

if __name__ == "__main__":
    main()
