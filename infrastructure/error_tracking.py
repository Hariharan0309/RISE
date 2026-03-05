"""
RISE Error Tracking and Alerting
Implements comprehensive error tracking with CloudWatch Logs Insights
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from infrastructure.monitoring_config import ERROR_TRACKING_CONFIG


class ErrorTracker:
    """Tracks and analyzes errors across RISE platform"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize error tracker
        
        Args:
            region: AWS region
        """
        self.logs = boto3.client('logs', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.region = region
    
    def create_log_groups(self, function_names: List[str]):
        """
        Create CloudWatch log groups for Lambda functions
        
        Args:
            function_names: List of Lambda function names
        """
        for function_name in function_names:
            log_group_name = f"/aws/lambda/{function_name}"
            
            try:
                self.logs.create_log_group(logGroupName=log_group_name)
                
                # Set retention policy
                self.logs.put_retention_policy(
                    logGroupName=log_group_name,
                    retentionInDays=ERROR_TRACKING_CONFIG['log_retention_days']
                )
                
                print(f"Created log group: {log_group_name}")
            except self.logs.exceptions.ResourceAlreadyExistsException:
                # Log group already exists, update retention
                self.logs.put_retention_policy(
                    logGroupName=log_group_name,
                    retentionInDays=ERROR_TRACKING_CONFIG['log_retention_days']
                )
            except Exception as e:
                print(f"Error creating log group {log_group_name}: {e}")
    
    def create_metric_filters(self, function_name: str):
        """
        Create metric filters for error patterns
        
        Args:
            function_name: Lambda function name
        """
        log_group_name = f"/aws/lambda/{function_name}"
        
        # Filter for general errors
        self._create_error_filter(
            log_group_name,
            f"{function_name}-Errors",
            '[ERROR]',
            "General errors"
        )
        
        # Filter for exceptions
        self._create_error_filter(
            log_group_name,
            f"{function_name}-Exceptions",
            'Exception',
            "Python exceptions"
        )
        
        # Filter for timeouts
        self._create_error_filter(
            log_group_name,
            f"{function_name}-Timeouts",
            'Task timed out',
            "Lambda timeouts"
        )
        
        # Filter for Bedrock errors
        self._create_error_filter(
            log_group_name,
            f"{function_name}-BedrockErrors",
            'BedrockException',
            "Amazon Bedrock errors"
        )
        
        # Filter for DynamoDB errors
        self._create_error_filter(
            log_group_name,
            f"{function_name}-DynamoDBErrors",
            'DynamoDB',
            "DynamoDB errors"
        )
    
    def _create_error_filter(
        self,
        log_group_name: str,
        filter_name: str,
        filter_pattern: str,
        description: str
    ):
        """Create a metric filter for error pattern"""
        try:
            self.logs.put_metric_filter(
                logGroupName=log_group_name,
                filterName=filter_name,
                filterPattern=filter_pattern,
                metricTransformations=[
                    {
                        'metricName': filter_name,
                        'metricNamespace': 'RISE/Errors',
                        'metricValue': '1',
                        'defaultValue': 0,
                        'unit': 'Count'
                    }
                ]
            )
            print(f"Created metric filter: {filter_name}")
        except Exception as e:
            print(f"Error creating metric filter {filter_name}: {e}")
    
    def query_errors(
        self,
        log_group_name: str,
        start_time: datetime,
        end_time: datetime,
        error_pattern: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query errors from CloudWatch Logs
        
        Args:
            log_group_name: Log group name
            start_time: Start time
            end_time: End time
            error_pattern: Error pattern to search for
            limit: Maximum number of results
            
        Returns:
            List of error log entries
        """
        # Build query
        if error_pattern:
            query = f"""
            fields @timestamp, @message, @logStream
            | filter @message like /{error_pattern}/
            | sort @timestamp desc
            | limit {limit}
            """
        else:
            query = f"""
            fields @timestamp, @message, @logStream
            | filter @message like /ERROR/ or @message like /Exception/ or @message like /Failed/
            | sort @timestamp desc
            | limit {limit}
            """
        
        # Start query
        response = self.logs.start_query(
            logGroupName=log_group_name,
            startTime=int(start_time.timestamp()),
            endTime=int(end_time.timestamp()),
            queryString=query
        )
        
        query_id = response['queryId']
        
        # Wait for query to complete
        while True:
            result = self.logs.get_query_results(queryId=query_id)
            status = result['status']
            
            if status == 'Complete':
                return result['results']
            elif status == 'Failed':
                raise Exception(f"Query failed: {result}")
            
            # Wait before checking again
            import time
            time.sleep(1)
    
    def analyze_error_trends(
        self,
        function_name: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Analyze error trends for a function
        
        Args:
            function_name: Lambda function name
            hours: Number of hours to analyze
            
        Returns:
            Error trend analysis
        """
        log_group_name = f"/aws/lambda/{function_name}"
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Query for errors
        query = f"""
        fields @timestamp, @message
        | filter @message like /ERROR/ or @message like /Exception/
        | stats count() as error_count by bin(5m) as time_bucket
        | sort time_bucket desc
        """
        
        response = self.logs.start_query(
            logGroupName=log_group_name,
            startTime=int(start_time.timestamp()),
            endTime=int(end_time.timestamp()),
            queryString=query
        )
        
        query_id = response['queryId']
        
        # Wait for results
        while True:
            result = self.logs.get_query_results(queryId=query_id)
            if result['status'] == 'Complete':
                break
            import time
            time.sleep(1)
        
        # Analyze results
        error_counts = []
        for row in result['results']:
            error_count = next((field['value'] for field in row if field['field'] == 'error_count'), 0)
            error_counts.append(int(error_count))
        
        total_errors = sum(error_counts)
        avg_errors = total_errors / len(error_counts) if error_counts else 0
        max_errors = max(error_counts) if error_counts else 0
        
        return {
            'function_name': function_name,
            'time_period_hours': hours,
            'total_errors': total_errors,
            'average_errors_per_5min': avg_errors,
            'max_errors_per_5min': max_errors,
            'error_trend': error_counts
        }
    
    def get_top_errors(
        self,
        function_name: str,
        hours: int = 24,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top errors by frequency
        
        Args:
            function_name: Lambda function name
            hours: Number of hours to analyze
            limit: Number of top errors to return
            
        Returns:
            List of top errors with counts
        """
        log_group_name = f"/aws/lambda/{function_name}"
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        query = f"""
        fields @message
        | filter @message like /ERROR/ or @message like /Exception/
        | stats count() as error_count by @message
        | sort error_count desc
        | limit {limit}
        """
        
        response = self.logs.start_query(
            logGroupName=log_group_name,
            startTime=int(start_time.timestamp()),
            endTime=int(end_time.timestamp()),
            queryString=query
        )
        
        query_id = response['queryId']
        
        # Wait for results
        while True:
            result = self.logs.get_query_results(queryId=query_id)
            if result['status'] == 'Complete':
                break
            import time
            time.sleep(1)
        
        # Format results
        top_errors = []
        for row in result['results']:
            error_message = next((field['value'] for field in row if field['field'] == '@message'), '')
            error_count = next((field['value'] for field in row if field['field'] == 'error_count'), 0)
            
            top_errors.append({
                'error_message': error_message,
                'count': int(error_count)
            })
        
        return top_errors
    
    def create_error_dashboard(self, dashboard_name: str = "RISE-Errors"):
        """Create CloudWatch dashboard for error monitoring"""
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["RISE/Errors", "Errors", {"stat": "Sum"}]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": self.region,
                        "title": "Total Errors (5min)",
                        "yAxis": {
                            "left": {
                                "min": 0
                            }
                        }
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["RISE/Errors", "Exceptions", {"stat": "Sum"}]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": self.region,
                        "title": "Exceptions (5min)",
                        "yAxis": {
                            "left": {
                                "min": 0
                            }
                        }
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["RISE/Errors", "Timeouts", {"stat": "Sum"}]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": self.region,
                        "title": "Lambda Timeouts (5min)",
                        "yAxis": {
                            "left": {
                                "min": 0
                            }
                        }
                    }
                },
                {
                    "type": "log",
                    "properties": {
                        "query": f"SOURCE '/aws/lambda/rise-*'\n| fields @timestamp, @message, @logStream\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 20",
                        "region": self.region,
                        "title": "Recent Errors",
                        "stacked": False
                    }
                }
            ]
        }
        
        self.cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_body)
        )
        
        print(f"Created error dashboard: {dashboard_name}")
    
    def send_error_alert(
        self,
        sns_topic_arn: str,
        function_name: str,
        error_message: str,
        severity: str = "HIGH"
    ):
        """
        Send error alert via SNS
        
        Args:
            sns_topic_arn: SNS topic ARN
            function_name: Lambda function name
            error_message: Error message
            severity: Error severity
        """
        subject = f"[{severity}] RISE Error Alert: {function_name}"
        
        message = f"""
RISE Platform Error Alert

Function: {function_name}
Severity: {severity}
Timestamp: {datetime.utcnow().isoformat()}

Error Message:
{error_message}

Please investigate immediately.
        """
        
        self.sns.publish(
            TopicArn=sns_topic_arn,
            Subject=subject,
            Message=message
        )
