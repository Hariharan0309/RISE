#!/usr/bin/env python3
"""
Blue-Green Deployment Script for RISE Platform
Manages blue-green deployment strategy for zero-downtime deployments
"""

import argparse
import boto3
import json
import time
import sys
from datetime import datetime

class BlueGreenDeployment:
    def __init__(self, environment):
        self.environment = environment
        self.elbv2 = boto3.client('elbv2')
        self.cloudformation = boto3.client('cloudformation')
        self.route53 = boto3.client('route53')
        self.cloudwatch = boto3.client('cloudwatch')
        
    def prepare(self):
        """Prepare for blue-green deployment"""
        print(f"[{datetime.now()}] Preparing blue-green deployment for {self.environment}")
        
        # Get current active environment (blue)
        current_stack = self.get_active_stack()
        print(f"Current active stack: {current_stack}")
        
        # Tag current environment as blue
        self.tag_stack(current_stack, 'blue')
        
        # Prepare green environment configuration
        green_config = self.create_green_config(current_stack)
        
        print(f"[{datetime.now()}] Blue-green preparation complete")
        return green_config
    
    def switch(self):
        """Switch traffic from blue to green"""
        print(f"[{datetime.now()}] Switching traffic to green environment")
        
        # Get target groups
        blue_tg = self.get_target_group('blue')
        green_tg = self.get_target_group('green')
        
        # Get load balancer listener
        listener_arn = self.get_listener_arn()
        
        # Gradually shift traffic (canary deployment)
        traffic_percentages = [10, 25, 50, 75, 100]
        
        for percentage in traffic_percentages:
            print(f"[{datetime.now()}] Shifting {percentage}% traffic to green")
            
            self.update_listener_rules(
                listener_arn,
                green_tg,
                blue_tg,
                percentage
            )
            
            # Wait and monitor
            time.sleep(60)
            
            # Check health metrics
            if not self.check_health_metrics('green'):
                print(f"[{datetime.now()}] Health check failed at {percentage}%")
                return False
        
        # Update Route53 to point to green
        self.update_route53('green')
        
        print(f"[{datetime.now()}] Traffic switch complete")
        return True
    
    def rollback(self):
        """Rollback to blue environment"""
        print(f"[{datetime.now()}] Rolling back to blue environment")
        
        # Get target groups
        blue_tg = self.get_target_group('blue')
        green_tg = self.get_target_group('green')
        
        # Get load balancer listener
        listener_arn = self.get_listener_arn()
        
        # Immediately switch all traffic back to blue
        self.update_listener_rules(
            listener_arn,
            blue_tg,
            green_tg,
            0  # 0% to green = 100% to blue
        )
        
        # Update Route53 back to blue
        self.update_route53('blue')
        
        # Send alert
        self.send_alert('Deployment rolled back to blue environment')
        
        print(f"[{datetime.now()}] Rollback complete")
        return True
    
    def cleanup(self):
        """Cleanup old blue environment after successful green deployment"""
        print(f"[{datetime.now()}] Cleaning up old blue environment")
        
        # Wait for monitoring period (24 hours in production)
        monitoring_period = 3600  # 1 hour for demo
        print(f"Waiting {monitoring_period}s monitoring period before cleanup")
        time.sleep(monitoring_period)
        
        # Get blue stack
        blue_stack = self.get_stack_by_tag('blue')
        
        if blue_stack:
            # Delete blue stack
            print(f"Deleting blue stack: {blue_stack}")
            self.cloudformation.delete_stack(StackName=blue_stack)
            
            # Wait for deletion
            waiter = self.cloudformation.get_waiter('stack_delete_complete')
            waiter.wait(StackName=blue_stack)
        
        # Rename green to blue for next deployment
        green_stack = self.get_stack_by_tag('green')
        self.tag_stack(green_stack, 'blue')
        
        print(f"[{datetime.now()}] Cleanup complete")
        return True
    
    def get_active_stack(self):
        """Get currently active CloudFormation stack"""
        response = self.cloudformation.list_stacks(
            StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE']
        )
        
        for stack in response['StackSummaries']:
            if self.environment in stack['StackName']:
                return stack['StackName']
        
        return None
    
    def tag_stack(self, stack_name, color):
        """Tag stack with blue or green"""
        self.cloudformation.update_stack(
            StackName=stack_name,
            UsePreviousTemplate=True,
            Tags=[
                {'Key': 'DeploymentColor', 'Value': color},
                {'Key': 'Environment', 'Value': self.environment}
            ]
        )
    
    def get_stack_by_tag(self, color):
        """Get stack by deployment color tag"""
        response = self.cloudformation.list_stacks(
            StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE']
        )
        
        for stack in response['StackSummaries']:
            if self.environment in stack['StackName']:
                # Get stack tags
                stack_detail = self.cloudformation.describe_stacks(
                    StackName=stack['StackName']
                )
                
                tags = stack_detail['Stacks'][0].get('Tags', [])
                for tag in tags:
                    if tag['Key'] == 'DeploymentColor' and tag['Value'] == color:
                        return stack['StackName']
        
        return None
    
    def create_green_config(self, blue_stack):
        """Create configuration for green environment"""
        return {
            'stack_name': f"{blue_stack}-green",
            'environment': f"{self.environment}-green",
            'timestamp': datetime.now().isoformat()
        }
    
    def get_target_group(self, color):
        """Get target group ARN by color"""
        response = self.elbv2.describe_target_groups()
        
        for tg in response['TargetGroups']:
            if color in tg['TargetGroupName'] and self.environment in tg['TargetGroupName']:
                return tg['TargetGroupArn']
        
        return None
    
    def get_listener_arn(self):
        """Get load balancer listener ARN"""
        # Get load balancer
        response = self.elbv2.describe_load_balancers()
        
        for lb in response['LoadBalancers']:
            if self.environment in lb['LoadBalancerName']:
                # Get listener
                listeners = self.elbv2.describe_listeners(
                    LoadBalancerArn=lb['LoadBalancerArn']
                )
                return listeners['Listeners'][0]['ListenerArn']
        
        return None
    
    def update_listener_rules(self, listener_arn, green_tg, blue_tg, green_percentage):
        """Update listener rules to shift traffic"""
        blue_percentage = 100 - green_percentage
        
        self.elbv2.modify_listener(
            ListenerArn=listener_arn,
            DefaultActions=[
                {
                    'Type': 'forward',
                    'ForwardConfig': {
                        'TargetGroups': [
                            {
                                'TargetGroupArn': green_tg,
                                'Weight': green_percentage
                            },
                            {
                                'TargetGroupArn': blue_tg,
                                'Weight': blue_percentage
                            }
                        ]
                    }
                }
            ]
        )
    
    def check_health_metrics(self, color):
        """Check CloudWatch health metrics"""
        # Check error rate
        error_rate = self.get_metric('ErrorRate', color)
        if error_rate > 5:  # 5% threshold
            print(f"Error rate too high: {error_rate}%")
            return False
        
        # Check latency
        latency = self.get_metric('Latency', color)
        if latency > 3000:  # 3 second threshold
            print(f"Latency too high: {latency}ms")
            return False
        
        return True
    
    def get_metric(self, metric_name, color):
        """Get CloudWatch metric value"""
        response = self.cloudwatch.get_metric_statistics(
            Namespace='RISE/Application',
            MetricName=metric_name,
            Dimensions=[
                {'Name': 'Environment', 'Value': f"{self.environment}-{color}"}
            ],
            StartTime=datetime.now(),
            EndTime=datetime.now(),
            Period=60,
            Statistics=['Average']
        )
        
        if response['Datapoints']:
            return response['Datapoints'][0]['Average']
        return 0
    
    def update_route53(self, color):
        """Update Route53 DNS to point to new environment"""
        hosted_zone_id = self.get_hosted_zone_id()
        
        # Get load balancer DNS
        lb_dns = self.get_load_balancer_dns(color)
        
        self.route53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': f'{self.environment}.rise-farming.com',
                            'Type': 'CNAME',
                            'TTL': 60,
                            'ResourceRecords': [{'Value': lb_dns}]
                        }
                    }
                ]
            }
        )
    
    def get_hosted_zone_id(self):
        """Get Route53 hosted zone ID"""
        response = self.route53.list_hosted_zones()
        
        for zone in response['HostedZones']:
            if 'rise-farming.com' in zone['Name']:
                return zone['Id'].split('/')[-1]
        
        return None
    
    def get_load_balancer_dns(self, color):
        """Get load balancer DNS name"""
        response = self.elbv2.describe_load_balancers()
        
        for lb in response['LoadBalancers']:
            if color in lb['LoadBalancerName'] and self.environment in lb['LoadBalancerName']:
                return lb['DNSName']
        
        return None
    
    def send_alert(self, message):
        """Send deployment alert"""
        sns = boto3.client('sns')
        topic_arn = f"arn:aws:sns:{boto3.session.Session().region_name}:*:rise-deployment-alerts"
        
        sns.publish(
            TopicArn=topic_arn,
            Subject='RISE Deployment Alert',
            Message=message
        )

def main():
    parser = argparse.ArgumentParser(description='Blue-Green Deployment Manager')
    parser.add_argument('--environment', required=True, help='Environment name')
    parser.add_argument('--action', required=True, 
                       choices=['prepare', 'switch', 'rollback', 'cleanup'],
                       help='Deployment action')
    
    args = parser.parse_args()
    
    deployer = BlueGreenDeployment(args.environment)
    
    try:
        if args.action == 'prepare':
            result = deployer.prepare()
            print(json.dumps(result, indent=2))
        elif args.action == 'switch':
            success = deployer.switch()
            sys.exit(0 if success else 1)
        elif args.action == 'rollback':
            success = deployer.rollback()
            sys.exit(0 if success else 1)
        elif args.action == 'cleanup':
            success = deployer.cleanup()
            sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
