#!/usr/bin/env python3
"""
Health Check Script for RISE Platform
Validates deployment health before traffic switch
"""

import argparse
import requests
import time
import sys
from datetime import datetime

class HealthChecker:
    def __init__(self, environment, timeout=300):
        self.environment = environment
        self.timeout = timeout
        self.base_url = self.get_base_url()
        
    def get_base_url(self):
        """Get base URL for environment"""
        if 'staging' in self.environment:
            return 'https://staging.rise-farming.com'
        elif 'green' in self.environment:
            return 'https://production-green.rise-farming.com'
        else:
            return 'https://rise-farming.com'
    
    def run_all_checks(self):
        """Run all health checks"""
        print(f"[{datetime.now()}] Starting health checks for {self.environment}")
        
        checks = [
            ('API Health', self.check_api_health),
            ('Database Connectivity', self.check_database),
            ('S3 Access', self.check_s3_access),
            ('Bedrock Integration', self.check_bedrock),
            ('Voice Services', self.check_voice_services),
            ('Translation Services', self.check_translation),
            ('Response Time', self.check_response_time),
            ('Error Rate', self.check_error_rate)
        ]
        
        results = {}
        all_passed = True
        
        for check_name, check_func in checks:
            print(f"\n[{datetime.now()}] Running: {check_name}")
            try:
                passed, message = check_func()
                results[check_name] = {'passed': passed, 'message': message}
                
                if passed:
                    print(f"✓ {check_name}: PASSED - {message}")
                else:
                    print(f"✗ {check_name}: FAILED - {message}")
                    all_passed = False
            except Exception as e:
                print(f"✗ {check_name}: ERROR - {str(e)}")
                results[check_name] = {'passed': False, 'message': str(e)}
                all_passed = False
        
        # Summary
        print(f"\n{'='*60}")
        print(f"Health Check Summary for {self.environment}")
        print(f"{'='*60}")
        
        passed_count = sum(1 for r in results.values() if r['passed'])
        total_count = len(results)
        
        print(f"Passed: {passed_count}/{total_count}")
        print(f"Status: {'✓ ALL CHECKS PASSED' if all_passed else '✗ SOME CHECKS FAILED'}")
        
        return all_passed
    
    def check_api_health(self):
        """Check API health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    return True, f"API healthy - {data.get('version')}"
            
            return False, f"API unhealthy - Status: {response.status_code}"
        except Exception as e:
            return False, f"API unreachable - {str(e)}"
    
    def check_database(self):
        """Check database connectivity"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health/database", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('database_status') == 'connected':
                    return True, f"Database connected - Latency: {data.get('latency_ms')}ms"
            
            return False, "Database connection failed"
        except Exception as e:
            return False, f"Database check error - {str(e)}"
    
    def check_s3_access(self):
        """Check S3 bucket access"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health/storage", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('s3_status') == 'accessible':
                    return True, "S3 buckets accessible"
            
            return False, "S3 access failed"
        except Exception as e:
            return False, f"S3 check error - {str(e)}"
    
    def check_bedrock(self):
        """Check Amazon Bedrock integration"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/health/bedrock",
                json={'test_prompt': 'Hello'},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('bedrock_status') == 'operational':
                    return True, f"Bedrock operational - Model: {data.get('model')}"
            
            return False, "Bedrock integration failed"
        except Exception as e:
            return False, f"Bedrock check error - {str(e)}"
    
    def check_voice_services(self):
        """Check voice processing services"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health/voice", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                transcribe_ok = data.get('transcribe_status') == 'available'
                polly_ok = data.get('polly_status') == 'available'
                
                if transcribe_ok and polly_ok:
                    return True, "Voice services operational"
            
            return False, "Voice services unavailable"
        except Exception as e:
            return False, f"Voice check error - {str(e)}"
    
    def check_translation(self):
        """Check translation services"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/health/translation",
                json={'text': 'Hello', 'target_language': 'hi'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('translation_status') == 'operational':
                    return True, f"Translation operational - Languages: {data.get('supported_languages')}"
            
            return False, "Translation service failed"
        except Exception as e:
            return False, f"Translation check error - {str(e)}"
    
    def check_response_time(self):
        """Check API response time"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=10)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if response.status_code == 200 and response_time < 3000:
                return True, f"Response time: {response_time:.2f}ms"
            
            return False, f"Response time too high: {response_time:.2f}ms"
        except Exception as e:
            return False, f"Response time check error - {str(e)}"
    
    def check_error_rate(self):
        """Check error rate from CloudWatch"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health/metrics", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                error_rate = data.get('error_rate_percent', 0)
                
                if error_rate < 5:  # Less than 5% error rate
                    return True, f"Error rate: {error_rate}%"
                else:
                    return False, f"Error rate too high: {error_rate}%"
            
            return False, "Could not retrieve error metrics"
        except Exception as e:
            return False, f"Error rate check failed - {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='Health Check Runner')
    parser.add_argument('--environment', required=True, help='Environment to check')
    parser.add_argument('--timeout', type=int, default=300, help='Timeout in seconds')
    
    args = parser.parse_args()
    
    checker = HealthChecker(args.environment, args.timeout)
    
    # Run checks with retry logic
    max_retries = 3
    retry_delay = 30
    
    for attempt in range(max_retries):
        print(f"\n{'='*60}")
        print(f"Health Check Attempt {attempt + 1}/{max_retries}")
        print(f"{'='*60}\n")
        
        if checker.run_all_checks():
            print(f"\n✓ All health checks passed on attempt {attempt + 1}")
            sys.exit(0)
        
        if attempt < max_retries - 1:
            print(f"\n⚠ Health checks failed. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    print(f"\n✗ Health checks failed after {max_retries} attempts")
    sys.exit(1)

if __name__ == '__main__':
    main()
