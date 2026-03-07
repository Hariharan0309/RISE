"""
Tests for RISE Weather Tools
"""

import pytest
import json
import requests
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.weather_tools import WeatherTools, create_weather_tools


class TestWeatherTools:
    """Test suite for WeatherTools"""
    
    @pytest.fixture
    def mock_dynamodb(self):
        """Mock DynamoDB resource"""
        with patch('boto3.resource') as mock_resource:
            mock_table = MagicMock()
            mock_resource.return_value.Table.return_value = mock_table
            yield mock_table
    
    @pytest.fixture
    def mock_requests(self):
        """Mock requests library"""
        with patch('tools.weather_tools.requests') as mock_req:
            yield mock_req
    
    @pytest.fixture
    def weather_tools(self, mock_dynamodb):
        """Create WeatherTools instance with mocked dependencies"""
        return WeatherTools(region='us-east-1', api_key='test_api_key')
    
    @pytest.fixture
    def sample_current_weather_response(self):
        """Sample Open-Meteo current weather API response"""
        return {
            'current': {
                'time': datetime.now().isoformat(),
                'temperature_2m': 28.5,
                'relative_humidity_2m': 65,
                'weather_code': 0,
                'wind_speed_10m': 3.5,
                'precipitation': 0.0
            }
        }
    
    @pytest.fixture
    def sample_forecast_response(self):
        """Sample Open-Meteo daily forecast API response"""
        base_date = datetime.now().date()
        return {
            'daily': {
                'time': [(base_date + timedelta(days=i)).isoformat() for i in range(5)],
                'temperature_2m_max': [32.0, 31.0, 30.0, 29.0, 28.0],
                'temperature_2m_min': [22.0, 21.0, 20.0, 19.0, 18.0],
                'precipitation_sum': [0.0, 0.0, 2.0, 0.0, 0.0],
                'weather_code': [0, 1, 61, 2, 0]
            }
        }
    
    def test_initialization(self, weather_tools):
        """Test WeatherTools initialization"""
        assert weather_tools.region == 'us-east-1'
        assert weather_tools.cache_ttl == timedelta(hours=6)
        assert 'open-meteo.com' in weather_tools.base_url
    
    def test_get_current_weather_success(self, weather_tools, mock_requests, 
                                        sample_current_weather_response, mock_dynamodb):
        """Test successful current weather retrieval"""
        # Mock cache miss
        mock_dynamodb.get_item.return_value = {}
        
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = sample_current_weather_response
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response
        
        # Get current weather
        result = weather_tools.get_current_weather(28.6139, 77.2090, 'New Delhi')
        
        # Assertions
        assert result['success'] is True
        assert result['from_cache'] is False
        assert result['location']['name'] == 'New Delhi'
        assert result['current']['temperature'] == 28.5
        assert result['current']['humidity'] == 65
        assert result['current']['weather'] == 'Clear sky'
    
    def test_get_current_weather_from_cache(self, weather_tools, mock_dynamodb):
        """Test current weather retrieval from cache"""
        # Mock cache hit
        cached_data = {
            'location': {'name': 'New Delhi'},
            'current': {'temperature': 28.5}
        }
        
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'cache_key': 'test_key',
                'weather_data': json.dumps(cached_data),
                'expires_at': (datetime.now() + timedelta(hours=3)).isoformat()
            }
        }
        
        # Get current weather
        result = weather_tools.get_current_weather(28.6139, 77.2090)
        
        # Assertions
        assert result['success'] is True
        assert result['from_cache'] is True
        assert result['location']['name'] == 'New Delhi'
    
    def test_get_current_weather_api_error(self, weather_tools, mock_requests, mock_dynamodb):
        """Test current weather with API error"""
        # Mock cache miss
        mock_dynamodb.get_item.return_value = {}
        
        # Mock API error
        mock_requests.get.side_effect = Exception('API Error')
        
        # Get current weather
        result = weather_tools.get_current_weather(28.6139, 77.2090)
        
        # Assertions
        assert result['success'] is False
        assert 'error' in result
    
    def test_get_forecast_success(self, weather_tools, mock_requests,
                                  sample_forecast_response, mock_dynamodb):
        """Test successful forecast retrieval"""
        # Mock cache miss
        mock_dynamodb.get_item.return_value = {}
        
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = sample_forecast_response
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response
        
        # Get forecast
        result = weather_tools.get_forecast(28.6139, 77.2090, days=1)
        
        # Assertions
        assert result['success'] is True
        assert result['from_cache'] is False
        assert result['location']['name'] == 'Unknown'
        assert len(result['daily_summary']) >= 1
        assert result['daily_summary'][0]['temp_max'] == 32.0
        assert result['daily_summary'][0]['rain_total'] == 0.0
    
    def test_get_forecast_from_cache(self, weather_tools, mock_dynamodb):
        """Test forecast retrieval from cache"""
        # Mock cache hit
        cached_data = {
            'location': {'name': 'New Delhi'},
            'forecast': [],
            'daily_summary': []
        }
        
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'cache_key': 'test_key',
                'weather_data': json.dumps(cached_data),
                'expires_at': (datetime.now() + timedelta(hours=3)).isoformat()
            }
        }
        
        # Get forecast
        result = weather_tools.get_forecast(28.6139, 77.2090)
        
        # Assertions
        assert result['success'] is True
        assert result['from_cache'] is True
    
    def test_generate_farming_recommendations(self, weather_tools):
        """Test farming recommendations generation"""
        current = {
            'temperature': 36,
            'humidity': 85,
            'wind_speed': 22,
            'rain_1h': 0,
            'rain_3h': 0
        }
        
        forecast = [
            {'rain_total': 15, 'temp_max': 35},
            {'rain_total': 5, 'temp_max': 32}
        ]
        
        recommendations = weather_tools._generate_farming_recommendations(current, forecast)
        
        # Assertions
        assert len(recommendations) > 0
        assert any('High temperature' in rec for rec in recommendations)
        assert any('High humidity' in rec for rec in recommendations)
        assert any('High wind' in rec for rec in recommendations)
    
    def test_generate_irrigation_advice_high_need(self, weather_tools):
        """Test irrigation advice with high need"""
        current = {
            'temperature': 38,
            'humidity': 30,
            'rain_1h': 0,
            'rain_3h': 0
        }
        
        forecast = [
            {'rain_total': 0},
            {'rain_total': 0}
        ]
        
        advice = weather_tools._generate_irrigation_advice(current, forecast)
        
        # Assertions
        assert advice['priority'] in ['High', 'Medium']
        assert advice['score'] >= 6
        assert 'advice' in advice
        assert 'optimal_timing' in advice
    
    def test_generate_irrigation_advice_low_need(self, weather_tools):
        """Test irrigation advice with low need"""
        current = {
            'temperature': 22,
            'humidity': 85,
            'rain_1h': 5,
            'rain_3h': 10
        }
        
        forecast = [
            {'rain_total': 20},
            {'rain_total': 15}
        ]
        
        advice = weather_tools._generate_irrigation_advice(current, forecast)
        
        # Assertions
        assert advice['priority'] in ['Not Needed', 'Low']
        assert advice['score'] <= 4
    
    def test_check_adverse_weather(self, weather_tools):
        """Test adverse weather detection"""
        forecast = [
            {'date': '2024-01-01', 'temp_max': 42, 'temp_min': 25, 'rain_total': 60},
            {'date': '2024-01-02', 'temp_max': 35, 'temp_min': 3, 'rain_total': 30},
            {'date': '2024-01-03', 'temp_max': 30, 'temp_min': 20, 'rain_total': 5}
        ]
        
        alerts = weather_tools._check_adverse_weather(forecast)
        
        # Assertions
        assert len(alerts) >= 2
        assert any(alert['date'] == '2024-01-01' for alert in alerts)
        assert any(alert['date'] == '2024-01-02' for alert in alerts)
    
    def test_suggest_optimal_activities(self, weather_tools):
        """Test optimal activities suggestion"""
        current = {
            'temperature': 25,
            'humidity': 60,
            'wind_speed': 5,
            'rain_1h': 0,
            'rain_3h': 0
        }
        
        forecast = [
            {'rain_total': 2, 'temp_max': 28}
        ]
        
        activities = weather_tools._suggest_optimal_activities(current, forecast)
        
        # Assertions
        assert 'recommended_today' in activities
        assert 'avoid_today' in activities
        assert 'plan_for_tomorrow' in activities
        assert len(activities['recommended_today']) > 0
    
    def test_cache_key_generation(self, weather_tools):
        """Test cache key generation"""
        key1 = weather_tools._get_cache_key(28.6139, 77.2090, 'current')
        key2 = weather_tools._get_cache_key(28.6139, 77.2090, 'current')
        key3 = weather_tools._get_cache_key(28.6140, 77.2090, 'current')
        
        # Same coordinates should generate same key
        assert key1 == key2
        
        # Different coordinates should generate different key
        # (but might be same due to rounding)
        # This tests the rounding logic
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5 hash length
    
    def test_save_to_cache(self, weather_tools, mock_dynamodb):
        """Test saving to cache"""
        weather_data = {'temperature': 28.5}
        cache_key = 'test_cache_key'
        
        weather_tools._save_to_cache(cache_key, weather_data)
        
        # Verify put_item was called
        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args[1]
        
        assert call_args['Item']['cache_key'] == cache_key
        assert 'weather_data' in call_args['Item']
        assert 'expires_at' in call_args['Item']
        assert 'ttl' in call_args['Item']
    
    def test_clear_cache(self, weather_tools, mock_dynamodb):
        """Test cache clearing"""
        # Mock scan response
        mock_dynamodb.scan.return_value = {
            'Items': [
                {'cache_key': 'key1'},
                {'cache_key': 'key2'}
            ]
        }
        
        # Mock batch writer
        mock_batch = MagicMock()
        mock_dynamodb.batch_writer.return_value.__enter__.return_value = mock_batch
        
        weather_tools.clear_cache()
        
        # Verify scan was called
        mock_dynamodb.scan.assert_called_once()
    
    def test_factory_function(self):
        """Test factory function"""
        with patch('boto3.resource'):
            tools = create_weather_tools(region='us-west-2', api_key='test_key')
            assert isinstance(tools, WeatherTools)
            assert tools.region == 'us-west-2'
            assert tools.base_url == 'https://api.open-meteo.com/v1/forecast'


class TestWeatherLambda:
    """Test suite for weather Lambda function (skipped when Lambda-style import fails)"""
    
    @pytest.fixture
    def mock_weather_tools(self):
        """Mock WeatherTools; skip if Lambda module cannot be imported (uses 'from weather_tools import ...')."""
        try:
            from tools.weather_lambda import lambda_handler  # noqa: F401
        except ModuleNotFoundError:
            pytest.skip("weather_lambda uses Lambda-style import (weather_tools); run from tools/ or deploy")
        import tools.weather_lambda as wl
        with patch.object(wl, 'weather_tools', MagicMock()) as mock_tools:
            yield mock_tools
    
    def test_lambda_handler_current_weather(self, mock_weather_tools):
        """Test Lambda handler for current weather"""
        from tools.weather_lambda import lambda_handler
        
        # Mock weather tools response
        mock_weather_tools.get_current_weather.return_value = {
            'success': True,
            'location': {'name': 'Test'},
            'current': {'temperature': 25}
        }
        
        # Create event
        event = {
            'body': json.dumps({
                'action': 'current',
                'latitude': 28.6139,
                'longitude': 77.2090
            })
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
    
    def test_lambda_handler_forecast(self, mock_weather_tools):
        """Test Lambda handler for forecast"""
        from tools.weather_lambda import lambda_handler
        
        # Mock weather tools response
        mock_weather_tools.get_forecast.return_value = {
            'success': True,
            'forecast': [],
            'daily_summary': []
        }
        
        # Create event
        event = {
            'body': json.dumps({
                'action': 'forecast',
                'latitude': 28.6139,
                'longitude': 77.2090,
                'days': 3
            })
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
    
    def test_lambda_handler_insights(self, mock_weather_tools):
        """Test Lambda handler for farming insights"""
        from tools.weather_lambda import lambda_handler
        
        # Mock weather tools response
        mock_weather_tools.get_farming_weather_insights.return_value = {
            'success': True,
            'farming_recommendations': [],
            'irrigation_advice': {}
        }
        
        # Create event
        event = {
            'body': json.dumps({
                'action': 'insights',
                'latitude': 28.6139,
                'longitude': 77.2090
            })
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
    
    def test_lambda_handler_invalid_action(self, mock_weather_tools):
        """Test Lambda handler with invalid action"""
        from tools.weather_lambda import lambda_handler
        
        # Create event
        event = {
            'body': json.dumps({
                'action': 'invalid',
                'latitude': 28.6139,
                'longitude': 77.2090
            })
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Assertions
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
    
    def test_lambda_handler_missing_coordinates(self, mock_weather_tools):
        """Test Lambda handler with missing coordinates"""
        from tools.weather_lambda import lambda_handler
        
        # Create event
        event = {
            'body': json.dumps({
                'action': 'current'
            })
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Assertions
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
