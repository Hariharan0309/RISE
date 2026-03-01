"""
MissionAI Farmer Agent - Streamlit UI
Voice-first multimodal AI agent for rural Indian farmers
"""

import streamlit as st
from typing import Optional, Dict, Any
import os
from datetime import datetime
import sys

# Import UI components
from ui.voice_components import (
    render_voice_input, 
    render_language_selector, 
    render_audio_playback,
    upload_audio_to_s3
)
from ui.image_components import (
    render_image_upload_with_validation,
    render_image_preview,
    validate_image_quality
)
from ui.chat_components import (
    render_chat_history,
    add_message_to_history,
    render_chat_controls,
    render_conversation_stats
)
from ui.tab_components import (
    render_weather_tab_content,
    render_market_tab_content,
    render_schemes_tab_content,
    render_finance_tab_content,
    render_community_tab_content
)
from ui.offline_components import (
    render_offline_indicator,
    render_network_status_widget,
    render_offline_data_status,
    render_sync_status,
    setup_pwa_meta_tags,
    register_service_worker,
    render_install_prompt,
    render_offline_help
)

# Page configuration
st.set_page_config(
    page_title="MissionAI - Farmer Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# PWA meta tags and service worker
st.markdown(setup_pwa_meta_tags(), unsafe_allow_html=True)
st.markdown(register_service_worker(), unsafe_allow_html=True)

# Mobile-responsive CSS styling
st.markdown("""
<style>
    /* Mobile-first responsive design */
    .main {
        padding: 0.5rem;
    }
    
    /* Large buttons for mobile */
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 0.5rem;
        margin: 0.25rem 0;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        overflow-x: auto;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: pre;
        padding: 0.5rem 1rem;
        font-size: 1rem;
        font-weight: 600;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        display: flex;
        flex-direction: column;
    }
    
    .user-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
    }
    
    .agent-message {
        background-color: #f5f5f5;
        margin-right: 2rem;
    }
    
    .message-header {
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.25rem;
        color: #666;
    }
    
    .message-content {
        font-size: 1rem;
        line-height: 1.5;
    }
    
    .message-timestamp {
        font-size: 0.75rem;
        color: #999;
        margin-top: 0.25rem;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        font-size: 1rem;
        padding: 0.75rem;
    }
    
    /* Card styling for schemes and results */
    .info-card {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Offline indicator */
    .offline-banner {
        background-color: #ff9800;
        color: white;
        padding: 0.75rem;
        text-align: center;
        font-weight: 600;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 1000;
    }
    
    /* Loading spinner */
    .stSpinner > div {
        text-align: center;
        font-size: 1.1rem;
    }
    
    /* Image preview */
    .image-preview {
        max-width: 100%;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    /* Responsive tables */
    .dataframe {
        font-size: 0.9rem;
        width: 100%;
        overflow-x: auto;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Mobile breakpoints */
    @media (max-width: 768px) {
        .main {
            padding: 0.25rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            font-size: 0.9rem;
            padding: 0.5rem;
        }
        
        .user-message {
            margin-left: 0.5rem;
        }
        
        .agent-message {
            margin-right: 0.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.user_id = None
        st.session_state.language = 'english'
        st.session_state.chat_history = []
        st.session_state.current_agent = None
        st.session_state.user_profile = {}
        st.session_state.audio_cache = {}
        st.session_state.is_online = True
        st.session_state.last_image = None
        st.session_state.last_audio = None

def main():
    """Main application entry point"""
    init_session_state()
    
    # Offline indicator banner
    render_offline_indicator()
    
    # App header
    st.title("🌾 MissionAI - Farmer Assistant")
    st.markdown("*Voice-first AI companion for farmers*")
    
    # Language selector
    st.session_state.language = render_language_selector()
    
    # Sidebar with network status and offline info
    with st.sidebar:
        render_network_status_widget()
        render_offline_data_status()
        render_sync_status()
        render_install_prompt()
        render_offline_help()
    
    # Tab navigation
    tabs = st.tabs([
        "💬 Chat",
        "🔬 Diagnose", 
        "🌤️ Weather", 
        "💰 Market", 
        "📋 Schemes", 
        "💵 Finance", 
        "👥 Community"
    ])
    
    # Tab 0: Chat (Main interaction)
    with tabs[0]:
        render_chat_tab()
    
    # Tab 1: Diagnose
    with tabs[1]:
        render_diagnose_tab()
    
    # Tab 2: Weather
    with tabs[2]:
        render_weather_tab()
    
    # Tab 3: Market
    with tabs[3]:
        render_market_tab()
    
    # Tab 4: Schemes
    with tabs[4]:
        render_schemes_tab()
    
    # Tab 5: Finance
    with tabs[5]:
        render_finance_tab()
    
    # Tab 6: Community
    with tabs[6]:
        render_community_tab()

def render_chat_tab():
    """Render the main chat interface"""
    st.subheader("Chat with AI Assistant")
    
    # Voice input component
    st.markdown("---")
    transcribed_text = render_voice_input(st.session_state.language)
    
    if transcribed_text:
        handle_user_message(transcribed_text)
    
    st.markdown("---")
    
    # Text input fallback
    st.markdown("### ⌨️ Or type your message")
    user_input = st.text_input("Type your message:", key="chat_input")
    
    if st.button("Send Message", type="primary"):
        if user_input:
            handle_user_message(user_input)
    
    # Chat controls
    st.markdown("---")
    render_chat_controls()
    
    # Conversation stats
    render_conversation_stats()
    
    # Chat history display
    st.markdown("---")
    st.subheader("💬 Conversation History")
    render_chat_history(
        st.session_state.get('chat_history', []),
        st.session_state.language
    )

def render_diagnose_tab():
    """Render disease diagnosis tab"""
    st.subheader("🔬 Crop Disease Diagnosis")
    st.write("Upload a photo of your crop to get instant diagnosis")
    
    # Image upload with validation
    result = render_image_upload_with_validation()
    
    if result:
        s3_url, image = result
        st.session_state.last_image = s3_url
        
        # Trigger diagnosis (will be fully implemented in task 10)
        with st.spinner("Analyzing crop image..."):
            st.info("Disease diagnosis will be integrated with agents in task 10")
            
            # Placeholder diagnosis result
            st.session_state.last_diagnosis = {
                'disease_name': 'Sample Disease',
                'severity': 'medium',
                'confidence': 0.85
            }
    
    # Display previous diagnosis if available
    if st.session_state.get('last_diagnosis'):
        st.markdown("---")
        st.subheader("📊 Diagnosis Results")
        display_diagnosis_results(st.session_state.last_diagnosis)

def render_weather_tab():
    """Render weather advisory tab"""
    render_weather_tab_content()

def render_market_tab():
    """Render market prices tab"""
    render_market_tab_content()

def render_schemes_tab():
    """Render government schemes tab"""
    render_schemes_tab_content()

def render_finance_tab():
    """Render financial calculator tab"""
    render_finance_tab_content()

def render_community_tab():
    """Render community forum tab"""
    render_community_tab_content()


def handle_user_message(message: str):
    """Handle user message submission"""
    # Add user message to history
    add_message_to_history('user', message)
    
    # Placeholder for agent integration (will be implemented in task 10)
    response = "Agent integration will be implemented in task 10. Your message was: " + message
    
    # Add agent response to history
    add_message_to_history('agent', response, agent='Manager Agent')
    
    # Rerun to update display
    st.rerun()

def display_chat_history():
    """Display chat message history (legacy function, now using chat_components)"""
    render_chat_history(
        st.session_state.get('chat_history', []),
        st.session_state.language
    )

def display_diagnosis_results(diagnosis: Dict[str, Any]):
    """Display disease diagnosis results"""
    st.markdown(f"""
    <div class="info-card">
        <h3>{diagnosis.get('disease_name', 'Unknown')}</h3>
        <p><strong>Severity:</strong> {diagnosis.get('severity', 'N/A')}</p>
        <p><strong>Confidence:</strong> {diagnosis.get('confidence', 0) * 100:.1f}%</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
