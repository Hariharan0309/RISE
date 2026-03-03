"""
Tests for RISE Scheme Discovery Tools
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

from scheme_discovery_tools import SchemeDiscoveryTools


@pytest.fixture
def mock_aws_clients():
    """Mock AWS clients for testing"""
    with patch('boto3.resource') as mock_dynamodb, \
         patch('boto3.client') as mock_bedrock:
        
        # Mock DynamoDB
        mock_table = Mock()
        mock_dynamodb.return_value.Table.return_value = mock_table
        
        # Mock Bedrock
        mock_bedrock_client = Mock()
        mock_bedrock.return_value = mock_bedrock_client
        
        yield {
            'dynamodb': mock_dynamodb,
            'bedrock': mock_bedrock_client,
            'table': mock_table
        }


@pytest.fixture
def sample_farmer_profile():
    """Sample farmer profile for testing"""
    return {
        'name': 'Test Farmer',
        'location': {
            'state': 'uttar pradesh',
            'district': 'lucknow'
        },
        'farm_details': {
            'land_size': 2.0,
            'soil_type': 'loamy',
            'crops': ['wheat', 'rice'],
            'farming_experience': '10 years',
            'land_ownership': True
        },
        'annual_income': 150000
    }


@pytest.fixture
def sample_scheme():
    """Sample scheme for testing"""
    return {
        'scheme_id': 'SCH_TEST123',
        'scheme_name': 'Test Subsidy Scheme',
        'scheme_type': 'central',
        'state': 'central',
        'category': 'subsidies',
        'description': 'Test scheme for farmers',
        'benefit_amount': Decimal('6000'),
        'eligibility_criteria': {
            'land_ownership': 'required',
            'land_size': 'any',
            'farmer_type': 'all'
        },
        'required_documents': ['Aadhaar', 'Bank Account', 'Land Records'],
        'application_process': 'Online application',
        'application_deadline': 0,
        'active_status': 'active'
    }


class TestSchemeDiscoveryTools:
    """Test suite for SchemeDiscoveryTools"""
    
    def test_initialization(self, mock_aws_clients):
        """Test tools initialization"""
        tools = SchemeDiscoveryTools(region='us-east-1')
        
        assert tools.region == 'us-east-1'
        assert tools.dynamodb is not None
        assert tools.bedrock is not None
        assert len(tools.farmer_categories) == 4
    
    def test_determine_farmer_category(self, mock_aws_clients):
        """Test farmer category determination"""
        tools = SchemeDiscoveryTools()
        
        assert tools._determine_farmer_category(0.5) == 'marginal'
        assert tools._determine_farmer_category(1.5) == 'small'
        assert tools._determine_farmer_category(5.0) == 'medium'
        assert tools._determine_farmer_category(15.0) == 'large'
    
    def test_calculate_profile_completeness(self, mock_aws_clients, sample_farmer_profile):
        """Test profile completeness calculation"""
        tools = SchemeDiscoveryTools()
        
        # Complete profile
        completeness = tools._calculate_profile_completeness(sample_farmer_profile)
        assert completeness == 1.0
        
        # Incomplete profile
        incomplete_profile = {
            'location': {'state': 'punjab'},
            'farm_details': {}
        }
        completeness = tools._calculate_profile_completeness(incomplete_profile)
        assert completeness < 1.0
    
    def test_analyze_farmer_profile(self, mock_aws_clients, sample_farmer_profile):
        """Test farmer profile analysis"""
        tools = SchemeDiscoveryTools()
        
        # Mock Bedrock response
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = b'''{
            "content": [{
                "text": "{\\"relevant_categories\\": [\\"subsidies\\", \\"crop_insurance\\"], \\"farmer_needs\\": [\\"Financial support\\"], \\"priority_areas\\": [\\"Income support\\"], \\"estimated_benefits\\": \\"High\\"}"
            }]
        }'''
        
        mock_aws_clients['bedrock'].invoke_model.return_value = mock_response
        
        result = tools.analyze_farmer_profile(sample_farmer_profile)
        
        assert result['success'] is True
        assert 'analysis' in result
        assert 'profile_summary' in result
        assert result['profile_summary']['farmer_category'] == 'small'
    
    def test_check_eligibility_eligible(self, mock_aws_clients, sample_farmer_profile, sample_scheme):
        """Test eligibility check for eligible farmer"""
        tools = SchemeDiscoveryTools()
        
        # Mock DynamoDB response
        mock_aws_clients['table'].get_item.return_value = {
            'Item': sample_scheme
        }
        
        result = tools.check_eligibility(sample_farmer_profile, 'SCH_TEST123')
        
        assert result['success'] is True
        assert result['eligible'] is True
        assert result['confidence_score'] > 0
        assert len(result['required_documents']) > 0
    
    def test_check_eligibility_not_eligible(self, mock_aws_clients, sample_farmer_profile, sample_scheme):
        """Test eligibility check for non-eligible farmer"""
        tools = SchemeDiscoveryTools()
        
        # Modify scheme to require different state
        sample_scheme['state'] = 'maharashtra'
        
        # Mock DynamoDB response
        mock_aws_clients['table'].get_item.return_value = {
            'Item': sample_scheme
        }
        
        result = tools.check_eligibility(sample_farmer_profile, 'SCH_TEST123')
        
        assert result['success'] is True
        assert result['eligible'] is False
        assert len(result['reasons']) > 0
    
    def test_check_eligibility_scheme_not_found(self, mock_aws_clients, sample_farmer_profile):
        """Test eligibility check with non-existent scheme"""
        tools = SchemeDiscoveryTools()
        
        # Mock DynamoDB response with no item
        mock_aws_clients['table'].get_item.return_value = {}
        
        result = tools.check_eligibility(sample_farmer_profile, 'SCH_INVALID')
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_calculate_benefit_amount(self, mock_aws_clients, sample_farmer_profile, sample_scheme):
        """Test benefit amount calculation"""
        tools = SchemeDiscoveryTools()
        
        # Mock DynamoDB response
        mock_aws_clients['table'].get_item.return_value = {
            'Item': sample_scheme
        }
        
        result = tools.calculate_benefit_amount(sample_farmer_profile, 'SCH_TEST123')
        
        assert result['success'] is True
        assert result['base_benefit'] == 6000.0
        assert result['estimated_benefit'] > 0
        assert 'is_recurring' in result
        assert 'total_5year_benefit' in result
    
    def test_prioritize_schemes(self, mock_aws_clients, sample_scheme):
        """Test scheme prioritization"""
        tools = SchemeDiscoveryTools()
        
        # Create multiple schemes with different attributes
        schemes = [
            {**sample_scheme, 'benefit_amount': 10000, 'application_deadline': 0},
            {**sample_scheme, 'benefit_amount': 50000, 'application_deadline': 0},
            {**sample_scheme, 'benefit_amount': 5000, 'application_deadline': 0}
        ]
        
        result = tools.prioritize_schemes(schemes)
        
        assert result['success'] is True
        assert len(result['schemes']) == 3
        assert result['schemes'][0]['priority_score'] > result['schemes'][2]['priority_score']
        assert 'total_benefit' in result
    
    def test_generate_required_documents(self, mock_aws_clients, sample_farmer_profile, sample_scheme):
        """Test required documents generation"""
        tools = SchemeDiscoveryTools()
        
        docs = tools._generate_required_documents(sample_scheme, sample_farmer_profile)
        
        assert len(docs) > 0
        assert 'Aadhaar' in docs
    
    def test_check_land_size_eligibility(self, mock_aws_clients):
        """Test land size eligibility checking"""
        tools = SchemeDiscoveryTools()
        
        # Test below requirement
        assert tools._check_land_size_eligibility(1.5, 'below 2 acres') is True
        assert tools._check_land_size_eligibility(3.0, 'below 2 acres') is False
        
        # Test above requirement
        assert tools._check_land_size_eligibility(5.0, 'above 3 acres') is True
        assert tools._check_land_size_eligibility(2.0, 'above 3 acres') is False
        
        # Test any requirement
        assert tools._check_land_size_eligibility(10.0, 'any') is True
    
    def test_get_priority_level(self, mock_aws_clients):
        """Test priority level determination"""
        tools = SchemeDiscoveryTools()
        
        assert tools._get_priority_level(85) == 'high'
        assert tools._get_priority_level(65) == 'medium'
        assert tools._get_priority_level(40) == 'low'
    
    def test_calculate_days_to_deadline(self, mock_aws_clients):
        """Test days to deadline calculation"""
        tools = SchemeDiscoveryTools()
        
        from datetime import datetime, timedelta
        
        # Future deadline
        future_deadline = int((datetime.now() + timedelta(days=30)).timestamp())
        days = tools._calculate_days_to_deadline(future_deadline)
        assert days is not None
        assert days > 0
        
        # Past deadline
        past_deadline = int((datetime.now() - timedelta(days=30)).timestamp())
        days = tools._calculate_days_to_deadline(past_deadline)
        assert days == 0
        
        # No deadline
        days = tools._calculate_days_to_deadline(0)
        assert days is None
    
    def test_convert_decimals(self, mock_aws_clients):
        """Test Decimal to float conversion"""
        tools = SchemeDiscoveryTools()
        
        # Test with dict
        data = {'amount': Decimal('100.50'), 'count': 5}
        converted = tools._convert_decimals(data)
        assert isinstance(converted['amount'], float)
        assert converted['amount'] == 100.50
        
        # Test with list
        data = [Decimal('10.5'), Decimal('20.5')]
        converted = tools._convert_decimals(data)
        assert all(isinstance(x, float) for x in converted)
        
        # Test with nested structure
        data = {'schemes': [{'benefit': Decimal('5000')}]}
        converted = tools._convert_decimals(data)
        assert isinstance(converted['schemes'][0]['benefit'], float)


class TestToolFunctions:
    """Test suite for tool functions"""
    
    def test_create_scheme_discovery_tools(self, mock_aws_clients):
        """Test factory function"""
        from scheme_discovery_tools import create_scheme_discovery_tools
        
        tools = create_scheme_discovery_tools(region='us-east-1')
        
        assert isinstance(tools, SchemeDiscoveryTools)
        assert tools.region == 'us-east-1'
    
    @patch('scheme_discovery_tools.SchemeDiscoveryTools')
    def test_recommend_schemes_tool(self, mock_tools_class, sample_farmer_profile):
        """Test recommend schemes tool function"""
        from scheme_discovery_tools import recommend_schemes_tool
        
        # Mock the tools instance
        mock_tools = Mock()
        mock_tools_class.return_value = mock_tools
        
        mock_tools.recommend_schemes.return_value = {
            'success': True,
            'count': 2,
            'schemes': [
                {
                    'scheme_name': 'Test Scheme 1',
                    'priority_level': 'high',
                    'priority_score': 85,
                    'estimated_benefit': 10000,
                    'category': 'subsidies',
                    'days_to_deadline': 30,
                    'required_documents': ['Aadhaar', 'Bank Account']
                }
            ],
            'total_potential_benefit': 10000
        }
        
        result = recommend_schemes_tool(sample_farmer_profile)
        
        assert isinstance(result, str)
        assert 'Test Scheme 1' in result
        assert 'HIGH' in result
    
    @patch('scheme_discovery_tools.SchemeDiscoveryTools')
    def test_check_eligibility_tool(self, mock_tools_class, sample_farmer_profile):
        """Test check eligibility tool function"""
        from scheme_discovery_tools import check_eligibility_tool
        
        # Mock the tools instance
        mock_tools = Mock()
        mock_tools_class.return_value = mock_tools
        
        mock_tools.check_eligibility.return_value = {
            'success': True,
            'scheme_name': 'Test Scheme',
            'eligible': True,
            'confidence_score': 0.9,
            'reasons': ['All criteria met'],
            'required_documents': ['Aadhaar', 'Bank Account'],
            'next_steps': ['Gather documents', 'Apply online']
        }
        
        result = check_eligibility_tool(sample_farmer_profile, 'SCH_TEST123')
        
        assert isinstance(result, str)
        assert 'ELIGIBLE' in result
        assert 'Test Scheme' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
