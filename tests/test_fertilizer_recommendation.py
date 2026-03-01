"""
Unit Tests for RISE Fertilizer Recommendation Tools
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.fertilizer_recommendation_tools import FertilizerRecommendationTools


class TestFertilizerRecommendationTools:
    """Test suite for fertilizer recommendation tools"""
    
    @pytest.fixture
    def fertilizer_tools(self):
        """Create fertilizer tools instance with mocked AWS clients"""
        with patch('boto3.client'), patch('boto3.resource'):
            tools = FertilizerRecommendationTools(region='us-east-1')
            
            # Mock AWS clients
            tools.bedrock_runtime = Mock()
            tools.dynamodb = Mock()
            tools.farm_data_table = Mock()
            
            return tools
    
    @pytest.fixture
    def sample_soil_analysis(self):
        """Sample soil analysis data"""
        return {
            'soil_type': 'loam',
            'fertility_level': 'medium',
            'ph_level': 6.5,
            'npk_levels': {
                'nitrogen': 'low',
                'phosphorus': 'medium',
                'potassium': 'high'
            },
            'organic_matter': 2.5,
            'deficiencies': ['Nitrogen deficiency', 'Low organic matter']
        }
    
    @pytest.fixture
    def sample_npk_requirements(self):
        """Sample NPK requirements"""
        return {
            'nitrogen_per_acre': 60,
            'phosphorus_per_acre': 30,
            'potassium_per_acre': 20,
            'total_nitrogen': 150,
            'total_phosphorus': 75,
            'total_potassium': 50
        }
    
    @pytest.fixture
    def sample_weather_forecast(self):
        """Sample weather forecast"""
        return {
            'next_7_days': [
                {'date': '2024-01-15', 'temp_max': 28, 'temp_min': 15, 'rainfall': 0, 'humidity': 65},
                {'date': '2024-01-16', 'temp_max': 29, 'temp_min': 16, 'rainfall': 5, 'humidity': 70},
                {'date': '2024-01-17', 'temp_max': 27, 'temp_min': 14, 'rainfall': 0, 'humidity': 60}
            ]
        }

    
    def test_initialization(self, fertilizer_tools):
        """Test tool initialization"""
        assert fertilizer_tools.region == 'us-east-1'
        assert fertilizer_tools.model_id == 'anthropic.claude-3-sonnet-20240229-v1:0'
        assert 'seedling' in fertilizer_tools.growth_stages
        assert 'vegetative' in fertilizer_tools.growth_stages
        assert 'flowering' in fertilizer_tools.growth_stages
    
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_calculate_npk_requirements_success(self, mock_resource, mock_client, sample_soil_analysis):
        """Test successful NPK calculation"""
        # Setup mocks
        mock_bedrock = Mock()
        mock_dynamodb = Mock()
        mock_table = Mock()
        
        mock_client.return_value = mock_bedrock
        mock_resource.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock Bedrock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{
                'text': """
1. CROP NPK REQUIREMENTS:
   - Total Nitrogen (N) needed: 60 kg per acre
   - Total Phosphorus (P2O5) needed: 30 kg per acre
   - Total Potassium (K2O) needed: 20 kg per acre

2. NET REQUIREMENTS:
   - Additional N needed: 50 kg per acre
   - Additional P needed: 25 kg per acre
   - Additional K needed: 15 kg per acre

3. TOTAL FARM REQUIREMENTS (2.5 acres):
   - Total N: 125 kg
   - Total P2O5: 62.5 kg
   - Total K2O: 37.5 kg
"""
            }]
        }).encode()
        
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Create tools instance
        tools = FertilizerRecommendationTools(region='us-east-1')
        tools.bedrock_runtime = mock_bedrock
        tools.farm_data_table = mock_table
        
        # Calculate NPK
        result = tools.calculate_npk_requirements(
            soil_analysis=sample_soil_analysis,
            target_crop='wheat',
            farm_size_acres=2.5,
            location={'state': 'Punjab', 'district': 'Ludhiana'}
        )
        
        # Verify result
        assert result['success'] == True
        assert result['target_crop'] == 'wheat'
        assert result['farm_size_acres'] == 2.5
        assert 'nitrogen_per_acre' in result
        assert 'full_calculation' in result
        
        # Verify Bedrock was called
        mock_bedrock.invoke_model.assert_called_once()

    
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_get_precision_recommendations_success(self, mock_resource, mock_client,
                                                   sample_npk_requirements, sample_soil_analysis):
        """Test successful precision recommendations"""
        # Setup mocks
        mock_bedrock = Mock()
        mock_dynamodb = Mock()
        mock_table = Mock()
        
        mock_client.return_value = mock_bedrock
        mock_resource.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock Bedrock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{
                'text': """
1. ORGANIC FERTILIZER OPTIONS:
   - Farmyard Manure: 5 tons per acre, ₹10,000 per acre
   - Vermicompost: 2 tons per acre, ₹8,000 per acre

2. CHEMICAL FERTILIZER OPTIONS:
   - Urea (46% N): 100 kg per acre, ₹2,000 per acre
   - DAP (18:46:0): 50 kg per acre, ₹1,500 per acre

3. COMBINED APPROACH:
   - Use 3 tons FYM + 50 kg Urea per acre
   - Total cost: ₹8,000 per acre

4. APPLICATION TIMING:
   - Apply FYM 2 weeks before planting
   - Apply Urea in split doses at 30 and 60 days
"""
            }]
        }).encode()
        
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Create tools instance
        tools = FertilizerRecommendationTools(region='us-east-1')
        tools.bedrock_runtime = mock_bedrock
        tools.farm_data_table = mock_table
        
        # Get recommendations
        result = tools.get_precision_recommendations(
            npk_requirements=sample_npk_requirements,
            soil_analysis=sample_soil_analysis,
            target_crop='wheat',
            growth_stage='vegetative',
            weather_forecast=None,
            budget_constraint=20000
        )
        
        # Verify result
        assert result['success'] == True
        assert result['target_crop'] == 'wheat'
        assert result['growth_stage'] == 'vegetative'
        assert 'organic_options' in result
        assert 'chemical_options' in result
        assert 'full_recommendations' in result
    
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_get_application_timing_success(self, mock_resource, mock_client, sample_weather_forecast):
        """Test successful application timing"""
        # Setup mocks
        mock_bedrock = Mock()
        mock_client.return_value = mock_bedrock
        
        # Mock Bedrock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{
                'text': """
1. OPTIMAL APPLICATION WINDOW:
   - Best dates: January 15-17, 2024
   - Rationale: No rainfall expected, moderate temperatures

2. WEATHER CONSIDERATIONS:
   - Avoid application before heavy rain
   - Optimal temperature: 20-30°C
   - Low wind conditions preferred

3. TIME OF DAY:
   - Best time: Early morning (6-9 AM) or late evening (4-6 PM)
   - Reason: Lower temperatures, less evaporation

4. RISK ASSESSMENT:
   - Low risk period identified
   - No heavy rainfall in forecast
"""
            }]
        }).encode()
        
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Create tools instance
        tools = FertilizerRecommendationTools(region='us-east-1')
        tools.bedrock_runtime = mock_bedrock
        
        # Get timing
        result = tools.get_application_timing(
            target_crop='wheat',
            growth_stage='vegetative',
            weather_forecast=sample_weather_forecast,
            location={'state': 'Punjab', 'district': 'Ludhiana'}
        )
        
        # Verify result
        assert result['success'] == True
        assert result['target_crop'] == 'wheat'
        assert result['growth_stage'] == 'vegetative'
        assert 'optimal_window' in result
        assert 'full_timing_analysis' in result

    
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_track_crop_growth_stage_success(self, mock_resource, mock_client):
        """Test successful growth stage tracking"""
        # Setup mocks
        mock_bedrock = Mock()
        mock_dynamodb = Mock()
        mock_table = Mock()
        
        mock_client.return_value = mock_bedrock
        mock_resource.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock Bedrock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{
                'text': """
1. CURRENT GROWTH STAGE:
   - Stage name: Vegetative
   - Sub-stage: Early vegetative
   - Confidence: High

2. STAGE CHARACTERISTICS:
   - Typical duration: 30-40 days
   - Key indicators: Rapid leaf growth, tillering

3. NUTRITIONAL NEEDS:
   - Primary nutrient: Nitrogen
   - Secondary: Phosphorus for root development

4. NEXT STAGE PREDICTION:
   - Expected transition: 15-20 days
   - Signs: Stem elongation, early flowering
"""
            }]
        }).encode()
        
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Create tools instance
        tools = FertilizerRecommendationTools(region='us-east-1')
        tools.bedrock_runtime = mock_bedrock
        tools.farm_data_table = mock_table
        
        # Track growth stage
        planting_date = (datetime.now() - timedelta(days=25)).isoformat()
        
        result = tools.track_crop_growth_stage(
            user_id='test_farmer_001',
            farm_id='farm_test_001',
            crop_name='wheat',
            planting_date=planting_date,
            current_observations={'height_cm': 30, 'leaf_count': 5}
        )
        
        # Verify result
        assert result['success'] == True
        assert 'tracking_id' in result
        assert result['crop_name'] == 'wheat'
        assert result['days_since_planting'] == 25
        assert 'current_stage' in result
        
        # Verify DynamoDB storage
        mock_table.put_item.assert_called_once()
    
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_generate_amendment_suggestions_success(self, mock_resource, mock_client,
                                                   sample_npk_requirements):
        """Test successful amendment suggestions"""
        # Setup mocks
        mock_bedrock = Mock()
        mock_client.return_value = mock_bedrock
        
        # Mock Bedrock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{
                'text': """
1. ORGANIC AMENDMENTS:
   - Farmyard Manure: 5 tons per acre, ₹10,000
   - Compost: 3 tons per acre, ₹6,000
   - Vermicompost: 2 tons per acre, ₹8,000

2. CHEMICAL AMENDMENTS:
   - Urea (46% N): 100 kg per acre, ₹2,000
   - DAP (18:46:0): 50 kg per acre, ₹1,500
   - MOP (60% K2O): 30 kg per acre, ₹900

3. MICRONUTRIENT AMENDMENTS:
   - Zinc Sulfate: 10 kg per acre, ₹500
   - Iron Chelate: 5 kg per acre, ₹400

4. INTEGRATED APPROACH:
   - Use 3 tons FYM + 50 kg Urea + 25 kg DAP
   - Total cost: ₹8,500 per acre
   - Expected yield increase: 20-25%

5. COST COMPARISON:
   - Organic-only: ₹10,000 per acre
   - Chemical-only: ₹4,400 per acre
   - Integrated: ₹8,500 per acre (Recommended)
"""
            }]
        }).encode()
        
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Create tools instance
        tools = FertilizerRecommendationTools(region='us-east-1')
        tools.bedrock_runtime = mock_bedrock
        
        # Generate amendments
        result = tools.generate_amendment_suggestions(
            npk_requirements=sample_npk_requirements,
            soil_deficiencies=['Nitrogen deficiency', 'Low organic matter'],
            farm_size_acres=2.5,
            prioritize_organic=True,
            budget_constraint=25000
        )
        
        # Verify result
        assert result['success'] == True
        assert result['farm_size_acres'] == 2.5
        assert result['prioritize_organic'] == True
        assert 'organic_amendments' in result
        assert 'chemical_amendments' in result
        assert 'full_amendments' in result

    
    def test_parse_npk_calculations(self, fertilizer_tools):
        """Test NPK calculations parsing"""
        calculation_text = """
1. CROP NPK REQUIREMENTS:
   - Total Nitrogen (N) needed: 60 kg per acre
   - Total Phosphorus (P2O5) needed: 30 kg per acre
   - Total Potassium (K2O) needed: 20 kg per acre

2. NET REQUIREMENTS:
   - Additional N needed: 50 kg per acre
   - Additional P needed: 25 kg per acre
   - Additional K needed: 15 kg per acre

3. TOTAL FARM REQUIREMENTS (2.5 acres):
   - Total N: 125 kg
   - Total P2O5: 62.5 kg
   - Total K2O: 37.5 kg
"""
        
        result = fertilizer_tools._parse_npk_calculations(calculation_text)
        
        assert result['nitrogen_per_acre'] == 50
        assert result['phosphorus_per_acre'] == 25
        assert result['potassium_per_acre'] == 15
        assert result['total_nitrogen'] == 125
    
    def test_parse_growth_stage(self, fertilizer_tools):
        """Test growth stage parsing"""
        stage_text = """
1. CURRENT GROWTH STAGE:
   - Stage name: Vegetative
   - Sub-stage: Early vegetative
   - Confidence: High

2. NUTRITIONAL NEEDS:
   - Primary nutrient: Nitrogen
"""
        
        result = fertilizer_tools._parse_growth_stage(stage_text)
        
        assert result['current_stage'] == 'vegetative'
        assert result['sub_stage'] == 'Early vegetative'
        assert result['confidence'] == 'high'
    
    def test_build_npk_calculation_prompt(self, fertilizer_tools, sample_soil_analysis):
        """Test NPK calculation prompt building"""
        prompt = fertilizer_tools._build_npk_calculation_prompt(
            soil_analysis=sample_soil_analysis,
            target_crop='wheat',
            farm_size_acres=2.5,
            location={'state': 'Punjab', 'district': 'Ludhiana'}
        )
        
        assert 'wheat' in prompt
        assert '2.5 acres' in prompt
        assert 'Punjab' in prompt
        assert 'loam' in prompt
        assert 'CROP NPK REQUIREMENTS' in prompt
    
    def test_build_precision_recommendation_prompt(self, fertilizer_tools,
                                                   sample_npk_requirements,
                                                   sample_soil_analysis):
        """Test precision recommendation prompt building"""
        prompt = fertilizer_tools._build_precision_recommendation_prompt(
            npk_requirements=sample_npk_requirements,
            soil_analysis=sample_soil_analysis,
            target_crop='wheat',
            growth_stage='vegetative',
            weather_forecast=None,
            budget_constraint=20000
        )
        
        assert 'wheat' in prompt
        assert 'vegetative' in prompt
        assert '20000' in prompt
        assert 'ORGANIC FERTILIZER OPTIONS' in prompt
        assert 'CHEMICAL FERTILIZER OPTIONS' in prompt
    
    def test_build_timing_prompt(self, fertilizer_tools, sample_weather_forecast):
        """Test timing prompt building"""
        prompt = fertilizer_tools._build_timing_prompt(
            target_crop='wheat',
            growth_stage='vegetative',
            weather_forecast=sample_weather_forecast,
            location={'state': 'Punjab', 'district': 'Ludhiana'}
        )
        
        assert 'wheat' in prompt
        assert 'vegetative' in prompt
        assert 'Punjab' in prompt
        assert 'OPTIMAL APPLICATION WINDOW' in prompt
        assert 'WEATHER CONSIDERATIONS' in prompt
    
    def test_build_growth_stage_prompt(self, fertilizer_tools):
        """Test growth stage prompt building"""
        prompt = fertilizer_tools._build_growth_stage_prompt(
            crop_name='wheat',
            days_since_planting=25,
            current_observations={'height_cm': 30, 'leaf_count': 5}
        )
        
        assert 'wheat' in prompt
        assert '25' in prompt
        assert 'height_cm' in prompt
        assert 'CURRENT GROWTH STAGE' in prompt
    
    def test_store_growth_tracking(self, fertilizer_tools):
        """Test growth tracking storage"""
        stage_data = {
            'current_stage': 'vegetative',
            'confidence': 'high',
            'nutritional_needs': {}
        }
        
        # Should not raise exception
        fertilizer_tools._store_growth_tracking(
            tracking_id='test_growth_123',
            user_id='test_user',
            farm_id='test_farm',
            crop_name='wheat',
            planting_date='2024-01-01',
            days_since_planting=25,
            stage_data=stage_data
        )
        
        # Verify DynamoDB put_item was called
        fertilizer_tools.farm_data_table.put_item.assert_called_once()
        
        # Verify item structure
        call_args = fertilizer_tools.farm_data_table.put_item.call_args
        item = call_args[1]['Item']
        
        assert item['farm_id'] == 'test_farm'
        assert item['user_id'] == 'test_user'
        assert item['data_type'] == 'growth_tracking'
        assert item['crop_name'] == 'wheat'


class TestFertilizerRecommendationIntegration:
    """Integration tests for fertilizer recommendations"""
    
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.environ.get('AWS_ACCESS_KEY_ID'),
        reason="AWS credentials not configured"
    )
    def test_real_bedrock_npk_calculation(self):
        """Test with real Bedrock API (requires AWS credentials)"""
        tools = FertilizerRecommendationTools(region='us-east-1')
        
        soil_analysis = {
            'soil_type': 'loam',
            'fertility_level': 'medium',
            'ph_level': 6.5,
            'npk_levels': {
                'nitrogen': 'low',
                'phosphorus': 'medium',
                'potassium': 'high'
            },
            'organic_matter': 2.5
        }
        
        result = tools.calculate_npk_requirements(
            soil_analysis=soil_analysis,
            target_crop='wheat',
            farm_size_acres=2.5,
            location={'state': 'Punjab', 'district': 'Ludhiana'}
        )
        
        # Should get a response
        assert 'nitrogen_per_acre' in result
        assert 'phosphorus_per_acre' in result
        assert 'potassium_per_acre' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
