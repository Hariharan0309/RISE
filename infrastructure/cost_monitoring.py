"""
RISE Cost Monitoring and Budget Alerts
Implements cost tracking and budget management
"""

import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from infrastructure.monitoring_config import COST_MONITORING_CONFIG


class CostMonitor:
    """Monitors AWS costs and manages budgets"""
    
    def __init__(self, account_id: str, region: str = "us-east-1"):
        """
        Initialize cost monitor
        
        Args:
            account_id: AWS account ID
            region: AWS region
        """
        self.ce = boto3.client('ce', region_name='us-east-1')  # Cost Explorer is us-east-1 only
        self.budgets = boto3.client('budgets', region_name='us-east-1')
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.account_id = account_id
        self.region = region
    
    def create_monthly_budget(
        self,
        budget_name: str,
        amount_usd: float,
        sns_topic_arn: str,
        alert_thresholds: List[int] = [50, 75, 90, 100]
    ):
        """
        Create monthly budget with alerts
        
        Args:
            budget_name: Budget name
            amount_usd: Monthly budget amount in USD
            sns_topic_arn: SNS topic ARN for alerts
            alert_thresholds: Alert thresholds as percentages
        """
        # Create budget
        budget = {
            'BudgetName': budget_name,
            'BudgetType': 'COST',
            'TimeUnit': 'MONTHLY',
            'BudgetLimit': {
                'Amount': str(amount_usd),
                'Unit': 'USD'
            },
            'CostFilters': {
                'TagKeyValue': [f'user:Service$RISE']
            },
            'CostTypes': {
                'IncludeTax': True,
                'IncludeSubscription': True,
                'UseBlended': False,
                'IncludeRefund': False,
                'IncludeCredit': False,
                'IncludeUpfront': True,
                'IncludeRecurring': True,
                'IncludeOtherSubscription': True,
                'IncludeSupport': True,
                'IncludeDiscount': True,
                'UseAmortized': False
            }
        }
        
        # Create notifications for each threshold
        notifications = []
        for threshold in alert_thresholds:
            notifications.append({
                'Notification': {
                    'NotificationType': 'ACTUAL',
                    'ComparisonOperator': 'GREATER_THAN',
                    'Threshold': threshold,
                    'ThresholdType': 'PERCENTAGE',
                    'NotificationState': 'ALARM'
                },
                'Subscribers': [
                    {
                        'SubscriptionType': 'SNS',
                        'Address': sns_topic_arn
                    }
                ]
            })
        
        try:
            self.budgets.create_budget(
                AccountId=self.account_id,
                Budget=budget,
                NotificationsWithSubscribers=notifications
            )
            print(f"Created budget: {budget_name}")
        except self.budgets.exceptions.DuplicateRecordException:
            print(f"Budget {budget_name} already exists, updating...")
            self.budgets.update_budget(
                AccountId=self.account_id,
                NewBudget=budget
            )
    
    def get_current_month_cost(self) -> Dict[str, Any]:
        """
        Get current month's cost
        
        Returns:
            Cost breakdown by service
        """
        # Get first day of current month
        today = datetime.utcnow()
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        
        response = self.ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ],
            Filter={
                'Tags': {
                    'Key': 'Service',
                    'Values': ['RISE']
                }
            }
        )
        
        # Parse results
        total_cost = 0.0
        service_costs = {}
        
        if response['ResultsByTime']:
            for group in response['ResultsByTime'][0]['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                service_costs[service] = cost
                total_cost += cost
        
        return {
            'total_cost_usd': total_cost,
            'service_costs': service_costs,
            'period': {
                'start': start_date,
                'end': end_date
            }
        }
    
    def get_cost_forecast(self, days: int = 30) -> Dict[str, Any]:
        """
        Get cost forecast
        
        Args:
            days: Number of days to forecast
            
        Returns:
            Cost forecast
        """
        today = datetime.utcnow()
        start_date = today.strftime('%Y-%m-%d')
        end_date = (today + timedelta(days=days)).strftime('%Y-%m-%d')
        
        response = self.ce.get_cost_forecast(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Metric='UNBLENDED_COST',
            Granularity='MONTHLY',
            Filter={
                'Tags': {
                    'Key': 'Service',
                    'Values': ['RISE']
                }
            }
        )
        
        forecast_cost = float(response['Total']['Amount'])
        
        return {
            'forecast_cost_usd': forecast_cost,
            'forecast_period_days': days,
            'start_date': start_date,
            'end_date': end_date
        }
    
    def get_service_costs(
        self,
        start_date: str,
        end_date: str,
        services: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Get costs by service
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            services: List of services to filter (optional)
            
        Returns:
            Service costs
        """
        filter_config = {
            'Tags': {
                'Key': 'Service',
                'Values': ['RISE']
            }
        }
        
        if services:
            filter_config = {
                'And': [
                    filter_config,
                    {
                        'Dimensions': {
                            'Key': 'SERVICE',
                            'Values': services
                        }
                    }
                ]
            }
        
        response = self.ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ],
            Filter=filter_config
        )
        
        # Aggregate costs by service
        service_costs = {}
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                
                if service in service_costs:
                    service_costs[service] += cost
                else:
                    service_costs[service] = cost
        
        return service_costs
    
    def get_lambda_costs(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get Lambda-specific costs"""
        response = self.ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            Filter={
                'And': [
                    {
                        'Tags': {
                            'Key': 'Service',
                            'Values': ['RISE']
                        }
                    },
                    {
                        'Dimensions': {
                            'Key': 'SERVICE',
                            'Values': ['AWS Lambda']
                        }
                    }
                ]
            }
        )
        
        total_cost = 0.0
        daily_costs = []
        
        for result in response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            cost = float(result['Total']['UnblendedCost']['Amount'])
            total_cost += cost
            daily_costs.append({'date': date, 'cost': cost})
        
        return {
            'total_cost_usd': total_cost,
            'daily_costs': daily_costs
        }
    
    def get_bedrock_costs(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get Amazon Bedrock costs"""
        response = self.ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            Filter={
                'And': [
                    {
                        'Tags': {
                            'Key': 'Service',
                            'Values': ['RISE']
                        }
                    },
                    {
                        'Dimensions': {
                            'Key': 'SERVICE',
                            'Values': ['Amazon Bedrock']
                        }
                    }
                ]
            }
        )
        
        total_cost = 0.0
        daily_costs = []
        
        for result in response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            cost = float(result['Total']['UnblendedCost']['Amount'])
            total_cost += cost
            daily_costs.append({'date': date, 'cost': cost})
        
        return {
            'total_cost_usd': total_cost,
            'daily_costs': daily_costs
        }
    
    def track_cost_metrics(self):
        """Track cost metrics to CloudWatch"""
        # Get current month cost
        current_cost = self.get_current_month_cost()
        
        # Put total cost metric
        self.cloudwatch.put_metric_data(
            Namespace='RISE/Cost',
            MetricData=[
                {
                    'MetricName': 'TotalMonthlyCost',
                    'Value': current_cost['total_cost_usd'],
                    'Unit': 'None',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
        
        # Put service-specific costs
        for service, cost in current_cost['service_costs'].items():
            self.cloudwatch.put_metric_data(
                Namespace='RISE/Cost',
                MetricData=[
                    {
                        'MetricName': 'ServiceCost',
                        'Value': cost,
                        'Unit': 'None',
                        'Timestamp': datetime.utcnow(),
                        'Dimensions': [
                            {
                                'Name': 'Service',
                                'Value': service
                            }
                        ]
                    }
                ]
            )
    
    def create_cost_anomaly_detector(self):
        """Create cost anomaly detector"""
        try:
            response = self.ce.create_anomaly_monitor(
                AnomalyMonitor={
                    'MonitorName': 'RISE-Cost-Anomaly-Monitor',
                    'MonitorType': 'DIMENSIONAL',
                    'MonitorDimension': 'SERVICE',
                    'MonitorSpecification': {
                        'Tags': {
                            'Key': 'Service',
                            'Values': ['RISE']
                        }
                    }
                }
            )
            
            monitor_arn = response['MonitorArn']
            print(f"Created cost anomaly monitor: {monitor_arn}")
            
            return monitor_arn
        except Exception as e:
            print(f"Error creating cost anomaly monitor: {e}")
            return None
    
    def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get cost optimization recommendations"""
        recommendations = []
        
        # Get current costs
        today = datetime.utcnow()
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        
        service_costs = self.get_service_costs(start_date, end_date)
        
        # Analyze Lambda costs
        if 'AWS Lambda' in service_costs:
            lambda_cost = service_costs['AWS Lambda']
            if lambda_cost > 100:  # If Lambda costs > $100/month
                recommendations.append({
                    'service': 'AWS Lambda',
                    'recommendation': 'Consider using Lambda reserved concurrency or Savings Plans',
                    'potential_savings_percent': 15,
                    'current_cost': lambda_cost
                })
        
        # Analyze DynamoDB costs
        if 'Amazon DynamoDB' in service_costs:
            dynamodb_cost = service_costs['Amazon DynamoDB']
            if dynamodb_cost > 50:
                recommendations.append({
                    'service': 'Amazon DynamoDB',
                    'recommendation': 'Review table capacity modes and consider on-demand billing',
                    'potential_savings_percent': 20,
                    'current_cost': dynamodb_cost
                })
        
        # Analyze S3 costs
        if 'Amazon Simple Storage Service' in service_costs:
            s3_cost = service_costs['Amazon Simple Storage Service']
            if s3_cost > 30:
                recommendations.append({
                    'service': 'Amazon S3',
                    'recommendation': 'Review lifecycle policies and consider Intelligent-Tiering',
                    'potential_savings_percent': 30,
                    'current_cost': s3_cost
                })
        
        return recommendations
    
    def generate_cost_report(self) -> Dict[str, Any]:
        """Generate comprehensive cost report"""
        today = datetime.utcnow()
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        
        # Get current costs
        current_cost = self.get_current_month_cost()
        
        # Get forecast
        forecast = self.get_cost_forecast(30)
        
        # Get service breakdown
        service_costs = self.get_service_costs(start_date, end_date)
        
        # Get recommendations
        recommendations = self.get_cost_optimization_recommendations()
        
        # Calculate budget utilization
        budget_amount = COST_MONITORING_CONFIG['monthly_budget_usd']
        budget_utilization = (current_cost['total_cost_usd'] / budget_amount) * 100
        
        return {
            'report_date': today.isoformat(),
            'current_month_cost': current_cost,
            'forecast_next_30_days': forecast,
            'service_breakdown': service_costs,
            'budget_amount_usd': budget_amount,
            'budget_utilization_percent': budget_utilization,
            'optimization_recommendations': recommendations
        }
