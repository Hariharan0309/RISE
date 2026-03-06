#!/usr/bin/env python3
"""
Notification Script for RISE Platform
Sends deployment notifications via SNS and Slack
"""

import argparse
import boto3
import json
import requests
import os
from datetime import datetime

class NotificationSender:
    def __init__(self, status, environment):
        self.status = status
        self.environment = environment
        self.sns = boto3.client('sns')
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        
    def send_all_notifications(self):
        """Send notifications via all channels"""
        print(f"[{datetime.now()}] Sending {self.status} notification for {self.environment}")
        
        # Send SNS notification
        self.send_sns_notification()
        
        # Send Slack notification if webhook configured
        if self.slack_webhook:
            self.send_slack_notification()
        
        print(f"[{datetime.now()}] Notifications sent successfully")
    
    def send_sns_notification(self):
        """Send notification via SNS"""
        topic_arn = f"arn:aws:sns:{boto3.session.Session().region_name}:*:rise-deployment-alerts"
        
        subject, message = self.get_notification_content()
        
        try:
            self.sns.publish(
                TopicArn=topic_arn,
                Subject=subject,
                Message=message
            )
            print(f"  ✓ SNS notification sent")
        except Exception as e:
            print(f"  ✗ SNS notification failed: {str(e)}")
    
    def send_slack_notification(self):
        """Send notification via Slack"""
        color = self.get_status_color()
        emoji = self.get_status_emoji()
        
        payload = {
            'attachments': [
                {
                    'color': color,
                    'title': f'{emoji} RISE Deployment {self.status.upper()}',
                    'fields': [
                        {
                            'title': 'Environment',
                            'value': self.environment,
                            'short': True
                        },
                        {
                            'title': 'Status',
                            'value': self.status.upper(),
                            'short': True
                        },
                        {
                            'title': 'Timestamp',
                            'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                            'short': True
                        },
                        {
                            'title': 'Deployed By',
                            'value': os.getenv('GITHUB_ACTOR', 'Unknown'),
                            'short': True
                        }
                    ],
                    'footer': 'RISE CI/CD Pipeline',
                    'footer_icon': 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'
                }
            ]
        }
        
        try:
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"  ✓ Slack notification sent")
            else:
                print(f"  ✗ Slack notification failed: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Slack notification failed: {str(e)}")
    
    def get_notification_content(self):
        """Get notification subject and message"""
        if self.status == 'success':
            subject = f'✓ RISE Deployment Successful - {self.environment}'
            message = f"""
RISE Deployment Completed Successfully

Environment: {self.environment}
Status: SUCCESS
Timestamp: {datetime.now().isoformat()}
Deployed By: {os.getenv('GITHUB_ACTOR', 'Unknown')}
Commit: {os.getenv('GITHUB_SHA', 'Unknown')[:7]}

The deployment has been completed and all post-deployment validations passed.

Next Steps:
- Monitor CloudWatch metrics for the next 24 hours
- Review application logs for any anomalies
- Old blue environment will be cleaned up after monitoring period

Dashboard: https://console.aws.amazon.com/cloudwatch/
"""
        elif self.status == 'failure':
            subject = f'✗ RISE Deployment Failed - {self.environment}'
            message = f"""
RISE Deployment Failed

Environment: {self.environment}
Status: FAILURE
Timestamp: {datetime.now().isoformat()}
Deployed By: {os.getenv('GITHUB_ACTOR', 'Unknown')}
Commit: {os.getenv('GITHUB_SHA', 'Unknown')[:7]}

The deployment has failed and automatic rollback has been initiated.

Action Required:
1. Review GitHub Actions logs
2. Check CloudWatch logs for errors
3. Investigate root cause
4. Fix issues and retry deployment

Logs: {os.getenv('GITHUB_SERVER_URL', 'https://github.com')}/{os.getenv('GITHUB_REPOSITORY', '')}/actions
"""
        else:
            subject = f'RISE Deployment {self.status.upper()} - {self.environment}'
            message = f"""
RISE Deployment Status Update

Environment: {self.environment}
Status: {self.status.upper()}
Timestamp: {datetime.now().isoformat()}
"""
        
        return subject, message
    
    def get_status_color(self):
        """Get color for status"""
        colors = {
            'success': 'good',
            'failure': 'danger',
            'warning': 'warning',
            'info': '#439FE0'
        }
        return colors.get(self.status, '#808080')
    
    def get_status_emoji(self):
        """Get emoji for status"""
        emojis = {
            'success': '✅',
            'failure': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        return emojis.get(self.status, '📢')

def main():
    parser = argparse.ArgumentParser(description='Notification Sender')
    parser.add_argument('--status', required=True, 
                       choices=['success', 'failure', 'warning', 'info'],
                       help='Deployment status')
    parser.add_argument('--environment', required=True, help='Environment name')
    
    args = parser.parse_args()
    
    sender = NotificationSender(args.status, args.environment)
    sender.send_all_notifications()

if __name__ == '__main__':
    main()
