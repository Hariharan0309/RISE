"""
RISE Analytics Data Aggregator
Aggregates metrics from CloudWatch and DynamoDB for analytics dashboard
"""

import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import json


class AnalyticsAggregator:
    """Aggregates analytics data from various sources"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize analytics aggregator
        
        Args:
            region: AWS region
        """
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.region = region
    
    def get_user_adoption_metrics(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Get user adoption metrics
        
        Returns:
            - Active users count
            - Average session duration
            - Return rate
            - Language distribution
        """
        # Get active users from CloudWatch
        active_users_response = self.cloudwatch.get_metric_statistics(
            Namespace='RISE/Agricultural',
            MetricName='ActiveUsers',
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,  # 1 hour
            Statistics=['Sum'],
            Dimensions=[{'Name': 'Service', 'Value': 'Platform'}]
        )
        
        total_active_users = sum(
            point['Sum'] for point in active_users_response.get('Datapoints', [])
        )
        
        # Get session duration
        session_duration_response = self.cloudwatch.get_metric_statistics(
            Namespace='RISE/Agricultural',
            MetricName='SessionDuration',
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average'],
            Dimensions=[{'Name': 'Service', 'Value': 'Platform'}]
        )
        
        avg_session_duration = 0
        if session_duration_response.get('Datapoints'):
            avg_session_duration = sum(
                point['Average'] for point in session_duration_response['Datapoints']
            ) / len(session_duration_response['Datapoints'])
        
        # Get language distribution
        languages = ['Hindi', 'English', 'Tamil', 'Telugu', 'Kannada', 
                    'Bengali', 'Gujarati', 'Marathi', 'Punjabi']
        language_distribution = {}
        
        for language in languages:
            lang_response = self.cloudwatch.get_metric_statistics(
                Namespace='RISE/Agricultural',
                MetricName='ActiveUsers',
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum'],
                Dimensions=[
                    {'Name': 'Service', 'Value': 'Platform'},
                    {'Name': 'Language', 'Value': language}
                ]
            )
            
            lang_count = sum(
                point['Sum'] for point in lang_response.get('Datapoints', [])
            )
            if lang_count > 0:
                language_distribution[language] = int(lang_count)
        
        # Calculate return rate (users who came back within the period)
        # This would require user-level tracking in DynamoDB
        return_rate = self._calculate_return_rate(start_time, end_time)
        
        return {
            'active_users': int(total_active_users),
            'avg_session_duration_seconds': int(avg_session_duration),
            'avg_session_duration_minutes': round(avg_session_duration / 60, 1),
            'return_rate_percent': return_rate,
            'language_distribution': language_distribution
        }
    
    def get_impact_metrics(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Get impact metrics
        
        Returns:
            - Yield improvement
            - Cost reduction
            - Market access
            - Scheme adoption
        """
        # Yield improvement
        yield_response = self.cloudwatch.get_metric_statistics(
            Namespace='RISE/Agricultural',
            MetricName='YieldImprovement',
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average', 'Maximum', 'Minimum'],
            Dimensions=[{'Name': 'Service', 'Value': 'Platform'}]
        )
        
        avg_yield_improvement = 0
        max_yield_improvement = 0
        min_yield_improvement = 0
        
        if yield_response.get('Datapoints'):
            datapoints = yield_response['Datapoints']
            avg_yield_improvement = sum(p['Average'] for p in datapoints) / len(datapoints)
            max_yield_improvement = max(p['Maximum'] for p in datapoints)
            min_yield_improvement = min(p['Minimum'] for p in datapoints)
        
        # Cost savings
        cost_savings_response = self.cloudwatch.get_metric_statistics(
            Namespace='RISE/Agricultural',
            MetricName='CostSavings',
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum'],
            Dimensions=[{'Name': 'Service', 'Value': 'Platform'}]
        )
        
        total_cost_savings = sum(
            point['Sum'] for point in cost_savings_response.get('Datapoints', [])
        )
        
        # Market access (users using buyer connection)
        market_access_users = self._get_feature_users('buyer_connection', start_time, end_time)
        total_users = self.get_user_adoption_metrics(start_time, end_time)['active_users']
        market_access_percent = (market_access_users / total_users * 100) if total_users > 0 else 0
        
        # Scheme adoption
        scheme_users = self._get_feature_users('government_scheme', start_time, end_time)
        scheme_adoption_percent = (scheme_users / total_users * 100) if total_users > 0 else 0
        
        return {
            'yield_improvement': {
                'average_percent': round(avg_yield_improvement, 1),
                'maximum_percent': round(max_yield_improvement, 1),
                'minimum_percent': round(min_yield_improvement, 1),
                'target_range': '15-25%',
                'meets_target': 15 <= avg_yield_improvement <= 25
            },
            'cost_reduction': {
                'total_savings_inr': round(total_cost_savings, 2),
                'target_range': '20-30%',
            },
            'market_access': {
                'users_count': market_access_users,
                'percent': round(market_access_percent, 1),
                'target': '40%+',
                'meets_target': market_access_percent >= 40
            },
            'scheme_adoption': {
                'users_count': scheme_users,
                'percent': round(scheme_adoption_percent, 1),
                'target': '60%+',
                'meets_target': scheme_adoption_percent >= 60
            }
        }
    
    def get_technical_performance_metrics(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Get technical performance metrics
        
        Returns:
            - Response time
            - Accuracy rates
            - Uptime
            - User satisfaction
        """
        # API Gateway latency
        latency_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/ApiGateway',
            MetricName='Latency',
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average', 'p99'],
            Dimensions=[{'Name': 'ApiName', 'Value': 'RISE-API'}]
        )
        
        avg_latency = 0
        p99_latency = 0
        if latency_response.get('Datapoints'):
            datapoints = latency_response['Datapoints']
            avg_latency = sum(p.get('Average', 0) for p in datapoints) / len(datapoints)
            # p99 might not be available in all responses
            p99_values = [p.get('p99', 0) for p in datapoints if 'p99' in p]
            p99_latency = sum(p99_values) / len(p99_values) if p99_values else 0
        
        # Diagnosis accuracy
        diagnosis_accuracy_response = self.cloudwatch.get_metric_statistics(
            Namespace='RISE/Agricultural',
            MetricName='DiagnosisAccuracy',
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average'],
            Dimensions=[{'Name': 'Service', 'Value': 'CropDiagnosis'}]
        )
        
        avg_diagnosis_accuracy = 0
        if diagnosis_accuracy_response.get('Datapoints'):
            datapoints = diagnosis_accuracy_response['Datapoints']
            avg_diagnosis_accuracy = sum(p['Average'] for p in datapoints) / len(datapoints)
        
        # Pest identification accuracy
        pest_accuracy_response = self.cloudwatch.get_metric_statistics(
            Namespace='RISE/Agricultural',
            MetricName='PestIdentificationAccuracy',
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average'],
            Dimensions=[{'Name': 'Service', 'Value': 'PestIdentification'}]
        )
        
        avg_pest_accuracy = 0
        if pest_accuracy_response.get('Datapoints'):
            datapoints = pest_accuracy_response['Datapoints']
            avg_pest_accuracy = sum(p['Average'] for p in datapoints) / len(datapoints)
        
        # Calculate uptime from Lambda errors
        uptime_percent = self._calculate_uptime(start_time, end_time)
        
        return {
            'response_time': {
                'average_ms': round(avg_latency, 0),
                'p99_ms': round(p99_latency, 0),
                'target_ms': 3000,
                'meets_target': avg_latency < 3000
            },
            'accuracy_rates': {
                'diagnosis_percent': round(avg_diagnosis_accuracy, 1),
                'pest_identification_percent': round(avg_pest_accuracy, 1),
                'diagnosis_target': 90,
                'pest_target': 85,
                'diagnosis_meets_target': avg_diagnosis_accuracy >= 90,
                'pest_meets_target': avg_pest_accuracy >= 85
            },
            'uptime': {
                'percent': round(uptime_percent, 2),
                'target': 99.5,
                'meets_target': uptime_percent >= 99.5
            }
        }
    
    def get_feature_adoption_metrics(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get feature adoption metrics for all major features"""
        features = [
            'crop_diagnosis',
            'pest_identification',
            'soil_analysis',
            'weather_alerts',
            'market_prices',
            'buyer_connection',
            'government_scheme',
            'profitability_calculator',
            'equipment_sharing',
            'cooperative_buying'
        ]
        
        feature_metrics = {}
        
        for feature in features:
            usage_response = self.cloudwatch.get_metric_statistics(
                Namespace='RISE/Application',
                MetricName='FeatureUsage',
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum'],
                Dimensions=[
                    {'Name': 'Service', 'Value': 'Platform'},
                    {'Name': 'Feature', 'Value': feature}
                ]
            )
            
            total_usage = sum(
                point['Sum'] for point in usage_response.get('Datapoints', [])
            )
            
            # Get success rate
            success_response = self.cloudwatch.get_metric_statistics(
                Namespace='RISE/Application',
                MetricName='FeatureSuccessRate',
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average'],
                Dimensions=[
                    {'Name': 'Service', 'Value': 'Platform'},
                    {'Name': 'Feature', 'Value': feature}
                ]
            )
            
            avg_success_rate = 0
            if success_response.get('Datapoints'):
                datapoints = success_response['Datapoints']
                avg_success_rate = sum(p['Average'] for p in datapoints) / len(datapoints)
            
            feature_metrics[feature] = {
                'usage_count': int(total_usage),
                'success_rate_percent': round(avg_success_rate, 1)
            }
        
        return feature_metrics
    
    def get_resource_sharing_metrics(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get resource sharing and cooperative buying metrics"""
        # Equipment utilization
        equipment_util_response = self.cloudwatch.get_metric_statistics(
            Namespace='RISE/Agricultural',
            MetricName='EquipmentUtilization',
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average'],
            Dimensions=[{'Name': 'Service', 'Value': 'ResourceSharing'}]
        )
        
        avg_equipment_util = 0
        if equipment_util_response.get('Datapoints'):
            datapoints = equipment_util_response['Datapoints']
            avg_equipment_util = sum(p['Average'] for p in datapoints) / len(datapoints)
        
        # Bulk purchase savings
        bulk_savings_response = self.cloudwatch.get_metric_statistics(
            Namespace='RISE/Agricultural',
            MetricName='BulkPurchaseSavings',
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average'],
            Dimensions=[{'Name': 'Service', 'Value': 'CooperativeBuying'}]
        )
        
        avg_bulk_savings = 0
        if bulk_savings_response.get('Datapoints'):
            datapoints = bulk_savings_response['Datapoints']
            avg_bulk_savings = sum(p['Average'] for p in datapoints) / len(datapoints)
        
        # Total bulk purchase savings amount
        bulk_total_response = self.cloudwatch.get_metric_statistics(
            Namespace='RISE/Agricultural',
            MetricName='BulkPurchaseTotalSavings',
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum'],
            Dimensions=[{'Name': 'Service', 'Value': 'CooperativeBuying'}]
        )
        
        total_bulk_savings = sum(
            point['Sum'] for point in bulk_total_response.get('Datapoints', [])
        )
        
        return {
            'equipment_utilization': {
                'average_percent': round(avg_equipment_util, 1),
                'description': 'Average equipment usage rate'
            },
            'cooperative_buying': {
                'average_savings_percent': round(avg_bulk_savings, 1),
                'total_savings_inr': round(total_bulk_savings, 2),
                'target_range': '15-30%',
                'meets_target': 15 <= avg_bulk_savings <= 30
            }
        }
    
    def generate_comprehensive_report(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        return {
            'report_period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'duration_days': (end_time - start_time).days
            },
            'user_adoption': self.get_user_adoption_metrics(start_time, end_time),
            'impact_metrics': self.get_impact_metrics(start_time, end_time),
            'technical_performance': self.get_technical_performance_metrics(start_time, end_time),
            'feature_adoption': self.get_feature_adoption_metrics(start_time, end_time),
            'resource_sharing': self.get_resource_sharing_metrics(start_time, end_time),
            'generated_at': datetime.utcnow().isoformat()
        }
    
    # Helper methods
    
    def _calculate_return_rate(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Calculate user return rate"""
        # This would require user-level session tracking
        # For now, return a placeholder based on active users
        # In production, query DynamoDB for actual user sessions
        return 70.0  # Placeholder: 70% return rate
    
    def _get_feature_users(
        self,
        feature_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """Get count of users who used a specific feature"""
        response = self.cloudwatch.get_metric_statistics(
            Namespace='RISE/Application',
            MetricName='FeatureUsage',
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum'],
            Dimensions=[
                {'Name': 'Service', 'Value': 'Platform'},
                {'Name': 'Feature', 'Value': feature_name}
            ]
        )
        
        return int(sum(point['Sum'] for point in response.get('Datapoints', [])))
    
    def _calculate_uptime(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Calculate system uptime percentage"""
        # Get total invocations
        invocations_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Invocations',
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum']
        )
        
        total_invocations = sum(
            point['Sum'] for point in invocations_response.get('Datapoints', [])
        )
        
        # Get errors
        errors_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Errors',
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum']
        )
        
        total_errors = sum(
            point['Sum'] for point in errors_response.get('Datapoints', [])
        )
        
        if total_invocations == 0:
            return 100.0
        
        uptime = ((total_invocations - total_errors) / total_invocations) * 100
        return uptime


def lambda_handler(event, context):
    """
    Lambda handler for analytics aggregation
    
    Event format:
    {
        "action": "generate_report",
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-01-31T23:59:59Z"
    }
    """
    aggregator = AnalyticsAggregator()
    
    action = event.get('action', 'generate_report')
    
    # Parse dates
    start_time = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
    end_time = datetime.fromisoformat(event['end_time'].replace('Z', '+00:00'))
    
    if action == 'generate_report':
        report = aggregator.generate_comprehensive_report(start_time, end_time)
        return {
            'statusCode': 200,
            'body': json.dumps(report, default=str)
        }
    
    elif action == 'user_adoption':
        metrics = aggregator.get_user_adoption_metrics(start_time, end_time)
        return {
            'statusCode': 200,
            'body': json.dumps(metrics, default=str)
        }
    
    elif action == 'impact_metrics':
        metrics = aggregator.get_impact_metrics(start_time, end_time)
        return {
            'statusCode': 200,
            'body': json.dumps(metrics, default=str)
        }
    
    elif action == 'technical_performance':
        metrics = aggregator.get_technical_performance_metrics(start_time, end_time)
        return {
            'statusCode': 200,
            'body': json.dumps(metrics, default=str)
        }
    
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid action'})
        }
