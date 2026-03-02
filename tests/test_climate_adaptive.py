"""
Tests for RISE Climate-Adaptive Recommendations Tools
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.climate_adaptive_tools import ClimateAdaptiveTools, create_climate_adaptive_tools


class TestClimateAdaptiveTools:
    """Test suite for ClimateAdaptiveTools"""
    
    @pytest.fixture
    def mock_dynamodb(self):
        """Mock DynamoDB resource"""
        with patch('boto3.resource') as mock_resource:
            mock_table = MagicMock()
            mock_resource.return_value.Table.return_value = mock_table
            yield mock_table
    
    @pytest.fixture
    def mock_bedrock(self):
        """Mock Bedrock client"""
        with patch('boto3.client') as mock_client:
            mock_bedrock = MagicMock()
            mock_client.return_value = mock_bedrock
            yield mock_bedrock
    
    @pytest.fixture
    def climate_tools(self, mock_dynamodb, mock_bedrock):
        """Create ClimateAdaptiveTools instance with mocked dependencies"""
        return ClimateAdaptiveTools(region='us-east-1')
    
    @pytest.fixture
    def sample_location(self):
        """Sample location data"""
        return {
            'name': 'Pune, Maharashtra',
            'latitude': 18.5204,
            'longitude': 73.8567
        }
    
    @pytest.fixture
    def sample_historical_weather(self):
        """Sample historical weather data"""
        return [
            {'date': '2024-01-01', 'temp_avg': 28, 'temp_max': 35, 'temp_min': 22, 'rainfall': 0},
            {'date': '2024-01-02', 'temp_avg': 29, 'temp_max': 36, 'temp_min': 23, 'rainfall': 0},
            {'date': '2024-01-03', 'temp_avg': 30, 'temp_max': 37, 'temp_min': 24, 'rainfall': 2},
            {'date': '2024-01-04', 'temp_avg': 31, 'temp_max': 38, 'temp_min': 25, 'rainfall': 0},
            {'date': '2024-01-05', 'temp_avg': 32, 'temp_max': 39, 'temp_min': 26, 'rainfall': 0},
            {'date': '2024-01-06', 'temp_avg': 33, 'temp_max': 40, 'temp_min': 27, 'rainfall': 0},
            {'date': '2024-01-07', 'temp_avg': 34, 'temp_max': 41, 'temp_min': 28, 'rainfall': 1}
        ]
    
    def test_initialization(self, climate_tools):
        """Test ClimateAdaptiveTools initialization"""
        assert climate_tools.region == 'us-east-1'
        assert climate_tools.model_id == 'anthropic.claude-3-sonnet-20240229-v1:0'
    
    def test_calculate_climate_trends(self, climate_tools, sample_historical_weather):
        """Test climate trend calculation"""
        trends = climate_tools._calculate_climate_trends(sample_historical_weather)
        
        # Assertions
        assert 'temperature' in trends
        assert 'rainfall' in trends
        assert 'extreme_events' in trends
        assert trends['temperature']['average'] > 0
        assert trends['rainfall']['total'] >= 0
        assert trends['data_points'] == len(sample_historical_weather)
    
    def test_calculate_climate_trends_empty_data(self, climate_tools):
        """Test climate trend calculation with empty data"""
        trends = climate_tools._calculate_climate_trends([])
        
        # Assertions
        assert trends['temperature_trend'] == 'stable'
        assert trends['rainfall_trend'] == 'stable'
        assert trends['extreme_events'] == []
    
    def test_identify_climate_risks_heat_stress(self, climate_tools):
        """Test climate risk identification for heat stress"""
        trends = {
            'temperature': {'average': 36, 'max': 42, 'min': 28, 'trend': 'increasing'},
            'rainfall': {'total': 50, 'average': 2, 'trend': 'stable'},
            'extreme_events': []
        }
        
        risks = climate_tools._identify_climate_risks(trends, 'Kharif')
        
        # Assertions
        assert len(risks) > 0
        assert any(r['type'] == 'heat_stress' for r in risks)
        assert any(r['type'] == 'extreme_heat' for r in risks)
    
    def test_identify_climate_risks_drought(self, climate_tools):
        """Test climate risk identification for drought"""
        trends = {
            'temperature': {'average': 30, 'max': 35, 'min': 25, 'trend': 'stable'},
            'rainfall': {'total': 10, 'average': 0.5, 'trend': 'decreasing'},
            'extreme_events': []
        }
        
        risks = climate_tools._identify_climate_risks(trends, 'Rabi')
        
        # Assertions
        assert len(risks) > 0
        assert any(r['type'] == 'drought' for r in risks)
    
    def test_identify_climate_risks_variability(self, climate_tools):
        """Test climate risk identification for high variability"""
        extreme_events = [
            {'type': 'extreme_heat', 'date': '2024-01-01', 'value': 42},
            {'type': 'heavy_rainfall', 'date': '2024-01-02', 'value': 60},
            {'type': 'extreme_heat', 'date': '2024-01-03', 'value': 43},
            {'type': 'heavy_rainfall', 'date': '2024-01-04', 'value': 55},
            {'type': 'extreme_heat', 'date': '2024-01-05', 'value': 41},
            {'type': 'heavy_rainfall', 'date': '2024-01-06', 'value': 58}
        ]
        
        trends = {
            'temperature': {'average': 32, 'max': 43, 'min': 25, 'trend': 'stable'},
            'rainfall': {'total': 200, 'average': 10, 'trend': 'stable'},
            'extreme_events': extreme_events
        }
        
        risks = climate_tools._identify_climate_risks(trends, 'Kharif')
        
        # Assertions
        assert any(r['type'] == 'climate_variability' for r in risks)
    
    def test_get_water_saving_techniques_high_scarcity(self, climate_tools):
        """Test water-saving technique recommendations for high scarcity"""
        techniques = climate_tools._get_water_saving_techniques('high', 'wheat')
        
        # Assertions
        assert len(techniques) > 0
        assert any(t['name'] == 'Drip Irrigation' for t in techniques)
        assert any(t['name'] == 'Rainwater Harvesting' for t in techniques)
        assert any(t['name'] == 'Mulching' for t in techniques)
    
    def test_get_water_saving_techniques_low_scarcity(self, climate_tools):
        """Test water-saving technique recommendations for low scarcity"""
        techniques = climate_tools._get_water_saving_techniques('low', 'rice')
        
        # Assertions
        assert len(techniques) > 0
        # Should still include basic techniques
        assert any(t['name'] == 'Mulching' for t in techniques)
    
    def test_calculate_cost_benefit(self, climate_tools):
        """Test cost-benefit analysis calculation"""
        techniques = [
            {
                'name': 'Drip Irrigation',
                'initial_cost': 'Medium (₹25,000-50,000 per acre)',
                'water_savings': '30-50%'
            },
            {
                'name': 'Mulching',
                'initial_cost': 'Low (₹2,000-5,000 per acre)',
                'water_savings': '20-30%'
            }
        ]
        
        cost_benefit = climate_tools._calculate_cost_benefit(techniques)
        
        # Assertions
        assert 'total_initial_investment' in cost_benefit
        assert 'average_water_savings' in cost_benefit
        assert 'estimated_annual_savings' in cost_benefit
        assert 'payback_period_years' in cost_benefit
        assert 'roi_5_years' in cost_benefit
    
    def test_extract_key_points(self, climate_tools):
        """Test key point extraction from text"""
        text = """
        Here are the recommendations:
        1. Plant drought-resistant varieties
        2. Implement drip irrigation
        3. Use mulching to conserve moisture
        - Monitor soil moisture regularly
        - Apply fertilizers based on soil tests
        """
        
        key_points = climate_tools._extract_key_points(text)
        
        # Assertions
        assert len(key_points) > 0
        assert any('drought-resistant' in point.lower() for point in key_points)
    
    def test_extract_priority_actions(self, climate_tools):
        """Test priority action extraction from text"""
        text = """
        Farmers should implement drip irrigation immediately.
        It is important to monitor soil moisture levels.
        You must apply fertilizers based on soil tests.
        Regular weeding ensures better crop growth.
        """
        
        priority_actions = climate_tools._extract_priority_actions(text)
        
        # Assertions
        assert len(priority_actions) > 0
        assert any('should' in action.lower() or 'important' in action.lower() 
                  or 'must' in action.lower() for action in priority_actions)
    
    def test_analyze_climate_data_success(self, climate_tools, mock_bedrock, mock_dynamodb,
                                         sample_location, sample_historical_weather):
        """Test successful climate data analysis"""
        # Mock Bedrock response
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{
                'text': 'Climate analysis shows increasing temperatures and drought risk.'
            }]
        }).encode()
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Analyze climate data
        result = climate_tools.analyze_climate_data(
            sample_location, sample_historical_weather, 'Kharif'
        )
        
        # Assertions
        assert result['success'] is True
        assert 'analysis_id' in result
        assert 'trends' in result
        assert 'risks' in result
        assert 'ai_insights' in result
        assert result['season'] == 'Kharif'
    
    def test_get_resilient_crop_varieties_success(self, climate_tools, mock_bedrock,
                                                  sample_location):
        """Test resilient crop variety recommendations"""
        # Mock Bedrock response
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{
                'text': json.dumps([
                    {
                        'crop_name': 'Pearl Millet',
                        'variety': 'HHB 67',
                        'resilience_features': ['Drought tolerant', 'Heat resistant'],
                        'expected_yield': '2-3 tons/hectare',
                        'market_demand': 'High',
                        'confidence_score': 85
                    }
                ])
            }]
        }).encode()
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Get crop varieties
        result = climate_tools.get_resilient_crop_varieties(
            sample_location, ['drought', 'heat_stress'], 'Sandy loam'
        )
        
        # Assertions
        assert result['success'] is True
        assert 'recommended_varieties' in result
        assert 'confidence_score' in result
    
    def test_get_water_efficient_techniques_success(self, climate_tools, mock_bedrock,
                                                   sample_location):
        """Test water-efficient technique recommendations"""
        # Mock Bedrock response
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{
                'text': 'Step 1: Install drip irrigation system. Step 2: Apply mulch...'
            }]
        }).encode()
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Get water techniques
        result = climate_tools.get_water_efficient_techniques(
            sample_location, 'high', 'wheat'
        )
        
        # Assertions
        assert result['success'] is True
        assert 'recommended_techniques' in result
        assert 'implementation_guide' in result
        assert 'cost_benefit_analysis' in result
    
    def test_generate_seasonal_advice_success(self, climate_tools, mock_bedrock,
                                             sample_location):
        """Test seasonal advice generation"""
        # Mock Bedrock response
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{
                'text': 'For Kharif season, plant rice and cotton. Monitor rainfall...'
            }]
        }).encode()
        mock_bedrock.invoke_model.return_value = mock_response
        
        climate_trends = {
            'temperature': {'average': 30, 'trend': 'stable'},
            'rainfall': {'average': 5, 'trend': 'stable'}
        }
        
        # Generate seasonal advice
        result = climate_tools.generate_seasonal_advice(
            sample_location, 'Kharif', climate_trends
        )
        
        # Assertions
        assert result['success'] is True
        assert 'advice' in result
        assert result['season'] == 'Kharif'
    
    def test_bedrock_invocation_error(self, climate_tools, mock_bedrock):
        """Test Bedrock invocation error handling"""
        # Mock Bedrock error
        mock_bedrock.invoke_model.side_effect = Exception('Bedrock API error')
        
        # Attempt to invoke Bedrock
        with pytest.raises(Exception):
            climate_tools._invoke_bedrock('Test prompt')
    
    def test_factory_function(self):
        """Test factory function"""
        with patch('boto3.resource'), patch('boto3.client'):
            tools = create_climate_adaptive_tools(region='us-west-2')
            assert isinstance(tools, ClimateAdaptiveTools)
            assert tools.region == 'us-west-2'


class TestClimateAdaptiveLambda:
    """Test suite for climate-adaptive Lambda function"""
    
    @pytest.fixture
    def mock_climate_tools(self):
        """Mock ClimateAdaptiveTools"""
        # Import the module first to ensure it's loaded
        import tools.climate_adaptive_lambda
        with patch.object(tools.climate_adaptive_lambda, 'climate_tools') as mock_tools:
            yield mock_tools
    
    def test_lambda_handler_analyze_climate(self, mock_climate_tools):
        """Test Lambda handler for climate analysis"""
        from tools.climate_adaptive_lambda import lambda_handler
        
        # Mock climate tools response
        mock_climate_tools.analyze_climate_data.return_value = {
            'success': True,
            'analysis_id': 'test_123',
            'trends': {},
            'risks': []
        }
        
        # Create event
        event = {
            'body': json.dumps({
                'action': 'analyze_climate',
                'location': {'name': 'Test', 'latitude': 18.5, 'longitude': 73.8},
                'historical_weather': [{'date': '2024-01-01', 'temp_avg': 28}],
                'current_season': 'Kharif'
            })
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
    
    def test_lambda_handler_crop_varieties(self, mock_climate_tools):
        """Test Lambda handler for crop variety recommendations"""
        from tools.climate_adaptive_lambda import lambda_handler
        
        # Mock climate tools response
        mock_climate_tools.get_resilient_crop_varieties.return_value = {
            'success': True,
            'recommended_varieties': []
        }
        
        # Create event
        event = {
            'body': json.dumps({
                'action': 'crop_varieties',
                'location': {'name': 'Test', 'latitude': 18.5, 'longitude': 73.8},
                'climate_risks': ['drought', 'heat_stress']
            })
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
    
    def test_lambda_handler_water_techniques(self, mock_climate_tools):
        """Test Lambda handler for water-efficient techniques"""
        from tools.climate_adaptive_lambda import lambda_handler
        
        # Mock climate tools response
        mock_climate_tools.get_water_efficient_techniques.return_value = {
            'success': True,
            'recommended_techniques': []
        }
        
        # Create event
        event = {
            'body': json.dumps({
                'action': 'water_techniques',
                'location': {'name': 'Test', 'latitude': 18.5, 'longitude': 73.8},
                'water_scarcity_level': 'high'
            })
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
    
    def test_lambda_handler_seasonal_advice(self, mock_climate_tools):
        """Test Lambda handler for seasonal advice"""
        from tools.climate_adaptive_lambda import lambda_handler
        
        # Mock climate tools response
        mock_climate_tools.generate_seasonal_advice.return_value = {
            'success': True,
            'advice': {}
        }
        
        # Create event
        event = {
            'body': json.dumps({
                'action': 'seasonal_advice',
                'location': {'name': 'Test', 'latitude': 18.5, 'longitude': 73.8},
                'current_season': 'Rabi',
                'climate_trends': {'temperature': {'average': 30}}
            })
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
    
    def test_lambda_handler_invalid_action(self, mock_climate_tools):
        """Test Lambda handler with invalid action"""
        from tools.climate_adaptive_lambda import lambda_handler
        
        # Create event
        event = {
            'body': json.dumps({
                'action': 'invalid_action',
                'location': {'name': 'Test'}
            })
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Assertions
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
    
    def test_lambda_handler_missing_required_fields(self, mock_climate_tools):
        """Test Lambda handler with missing required fields"""
        from tools.climate_adaptive_lambda import lambda_handler
        
        # Create event with missing location
        event = {
            'body': json.dumps({
                'action': 'analyze_climate',
                'historical_weather': []
            })
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Assertions - handler returns error in body with 200 or 500 status
        assert response['statusCode'] in [200, 500]
        body = json.loads(response['body'])
        assert body['success'] is False
    
    def test_lambda_handler_invalid_water_scarcity_level(self, mock_climate_tools):
        """Test Lambda handler with invalid water scarcity level"""
        from tools.climate_adaptive_lambda import lambda_handler
        
        # Create event
        event = {
            'body': json.dumps({
                'action': 'water_techniques',
                'location': {'name': 'Test'},
                'water_scarcity_level': 'invalid_level'
            })
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Assertions - handler returns error in body with 200 or 500 status
        assert response['statusCode'] in [200, 500]
        body = json.loads(response['body'])
        assert body['success'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
