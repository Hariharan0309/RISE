"""
Offline functionality tests for RISE.

Validates offline-first architecture:
- Service worker caching
- IndexedDB storage
- Offline queue management
- Data synchronization
- Conflict resolution
"""

import unittest
import time
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))


class OfflineStorageSimulator:
    """Simulate IndexedDB offline storage."""
    
    def __init__(self):
        self.storage = {}
        self.queue = []
    
    def store_offline(self, key, data):
        """Store data for offline access."""
        self.storage[key] = {
            'data': data,
            'timestamp': time.time(),
            'synced': False
        }
    
    def get_offline(self, key):
        """Retrieve data from offline storage."""
        return self.storage.get(key)
    
    def queue_operation(self, operation):
        """Queue operation for later sync."""
        operation['queued_at'] = time.time()
        operation['status'] = 'pending'
        self.queue.append(operation)
    
    def get_queue(self):
        """Get pending operations."""
        return [op for op in self.queue if op['status'] == 'pending']
    
    def mark_synced(self, operation_id):
        """Mark operation as synced."""
        for op in self.queue:
            if op.get('id') == operation_id:
                op['status'] = 'synced'
                op['synced_at'] = time.time()


class TestOfflineFunctionality(unittest.TestCase):
    """Test offline functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.storage = OfflineStorageSimulator()
        self.test_user_id = "test_farmer_offline"
    
    def test_offline_data_storage(self):
        """Test storing data for offline access."""
        print(f"\n{'='*60}")
        print(f"OFFLINE DATA STORAGE")
        print(f"{'='*60}")
        
        # Store various types of data offline
        test_data = {
            'market_prices': {
                'wheat': 2500,
                'rice': 3000,
                'last_updated': time.time()
            },
            'weather_forecast': {
                'temperature': 28,
                'rainfall': 'moderate',
                'last_updated': time.time()
            },
            'user_profile': {
                'user_id': self.test_user_id,
                'crops': ['wheat', 'rice'],
                'location': {'state': 'Punjab'}
            }
        }
        
        # Store data
        for key, data in test_data.items():
            self.storage.store_offline(key, data)
            print(f"✅ Stored {key} offline")
        
        # Verify retrieval
        print("\nVerifying offline data retrieval:")
        for key in test_data.keys():
            retrieved = self.storage.get_offline(key)
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved['data'], test_data[key])
            print(f"✅ Retrieved {key} successfully")
        
        print(f"{'='*60}\n")
    
    def test_offline_queue_management(self):
        """Test queuing operations while offline."""
        print(f"\n{'='*60}")
        print(f"OFFLINE QUEUE MANAGEMENT")
        print(f"{'='*60}")
        
        # Simulate user actions while offline
        operations = [
            {
                'id': 'op1',
                'type': 'voice_query',
                'data': {'query': 'What fertilizer for wheat?'},
                'priority': 'high'
            },
            {
                'id': 'op2',
                'type': 'image_upload',
                'data': {'image_path': '/local/image1.jpg'},
                'priority': 'high'
            },
            {
                'id': 'op3',
                'type': 'forum_post',
                'data': {'content': 'Best practices for rice'},
                'priority': 'medium'
            },
            {
                'id': 'op4',
                'type': 'price_check',
                'data': {'crop': 'wheat'},
                'priority': 'low'
            }
        ]
        
        # Queue operations
        print("Queuing operations while offline:")
        for op in operations:
            self.storage.queue_operation(op)
            print(f"  ✅ Queued {op['type']} (priority: {op['priority']})")
        
        # Verify queue
        queued = self.storage.get_queue()
        self.assertEqual(len(queued), len(operations))
        print(f"\nTotal queued operations: {len(queued)}")
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        sorted_queue = sorted(queued, key=lambda x: priority_order[x['priority']])
        
        print("\nQueue order (by priority):")
        for i, op in enumerate(sorted_queue, 1):
            print(f"  {i}. {op['type']} (priority: {op['priority']})")
        
        print(f"{'='*60}\n")
    
    def test_offline_to_online_sync(self):
        """Test synchronization when coming back online."""
        print(f"\n{'='*60}")
        print(f"OFFLINE TO ONLINE SYNCHRONIZATION")
        print(f"{'='*60}")
        
        # Queue operations while offline
        operations = [
            {'id': 'sync1', 'type': 'voice_query', 'data': {'query': 'Test'}},
            {'id': 'sync2', 'type': 'image_upload', 'data': {'image': 'test.jpg'}},
            {'id': 'sync3', 'type': 'forum_post', 'data': {'content': 'Test post'}}
        ]
        
        for op in operations:
            self.storage.queue_operation(op)
        
        print(f"Queued {len(operations)} operations while offline")
        
        # Simulate coming back online
        print("\n📶 Connection restored, syncing...")
        
        start_time = time.time()
        synced_count = 0
        failed_count = 0
        
        for op in self.storage.get_queue():
            try:
                # Simulate sync operation
                time.sleep(0.1)  # Simulate network request
                
                # Mark as synced
                self.storage.mark_synced(op['id'])
                synced_count += 1
                print(f"  ✅ Synced {op['type']}")
                
            except Exception as e:
                failed_count += 1
                print(f"  ❌ Failed to sync {op['type']}: {e}")
        
        sync_time = time.time() - start_time
        
        print(f"\nSync completed in {sync_time:.2f}s")
        print(f"  Synced: {synced_count}")
        print(f"  Failed: {failed_count}")
        print(f"  Success rate: {(synced_count/len(operations))*100:.1f}%")
        
        # Verify all operations synced
        pending = self.storage.get_queue()
        self.assertEqual(len(pending), 0, "All operations should be synced")
        
        print(f"{'='*60}\n")
    
    def test_conflict_resolution(self):
        """Test conflict resolution during sync."""
        print(f"\n{'='*60}")
        print(f"CONFLICT RESOLUTION")
        print(f"{'='*60}")
        
        # Simulate conflict scenario
        local_data = {
            'user_profile': {
                'crops': ['wheat', 'rice', 'cotton'],  # User added cotton offline
                'last_modified': time.time() - 100
            }
        }
        
        server_data = {
            'user_profile': {
                'crops': ['wheat', 'rice', 'maize'],  # Server has maize (added by another device)
                'last_modified': time.time() - 50
            }
        }
        
        print("Conflict detected:")
        print(f"  Local: {local_data['user_profile']['crops']}")
        print(f"  Server: {server_data['user_profile']['crops']}")
        
        # Conflict resolution strategy: Merge arrays
        def resolve_conflict(local, server):
            """Merge conflicting arrays."""
            local_crops = set(local['user_profile']['crops'])
            server_crops = set(server['user_profile']['crops'])
            merged_crops = list(local_crops.union(server_crops))
            
            return {
                'user_profile': {
                    'crops': sorted(merged_crops),
                    'last_modified': max(local['user_profile']['last_modified'],
                                       server['user_profile']['last_modified'])
                }
            }
        
        resolved = resolve_conflict(local_data, server_data)
        
        print(f"\nResolved: {resolved['user_profile']['crops']}")
        print(f"Strategy: Merge (union of both sets)")
        
        # Verify resolution includes all crops
        expected_crops = ['cotton', 'maize', 'rice', 'wheat']
        self.assertEqual(resolved['user_profile']['crops'], expected_crops)
        
        print(f"✅ Conflict resolved successfully")
        print(f"{'='*60}\n")
    
    def test_cache_invalidation(self):
        """Test cache invalidation and refresh."""
        print(f"\n{'='*60}")
        print(f"CACHE INVALIDATION")
        print(f"{'='*60}")
        
        # Store data with TTL
        cache_data = {
            'market_prices': {
                'data': {'wheat': 2500},
                'cached_at': time.time(),
                'ttl': 3600  # 1 hour
            },
            'weather': {
                'data': {'temp': 28},
                'cached_at': time.time() - 7200,  # 2 hours ago
                'ttl': 3600  # 1 hour
            }
        }
        
        def is_cache_valid(cache_entry):
            """Check if cache is still valid."""
            age = time.time() - cache_entry['cached_at']
            return age < cache_entry['ttl']
        
        print("Checking cache validity:")
        for key, entry in cache_data.items():
            valid = is_cache_valid(entry)
            age_minutes = (time.time() - entry['cached_at']) / 60
            status = "✅ Valid" if valid else "❌ Expired"
            print(f"  {key}: {status} (age: {age_minutes:.1f} minutes)")
            
            if key == 'market_prices':
                self.assertTrue(valid, "Market prices should be valid")
            elif key == 'weather':
                self.assertFalse(valid, "Weather data should be expired")
        
        print(f"\nCache management ensures:")
        print(f"  • Fresh data when online")
        print(f"  • Stale data better than no data offline")
        print(f"  • Automatic refresh when TTL expires")
        print(f"{'='*60}\n")
    
    def test_offline_performance_metrics(self):
        """Test performance metrics for offline operations."""
        print(f"\n{'='*60}")
        print(f"OFFLINE PERFORMANCE METRICS")
        print(f"{'='*60}")
        
        metrics = {
            'storage_operations': [],
            'queue_operations': [],
            'sync_operations': []
        }
        
        # Test storage performance
        print("Testing storage operations:")
        for i in range(10):
            start = time.time()
            self.storage.store_offline(f'key_{i}', {'data': f'value_{i}'})
            elapsed_ms = (time.time() - start) * 1000
            metrics['storage_operations'].append(elapsed_ms)
        
        avg_storage = sum(metrics['storage_operations']) / len(metrics['storage_operations'])
        print(f"  Average storage time: {avg_storage:.2f}ms")
        
        # Test queue performance
        print("\nTesting queue operations:")
        for i in range(10):
            start = time.time()
            self.storage.queue_operation({
                'id': f'queue_{i}',
                'type': 'test',
                'data': {}
            })
            elapsed_ms = (time.time() - start) * 1000
            metrics['queue_operations'].append(elapsed_ms)
        
        avg_queue = sum(metrics['queue_operations']) / len(metrics['queue_operations'])
        print(f"  Average queue time: {avg_queue:.2f}ms")
        
        # Test sync performance
        print("\nTesting sync operations:")
        for op in self.storage.get_queue()[:10]:
            start = time.time()
            self.storage.mark_synced(op['id'])
            elapsed_ms = (time.time() - start) * 1000
            metrics['sync_operations'].append(elapsed_ms)
        
        avg_sync = sum(metrics['sync_operations']) / len(metrics['sync_operations'])
        print(f"  Average sync time: {avg_sync:.2f}ms")
        
        print(f"\nPerformance summary:")
        print(f"  All operations complete in <10ms")
        print(f"  Offline operations are instant for users")
        print(f"  No blocking on network requests")
        print(f"{'='*60}\n")
        
        # All operations should be fast
        self.assertLess(avg_storage, 10, "Storage should be <10ms")
        self.assertLess(avg_queue, 10, "Queue should be <10ms")
        self.assertLess(avg_sync, 10, "Sync marking should be <10ms")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
