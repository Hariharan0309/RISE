"""
RISE Network Adapter UI Component
Detects network conditions and adapts UI accordingly
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, Any, Optional


def inject_network_detection_script():
    """Inject JavaScript for network detection"""
    
    script = """
    <script>
    // Network detection and adaptation
    (function() {
        // Store network info in session storage
        function detectNetwork() {
            if ('connection' in navigator) {
                const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
                
                const networkInfo = {
                    effectiveType: connection.effectiveType || 'unknown',
                    downlink: connection.downlink || 0,
                    rtt: connection.rtt || 0,
                    saveData: connection.saveData || false,
                    timestamp: Date.now()
                };
                
                // Store in session storage
                sessionStorage.setItem('rise_network_info', JSON.stringify(networkInfo));
                
                // Dispatch custom event
                window.dispatchEvent(new CustomEvent('networkDetected', { detail: networkInfo }));
                
                return networkInfo;
            }
            
            return null;
        }
        
        // Detect network on load
        const initialNetwork = detectNetwork();
        
        // Listen for network changes
        if ('connection' in navigator) {
            const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
            connection.addEventListener('change', detectNetwork);
        }
        
        // Expose function globally
        window.riseDetectNetwork = detectNetwork;
        
        // Apply network-specific optimizations
        function applyNetworkOptimizations(networkType) {
            const body = document.body;
            
            // Remove existing network classes
            body.classList.remove('network-2g', 'network-3g', 'network-4g', 'network-wifi');
            
            // Add current network class
            body.classList.add('network-' + networkType);
            
            // Apply optimizations based on network
            if (networkType === '2g' || networkType === 'slow-2g') {
                // Disable animations
                body.style.setProperty('--animation-duration', '0s');
                
                // Reduce image quality
                document.querySelectorAll('img').forEach(img => {
                    if (img.dataset.lowQualitySrc) {
                        img.src = img.dataset.lowQualitySrc;
                    }
                });
            } else if (networkType === '3g') {
                // Reduce animations
                body.style.setProperty('--animation-duration', '0.2s');
            } else {
                // Normal animations
                body.style.setProperty('--animation-duration', '0.3s');
            }
        }
        
        // Apply optimizations on network detection
        window.addEventListener('networkDetected', function(e) {
            const networkType = e.detail.effectiveType;
            applyNetworkOptimizations(networkType);
        });
        
        // Apply initial optimizations
        if (initialNetwork) {
            applyNetworkOptimizations(initialNetwork.effectiveType);
        }
        
        // Periodic network check (every 30 seconds)
        setInterval(detectNetwork, 30000);
    })();
    </script>
    
    <style>
    /* Network-specific styles */
    .network-2g img,
    .network-slow-2g img {
        image-rendering: -webkit-optimize-contrast;
        image-rendering: crisp-edges;
    }
    
    .network-2g .stSpinner,
    .network-slow-2g .stSpinner {
        animation-duration: 0s !important;
    }
    
    /* Reduce motion for slow networks */
    .network-2g *,
    .network-slow-2g * {
        animation-duration: 0s !important;
        transition-duration: 0s !important;
    }
    
    .network-3g * {
        animation-duration: 0.2s !important;
        transition-duration: 0.2s !important;
    }
    </style>
    """
    
    components.html(script, height=0)


def get_network_info_script() -> str:
    """Generate script to retrieve network info"""
    
    return """
    <script>
    // Retrieve network info from session storage
    const networkInfo = sessionStorage.getItem('rise_network_info');
    if (networkInfo) {
        const data = JSON.parse(networkInfo);
        // Send to Streamlit
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: data
        }, '*');
    }
    </script>
    """


def render_network_indicator(language_code: str = 'en'):
    """
    Render network quality indicator
    
    Args:
        language_code: Language code for translations
    """
    
    # Inject network detection
    inject_network_detection_script()
    
    # Network status messages
    messages = {
        'en': {
            '2g': '🔴 Slow Network (2G) - Limited features',
            '3g': '🟡 Moderate Network (3G) - Some features limited',
            '4g': '🟢 Good Network (4G)',
            'wifi': '🟢 Excellent Network (WiFi)',
            'unknown': '⚪ Network status unknown'
        },
        'hi': {
            '2g': '🔴 धीमा नेटवर्क (2G) - सीमित सुविधाएं',
            '3g': '🟡 मध्यम नेटवर्क (3G) - कुछ सुविधाएं सीमित',
            '4g': '🟢 अच्छा नेटवर्क (4G)',
            'wifi': '🟢 उत्कृष्ट नेटवर्क (WiFi)',
            'unknown': '⚪ नेटवर्क स्थिति अज्ञात'
        }
    }
    
    lang_messages = messages.get(language_code, messages['en'])
    
    # Try to get network info from session state
    if 'network_type' not in st.session_state:
        st.session_state.network_type = 'unknown'
    
    network_type = st.session_state.network_type
    message = lang_messages.get(network_type, lang_messages['unknown'])
    
    # Display indicator
    if network_type in ['2g', 'slow-2g']:
        st.warning(message)
    elif network_type == '3g':
        st.info(message)
    elif network_type in ['4g', 'wifi']:
        st.success(message)
    else:
        st.caption(message)


def render_data_saver_toggle(language_code: str = 'en'):
    """
    Render data saver mode toggle
    
    Args:
        language_code: Language code for translations
    """
    
    labels = {
        'en': {
            'title': '📊 Data Saver Mode',
            'description': 'Reduce data usage by limiting image quality and animations',
            'enabled': 'Data Saver: ON',
            'disabled': 'Data Saver: OFF'
        },
        'hi': {
            'title': '📊 डेटा सेवर मोड',
            'description': 'छवि गुणवत्ता और एनिमेशन को सीमित करके डेटा उपयोग कम करें',
            'enabled': 'डेटा सेवर: चालू',
            'disabled': 'डेटा सेवर: बंद'
        }
    }
    
    lang_labels = labels.get(language_code, labels['en'])
    
    # Initialize data saver state
    if 'data_saver_enabled' not in st.session_state:
        st.session_state.data_saver_enabled = False
    
    # Render toggle
    st.markdown(f"### {lang_labels['title']}")
    st.caption(lang_labels['description'])
    
    data_saver = st.toggle(
        lang_labels['enabled'] if st.session_state.data_saver_enabled else lang_labels['disabled'],
        value=st.session_state.data_saver_enabled,
        key='data_saver_toggle'
    )
    
    st.session_state.data_saver_enabled = data_saver
    
    if data_saver:
        st.info("✅ Images will load in lower quality to save data")


def render_network_stats(language_code: str = 'en'):
    """
    Render network statistics
    
    Args:
        language_code: Language code for translations
    """
    
    labels = {
        'en': {
            'title': '📡 Network Statistics',
            'type': 'Connection Type',
            'speed': 'Download Speed',
            'latency': 'Latency',
            'data_saved': 'Data Saved'
        },
        'hi': {
            'title': '📡 नेटवर्क आंकड़े',
            'type': 'कनेक्शन प्रकार',
            'speed': 'डाउनलोड गति',
            'latency': 'विलंबता',
            'data_saved': 'डेटा बचाया'
        }
    }
    
    lang_labels = labels.get(language_code, labels['en'])
    
    st.markdown(f"### {lang_labels['title']}")
    
    # Get network info from session state
    network_type = st.session_state.get('network_type', 'unknown')
    downlink = st.session_state.get('network_downlink', 0)
    rtt = st.session_state.get('network_rtt', 0)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(lang_labels['type'], network_type.upper())
    
    with col2:
        st.metric(lang_labels['speed'], f"{downlink:.1f} Mbps")
    
    with col3:
        st.metric(lang_labels['latency'], f"{rtt} ms")
    
    # Show data savings if available
    if 'total_data_saved_mb' in st.session_state:
        st.metric(
            lang_labels['data_saved'],
            f"{st.session_state.total_data_saved_mb:.2f} MB"
        )


def apply_network_adaptive_css():
    """Apply CSS that adapts to network conditions"""
    
    css = """
    <style>
    /* Base animation variables */
    :root {
        --animation-duration: 0.3s;
        --transition-duration: 0.3s;
    }
    
    /* Adaptive animations */
    .stButton button,
    .stSelectbox,
    .stTextInput input {
        transition: all var(--transition-duration) ease;
    }
    
    /* Progressive image loading */
    .progressive-image {
        position: relative;
        overflow: hidden;
    }
    
    .progressive-image img {
        transition: filter var(--transition-duration);
    }
    
    .progressive-image.loading img {
        filter: blur(10px);
    }
    
    .progressive-image.loaded img {
        filter: blur(0);
    }
    
    /* Skeleton loaders for slow networks */
    .skeleton {
        background: linear-gradient(
            90deg,
            #f0f0f0 25%,
            #e0e0e0 50%,
            #f0f0f0 75%
        );
        background-size: 200% 100%;
        animation: skeleton-loading 1.5s infinite;
    }
    
    @keyframes skeleton-loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    /* Disable skeleton animation on slow networks */
    .network-2g .skeleton,
    .network-slow-2g .skeleton {
        animation: none;
        background: #f0f0f0;
    }
    
    /* Reduce visual complexity on slow networks */
    .network-2g .stAlert,
    .network-slow-2g .stAlert {
        box-shadow: none;
        border: 1px solid #ddd;
    }
    
    /* Optimize font rendering */
    .network-2g,
    .network-slow-2g {
        text-rendering: optimizeSpeed;
        -webkit-font-smoothing: subpixel-antialiased;
    }
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)


def update_network_state_from_js():
    """Update Streamlit session state with network info from JavaScript"""
    
    # This would be called periodically to sync JS network detection with Streamlit
    # In practice, this requires a custom component or server-side detection
    pass


# Export main functions
__all__ = [
    'inject_network_detection_script',
    'render_network_indicator',
    'render_data_saver_toggle',
    'render_network_stats',
    'apply_network_adaptive_css'
]
