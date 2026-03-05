"""
Tests for RISE Network Optimization
"""

import pytest
import json
import gzip
import base64
from PIL import Image
import io
import sys
import os

# Add infrastructure to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'infrastructure'))

from network_optimization import NetworkOptimizer, ImageOptimizer
from image_optimizer import ImageProcessor
from batch_request_handler import BatchRequestHandler, BatchRequestQueue, BatchResponseCache


class TestNetworkOptimizer:
    """Test NetworkOptimizer class"""
    
    def test_detect_network_type_2g(self):
        """Test 2G network detection"""
        network_type = NetworkOptimizer.detect_network_type(
            downlink_mbps=0.1,
            rtt_ms=500
        )
        assert network_type == "2g"
    
    def test_detect_network_type_3g(self):
        """Test 3G network detection"""
        network_type = NetworkOptimizer.detect_network_type(
            downlink_mbps=1.0,
            rtt_ms=200
        )
        assert network_type == "3g"
    
    def test_detect_network_type_4g(self):
        """Test 4G network detection"""
        network_type = NetworkOptimizer.detect_network_type(
            downlink_mbps=10.0,
            rtt_ms=50
        )
        assert network_type == "4g"
    
    def test_detect_network_type_wifi(self):
        """Test WiFi network detection"""
        network_type = NetworkOptimizer.detect_network_type(
            downlink_mbps=50.0,
            rtt_ms=20
        )
        assert network_type == "wifi"
    
    def test_get_adaptive_config_2g(self):
        """Test adaptive config for 2G"""
        config = NetworkOptimizer.get_adaptive_config("2g")
        
        assert config['image_quality'] == 30
        assert config['image_max_width'] == 320
        assert config['enable_compression'] is True
        assert config['compression_level'] == 9
        assert config['batch_requests'] is True
        assert config['batch_size'] == 5
    
    def test_get_adaptive_config_3g(self):
        """Test adaptive config for 3G"""
        config = NetworkOptimizer.get_adaptive_config("3g")
        
        assert config['image_quality'] == 50
        assert config['image_max_width'] == 640
        assert config['compression_level'] == 6
        assert config['batch_size'] == 3
    
    def test_compress_response(self):
        """Test response compression"""
        data = {'message': 'Hello' * 100, 'numbers': list(range(100))}
        
        compressed = NetworkOptimizer.compress_response(data, compression_level=6)
        
        # Compressed should be smaller
        original_size = len(json.dumps(data))
        compressed_size = len(compressed)
        
        assert compressed_size < original_size
        assert isinstance(compressed, bytes)
    
    def test_decompress_response(self):
        """Test response decompression"""
        original_data = {'test': 'data', 'numbers': [1, 2, 3]}
        
        compressed = NetworkOptimizer.compress_response(original_data)
        decompressed = NetworkOptimizer.decompress_response(compressed)
        
        assert decompressed == original_data
    
    def test_create_compressed_lambda_response(self):
        """Test compressed Lambda response creation"""
        data = {'result': 'success', 'data': list(range(50))}
        
        response = NetworkOptimizer.create_compressed_lambda_response(
            data,
            status_code=200,
            compression_level=6
        )
        
        assert response['statusCode'] == 200
        assert response['headers']['Content-Encoding'] == 'gzip'
        assert response['isBase64Encoded'] is True
        assert 'body' in response
        
        # Verify can decode
        decoded = base64.b64decode(response['body'])
        decompressed = gzip.decompress(decoded)
        result = json.loads(decompressed)
        assert result == data
    
    def test_batch_api_requests(self):
        """Test batch request creation"""
        requests = [
            {'endpoint': 'weather', 'params': {'location': 'Delhi'}},
            {'endpoint': 'prices', 'params': {'crop': 'wheat'}}
        ]
        
        batch = NetworkOptimizer.batch_api_requests(requests)
        
        assert batch['batch'] is True
        assert len(batch['requests']) == 2
        assert 'timestamp' in batch
    
    def test_prioritize_resources(self):
        """Test resource prioritization"""
        resources = [
            {'name': 'low', 'priority': 'low'},
            {'name': 'critical', 'priority': 'critical'},
            {'name': 'medium', 'priority': 'medium'},
            {'name': 'high', 'priority': 'high'}
        ]
        
        prioritized = NetworkOptimizer.prioritize_resources(resources)
        
        assert prioritized[0]['priority'] == 'critical'
        assert prioritized[1]['priority'] == 'high'
        assert prioritized[2]['priority'] == 'medium'
        assert prioritized[3]['priority'] == 'low'
    
    def test_calculate_data_savings(self):
        """Test data savings calculation"""
        savings = NetworkOptimizer.calculate_data_savings(
            original_size=1000,
            optimized_size=300
        )
        
        assert savings['original_size_bytes'] == 1000
        assert savings['optimized_size_bytes'] == 300
        assert savings['savings_bytes'] == 700
        assert savings['savings_percent'] == 70.0
        assert savings['compression_ratio'] == pytest.approx(3.33, rel=0.01)


class TestImageOptimizer:
    """Test ImageOptimizer class"""
    
    def test_get_progressive_sizes_2g(self):
        """Test progressive sizes for 2G"""
        sizes = ImageOptimizer.get_progressive_sizes("2g")
        assert sizes == [160, 320]
    
    def test_get_progressive_sizes_3g(self):
        """Test progressive sizes for 3G"""
        sizes = ImageOptimizer.get_progressive_sizes("3g")
        assert sizes == [320, 640]
    
    def test_generate_webp_config(self):
        """Test WebP config generation"""
        config = ImageOptimizer.generate_webp_config(quality=80)
        
        assert config['format'] == 'webp'
        assert config['quality'] == 80
        assert config['method'] == 6
        assert config['lossless'] is False
    
    def test_create_image_srcset(self):
        """Test srcset creation"""
        srcset = ImageOptimizer.create_image_srcset(
            base_url='https://example.com/image.jpg',
            sizes=[320, 640, 1024],
            format='webp'
        )
        
        assert '320w' in srcset
        assert '640w' in srcset
        assert '1024w' in srcset
        assert 'f=webp' in srcset
    
    def test_get_placeholder_config(self):
        """Test placeholder config"""
        config = ImageOptimizer.get_placeholder_config(width=1000, height=800)
        
        assert config['width'] == 50  # 1000 / 20
        assert config['height'] == 40  # 800 / 20
        assert config['quality'] == 10
        assert config['blur'] == 20


class TestImageProcessor:
    """Test ImageProcessor class"""
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample test image"""
        img = Image.new('RGB', (800, 600), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=90)
        return buffer.getvalue()
    
    def test_optimize_image_resize(self, sample_image):
        """Test image optimization with resizing"""
        optimized, metadata = ImageProcessor.optimize_image(
            sample_image,
            target_width=400,
            quality=75,
            output_format='WEBP'
        )
        
        assert isinstance(optimized, bytes)
        assert metadata['output_format'] == 'WEBP'
        assert metadata['output_dimensions']['width'] == 400
        assert metadata['output_dimensions']['height'] == 300  # Maintains aspect ratio
        assert metadata['optimized_size_bytes'] < metadata['original_size_bytes']
        assert metadata['savings_percent'] > 0
    
    def test_optimize_image_webp(self, sample_image):
        """Test WebP conversion"""
        optimized, metadata = ImageProcessor.optimize_image(
            sample_image,
            quality=75,
            output_format='WEBP'
        )
        
        # WebP should be significantly smaller
        assert metadata['optimized_size_bytes'] < metadata['original_size_bytes']
        assert metadata['savings_percent'] > 30  # At least 30% savings
    
    def test_create_progressive_versions(self, sample_image):
        """Test progressive version creation"""
        versions = ImageProcessor.create_progressive_versions(
            sample_image,
            sizes=[320, 640],
            quality=75
        )
        
        assert '320w' in versions
        assert '640w' in versions
        assert 'data' in versions['320w']
        assert 'metadata' in versions['320w']
        assert 'base64' in versions['320w']
    
    def test_create_placeholder(self, sample_image):
        """Test placeholder creation"""
        placeholder = ImageProcessor.create_placeholder(
            sample_image,
            width=20,
            quality=10
        )
        
        assert isinstance(placeholder, str)
        assert len(placeholder) > 0
        # Placeholder should be very small
        assert len(placeholder) < 1000  # Less than 1KB base64
    
    def test_get_image_info(self, sample_image):
        """Test image info extraction"""
        info = ImageProcessor.get_image_info(sample_image)
        
        assert info['format'] == 'JPEG'
        assert info['width'] == 800
        assert info['height'] == 600
        assert info['aspect_ratio'] == pytest.approx(1.33, rel=0.01)
    
    def test_validate_image_valid(self, sample_image):
        """Test image validation - valid image"""
        is_valid, error = ImageProcessor.validate_image(sample_image, max_size_mb=5)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_image_too_large(self):
        """Test image validation - too large"""
        # Create large image data
        large_data = b'x' * (6 * 1024 * 1024)  # 6MB
        
        is_valid, error = ImageProcessor.validate_image(large_data, max_size_mb=5)
        
        assert is_valid is False
        assert 'too large' in error.lower()
    
    def test_validate_image_invalid_data(self):
        """Test image validation - invalid data"""
        invalid_data = b'not an image'
        
        is_valid, error = ImageProcessor.validate_image(invalid_data)
        
        assert is_valid is False
        assert error is not None


class TestBatchRequestHandler:
    """Test BatchRequestHandler class"""
    
    def test_create_batch_request(self):
        """Test batch request creation"""
        handler = BatchRequestHandler()
        
        requests = [
            {'endpoint': 'test1', 'params': {'id': 1}},
            {'endpoint': 'test2', 'params': {'id': 2}}
        ]
        
        batch = handler.create_batch_request(requests)
        
        assert 'batch_id' in batch
        assert batch['request_count'] == 2
        assert len(batch['requests']) == 2
        assert all('request_id' in req for req in batch['requests'])
    
    def test_process_batch(self):
        """Test batch processing"""
        handler = BatchRequestHandler()
        
        requests = [
            {'endpoint': 'add', 'params': {'a': 1, 'b': 2}},
            {'endpoint': 'multiply', 'params': {'a': 3, 'b': 4}}
        ]
        
        batch = handler.create_batch_request(requests)
        
        # Define handlers
        handler_map = {
            'add': lambda a, b: a + b,
            'multiply': lambda a, b: a * b
        }
        
        response = handler.process_batch(batch, handler_map)
        
        assert response['response_count'] == 2
        assert all(r['success'] for r in response['responses'])
        
        # Check results
        results = {r['endpoint']: r['data'] for r in response['responses']}
        assert results['add'] == 3
        assert results['multiply'] == 12
    
    def test_process_batch_with_error(self):
        """Test batch processing with error"""
        handler = BatchRequestHandler()
        
        requests = [
            {'endpoint': 'success', 'params': {}},
            {'endpoint': 'error', 'params': {}}
        ]
        
        batch = handler.create_batch_request(requests)
        
        def error_handler():
            raise ValueError("Test error")
        
        handler_map = {
            'success': lambda: 'ok',
            'error': error_handler
        }
        
        response = handler.process_batch(batch, handler_map)
        
        assert response['response_count'] == 2
        
        # One success, one error
        success_count = sum(1 for r in response['responses'] if r['success'])
        error_count = sum(1 for r in response['responses'] if not r['success'])
        
        assert success_count == 1
        assert error_count == 1
    
    def test_split_into_batches(self):
        """Test splitting large request list"""
        handler = BatchRequestHandler(max_batch_size=3)
        
        requests = [{'endpoint': f'test{i}'} for i in range(10)]
        
        batches = handler.split_into_batches(requests)
        
        assert len(batches) == 4  # 10 requests / 3 per batch = 4 batches
        assert len(batches[0]['requests']) == 3
        assert len(batches[1]['requests']) == 3
        assert len(batches[2]['requests']) == 3
        assert len(batches[3]['requests']) == 1
    
    def test_merge_batch_responses(self):
        """Test merging batch responses"""
        handler = BatchRequestHandler()
        
        batch_responses = [
            {'responses': [{'id': 1}, {'id': 2}]},
            {'responses': [{'id': 3}, {'id': 4}]}
        ]
        
        merged = handler.merge_batch_responses(batch_responses)
        
        assert merged['merged'] is True
        assert merged['batch_count'] == 2
        assert merged['total_responses'] == 4


class TestBatchRequestQueue:
    """Test BatchRequestQueue class"""
    
    def test_add_request(self):
        """Test adding request to queue"""
        queue = BatchRequestQueue(batch_size=5, auto_flush=False)
        
        request_id = queue.add_request('test', {'param': 'value'})
        
        assert isinstance(request_id, str)
        assert queue.get_queue_size() == 1
    
    def test_auto_flush_on_size(self):
        """Test auto flush when batch size reached"""
        queue = BatchRequestQueue(batch_size=3, auto_flush=False)
        
        queue.add_request('test1', {})
        queue.add_request('test2', {})
        assert queue.get_queue_size() == 2
        
        queue.add_request('test3', {})
        # Should auto-flush
        assert queue.get_queue_size() == 0
    
    def test_manual_flush(self):
        """Test manual flush"""
        queue = BatchRequestQueue(batch_size=10, auto_flush=False)
        
        queue.add_request('test1', {})
        queue.add_request('test2', {})
        
        batch = queue.flush()
        
        assert batch is not None
        assert len(batch['requests']) == 2
        assert queue.get_queue_size() == 0
    
    def test_clear_queue(self):
        """Test clearing queue"""
        queue = BatchRequestQueue(batch_size=10, auto_flush=False)
        
        queue.add_request('test1', {})
        queue.add_request('test2', {})
        
        queue.clear_queue()
        
        assert queue.get_queue_size() == 0


class TestBatchResponseCache:
    """Test BatchResponseCache class"""
    
    def test_cache_set_and_get(self):
        """Test caching response"""
        cache = BatchResponseCache(ttl_seconds=300)
        
        endpoint = 'test'
        params = {'id': 1}
        response = {'result': 'data'}
        
        cache.set(endpoint, params, response)
        cached = cache.get(endpoint, params)
        
        assert cached == response
    
    def test_cache_miss(self):
        """Test cache miss"""
        cache = BatchResponseCache()
        
        cached = cache.get('nonexistent', {})
        
        assert cached is None
    
    def test_cache_expiration(self):
        """Test cache expiration"""
        import time
        
        cache = BatchResponseCache(ttl_seconds=1)
        
        cache.set('test', {}, {'data': 'value'})
        
        # Should be cached
        assert cache.get('test', {}) is not None
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get('test', {}) is None
    
    def test_clear_expired(self):
        """Test clearing expired entries"""
        import time
        
        cache = BatchResponseCache(ttl_seconds=1)
        
        cache.set('test1', {}, {'data': '1'})
        time.sleep(1.1)
        cache.set('test2', {}, {'data': '2'})
        
        cache.clear_expired()
        
        # test1 should be cleared, test2 should remain
        assert cache.get('test1', {}) is None
        assert cache.get('test2', {}) is not None
    
    def test_clear_all(self):
        """Test clearing all cache"""
        cache = BatchResponseCache()
        
        cache.set('test1', {}, {'data': '1'})
        cache.set('test2', {}, {'data': '2'})
        
        cache.clear_all()
        
        assert cache.get('test1', {}) is None
        assert cache.get('test2', {}) is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
