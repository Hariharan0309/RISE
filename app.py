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
def inject_offline_support():
    """Inject offline support scripts and service worker"""
    from infrastructure.offline_storage import get_storage_manager
    from infrastructure.sync_manager import get_sync_manager
    
    storage_manager = get_storage_manager()
    sync_manager = get_sync_manager()
    
    # Inject IndexedDB initialization
    st.components.v1.html(storage_manager.generate_indexeddb_init_script(), height=0)
    
    # Inject sync manager
    st.components.v1.html(sync_manager.generate_sync_script(), height=0)
    
    # Inject storage stats checker
    st.components.v1.html(storage_manager.generate_storage_check_script(), height=0)
    
    # Register service worker
    service_worker_script = """
    <script>
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/static/service-worker.js')
                .then(registration => {
                    console.log('Service Worker registered:', registration);
                })
                .catch(error => {
                    console.error('Service Worker registration failed:', error);
                });
        });
    }
    </script>
    """
    st.components.v1.html(service_worker_script, height=0)


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
        color: #000000 !important;
    }
    
    /* Force text color in chat messages */
    .stChatMessage p, .stChatMessage div, .stChatMessage span {
        color: #000000 !important;
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


def inject_chunk_error_recovery():
    """On deploy, browsers may request old JS chunks (404). Reload once to load fresh chunks."""
    script = """
    <script>
    (function() {
        var key = 'rise_chunk_reload';
        window.addEventListener('unhandledrejection', function(e) {
            var msg = (e.reason && (e.reason.message || e.reason + '')) || '';
            if (msg.indexOf('Failed to fetch dynamically imported module') !== -1 ||
                msg.indexOf('Loading chunk') !== -1 || msg.indexOf('ChunkLoadError') !== -1) {
                e.preventDefault();
                if (!sessionStorage.getItem(key)) {
                    sessionStorage.setItem(key, '1');
                    window.location.reload();
                }
            }
        });
    })();
    </script>
    """
    st.components.v1.html(script, height=0)


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

def _set_session_from_user(user: dict):
    """Set session state from a user dict (after login or register)."""
    phone = user["phone"]
    st.session_state.authenticated = True
    st.session_state.user_name = user["name"]
    st.session_state.phone_number = phone
    st.session_state.user_id = f"farmer_{phone}"
    st.session_state.location = user.get("location", "Not specified")
    st.session_state.crops = user.get("crops", [])
    if st.session_state.orchestrator:
        try:
            session_id = st.session_state.orchestrator.create_session(
                user_id=st.session_state.user_id,
                language=st.session_state.language,
                metadata={
                    "name": user["name"],
                    "phone": phone,
                    "location": st.session_state.location,
                    "crops": st.session_state.crops,
                },
            )
            st.session_state.session_id = session_id
        except Exception:
            st.session_state.session_id = f"demo_{phone}"
    else:
        st.session_state.session_id = f"demo_{phone}"


def render_authentication():
    """Render login and register interface. First-time users register; returning users log in."""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.markdown("# 🌾 RISE - Rural Innovation and Sustainable Ecosystem")
    st.markdown("### AI-Powered Farming Assistant for Rural India")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="welcome-card">', unsafe_allow_html=True)
        auth_mode = st.radio(
            "**Choose**",
            ["🔐 Login", "📝 Register (first time)"],
            horizontal=True,
            key="auth_mode",
        )
        is_login = auth_mode.startswith("🔐")

        if is_login:
            st.markdown("### Login with your phone number")
            with st.form("login_form"):
                login_phone = st.text_input(
                    "Phone Number",
                    placeholder="10-digit mobile number",
                    max_chars=10,
                    key="login_phone",
                )
                login_btn = st.form_submit_button("Login", type="primary")
                if login_btn:
                    try:
                        from auth.user_store import login as user_login
                        user = user_login(login_phone)
                        if user:
                            _set_session_from_user(user)
                            st.success("✅ Welcome back!")
                            st.rerun()
                        else:
                            st.error("No account found with this phone number. Please **Register** first.")
                    except Exception as e:
                        st.error(f"Login failed: {e}")
        else:
            st.markdown("### Register (one-time) – enter your details")
            with st.form("register_form"):
                name = st.text_input("Name / नाम", placeholder="Your name", key="reg_name")
                phone = st.text_input(
                    "Phone Number / फ़ोन नंबर",
                    placeholder="10-digit mobile number",
                    max_chars=10,
                    key="reg_phone",
                )
                location = st.text_input(
                    "Location / स्थान",
                    placeholder="Village, District, State",
                    key="reg_location",
                )
                crops_input = st.text_input(
                    "Crops / फसलें",
                    placeholder="e.g., wheat, rice, cotton",
                    key="reg_crops",
                )
                submit = st.form_submit_button("Register & Start", type="primary")
                if submit:
                    if name and phone and len(phone) == 10 and phone.isdigit():
                        try:
                            from auth.user_store import register
                            result = register(
                                phone=phone,
                                name=name,
                                location=location or "",
                                crops=[c.strip() for c in (crops_input or "").split(",") if c.strip()],
                            )
                            if result.get("success") and result.get("user"):
                                _set_session_from_user(result["user"])
                                st.success("✅ Account created! Welcome to RISE.")
                                st.rerun()
                            else:
                                st.error(result.get("error", "Registration failed"))
                        except Exception as e:
                            st.error(f"Registration failed: {e}")
                    else:
                        st.error("Please enter valid name and 10-digit phone number")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### System Status")
        health = get_orchestrator_health()
        if health.get("status") == "healthy":
            st.success("✅ All systems operational")
        else:
            st.warning("⚠️ Some systems may be unavailable")

def render_sidebar():
    """Render sidebar: features at top, user profile at bottom."""
    with st.sidebar:
        # Feature / page navigation – at TOP so all features are visible first
        st.markdown("### 📍 All features")
        page_options = [
            "💬 Chat & Diagnosis",
            "👥 Farmer Forum",
            "🏛️ Scheme Discovery",
            "📝 Scheme Application",
            "📊 Market Prices",
            "📅 Equipment Booking",
            "🛒 Equipment Marketplace",
            "🤝 Buying Groups",
            "🚚 Supplier Negotiation",
            "📦 Buyer Connection",
            "🌾 Profitability Calculator",
            "💰 Loan Calculator",
            "🔔 Alert Customization",
            "🌍 Local Economy",
            "📚 Best Practices",
            "🌤️ Weather Alerts",
            "🎤 Voice Input",
        ]
        if "current_page" not in st.session_state or st.session_state.current_page not in page_options:
            st.session_state.current_page = page_options[0]
        selected_page = st.radio(
            "Choose a feature",
            page_options,
            index=page_options.index(st.session_state.current_page),
            key="page_selector",
            label_visibility="collapsed",
        )
        if selected_page != st.session_state.current_page:
            st.session_state.current_page = selected_page
            st.rerun()
        
        st.divider()
        
        # Offline indicator and storage (compact)
        from ui.offline_indicator import render_offline_features_info, render_storage_stats
        render_offline_features_info(st.session_state.language)
        render_storage_stats()
        
        st.divider()
        
        # Language selector
        st.markdown("### 🌐 Language / भाषा")
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
        
        st.divider()
        
        # User profile at BOTTOM so features stay visible at top
        st.markdown("### 👤 User Profile")
        st.markdown(f"**Name:** {st.session_state.user_name}")
        st.markdown(f"**Phone:** {st.session_state.phone_number}")
        st.markdown(f"**Location:** {st.session_state.location}")
        if st.session_state.crops:
            st.markdown(f"**Crops:** {', '.join(st.session_state.crops)}")
        
        if st.button("🚪 Logout", use_container_width=True):
            if st.session_state.orchestrator and st.session_state.session_id:
                st.session_state.orchestrator.cleanup_session(st.session_state.session_id)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.divider()
        
        # Footer
        st.caption("RISE v1.0.0")
        st.caption("Built with Strands Agents & AWS Bedrock")

def render_chat_interface():
    """Render main interface - dispatches to selected page."""
    
    inject_offline_support()
    from ui.offline_indicator import render_offline_indicator
    render_offline_indicator(st.session_state.language)
    
    page = st.session_state.get("current_page", "💬 Chat & Diagnosis")
    
    # Header (compact when not on home)
    if page == "💬 Chat & Diagnosis":
        st.markdown('<div class="main-header">', unsafe_allow_html=True)
        st.markdown(f"# 🌾 Welcome, {st.session_state.user_name}!")
        st.markdown("### Ask me anything about farming, crops, weather, markets, and more")
        st.markdown('</div>', unsafe_allow_html=True)
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
        tab1, tab2, tab3 = st.tabs(["💬 Chat Assistant", "📸 Disease Diagnosis", "📜 Diagnosis History"])
        with tab1:
            render_chat_tab()
        with tab2:
            render_disease_diagnosis_tab()
        with tab3:
            render_diagnosis_history_tab()
        return
    
    # Minimal header for other pages
    st.markdown(f"# {page}")
    st.markdown("---")
    
    # Default location for UIs that need lat/lon (e.g. Delhi)
    user_location = getattr(st.session_state, "user_location", {"latitude": 28.6139, "longitude": 77.2090})
    
    try:
        if page == "👥 Farmer Forum":
            from tools.forum_tools import create_forum_tools
            if "forum_tools" not in st.session_state:
                st.session_state.forum_tools = create_forum_tools()
            from ui.farmer_forum import render_farmer_forum
            render_farmer_forum(st.session_state.forum_tools, st.session_state.user_id, st.session_state.language)
        elif page == "🏛️ Scheme Discovery":
            from ui.scheme_discovery import render_scheme_discovery
            render_scheme_discovery()
        elif page == "📝 Scheme Application":
            from ui.scheme_application import render_scheme_application
            render_scheme_application()
        elif page == "📊 Market Prices":
            from tools.market_price_tools import create_market_price_tools
            if "market_tools" not in st.session_state:
                st.session_state.market_tools = create_market_price_tools()
            from ui.market_price_dashboard import render_market_price_dashboard
            render_market_price_dashboard(st.session_state.market_tools, user_location)
        elif page == "📅 Equipment Booking":
            from ui.equipment_booking import render_equipment_booking_management
            render_equipment_booking_management()
        elif page == "🛒 Equipment Marketplace":
            from ui.equipment_marketplace import render_equipment_marketplace
            render_equipment_marketplace()
        elif page == "🤝 Buying Groups":
            from ui.buying_groups import render_buying_groups
            render_buying_groups()
        elif page == "🚚 Supplier Negotiation":
            from ui.supplier_negotiation import render_supplier_negotiation_ui
            render_supplier_negotiation_ui()
        elif page == "🤝 Buyer Connection":
            from ui.buyer_connection_dashboard import render_buyer_connection_dashboard
            render_buyer_connection_dashboard()
        elif page == "🌾 Profitability Calculator":
            from ui.profitability_calculator import render_profitability_calculator
            render_profitability_calculator()
        elif page == "💰 Loan Calculator":
            from ui.loan_calculator import render_loan_calculator
            render_loan_calculator()
        elif page == "🔔 Alert Customization":
            from ui.alert_customization import render_alert_customization
            render_alert_customization()
        elif page == "🌍 Local Economy":
            from ui.local_economy_dashboard import render_local_economy_dashboard
            render_local_economy_dashboard()
        elif page == "📚 Best Practices":
            from tools.best_practice_tools import BestPracticeTools
            if "best_practice_tools" not in st.session_state:
                st.session_state.best_practice_tools = BestPracticeTools()
            from ui.best_practices_library import render_best_practices_library
            render_best_practices_library(st.session_state.best_practice_tools, st.session_state.user_id, st.session_state.language)
        elif page == "🌤️ Weather Alerts":
            from ui.weather_alerts import render_weather_alerts_dashboard
            render_weather_alerts_dashboard(st.session_state.user_id, user_location)
        elif page == "🎤 Voice Input":
            from ui.voice_recorder import render_voice_recorder
            render_voice_recorder(key="main_voice_recorder")
        else:
            st.info("Select a feature from the sidebar.")
    except Exception as e:
        st.error(f"Error loading {page}: {e}")
        import traceback
        st.code(traceback.format_exc())


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
        
        # Get AI response
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
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response_text,
                        "timestamp": timestamp
                    })
                else:
                    error_msg = response.get("error", "Unknown error occurred")
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
                
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": fallback_msg,
                    "timestamp": timestamp
                })
        
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
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
    inject_chunk_error_recovery()
    
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
