"""
RISE Offline Storage Manager
Handles IndexedDB operations and offline data management
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time

class OfflineStorageManager:
    """
    Manages offline data storage using IndexedDB (via JavaScript bridge)
    and provides Python interface for offline operations
    """
    
    def __init__(self):
        self.storage_config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load offline storage configuration"""
        from infrastructure.offline_config import (
            OFFLINE_STORAGE_CONFIG,
            CACHE_DURATIONS,
            STORAGE_LIMITS
        )
        return {
            "db_config": OFFLINE_STORAGE_CONFIG,
            "cache_durations": CACHE_DURATIONS,
            "limits": STORAGE_LIMITS
        }
    
    def generate_indexeddb_init_script(self) -> str:
        """
        Generate JavaScript code to initialize IndexedDB
        This will be injected into the Streamlit app
        """
        config = self.storage_config["db_config"]
        
        script = f"""
        <script>
        // Initialize RISE Offline Storage
        const RISE_DB_NAME = '{config["indexeddb_name"]}';
        const RISE_DB_VERSION = {config["version"]};
        let riseDB = null;
        
        // Open IndexedDB connection
        function initRiseOfflineDB() {{
            return new Promise((resolve, reject) => {{
                const request = indexedDB.open(RISE_DB_NAME, RISE_DB_VERSION);
                
                request.onerror = () => {{
                    console.error('Failed to open IndexedDB:', request.error);
                    reject(request.error);
                }};
                
                request.onsuccess = () => {{
                    riseDB = request.result;
                    console.log('RISE Offline DB initialized successfully');
                    resolve(riseDB);
                }};
                
                request.onupgradeneeded = (event) => {{
                    const db = event.target.result;
                    
                    // Create object stores
        """
        
        # Add store creation code
        for store_name, store_config in config["stores"].items():
            script += f"""
                    if (!db.objectStoreNames.contains('{store_name}')) {{
                        const store = db.createObjectStore('{store_name}', {{
                            keyPath: '{store_config["keyPath"]}'
                        }});
                        
                        // Create indexes
            """
            for index in store_config.get("indexes", []):
                script += f"""
                        store.createIndex('{index}', '{index}', {{ unique: false }});
                """
            script += """
                    }
            """
        
        script += """
                };
            });
        }
        
        // Store data in IndexedDB
        function storeOfflineData(storeName, data) {
            return new Promise((resolve, reject) => {
                if (!riseDB) {
                    reject(new Error('Database not initialized'));
                    return;
                }
                
                const transaction = riseDB.transaction([storeName], 'readwrite');
                const store = transaction.objectStore(storeName);
                const request = store.put(data);
                
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
        }
        
        // Retrieve data from IndexedDB
        function getOfflineData(storeName, key) {
            return new Promise((resolve, reject) => {
                if (!riseDB) {
                    reject(new Error('Database not initialized'));
                    return;
                }
                
                const transaction = riseDB.transaction([storeName], 'readonly');
                const store = transaction.objectStore(storeName);
                const request = store.get(key);
                
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
        }
        
        // Get all data from a store
        function getAllOfflineData(storeName) {
            return new Promise((resolve, reject) => {
                if (!riseDB) {
                    reject(new Error('Database not initialized'));
                    return;
                }
                
                const transaction = riseDB.transaction([storeName], 'readonly');
                const store = transaction.objectStore(storeName);
                const request = store.getAll();
                
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
        }
        
        // Delete data from IndexedDB
        function deleteOfflineData(storeName, key) {
            return new Promise((resolve, reject) => {
                if (!riseDB) {
                    reject(new Error('Database not initialized'));
                    return;
                }
                
                const transaction = riseDB.transaction([storeName], 'readwrite');
                const store = transaction.objectStore(storeName);
                const request = store.delete(key);
                
                request.onsuccess = () => resolve();
                request.onerror = () => reject(request.error);
            });
        }
        
        // Clear expired cache entries
        function clearExpiredCache() {
            const now = Date.now();
            const stores = ['weather_cache', 'market_prices', 'forum_posts'];
            
            stores.forEach(storeName => {
                getAllOfflineData(storeName).then(items => {
                    items.forEach(item => {
                        if (item.expires_at && item.expires_at < now) {
                            deleteOfflineData(storeName, item[getKeyPath(storeName)]);
                        }
                    });
                });
            });
        }
        
        function getKeyPath(storeName) {
            const keyPaths = {
                'diagnosis_history': 'diagnosis_id',
                'weather_cache': 'location',
                'market_prices': 'cache_key',
                'forum_posts': 'post_id',
                'offline_queue': 'action_id'
            };
            return keyPaths[storeName] || 'id';
        }
        
        // Initialize on page load
        initRiseOfflineDB().catch(err => {
            console.error('Failed to initialize offline storage:', err);
        });
        
        // Clear expired cache every hour
        setInterval(clearExpiredCache, 60 * 60 * 1000);
        </script>
        """
        
        return script
    
    def cache_diagnosis_history(self, diagnosis_data: Dict) -> Dict:
        """
        Prepare diagnosis data for offline caching
        """
        cache_duration = self.storage_config["cache_durations"]["diagnosis_history"]
        
        return {
            **diagnosis_data,
            "cached_at": int(time.time()),
            "expires_at": int(time.time() + cache_duration)
        }
    
    def cache_weather_data(self, location: str, weather_data: Dict) -> Dict:
        """
        Prepare weather data for offline caching
        """
        cache_duration = self.storage_config["cache_durations"]["weather_data"]
        
        return {
            "location": location,
            "data": weather_data,
            "cached_at": int(time.time()),
            "expires_at": int(time.time() + cache_duration)
        }
    
    def cache_market_prices(self, crop: str, location: str, price_data: Dict) -> Dict:
        """
        Prepare market price data for offline caching
        """
        cache_duration = self.storage_config["cache_durations"]["market_prices"]
        cache_key = f"{crop}_{location}_{datetime.now().strftime('%Y%m%d')}"
        
        return {
            "cache_key": cache_key,
            "crop": crop,
            "location": location,
            "data": price_data,
            "cached_at": int(time.time()),
            "expires_at": int(time.time() + cache_duration)
        }
    
    def cache_forum_posts(self, posts: List[Dict]) -> List[Dict]:
        """
        Prepare forum posts for offline caching
        """
        cache_duration = self.storage_config["cache_durations"]["forum_posts"]
        cached_posts = []
        
        for post in posts:
            cached_posts.append({
                **post,
                "cached_at": int(time.time()),
                "expires_at": int(time.time() + cache_duration)
            })
        
        return cached_posts
    
    def create_offline_action(self, action_type: str, action_data: Dict) -> Dict:
        """
        Create an offline action to be synced later
        """
        import uuid
        
        return {
            "action_id": f"offline_{uuid.uuid4().hex[:12]}",
            "action_type": action_type,
            "action_data": action_data,
            "timestamp": int(time.time()),
            "sync_status": "pending",
            "retry_count": 0,
            "created_at": datetime.now().isoformat()
        }
    
    def get_storage_stats(self) -> Dict:
        """
        Get storage usage statistics
        This would be called from JavaScript and returned to Python
        """
        return {
            "indexeddb_used_mb": 0,  # Placeholder - actual value from JS
            "cache_used_mb": 0,  # Placeholder - actual value from JS
            "total_limit_mb": self.storage_config["limits"]["indexeddb_max_mb"] + 
                            self.storage_config["limits"]["cache_max_mb"],
            "diagnosis_count": 0,
            "cached_weather_locations": 0,
            "cached_market_prices": 0,
            "pending_sync_actions": 0
        }
    
    def generate_storage_check_script(self) -> str:
        """
        Generate JavaScript to check storage usage
        """
        return """
        <script>
        async function getRiseStorageStats() {
            const stats = {
                indexeddb_used_mb: 0,
                cache_used_mb: 0,
                diagnosis_count: 0,
                cached_weather_locations: 0,
                cached_market_prices: 0,
                pending_sync_actions: 0
            };
            
            try {
                // Get IndexedDB usage
                if (navigator.storage && navigator.storage.estimate) {
                    const estimate = await navigator.storage.estimate();
                    stats.indexeddb_used_mb = (estimate.usage / (1024 * 1024)).toFixed(2);
                }
                
                // Count items in stores
                if (riseDB) {
                    stats.diagnosis_count = (await getAllOfflineData('diagnosis_history')).length;
                    stats.cached_weather_locations = (await getAllOfflineData('weather_cache')).length;
                    stats.cached_market_prices = (await getAllOfflineData('market_prices')).length;
                    stats.pending_sync_actions = (await getAllOfflineData('offline_queue'))
                        .filter(a => a.sync_status === 'pending').length;
                }
            } catch (err) {
                console.error('Error getting storage stats:', err);
            }
            
            return stats;
        }
        
        // Expose to Streamlit
        window.getRiseStorageStats = getRiseStorageStats;
        </script>
        """


# Singleton instance
_storage_manager = None

def get_storage_manager() -> OfflineStorageManager:
    """Get singleton instance of OfflineStorageManager"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = OfflineStorageManager()
    return _storage_manager
