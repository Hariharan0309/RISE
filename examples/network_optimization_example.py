"""
RISE Network Optimization Example
Demonstrates how to use network optimization features for rural connectivity
"""

import sys
import os
import json
from PIL import Image
import io

# Add infrastructure to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'infrastructure'))

from network_optimization import NetworkOptimizer, ImageOptimizer
from image_optimizer import ImageProcessor
from batch_request_handler import BatchRequestHandler, BatchRequestQueue


def example_1_network_detection():
    """Example 1: Detect network type and get adaptive configuration"""
    
    print("=" * 60)
    print("Example 1: Network Detection and Adaptive Configuration")
    print("=" * 60)
    
    # Simulate different network conditions
    network_scenarios = [
        {"name": "Rural 2G", "downlink": 0.1, "rtt": 500},
        {"name": "Rural 3G", "downlink": 1.0, "rtt": 200},
        {"name": "Urban 4G", "downlink": 10.0, "rtt": 50},
        {"name": "WiFi", "downlink": 50.0, "rtt": 20}
    ]
    
    for scenario in network_scenarios:
        network_type = NetworkOptimizer.detect_network_type(
            downlink_mbps=scenario["downlink"],
            rtt_ms=scenario["rtt"]
        )
        
        config = NetworkOptimizer.get_adaptive_config(network_type)
        
        print(f"\n{scenario['name']}:")
        print(f"  Network Type: {network_type.upper()}")
        print(f"  Image Quality: {config['image_quality']}%")
        print(f"  Max Image Width: {config['image_max_width']}px")
        print(f"  Compression Level: {config['compression_level']}/9")
        print(f"  Batch Requests: {config['batch_requests']}")
        print(f"  Batch Size: {config['batch_size']}")
        print(f"  Max Concurrent: {config['max_concurrent_requests']}")


def example_2_api_compression():
    """Example 2: Compress API responses"""
    
    print("\n" + "=" * 60)
    print("Example 2: API Response Compression")
    print("=" * 60)
    
    # Sample API response
    api_response = {
        "weather": {
            "location": "Delhi",
            "temperature": 28,
            "humidity": 65,
            "forecast": [
                {"day": "Today", "temp": 28, "condition": "Partly Cloudy"},
                {"day": "Tomorrow", "temp": 30, "condition": "Sunny"},
                {"day": "Day 3", "temp": 27, "condition": "Rainy"}
            ]
        },
        "market_prices": [
            {"crop": "Wheat", "price": 2500, "unit": "quintal"},
            {"crop": "Rice", "price": 3200, "unit": "quintal"},
            {"crop": "Cotton", "price": 6800, "unit": "quintal"}
        ]
    }
    
    # Original size
    original_json = json.dumps(api_response)
    original_size = len(original_json.encode('utf-8'))
    
    print(f"\nOriginal Response Size: {original_size} bytes")
    
    # Compress with different levels
    for level in [1, 6, 9]:
        compressed = NetworkOptimizer.compress_response(api_response, compression_level=level)
        compressed_size = len(compressed)
        
        savings = NetworkOptimizer.calculate_data_savings(original_size, compressed_size)
        
        print(f"\nCompression Level {level}:")
        print(f"  Compressed Size: {compressed_size} bytes")
        print(f"  Savings: {savings['savings_bytes']} bytes ({savings['savings_percent']}%)")
        print(f"  Compression Ratio: {savings['compression_ratio']}:1")
    
    # Test decompression
    compressed = NetworkOptimizer.compress_response(api_response)
    decompressed = NetworkOptimizer.decompress_response(compressed)
    
    print(f"\n✅ Decompression successful: {decompressed == api_response}")


def example_3_image_optimization():
    """Example 3: Optimize images for different networks"""
    
    print("\n" + "=" * 60)
    print("Example 3: Image Optimization")
    print("=" * 60)
    
    # Create a sample image
    img = Image.new('RGB', (1920, 1080), color='green')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=90)
    image_data = buffer.getvalue()
    
    original_size = len(image_data)
    print(f"\nOriginal Image: 1920x1080 JPEG")
    print(f"Original Size: {original_size / 1024:.2f} KB")
    
    # Optimize for different networks
    network_configs = {
        "2g": {"width": 320, "quality": 30},
        "3g": {"width": 640, "quality": 50},
        "4g": {"width": 1024, "quality": 75},
        "wifi": {"width": 1920, "quality": 90}
    }
    
    for network, config in network_configs.items():
        optimized, metadata = ImageProcessor.optimize_image(
            image_data,
            target_width=config["width"],
            quality=config["quality"],
            output_format='WEBP'
        )
        
        print(f"\n{network.upper()} Optimization:")
        print(f"  Dimensions: {metadata['output_dimensions']['width']}x{metadata['output_dimensions']['height']}")
        print(f"  Size: {metadata['optimized_size_bytes'] / 1024:.2f} KB")
        print(f"  Savings: {metadata['savings_percent']:.1f}%")
        print(f"  Format: {metadata['output_format']}")


def example_4_progressive_loading():
    """Example 4: Create progressive image versions"""
    
    print("\n" + "=" * 60)
    print("Example 4: Progressive Image Loading")
    print("=" * 60)
    
    # Create sample image
    img = Image.new('RGB', (1600, 1200), color='blue')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    image_data = buffer.getvalue()
    
    print(f"\nOriginal Image: {len(image_data) / 1024:.2f} KB")
    
    # Create progressive versions
    versions = ImageProcessor.create_progressive_versions(
        image_data,
        sizes=[320, 640, 1024],
        quality=75
    )
    
    print("\nProgressive Versions:")
    for size_key, version_data in versions.items():
        metadata = version_data['metadata']
        print(f"\n  {size_key}:")
        print(f"    Dimensions: {metadata['output_dimensions']['width']}x{metadata['output_dimensions']['height']}")
        print(f"    Size: {metadata['optimized_size_bytes'] / 1024:.2f} KB")
        print(f"    Savings: {metadata['savings_percent']:.1f}%")
    
    # Create placeholder
    placeholder = ImageProcessor.create_placeholder(image_data, width=20, quality=10)
    placeholder_size = len(placeholder)
    
    print(f"\nPlaceholder:")
    print(f"  Base64 Size: {placeholder_size} bytes")
    print(f"  Savings: {(1 - placeholder_size / len(image_data)) * 100:.1f}%")
    print(f"  ✅ Instant display with {placeholder_size} bytes!")


def example_5_batch_requests():
    """Example 5: Batch multiple API requests"""
    
    print("\n" + "=" * 60)
    print("Example 5: Batch API Requests")
    print("=" * 60)
    
    # Create batch handler
    handler = BatchRequestHandler()
    
    # Define multiple requests
    requests = [
        {'endpoint': 'weather', 'params': {'location': 'Delhi'}},
        {'endpoint': 'market_prices', 'params': {'crop': 'wheat', 'location': 'Delhi'}},
        {'endpoint': 'schemes', 'params': {'user_id': 'farmer123'}},
        {'endpoint': 'forum_posts', 'params': {'limit': 5}}
    ]
    
    print(f"\nBatching {len(requests)} requests:")
    for req in requests:
        print(f"  - {req['endpoint']}")
    
    # Create batch
    batch = handler.create_batch_request(requests)
    
    print(f"\nBatch ID: {batch['batch_id']}")
    print(f"Request Count: {batch['request_count']}")
    
    # Define mock handlers
    def get_weather(location):
        return {'location': location, 'temp': 28, 'condition': 'Sunny'}
    
    def get_market_prices(crop, location):
        return {'crop': crop, 'location': location, 'price': 2500}
    
    def get_schemes(user_id):
        return {'user_id': user_id, 'schemes': ['PM-KISAN', 'Soil Health Card']}
    
    def get_forum_posts(limit):
        return {'posts': [f'Post {i}' for i in range(limit)], 'total': limit}
    
    handler_map = {
        'weather': get_weather,
        'market_prices': get_market_prices,
        'schemes': get_schemes,
        'forum_posts': get_forum_posts
    }
    
    # Process batch
    response = handler.process_batch(batch, handler_map)
    
    print(f"\nBatch Response:")
    print(f"  Response Count: {response['response_count']}")
    print(f"  Success Rate: {sum(1 for r in response['responses'] if r['success'])}/{response['response_count']}")
    
    print("\nResults:")
    for resp in response['responses']:
        if resp['success']:
            print(f"  ✅ {resp['endpoint']}: {resp.get('duration_ms', 0)}ms")
        else:
            print(f"  ❌ {resp['endpoint']}: {resp.get('error', 'Unknown error')}")


def example_6_request_queue():
    """Example 6: Auto-batching request queue"""
    
    print("\n" + "=" * 60)
    print("Example 6: Auto-Batching Request Queue")
    print("=" * 60)
    
    # Create queue with auto-batching
    queue = BatchRequestQueue(
        batch_size=3,  # Flush after 3 requests
        max_wait_ms=1000,  # Or after 1 second
        auto_flush=False  # Manual control for demo
    )
    
    print("\nAdding requests to queue (batch size: 3):")
    
    # Add requests one by one
    queue.add_request('weather', {'location': 'Mumbai'})
    print(f"  Request 1 added - Queue size: {queue.get_queue_size()}")
    
    queue.add_request('market_prices', {'crop': 'rice'})
    print(f"  Request 2 added - Queue size: {queue.get_queue_size()}")
    
    queue.add_request('schemes', {'user_id': 'farmer456'})
    print(f"  Request 3 added - Queue size: {queue.get_queue_size()}")
    
    # Note: Queue auto-flushed when size reached 3
    print(f"\n✅ Queue auto-flushed when batch size (3) was reached")
    print(f"  Queue size after auto-flush: {queue.get_queue_size()}")


def example_7_resource_prioritization():
    """Example 7: Prioritize critical resources"""
    
    print("\n" + "=" * 60)
    print("Example 7: Resource Prioritization")
    print("=" * 60)
    
    # Define resources with priorities
    resources = [
        {'name': 'app.js', 'type': 'script', 'priority': 'critical', 'size': '50KB'},
        {'name': 'logo.png', 'type': 'image', 'priority': 'high', 'size': '10KB'},
        {'name': 'banner.jpg', 'type': 'image', 'priority': 'low', 'size': '200KB'},
        {'name': 'styles.css', 'type': 'style', 'priority': 'critical', 'size': '20KB'},
        {'name': 'analytics.js', 'type': 'script', 'priority': 'low', 'size': '30KB'},
        {'name': 'icon.svg', 'type': 'image', 'priority': 'medium', 'size': '5KB'}
    ]
    
    print("\nOriginal Resource Order:")
    for i, res in enumerate(resources, 1):
        print(f"  {i}. {res['name']} ({res['priority']}) - {res['size']}")
    
    # Prioritize
    prioritized = NetworkOptimizer.prioritize_resources(resources)
    
    print("\nPrioritized Loading Order:")
    for i, res in enumerate(prioritized, 1):
        print(f"  {i}. {res['name']} ({res['priority']}) - {res['size']}")
    
    print("\n✅ Critical resources load first!")


def example_8_data_savings_calculation():
    """Example 8: Calculate total data savings"""
    
    print("\n" + "=" * 60)
    print("Example 8: Data Savings Calculation")
    print("=" * 60)
    
    # Simulate a typical farming session
    session_data = {
        "Crop diagnosis image": {"original": 2500000, "optimized": 150000},
        "Weather API response": {"original": 45000, "optimized": 8000},
        "Market prices (5 crops)": {"original": 25000, "optimized": 5000},
        "Forum posts (10 posts)": {"original": 60000, "optimized": 12000},
        "Scheme information": {"original": 80000, "optimized": 15000}
    }
    
    print("\nTypical Farming Session Data Usage:")
    print("-" * 60)
    
    total_original = 0
    total_optimized = 0
    
    for feature, sizes in session_data.items():
        original = sizes["original"]
        optimized = sizes["optimized"]
        
        total_original += original
        total_optimized += optimized
        
        savings = NetworkOptimizer.calculate_data_savings(original, optimized)
        
        print(f"\n{feature}:")
        print(f"  Original: {original / 1024:.1f} KB")
        print(f"  Optimized: {optimized / 1024:.1f} KB")
        print(f"  Savings: {savings['savings_percent']:.1f}%")
    
    # Total savings
    total_savings = NetworkOptimizer.calculate_data_savings(total_original, total_optimized)
    
    print("\n" + "=" * 60)
    print("TOTAL SESSION:")
    print(f"  Original: {total_original / 1024 / 1024:.2f} MB")
    print(f"  Optimized: {total_optimized / 1024 / 1024:.2f} MB")
    print(f"  Savings: {total_savings['savings_bytes'] / 1024 / 1024:.2f} MB ({total_savings['savings_percent']:.1f}%)")
    
    # Monthly projection
    sessions_per_month = 30
    monthly_original = total_original * sessions_per_month / 1024 / 1024
    monthly_optimized = total_optimized * sessions_per_month / 1024 / 1024
    monthly_savings = monthly_original - monthly_optimized
    
    print(f"\nMONTHLY PROJECTION (30 sessions):")
    print(f"  Without optimization: {monthly_original:.1f} MB/month")
    print(f"  With optimization: {monthly_optimized:.1f} MB/month")
    print(f"  Savings: {monthly_savings:.1f} MB/month")
    
    # Cost savings (assuming ₹10 per GB)
    cost_per_gb = 10
    monthly_cost_savings = (monthly_savings / 1024) * cost_per_gb
    
    print(f"\nCOST SAVINGS:")
    print(f"  Monthly: ₹{monthly_cost_savings:.2f} per farmer")
    print(f"  For 10,000 farmers: ₹{monthly_cost_savings * 10000:.2f}/month")


def main():
    """Run all examples"""
    
    print("\n" + "=" * 60)
    print("RISE NETWORK OPTIMIZATION EXAMPLES")
    print("Optimizing for Rural 2G/3G Networks")
    print("=" * 60)
    
    try:
        example_1_network_detection()
        example_2_api_compression()
        example_3_image_optimization()
        example_4_progressive_loading()
        example_5_batch_requests()
        example_6_request_queue()
        example_7_resource_prioritization()
        example_8_data_savings_calculation()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
