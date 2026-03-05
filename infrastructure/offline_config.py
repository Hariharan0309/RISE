"""
RISE Offline-First Configuration
Defines offline capabilities and caching strategies for rural connectivity
"""

# Offline storage configuration
OFFLINE_STORAGE_CONFIG = {
    "indexeddb_name": "rise_offline_db",
    "version": 1,
    "stores": {
        "diagnosis_history": {
            "keyPath": "diagnosis_id",
            "indexes": ["user_id", "timestamp"]
        },
        "weather_cache": {
            "keyPath": "location",
            "indexes": ["timestamp"]
        },
        "market_prices": {
            "keyPath": "cache_key",
            "indexes": ["crop", "location", "timestamp"]
        },
        "forum_posts": {
            "keyPath": "post_id",
            "indexes": ["user_id", "timestamp"]
        },
        "offline_queue": {
            "keyPath": "action_id",
            "indexes": ["action_type", "timestamp", "sync_status"]
        }
    }
}

# Cache duration settings (in seconds)
CACHE_DURATIONS = {
    "diagnosis_history": 30 * 24 * 60 * 60,  # 30 days
    "weather_data": 6 * 60 * 60,  # 6 hours
    "market_prices": 24 * 60 * 60,  # 24 hours
    "forum_posts": 7 * 24 * 60 * 60,  # 7 days
    "static_content": 30 * 24 * 60 * 60  # 30 days
}

# Features available offline
OFFLINE_FEATURES = {
    "diagnosis_history_view": True,
    "weather_view_cached": True,
    "market_prices_view_cached": True,
    "forum_read_only": True,
    "voice_input": True,  # Can record and queue
    "voice_output": True,  # Can play cached responses
    "chat_view_history": True,
    "profile_view": True,
    "offline_queue_management": True
}

# Sync priorities (1 = highest)
SYNC_PRIORITIES = {
    "diagnosis_upload": 1,
    "forum_post": 2,
    "chat_message": 3,
    "profile_update": 4,
    "analytics": 5
}

# Service worker caching strategies
SW_CACHE_STRATEGIES = {
    "static_assets": "CacheFirst",  # CSS, JS, images
    "api_data": "NetworkFirst",  # API responses
    "images": "CacheFirst",  # User uploaded images
    "audio": "CacheFirst"  # Voice recordings
}

# Maximum storage limits
STORAGE_LIMITS = {
    "indexeddb_max_mb": 50,  # 50MB for IndexedDB
    "cache_max_mb": 100,  # 100MB for Cache API
    "image_max_size_mb": 5,  # 5MB per image
    "audio_max_size_mb": 2  # 2MB per audio file
}

# Offline indicator settings
OFFLINE_INDICATOR_CONFIG = {
    "show_banner": True,
    "banner_color": "#FF9800",
    "banner_text": {
        "en": "You are offline. Some features are limited.",
        "hi": "आप ऑफ़लाइन हैं। कुछ सुविधाएं सीमित हैं।",
        "ta": "நீங்கள் ஆஃப்லைனில் உள்ளீர்கள். சில அம்சங்கள் வரம்புக்குட்பட்டவை.",
        "te": "మీరు ఆఫ్‌లైన్‌లో ఉన్నారు. కొన్ని ఫీచర్లు పరిమితం.",
        "kn": "ನೀವು ಆಫ್‌ಲೈನ್‌ನಲ್ಲಿದ್ದೀರಿ. ಕೆಲವು ವೈಶಿಷ್ಟ್ಯಗಳು ಸೀಮಿತವಾಗಿವೆ.",
        "bn": "আপনি অফলাইন আছেন। কিছু বৈশিষ্ট্য সীমিত।",
        "gu": "તમે ઑફલાઇન છો. કેટલીક સુવિધાઓ મર્યાદિત છે.",
        "mr": "तुम्ही ऑफलाइन आहात. काही वैशिष्ट्ये मर्यादित आहेत.",
        "pa": "ਤੁਸੀਂ ਔਫਲਾਈਨ ਹੋ। ਕੁਝ ਵਿਸ਼ੇਸ਼ਤਾਵਾਂ ਸੀਮਤ ਹਨ।"
    },
    "sync_pending_text": {
        "en": "Syncing {count} pending actions...",
        "hi": "{count} लंबित क्रियाएं सिंक हो रही हैं...",
        "ta": "{count} நிலுவையில் உள்ள செயல்களை ஒத்திசைக்கிறது...",
        "te": "{count} పెండింగ్ చర్యలను సింక్ చేస్తోంది...",
        "kn": "{count} ಬಾಕಿ ಇರುವ ಕ್ರಿಯೆಗಳನ್ನು ಸಿಂಕ್ ಮಾಡಲಾಗುತ್ತಿದೆ...",
        "bn": "{count} টি মুলতুবি কাজ সিঙ্ক হচ্ছে...",
        "gu": "{count} બાકી ક્રિયાઓ સિંક થઈ રહી છે...",
        "mr": "{count} प्रलंबित क्रिया सिंक होत आहेत...",
        "pa": "{count} ਬਕਾਇਆ ਕਾਰਵਾਈਆਂ ਸਿੰਕ ਹੋ ਰਹੀਆਂ ਹਨ..."
    }
}
