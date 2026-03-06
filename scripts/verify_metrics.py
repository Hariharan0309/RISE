#!/usr/bin/env python3
"""
Metrics Verification Script for RISE Platform
Verifies CloudWatch metrics after deployment
"""

import argparse
import boto3
import sys
from datetime import datetime, timedelta

class MetricsVerifier:
    def __init__(self, environment):
        self.environment = environment
        self.cloudwatch = boto3.client('cloudwatch')
        
    def verify_all_metrics(self):
        """Verify all critical metrics"""
        print(f"[{datetime.now()}] Verifying metrics for {self.environment}")
        
        checks = [
            ('Error Rate', self.verify_error_rate),
            ('Response Time', self.verify_response_time),
            ('Throughput', self.verify_throughput),
            ('Lambda Performance', self.verify_lambda_metrics),
            ('DynamoDB Performance', self.verify_dynamodb_metrics),
            ('API Gateway', self.verify_api_gateway_metrics)
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            print(f"\nVerifying: {check_name}")
            try:
                passed, message = check_func()
                if passed:
                    print(f"  ✓ {message}")
                else:
                    print(f"  ✗ {message}")
                    all_passed = False
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def verify_error_rate(self):
        """Verify error rate is within acceptable limits"""
        error_rate = self.get_metric_average('ErrorRate', minutes=15)
        
        if error_rate < 1:
            return True, f"Error rate: {error_rate:.2f}% (Excellent)"
        elif error_rate < 5:
            return True, f"Error rate: {error_rate:.2f}% (Acceptable)"
        else:
            return False, f"Error rate too high: {error_rate:.2f}%"
    
    def verify_response_time(self):
        """Verify response time is acceptable"""
        p95_latency = self.get_metric_percentile('Latency', 'p95', minutes=15)
        
        if p95_latency < 1000:
            return True, f"P95 latency: {p95_latency:.0f}ms (Excellent)"
        elif p95_latency < 3000:
            return True, f"P95 latency: {p95_latency:.0f}ms (Acceptable)"
        else:
            return False, f"P95 latency too high: {p95_latency:.0f}ms"
    
    def verify_throughput(self):
        """Verify request throughput"""
        request_count = self.get_metric_sum('RequestCount', minutes=15)
        
        if request_count > 0:
            return True, f"Request count: {request_count:.0f} (Active)"
        else:
            return False, "No requests processed"
    
    def verify_lambda_metrics(self):
        """Verify Lambda function metrics"""
        errors = self.get_metric_sum('LambdaErrors', minutes=15)
        throttles = self.get_metric_sum('LambdaThrottles', minutes=15)
        
        if errors == 0 and throttles == 0:
            return True, "No Lambda errors or throttles"
        elif errors < 10 and throttles < 5:
            return True, f"Lambda errors: {errors:.0f}, throttles: {throttles:.0f} (Acceptable)"
        else:
            return False, f"Lambda issues - errors: {errors:.0f}, throttles: {throttles:.0f}"
    
    def verify_dynamodb_metrics(self):
        """Verify DynamoDB metrics"""
        throttles = self.get_metric_sum('DynamoDBThrottles', minutes=15)
        
        if throttles == 0:
            return True, "No DynamoDB throttles"
        elif throttles < 5:
            return True, f"DynamoDB throttles: {throttles:.0f} (Acceptable)"
        else:
            return False, f"DynamoDB throttles too high: {throttles:.0f}"
    
    def verify_api_gateway_metrics(self):
        """Verify API Gateway metrics"""
        errors_4xx = self.get_metric_sum('4XXError', minutes=15)
        errors_5xx = self.get_metric_sum('5XXError', minutes=15)
        
        if errors_5xx == 0:
            return True, f"No 5XX errors (4XX: {errors_4xx:.0f})"
        elif errors_5xx < 10:
            return True, f"5XX errors: {errors_5xx:.0f} (Acceptable)"
        else:
            return False, f"Too many 5XX errors: {errors_5xx:.0f}"
    
    def get_metric_average(self, metric_name, minutes=15):
        """Get average metric value"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        response = self.cloudwatch.get_metric_statistics(
            Namespace='RISE/Application',
            MetricName=metric_name,
            Dimensions=[
                {'Name': 'Environment', 'Value': self.environment}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Average']
        )
        
        if response['Datapoints']:
            return sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
        return 0
    
    def get_metric_percentile(self, metric_name, percentile, minutes=15):
        """Get percentile metric value"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        response = self.cloudwatch.get_metric_statistics(
            Namespace='RISE/Application',
            MetricName=metric_name,
            Dimensions=[
                {'Name': 'Environment', 'Value': self.environment}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            ExtendedStatistics=[percentile]
        )
        
        if response['Datapoints']:
            return sum(dp[percentile] for dp in response['Datapoints']) / len(response['Datapoints'])
        return 0
    
    def get_metric_sum(self, metric_name, minutes=15):
        """Get sum of metric values"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        response = self.cloudwatch.get_metric_statistics(
            Namespace='RISE/Application',
            MetricName=metric_name,
            Dimensions=[
                {'Name': 'Environment', 'Value': self.environment}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Sum']
        )
        
        if response['Datapoints']:
            return sum(dp['Sum'] for dp in response['Datapoints'])
        return 0

def main():
    parser = argparse.ArgumentParser(description='Metrics Verifier')
    parser.add_argument('--environment', required=True, help='Environment to verify')
    
    args = parser.parse_args()
    
    verifier = MetricsVerifier(args.environment)
    
    success = verifier.verify_all_metrics()
    
    if success:
        print(f"\n✓ All metrics verified successfully")
        sys.exit(0)
    else:
        print(f"\n✗ Some metrics failed verification")
        sys.exit(1)

if __name__ == '__main__':
    main()
