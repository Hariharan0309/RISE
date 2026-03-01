"""
Offline functionality components
Network status detection, offline indicators, and PWA setup
"""

import streamlit as st
from typing import Optional
import time


def check_network_status() -> bool:
    """
    Check if network is available
    
    Returns:
        True if online, False if offline
    """
    # In a real implementation, this would check actual network connectivity
    # For now, we'll use session state to simulate
    if 'is_online' not in st.session_state:
        st.session_state.is_online = True
    
    return st.session_state.is_online


def render_offline_indicator():
    """Render offline indicator banner when network is unavailable"""
    if not check_network_status():
        st.markdown("""
        <div class="offline-banner">
            ⚠️ You are offline. Some features may be limited. Cached data is available.
        </div>
        """, unsafe_allow_html=True)


def render_network_status_widget():
    """Render network status widget in sidebar"""
    is_online = check_network_status()
    
    status_color = "🟢" if is_online else "🔴"
    status_text = "Online" if is_online else "Offline"
    
    st.sidebar.markdown(f"### Network Status")
    st.sidebar.markdown(f"{status_color} **{status_text}**")
    
    # Toggle for testing (development only)
    if st.sidebar.checkbox("Simulate offline mode", value=not is_online):
        st.session_state.is_online = False
    else:
        st.session_state.is_online = True


def get_cached_data_info() -> dict:
    """
    Get information about cached data
    
    Returns:
        Dictionary with cache statistics
    """
    chat_messages = len(st.session_state.get('chat_history', []))
    audio_files = len(st.session_state.get('audio_cache', {}))
    
    return {
        'chat_messages': chat_messages,
        'audio_files': audio_files,
        'last_sync': st.session_state.get('last_sync_time', 'Never')
    }


def render_offline_data_status():
    """Render status of offline-available data"""
    cache_info = get_cached_data_info()
    
    st.sidebar.markdown("### Offline Data")
    st.sidebar.metric("Cached Messages", cache_info['chat_messages'])
    st.sidebar.metric("Cached Audio", cache_info['audio_files'])
    st.sidebar.caption(f"Last sync: {cache_info['last_sync']}")


def queue_offline_action(action_type: str, action_data: dict):
    """
    Queue an action to be synced when back online
    
    Args:
        action_type: Type of action (message, listing, etc.)
        action_data: Action data to sync
    """
    if 'offline_queue' not in st.session_state:
        st.session_state.offline_queue = []
    
    st.session_state.offline_queue.append({
        'type': action_type,
        'data': action_data,
        'timestamp': time.time()
    })


def sync_offline_actions():
    """Sync queued offline actions when back online"""
    if not check_network_status():
        return False
    
    if 'offline_queue' not in st.session_state or not st.session_state.offline_queue:
        return True
    
    # Sync each queued action
    synced_count = 0
    failed_actions = []
    
    for action in st.session_state.offline_queue:
        try:
            # Placeholder for actual sync logic (will be implemented in task 10)
            # sync_action_to_backend(action)
            synced_count += 1
        except Exception as e:
            failed_actions.append(action)
    
    # Update queue with failed actions
    st.session_state.offline_queue = failed_actions
    st.session_state.last_sync_time = time.strftime('%Y-%m-%d %H:%M:%S')
    
    return len(failed_actions) == 0


def render_sync_status():
    """Render sync status and controls"""
    if not check_network_status():
        st.info("📡 Offline mode - Actions will sync when connection is restored")
        
        pending_count = len(st.session_state.get('offline_queue', []))
        if pending_count > 0:
            st.warning(f"⏳ {pending_count} actions pending sync")
    else:
        if st.button("🔄 Sync Now"):
            with st.spinner("Syncing..."):
                success = sync_offline_actions()
                if success:
                    st.success("✅ All data synced!")
                else:
                    st.error("⚠️ Some actions failed to sync")


def setup_pwa_meta_tags() -> str:
    """
    Generate PWA meta tags for HTML head
    
    Returns:
        HTML string with meta tags
    """
    return """
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#4CAF50">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="MissionAI">
    <link rel="apple-touch-icon" href="/static/icon-192.png">
    <meta name="mobile-web-app-capable" content="yes">
    """


def register_service_worker() -> str:
    """
    Generate JavaScript to register service worker
    
    Returns:
        JavaScript code as string
    """
    return """
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/service-worker.js')
                    .then((registration) => {
                        console.log('Service Worker registered:', registration);
                    })
                    .catch((error) => {
                        console.log('Service Worker registration failed:', error);
                    });
            });
        }
        
        // Listen for online/offline events
        window.addEventListener('online', () => {
            console.log('Back online');
            // Trigger sync
        });
        
        window.addEventListener('offline', () => {
            console.log('Gone offline');
        });
    </script>
    """


def render_install_prompt():
    """Render PWA install prompt"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📱 Install App")
    
    if st.sidebar.button("Install on Device"):
        st.sidebar.info("""
        To install:
        1. Open menu in your browser
        2. Select "Add to Home Screen"
        3. Follow the prompts
        """)


def get_offline_capabilities() -> list:
    """
    Get list of features available offline
    
    Returns:
        List of offline-capable features
    """
    return [
        "View cached chat history",
        "Play cached audio responses",
        "View previously loaded data",
        "Queue actions for later sync"
    ]


def render_offline_help():
    """Render help information about offline mode"""
    with st.expander("ℹ️ About Offline Mode"):
        st.markdown("### Offline Capabilities")
        
        capabilities = get_offline_capabilities()
        for capability in capabilities:
            st.markdown(f"✅ {capability}")
        
        st.markdown("### Limitations")
        st.markdown("""
        - Cannot send new messages to AI
        - Cannot upload new images
        - Cannot fetch live weather/market data
        - Cannot check scheme eligibility
        """)
        
        st.markdown("### Tips")
        st.markdown("""
        - Important data is automatically cached
        - Actions are queued and synced when online
        - Audio responses are cached for offline playback
        """)
