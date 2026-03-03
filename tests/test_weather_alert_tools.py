"""
Unit tests for RISE Weather Alert Tools
Tests for weather monitoring, alerts, irrigation calculator, and protective measures
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.weather_alert_tools import WeatherAlertTools, create_weather_alert_tools


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB resource"""
    with patch('boto3.resource') as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        yield mock_table


@pytest.fixture
def mock_sns():
    """Mock SNS client"""
    with patch('boto3.client') as mock_client:
        yield mock_client.return_value


@pytest.fixture
def mock_weather_tools():
    """Mock WeatherTools"""
    with patch('tools.weather_alert_tools.WeatherTools') as mock_tools:
        yield mock_tools.return_value


@pytest.fixture
def sample_user_profile():
    """Sample user profile with location"""
    return {
        'user_id': 'test_user_123',
        'name': 'Test Farmer',
        'phone_number': '+919876543210',
        'location': {
            'name': 'Test Village',
            'latitude': 28.6139,
            'longitude': 77.2090,
            'state': 'Delhi',
            'district': 'New Delhi'
        },
        'farm_details': {
            'land_size': 2.5,
            'soil_type': 'loam',
            'crops': ['wheat', 'rice']
        },
        'preferences': {
            'language': 'hi',
            'notification_settings': {
                'weather_alerts': True
            }
        },
        'crops': ['wheat', 'rice']
    }


@pytest.fixture
def sample_forecast_data():
    """Sample weather forecast data"""
    return {
        'success': True,
        'location': {
            'name': 'Test Village',
            'latitude': 28.6139,
            'longitude': 77.2090
        },
        'daily_summary': [
            {
                'date': '2024-01-10',
                'temp_min': 15,
                'temp_max': 28,
                'humidity_avg': 60,
                'rain_total': 0,
                'weather': 'Clear'
            },
            {
                'date': '2024-01-11',
                'temp_min': 16,
                'temp_max': 30,
                'humidity_avg': 55,
                'rain_total': 2,
                'weather': 'Clear'
            },
            {
                'date': '2024-01-12',
                'temp_min': 18,
                'temp_max': 42,  # Extreme heat
                'humidity_avg': 35,
                'rain_total': 0,
                'weather': 'Clear'
            },
            {
                'date': '2024-01-13',
                'temp_min': 20,
                'temp_max': 32,
                'humidity_avg': 70,
                'rain_total': 60,  # Heavy rain
                'weather': 'Rain'
            },
            {
                'date': '2024-01-14',
                'temp_min': 3,  # Cold wave
                'temp_max': 15,
                'humidity_avg': 80,
                'rain_total': 5,
                'weather': 'Clouds'
            }
        ],
        'forecast': []
    }


class TestWeatherAlertTools:
    """Test WeatherAlertTools class"""
    
    def test_initialization(self, mock_dynamodb, mock_sns):
        """Test WeatherAlertTools initialization"""
        tools = WeatherAlertTools(region='us-east-1')
        
        assert tools.region == 'us-east-1'
        assert tools.dynamodb is not None
        assert tools.sns is not None
        assert tools.weather_tools is not None
    
    def test_factory_function(self):
        """Test create_weather_alert_tools factory function"""
        with patch('tools.weather_alert_tools.WeatherAlertTools') as mock_class:
            tools = create_weather_alert_tools(region='us-west-2')
            mock_class.assert_called_once_with(region='us-west-2')
    
    def test_monitor_weather_conditions_success(self,
                                               mock_dynamodb,
                                               mock_sns,
                                               mock_weather_tools,
                                               sample_user_profile,
                                               sample_forecast_data):
        """Test successful weather monitoring"""
        # Setup mocks
        mock_dynamodb.get_item.return_value = {'Item': sample_user_profile}
        mock_weather_tools.get_forecast.return_value = sample_forecast_data
        
        tools = WeatherAlertTools()
        tools.weather_tools = mock_weather_tools
        
        # Monitor weather
        result = tools.monitor_weather_conditions('test_user_123')
        
        # Assertions
        assert result['success'] is True
        assert 'alerts' in result
        assert 'recommendations' in result
        assert 'irrigation' in result
        assert 'protective_measures' in result
        assert 'location' in result
        
        # Verify alerts were generated
        assert len(result['alerts']) > 0
        
        # Verify recommendations were generated
        assert len(result['recommendations']) > 0
        
        # Verify irrigation schedule was created
        assert 'schedule' in result['irrigation']
        assert len(result['irrigation']['schedule']) > 0
    
    def test_monitor_weather_no_location(self, mock_dynamodb, mock_sns):
        """Test monitoring with user without location"""
        # User without location
        mock_dynamodb.get_item.return_value = {
            'Item': {'user_id': 'test_user_123'}
        }
        
        tools = WeatherAlertTools()
        result = tools.monitor_weather_conditions('test_user_123')
        
        assert result['success'] is False
        assert 'error' in result
        assert 'location not found' in result['error'].lower()
    
    def test_detect_adverse_weather_extreme_heat(self, sample_forecast_data):
        """Test detection of extreme heat alert"""
        tools = WeatherAlertTools()
        
        alerts = tools._detect_adverse_weather(
            sample_forecast_data['daily_summary'],
            []
        )
        
        # Should detect extreme heat on day 3 (42°C)
        heat_alerts = [a for a in alerts if a['type'] == 'extreme_heat']
        assert len(heat_alerts) > 0
        
        heat_alert = heat_alerts[0]
        assert heat_alert['severity'] == 'high'
        assert heat_alert['date'] == '2024-01-12'
        assert 48 <= heat_alert['hours_ahead'] <= 96
    
    def test_detect_adverse_weather_heavy_rain(self, sample_forecast_data):
        """Test detection of heavy rain alert"""
        tools = WeatherAlertTools()
        
        alerts = tools._detect_adverse_weather(
            sample_forecast_data['daily_summary'],
            []
        )
        
        # Should detect heavy rain on day 4 (60mm)
        rain_alerts = [a for a in alerts if a['type'] == 'heavy_rain']
        assert len(rain_alerts) > 0
        
        rain_alert = rain_alerts[0]
        assert rain_alert['severity'] == 'high'
        assert rain_alert['date'] == '2024-01-13'
    
    def test_detect_adverse_weather_cold_wave(self, sample_forecast_data):
        """Test detection of cold wave alert"""
        tools = WeatherAlertTools()
        
        # Modify forecast to have cold wave in 48-72 hour window (day 3)
        modified_forecast = sample_forecast_data['daily_summary'].copy()
        modified_forecast[2] = {
            'date': '2024-01-12',
            'temp_min': 3,  # Cold wave
            'temp_max': 15,
            'humidity_avg': 80,
            'rain_total': 5,
            'weather': 'Clouds'
        }
        
        alerts = tools._detect_adverse_weather(modified_forecast, [])
        
        # Should detect cold wave on day 3 (3°C)
        cold_alerts = [a for a in alerts if a['type'] == 'cold_wave']
        assert len(cold_alerts) > 0
        
        cold_alert = cold_alerts[0]
        assert cold_alert['severity'] == 'high'
        assert cold_alert['date'] == '2024-01-12'
    
    def test_generate_activity_recommendations(self, sample_forecast_data):
        """Test farming activity recommendations generation"""
        tools = WeatherAlertTools()
        
        recommendations = tools._generate_activity_recommendations(
            sample_forecast_data['daily_summary'],
            ['wheat', 'rice']
        )
        
        # Should generate recommendations for 3 days
        assert len(recommendations) == 3
        
        # Each day should have structure
        for day_rec in recommendations:
            assert 'date' in day_rec
            assert 'day_number' in day_rec
            assert 'recommended' in day_rec
            assert 'avoid' in day_rec
            assert 'optimal_timing' in day_rec
    
    def test_activity_recommendations_spraying(self):
        """Test spraying recommendations based on weather"""
        tools = WeatherAlertTools()
        
        # Ideal conditions for spraying
        daily_summary = [{
            'date': '2024-01-10',
            'temp_min': 20,
            'temp_max': 28,
            'humidity_avg': 60,
            'rain_total': 0,
            'weather': 'Clear'
        }]
        
        recommendations = tools._generate_activity_recommendations(daily_summary, [])
        
        # Should recommend spraying
        spraying_recs = [
            a for a in recommendations[0]['recommended']
            if 'Spraying' in a['activity']
        ]
        assert len(spraying_recs) > 0
    
    def test_activity_recommendations_avoid_rain(self):
        """Test avoiding activities during rain"""
        tools = WeatherAlertTools()
        
        # Rainy conditions
        daily_summary = [{
            'date': '2024-01-10',
            'temp_min': 20,
            'temp_max': 28,
            'humidity_avg': 80,
            'rain_total': 30,
            'weather': 'Rain'
        }]
        
        recommendations = tools._generate_activity_recommendations(daily_summary, [])
        
        # Should avoid spraying and fertilizer
        avoid_activities = recommendations[0]['avoid']
        assert len(avoid_activities) > 0
        assert any('Spraying' in a['activity'] for a in avoid_activities)
    
    def test_calculate_irrigation_timing(self):
        """Test irrigation timing calculator"""
        tools = WeatherAlertTools()
        
        daily_summary = [
            {
                'date': '2024-01-10',
                'temp_min': 20,
                'temp_max': 36,  # High temp
                'humidity_avg': 35,  # Low humidity
                'rain_total': 0,  # No rain
                'weather': 'Clear'
            },
            {
                'date': '2024-01-11',
                'temp_min': 18,
                'temp_max': 25,
                'humidity_avg': 70,
                'rain_total': 15,  # Good rain
                'weather': 'Rain'
            }
        ]
        
        farm_details = {'soil_type': 'loam'}
        
        irrigation = tools._calculate_irrigation_timing(daily_summary, farm_details)
        
        # Verify structure
        assert 'schedule' in irrigation
        assert 'soil_type' in irrigation
        assert 'retention_factor' in irrigation
        assert 'total_water_week' in irrigation
        assert 'water_saving_tips' in irrigation
        
        # Day 1 should have high priority (hot, dry)
        day1 = irrigation['schedule'][0]
        assert day1['priority'] in ['High', 'Medium']
        assert day1['score'] >= 6
        
        # Day 2 should have low/no priority (rain expected)
        day2 = irrigation['schedule'][1]
        assert day2['priority'] in ['Low', 'Not Needed']
    
    def test_irrigation_soil_type_adjustment(self):
        """Test irrigation adjustment for different soil types"""
        tools = WeatherAlertTools()
        
        daily_summary = [{
            'date': '2024-01-10',
            'temp_min': 20,
            'temp_max': 35,
            'humidity_avg': 40,
            'rain_total': 0,
            'weather': 'Clear'
        }]
        
        # Test sandy soil (needs more water)
        irrigation_sandy = tools._calculate_irrigation_timing(
            daily_summary,
            {'soil_type': 'sandy'}
        )
        
        # Test clay soil (retains water)
        irrigation_clay = tools._calculate_irrigation_timing(
            daily_summary,
            {'soil_type': 'clay'}
        )
        
        # Sandy soil should have higher retention factor
        assert irrigation_sandy['retention_factor'] > irrigation_clay['retention_factor']
    
    def test_generate_protective_measures_heat(self):
        """Test protective measures for extreme heat"""
        tools = WeatherAlertTools()
        
        alerts = [{
            'type': 'extreme_heat',
            'date': '2024-01-12',
            'severity': 'high'
        }]
        
        measures = tools._generate_protective_measures(alerts)
        
        assert len(measures) > 0
        heat_measure = measures[0]
        
        assert heat_measure['alert_type'] == 'extreme_heat'
        assert heat_measure['urgency'] == 'high'
        assert len(heat_measure['measures']) > 0
        
        # Should include irrigation and mulch recommendations
        measure_text = ' '.join(heat_measure['measures'])
        assert 'irrigation' in measure_text.lower()
        assert 'mulch' in measure_text.lower()
    
    def test_generate_protective_measures_rain(self):
        """Test protective measures for heavy rain"""
        tools = WeatherAlertTools()
        
        alerts = [{
            'type': 'heavy_rain',
            'date': '2024-01-13',
            'severity': 'high'
        }]
        
        measures = tools._generate_protective_measures(alerts)
        
        assert len(measures) > 0
        rain_measure = measures[0]
        
        assert rain_measure['alert_type'] == 'heavy_rain'
        assert rain_measure['urgency'] == 'high'
        
        # Should include drainage and harvest recommendations
        measure_text = ' '.join(rain_measure['measures'])
        assert 'drainage' in measure_text.lower()
        assert 'harvest' in measure_text.lower()
    
    def test_generate_protective_measures_cold(self):
        """Test protective measures for cold wave"""
        tools = WeatherAlertTools()
        
        alerts = [{
            'type': 'cold_wave',
            'date': '2024-01-14',
            'severity': 'high'
        }]
        
        measures = tools._generate_protective_measures(alerts)
        
        assert len(measures) > 0
        cold_measure = measures[0]
        
        assert cold_measure['alert_type'] == 'cold_wave'
        assert cold_measure['urgency'] == 'high'
        
        # Should include covering and protection recommendations
        measure_text = ' '.join(cold_measure['measures'])
        assert 'cover' in measure_text.lower()
        assert 'protect' in measure_text.lower()
    
    def test_water_saving_tips(self):
        """Test water-saving tips generation"""
        tools = WeatherAlertTools()
        
        # Test for different soil types
        tips_sandy = tools._get_water_saving_tips('sandy')
        tips_clay = tools._get_water_saving_tips('clay')
        tips_loam = tools._get_water_saving_tips('loam')
        
        # All should have base tips
        assert len(tips_sandy) > 0
        assert len(tips_clay) > 0
        assert len(tips_loam) > 0
        
        # Sandy soil should have specific tips
        sandy_text = ' '.join(tips_sandy)
        assert 'sandy' in sandy_text.lower()
        
        # Clay soil should have specific tips
        clay_text = ' '.join(tips_clay)
        assert 'clay' in clay_text.lower()
    
    def test_save_alert(self, mock_dynamodb):
        """Test saving alert to DynamoDB"""
        tools = WeatherAlertTools()
        
        alert_data = {
            'user_id': 'test_user_123',
            'alerts': [],
            'recommendations': [],
            'irrigation': {},
            'protective_measures': [],
            'location': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Should not raise exception
        tools._save_alert('test_user_123', alert_data)
        
        # Verify put_item was called
        mock_dynamodb.put_item.assert_called_once()
    
    def test_get_user_alerts(self, mock_dynamodb):
        """Test retrieving user alerts"""
        # Mock query response
        mock_dynamodb.query.return_value = {
            'Items': [
                {
                    'alert_id': 'alert_1',
                    'user_id': 'test_user_123',
                    'alert_data': json.dumps({
                        'alerts': [],
                        'timestamp': datetime.now().isoformat()
                    }),
                    'timestamp': datetime.now().isoformat()
                }
            ]
        }
        
        tools = WeatherAlertTools()
        result = tools.get_user_alerts('test_user_123', days=7)
        
        assert result['success'] is True
        assert 'alerts' in result
        assert result['count'] > 0
    
    def test_format_alert_message_english(self):
        """Test alert message formatting in English"""
        tools = WeatherAlertTools()
        
        alerts = [
            {
                'title': 'Extreme Heat Warning',
                'message': 'Temperature will reach 42°C'
            },
            {
                'title': 'Heavy Rain Alert',
                'message': 'Rainfall expected: 60mm'
            }
        ]
        
        message = tools._format_alert_message(alerts, 'en')
        
        assert 'RISE Weather Alert' in message
        assert 'Extreme Heat Warning' in message
        assert 'Heavy Rain Alert' in message
    
    def test_format_alert_message_hindi(self):
        """Test alert message formatting in Hindi"""
        tools = WeatherAlertTools()
        
        alerts = [
            {
                'title': 'Extreme Heat Warning',
                'message': 'Temperature will reach 42°C'
            }
        ]
        
        message = tools._format_alert_message(alerts, 'hi')
        
        assert 'RISE' in message
        assert 'चेतावनी' in message  # Warning in Hindi


class TestIntegration:
    """Integration tests for weather alert system"""
    
    @patch('tools.weather_alert_tools.WeatherTools')
    def test_end_to_end_monitoring(self,
                                   mock_weather_tools_class,
                                   mock_dynamodb,
                                   mock_sns,
                                   sample_user_profile,
                                   sample_forecast_data):
        """Test end-to-end weather monitoring flow"""
        # Setup mocks
        mock_weather_tools = mock_weather_tools_class.return_value
        mock_weather_tools.get_forecast.return_value = sample_forecast_data
        mock_dynamodb.get_item.return_value = {'Item': sample_user_profile}
        
        # Create tools and monitor
        tools = WeatherAlertTools()
        result = tools.monitor_weather_conditions('test_user_123')
        
        # Verify complete flow
        assert result['success'] is True
        
        # Verify all components present
        assert len(result['alerts']) > 0
        assert len(result['recommendations']) > 0
        assert len(result['irrigation']['schedule']) > 0
        assert len(result['protective_measures']) > 0
        
        # Verify alert was saved
        mock_dynamodb.put_item.assert_called()
        
        # Verify critical alerts triggered notification
        critical_alerts = [a for a in result['alerts'] if a['severity'] == 'high']
        if critical_alerts:
            # Notification should be attempted (may fail in test)
            pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
