"""
RISE Batch Request Handler
Handles batching multiple API requests to reduce network round-trips
"""

import json
import time
import asyncio
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid


class BatchRequestHandler:
    """Handle batched API requests for rural networks"""
    
    def __init__(self, max_batch_size: int = 10, timeout_seconds: int = 30):
        """
        Initialize batch request handler
        
        Args:
            max_batch_size: Maximum number of requests per batch
            timeout_seconds: Timeout for batch processing
        """
        self.max_batch_size = max_batch_size
        self.timeout_seconds = timeout_seconds
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    def create_batch_request(
        self,
        requests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a batched request structure
        
        Args:
            requests: List of individual request dicts
        
        Returns:
            Batched request structure
        """
        # Assign IDs to requests if not present
        for i, req in enumerate(requests):
            if 'request_id' not in req:
                req['request_id'] = f"req_{uuid.uuid4().hex[:8]}"
        
        return {
            'batch_id': f"batch_{uuid.uuid4().hex[:8]}",
            'timestamp': int(time.time() * 1000),
            'request_count': len(requests),
            'requests': requests
        }
    
    def process_batch(
        self,
        batch_request: Dict[str, Any],
        handler_map: Dict[str, Callable]
    ) -> Dict[str, Any]:
        """
        Process a batch of requests
        
        Args:
            batch_request: Batched request structure
            handler_map: Dict mapping endpoint names to handler functions
        
        Returns:
            Batched response structure
        """
        batch_id = batch_request.get('batch_id')
        requests = batch_request.get('requests', [])
        
        responses = []
        futures = {}
        
        # Submit all requests to thread pool
        for req in requests:
            request_id = req.get('request_id')
            endpoint = req.get('endpoint')
            params = req.get('params', {})
            
            # Get handler for endpoint
            handler = handler_map.get(endpoint)
            
            if handler:
                future = self.executor.submit(
                    self._execute_request,
                    request_id,
                    endpoint,
                    handler,
                    params
                )
                futures[future] = request_id
            else:
                # Unknown endpoint
                responses.append({
                    'request_id': request_id,
                    'success': False,
                    'error': f"Unknown endpoint: {endpoint}"
                })
        
        # Collect results with timeout
        try:
            for future in as_completed(futures, timeout=self.timeout_seconds):
                response = future.result()
                responses.append(response)
        except TimeoutError:
            # Add timeout errors for incomplete requests
            completed_ids = {r['request_id'] for r in responses}
            for future, request_id in futures.items():
                if request_id not in completed_ids:
                    responses.append({
                        'request_id': request_id,
                        'success': False,
                        'error': 'Request timeout'
                    })
        
        return {
            'batch_id': batch_id,
            'timestamp': int(time.time() * 1000),
            'response_count': len(responses),
            'responses': responses
        }
    
    def _execute_request(
        self,
        request_id: str,
        endpoint: str,
        handler: Callable,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single request
        
        Args:
            request_id: Request ID
            endpoint: Endpoint name
            handler: Handler function
            params: Request parameters
        
        Returns:
            Response dict
        """
        try:
            start_time = time.time()
            result = handler(**params)
            duration_ms = int((time.time() - start_time) * 1000)
            
            return {
                'request_id': request_id,
                'endpoint': endpoint,
                'success': True,
                'data': result,
                'duration_ms': duration_ms
            }
        except Exception as e:
            return {
                'request_id': request_id,
                'endpoint': endpoint,
                'success': False,
                'error': str(e)
            }
    
    def split_into_batches(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Split large request list into multiple batches
        
        Args:
            requests: List of requests
        
        Returns:
            List of batch request structures
        """
        batches = []
        
        for i in range(0, len(requests), self.max_batch_size):
            batch_requests = requests[i:i + self.max_batch_size]
            batch = self.create_batch_request(batch_requests)
            batches.append(batch)
        
        return batches
    
    def merge_batch_responses(
        self,
        batch_responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merge multiple batch responses into single response
        
        Args:
            batch_responses: List of batch response dicts
        
        Returns:
            Merged response dict
        """
        all_responses = []
        
        for batch_response in batch_responses:
            all_responses.extend(batch_response.get('responses', []))
        
        return {
            'merged': True,
            'batch_count': len(batch_responses),
            'total_responses': len(all_responses),
            'responses': all_responses
        }


class BatchRequestQueue:
    """Queue for accumulating requests before batching"""
    
    def __init__(
        self,
        batch_size: int = 5,
        max_wait_ms: int = 1000,
        auto_flush: bool = True
    ):
        """
        Initialize batch request queue
        
        Args:
            batch_size: Trigger batch when this many requests queued
            max_wait_ms: Maximum time to wait before flushing
            auto_flush: Automatically flush on timer
        """
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms
        self.auto_flush = auto_flush
        self.queue = []
        self.last_flush_time = time.time()
        self.handler = BatchRequestHandler()
    
    def add_request(
        self,
        endpoint: str,
        params: Dict[str, Any],
        callback: Optional[Callable] = None
    ) -> str:
        """
        Add request to queue
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            callback: Optional callback for response
        
        Returns:
            Request ID
        """
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        
        self.queue.append({
            'request_id': request_id,
            'endpoint': endpoint,
            'params': params,
            'callback': callback,
            'timestamp': time.time()
        })
        
        # Check if should flush
        if len(self.queue) >= self.batch_size:
            self.flush()
        elif self.auto_flush:
            elapsed_ms = (time.time() - self.last_flush_time) * 1000
            if elapsed_ms >= self.max_wait_ms:
                self.flush()
        
        return request_id
    
    def flush(self) -> Optional[Dict[str, Any]]:
        """
        Flush queue and process batch
        
        Returns:
            Batch response or None if queue empty
        """
        if not self.queue:
            return None
        
        # Get requests from queue
        requests = self.queue.copy()
        self.queue.clear()
        self.last_flush_time = time.time()
        
        # Create batch
        batch_request = self.handler.create_batch_request(requests)
        
        return batch_request
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return len(self.queue)
    
    def clear_queue(self):
        """Clear the queue"""
        self.queue.clear()
        self.last_flush_time = time.time()


class BatchResponseCache:
    """Cache for batch responses to avoid duplicate requests"""
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize batch response cache
        
        Args:
            ttl_seconds: Time to live for cached responses
        """
        self.ttl_seconds = ttl_seconds
        self.cache = {}
    
    def get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """
        Generate cache key for request
        
        Args:
            endpoint: API endpoint
            params: Request parameters
        
        Returns:
            Cache key string
        """
        # Sort params for consistent key
        sorted_params = json.dumps(params, sort_keys=True)
        return f"{endpoint}:{sorted_params}"
    
    def get(self, endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        Get cached response
        
        Args:
            endpoint: API endpoint
            params: Request parameters
        
        Returns:
            Cached response or None
        """
        cache_key = self.get_cache_key(endpoint, params)
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            
            # Check if expired
            if time.time() - cached_data['timestamp'] < self.ttl_seconds:
                return cached_data['response']
            else:
                # Remove expired entry
                del self.cache[cache_key]
        
        return None
    
    def set(self, endpoint: str, params: Dict[str, Any], response: Any):
        """
        Cache response
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            response: Response to cache
        """
        cache_key = self.get_cache_key(endpoint, params)
        
        self.cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
    
    def clear_expired(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, data in self.cache.items()
            if current_time - data['timestamp'] >= self.ttl_seconds
        ]
        
        for key in expired_keys:
            del self.cache[key]
    
    def clear_all(self):
        """Clear all cache entries"""
        self.cache.clear()


# Export main classes
__all__ = [
    'BatchRequestHandler',
    'BatchRequestQueue',
    'BatchResponseCache'
]
