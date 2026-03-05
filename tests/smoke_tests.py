#!/usr/bin/env python3
"""
Smoke Tests for RISE Platform
Quick validation tests after deployment
"""

import argparse
import requests
import sys
from datetime import datetime

class SmokeTests:
    def __init__(self, environment):
        self.environment = environment
        self.base_url = self.get_base_url()
        self.passed = 0
        self.failed = 0
        
    def get_base_url(self):
        """Get base URL for environment"""
        if self.environment == 'staging':
            return 'https://staging.rise-farming.com'
        elif self.environment == 'production':
            return 'https://rise-farming.com'
        elif 'green' in self.environment:
            return 'https://production-green.rise-farming.com'
        else:
            return f'https://{self.environment}.rise-farming.com'
    
    def run_all_tests(self):
        """Run all smoke tests"""
        print(f"[{datetime.now()}] Running smoke tests for {self.environment}")
        print(f"Base URL: {self.base_url}\n")
        
        tests = [
            ('API Health Check', self.test_api_health),
            ('Authentication', self.test_authentication),
            ('Voice Transcription', self.test_voice_transcription),
            ('Translation Service', self.test_translation),
            ('Crop Diagnosis', self.test_crop_diagnosis),
            ('Market Prices', self.test_market_prices),
            ('Weather Data', self.test_weather_data),
            ('Forum Access', self.test_forum_access)
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Summary
        print(f"\n{'='*60}")
        print(f"Smoke Test Summary")
        print(f"{'='*60}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Total:  {self.passed + self.failed}")
        
        if self.failed == 0:
            print(f"\n✓ All smoke tests passed")
            return True
        else:
            print(f"\n✗ {self.failed} smoke test(s) failed")
            return False
    
    def run_test(self, test_name, test_func):
        """Run individual test"""
        try:
            print(f"Running: {test_name}...", end=' ')
            test_func()
            print(f"✓ PASSED")
            self.passed += 1
        except AssertionError as e:
            print(f"✗ FAILED - {str(e)}")
            self.failed += 1
        except Exception as e:
            print(f"✗ ERROR - {str(e)}")
            self.failed += 1
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{self.base_url}/api/v1/health", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get('status') == 'healthy', "API not healthy"
    
    def test_authentication(self):
        """Test authentication endpoint"""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={
                'phone_number': '+919876543210',
                'password': 'test_password'
            },
            timeout=10
        )
        
        # Should return 200 or 401 (not 500)
        assert response.status_code in [200, 401], f"Unexpected status: {response.status_code}"
    
    def test_voice_transcription(self):
        """Test voice transcription endpoint"""
        response = requests.post(
            f"{self.base_url}/api/v1/voice/transcribe",
            json={
                'audio_url': 's3://test-bucket/test-audio.wav',
                'language': 'hi'
            },
            timeout=15
        )
        
        # Should return 200 or 400 (not 500)
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
    
    def test_translation(self):
        """Test translation service"""
        response = requests.post(
            f"{self.base_url}/api/v1/voice/translate",
            json={
                'text': 'Hello farmer',
                'source_language': 'en',
                'target_language': 'hi'
            },
            timeout=10
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'translated_text' in data, "Missing translated_text in response"
    
    def test_crop_diagnosis(self):
        """Test crop diagnosis endpoint"""
        response = requests.post(
            f"{self.base_url}/api/v1/diagnosis/crop-disease",
            json={
                'image_url': 's3://test-bucket/test-crop.jpg',
                'crop_type': 'wheat'
            },
            timeout=20
        )
        
        # Should return 200 or 400 (not 500)
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
    
    def test_market_prices(self):
        """Test market price endpoint"""
        response = requests.get(
            f"{self.base_url}/api/v1/intelligence/market-prices/wheat/delhi",
            timeout=10
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'prices' in data, "Missing prices in response"
    
    def test_weather_data(self):
        """Test weather data endpoint"""
        response = requests.get(
            f"{self.base_url}/api/v1/intelligence/weather/delhi",
            timeout=10
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'current_weather' in data, "Missing weather data in response"
    
    def test_forum_access(self):
        """Test forum access endpoint"""
        response = requests.get(
            f"{self.base_url}/api/v1/community/forums",
            timeout=10
        )
        
        assert response.status_code in [200, 401], f"Unexpected status: {response.status_code}"

def main():
    parser = argparse.ArgumentParser(description='Smoke Test Runner')
    parser.add_argument('--environment', required=True, help='Environment to test')
    
    args = parser.parse_args()
    
    tester = SmokeTests(args.environment)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
