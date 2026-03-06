"""
RISE Monitoring Dashboard Configuration
Creates comprehensive CloudWatch dashboards for monitoring
"""

import boto3
import json
from typing import List, Dict, Any
from infrastructure.monitoring_config import (
    LAMBDA_FUNCTIONS,
    API_GATEWAY_CONFIG,
    DYNAMODB_TABLES,
    get_all_lambda_functions,
    get_critical_functions,
)


class MonitoringDashboard:
    """Creates and manages CloudWatch dashboards"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize monitoring dashboard
        
        Args:
            region: AWS region
        """
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.region = region
    
    def create_lambda_overview_dashboard(self, dashboard_name: str = "RISE-Lambda-Overview"):
        """Create overview dashboard for all Lambda functions"""
        
        # Get all function names
        function_names = get_all_lambda_functions()
        
        widgets = []
        
        # Total invocations widget
        invocation_metrics = [
            ["AWS/Lambda", "Invocations", {"stat": "Sum", "label": func}]
            for func in function_names[:10]  # Limit to 10 for readability
        ]
        
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": invocation_metrics,
                "period": 300,
                "stat": "Sum",
                "region": self.region,
                "title": "Lambda Invocations (Top 10)",
                "yAxis": {"left": {"min": 0}}
            }
        })
        
        # Error rate widget
        error_metrics = [
            ["AWS/Lambda", "Errors", {"stat": "Sum", "label": func}]
            for func in get_critical_functions()
        ]
        
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": error_metrics,
                "period": 300,
                "stat": "Sum",
                "region": self.region,
                "title": "Lambda Errors (Critical Functions)",
                "yAxis": {"left": {"min": 0}}
            }
        })
        
        # Duration widget
        duration_metrics = [
            ["AWS/Lambda", "Duration", {"stat": "Average", "label": func}]
            for func in get_critical_functions()
        ]
        
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": duration_metrics,
                "period": 300,
                "stat": "Average",
                "region": self.region,
                "title": "Lambda Duration (Critical Functions)",
                "yAxis": {"left": {"min": 0}}
            }
        })
        
        # Throttles widget
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/Lambda", "Throttles", {"stat": "Sum"}]
                ],
                "period": 300,
                "stat": "Sum",
                "region": self.region,
                "title": "Lambda Throttles (All Functions)",
                "yAxis": {"left": {"min": 0}}
            }
        })
        
        dashboard_body = {"widgets": widgets}
        
        self.cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_body)
        )
        
        print(f"Created Lambda overview dashboard: {dashboard_name}")
    
    def create_agricultural_metrics_dashboard(
        self,
        dashboard_name: str = "RISE-Agricultural-Metrics"
    ):
        """Create dashboard for custom agricultural metrics"""
        
        widgets = [
            # Diagnosis accuracy
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["RISE/Agricultural", "DiagnosisAccuracy", {"stat": "Average"}]
                    ],
                    "period": 3600,
                    "stat": "Average",
                    "region": self.region,
                    "title": "Crop Diagnosis Accuracy",
                    "yAxis": {"left": {"min": 0, "max": 100}}
                }
            },
            # Pest identification accuracy
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["RISE/Agricultural", "PestIdentificationAccuracy", {"stat": "Average"}]
                    ],
                    "period": 3600,
                    "stat": "Average",
                    "region": self.region,
                    "title": "Pest Identification Accuracy",
                    "yAxis": {"left": {"min": 0, "max": 100}}
                }
            },
            # User engagement
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["RISE/Agricultural", "ActiveUsers", {"stat": "Sum"}]
                    ],
                    "period": 3600,
                    "stat": "Sum",
                    "region": self.region,
                    "title": "Active Users (Hourly)",
                    "yAxis": {"left": {"min": 0}}
                }
            },
            # Yield improvement
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["RISE/Agricultural", "YieldImprovement", {"stat": "Average"}]
                    ],
                    "period": 86400,
                    "stat": "Average",
                    "region": self.region,
                    "title": "Average Yield Improvement (%)",
                    "yAxis": {"left": {"min": 0}}
                }
            },
            # Cost savings
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["RISE/Agricultural", "CostSavings", {"stat": "Sum"}]
                    ],
                    "period": 86400,
                    "stat": "Sum",
                    "region": self.region,
                    "title": "Total Cost Savings (INR)",
                    "yAxis": {"left": {"min": 0}}
                }
            },
            # Equipment utilization
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["RISE/Agricultural", "EquipmentUtilization", {"stat": "Average"}]
                    ],
                    "period": 3600,
                    "stat": "Average",
                    "region": self.region,
                    "title": "Equipment Utilization Rate (%)",
                    "yAxis": {"left": {"min": 0, "max": 100}}
                }
            },
            # Bulk purchase savings
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["RISE/Agricultural", "BulkPurchaseSavings", {"stat": "Average"}]
                    ],
                    "period": 86400,
                    "stat": "Average",
                    "region": self.region,
                    "title": "Bulk Purchase Savings (%)",
                    "yAxis": {"left": {"min": 0, "max": 100}}
                }
            },
            # Scheme application success
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["RISE/Agricultural", "SchemeApplicationSuccess", {"stat": "Average"}]
                    ],
                    "period": 86400,
                    "stat": "Average",
                    "region": self.region,
                    "title": "Scheme Application Success Rate (%)",
                    "yAxis": {"left": {"min": 0, "max": 100}}
                }
            }
        ]
        
        dashboard_body = {"widgets": widgets}
        
        self.cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_body)
        )
        
        print(f"Created agricultural metrics dashboard: {dashboard_name}")
    
    def create_api_gateway_dashboard(
        self,
        dashboard_name: str = "RISE-API-Gateway"
    ):
        """Create dashboard for API Gateway monitoring"""
        
        api_name = API_GATEWAY_CONFIG['api_name']
        stage = API_GATEWAY_CONFIG['stage']
        
        widgets = [
            # Request count
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/ApiGateway", "Count", {"stat": "Sum"}]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": self.region,
                    "title": "API Requests (5min)",
                    "yAxis": {"left": {"min": 0}}
                }
            },
            # Latency
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/ApiGateway", "Latency", {"stat": "Average"}],
                        [".", ".", {"stat": "p99"}]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": self.region,
                    "title": "API Latency (ms)",
                    "yAxis": {"left": {"min": 0}}
                }
            },
            # 4XX errors
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/ApiGateway", "4XXError", {"stat": "Sum"}]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": self.region,
                    "title": "4XX Errors (5min)",
                    "yAxis": {"left": {"min": 0}}
                }
            },
            # 5XX errors
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/ApiGateway", "5XXError", {"stat": "Sum"}]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": self.region,
                    "title": "5XX Errors (5min)",
                    "yAxis": {"left": {"min": 0}}
                }
            },
            # Cache hit/miss
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/ApiGateway", "CacheHitCount", {"stat": "Sum", "label": "Cache Hits"}],
                        [".", "CacheMissCount", {"stat": "Sum", "label": "Cache Misses"}]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": self.region,
                    "title": "API Cache Performance",
                    "yAxis": {"left": {"min": 0}}
                }
            }
        ]
        
        dashboard_body = {"widgets": widgets}
        
        self.cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_body)
        )
        
        print(f"Created API Gateway dashboard: {dashboard_name}")
    
    def create_dynamodb_dashboard(
        self,
        dashboard_name: str = "RISE-DynamoDB"
    ):
        """Create dashboard for DynamoDB monitoring"""
        
        table_names = list(DYNAMODB_TABLES.keys())
        
        widgets = []
        
        # Read capacity for each table
        for table_name in table_names[:5]:  # Limit to 5 tables
            widgets.append({
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/DynamoDB", "ConsumedReadCapacityUnits", 
                         {"stat": "Sum", "label": table_name}]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": self.region,
                    "title": f"{table_name} - Read Capacity",
                    "yAxis": {"left": {"min": 0}}
                }
            })
        
        # Write capacity for each table
        for table_name in table_names[:5]:
            widgets.append({
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/DynamoDB", "ConsumedWriteCapacityUnits",
                         {"stat": "Sum", "label": table_name}]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": self.region,
                    "title": f"{table_name} - Write Capacity",
                    "yAxis": {"left": {"min": 0}}
                }
            })
        
        # Throttles
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/DynamoDB", "ReadThrottleEvents", {"stat": "Sum", "label": "Read Throttles"}],
                    [".", "WriteThrottleEvents", {"stat": "Sum", "label": "Write Throttles"}]
                ],
                "period": 300,
                "stat": "Sum",
                "region": self.region,
                "title": "DynamoDB Throttles (All Tables)",
                "yAxis": {"left": {"min": 0}}
            }
        })
        
        dashboard_body = {"widgets": widgets}
        
        self.cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_body)
        )
        
        print(f"Created DynamoDB dashboard: {dashboard_name}")
    
    def create_cost_dashboard(self, dashboard_name: str = "RISE-Cost-Monitoring"):
        """Create dashboard for cost monitoring"""
        
        widgets = [
            # Total monthly cost
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["RISE/Cost", "TotalMonthlyCost", {"stat": "Average"}]
                    ],
                    "period": 86400,
                    "stat": "Average",
                    "region": self.region,
                    "title": "Total Monthly Cost (USD)",
                    "yAxis": {"left": {"min": 0}}
                }
            },
            # Service costs
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["RISE/Cost", "ServiceCost", {"stat": "Average"}]
                    ],
                    "period": 86400,
                    "stat": "Average",
                    "region": self.region,
                    "title": "Cost by Service (USD)",
                    "yAxis": {"left": {"min": 0}}
                }
            }
        ]
        
        dashboard_body = {"widgets": widgets}
        
        self.cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_body)
        )
        
        print(f"Created cost monitoring dashboard: {dashboard_name}")
    
    def create_all_dashboards(self):
        """Create all monitoring dashboards"""
        self.create_lambda_overview_dashboard()
        self.create_agricultural_metrics_dashboard()
        self.create_api_gateway_dashboard()
        self.create_dynamodb_dashboard()
        self.create_cost_dashboard()
        
        print("All monitoring dashboards created successfully!")
    
    def delete_dashboard(self, dashboard_name: str):
        """Delete a dashboard"""
        self.cloudwatch.delete_dashboards(DashboardNames=[dashboard_name])
        print(f"Deleted dashboard: {dashboard_name}")
    
    def list_dashboards(self) -> List[str]:
        """List all RISE dashboards"""
        response = self.cloudwatch.list_dashboards(DashboardNamePrefix="RISE-")
        return [dashboard['DashboardName'] for dashboard in response['DashboardEntries']]
