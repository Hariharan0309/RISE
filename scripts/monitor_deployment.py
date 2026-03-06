#!/usr/bin/env python3
"""
Deployment Monitoring Script for RISE Platform
Monitors key metrics during and after deployment
"""

import argparse
import boto3
import time
import sys
from datetime import datetime, timedelta

class DeploymentMonitor:
    def __init__(self, environment, duration=600):
        self.environment = environment
        self.duration = duration
        self.cloudwatch = boto3.client('cloudwatch')
        self.sns = boto3.client('sns')
        
    def monitor(self):
        """Monitor deployment for specified duration"""
        print(f"[{datetime.now()}] Starting deployment monitoring for {self.duration}s")
        
        start_time = time.time()
        check_interval = 60  # Check every minute
        
        metrics_history = []
        alerts_triggered = []
        
        while (time.time() - start_time) < self.duration:
            elapsed = int(time.time() - start_time)
            remaining = self.duration - elapsed
            
            print(f"\n[{datetime.now()}] Monitoring... ({elapsed}s elapsed, {remaining}s remaining)")
            
            # Collect metrics
            metrics = self.collect_metrics()
            metrics_history.append(metrics)
            
            # Display current metrics
            self.display_metrics(metrics)
            
            # Check thresholds
            alerts = self.check_thresholds(metrics)
            if alerts:
                alerts_triggered.extend(alerts)
                self.send_alerts(alerts)
            
            # Check if critical failure
            if self.is_critical_failure(metrics):
                print(f"\n✗ CRITICAL FAILURE DETECTED")
                self.send_critical_alert(metrics)
                return False
            
            time.sleep(check_interval)
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"Monitoring Complete - {self.environment}")
        print(f"{'='*60}")
        
        self.print_summary(metrics_history, alerts_triggered)
        
        return len(alerts_triggered) == 0
    
    def collect_metrics(self):
        """Collect CloudWatch metrics"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'error_rate': self.get_metric('ErrorRate', start_time, end_time),
            'latency_p50': self.get_metric('Latency', start_time, end_time, 'p50'),
            'latency_p95': self.get_metric('Latency', start_time, end_time, 'p95'),
            'latency_p99': self.get_metric('Latency', start_time, end_time, 'p99'),
            'request_count': self.get_metric('RequestCount', start_time, end_time),
            'cpu_utilization': self.get_metric('CPUUtilization', start_time, end_time),
            'memory_utilization': self.get_metric('MemoryUtilization', start_time, end_time),
            'lambda_errors': self.get_metric('LambdaErrors', start_time, end_time),
            'lambda_throttles': self.get_metric('LambdaThrottles', start_time, end_time),
            'dynamodb_throttles': self.get_metric('DynamoDBThrottles', start_time, end_time),
            'api_4xx_errors': self.get_metric('4XXError', start_time, end_time),
            'api_5xx_errors': self.get_metric('5XXError', start_time, end_time)
        }
        
        return metrics
    
    def get_metric(self, metric_name, start_time, end_time, statistic='Average'):
        """Get specific metric from CloudWatch"""
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='RISE/Application',
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'Environment', 'Value': self.environment}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=[statistic]
            )
            
            if response['Datapoints']:
                return response['Datapoints'][0][statistic]
            return 0
        except Exception as e:
            print(f"Warning: Could not retrieve {metric_name}: {str(e)}")
            return 0
    
    def display_metrics(self, metrics):
        """Display current metrics"""
        print(f"\nCurrent Metrics:")
        print(f"  Error Rate:          {metrics['error_rate']:.2f}%")
        print(f"  Latency (p50):       {metrics['latency_p50']:.2f}ms")
        print(f"  Latency (p95):       {metrics['latency_p95']:.2f}ms")
        print(f"  Latency (p99):       {metrics['latency_p99']:.2f}ms")
        print(f"  Request Count:       {metrics['request_count']:.0f}")
        print(f"  CPU Utilization:     {metrics['cpu_utilization']:.2f}%")
        print(f"  Memory Utilization:  {metrics['memory_utilization']:.2f}%")
        print(f"  Lambda Errors:       {metrics['lambda_errors']:.0f}")
        print(f"  Lambda Throttles:    {metrics['lambda_throttles']:.0f}")
        print(f"  DynamoDB Throttles:  {metrics['dynamodb_throttles']:.0f}")
        print(f"  API 4XX Errors:      {metrics['api_4xx_errors']:.0f}")
        print(f"  API 5XX Errors:      {metrics['api_5xx_errors']:.0f}")
    
    def check_thresholds(self, metrics):
        """Check if metrics exceed thresholds"""
        alerts = []
        
        thresholds = {
            'error_rate': {'value': 5, 'severity': 'warning'},
            'latency_p95': {'value': 3000, 'severity': 'warning'},
            'latency_p99': {'value': 5000, 'severity': 'warning'},
            'cpu_utilization': {'value': 80, 'severity': 'warning'},
            'memory_utilization': {'value': 85, 'severity': 'warning'},
            'lambda_throttles': {'value': 10, 'severity': 'critical'},
            'dynamodb_throttles': {'value': 5, 'severity': 'critical'},
            'api_5xx_errors': {'value': 50, 'severity': 'critical'}
        }
        
        for metric_name, threshold in thresholds.items():
            if metrics[metric_name] > threshold['value']:
                alert = {
                    'metric': metric_name,
                    'value': metrics[metric_name],
                    'threshold': threshold['value'],
                    'severity': threshold['severity'],
                    'timestamp': metrics['timestamp']
                }
                alerts.append(alert)
                
                severity_icon = '⚠' if threshold['severity'] == 'warning' else '✗'
                print(f"{severity_icon} ALERT: {metric_name} = {metrics[metric_name]:.2f} (threshold: {threshold['value']})")
        
        return alerts
    
    def is_critical_failure(self, metrics):
        """Check if there's a critical failure"""
        critical_conditions = [
            metrics['error_rate'] > 10,  # >10% error rate
            metrics['api_5xx_errors'] > 100,  # >100 5xx errors
            metrics['lambda_throttles'] > 50,  # >50 throttles
            metrics['latency_p99'] > 10000  # >10s latency
        ]
        
        return any(critical_conditions)
    
    def send_alerts(self, alerts):
        """Send alerts via SNS"""
        for alert in alerts:
            message = f"""
RISE Deployment Alert

Environment: {self.environment}
Metric: {alert['metric']}
Current Value: {alert['value']:.2f}
Threshold: {alert['threshold']}
Severity: {alert['severity']}
Timestamp: {alert['timestamp']}
"""
            
            try:
                topic_arn = f"arn:aws:sns:{boto3.session.Session().region_name}:*:rise-deployment-alerts"
                self.sns.publish(
                    TopicArn=topic_arn,
                    Subject=f"RISE {alert['severity'].upper()} Alert - {alert['metric']}",
                    Message=message
                )
            except Exception as e:
                print(f"Warning: Could not send alert: {str(e)}")
    
    def send_critical_alert(self, metrics):
        """Send critical failure alert"""
        message = f"""
CRITICAL DEPLOYMENT FAILURE

Environment: {self.environment}
Timestamp: {datetime.now().isoformat()}

Current Metrics:
- Error Rate: {metrics['error_rate']:.2f}%
- API 5XX Errors: {metrics['api_5xx_errors']:.0f}
- Lambda Throttles: {metrics['lambda_throttles']:.0f}
- Latency P99: {metrics['latency_p99']:.2f}ms

ACTION REQUIRED: Immediate rollback recommended
"""
        
        try:
            topic_arn = f"arn:aws:sns:{boto3.session.Session().region_name}:*:rise-deployment-alerts"
            self.sns.publish(
                TopicArn=topic_arn,
                Subject='CRITICAL: RISE Deployment Failure',
                Message=message
            )
        except Exception as e:
            print(f"Warning: Could not send critical alert: {str(e)}")
    
    def print_summary(self, metrics_history, alerts_triggered):
        """Print monitoring summary"""
        if not metrics_history:
            print("No metrics collected")
            return
        
        # Calculate averages
        avg_error_rate = sum(m['error_rate'] for m in metrics_history) / len(metrics_history)
        avg_latency_p95 = sum(m['latency_p95'] for m in metrics_history) / len(metrics_history)
        total_requests = sum(m['request_count'] for m in metrics_history)
        
        print(f"\nSummary:")
        print(f"  Duration:            {self.duration}s")
        print(f"  Samples Collected:   {len(metrics_history)}")
        print(f"  Avg Error Rate:      {avg_error_rate:.2f}%")
        print(f"  Avg Latency (p95):   {avg_latency_p95:.2f}ms")
        print(f"  Total Requests:      {total_requests:.0f}")
        print(f"  Alerts Triggered:    {len(alerts_triggered)}")
        
        if alerts_triggered:
            print(f"\nAlert Breakdown:")
            warning_count = sum(1 for a in alerts_triggered if a['severity'] == 'warning')
            critical_count = sum(1 for a in alerts_triggered if a['severity'] == 'critical')
            print(f"  Warnings:  {warning_count}")
            print(f"  Critical:  {critical_count}")
        
        # Overall status
        if len(alerts_triggered) == 0:
            print(f"\n✓ Deployment monitoring completed successfully")
        elif critical_count > 0:
            print(f"\n✗ Deployment has critical issues")
        else:
            print(f"\n⚠ Deployment has warnings but is stable")

def main():
    parser = argparse.ArgumentParser(description='Deployment Monitor')
    parser.add_argument('--environment', required=True, help='Environment to monitor')
    parser.add_argument('--duration', type=int, default=600, help='Monitoring duration in seconds')
    
    args = parser.parse_args()
    
    monitor = DeploymentMonitor(args.environment, args.duration)
    
    try:
        success = monitor.monitor()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\nMonitoring interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during monitoring: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
