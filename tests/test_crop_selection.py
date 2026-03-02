"""
Tests for crop selection tools
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from tools.crop_selection_tools import (
    CropSelectionTools,
    create_crop_selection_tools,
    recommend_crops,
    calculate_crop_profitability,
    generate_seasonal_calendar
)


@pytest.fixture
def mock_bedrock_client():
    """Mock Bedrock client"""
    with patch('boto3.client') as mock_client:
        mock_bedrock = Mock()
        mock_client.return_value = mock_bedrock
        yield mock_bedrock


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB resource"""
    with patch('boto3.resource') as mock_resource:
        mock_db = Mock()
        mock_table = Mock()
        mock_db.Table.return_value = mock_table
        mock_resource.return_value = mock_db
        yield mock_table


@pytest.fixture
def sample_soil_analysis():
    """Sample soil analysis data"""
    return {
        'soil_type': 'loam',
        'fertility_level': 'medium',
        'ph_level': 6.5,
        'npk_levels': {
            'nitrogen': 'medium',
            'phosphorus': 'low',
            'potassium': 'high'
        },
        'organic_matter': 2.5,
        'deficiencies': ['phosphorus']
    }


@pytest.fixture
def sample_location():
    """Sample location data"""
    return {
        'state': 'Punjab',
        'district': 'Ludhiana'
    }


class TestCropSelectionTools:
    """Test CropSelectionTools class"""
    
    def test_initialization(self, mock_bedrock_client, mock_dynamodb):
        """Test tools initialization"""
        tools = CropSelectionTools(region='us-east-1')
        
        assert tools.region == 'us-east-1'
        assert tools.model_id == 'anthropic.claude-3-sonnet-20240229-v1:0'
        assert len(tools.seasons) == 4
    
    def test_recommend_crops_success(self, mock_bedrock_client, mock_dynamodb, 
                                     sample_soil_analysis, sample_location):
        """Test successful crop recommendation"""
        # Mock Bedrock response
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = b'''{
            "content": [{
                "text": "HIGHLY RECOMMENDED CROPS:\\n\\nCrop Name: Wheat\\nExpected Yield: 25 quintals per acre\\nMarket Demand: high\\nNet Profit: Rs 30000 per acre\\nRisk Level: low"
            }]
        }'''
        mock_bedrock_client.invoke_model.return_value = mock_response
        
        tools = CropSelectionTools(region='us-east-1')
        
        result = tools.recommend_crops(
            soil_analysis=sample_soil_analysis,
            location=sample_location,
            farm_size_acres=5.0
        )
        
        assert result['success'] is True
        assert 'recommendation_id' in result
        assert 'highly_recommended_crops' in result
        assert mock_bedrock_client.invoke_model.called
    
    def test_recommend_crops_with_climate_data(self, mock_bedrock_client, mock_dynamodb,
                                               sample_soil_analysis, sample_location):
        """Test crop recommendation with climate data"""
        climate_data = {
            'temperature': {'min': 15, 'max': 30},
            'rainfall': 800,
            'season': 'kharif'
        }
        
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = b'''{
            "content": [{
                "text": "HIGHLY RECOMMENDED CROPS:\\n\\nCrop Name: Rice\\nExpected Yield: 30 quintals"
            }]
        }'''
        mock_bedrock_client.invoke_model.return_value = mock_response
        
        tools = CropSelectionTools(region='us-east-1')
        
        result = tools.recommend_crops(
            soil_analysis=sample_soil_analysis,
            location=sample_location,
            farm_size_acres=3.0,
            climate_data=climate_data
        )
        
        assert result['success'] is True
        assert 'recommendation_id' in result
    
    def test_calculate_crop_profitability_success(self, mock_bedrock_client, mock_dynamodb,
                                                  sample_location):
        """Test successful profitability calculation"""
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = b'''{
            "content": [{
                "text": "TOTAL INPUT COST PER ACRE: Rs 25000\\nAverage Yield: 25 quintals per acre\\nAverage Net Profit: Rs 30000\\nROI: 120%"
            }]
        }'''
        mock_bedrock_client.invoke_model.return_value = mock_response
        
        tools = CropSelectionTools(region='us-east-1')
        
        result = tools.calculate_crop_profitability(
            crop_name='Wheat',
            farm_size_acres=5.0,
            location=sample_location,
            soil_type='loam',
            market_price=2200
        )
        
        assert result['success'] is True
        assert result['crop_name'] == 'Wheat'
        assert 'input_costs_per_acre' in result
        assert 'net_profit_per_acre' in result
        assert mock_bedrock_client.invoke_model.called
    
    def test_calculate_profitability_with_custom_costs(self, mock_bedrock_client, mock_dynamodb,
                                                       sample_location):
        """Test profitability with custom input costs"""
        input_costs = {
            'seeds': 3000,
            'fertilizers': 8000,
            'labor': 10000,
            'irrigation': 4000
        }
        
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = b'''{
            "content": [{
                "text": "TOTAL INPUT COST PER ACRE: Rs 25000\\nNet Profit: Rs 28000"
            }]
        }'''
        mock_bedrock_client.invoke_model.return_value = mock_response
        
        tools = CropSelectionTools(region='us-east-1')
        
        result = tools.calculate_crop_profitability(
            crop_name='Maize',
            farm_size_acres=3.0,
            location=sample_location,
            soil_type='sandy',
            input_costs=input_costs
        )
        
        assert result['success'] is True
    
    def test_generate_seasonal_calendar_success(self, mock_bedrock_client, mock_dynamodb,
                                               sample_location):
        """Test successful seasonal calendar generation"""
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = b'''{
            "content": [{
                "text": "KHARIF SEASON:\\nCrop Name: Rice\\nPlanting Window: June-July\\n\\nRABI SEASON:\\nCrop Name: Wheat\\nPlanting Window: November-December"
            }]
        }'''
        mock_bedrock_client.invoke_model.return_value = mock_response
        
        tools = CropSelectionTools(region='us-east-1')
        
        result = tools.generate_seasonal_calendar(
            location=sample_location,
            soil_type='loam',
            farm_size_acres=5.0
        )
        
        assert result['success'] is True
        assert 'kharif_crops' in result
        assert 'rabi_crops' in result
        assert mock_bedrock_client.invoke_model.called
    
    def test_generate_calendar_with_selected_crops(self, mock_bedrock_client, mock_dynamodb,
                                                   sample_location):
        """Test calendar generation with selected crops"""
        selected_crops = ['Wheat', 'Rice', 'Cotton']
        
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = b'''{
            "content": [{
                "text": "KHARIF SEASON:\\nCrop Name: Rice\\nCrop Name: Cotton\\n\\nRABI SEASON:\\nCrop Name: Wheat"
            }]
        }'''
        mock_bedrock_client.invoke_model.return_value = mock_response
        
        tools = CropSelectionTools(region='us-east-1')
        
        result = tools.generate_seasonal_calendar(
            location=sample_location,
            soil_type='clay',
            farm_size_acres=10.0,
            selected_crops=selected_crops
        )
        
        assert result['success'] is True
        assert result['location'] == sample_location
    
    def test_compare_crop_options_success(self, mock_bedrock_client, mock_dynamodb,
                                         sample_soil_analysis, sample_location):
        """Test successful crop comparison"""
        crop_list = ['Wheat', 'Rice', 'Maize']
        
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = b'''{
            "content": [{
                "text": "COMPARISON TABLE:\\nWheat | Rice | Maize\\nTop Choice: Wheat - highest profitability"
            }]
        }'''
        mock_bedrock_client.invoke_model.return_value = mock_response
        
        tools = CropSelectionTools(region='us-east-1')
        
        result = tools.compare_crop_options(
            crop_list=crop_list,
            soil_analysis=sample_soil_analysis,
            location=sample_location,
            farm_size_acres=5.0
        )
        
        assert result['success'] is True
        assert result['crops_compared'] == crop_list
        assert 'comparison_criteria' in result
        assert mock_bedrock_client.invoke_model.called
    
    def test_get_mock_market_price(self, mock_bedrock_client, mock_dynamodb):
        """Test mock market price retrieval"""
        tools = CropSelectionTools(region='us-east-1')
        
        # Test known crops
        assert tools._get_mock_market_price('Wheat', {}) == 2200
        assert tools._get_mock_market_price('Rice', {}) == 2000
        assert tools._get_mock_market_price('Cotton', {}) == 6000
        
        # Test unknown crop (should return default)
        assert tools._get_mock_market_price('UnknownCrop', {}) == 2500
    
    def test_error_handling(self, mock_bedrock_client, mock_dynamodb, sample_soil_analysis,
                           sample_location):
        """Test error handling in crop recommendation"""
        # Mock Bedrock to raise an exception
        mock_bedrock_client.invoke_model.side_effect = Exception('Bedrock error')
        
        tools = CropSelectionTools(region='us-east-1')
        
        result = tools.recommend_crops(
            soil_analysis=sample_soil_analysis,
            location=sample_location,
            farm_size_acres=5.0
        )
        
        assert result['success'] is False
        assert 'error' in result


class TestFactoryFunctions:
    """Test factory and helper functions"""
    
    def test_create_crop_selection_tools(self, mock_bedrock_client, mock_dynamodb):
        """Test factory function"""
        tools = create_crop_selection_tools(region='us-west-2')
        
        assert isinstance(tools, CropSelectionTools)
        assert tools.region == 'us-west-2'
    
    def test_recommend_crops_function(self, mock_bedrock_client, mock_dynamodb,
                                     sample_soil_analysis, sample_location):
        """Test recommend_crops helper function"""
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = b'''{
            "content": [{
                "text": "HIGHLY RECOMMENDED CROPS:\\nCrop Name: Wheat"
            }]
        }'''
        mock_bedrock_client.invoke_model.return_value = mock_response
        
        result = recommend_crops(
            soil_analysis=sample_soil_analysis,
            location=sample_location,
            farm_size_acres=5.0
        )
        
        assert result['success'] is True
    
    def test_calculate_crop_profitability_function(self, mock_bedrock_client, mock_dynamodb,
                                                   sample_location):
        """Test calculate_crop_profitability helper function"""
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = b'''{
            "content": [{
                "text": "Net Profit: Rs 30000"
            }]
        }'''
        mock_bedrock_client.invoke_model.return_value = mock_response
        
        result = calculate_crop_profitability(
            crop_name='Wheat',
            farm_size_acres=5.0,
            location=sample_location,
            soil_type='loam'
        )
        
        assert result['success'] is True
    
    def test_generate_seasonal_calendar_function(self, mock_bedrock_client, mock_dynamodb,
                                                sample_location):
        """Test generate_seasonal_calendar helper function"""
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = b'''{
            "content": [{
                "text": "KHARIF SEASON: Rice\\nRABI SEASON: Wheat"
            }]
        }'''
        mock_bedrock_client.invoke_model.return_value = mock_response
        
        result = generate_seasonal_calendar(
            location=sample_location,
            soil_type='loam',
            farm_size_acres=5.0
        )
        
        assert result['success'] is True
