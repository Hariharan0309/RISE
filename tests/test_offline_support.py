"""
Tests for RISE Offline Support
"""

import pytest
import sys
import os
from datetime import datetime
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.offline_storage import get_storage_manager, OfflineStorageManager
from infrastructure.sync_manager import get_sync_manager, SyncManager
from infrastructure.offline_config import (
    OFFLINE_STORAGE_CONFIG,
    CACHE_DURATIONS,
    OFFLINE_FEATURES,
    SYNC_PRIORITIES,
    STORAGE_LIMITS
)


class TestOfflineStorageManager:
    """Test OfflineStorageManager functionality"""
    
    def test_singleton_instance(self):
        """Test that get_storage_manager returns singleton"""
        manager1 = get_storage_manager()
        manager2 = get_storage_manager()
        assert manager1 is manager2
    
    def test_cache_diagnosis_history(self):
        """Test caching diagnosis data"""
        manager = get_storage_manager()
        
        diagnosis_data = {
            "diagnosis_id": "test_diag_001",
            "user_id": "test_user",
            "diagnosis_result": {"disease": "Test Disease"}
        }
        
        cached = manager.cache_diagnosis_history(diagnosis_data)
        
        assert "cached_at" in cached
        assert "expires_at" in cached
        assert cached["diagnosis_id"] == "test_diag_001"
        assert cached["expires_at"] > cached["cached_at"]
    
    def test_cache_weather_data(self):
        """Test caching weather data"""
        manager = get_storage_manager()
        
        weather_data = {
            "temperature": 25,
            "humidity": 60,
            "forecast": []
        }
        
        cached = manager.cache_weather_data("Test Location", weather_data)
        
        assert cached["location"] == "Test Location"
        assert "cached_at" in cached
        assert "expires_at" in cached
        assert cached["data"]["temperature"] == 25
    
    def test_cache_market_prices(self):
        """Test caching market price data"""
        manager = get_storage_manager()
        
        price_data = {
            "current_price": 2000,
            "currency": "INR"
        }
        
        cached = manager.cache_market_prices("wheat", "Test City", price_data)
        
        assert cached["crop"] == "wheat"
        assert cached["location"] == "Test City"
        assert "cache_key" in cached
        assert cached["data"]["current_price"] == 2000
    
    def test_create_offline_action(self):
        """Test creating offline action"""
        manager = get_storage_manager()
        
        action_data = {
            "user_id": "test_user",
            "content": "Test content"
        }
        
        action = manager.create_offline_action("forum_post", action_data)
        
        assert "action_id" in action
        assert action["action_type"] == "forum_post"
        assert action["sync_status"] == "pending"
        assert action["retry_count"] == 0
        assert "timestamp" in action
    
    def test_generate_indexeddb_script(self):
        """Test IndexedDB initialization script generation"""
        manager = get_storage_manager()
        
        script = manager.generate_indexeddb_init_script()
        
        assert "<script>" in script
        assert "indexedDB.open" in script
        assert OFFLINE_STORAGE_CONFIG["indexeddb_name"] in script
        assert "diagnosis_history" in script
        assert "weather_cache" in script
    
    def test_generate_storage_check_script(self):
        """Test storage check script generation"""
        manager = get_storage_manager()
        
        script = manager.generate_storage_check_script()
        
        assert "<script>" in script
        assert "getRiseStorageStats" in script
        assert "navigator.storage" in script
    
    def test_storage_stats_structure(self):
        """Test storage stats structure"""
        manager = get_storage_manager()
        
        stats = manager.get_storage_stats()
        
        assert "indexeddb_used_mb" in stats
        assert "cache_used_mb" in stats
        assert "total_limit_mb" in stats
        assert "diagnosis_count" in stats
        assert "pending_sync_actions" in stats


class TestSyncManager:
    """Test SyncManager functionality"""
    
    def test_singleton_instance(self):
        """Test that get_sync_manager returns singleton"""
        manager1 = get_sync_manager()
        manager2 = get_sync_manager()
        assert manager1 is manager2
    
    def test_generate_sync_script(self):
        """Test sync script generation"""
        manager = get_sync_manager()
        
        script = manager.generate_sync_script()
        
        assert "<script>" in script
        assert "syncPendingActions" in script
        assert "queueOfflineAction" in script
        assert "navigator.onLine" in script
    
    def test_get_sync_status(self):
        """Test getting sync status"""
        manager = get_sync_manager()
        
        status = manager.get_sync_status()
        
        assert "sync_in_progress" in status
        assert "pending_count" in status
        assert isinstance(status["sync_in_progress"], bool)
    
    def test_process_synced_action_unknown_type(self):
        """Test processing unknown action type"""
        manager = get_sync_manager()
        
        action = {
            "action_type": "unknown_type",
            "action_data": {}
        }
        
        result = manager.process_synced_action(action)
        
        assert result["success"] is False
        assert "error" in result


class TestOfflineConfig:
    """Test offline configuration"""
    
    def test_storage_config_structure(self):
        """Test storage config has required structure"""
        assert "indexeddb_name" in OFFLINE_STORAGE_CONFIG
        assert "version" in OFFLINE_STORAGE_CONFIG
        assert "stores" in OFFLINE_STORAGE_CONFIG
        
        # Check required stores
        stores = OFFLINE_STORAGE_CONFIG["stores"]
        assert "diagnosis_history" in stores
        assert "weather_cache" in stores
        assert "market_prices" in stores
        assert "forum_posts" in stores
        assert "offline_queue" in stores
    
    def test_cache_durations(self):
        """Test cache durations are defined"""
        assert "diagnosis_history" in CACHE_DURATIONS
        assert "weather_data" in CACHE_DURATIONS
        assert "market_prices" in CACHE_DURATIONS
        
        # Check durations are positive
        for duration in CACHE_DURATIONS.values():
            assert duration > 0
    
    def test_offline_features(self):
        """Test offline features configuration"""
        assert "diagnosis_history_view" in OFFLINE_FEATURES
        assert "weather_view_cached" in OFFLINE_FEATURES
        assert "voice_input" in OFFLINE_FEATURES
        
        # Check all are boolean
        for value in OFFLINE_FEATURES.values():
            assert isinstance(value, bool)
    
    def test_sync_priorities(self):
        """Test sync priorities are defined"""
        assert "diagnosis_upload" in SYNC_PRIORITIES
        assert "forum_post" in SYNC_PRIORITIES
        
        # Check priorities are positive integers
        for priority in SYNC_PRIORITIES.values():
            assert isinstance(priority, int)
            assert priority > 0
    
    def test_storage_limits(self):
        """Test storage limits are defined"""
        assert "indexeddb_max_mb" in STORAGE_LIMITS
        assert "cache_max_mb" in STORAGE_LIMITS
        assert "image_max_size_mb" in STORAGE_LIMITS
        
        # Check limits are positive
        for limit in STORAGE_LIMITS.values():
            assert limit > 0


class TestOfflineIndicator:
    """Test offline indicator UI component"""
    
    def test_render_offline_indicator_import(self):
        """Test that offline indicator can be imported"""
        from ui.offline_indicator import render_offline_indicator
        assert callable(render_offline_indicator)
    
    def test_render_offline_features_info_import(self):
        """Test that offline features info can be imported"""
        from ui.offline_indicator import render_offline_features_info
        assert callable(render_offline_features_info)
    
    def test_render_storage_stats_import(self):
        """Test that storage stats can be imported"""
        from ui.offline_indicator import render_storage_stats
        assert callable(render_storage_stats)


class TestServiceWorker:
    """Test service worker file"""
    
    def test_service_worker_exists(self):
        """Test that service worker file exists"""
        sw_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "static",
            "service-worker.js"
        )
        assert os.path.exists(sw_path)
    
    def test_service_worker_content(self):
        """Test service worker has required content"""
        sw_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "static",
            "service-worker.js"
        )
        
        with open(sw_path, 'r') as f:
            content = f.read()
        
        assert "CACHE_VERSION" in content
        assert "addEventListener('install'" in content
        assert "addEventListener('fetch'" in content
        assert "cacheFirst" in content
        assert "networkFirst" in content


class TestOfflinePage:
    """Test offline fallback page"""
    
    def test_offline_page_exists(self):
        """Test that offline page exists"""
        offline_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "static",
            "offline.html"
        )
        assert os.path.exists(offline_path)
    
    def test_offline_page_content(self):
        """Test offline page has required content"""
        offline_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "static",
            "offline.html"
        )
        
        with open(offline_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "You're Offline" in content
        assert "Available Offline" in content
        assert "Retry Connection" in content
        assert "navigator.onLine" in content


def test_integration_cache_and_sync():
    """Integration test: Cache data and create sync action"""
    storage_manager = get_storage_manager()
    
    # Cache some data
    diagnosis = storage_manager.cache_diagnosis_history({
        "diagnosis_id": "int_test_001",
        "user_id": "test_user"
    })
    
    # Create offline action
    action = storage_manager.create_offline_action("diagnosis_upload", {
        "diagnosis_id": diagnosis["diagnosis_id"]
    })
    
    assert diagnosis["diagnosis_id"] == "int_test_001"
    assert action["action_type"] == "diagnosis_upload"
    assert action["sync_status"] == "pending"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
