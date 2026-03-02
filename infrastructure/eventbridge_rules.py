"""
RISE EventBridge Rules Configuration
EventBridge scheduled rules for weather monitoring and alerts
"""

from aws_cdk import (
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lambda_,
    Duration,
    Stack
)
from constructs import Construct


class WeatherMonitoringRules(Construct):
    """EventBridge rules for weather monitoring"""
    
    def __init__(self,
                 scope: Construct,
                 id: str,
                 weather_alert_lambda: lambda_.Function):
        """
        Initialize weather monitoring rules
        
        Args:
            scope: CDK scope
            id: Construct ID
            weather_alert_lambda: Lambda function for weather alerts
        """
        super().__init__(scope, id)
        
        # Rule 1: Weather monitoring every 6 hours
        self.weather_monitoring_rule = events.Rule(
            self, "WeatherMonitoringRule",
            description="Monitor weather conditions every 6 hours for all users",
            schedule=events.Schedule.rate(Duration.hours(6)),
            enabled=True
        )
        
        # Add Lambda target
        self.weather_monitoring_rule.add_target(
            targets.LambdaFunction(
                weather_alert_lambda,
                retry_attempts=2
            )
        )
        
        # Rule 2: Critical weather check every 2 hours (during farming season)
        self.critical_weather_rule = events.Rule(
            self, "CriticalWeatherRule",
            description="Check for critical weather conditions every 2 hours",
            schedule=events.Schedule.rate(Duration.hours(2)),
            enabled=True
        )
        
        self.critical_weather_rule.add_target(
            targets.LambdaFunction(
                weather_alert_lambda,
                retry_attempts=2
            )
        )
        
        # Rule 3: Daily weather summary at 6 AM IST
        self.daily_summary_rule = events.Rule(
            self, "DailyWeatherSummaryRule",
            description="Generate daily weather summary at 6 AM IST",
            schedule=events.Schedule.cron(
                minute="30",
                hour="0",  # 6 AM IST = 12:30 AM UTC
                month="*",
                week_day="*",
                year="*"
            ),
            enabled=True
        )
        
        self.daily_summary_rule.add_target(
            targets.LambdaFunction(
                weather_alert_lambda,
                retry_attempts=2
            )
        )
        
        # Rule 4: Evening weather update at 6 PM IST
        self.evening_update_rule = events.Rule(
            self, "EveningWeatherUpdateRule",
            description="Generate evening weather update at 6 PM IST",
            schedule=events.Schedule.cron(
                minute="30",
                hour="12",  # 6 PM IST = 12:30 PM UTC
                month="*",
                week_day="*",
                year="*"
            ),
            enabled=True
        )
        
        self.evening_update_rule.add_target(
            targets.LambdaFunction(
                weather_alert_lambda,
                retry_attempts=2
            )
        )


def add_weather_monitoring_to_stack(stack: Stack,
                                    weather_alert_lambda: lambda_.Function):
    """
    Add weather monitoring rules to CDK stack
    
    Args:
        stack: CDK stack
        weather_alert_lambda: Lambda function for weather alerts
    
    Returns:
        WeatherMonitoringRules construct
    """
    return WeatherMonitoringRules(
        stack,
        "WeatherMonitoringRules",
        weather_alert_lambda=weather_alert_lambda
    )


# Manual EventBridge rule creation (for non-CDK deployments)
def create_eventbridge_rules_manual():
    """
    Create EventBridge rules manually using boto3
    Use this for quick setup without CDK
    """
    import boto3
    import json
    
    events_client = boto3.client('events')
    lambda_client = boto3.client('lambda')
    
    # Get Lambda function ARN
    lambda_function_name = 'RISE-WeatherAlertLambda'
    
    try:
        lambda_response = lambda_client.get_function(FunctionName=lambda_function_name)
        lambda_arn = lambda_response['Configuration']['FunctionArn']
    except Exception as e:
        print(f"Error: Lambda function {lambda_function_name} not found")
        print(f"Please create the Lambda function first")
        return
    
    # Rule 1: Every 6 hours
    rule_name_1 = 'RISE-WeatherMonitoring-6Hours'
    try:
        events_client.put_rule(
            Name=rule_name_1,
            Description='Monitor weather conditions every 6 hours for all users',
            ScheduleExpression='rate(6 hours)',
            State='ENABLED'
        )
        
        # Add Lambda permission
        lambda_client.add_permission(
            FunctionName=lambda_function_name,
            StatementId=f'{rule_name_1}-Permission',
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=f'arn:aws:events:*:*:rule/{rule_name_1}'
        )
        
        # Add target
        events_client.put_targets(
            Rule=rule_name_1,
            Targets=[{
                'Id': '1',
                'Arn': lambda_arn,
                'RetryPolicy': {
                    'MaximumRetryAttempts': 2
                }
            }]
        )
        
        print(f"✅ Created rule: {rule_name_1}")
    except Exception as e:
        print(f"Error creating rule {rule_name_1}: {e}")
    
    # Rule 2: Every 2 hours (critical)
    rule_name_2 = 'RISE-CriticalWeatherCheck-2Hours'
    try:
        events_client.put_rule(
            Name=rule_name_2,
            Description='Check for critical weather conditions every 2 hours',
            ScheduleExpression='rate(2 hours)',
            State='ENABLED'
        )
        
        lambda_client.add_permission(
            FunctionName=lambda_function_name,
            StatementId=f'{rule_name_2}-Permission',
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=f'arn:aws:events:*:*:rule/{rule_name_2}'
        )
        
        events_client.put_targets(
            Rule=rule_name_2,
            Targets=[{
                'Id': '1',
                'Arn': lambda_arn,
                'RetryPolicy': {
                    'MaximumRetryAttempts': 2
                }
            }]
        )
        
        print(f"✅ Created rule: {rule_name_2}")
    except Exception as e:
        print(f"Error creating rule {rule_name_2}: {e}")
    
    # Rule 3: Daily at 6 AM IST
    rule_name_3 = 'RISE-DailyWeatherSummary-6AM'
    try:
        events_client.put_rule(
            Name=rule_name_3,
            Description='Generate daily weather summary at 6 AM IST',
            ScheduleExpression='cron(30 0 * * ? *)',  # 6 AM IST = 12:30 AM UTC
            State='ENABLED'
        )
        
        lambda_client.add_permission(
            FunctionName=lambda_function_name,
            StatementId=f'{rule_name_3}-Permission',
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=f'arn:aws:events:*:*:rule/{rule_name_3}'
        )
        
        events_client.put_targets(
            Rule=rule_name_3,
            Targets=[{
                'Id': '1',
                'Arn': lambda_arn,
                'RetryPolicy': {
                    'MaximumRetryAttempts': 2
                }
            }]
        )
        
        print(f"✅ Created rule: {rule_name_3}")
    except Exception as e:
        print(f"Error creating rule {rule_name_3}: {e}")
    
    # Rule 4: Evening at 6 PM IST
    rule_name_4 = 'RISE-EveningWeatherUpdate-6PM'
    try:
        events_client.put_rule(
            Name=rule_name_4,
            Description='Generate evening weather update at 6 PM IST',
            ScheduleExpression='cron(30 12 * * ? *)',  # 6 PM IST = 12:30 PM UTC
            State='ENABLED'
        )
        
        lambda_client.add_permission(
            FunctionName=lambda_function_name,
            StatementId=f'{rule_name_4}-Permission',
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=f'arn:aws:events:*:*:rule/{rule_name_4}'
        )
        
        events_client.put_targets(
            Rule=rule_name_4,
            Targets=[{
                'Id': '1',
                'Arn': lambda_arn,
                'RetryPolicy': {
                    'MaximumRetryAttempts': 2
                }
            }]
        )
        
        print(f"✅ Created rule: {rule_name_4}")
    except Exception as e:
        print(f"Error creating rule {rule_name_4}: {e}")
    
    print("\n✅ All EventBridge rules created successfully!")
    print("\nRules created:")
    print(f"  1. {rule_name_1} - Every 6 hours")
    print(f"  2. {rule_name_2} - Every 2 hours (critical)")
    print(f"  3. {rule_name_3} - Daily at 6 AM IST")
    print(f"  4. {rule_name_4} - Evening at 6 PM IST")


if __name__ == '__main__':
    print("Creating EventBridge rules for weather monitoring...")
    create_eventbridge_rules_manual()
