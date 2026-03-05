"""
Tests for RISE Monitoring System
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.monitoring_config import (
    LambdaMonitoringConfig,
    AlarmSeverity,
    MetricNamespace,
    get_lambda_config,
    get_all_lambda_functions,
    get_critical_functions,
)
from infrastructure.cloudwatch_alarms import CloudWatchAlarmsManager
from infrastructure.custom_metrics import CustomMetricsTracker
from infrastructure.error_tracking import ErrorTracker
from infrastructure.cost_monitoring import CostMonitor
from infrastructure.monitoring_dashboard import MonitoringDashboard


class TestMonitoringConfig(unittest.TestCase):
    """Test monitoring configuration"""
    
    def test_lambda_config_exists(self):
        """Test that Lambda configurations are defined"""
        config = get_lambda_config('image_analysis')
        self.assertIsNotNone(config)
        self.assertEqual(config.function_name, 'rise-image-analysis')
        self.assertEqual(config.alarm_severity, AlarmSeverity.CRITICAL)
    
    def test_get_all_lambda_functions(self):
        """Test getting all Lambda function names"""
        functions = get_all_lambda_functions()
        self.assertIsInstance(functions, list)
        self.assertGreater(len(functions), 0)
        self.assertIn('rise-image-analysis', functions)
    
    def test_get_critical_functions(self):
        """Test getting critical Lambda functions"""
        critical = get_critical_functions()
        self.assertIsInstance(critical, list)
        self.assertIn('rise-image-analysis', critical)
        self.assertIn('rise-pest-analysis', critical)


class TestCloudWatchAlarms(unittest.TestCase):
    """Test CloudWatch alarms manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sns_topic_arn = "arn:aws:sns:us-east-1:123456789012:test-topic"
        
    @patch('infrastructure.cloudwatch_alarms.boto3.client')
    def test_create_lambda_alarms(self, mock_boto_client):
        """Test creating Lambda alarms"""
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch
        
        manager = CloudWatchAlarmsManager(self.sns_topic_arn)
        alarms = manager.create_lambda_alarms('image_analysis')
        
        # Should create 5 alarms (error, duration, throttle, concurrent, invocation)
        self.assertEqual(len(alarms), 5)
        self.assertEqual(mock_cloudwatch.put_metric_alarm.call_count, 5)
    
    @patch('infrastructure.cloudwatch_alarms.boto3.client')
    def test_create_api_gateway_alarms(self, mock_boto_client):
        """Test creating API Gateway alarms"""
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch
        
        manager = CloudWatchAlarmsManager(self.sns_topic_arn)
        alarms = manager.create_api_gateway_alarms()
        
        # Should create 3 alarms (latency, 4XX, 5XX)
        self.assertEqual(len(alarms), 3)
        self.assertEqual(mock_cloudwatch.put_metric_alarm.call_count, 3)
    
    @patch('infrastructure.cloudwatch_alarms.boto3.client')
    def test_create_dynamodb_alarms(self, mock_boto_client):
        """Test creating DynamoDB alarms"""
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch
        
        manager = CloudWatchAlarmsManager(self.sns_topic_arn)
        alarms = manager.create_dynamodb_alarms('RISE-DiagnosisHistory')
        
        # Should create 3 alarms (read throttle, write throttle, system errors)
        self.assertEqual(len(alarms), 3)
        self.assertEqual(mock_cloudwatch.put_metric_alarm.call_count, 3)


class TestCustomMetrics(unittest.TestCase):
    """Test custom metrics tracker"""
    
    @patch('infrastructure.custom_metrics.boto3.client')
    @patch('infrastructure.custom_metrics.boto3.resource')
    def test_track_diagnosis_accuracy(self, mock_boto_resource, mock_boto_client):
        """Test tracking diagnosis accuracy"""
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch
        
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_dynamodb
        
        tracker = CustomMetricsTracker()
        tracker.track_diagnosis_accuracy(
            diagnosis_id="test_123",
            predicted_disease="Late Blight",
            actual_disease="Late Blight",
            confidence_score=92.5
        )
        
        # Should put metrics to CloudWatch
        self.assertTrue(mock_cloudwatch.put_metric_data.called)
    
    @patch('infrastructure.custom_metrics.boto3.client')
    @patch('infrastructure.custom_metrics.boto3.resource')
    def test_track_user_engagement(self, mock_boto_resource, mock_boto_client):
        """Test tracking user engagement"""
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch
        
        tracker = CustomMetricsTracker()
        tracker.track_user_engagement(
            user_id="user_123",
            session_duration_seconds=1200,
            features_used=["diagnosis", "weather"],
            language="hi"
        )
        
        # Should put multiple metrics
        self.assertTrue(mock_cloudwatch.put_metric_data.called)
        self.assertGreaterEqual(mock_cloudwatch.put_metric_data.call_count, 3)
    
    @patch('infrastructure.custom_metrics.boto3.client')
    @patch('infrastructure.custom_metrics.boto3.resource')
    def test_track_cost_savings(self, mock_boto_resource, mock_boto_client):
        """Test tracking cost savings"""
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch
        
        tracker = CustomMetricsTracker()
        tracker.track_cost_savings(
            user_id="user_123",
            savings_type="fertilizer",
            amount_saved_inr=5000,
            category="precision_agriculture"
        )
        
        # Should put metric to CloudWatch
        self.assertTrue(mock_cloudwatch.put_metric_data.called)


class TestErrorTracking(unittest.TestCase):
    """Test error tracking"""
    
    @patch('infrastructure.error_tracking.boto3.client')
    def test_create_log_groups(self, mock_boto_client):
        """Test creating log groups"""
        mock_logs = Mock()
        mock_boto_client.return_value = mock_logs
        
        tracker = ErrorTracker()
        function_names = ['rise-test-function']
        tracker.create_log_groups(function_names)
        
        # Should create log group and set retention
        self.assertTrue(mock_logs.create_log_group.called or 
                       mock_logs.put_retention_policy.called)
    
    @patch('infrastructure.error_tracking.boto3.client')
    def test_create_metric_filters(self, mock_boto_client):
        """Test creating metric filters"""
        mock_logs = Mock()
        mock_boto_client.return_value = mock_logs
        
        tracker = ErrorTracker()
        tracker.create_metric_filters('rise-test-function')
        
        # Should create multiple metric filters
        self.assertTrue(mock_logs.put_metric_filter.called)
        self.assertGreaterEqual(mock_logs.put_metric_filter.call_count, 5)


class TestCostMonitoring(unittest.TestCase):
    """Test cost monitoring"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.account_id = "123456789012"
    
    @patch('infrastructure.cost_monitoring.boto3.client')
    def test_create_monthly_budget(self, mock_boto_client):
        """Test creating monthly budget"""
        mock_budgets = Mock()
        mock_boto_client.return_value = mock_budgets
        
        monitor = CostMonitor(self.account_id)
        monitor.create_monthly_budget(
            budget_name="Test-Budget",
            amount_usd=1000,
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test",
            alert_thresholds=[50, 75, 90, 100]
        )
        
        # Should create budget
        self.assertTrue(mock_budgets.create_budget.called or 
                       mock_budgets.update_budget.called)
    
    @patch('infrastructure.cost_monitoring.boto3.client')
    def test_get_current_month_cost(self, mock_boto_client):
        """Test getting current month cost"""
        mock_ce = Mock()
        mock_ce.get_cost_and_usage.return_value = {
            'ResultsByTime': [
                {
                    'Groups': [
                        {
                            'Keys': ['AWS Lambda'],
                            'Metrics': {
                                'UnblendedCost': {'Amount': '50.00'}
                            }
                        }
                    ]
                }
            ]
        }
        mock_boto_client.return_value = mock_ce
        
        monitor = CostMonitor(self.account_id)
        result = monitor.get_current_month_cost()
        
        self.assertIn('total_cost_usd', result)
        self.assertIn('service_costs', result)
        self.assertEqual(result['total_cost_usd'], 50.0)


class TestMonitoringDashboard(unittest.TestCase):
    """Test monitoring dashboard"""
    
    @patch('infrastructure.monitoring_dashboard.boto3.client')
    def test_create_lambda_overview_dashboard(self, mock_boto_client):
        """Test creating Lambda overview dashboard"""
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch
        
        dashboard = MonitoringDashboard()
        dashboard.create_lambda_overview_dashboard()
        
        # Should create dashboard
        self.assertTrue(mock_cloudwatch.put_dashboard.called)
    
    @patch('infrastructure.monitoring_dashboard.boto3.client')
    def test_create_agricultural_metrics_dashboard(self, mock_boto_client):
        """Test creating agricultural metrics dashboard"""
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch
        
        dashboard = MonitoringDashboard()
        dashboard.create_agricultural_metrics_dashboard()
        
        # Should create dashboard
        self.assertTrue(mock_cloudwatch.put_dashboard.called)
    
    @patch('infrastructure.monitoring_dashboard.boto3.client')
    def test_list_dashboards(self, mock_boto_client):
        """Test listing dashboards"""
        mock_cloudwatch = Mock()
        mock_cloudwatch.list_dashboards.return_value = {
            'DashboardEntries': [
                {'DashboardName': 'RISE-Lambda-Overview'},
                {'DashboardName': 'RISE-Agricultural-Metrics'}
            ]
        }
        mock_boto_client.return_value = mock_cloudwatch
        
        dashboard = MonitoringDashboard()
        dashboards = dashboard.list_dashboards()
        
        self.assertEqual(len(dashboards), 2)
        self.assertIn('RISE-Lambda-Overview', dashboards)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
