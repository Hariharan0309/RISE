"""
RISE Network Optimization for Rural Connectivity
Implements progressive loading, compression, and network adaptation for 2G/3G networks
"""

import json
import gzip
import base64
from typing import Dict, Any, List, Optional
from io import BytesIO


class NetworkOptimizer:
    """Network optimization utilities for rural connectivity"""
    
    # Network type thresholds (in Mbps)
    NETWORK_TYPES = {
        "2g": {"downlink": 0.1, "rtt": 500},  # ~100 Kbps, 500ms RTT
        "3g": {"downlink": 1.0, "rtt": 200},  # ~1 Mbps, 200ms RTT
        "4g": {"downlink": 10.0, "rtt": 50},  # ~10 Mbps, 50ms RTT
        "wifi": {"downlink": 50.0, "rtt": 20}  # ~50 Mbps, 20ms RTT
    }
    
    @staticmethod
    def detect_network_type(downlink_mbps: float, rtt_ms: float) -> str:
        """
        Detect network type based on connection speed
        
        Args:
            downlink_mbps: Download speed in Mbps
            rtt_ms: Round-trip time in milliseconds
        
        Returns:
            Network type: '2g', '3g', '4g', or 'wifi'
        """
        if downlink_mbps < 0.5 or rtt_ms > 400:
            return "2g"
        elif downlink_mbps < 5.0 or rtt_ms > 150:
            return "3g"
        elif downlink_mbps < 30.0:
            return "4g"
        else:
            return "wifi"
    
    @staticmethod
    def get_adaptive_config(network_type: str) -> Dict[str, Any]:
        """
        Get adaptive configuration based on network type
        
        Args:
            network_type: '2g', '3g', '4g', or 'wifi'
        
        Returns:
            Configuration dict with optimization settings
        """
        configs = {
            "2g": {
                "image_quality": 30,  # Very low quality
                "image_max_width": 320,
                "enable_webp": True,
                "enable_compression": True,
                "compression_level": 9,  # Maximum compression
                "batch_requests": True,
                "batch_size": 5,
                "prefetch_enabled": False,
                "lazy_load": True,
                "reduce_animations": True,
                "api_timeout": 30000,  # 30 seconds
                "max_concurrent_requests": 2
            },
            "3g": {
                "image_quality": 50,  # Low quality
                "image_max_width": 640,
                "enable_webp": True,
                "enable_compression": True,
                "compression_level": 6,
                "batch_requests": True,
                "batch_size": 3,
                "prefetch_enabled": True,
                "lazy_load": True,
                "reduce_animations": False,
                "api_timeout": 20000,  # 20 seconds
                "max_concurrent_requests": 3
            },
            "4g": {
                "image_quality": 75,  # Medium quality
                "image_max_width": 1024,
                "enable_webp": True,
                "enable_compression": True,
                "compression_level": 3,
                "batch_requests": False,
                "batch_size": 1,
                "prefetch_enabled": True,
                "lazy_load": False,
                "reduce_animations": False,
                "api_timeout": 10000,  # 10 seconds
                "max_concurrent_requests": 6
            },
            "wifi": {
                "image_quality": 90,  # High quality
                "image_max_width": 1920,
                "enable_webp": True,
                "enable_compression": False,
                "compression_level": 1,
                "batch_requests": False,
                "batch_size": 1,
                "prefetch_enabled": True,
                "lazy_load": False,
                "reduce_animations": False,
                "api_timeout": 5000,  # 5 seconds
                "max_concurrent_requests": 10
            }
        }
        
        return configs.get(network_type, configs["3g"])
    
    @staticmethod
    def compress_response(data: Any, compression_level: int = 6) -> bytes:
        """
        Compress API response data using gzip
        
        Args:
            data: Data to compress (will be JSON serialized)
            compression_level: Compression level (1-9, higher = more compression)
        
        Returns:
            Compressed bytes
        """
        # Serialize to JSON
        json_data = json.dumps(data, separators=(',', ':'))  # Compact JSON
        json_bytes = json_data.encode('utf-8')
        
        # Compress with gzip
        compressed = gzip.compress(json_bytes, compresslevel=compression_level)
        
        return compressed
    
    @staticmethod
    def decompress_response(compressed_data: bytes) -> Any:
        """
        Decompress gzip compressed response
        
        Args:
            compressed_data: Compressed bytes
        
        Returns:
            Decompressed and parsed data
        """
        # Decompress
        decompressed = gzip.decompress(compressed_data)
        
        # Parse JSON
        json_str = decompressed.decode('utf-8')
        data = json.loads(json_str)
        
        return data
    
    @staticmethod
    def create_compressed_lambda_response(
        data: Any,
        status_code: int = 200,
        compression_level: int = 6
    ) -> Dict[str, Any]:
        """
        Create Lambda response with gzip compression
        
        Args:
            data: Response data
            status_code: HTTP status code
            compression_level: Compression level (1-9)
        
        Returns:
            Lambda response dict with compressed body
        """
        # Compress data
        compressed = NetworkOptimizer.compress_response(data, compression_level)
        
        # Base64 encode for Lambda
        encoded = base64.b64encode(compressed).decode('utf-8')
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Content-Encoding': 'gzip',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age=300'
            },
            'body': encoded,
            'isBase64Encoded': True
        }
    
    @staticmethod
    def batch_api_requests(requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Batch multiple API requests into a single request
        
        Args:
            requests: List of request dicts with 'endpoint' and 'params'
        
        Returns:
            Batched request structure
        """
        return {
            'batch': True,
            'requests': requests,
            'timestamp': int(time.time() * 1000)
        }
    
    @staticmethod
    def process_batch_response(batch_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process batched API response
        
        Args:
            batch_response: Batched response from server
        
        Returns:
            Dict mapping request IDs to responses
        """
        results = {}
        
        if 'responses' in batch_response:
            for response in batch_response['responses']:
                request_id = response.get('request_id')
                results[request_id] = response.get('data')
        
        return results
    
    @staticmethod
    def prioritize_resources(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prioritize critical resources for loading
        
        Args:
            resources: List of resource dicts with 'type' and 'priority'
        
        Returns:
            Sorted list of resources by priority
        """
        # Priority order: critical > high > medium > low
        priority_order = {
            'critical': 0,
            'high': 1,
            'medium': 2,
            'low': 3
        }
        
        return sorted(
            resources,
            key=lambda r: priority_order.get(r.get('priority', 'medium'), 2)
        )
    
    @staticmethod
    def calculate_data_savings(
        original_size: int,
        optimized_size: int
    ) -> Dict[str, Any]:
        """
        Calculate data savings from optimization
        
        Args:
            original_size: Original data size in bytes
            optimized_size: Optimized data size in bytes
        
        Returns:
            Dict with savings metrics
        """
        savings_bytes = original_size - optimized_size
        savings_percent = (savings_bytes / original_size * 100) if original_size > 0 else 0
        
        return {
            'original_size_bytes': original_size,
            'optimized_size_bytes': optimized_size,
            'savings_bytes': savings_bytes,
            'savings_percent': round(savings_percent, 2),
            'compression_ratio': round(original_size / optimized_size, 2) if optimized_size > 0 else 0
        }


class ImageOptimizer:
    """Image optimization for progressive loading and WebP conversion"""
    
    @staticmethod
    def get_progressive_sizes(network_type: str) -> List[int]:
        """
        Get progressive image sizes based on network type
        
        Args:
            network_type: '2g', '3g', '4g', or 'wifi'
        
        Returns:
            List of image widths for progressive loading
        """
        sizes = {
            "2g": [160, 320],  # Tiny, small
            "3g": [320, 640],  # Small, medium
            "4g": [640, 1024],  # Medium, large
            "wifi": [1024, 1920]  # Large, full
        }
        
        return sizes.get(network_type, sizes["3g"])
    
    @staticmethod
    def generate_webp_config(quality: int = 75) -> Dict[str, Any]:
        """
        Generate WebP conversion configuration
        
        Args:
            quality: WebP quality (0-100)
        
        Returns:
            WebP configuration dict
        """
        return {
            'format': 'webp',
            'quality': quality,
            'method': 6,  # Compression method (0-6, higher = slower but better)
            'lossless': False,
            'alpha_quality': 100
        }
    
    @staticmethod
    def create_image_srcset(
        base_url: str,
        sizes: List[int],
        format: str = 'webp'
    ) -> str:
        """
        Create responsive image srcset attribute
        
        Args:
            base_url: Base image URL
            sizes: List of image widths
            format: Image format ('webp', 'jpg', etc.)
        
        Returns:
            srcset string
        """
        srcset_parts = []
        
        for size in sizes:
            url = f"{base_url}?w={size}&f={format}"
            srcset_parts.append(f"{url} {size}w")
        
        return ", ".join(srcset_parts)
    
    @staticmethod
    def get_placeholder_config(width: int, height: int) -> Dict[str, Any]:
        """
        Get configuration for low-quality image placeholder
        
        Args:
            width: Image width
            height: Image height
        
        Returns:
            Placeholder configuration
        """
        return {
            'width': max(20, width // 20),  # 5% of original
            'height': max(20, height // 20),
            'quality': 10,
            'blur': 20,
            'format': 'webp'
        }


# Import time for batch requests
import time


# Export main classes
__all__ = [
    'NetworkOptimizer',
    'ImageOptimizer'
]
