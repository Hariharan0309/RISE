"""
RISE CloudWatch Alarms Configuration
Defines CloudWatch alarms for Lambda functions, API Gateway, and DynamoDB
"""

import boto3
from typing import List, Dict, Optional
from infrastructure.monitoring_config import (
    LAMBDA_FUNCTIONS,
    API_GATEWAY_CONFIG,
    DYNAMODB_TABLES,
    AlarmSeverity,
    MetricNamespace,
)


class CloudWatchAlarmsManager:
    """Manages CloudWatch alarms for RISE platform"""
    
    def __init__(self, sns_topic_arn: str, region: str = "us-east-1"):
        """
        Initialize CloudWatch alarms manager
        
        Args:
            sns_topic_arn: SNS topic ARN for alarm notifications
            region: AWS region
        """
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.sns_topic_arn = sns_topic_arn
        self.region = region
    
    def create_lambda_alarms(self, function_key: str) -> List[str]:
        """
        Create comprehensive alarms for a Lambda function
        
        Args:
            function_key: Key from LAMBDA_FUNCTIONS config
            
        Returns:
            List of created alarm names
        """
        config = LAMBDA_FUNCTIONS.get(function_key)
        if not config:
            raise ValueError(f"Unknown function key: {function_key}")
        
        alarm_names = []
        function_name = config.function_name
        
        # 1. Error rate alarm
        error_alarm = self._create_error_rate_alarm(function_name, config)
        alarm_names.append(error_alarm)
        
        # 2. Duration alarm
        duration_alarm = self._create_duration_alarm(function_name, config)
        alarm_names.append(duration_alarm)
        
        # 3. Throttle alarm
        throttle_alarm = self._create_throttle_alarm(function_name, config)
        alarm_names.append(throttle_alarm)
        
        # 4. Concurrent executions alarm
        concurrent_alarm = self._create_concurrent_executions_alarm(function_name, config)
        alarm_names.append(concurrent_alarm)
        
        # 5. Invocation count alarm (for monitoring usage)
        invocation_alarm = self._create_invocation_alarm(function_name, config)
        alarm_names.append(invocation_alarm)
        
        return alarm_names
    
    def _create_error_rate_alarm(self, function_name: str, config) -> str:
        """Create alarm for Lambda error rate"""
        alarm_name = f"{function_name}-ErrorRate-{config.alarm_severity.value}"
        
        self.cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription=f"Error rate exceeds {config.error_threshold}% for {function_name}",
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            MetricName='Errors',
            Namespace=MetricNamespace.LAMBDA.value,
            Statistic='Sum',
            Dimensions=[
                {'Name': 'FunctionName', 'Value': function_name}
            ],
            Period=300,  # 5 minutes
            EvaluationPeriods=2,
            DatapointsToAlarm=2,
            Threshold=config.error_threshold,
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching',
            Tags=[
                {'Key': 'Service', 'Value': 'RISE'},
                {'Key': 'Severity', 'Value': config.alarm_severity.value},
                {'Key': 'Type', 'Value': 'ErrorRate'}
            ]
        )
        
        return alarm_name
    
    def _create_duration_alarm(self, function_name: str, config) -> str:
        """Create alarm for Lambda duration"""
        alarm_name = f"{function_name}-Duration-{config.alarm_severity.value}"
        
        self.cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription=f"Duration exceeds {config.duration_threshold_ms}ms for {function_name}",
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            MetricName='Duration',
            Namespace=MetricNamespace.LAMBDA.value,
            Statistic='Average',
            Dimensions=[
                {'Name': 'FunctionName', 'Value': function_name}
            ],
            Period=300,  # 5 minutes
            EvaluationPeriods=2,
            DatapointsToAlarm=2,
            Threshold=config.duration_threshold_ms,
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching',
            Tags=[
                {'Key': 'Service', 'Value': 'RISE'},
                {'Key': 'Severity', 'Value': config.alarm_severity.value},
                {'Key': 'Type', 'Value': 'Duration'}
            ]
        )
        
        return alarm_name
    
    def _create_throttle_alarm(self, function_name: str, config) -> str:
        """Create alarm for Lambda throttles"""
        alarm_name = f"{function_name}-Throttles-{config.alarm_severity.value}"
        
        self.cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription=f"Throttles exceed {config.throttle_threshold} for {function_name}",
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            MetricName='Throttles',
            Namespace=MetricNamespace.LAMBDA.value,
            Statistic='Sum',
            Dimensions=[
                {'Name': 'FunctionName', 'Value': function_name}
            ],
            Period=300,  # 5 minutes
            EvaluationPeriods=1,
            DatapointsToAlarm=1,
            Threshold=config.throttle_threshold,
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching',
            Tags=[
                {'Key': 'Service', 'Value': 'RISE'},
                {'Key': 'Severity', 'Value': AlarmSeverity.CRITICAL.value},
                {'Key': 'Type', 'Value': 'Throttle'}
            ]
        )
        
        return alarm_name
    
    def _create_concurrent_executions_alarm(self, function_name: str, config) -> str:
        """Create alarm for Lambda concurrent executions"""
        alarm_name = f"{function_name}-ConcurrentExecutions-{config.alarm_severity.value}"
        
        self.cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription=f"Concurrent executions exceed {config.concurrent_executions_threshold} for {function_name}",
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            MetricName='ConcurrentExecutions',
            Namespace=MetricNamespace.LAMBDA.value,
            Statistic='Maximum',
            Dimensions=[
                {'Name': 'FunctionName', 'Value': function_name}
            ],
            Period=60,  # 1 minute
            EvaluationPeriods=2,
            DatapointsToAlarm=2,
            Threshold=config.concurrent_executions_threshold,
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching',
            Tags=[
                {'Key': 'Service', 'Value': 'RISE'},
                {'Key': 'Severity', 'Value': config.alarm_severity.value},
                {'Key': 'Type', 'Value': 'ConcurrentExecutions'}
            ]
        )
        
        return alarm_name
    
    def _create_invocation_alarm(self, function_name: str, config) -> str:
        """Create alarm for monitoring Lambda invocations"""
        alarm_name = f"{function_name}-LowInvocations-INFO"
        
        # This alarm triggers if invocations drop to zero (potential issue)
        self.cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription=f"No invocations detected for {function_name} in 1 hour",
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            MetricName='Invocations',
            Namespace=MetricNamespace.LAMBDA.value,
            Statistic='Sum',
            Dimensions=[
                {'Name': 'FunctionName', 'Value': function_name}
            ],
            Period=3600,  # 1 hour
            EvaluationPeriods=1,
            DatapointsToAlarm=1,
            Threshold=1,
            ComparisonOperator='LessThanThreshold',
            TreatMissingData='breaching',
            Tags=[
                {'Key': 'Service', 'Value': 'RISE'},
                {'Key': 'Severity', 'Value': AlarmSeverity.LOW.value},
                {'Key': 'Type', 'Value': 'Invocations'}
            ]
        )
        
        return alarm_name
    
    def create_api_gateway_alarms(self) -> List[str]:
        """Create alarms for API Gateway"""
        alarm_names = []
        api_name = API_GATEWAY_CONFIG['api_name']
        stage = API_GATEWAY_CONFIG['stage']
        
        # 1. Latency alarm
        latency_alarm = f"{api_name}-{stage}-Latency-HIGH"
        self.cloudwatch.put_metric_alarm(
            AlarmName=latency_alarm,
            AlarmDescription=f"API Gateway latency exceeds {API_GATEWAY_CONFIG['latency_threshold_ms']}ms",
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            MetricName='Latency',
            Namespace=MetricNamespace.API_GATEWAY.value,
            Statistic='Average',
            Dimensions=[
                {'Name': 'ApiName', 'Value': api_name},
                {'Name': 'Stage', 'Value': stage}
            ],
            Period=300,
            EvaluationPeriods=2,
            DatapointsToAlarm=2,
            Threshold=API_GATEWAY_CONFIG['latency_threshold_ms'],
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching',
            Tags=[
                {'Key': 'Service', 'Value': 'RISE'},
                {'Key': 'Severity', 'Value': AlarmSeverity.HIGH.value},
                {'Key': 'Type', 'Value': 'Latency'}
            ]
        )
        alarm_names.append(latency_alarm)
        
        # 2. 4XX error alarm
        error_4xx_alarm = f"{api_name}-{stage}-4XXError-MEDIUM"
        self.cloudwatch.put_metric_alarm(
            AlarmName=error_4xx_alarm,
            AlarmDescription=f"API Gateway 4XX error rate exceeds threshold",
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            MetricName='4XXError',
            Namespace=MetricNamespace.API_GATEWAY.value,
            Statistic='Sum',
            Dimensions=[
                {'Name': 'ApiName', 'Value': api_name},
                {'Name': 'Stage', 'Value': stage}
            ],
            Period=300,
            EvaluationPeriods=2,
            DatapointsToAlarm=2,
            Threshold=50,  # 50 4XX errors in 5 minutes
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching',
            Tags=[
                {'Key': 'Service', 'Value': 'RISE'},
                {'Key': 'Severity', 'Value': AlarmSeverity.MEDIUM.value},
                {'Key': 'Type', 'Value': '4XXError'}
            ]
        )
        alarm_names.append(error_4xx_alarm)
        
        # 3. 5XX error alarm
        error_5xx_alarm = f"{api_name}-{stage}-5XXError-CRITICAL"
        self.cloudwatch.put_metric_alarm(
            AlarmName=error_5xx_alarm,
            AlarmDescription=f"API Gateway 5XX error rate exceeds threshold",
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            MetricName='5XXError',
            Namespace=MetricNamespace.API_GATEWAY.value,
            Statistic='Sum',
            Dimensions=[
                {'Name': 'ApiName', 'Value': api_name},
                {'Name': 'Stage', 'Value': stage}
            ],
            Period=300,
            EvaluationPeriods=1,
            DatapointsToAlarm=1,
            Threshold=10,  # 10 5XX errors in 5 minutes
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching',
            Tags=[
                {'Key': 'Service', 'Value': 'RISE'},
                {'Key': 'Severity', 'Value': AlarmSeverity.CRITICAL.value},
                {'Key': 'Type', 'Value': '5XXError'}
            ]
        )
        alarm_names.append(error_5xx_alarm)
        
        return alarm_names
    
    def create_dynamodb_alarms(self, table_name: str) -> List[str]:
        """Create alarms for DynamoDB table"""
        if table_name not in DYNAMODB_TABLES:
            raise ValueError(f"Unknown table: {table_name}")
        
        config = DYNAMODB_TABLES[table_name]
        alarm_names = []
        
        # 1. Read throttle alarm
        read_throttle_alarm = f"{table_name}-ReadThrottles-HIGH"
        self.cloudwatch.put_metric_alarm(
            AlarmName=read_throttle_alarm,
            AlarmDescription=f"Read throttles detected for {table_name}",
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            MetricName='ReadThrottleEvents',
            Namespace=MetricNamespace.DYNAMODB.value,
            Statistic='Sum',
            Dimensions=[
                {'Name': 'TableName', 'Value': table_name}
            ],
            Period=300,
            EvaluationPeriods=1,
            DatapointsToAlarm=1,
            Threshold=config['throttle_threshold'],
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching',
            Tags=[
                {'Key': 'Service', 'Value': 'RISE'},
                {'Key': 'Severity', 'Value': AlarmSeverity.HIGH.value},
                {'Key': 'Type', 'Value': 'ReadThrottle'}
            ]
        )
        alarm_names.append(read_throttle_alarm)
        
        # 2. Write throttle alarm
        write_throttle_alarm = f"{table_name}-WriteThrottles-HIGH"
        self.cloudwatch.put_metric_alarm(
            AlarmName=write_throttle_alarm,
            AlarmDescription=f"Write throttles detected for {table_name}",
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            MetricName='WriteThrottleEvents',
            Namespace=MetricNamespace.DYNAMODB.value,
            Statistic='Sum',
            Dimensions=[
                {'Name': 'TableName', 'Value': table_name}
            ],
            Period=300,
            EvaluationPeriods=1,
            DatapointsToAlarm=1,
            Threshold=config['throttle_threshold'],
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching',
            Tags=[
                {'Key': 'Service', 'Value': 'RISE'},
                {'Key': 'Severity', 'Value': AlarmSeverity.HIGH.value},
                {'Key': 'Type', 'Value': 'WriteThrottle'}
            ]
        )
        alarm_names.append(write_throttle_alarm)
        
        # 3. System errors alarm
        system_errors_alarm = f"{table_name}-SystemErrors-CRITICAL"
        self.cloudwatch.put_metric_alarm(
            AlarmName=system_errors_alarm,
            AlarmDescription=f"System errors detected for {table_name}",
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            MetricName='SystemErrors',
            Namespace=MetricNamespace.DYNAMODB.value,
            Statistic='Sum',
            Dimensions=[
                {'Name': 'TableName', 'Value': table_name}
            ],
            Period=300,
            EvaluationPeriods=1,
            DatapointsToAlarm=1,
            Threshold=5,
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching',
            Tags=[
                {'Key': 'Service', 'Value': 'RISE'},
                {'Key': 'Severity', 'Value': AlarmSeverity.CRITICAL.value},
                {'Key': 'Type', 'Value': 'SystemErrors'}
            ]
        )
        alarm_names.append(system_errors_alarm)
        
        return alarm_names
    
    def create_all_alarms(self) -> Dict[str, List[str]]:
        """Create all alarms for RISE platform"""
        all_alarms = {
            'lambda': [],
            'api_gateway': [],
            'dynamodb': []
        }
        
        # Create Lambda alarms
        for function_key in LAMBDA_FUNCTIONS.keys():
            try:
                alarms = self.create_lambda_alarms(function_key)
                all_alarms['lambda'].extend(alarms)
                print(f"Created {len(alarms)} alarms for {function_key}")
            except Exception as e:
                print(f"Error creating alarms for {function_key}: {e}")
        
        # Create API Gateway alarms
        try:
            alarms = self.create_api_gateway_alarms()
            all_alarms['api_gateway'].extend(alarms)
            print(f"Created {len(alarms)} API Gateway alarms")
        except Exception as e:
            print(f"Error creating API Gateway alarms: {e}")
        
        # Create DynamoDB alarms
        for table_name in DYNAMODB_TABLES.keys():
            try:
                alarms = self.create_dynamodb_alarms(table_name)
                all_alarms['dynamodb'].extend(alarms)
                print(f"Created {len(alarms)} alarms for {table_name}")
            except Exception as e:
                print(f"Error creating alarms for {table_name}: {e}")
        
        return all_alarms
    
    def delete_alarm(self, alarm_name: str):
        """Delete a CloudWatch alarm"""
        self.cloudwatch.delete_alarms(AlarmNames=[alarm_name])
    
    def delete_all_rise_alarms(self):
        """Delete all RISE alarms"""
        # Get all alarms with RISE tag
        paginator = self.cloudwatch.get_paginator('describe_alarms')
        
        for page in paginator.paginate():
            for alarm in page['MetricAlarms']:
                # Check if alarm has RISE tag
                alarm_name = alarm['AlarmName']
                if 'rise-' in alarm_name.lower() or 'RISE-' in alarm_name:
                    self.delete_alarm(alarm_name)
                    print(f"Deleted alarm: {alarm_name}")
