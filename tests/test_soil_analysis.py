"""
Unit Tests for RISE Soil Analysis Tools
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import base64
import json
from PIL import Image
import io

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.soil_analysis_tools import SoilAnalysisTools


class TestSoilAnalysisTools:
    """Test suite for soil analysis tools"""
    
    @pytest.fixture
    def soil_tools(self):
        """Create soil tools instance with mocked AWS clients"""
        with patch('boto3.client'), patch('boto3.resource'):
            tools = SoilAnalysisTools(region='us-east-1')
            
            # Mock AWS clients
            tools.bedrock_runtime = Mock()
            tools.s3_client = Mock()
            tools.dynamodb = Mock()
            tools.farm_data_table = Mock()
            
            return tools
    
    @pytest.fixture
    def sample_soil_image(self):
        """Create a sample soil image"""
        img = Image.new('RGB', (800, 600), color='brown')
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        return img_bytes.read()
    
    @pytest.fixture
    def small_image(self):
        """Create a small test image"""
        img = Image.new('RGB', (200, 150), color='brown')
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        return img_bytes.read()
    
    @pytest.fixture
    def sample_test_data(self):
        """Sample soil test data"""
        return {
            'ph': 6.5,
            'nitrogen': 'low',
            'phosphorus': 'medium',
            'potassium': 'high',
            'organic_matter': 2.5,
            'texture': 'loam'
        }
    
    def test_initialization(self, soil_tools):
        """Test tool initialization"""
        assert soil_tools.region == 'us-east-1'
        assert soil_tools.model_id == 'anthropic.claude-3-sonnet-20240229-v1:0'
        assert 'clay' in soil_tools.soil_types
        assert 'loam' in soil_tools.soil_types
        assert soil_tools.fertility_levels == ['low', 'medium', 'high']
    
    def test_validate_image_valid(self, soil_tools, sample_soil_image):
        """Test image validation with valid image"""
        result = soil_tools._validate_image(sample_soil_image)
        
        assert result['valid'] == True
        assert len(result['issues']) == 0
        assert result['dimensions']['width'] == 800
        assert result['dimensions']['height'] == 600
    
    def test_validate_image_low_resolution(self, soil_tools, small_image):
        """Test image validation with low resolution"""
        result = soil_tools._validate_image(small_image)
        
        assert result['valid'] == False
        assert 'low_resolution' in result['issues']
    
    def test_validate_image_invalid(self, soil_tools):
        """Test image validation with invalid data"""
        invalid_data = b'not an image'
        
        result = soil_tools._validate_image(invalid_data)
        
        assert result['valid'] == False
        assert 'invalid_image' in result['issues']
    
    def test_compress_image(self, soil_tools, sample_soil_image):
        """Test image compression"""
        compressed = soil_tools._compress_image(sample_soil_image, max_size_kb=50)
        
        # Should be valid image
        img = Image.open(io.BytesIO(compressed))
        assert img.format == 'JPEG'
    
    def test_build_soil_image_prompt(self, soil_tools):
        """Test soil image prompt building"""
        location = {'state': 'Karnataka', 'district': 'Bangalore'}
        
        prompt = soil_tools._build_soil_image_prompt(location)
        
        assert 'Karnataka' in prompt
        assert 'Bangalore' in prompt
        assert 'SOIL TYPE' in prompt
        assert 'FERTILITY LEVEL' in prompt
        assert 'NPK LEVELS' in prompt
    
    def test_build_soil_image_prompt_no_location(self, soil_tools):
        """Test prompt building without location"""
        prompt = soil_tools._build_soil_image_prompt({})
        
        assert 'SOIL TYPE' in prompt
        assert 'FERTILITY LEVEL' in prompt
    
    def test_build_test_data_prompt(self, soil_tools, sample_test_data):
        """Test test data prompt building"""
        location = {'state': 'Karnataka', 'district': 'Bangalore'}
        
        prompt = soil_tools._build_test_data_prompt(sample_test_data, location)
        
        assert 'Karnataka' in prompt
        assert '6.5' in prompt  # pH value
        assert 'SOIL TYPE' in prompt
        assert 'NPK ANALYSIS' in prompt
    
    def test_parse_soil_analysis_complete(self, soil_tools):
        """Test parsing complete soil analysis"""
        analysis_text = """
1. SOIL TYPE: Loam
2. FERTILITY LEVEL: Medium
3. ESTIMATED pH: 6.5
4. NPK LEVELS:
   - Nitrogen: Low
   - Phosphorus: Medium
   - Potassium: High
5. ORGANIC MATTER: 2.5%
6. DEFICIENCIES: Nitrogen deficiency, Low organic matter
7. SUITABLE CROPS: Wheat, Rice, Maize, Cotton, Sugarcane
8. AMENDMENTS: Apply compost at 5 tons per acre
"""
        
        result = soil_tools._parse_soil_analysis(analysis_text)
        
        assert result['soil_type'] == 'loam'
        assert result['fertility_level'] == 'medium'
        assert result['ph_level'] == 6.5
        assert result['npk_levels']['nitrogen'] == 'low'
        assert result['npk_levels']['phosphorus'] == 'medium'
        assert result['npk_levels']['potassium'] == 'high'
        assert result['organic_matter'] == 2.5
        assert len(result['deficiencies']) > 0
        assert len(result['suitable_crops']) > 0
    
    def test_parse_soil_analysis_minimal(self, soil_tools):
        """Test parsing minimal soil analysis"""
        analysis_text = """
SOIL TYPE: Clay
FERTILITY LEVEL: Low
"""
        
        result = soil_tools._parse_soil_analysis(analysis_text)
        
        assert result['soil_type'] == 'clay'
        assert result['fertility_level'] == 'low'
        assert result['full_analysis'] == analysis_text
    
    def test_extract_level(self, soil_tools):
        """Test nutrient level extraction"""
        assert soil_tools._extract_level('Nitrogen: Low') == 'low'
        assert soil_tools._extract_level('Phosphorus: High') == 'high'
        assert soil_tools._extract_level('Potassium: Medium') == 'medium'
        assert soil_tools._extract_level('Unknown: Something') == 'unknown'
    
    def test_extract_recommendations(self, soil_tools):
        """Test recommendations extraction"""
        analysis_text = """
Apply compost at 5 tons per acre.
Use organic manure for nitrogen.
Apply NPK fertilizer 10:26:26 at 200 kg per acre.
"""
        
        recommendations = soil_tools._extract_recommendations(analysis_text)
        
        assert len(recommendations['organic_amendments']) > 0
        assert len(recommendations['chemical_amendments']) > 0
    
    def test_parse_crop_recommendations(self, soil_tools):
        """Test crop recommendations parsing"""
        recommendations_text = """
1. HIGHLY SUITABLE CROPS:
   - Wheat
   - Rice
   - Maize

2. MODERATELY SUITABLE CROPS:
   - Cotton
   - Sugarcane

3. NOT RECOMMENDED CROPS:
   - Tea (requires acidic soil)
"""
        
        result = soil_tools._parse_crop_recommendations(recommendations_text)
        
        assert len(result['highly_suitable_crops']) >= 2
        assert len(result['moderately_suitable_crops']) >= 1
        assert len(result['not_recommended_crops']) >= 1
    
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_analyze_soil_from_image_success(self, mock_resource, mock_client, sample_soil_image):
        """Test successful soil image analysis"""
        # Setup mocks
        mock_bedrock = Mock()
        mock_s3 = Mock()
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
1. SOIL TYPE: Loam
2. FERTILITY LEVEL: Medium
3. ESTIMATED pH: 6.5
4. NPK LEVELS:
   - Nitrogen: Low
   - Phosphorus: Medium
   - Potassium: High
5. SUITABLE CROPS: Wheat, Rice, Maize
"""
            }]
        }).encode()
        
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Create tools instance
        tools = SoilAnalysisTools(region='us-east-1')
        tools.s3_client = mock_s3
        tools.farm_data_table = mock_table
        tools.bedrock_runtime = mock_bedrock
        
        # Analyze soil
        result = tools.analyze_soil_from_image(
            image_data=sample_soil_image,
            user_id='test_user',
            farm_id='test_farm',
            location={'state': 'Karnataka', 'district': 'Bangalore'}
        )
        
        # Verify result
        assert result['success'] == True
        assert 'analysis_id' in result
        assert result['soil_type'] == 'loam'
        assert result['fertility_level'] == 'medium'
        
        # Verify S3 upload was called
        mock_s3.put_object.assert_called_once()
        
        # Verify DynamoDB storage was called
        mock_table.put_item.assert_called_once()
    
    def test_analyze_soil_from_image_invalid(self, soil_tools, small_image):
        """Test soil analysis with invalid image"""
        result = soil_tools.analyze_soil_from_image(
            image_data=small_image,
            user_id='test_user',
            farm_id='test_farm'
        )
        
        assert result['success'] == False
        assert result['error'] == 'invalid_image'
    
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_analyze_soil_from_test_data_success(self, mock_resource, mock_client, sample_test_data):
        """Test successful soil test data analysis"""
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
1. SOIL TYPE: Loam
2. FERTILITY ASSESSMENT: Medium fertility
3. NPK ANALYSIS:
   - Nitrogen: Low (needs improvement)
   - Phosphorus: Medium (adequate)
   - Potassium: High (excellent)
4. pH ANALYSIS: 6.5 (slightly acidic, good for most crops)
5. DEFICIENCIES: Nitrogen deficiency
6. SUITABLE CROPS: Wheat, Rice, Maize
"""
            }]
        }).encode()
        
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Create tools instance
        tools = SoilAnalysisTools(region='us-east-1')
        tools.farm_data_table = mock_table
        tools.bedrock_runtime = mock_bedrock
        
        # Analyze test data
        result = tools.analyze_soil_from_test_data(
            test_data=sample_test_data,
            user_id='test_user',
            farm_id='test_farm',
            location={'state': 'Karnataka', 'district': 'Bangalore'}
        )
        
        # Verify result
        assert result['success'] == True
        assert 'analysis_id' in result
        assert result['soil_type'] == 'loam'
        assert 'test_data_provided' in result
        
        # Verify DynamoDB storage was called
        mock_table.put_item.assert_called_once()
    
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_get_crop_recommendations(self, mock_resource, mock_client):
        """Test crop recommendations generation"""
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
1. HIGHLY SUITABLE CROPS:
   - Wheat: Expected yield 25 quintals/acre
   - Rice: Expected yield 30 quintals/acre
   - Maize: Expected yield 28 quintals/acre

2. MODERATELY SUITABLE CROPS:
   - Cotton: Requires additional phosphorus
   - Sugarcane: Needs irrigation management

3. NOT RECOMMENDED CROPS:
   - Tea: Requires acidic soil (pH 4.5-5.5)
"""
            }]
        }).encode()
        
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Create tools instance
        tools = SoilAnalysisTools(region='us-east-1')
        tools.bedrock_runtime = mock_bedrock
        
        # Get recommendations
        result = tools.get_crop_recommendations(
            soil_type='loam',
            fertility_level='medium',
            location={'state': 'Karnataka', 'district': 'Bangalore'}
        )
        
        # Verify result
        assert result['success'] == True
        assert len(result['highly_suitable_crops']) >= 2
        assert 'full_recommendations' in result
    
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_generate_deficiency_report(self, mock_resource, mock_client):
        """Test deficiency report generation"""
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
1. DEFICIENCY ANALYSIS:
   - Nitrogen Deficiency: High severity
   - Impact: 30-40% yield reduction

2. ORGANIC AMENDMENT RECOMMENDATIONS:
   - Compost: 5 tons per acre
   - Cost: ₹15,000 per acre

3. CHEMICAL AMENDMENT RECOMMENDATIONS:
   - Urea (46% N): 100 kg per acre
   - Cost: ₹2,000 per acre

4. COMBINED TREATMENT PLAN:
   - Total cost: ₹17,000 per acre
   - Expected improvement: 3-4 months
"""
            }]
        }).encode()
        
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Create tools instance
        tools = SoilAnalysisTools(region='us-east-1')
        tools.bedrock_runtime = mock_bedrock
        
        # Generate report
        result = tools.generate_deficiency_report(
            deficiencies=['Nitrogen deficiency', 'Low organic matter'],
            soil_type='loam',
            location={'state': 'Karnataka', 'district': 'Bangalore'}
        )
        
        # Verify result
        assert result['success'] == True
        assert 'report' in result
        assert len(result['deficiencies']) == 2
        assert result['soil_type'] == 'loam'
    
    def test_store_soil_analysis(self, soil_tools):
        """Test soil analysis storage"""
        analysis = {
            'soil_type': 'loam',
            'fertility_level': 'medium',
            'ph_level': 6.5,
            'npk_levels': {'nitrogen': 'low', 'phosphorus': 'medium', 'potassium': 'high'},
            'deficiencies': ['Nitrogen deficiency'],
            'suitable_crops': ['Wheat', 'Rice'],
            'recommendations': {},
            'full_analysis': 'Test analysis'
        }
        
        # Should not raise exception
        soil_tools._store_soil_analysis(
            analysis_id='test_soil_123',
            farm_id='test_farm',
            user_id='test_user',
            s3_key='test/key.jpg',
            analysis=analysis,
            location={'state': 'Karnataka', 'district': 'Bangalore'}
        )
        
        # Verify DynamoDB put_item was called
        soil_tools.farm_data_table.put_item.assert_called_once()
        
        # Verify item structure
        call_args = soil_tools.farm_data_table.put_item.call_args
        item = call_args[1]['Item']
        
        assert item['farm_id'] == 'test_farm'
        assert item['user_id'] == 'test_user'
        assert item['data_type'] == 'soil_analysis'
        assert item['soil_analysis']['soil_type'] == 'loam'


class TestSoilAnalysisIntegration:
    """Integration tests for soil analysis"""
    
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.environ.get('AWS_ACCESS_KEY_ID'),
        reason="AWS credentials not configured"
    )
    def test_real_bedrock_soil_analysis(self):
        """Test with real Bedrock API (requires AWS credentials)"""
        tools = SoilAnalysisTools(region='us-east-1')
        
        # Create a test image
        img = Image.new('RGB', (800, 600), color='brown')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        result = tools.analyze_soil_from_image(
            image_data=img_bytes.read(),
            user_id='integration_test_user',
            farm_id='integration_test_farm',
            location={'state': 'Karnataka', 'district': 'Bangalore'}
        )
        
        # Should get a response
        assert 'soil_type' in result
        assert 'fertility_level' in result
    
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.environ.get('AWS_ACCESS_KEY_ID'),
        reason="AWS credentials not configured"
    )
    def test_real_bedrock_test_data_analysis(self):
        """Test test data analysis with real Bedrock API"""
        tools = SoilAnalysisTools(region='us-east-1')
        
        test_data = {
            'ph': 6.5,
            'nitrogen': 'low',
            'phosphorus': 'medium',
            'potassium': 'high',
            'organic_matter': 2.5
        }
        
        result = tools.analyze_soil_from_test_data(
            test_data=test_data,
            user_id='integration_test_user',
            farm_id='integration_test_farm',
            location={'state': 'Karnataka', 'district': 'Bangalore'}
        )
        
        # Should get a response
        assert 'soil_type' in result
        assert 'fertility_level' in result
        assert 'test_data_provided' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
