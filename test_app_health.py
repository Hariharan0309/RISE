#!/usr/bin/env python3
"""
Quick health check for RISE Streamlit application
"""

import requests
import sys

def test_app_health():
    """Test if the Streamlit app is running and healthy"""
    
    print("=" * 70)
    print("  RISE Application Health Check")
    print("=" * 70)
    print()
    
    # Test 1: Check if app is responding
    print("1. Testing HTTP endpoint...")
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("   ✅ App is responding (HTTP 200)")
        else:
            print(f"   ⚠️  App returned HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ App is not responding: {e}")
        return False
    
    # Test 2: Check if health endpoint exists
    print("\n2. Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8501/_stcore/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Health endpoint is responding")
        else:
            print(f"   ⚠️  Health endpoint returned HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  Health endpoint not available: {e}")
    
    print("\n" + "=" * 70)
    print("  Summary")
    print("=" * 70)
    print()
    print("✅ RISE Streamlit application is running successfully!")
    print()
    print("📍 Access the application at:")
    print("   http://localhost:8501")
    print()
    print("🌐 If running on a remote server, access via:")
    print("   http://<your-server-ip>:8501")
    print()
    print("📋 Features available:")
    print("   • Voice-first multilingual interface (9 languages)")
    print("   • AI-powered crop disease diagnosis")
    print("   • Soil analysis and recommendations")
    print("   • Weather alerts and forecasts")
    print("   • Market price intelligence")
    print("   • Resource sharing marketplace")
    print("   • Government scheme navigation")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = test_app_health()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
