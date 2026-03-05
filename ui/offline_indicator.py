"""
RISE Offline Indicator UI Component
Displays online/offline status and sync progress
"""

import streamlit as st
from typing import Optional


def render_offline_indicator(language_code: str = "en") -> None:
    """
    Render offline/online status indicator with sync progress
    
    Args:
        language_code: User's preferred language code
    """
    from infrastructure.offline_config import OFFLINE_INDICATOR_CONFIG
    
    # Generate the offline indicator HTML and JavaScript
    indicator_html = f"""
    <style>
    .rise-offline-banner {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background-color: {OFFLINE_INDICATOR_CONFIG['banner_color']};
        color: white;
        padding: 0.75rem 1rem;
        text-align: center;
        font-weight: 600;
        z-index: 9999;
        display: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        animation: slideDown 0.3s ease-out;
    }}
    
    .rise-offline-banner.show {{
        display: block;
    }}
    
    .rise-sync-indicator {{
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #4CAF50;
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 9998;
        display: none;
        font-size: 0.9rem;
        animation: fadeIn 0.3s ease-out;
    }}
    
    .rise-sync-indicator.show {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    .rise-sync-spinner {{
        width: 16px;
        height: 16px;
        border: 2px solid rgba(255,255,255,0.3);
        border-top-color: white;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }}
    
    .rise-online-indicator {{
        position: fixed;
        top: 70px;
        right: 20px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #4CAF50;
        box-shadow: 0 0 8px rgba(76, 175, 80, 0.6);
        z-index: 9997;
        transition: background-color 0.3s;
    }}
    
    .rise-online-indicator.offline {{
        background-color: #F44336;
        box-shadow: 0 0 8px rgba(244, 67, 54, 0.6);
    }}
    
    @keyframes slideDown {{
        from {{
            transform: translateY(-100%);
        }}
        to {{
            transform: translateY(0);
        }}
    }}
    
    @keyframes fadeIn {{
        from {{
            opacity: 0;
            transform: translateY(20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    @keyframes spin {{
        to {{
            transform: rotate(360deg);
        }}
    }}
    </style>
    
    <div id="rise-offline-banner" class="rise-offline-banner">
        <span id="offline-message">{OFFLINE_INDICATOR_CONFIG['banner_text'].get(language_code, OFFLINE_INDICATOR_CONFIG['banner_text']['en'])}</span>
    </div>
    
    <div id="rise-sync-indicator" class="rise-sync-indicator">
        <div class="rise-sync-spinner"></div>
        <span id="sync-message">Syncing...</span>
    </div>
    
    <div id="rise-online-indicator" class="rise-online-indicator" title="Online"></div>
    
    <script>
    (function() {{
        const offlineBanner = document.getElementById('rise-offline-banner');
        const syncIndicator = document.getElementById('rise-sync-indicator');
        const onlineIndicator = document.getElementById('rise-online-indicator');
        const syncMessage = document.getElementById('sync-message');
        
        // Offline/Online status messages
        const messages = {json.dumps(OFFLINE_INDICATOR_CONFIG['banner_text'])};
        const syncMessages = {json.dumps(OFFLINE_INDICATOR_CONFIG['sync_pending_text'])};
        const currentLang = '{language_code}';
        
        // Update UI based on online status
        function updateOnlineStatus() {{
            const isOnline = navigator.onLine;
            
            if (isOnline) {{
                offlineBanner.classList.remove('show');
                onlineIndicator.classList.remove('offline');
                onlineIndicator.title = 'Online';
                
                // Trigger sync if there are pending actions
                if (window.syncPendingActions) {{
                    window.syncPendingActions();
                }}
            }} else {{
                offlineBanner.classList.add('show');
                onlineIndicator.classList.add('offline');
                onlineIndicator.title = 'Offline';
                syncIndicator.classList.remove('show');
            }}
        }}
        
        // Update sync progress
        function updateSyncProgress(detail) {{
            const {{ total, current }} = detail;
            const message = syncMessages[currentLang] || syncMessages['en'];
            syncMessage.textContent = message.replace('{{count}}', total - current);
            
            if (current < total) {{
                syncIndicator.classList.add('show');
            }} else {{
                // Hide after 2 seconds
                setTimeout(() => {{
                    syncIndicator.classList.remove('show');
                }}, 2000);
            }}
        }}
        
        // Listen for online/offline events
        window.addEventListener('online', updateOnlineStatus);
        window.addEventListener('offline', updateOnlineStatus);
        
        // Listen for sync progress events
        window.addEventListener('rise-sync-progress', (event) => {{
            updateSyncProgress(event.detail);
        }});
        
        // Initial status check
        updateOnlineStatus();
        
        // Periodic status check (every 10 seconds)
        setInterval(updateOnlineStatus, 10000);
    }})();
    </script>
    """
    
    # Render the indicator
    st.components.v1.html(indicator_html, height=0)


def render_offline_features_info(language_code: str = "en") -> None:
    """
    Render information about offline features
    
    Args:
        language_code: User's preferred language code
    """
    from infrastructure.offline_config import OFFLINE_FEATURES
    
    offline_info = {
        "en": {
            "title": "📱 Offline Features",
            "description": "These features are available even without internet connection:",
            "features": {
                "diagnosis_history_view": "View past crop diagnoses",
                "weather_view_cached": "View cached weather information",
                "market_prices_view_cached": "View cached market prices",
                "forum_read_only": "Read forum posts (read-only)",
                "voice_input": "Record voice queries (will sync later)",
                "chat_view_history": "View chat history",
                "profile_view": "View your profile"
            },
            "note": "Actions taken offline will be automatically synced when connection is restored."
        },
        "hi": {
            "title": "📱 ऑफ़लाइन सुविधाएं",
            "description": "ये सुविधाएं इंटरनेट कनेक्शन के बिना भी उपलब्ध हैं:",
            "features": {
                "diagnosis_history_view": "पिछले फसल निदान देखें",
                "weather_view_cached": "कैश किया गया मौसम जानकारी देखें",
                "market_prices_view_cached": "कैश किए गए बाजार मूल्य देखें",
                "forum_read_only": "फोरम पोस्ट पढ़ें (केवल पढ़ने के लिए)",
                "voice_input": "वॉयस प्रश्न रिकॉर्ड करें (बाद में सिंक होगा)",
                "chat_view_history": "चैट इतिहास देखें",
                "profile_view": "अपनी प्रोफ़ाइल देखें"
            },
            "note": "ऑफ़लाइन की गई कार्रवाइयां कनेक्शन बहाल होने पर स्वचालित रूप से सिंक हो जाएंगी।"
        }
    }
    
    info = offline_info.get(language_code, offline_info["en"])
    
    with st.expander(info["title"]):
        st.markdown(f"**{info['description']}**")
        st.markdown("")
        
        for feature_key, feature_desc in info["features"].items():
            if OFFLINE_FEATURES.get(feature_key, False):
                st.markdown(f"✅ {feature_desc}")
        
        st.markdown("")
        st.info(info["note"])


def render_sync_status(language_code: str = "en") -> None:
    """
    Render sync status information
    
    Args:
        language_code: User's preferred language code
    """
    sync_status_html = """
    <div id="rise-sync-status-container"></div>
    
    <script>
    (function() {
        async function updateSyncStatus() {
            const container = document.getElementById('rise-sync-status-container');
            
            try {
                if (window.getAllOfflineData) {
                    const pendingActions = await window.getAllOfflineData('offline_queue');
                    const pending = pendingActions.filter(a => a.sync_status === 'pending');
                    const failed = pendingActions.filter(a => a.sync_status === 'failed');
                    
                    if (pending.length > 0 || failed.length > 0) {
                        container.innerHTML = `
                            <div style="background: #FFF3E0; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                                <strong>🔄 Sync Status:</strong><br>
                                ${pending.length > 0 ? `⏳ ${pending.length} action(s) pending sync` : ''}
                                ${failed.length > 0 ? `<br>❌ ${failed.length} action(s) failed` : ''}
                            </div>
                        `;
                    } else {
                        container.innerHTML = `
                            <div style="background: #E8F5E9; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                                <strong>✅ All synced!</strong>
                            </div>
                        `;
                    }
                }
            } catch (err) {
                console.error('Error updating sync status:', err);
            }
        }
        
        // Update every 5 seconds
        setInterval(updateSyncStatus, 5000);
        updateSyncStatus();
    })();
    </script>
    """
    
    st.components.v1.html(sync_status_html, height=100)


def render_storage_stats() -> None:
    """Render offline storage statistics"""
    storage_stats_html = """
    <div id="rise-storage-stats"></div>
    
    <script>
    (function() {
        async function updateStorageStats() {
            const container = document.getElementById('rise-storage-stats');
            
            try {
                if (window.getRiseStorageStats) {
                    const stats = await window.getRiseStorageStats();
                    
                    container.innerHTML = `
                        <div style="background: #F5F5F5; padding: 1rem; border-radius: 8px;">
                            <strong>💾 Offline Storage</strong><br>
                            <small>
                                Storage Used: ${stats.indexeddb_used_mb} MB<br>
                                Diagnoses: ${stats.diagnosis_count}<br>
                                Cached Locations: ${stats.cached_weather_locations}<br>
                                Pending Sync: ${stats.pending_sync_actions}
                            </small>
                        </div>
                    `;
                }
            } catch (err) {
                console.error('Error updating storage stats:', err);
            }
        }
        
        // Update every 10 seconds
        setInterval(updateStorageStats, 10000);
        updateStorageStats();
    })();
    </script>
    """
    
    st.components.v1.html(storage_stats_html, height=120)
