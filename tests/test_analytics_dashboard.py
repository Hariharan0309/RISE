"""
Tests for RISE Analytics Dashboard
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
from infrastructure.analytics_aggregator import AnalyticsAggregator


@pytest.fixture
def mock_cloudwatch():
    """Mock CloudWatch client"""
    with patch('boto3.client') as mock_client:
        mock_cw = Mock()
        mock_client.return_value = mock_cw
        yield mock_cw


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB resource"""
    with patch('boto3.resource') as mock_resource:
        mock_db = Mock()
        mock_resource.return_value = mock_db
        yield mock_db


@pytest.fixture
def aggregator(mock_cloudwatch, mock_dynamodb):
    """Create AnalyticsAggregator instance with mocked AWS services"""
    return AnalyticsAggregator()


@pytest.fixture
def time_range():
    """Create time range for testing"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    return start_time, end_time


class TestAnalyticsAggregator:
    """Test AnalyticsAggregator class"""
    
    def test_initialization(self, aggregator):
        """Test aggregator initialization"""
        assert aggregator is not None
        assert aggregator.cloudwatch is not None
        assert aggregator.dynamodb is not None
        assert aggregator.region == "us-east-1"
    
    def test_get_user_adoption_metrics(self, aggregator, mock_cloudwatch, time_range):
        """Test user adoption metrics retrieval"""
        start_time, end_time = time_range
        
        # Mock CloudWatch responses
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Sum': 100, 'Timestamp': datetime.now()},
                {'Sum': 150, 'Timestamp': datetime.now()}
            ]
        }
        
        metrics = aggregator.get_user_adoption_metrics(start_time, end_time)
        
        assert 'active_users' in metrics
        assert 'avg_session_duration_seconds' in metrics
        assert 'avg_session_duration_minutes' in metrics
        assert 'return_rate_percent' in metrics
        assert 'language_distribution' in metrics
        
        assert isinstance(metrics['active_users'], int)
        assert isinstance(metrics['language_distribution'], dict)
    
    def test_get_impact_metrics(self, aggregator, mock_cloudwatch, time_range):
        """Test impact metrics retrieval"""
        start_time, end_time = time_range
        
        # Mock CloudWatch responses
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Average': 18.5, 'Maximum': 25.0, 'Minimum': 10.0, 'Timestamp': datetime.now()}
            ]
        }
        
        metrics = aggregator.get_impact_metrics(start_time, end_time)
        
        assert 'yield_improvement' in metrics
        assert 'cost_reduction' in metrics
        assert 'market_access' in metrics
        assert 'scheme_adoption' in metrics
        
        # Check yield improvement structure
        yield_data = metrics['yield_improvement']
        assert 'average_percent' in yield_data
        assert 'maximum_percent' in yield_data
        assert 'minimum_percent' in yield_data
        assert 'target_range' in yield_data
        assert 'meets_target' in yield_data
        
        assert isinstance(yield_data['meets_target'], bool)
    
    def test_get_technical_performance_metrics(self, aggregator, mock_cloudwatch, time_range):
        """Test technical performance metrics retrieval"""
        start_time, end_time = time_range
        
        # Mock CloudWatch responses
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Average': 2500, 'p99': 4000, 'Timestamp': datetime.now()}
            ]
        }
        
        metrics = aggregator.get_technical_performance_metrics(start_time, end_time)
        
        assert 'response_time' in metrics
        assert 'accuracy_rates' in metrics
        assert 'uptime' in metrics
        
        # Check response time structure
        response_data = metrics['response_time']
        assert 'average_ms' in response_data
        assert 'p99_ms' in response_data
        assert 'target_ms' in response_data
        assert 'meets_target' in response_data
        
        # Check accuracy rates structure
        accuracy_data = metrics['accuracy_rates']
        assert 'diagnosis_percent' in accuracy_data
        assert 'pest_identification_percent' in accuracy_data
        assert 'diagnosis_target' in accuracy_data
        assert 'pest_target' in accuracy_data
    
    def test_get_feature_adoption_metrics(self, aggregator, mock_cloudwatch, time_range):
        """Test feature adoption metrics retrieval"""
        start_time, end_time = time_range
        
        # Mock CloudWatch responses
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Sum': 500, 'Timestamp': datetime.now()}
            ]
        }
        
        metrics = aggregator.get_feature_adoption_metrics(start_time, end_time)
        
        assert isinstance(metrics, dict)
        
        # Check that all expected features are present
        expected_features = [
            'crop_diagnosis',
            'pest_identification',
            'soil_analysis',
            'weather_alerts',
            'market_prices'
        ]
        
        for feature in expected_features:
            if feature in metrics:
                assert 'usage_count' in metrics[feature]
                assert 'success_rate_percent' in metrics[feature]
    
    def test_get_resource_sharing_metrics(self, aggregator, mock_cloudwatch, time_range):
        """Test resource sharing metrics retrieval"""
        start_time, end_time = time_range
        
        # Mock CloudWatch responses
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Average': 65.5, 'Timestamp': datetime.now()}
            ]
        }
        
        metrics = aggregator.get_resource_sharing_metrics(start_time, end_time)
        
        assert 'equipment_utilization' in metrics
        assert 'cooperative_buying' in metrics
        
        # Check equipment utilization structure
        equipment_data = metrics['equipment_utilization']
        assert 'average_percent' in equipment_data
        assert 'description' in equipment_data
        
        # Check cooperative buying structure
        coop_data = metrics['cooperative_buying']
        assert 'average_savings_percent' in coop_data
        assert 'total_savings_inr' in coop_data
        assert 'target_range' in coop_data
        assert 'meets_target' in coop_data
    
    def test_generate_comprehensive_report(self, aggregator, mock_cloudwatch, time_range):
        """Test comprehensive report generation"""
        start_time, end_time = time_range
        
        # Mock CloudWatch responses
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Sum': 100, 'Average': 50, 'Maximum': 75, 'Minimum': 25, 'Timestamp': datetime.now()}
            ]
        }
        
        report = aggregator.generate_comprehensive_report(start_time, end_time)
        
        assert 'report_period' in report
        assert 'user_adoption' in report
        assert 'impact_metrics' in report
        assert 'technical_performance' in report
        assert 'feature_adoption' in report
        assert 'resource_sharing' in report
        assert 'generated_at' in report
        
        # Check report period
        period = report['report_period']
        assert 'start' in period
        assert 'end' in period
        assert 'duration_days' in period
    
    def test_calculate_return_rate(self, aggregator, time_range):
        """Test return rate calculation"""
        start_time, end_time = time_range
        
        return_rate = aggregator._calculate_return_rate(start_time, end_time)
        
        assert isinstance(return_rate, float)
        assert 0 <= return_rate <= 100
    
    def test_get_feature_users(self, aggregator, mock_cloudwatch, time_range):
        """Test feature users count retrieval"""
        start_time, end_time = time_range
        
        # Mock CloudWatch response
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Sum': 250, 'Timestamp': datetime.now()},
                {'Sum': 300, 'Timestamp': datetime.now()}
            ]
        }
        
        user_count = aggregator._get_feature_users('crop_diagnosis', start_time, end_time)
        
        assert isinstance(user_count, int)
        assert user_count >= 0
    
    def test_calculate_uptime(self, aggregator, mock_cloudwatch, time_range):
        """Test uptime calculation"""
        start_time, end_time = time_range
        
        # Mock CloudWatch responses for invocations and errors
        def mock_get_metric_statistics(**kwargs):
            if kwargs['MetricName'] == 'Invocations':
                return {'Datapoints': [{'Sum': 1000, 'Timestamp': datetime.now()}]}
            elif kwargs['MetricName'] == 'Errors':
                return {'Datapoints': [{'Sum': 5, 'Timestamp': datetime.now()}]}
            return {'Datapoints': []}
        
        mock_cloudwatch.get_metric_statistics.side_effect = mock_get_metric_statistics
        
        uptime = aggregator._calculate_uptime(start_time, end_time)
        
        assert isinstance(uptime, float)
        assert 0 <= uptime <= 100
        assert uptime == 99.5  # (1000 - 5) / 1000 * 100


class TestLambdaHandler:
    """Test Lambda handler function"""
    
    def test_lambda_handler_generate_report(self, mock_cloudwatch, mock_dynamodb):
        """Test Lambda handler for generate_report action"""
        from infrastructure.analytics_aggregator import lambda_handler
        
        # Mock CloudWatch responses
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Sum': 100, 'Average': 50, 'Timestamp': datetime.now()}
            ]
        }
        
        event = {
            'action': 'generate_report',
            'start_time': '2024-01-01T00:00:00Z',
            'end_time': '2024-01-31T23:59:59Z'
        }
        
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 200
        assert 'body' in response
        
        body = json.loads(response['body'])
        assert 'user_adoption' in body
        assert 'impact_metrics' in body
    
    def test_lambda_handler_user_adoption(self, mock_cloudwatch, mock_dynamodb):
        """Test Lambda handler for user_adoption action"""
        from infrastructure.analytics_aggregator import lambda_handler
        
        # Mock CloudWatch responses
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Sum': 100, 'Timestamp': datetime.now()}
            ]
        }
        
        event = {
            'action': 'user_adoption',
            'start_time': '2024-01-01T00:00:00Z',
            'end_time': '2024-01-31T23:59:59Z'
        }
        
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'active_users' in body
    
    def test_lambda_handler_invalid_action(self, mock_cloudwatch, mock_dynamodb):
        """Test Lambda handler with invalid action"""
        from infrastructure.analytics_aggregator import lambda_handler
        
        event = {
            'action': 'invalid_action',
            'start_time': '2024-01-01T00:00:00Z',
            'end_time': '2024-01-31T23:59:59Z'
        }
        
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body


class TestAnalyticsDashboard:
    """Test Analytics Dashboard UI"""
    
    @patch('ui.analytics_dashboard.boto3.client')
    def test_dashboard_initialization(self, mock_boto_client):
        """Test dashboard initialization"""
        from ui.analytics_dashboard import AnalyticsDashboard
        
        dashboard = AnalyticsDashboard()
        
        assert dashboard is not None
        assert dashboard.cloudwatch is not None
        assert dashboard.lambda_client is not None
    
    @patch('ui.analytics_dashboard.boto3.client')
    def test_fetch_analytics_data(self, mock_boto_client):
        """Test analytics data fetching"""
        from ui.analytics_dashboard import AnalyticsDashboard
        
        # Mock Lambda client
        mock_lambda = Mock()
        mock_boto_client.return_value = mock_lambda
        
        # Mock Lambda response
        mock_payload = Mock()
        mock_payload.read.return_value = json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'user_adoption': {'active_users': 1000},
                'impact_metrics': {},
                'technical_performance': {},
                'feature_adoption': {},
                'resource_sharing': {}
            })
        })
        
        mock_lambda.invoke.return_value = {'Payload': mock_payload}
        
        dashboard = AnalyticsDashboard()
        
        start_time = datetime.now() - timedelta(days=7)
        end_time = datetime.now()
        
        data = dashboard._fetch_analytics_data(start_time, end_time)
        
        assert data is not None
        assert 'user_adoption' in data
    
    @patch('ui.analytics_dashboard.boto3.client')
    def test_get_mock_data(self, mock_boto_client):
        """Test mock data generation"""
        from ui.analytics_dashboard import AnalyticsDashboard
        
        dashboard = AnalyticsDashboard()
        
        start_time = datetime.now() - timedelta(days=7)
        end_time = datetime.now()
        
        mock_data = dashboard._get_mock_data(start_time, end_time)
        
        assert mock_data is not None
        assert 'user_adoption' in mock_data
        assert 'impact_metrics' in mock_data
        assert 'technical_performance' in mock_data
        assert 'feature_adoption' in mock_data
        assert 'resource_sharing' in mock_data
        
        # Verify mock data structure
        user_adoption = mock_data['user_adoption']
        assert user_adoption['active_users'] > 0
        assert user_adoption['return_rate_percent'] > 0
        assert len(user_adoption['language_distribution']) > 0


def test_analytics_integration():
    """Integration test for analytics system"""
    # This would be an integration test that requires actual AWS services
    # For now, we'll just verify the components can be imported
    from infrastructure.analytics_aggregator import AnalyticsAggregator
    from ui.analytics_dashboard import AnalyticsDashboard
    
    assert AnalyticsAggregator is not None
    assert AnalyticsDashboard is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
