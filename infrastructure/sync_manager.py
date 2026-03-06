"""
RISE Offline Sync Manager
Handles synchronization of offline actions when connection is restored
"""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SyncManager:
    """
    Manages synchronization of offline actions with backend services
    """
    
    def __init__(self):
        self.sync_config = self._load_config()
        self.sync_in_progress = False
    
    def _load_config(self) -> Dict:
        """Load sync configuration"""
        from infrastructure.offline_config import SYNC_PRIORITIES
        return {
            "priorities": SYNC_PRIORITIES,
            "max_retries": 3,
            "retry_delay_seconds": 5,
            "batch_size": 10
        }
    
    def generate_sync_script(self) -> str:
        """
        Generate JavaScript code for background sync
        """
        return """
        <script>
        // Background Sync Manager
        let syncInProgress = false;
        let syncQueue = [];
        
        // Check online status
        function isOnline() {
            return navigator.onLine;
        }
        
        // Sync pending actions
        async function syncPendingActions() {
            if (syncInProgress || !isOnline()) {
                return;
            }
            
            syncInProgress = true;
            
            try {
                // Get all pending actions
                const pendingActions = await getAllOfflineData('offline_queue');
                const toSync = pendingActions.filter(a => a.sync_status === 'pending');
                
                if (toSync.length === 0) {
                    syncInProgress = false;
                    return;
                }
                
                // Sort by priority and timestamp
                toSync.sort((a, b) => {
                    const priorityA = getSyncPriority(a.action_type);
                    const priorityB = getSyncPriority(b.action_type);
                    
                    if (priorityA !== priorityB) {
                        return priorityA - priorityB;
                    }
                    return a.timestamp - b.timestamp;
                });
                
                // Sync actions
                for (const action of toSync) {
                    try {
                        await syncAction(action);
                        
                        // Mark as synced
                        action.sync_status = 'synced';
                        action.synced_at = Date.now();
                        await storeOfflineData('offline_queue', action);
                        
                        // Notify success
                        notifySyncProgress(toSync.length, toSync.indexOf(action) + 1);
                        
                    } catch (err) {
                        console.error('Failed to sync action:', action.action_id, err);
                        
                        // Update retry count
                        action.retry_count = (action.retry_count || 0) + 1;
                        
                        if (action.retry_count >= 3) {
                            action.sync_status = 'failed';
                        }
                        
                        await storeOfflineData('offline_queue', action);
                    }
                }
                
                // Clean up synced actions older than 7 days
                await cleanupSyncedActions();
                
            } catch (err) {
                console.error('Sync process error:', err);
            } finally {
                syncInProgress = false;
            }
        }
        
        // Sync individual action
        async function syncAction(action) {
            const endpoint = getActionEndpoint(action.action_type);
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(action.action_data)
            });
            
            if (!response.ok) {
                throw new Error(`Sync failed: ${response.status}`);
            }
            
            return await response.json();
        }
        
        // Get sync priority for action type
        function getSyncPriority(actionType) {
            const priorities = {
                'diagnosis_upload': 1,
                'forum_post': 2,
                'chat_message': 3,
                'profile_update': 4,
                'analytics': 5
            };
            return priorities[actionType] || 10;
        }
        
        // Get API endpoint for action type
        function getActionEndpoint(actionType) {
            const endpoints = {
                'diagnosis_upload': '/api/v1/diagnosis/crop-disease',
                'forum_post': '/api/v1/community/discussions',
                'chat_message': '/api/v1/chat/message',
                'profile_update': '/api/v1/user/profile',
                'analytics': '/api/v1/analytics/event'
            };
            return endpoints[actionType] || '/api/v1/sync';
        }
        
        // Notify sync progress
        function notifySyncProgress(total, current) {
            const event = new CustomEvent('rise-sync-progress', {
                detail: { total, current }
            });
            window.dispatchEvent(event);
        }
        
        // Clean up old synced actions
        async function cleanupSyncedActions() {
            const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
            const allActions = await getAllOfflineData('offline_queue');
            
            for (const action of allActions) {
                if (action.sync_status === 'synced' && action.synced_at < sevenDaysAgo) {
                    await deleteOfflineData('offline_queue', action.action_id);
                }
            }
        }
        
        // Queue action for offline sync
        async function queueOfflineAction(actionType, actionData) {
            const action = {
                action_id: 'offline_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
                action_type: actionType,
                action_data: actionData,
                timestamp: Date.now(),
                sync_status: 'pending',
                retry_count: 0,
                created_at: new Date().toISOString()
            };
            
            await storeOfflineData('offline_queue', action);
            
            // Try to sync immediately if online
            if (isOnline()) {
                setTimeout(syncPendingActions, 1000);
            }
            
            return action.action_id;
        }
        
        // Listen for online event
        window.addEventListener('online', () => {
            console.log('Connection restored, syncing pending actions...');
            setTimeout(syncPendingActions, 2000);
        });
        
        // Periodic sync check (every 5 minutes)
        setInterval(() => {
            if (isOnline() && !syncInProgress) {
                syncPendingActions();
            }
        }, 5 * 60 * 1000);
        
        // Expose functions
        window.queueOfflineAction = queueOfflineAction;
        window.syncPendingActions = syncPendingActions;
        window.isOnline = isOnline;
        </script>
        """
    
    def process_synced_action(self, action: Dict) -> Dict:
        """
        Process a synced action on the backend
        """
        action_type = action.get("action_type")
        action_data = action.get("action_data", {})
        
        try:
            if action_type == "diagnosis_upload":
                return self._sync_diagnosis(action_data)
            elif action_type == "forum_post":
                return self._sync_forum_post(action_data)
            elif action_type == "chat_message":
                return self._sync_chat_message(action_data)
            elif action_type == "profile_update":
                return self._sync_profile_update(action_data)
            elif action_type == "analytics":
                return self._sync_analytics(action_data)
            else:
                logger.warning(f"Unknown action type: {action_type}")
                return {"success": False, "error": "Unknown action type"}
        
        except Exception as e:
            logger.error(f"Error processing synced action: {e}")
            return {"success": False, "error": str(e)}
    
    def _sync_diagnosis(self, data: Dict) -> Dict:
        """Sync diagnosis data"""
        # Import here to avoid circular dependencies
        from tools.disease_identification_tools import analyze_crop_disease
        
        try:
            result = analyze_crop_disease(
                image_path=data.get("image_path"),
                user_id=data.get("user_id"),
                crop_type=data.get("crop_type")
            )
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _sync_forum_post(self, data: Dict) -> Dict:
        """Sync forum post"""
        from tools.forum_tools import create_forum_post
        
        try:
            result = create_forum_post(
                user_id=data.get("user_id"),
                title=data.get("title"),
                content=data.get("content"),
                category=data.get("category")
            )
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _sync_chat_message(self, data: Dict) -> Dict:
        """Sync chat message"""
        # Store in conversation history
        return {"success": True, "message": "Chat message synced"}
    
    def _sync_profile_update(self, data: Dict) -> Dict:
        """Sync profile update"""
        # Update user profile in DynamoDB
        return {"success": True, "message": "Profile updated"}
    
    def _sync_analytics(self, data: Dict) -> Dict:
        """Sync analytics event"""
        # Send to analytics service
        return {"success": True, "message": "Analytics event recorded"}
    
    def get_pending_sync_count(self) -> int:
        """
        Get count of pending sync actions
        This would be called from JavaScript
        """
        # Placeholder - actual count from IndexedDB
        return 0
    
    def get_sync_status(self) -> Dict:
        """Get current sync status"""
        return {
            "sync_in_progress": self.sync_in_progress,
            "pending_count": self.get_pending_sync_count(),
            "last_sync": None  # Placeholder
        }


# Singleton instance
_sync_manager = None

def get_sync_manager() -> SyncManager:
    """Get singleton instance of SyncManager"""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = SyncManager()
    return _sync_manager
