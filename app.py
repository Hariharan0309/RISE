"""
RISE - Rural Innovation and Sustainable Ecosystem
Main Streamlit Application Entry Point
"""

import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import get_orchestrator, get_orchestrator_health

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="RISE - Farming Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Language mapping
LANGUAGE_MAP = {
    "English": "en",
    "हिंदी (Hindi)": "hi",
    "தமிழ் (Tamil)": "ta",
    "తెలుగు (Telugu)": "te",
    "ಕನ್ನಡ (Kannada)": "kn",
    "বাংলা (Bengali)": "bn",
    "ગુજરાતી (Gujarati)": "gu",
    "मराठी (Marathi)": "mr",
    "ਪੰਜਾਬੀ (Punjabi)": "pa"
}

# Agricultural theme CSS
def apply_custom_css():
    """Apply custom CSS for agricultural theme"""
    st.markdown("""
    <style>
    /* Agricultural color scheme */
    :root {
        --primary-green: #2E7D32;
        --light-green: #66BB6A;
        --earth-brown: #5D4037;
        --sky-blue: #1976D2;
        --wheat-gold: #FFA726;
    }
    
    /* Main container styling */
    .main {
        background-color: #F1F8E9;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #2E7D32 0%, #66BB6A 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Chat message styling */
    .stChatMessage {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* User message */
    .stChatMessage[data-testid="user-message"] {
        background-color: #E8F5E9;
        border-left: 4px solid #2E7D32;
    }
    
    /* Assistant message */
    .stChatMessage[data-testid="assistant-message"] {
        background-color: #FFF3E0;
        border-left: 4px solid #FFA726;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #FAFAFA;
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #2E7D32;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #1B5E20;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Input field styling */
    .stTextInput>div>div>input {
        border-radius: 5px;
        border: 2px solid #2E7D32;
    }
    
    /* Success/Info boxes */
    .stSuccess {
        background-color: #E8F5E9;
        border-left: 4px solid #2E7D32;
    }
    
    .stInfo {
        background-color: #E3F2FD;
        border-left: 4px solid #1976D2;
    }
    
    /* Welcome card */
    .welcome-card {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    /* Feature badge */
    .feature-badge {
        display: inline-block;
        background-color: #2E7D32;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.85rem;
        margin: 0.2rem;
    }
    </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    
    if "user_name" not in st.session_state:
        st.session_state.user_name = None
    
    if "phone_number" not in st.session_state:
        st.session_state.phone_number = None
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    
    if "language" not in st.session_state:
        st.session_state.language = "en"
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "location" not in st.session_state:
        st.session_state.location = None
    
    if "crops" not in st.session_state:
        st.session_state.crops = []
    
    if "orchestrator" not in st.session_state:
        try:
            st.session_state.orchestrator = get_orchestrator()
        except Exception as e:
            st.session_state.orchestrator = None
            st.session_state.orchestrator_error = str(e)

def render_authentication():
    """Render simple authentication interface"""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.markdown("# 🌾 RISE - Rural Innovation and Sustainable Ecosystem")
    st.markdown("### AI-Powered Farming Assistant for Rural India")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="welcome-card">', unsafe_allow_html=True)
        st.markdown("## Welcome! स्वागत है! வரவேற்கிறோம்!")
        st.markdown("### Please enter your details to continue")
        
        with st.form("auth_form"):
            name = st.text_input(
                "Name / नाम / பெயர்",
                placeholder="Enter your name",
                help="Your name for personalized assistance"
            )
            
            phone = st.text_input(
                "Phone Number / फ़ोन नंबर / தொலைபேசி எண்",
                placeholder="10-digit mobile number",
                max_chars=10,
                help="Your mobile number (demo mode - any 10 digits)"
            )
            
            location = st.text_input(
                "Location / स्थान / இடம்",
                placeholder="Village, District, State",
                help="Your farming location"
            )
            
            crops_input = st.text_input(
                "Crops / फसलें / பயிர்கள்",
                placeholder="e.g., wheat, rice, cotton",
                help="Crops you grow (comma-separated)"
            )
            
            submit = st.form_submit_button("Start Farming Assistant / शुरू करें", use_container_width=True)
            
            if submit:
                if name and phone and len(phone) == 10 and phone.isdigit():
                    # Store user info
                    st.session_state.authenticated = True
                    st.session_state.user_name = name
                    st.session_state.phone_number = phone
                    st.session_state.user_id = f"farmer_{phone}"
                    st.session_state.location = location if location else "Not specified"
                    st.session_state.crops = [c.strip() for c in crops_input.split(",")] if crops_input else []
                    
                    # Create session with orchestrator
                    if st.session_state.orchestrator:
                        try:
                            session_id = st.session_state.orchestrator.create_session(
                                user_id=st.session_state.user_id,
                                language=st.session_state.language,
                                metadata={
                                    "name": name,
                                    "phone": phone,
                                    "location": st.session_state.location,
                                    "crops": st.session_state.crops
                                }
                            )
                            st.session_state.session_id = session_id
                            st.success("✅ Session created successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating session: {e}")
                    else:
                        st.warning("⚠️ Orchestrator not available. Running in limited mode.")
                        st.session_state.session_id = f"demo_{phone}"
                        st.rerun()
                else:
                    st.error("Please enter valid name and 10-digit phone number")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # System status
        st.markdown("---")
        st.markdown("### System Status")
        
        health = get_orchestrator_health()
        if health.get("status") == "healthy":
            st.success("✅ All systems operational")
        else:
            st.warning("⚠️ Some systems may be unavailable")

def render_sidebar():
    """Render sidebar with user profile and settings"""
    with st.sidebar:
        st.markdown("### 👤 User Profile")
        
        # User info
        st.markdown(f"**Name:** {st.session_state.user_name}")
        st.markdown(f"**Phone:** {st.session_state.phone_number}")
        st.markdown(f"**Location:** {st.session_state.location}")
        
        if st.session_state.crops:
            st.markdown(f"**Crops:** {', '.join(st.session_state.crops)}")
        
        st.divider()
        
        # Language selector
        st.markdown("### 🌐 Language / भाषा")
        
        # Find current language display name
        current_lang_display = "English"
        for display, code in LANGUAGE_MAP.items():
            if code == st.session_state.language:
                current_lang_display = display
                break
        
        language_display = st.selectbox(
            "Select Language",
            list(LANGUAGE_MAP.keys()),
            index=list(LANGUAGE_MAP.keys()).index(current_lang_display),
            key="language_selector"
        )
        
        # Update language if changed
        new_lang_code = LANGUAGE_MAP[language_display]
        if new_lang_code != st.session_state.language:
            st.session_state.language = new_lang_code
            if st.session_state.orchestrator and st.session_state.session_id:
                st.session_state.orchestrator.update_session_context(
                    st.session_state.session_id,
                    {"language": new_lang_code}
                )
            st.success(f"Language changed to {language_display}")
        
        st.divider()
        
        # System status
        st.markdown("### ⚙️ System Status")
        
        if st.session_state.orchestrator:
            try:
                status = st.session_state.orchestrator.get_status()
                
                if status["orchestrator"]["agent_initialized"]:
                    st.success("✅ AI Agent Active")
                else:
                    st.error("❌ AI Agent Inactive")
                
                if status["orchestrator"]["aws_configured"]:
                    st.success("✅ AWS Connected")
                else:
                    st.warning("⚠️ AWS Not Connected")
                
                st.info(f"📊 Messages: {status['sessions'].get('active_count', 0)}")
                
            except Exception as e:
                st.error(f"Status check failed: {e}")
        else:
            st.error("❌ Orchestrator unavailable")
        
        st.divider()
        
        # Quick actions
        st.markdown("### 🚀 Quick Actions")
        
        if st.button("🔄 Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
        
        if st.button("📊 Session Stats", use_container_width=True):
            if st.session_state.orchestrator and st.session_state.session_id:
                stats = st.session_state.orchestrator.get_session_stats(st.session_state.session_id)
                if stats:
                    st.json(stats)
        
        if st.button("🚪 Logout", use_container_width=True):
            # Cleanup session
            if st.session_state.orchestrator and st.session_state.session_id:
                st.session_state.orchestrator.cleanup_session(st.session_state.session_id)
            
            # Reset session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.divider()
        
        # Footer
        st.caption("RISE v1.0.0")
        st.caption("Built with Strands Agents & AWS Bedrock")

def render_chat_interface():
    """Render main chat interface"""
    
    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.markdown(f"# 🌾 Welcome, {st.session_state.user_name}!")
    st.markdown("### Ask me anything about farming, crops, weather, markets, and more")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Feature badges
    st.markdown("""
    <div style="text-align: center; margin: 1rem 0;">
        <span class="feature-badge">🌿 Crop Diagnosis</span>
        <span class="feature-badge">🌍 Soil Analysis</span>
        <span class="feature-badge">☁️ Weather Alerts</span>
        <span class="feature-badge">💰 Market Prices</span>
        <span class="feature-badge">🤝 Resource Sharing</span>
        <span class="feature-badge">📋 Govt Schemes</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Create tabs for different features
    tab1, tab2, tab3 = st.tabs(["💬 Chat Assistant", "📸 Disease Diagnosis", "📜 Diagnosis History"])
    
    with tab1:
        render_chat_tab()
    
    with tab2:
        render_disease_diagnosis_tab()
    
    with tab3:
        render_diagnosis_history_tab()


def render_chat_tab():
    """Render chat assistant tab"""
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "timestamp" in message:
                    st.caption(f"🕐 {message['timestamp']}")
    
    # Chat input
    user_input = st.chat_input(
        "Ask me anything about farming... / खेती के बारे में कुछ भी पूछें...",
        key="chat_input"
    )
    
    if user_input:
        # Add user message to chat
        timestamp = datetime.now().strftime("%I:%M %p")
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
            st.caption(f"🕐 {timestamp}")
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking... / सोच रहा हूँ..."):
                try:
                    if st.session_state.orchestrator and st.session_state.session_id:
                        # Process query with orchestrator
                        response = st.session_state.orchestrator.process_query(
                            session_id=st.session_state.session_id,
                            query=user_input,
                            context={
                                "location": st.session_state.location,
                                "crops": st.session_state.crops
                            }
                        )
                        
                        if response["success"]:
                            response_text = response["response"]
                            duration = response.get("duration_ms", 0)
                            
                            st.markdown(response_text)
                            st.caption(f"🕐 {timestamp} • ⚡ {duration:.0f}ms")
                            
                            # Add to chat history
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": response_text,
                                "timestamp": timestamp
                            })
                        else:
                            error_msg = response.get("error", "Unknown error occurred")
                            st.error(f"Error: {error_msg}")
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": f"⚠️ Error: {error_msg}",
                                "timestamp": timestamp
                            })
                    else:
                        # Fallback response when orchestrator is not available
                        fallback_msg = """I apologize, but the AI assistant is currently unavailable. 
                        
Please ensure:
1. AWS credentials are configured in `.env` file
2. Amazon Bedrock access is enabled
3. The orchestrator agent is properly initialized

For now, I can provide general information, but advanced AI features require proper AWS setup."""
                        
                        st.warning(fallback_msg)
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": fallback_msg,
                            "timestamp": timestamp
                        })
                
                except Exception as e:
                    error_msg = f"An error occurred: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"⚠️ {error_msg}",
                        "timestamp": timestamp
                    })
        
        # Rerun to update chat display
        st.rerun()
    
    # Suggested questions
    if len(st.session_state.chat_history) == 0:
        st.markdown("---")
        st.markdown("### 💡 Suggested Questions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🌿 How to identify crop diseases?", use_container_width=True):
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": "How can I identify diseases in my crops?",
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })
                st.rerun()
        
        with col2:
            if st.button("☁️ What's the weather forecast?", use_container_width=True):
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": f"What's the weather forecast for {st.session_state.location}?",
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })
                st.rerun()
        
        with col3:
            if st.button("💰 Current market prices?", use_container_width=True):
                crops_str = ", ".join(st.session_state.crops) if st.session_state.crops else "wheat and rice"
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": f"What are the current market prices for {crops_str}?",
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })
                st.rerun()

def render_disease_diagnosis_tab():
    """Render disease diagnosis tab with image upload"""
    try:
        from ui.image_uploader import render_image_uploader
        
        st.markdown("## 📸 Crop Disease Identification")
        st.markdown("Upload a photo of your crop to identify diseases and get treatment recommendations")
        
        # Render image uploader
        result = render_image_uploader(
            user_id=st.session_state.user_id,
            language_code=st.session_state.language
        )
        
        if result and result.get('success'):
            # Add diagnosis to chat history for context
            diagnosis_summary = f"""
🔬 **Disease Diagnosis Complete**

**Diagnosis ID:** {result.get('diagnosis_id')}
**Diseases Detected:** {', '.join(result.get('diseases', []))}
**Severity:** {result.get('severity', 'unknown').upper()}
**Confidence:** {result.get('confidence_score', 0)*100:.1f}%

You can ask me questions about this diagnosis or request more details about treatment.
"""
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": diagnosis_summary,
                "timestamp": datetime.now().strftime("%I:%M %p")
            })
    
    except ImportError as e:
        st.error(f"Disease identification module not available: {e}")
        st.info("Please ensure all dependencies are installed: `pip install pillow`")
    except Exception as e:
        st.error(f"Error loading disease diagnosis: {e}")


def render_diagnosis_history_tab():
    """Render diagnosis history tab"""
    try:
        from ui.image_uploader import render_diagnosis_history
        
        st.markdown("## 📜 Your Diagnosis History")
        
        # Render diagnosis history
        render_diagnosis_history(
            user_id=st.session_state.user_id,
            language_code=st.session_state.language
        )
    
    except ImportError as e:
        st.error(f"Disease identification module not available: {e}")
    except Exception as e:
        st.error(f"Error loading diagnosis history: {e}")


def main():
    """Main application entry point"""
    
    # Apply custom CSS
    apply_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Check authentication
    if not st.session_state.authenticated:
        render_authentication()
    else:
        # Render sidebar
        render_sidebar()
        
        # Render main chat interface
        render_chat_interface()

if __name__ == "__main__":
    main()
