#!/usr/bin/env python3
"""
CloudWatch Alarms Setup for RISE Production
Creates monitoring alarms for API Gateway, DynamoDB, and cost tracking
"""

import boto3
import sys

def create_api_gateway_alarms(cloudwatch, api_id, sns_topic_arn=None):
    """Create CloudWatch alarms for API Gateway"""
    
    print("\n📊 Creating API Gateway alarms...")
    
    alarms = [
        {
            'AlarmName': 'RISE-API-HighErrorRate',
            'AlarmDescription': 'Alert when API error rate exceeds 5%',
            'MetricName': '5XXError',
            'Namespace': 'AWS/ApiGateway',
            'Statistic': 'Sum',
            'Period': 300,  # 5 minutes
            'EvaluationPeriods': 2,
            'Threshold': 10,  # 10 errors in 5 minutes
            'ComparisonOperator': 'GreaterThanThreshold',
            'Dimensions': [
                {'Name': 'ApiName', 'Value': 'RISE-API'}
            ]
        },
        {
            'AlarmName': 'RISE-API-HighLatency',
            'AlarmDescription': 'Alert when API latency exceeds 3 seconds',
            'MetricName': 'Latency',
            'Namespace': 'AWS/ApiGateway',
            'Statistic': 'Average',
            'Period': 300,
            'EvaluationPeriods': 2,
            'Threshold': 3000,  # 3 seconds in milliseconds
            'ComparisonOperator': 'GreaterThanThreshold',
            'Dimensions': [
                {'Name': 'ApiName', 'Value': 'RISE-API'}
            ]
        },
        {
            'AlarmName': 'RISE-API-ClientErrors',
            'AlarmDescription': 'Alert when client error rate is high',
            'MetricName': '4XXError',
            'Namespace': 'AWS/ApiGateway',
            'Statistic': 'Sum',
            'Period': 300,
            'EvaluationPeriods': 2,
            'Threshold': 50,  # 50 client errors in 5 minutes
            'ComparisonOperator': 'GreaterThanThreshold',
            'Dimensions': [
                {'Name': 'ApiName', 'Value': 'RISE-API'}
            ]
        }
    ]
    
    for alarm in alarms:
        try:
            if sns_topic_arn:
                alarm['AlarmActions'] = [sns_topic_arn]
            
            cloudwatch.put_metric_alarm(**alarm)
            print(f"  ✅ Created: {alarm['AlarmName']}")
        except Exception as e:
            print(f"  ❌ Failed to create {alarm['AlarmName']}: {e}")


def create_dynamodb_alarms(cloudwatch, table_names, sns_topic_arn=None):
    """Create CloudWatch alarms for DynamoDB tables"""
    
    print("\n📊 Creating DynamoDB alarms...")
    
    # Create alarms for critical tables
    critical_tables = [
        'RISE-UserProfiles',
        'RISE-DiagnosisHistory',
        'RISE-ConversationHistory'
    ]
    
    for table_name in critical_tables:
        if table_name not in table_names:
            continue
        
        alarms = [
            {
                'AlarmName': f'RISE-DDB-{table_name}-ReadThrottle',
                'AlarmDescription': f'Alert when {table_name} read requests are throttled',
                'MetricName': 'ReadThrottleEvents',
                'Namespace': 'AWS/DynamoDB',
                'Statistic': 'Sum',
                'Period': 300,
                'EvaluationPeriods': 1,
                'Threshold': 5,
                'ComparisonOperator': 'GreaterThanThreshold',
                'Dimensions': [
                    {'Name': 'TableName', 'Value': table_name}
                ]
            },
            {
                'AlarmName': f'RISE-DDB-{table_name}-WriteThrottle',
                'AlarmDescription': f'Alert when {table_name} write requests are throttled',
                'MetricName': 'WriteThrottleEvents',
                'Namespace': 'AWS/DynamoDB',
                'Statistic': 'Sum',
                'Period': 300,
                'EvaluationPeriods': 1,
                'Threshold': 5,
                'ComparisonOperator': 'GreaterThanThreshold',
                'Dimensions': [
                    {'Name': 'TableName', 'Value': table_name}
                ]
            }
        ]
        
        for alarm in alarms:
            try:
                if sns_topic_arn:
                    alarm['AlarmActions'] = [sns_topic_arn]
                
                cloudwatch.put_metric_alarm(**alarm)
                print(f"  ✅ Created: {alarm['AlarmName']}")
            except Exception as e:
                print(f"  ❌ Failed to create {alarm['AlarmName']}: {e}")


def create_cost_alarm(cloudwatch, sns_topic_arn=None):
    """Create cost budget alarm"""
    
    print("\n💰 Creating cost alarm...")
    
    alarm = {
        'AlarmName': 'RISE-HighCost',
        'AlarmDescription': 'Alert when estimated charges exceed $50',
        'MetricName': 'EstimatedCharges',
        'Namespace': 'AWS/Billing',
        'Statistic': 'Maximum',
        'Period': 21600,  # 6 hours
        'EvaluationPeriods': 1,
        'Threshold': 50.0,
        'ComparisonOperator': 'GreaterThanThreshold',
        'Dimensions': [
            {'Name': 'Currency', 'Value': 'USD'}
        ]
    }
    
    try:
        if sns_topic_arn:
            alarm['AlarmActions'] = [sns_topic_arn]
        
        cloudwatch.put_metric_alarm(**alarm)
        print(f"  ✅ Created: {alarm['AlarmName']}")
    except Exception as e:
        print(f"  ❌ Failed to create cost alarm: {e}")


def create_sns_topic(sns):
    """Create SNS topic for alarm notifications"""
    
    print("\n📧 Creating SNS topic for alarm notifications...")
    
    try:
        response = sns.create_topic(
            Name='RISE-Alarms',
            Tags=[
                {'Key': 'Project', 'Value': 'RISE'},
                {'Key': 'Purpose', 'Value': 'CloudWatch Alarms'}
            ]
        )
        
        topic_arn = response['TopicArn']
        print(f"  ✅ Created SNS topic: {topic_arn}")
        print(f"\n  📝 To receive notifications, subscribe to this topic:")
        print(f"     aws sns subscribe --topic-arn {topic_arn} --protocol email --notification-endpoint your-email@example.com")
        
        return topic_arn
    except Exception as e:
        print(f"  ⚠️  SNS topic may already exist or failed to create: {e}")
        return None


def main():
    """Main function to set up all CloudWatch alarms"""
    
    print("=" * 70)
    print("  RISE CloudWatch Alarms Setup")
    print("=" * 70)
    
    # Initialize AWS clients
    region = 'us-east-1'
    cloudwatch = boto3.client('cloudwatch', region_name=region)
    dynamodb = boto3.client('dynamodb', region_name=region)
    apigateway = boto3.client('apigateway', region_name=region)
    sns = boto3.client('sns', region_name=region)
    
    # Create SNS topic for notifications
    sns_topic_arn = create_sns_topic(sns)
    
    # Get API Gateway ID
    try:
        apis = apigateway.get_rest_apis()
        rise_api = next((api for api in apis['items'] if api['name'] == 'RISE-API'), None)
        api_id = rise_api['id'] if rise_api else None
    except Exception as e:
        print(f"  ⚠️  Could not get API Gateway ID: {e}")
        api_id = None
    
    # Get DynamoDB table names
    try:
        tables = dynamodb.list_tables()
        table_names = [t for t in tables['TableNames'] if t.startswith('RISE-')]
    except Exception as e:
        print(f"  ⚠️  Could not list DynamoDB tables: {e}")
        table_names = []
    
    # Create alarms
    if api_id:
        create_api_gateway_alarms(cloudwatch, api_id, sns_topic_arn)
    else:
        print("\n  ⚠️  Skipping API Gateway alarms (API not found)")
    
    if table_names:
        create_dynamodb_alarms(cloudwatch, table_names, sns_topic_arn)
    else:
        print("\n  ⚠️  Skipping DynamoDB alarms (tables not found)")
    
    create_cost_alarm(cloudwatch, sns_topic_arn)
    
    # Summary
    print("\n" + "=" * 70)
    print("  Summary")
    print("=" * 70)
    
    try:
        alarms = cloudwatch.describe_alarms(
            AlarmNamePrefix='RISE-'
        )
        
        print(f"\n  ✅ Total alarms created: {len(alarms['MetricAlarms'])}")
        print("\n  Alarms:")
        for alarm in alarms['MetricAlarms']:
            state_icon = "🟢" if alarm['StateValue'] == 'OK' else "🔴" if alarm['StateValue'] == 'ALARM' else "⚪"
            print(f"    {state_icon} {alarm['AlarmName']} - {alarm['StateValue']}")
        
        if sns_topic_arn:
            print(f"\n  📧 Subscribe to notifications:")
            print(f"     aws sns subscribe \\")
            print(f"       --topic-arn {sns_topic_arn} \\")
            print(f"       --protocol email \\")
            print(f"       --notification-endpoint your-email@example.com")
        
        print("\n  ✅ CloudWatch alarms setup complete!")
        return 0
        
    except Exception as e:
        print(f"\n  ❌ Error getting alarm summary: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
