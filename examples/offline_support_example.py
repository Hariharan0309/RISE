"""
RISE Offline Support Example
Demonstrates offline-first capabilities for rural connectivity
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.offline_storage import get_storage_manager
from infrastructure.sync_manager import get_sync_manager
from infrastructure.offline_config import (
    OFFLINE_FEATURES,
    CACHE_DURATIONS,
    SYNC_PRIORITIES
)
import json
from datetime import datetime


def example_cache_diagnosis():
    """Example: Cache diagnosis data for offline access"""
    print("\n=== Caching Diagnosis Data ===")
    
    storage_manager = get_storage_manager()
    
    # Sample diagnosis data
    diagnosis_data = {
        "diagnosis_id": "diag_12345",
        "user_id": "farmer_9876543210",
        "image_s3_key": "images/crop-photos/farmer_9876543210/20240115-wheat-leaf.jpg",
        "diagnosis_result": {
            "disease": "Wheat Rust",
            "confidence": 0.92,
            "severity": "moderate"
        },
        "treatment_recommended": {
            "fungicide": "Propiconazole",
            "dosage": "250ml per acre",
            "timing": "Apply within 48 hours"
        },
        "created_timestamp": int(datetime.now().timestamp())
    }
    
    # Prepare for offline caching
    cached_data = storage_manager.cache_diagnosis_history(diagnosis_data)
    
    print(f"Diagnosis ID: {cached_data['diagnosis_id']}")
    print(f"Disease: {cached_data['diagnosis_result']['disease']}")
    print(f"Cached at: {datetime.fromtimestamp(cached_data['cached_at'])}")
    print(f"Expires at: {datetime.fromtimestamp(cached_data['expires_at'])}")
    print(f"Cache duration: {CACHE_DURATIONS['diagnosis_history'] / 86400} days")
    
    return cached_data


def example_cache_weather():
    """Example: Cache weather data for offline access"""
    print("\n=== Caching Weather Data ===")
    
    storage_manager = get_storage_manager()
    
    # Sample weather data
    weather_data = {
        "temperature": 28,
        "humidity": 65,
        "rainfall_probability": 40,
        "wind_speed": 12,
        "forecast": [
            {"day": "Today", "temp_max": 32, "temp_min": 22, "condition": "Partly Cloudy"},
            {"day": "Tomorrow", "temp_max": 30, "temp_min": 21, "condition": "Sunny"},
            {"day": "Day 3", "temp_max": 29, "temp_min": 20, "condition": "Rainy"}
        ],
        "farming_advice": "Good conditions for irrigation. Avoid pesticide application tomorrow."
    }
    
    location = "Lucknow, Uttar Pradesh"
    
    # Prepare for offline caching
    cached_data = storage_manager.cache_weather_data(location, weather_data)
    
    print(f"Location: {cached_data['location']}")
    print(f"Temperature: {cached_data['data']['temperature']}°C")
    print(f"Humidity: {cached_data['data']['humidity']}%")
    print(f"Cached at: {datetime.fromtimestamp(cached_data['cached_at'])}")
    print(f"Cache duration: {CACHE_DURATIONS['weather_data'] / 3600} hours")
    
    return cached_data


def example_cache_market_prices():
    """Example: Cache market price data for offline access"""
    print("\n=== Caching Market Price Data ===")
    
    storage_manager = get_storage_manager()
    
    # Sample market price data
    price_data = {
        "current_price": 2150,
        "currency": "INR",
        "unit": "quintal",
        "market_name": "Lucknow Mandi",
        "price_trend": "increasing",
        "historical_prices": [
            {"date": "2024-01-10", "price": 2100},
            {"date": "2024-01-11", "price": 2120},
            {"date": "2024-01-12", "price": 2140},
            {"date": "2024-01-13", "price": 2150}
        ],
        "nearby_markets": [
            {"name": "Kanpur Mandi", "price": 2180, "distance_km": 80},
            {"name": "Sitapur Mandi", "price": 2130, "distance_km": 90}
        ]
    }
    
    crop = "wheat"
    location = "Lucknow"
    
    # Prepare for offline caching
    cached_data = storage_manager.cache_market_prices(crop, location, price_data)
    
    print(f"Crop: {cached_data['crop']}")
    print(f"Location: {cached_data['location']}")
    print(f"Current Price: ₹{cached_data['data']['current_price']}/{cached_data['data']['unit']}")
    print(f"Trend: {cached_data['data']['price_trend']}")
    print(f"Cache duration: {CACHE_DURATIONS['market_prices'] / 3600} hours")
    
    return cached_data


def example_create_offline_action():
    """Example: Create offline action to be synced later"""
    print("\n=== Creating Offline Action ===")
    
    storage_manager = get_storage_manager()
    
    # Example: User posts to forum while offline
    action_data = {
        "user_id": "farmer_9876543210",
        "title": "Best practices for wheat irrigation",
        "content": "I've been experimenting with drip irrigation for wheat. Results are promising!",
        "category": "irrigation",
        "language": "en"
    }
    
    # Create offline action
    offline_action = storage_manager.create_offline_action("forum_post", action_data)
    
    print(f"Action ID: {offline_action['action_id']}")
    print(f"Action Type: {offline_action['action_type']}")
    print(f"Priority: {SYNC_PRIORITIES.get(offline_action['action_type'], 10)}")
    print(f"Status: {offline_action['sync_status']}")
    print(f"Created: {offline_action['created_at']}")
    print("\nThis action will be synced when connection is restored.")
    
    return offline_action


def example_sync_manager():
    """Example: Demonstrate sync manager functionality"""
    print("\n=== Sync Manager ===")
    
    sync_manager = get_sync_manager()
    
    # Get sync status
    status = sync_manager.get_sync_status()
    
    print(f"Sync in progress: {status['sync_in_progress']}")
    print(f"Pending actions: {status['pending_count']}")
    
    # Show sync priorities
    print("\nSync Priorities (1 = highest):")
    for action_type, priority in SYNC_PRIORITIES.items():
        print(f"  {priority}. {action_type}")
    
    return status


def example_offline_features():
    """Example: Show available offline features"""
    print("\n=== Offline Features ===")
    
    print("Features available without internet connection:")
    for feature, available in OFFLINE_FEATURES.items():
        status = "✓" if available else "✗"
        feature_name = feature.replace("_", " ").title()
        print(f"  {status} {feature_name}")


def example_storage_stats():
    """Example: Get storage statistics"""
    print("\n=== Storage Statistics ===")
    
    storage_manager = get_storage_manager()
    stats = storage_manager.get_storage_stats()
    
    print(f"IndexedDB Used: {stats['indexeddb_used_mb']} MB")
    print(f"Cache Used: {stats['cache_used_mb']} MB")
    print(f"Total Limit: {stats['total_limit_mb']} MB")
    print(f"Diagnoses Cached: {stats['diagnosis_count']}")
    print(f"Weather Locations: {stats['cached_weather_locations']}")
    print(f"Market Prices: {stats['cached_market_prices']}")
    print(f"Pending Sync: {stats['pending_sync_actions']}")


def example_generate_scripts():
    """Example: Generate JavaScript for offline support"""
    print("\n=== Generating Offline Scripts ===")
    
    storage_manager = get_storage_manager()
    sync_manager = get_sync_manager()
    
    # Generate IndexedDB init script
    indexeddb_script = storage_manager.generate_indexeddb_init_script()
    print(f"IndexedDB script length: {len(indexeddb_script)} characters")
    
    # Generate sync script
    sync_script = sync_manager.generate_sync_script()
    print(f"Sync script length: {len(sync_script)} characters")
    
    # Generate storage check script
    storage_script = storage_manager.generate_storage_check_script()
    print(f"Storage check script length: {len(storage_script)} characters")
    
    print("\nThese scripts are injected into the Streamlit app for offline functionality.")


def main():
    """Run all offline support examples"""
    print("=" * 60)
    print("RISE Offline Support Examples")
    print("Demonstrating offline-first capabilities for rural areas")
    print("=" * 60)
    
    # Show offline features
    example_offline_features()
    
    # Cache examples
    example_cache_diagnosis()
    example_cache_weather()
    example_cache_market_prices()
    
    # Offline action example
    example_create_offline_action()
    
    # Sync manager
    example_sync_manager()
    
    # Storage stats
    example_storage_stats()
    
    # Generate scripts
    example_generate_scripts()
    
    print("\n" + "=" * 60)
    print("Examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
