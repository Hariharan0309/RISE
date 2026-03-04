"""
Tests for RISE Best Practice Sharing Tools
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.best_practice_tools import BestPracticeTools


@pytest.fixture
def mock_aws_clients():
    """Mock AWS clients"""
    with patch('boto3.resource') as mock_resource, \
         patch('boto3.client') as mock_client:
        
        # Mock DynamoDB
        mock_table = Mock()
        mock_table.put_item = Mock(return_value={})
        mock_table.get_item = Mock(return_value={'Item': {}})
        mock_table.scan = Mock(return_value={'Items': []})
        mock_table.update_item = Mock(return_value={})
        
        mock_dynamodb = Mock()
        mock_dynamodb.Table = Mock(return_value=mock_table)
        mock_resource.return_value = mock_dynamodb
        
        # Mock Bedrock
        mock_bedrock = Mock()
        mock_bedrock.invoke_model = Mock()
        
        # Mock Translate
        mock_translate = Mock()
        mock_translate.translate_text = Mock()
        
        mock_client.side_effect = lambda service, **kwargs: {
            'bedrock-runtime': mock_bedrock,
            'translate': mock_translate
        }.get(service, Mock())
        
        yield {
            'dynamodb': mock_dynamodb,
            'table': mock_table,
            'bedrock': mock_bedrock,
            'translate': mock_translate
        }


@pytest.fixture
def best_practice_tools(mock_aws_clients):
    """Create BestPracticeTools instance with mocked AWS clients"""
    return BestPracticeTools(region='us-east-1')


def test_submit_practice_success(best_practice_tools, mock_aws_clients):
    """Test successful practice submission"""
    # Mock Bedrock validation response
    validation_response = {
        'is_valid': True,
        'validation_score': 85,
        'reason': 'Practice aligns with scientific principles',
        'references': ['Study on organic farming benefits'],
        'suggestions': [],
        'risk_assessment': 'low',
        'confidence': 0.9
    }
    
    mock_aws_clients['bedrock'].invoke_model.return_value = {
        'body': Mock(read=lambda: json.dumps({
            'content': [{'text': json.dumps(validation_response)}]
        }).encode())
    }
    
    # Submit practice
    result = best_practice_tools.submit_practice(
        user_id='test_user_001',
        title='Organic Pest Control',
        description='Using neem oil for pest control',
        language='en',
        category={'crop_type': 'wheat', 'practice_type': 'pest_control', 'region': 'north_india'},
        steps=['Step 1', 'Step 2', 'Step 3'],
        expected_benefits={'yield_increase': 15, 'cost_reduction': 10}
    )
    
    assert result['success'] is True
    assert 'practice_id' in result
    assert result['validation_score'] == 85
    assert len(result['scientific_references']) > 0
    
    # Verify DynamoDB put_item was called
    mock_aws_clients['table'].put_item.assert_called_once()


def test_submit_practice_validation_failure(best_practice_tools, mock_aws_clients):
    """Test practice submission with validation failure"""
    # Mock Bedrock validation response with low score
    validation_response = {
        'is_valid': False,
        'validation_score': 45,
        'reason': 'Practice lacks scientific backing',
        'references': [],
        'suggestions': ['Add more details', 'Provide evidence'],
        'risk_assessment': 'high',
        'confidence': 0.7
    }
    
    mock_aws_clients['bedrock'].invoke_model.return_value = {
        'body': Mock(read=lambda: json.dumps({
            'content': [{'text': json.dumps(validation_response)}]
        }).encode())
    }
    
    # Submit practice
    result = best_practice_tools.submit_practice(
        user_id='test_user_001',
        title='Unproven Method',
        description='Some unverified practice',
        language='en',
        category={'crop_type': 'wheat', 'practice_type': 'pest_control', 'region': 'north_india'},
        steps=['Step 1'],
        expected_benefits={'yield_increase': 100}
    )
    
    assert result['success'] is False
    assert 'validation failed' in result['error'].lower()
    assert len(result.get('suggestions', [])) > 0


def test_get_practices(best_practice_tools, mock_aws_clients):
    """Test getting practices with filtering"""
    # Mock DynamoDB scan response
    mock_practices = [
        {
            'practice_id': 'practice_001',
            'title': 'Practice 1',
            'category': {'crop_type': 'wheat'},
            'adoption_count': 10,
            'avg_success_rate': 85.5,
            'timestamp': 1000000,
            'status': 'active'
        },
        {
            'practice_id': 'practice_002',
            'title': 'Practice 2',
            'category': {'crop_type': 'rice'},
            'adoption_count': 5,
            'avg_success_rate': 90.0,
            'timestamp': 2000000,
            'status': 'active'
        }
    ]
    
    mock_aws_clients['table'].scan.return_value = {'Items': mock_practices}
    
    # Get practices sorted by popularity
    result = best_practice_tools.get_practices(sort_by='popular', limit=10)
    
    assert result['success'] is True
    assert len(result['practices']) == 2
    assert result['practices'][0]['adoption_count'] >= result['practices'][1]['adoption_count']


def test_get_practice(best_practice_tools, mock_aws_clients):
    """Test getting a single practice"""
    # Mock DynamoDB get_item response
    mock_practice = {
        'practice_id': 'practice_001',
        'title': 'Test Practice',
        'description': 'Test description',
        'steps': ['Step 1', 'Step 2'],
        'status': 'active'
    }
    
    mock_aws_clients['table'].get_item.return_value = {'Item': mock_practice}
    
    # Get practice
    result = best_practice_tools.get_practice('practice_001')
    
    assert result['success'] is True
    assert result['practice']['practice_id'] == 'practice_001'
    assert result['practice']['title'] == 'Test Practice'


def test_adopt_practice(best_practice_tools, mock_aws_clients):
    """Test adopting a practice"""
    # Adopt practice
    result = best_practice_tools.adopt_practice(
        practice_id='practice_001',
        user_id='test_user_001',
        implementation_date='2024-01-15',
        notes='Testing on 2 acres'
    )
    
    assert result['success'] is True
    assert 'adoption_id' in result
    
    # Verify DynamoDB operations
    assert mock_aws_clients['table'].put_item.called
    assert mock_aws_clients['table'].update_item.called


def test_submit_feedback(best_practice_tools, mock_aws_clients):
    """Test submitting feedback on adopted practice"""
    # Mock adoption record
    mock_adoption = {
        'adoption_id': 'adoption_001',
        'practice_id': 'practice_001',
        'user_id': 'test_user_001',
        'status': 'in_progress'
    }
    
    mock_aws_clients['table'].get_item.return_value = {'Item': mock_adoption}
    
    # Mock practice record
    mock_practice = {
        'practice_id': 'practice_001',
        'user_id': 'contributor_001',
        'title': 'Test Practice',
        'success_count': 5,
        'failure_count': 1,
        'total_feedback': 6
    }
    
    # Setup get_item to return different values
    mock_aws_clients['table'].get_item.side_effect = [
        {'Item': mock_adoption},
        {'Item': mock_practice}
    ]
    
    # Submit feedback
    result = best_practice_tools.submit_feedback(
        adoption_id='adoption_001',
        user_id='test_user_001',
        success=True,
        feedback='Worked great! Yield increased by 20%',
        results={'yield_change': 20, 'cost_change': -15}
    )
    
    assert result['success'] is True
    
    # Verify updates were called
    assert mock_aws_clients['table'].update_item.call_count >= 2


def test_get_adoption_analytics(best_practice_tools, mock_aws_clients):
    """Test getting practice analytics"""
    # Mock practice
    mock_practice = {
        'practice_id': 'practice_001',
        'title': 'Test Practice',
        'avg_success_rate': 85.5,
        'validation_score': 90
    }
    
    # Mock adoptions
    mock_adoptions = [
        {
            'adoption_id': 'adoption_001',
            'practice_id': 'practice_001',
            'status': 'completed',
            'success': True,
            'results': {'yield_change': 20, 'cost_change': -10},
            'created_at': '2024-01-01'
        },
        {
            'adoption_id': 'adoption_002',
            'practice_id': 'practice_001',
            'status': 'completed',
            'success': True,
            'results': {'yield_change': 25, 'cost_change': -15},
            'created_at': '2024-01-15'
        },
        {
            'adoption_id': 'adoption_003',
            'practice_id': 'practice_001',
            'status': 'in_progress',
            'created_at': '2024-02-01'
        }
    ]
    
    mock_aws_clients['table'].get_item.return_value = {'Item': mock_practice}
    mock_aws_clients['table'].scan.return_value = {'Items': mock_adoptions}
    
    # Get analytics
    result = best_practice_tools.get_adoption_analytics('practice_001')
    
    assert result['success'] is True
    assert result['analytics']['total_adoptions'] == 3
    assert result['analytics']['completed_adoptions'] == 2
    assert result['analytics']['successful_adoptions'] == 2
    assert result['analytics']['avg_yield_change'] == 22.5
    assert result['analytics']['avg_cost_change'] == -12.5


def test_search_practices(best_practice_tools, mock_aws_clients):
    """Test searching practices"""
    # Mock practices
    mock_practices = [
        {
            'practice_id': 'practice_001',
            'title': 'Organic Pest Control',
            'description': 'Using neem oil for pest management',
            'category': {'crop_type': 'wheat'},
            'avg_success_rate': 85,
            'status': 'active'
        },
        {
            'practice_id': 'practice_002',
            'title': 'Water Management',
            'description': 'Efficient irrigation techniques',
            'category': {'crop_type': 'rice'},
            'avg_success_rate': 90,
            'status': 'active'
        }
    ]
    
    mock_aws_clients['table'].scan.return_value = {'Items': mock_practices}
    
    # Search for "pest"
    result = best_practice_tools.search_practices(query='pest', limit=10)
    
    assert result['success'] is True
    assert len(result['practices']) == 1
    assert 'pest' in result['practices'][0]['title'].lower()


def test_translate_practice(best_practice_tools, mock_aws_clients):
    """Test translating a practice"""
    # Mock practice
    mock_practice = {
        'practice_id': 'practice_001',
        'title': 'Organic Farming',
        'description': 'Using organic methods',
        'steps': ['Step 1', 'Step 2'],
        'original_language': 'en'
    }
    
    mock_aws_clients['table'].get_item.return_value = {'Item': mock_practice}
    
    # Mock translation responses
    mock_aws_clients['translate'].translate_text.return_value = {
        'TranslatedText': 'जैविक खेती'
    }
    
    # Translate to Hindi
    result = best_practice_tools.translate_practice('practice_001', 'hi')
    
    assert result['success'] is True
    assert result['translated'] is True
    assert result['target_language'] == 'hi'
    
    # Verify translate was called
    assert mock_aws_clients['translate'].translate_text.called


def test_get_user_contributions(best_practice_tools, mock_aws_clients):
    """Test getting user contributions"""
    # Mock user's practices
    mock_practices = [
        {
            'practice_id': 'practice_001',
            'user_id': 'test_user_001',
            'title': 'Practice 1',
            'adoption_count': 10,
            'success_count': 8,
            'avg_success_rate': 80,
            'status': 'active'
        },
        {
            'practice_id': 'practice_002',
            'user_id': 'test_user_001',
            'title': 'Practice 2',
            'adoption_count': 5,
            'success_count': 4,
            'avg_success_rate': 80,
            'status': 'active'
        }
    ]
    
    mock_aws_clients['table'].scan.return_value = {'Items': mock_practices}
    
    # Get contributions
    result = best_practice_tools.get_user_contributions('test_user_001')
    
    assert result['success'] is True
    assert result['contributions']['total_practices'] == 2
    assert result['contributions']['total_adoptions'] == 15
    assert result['contributions']['total_successful'] == 12
    assert result['contributions']['most_popular_practice']['practice_id'] == 'practice_001'


def test_unsupported_language(best_practice_tools, mock_aws_clients):
    """Test submitting practice with unsupported language"""
    result = best_practice_tools.submit_practice(
        user_id='test_user_001',
        title='Test',
        description='Test',
        language='unsupported_lang',
        category={},
        steps=['Step 1'],
        expected_benefits={}
    )
    
    assert result['success'] is False
    assert 'Unsupported language' in result['error']


def test_practice_not_found(best_practice_tools, mock_aws_clients):
    """Test getting non-existent practice"""
    mock_aws_clients['table'].get_item.return_value = {}
    
    result = best_practice_tools.get_practice('nonexistent_id')
    
    assert result['success'] is False
    assert 'not found' in result['error'].lower()


def test_unauthorized_feedback(best_practice_tools, mock_aws_clients):
    """Test submitting feedback for someone else's adoption"""
    # Mock adoption by different user
    mock_adoption = {
        'adoption_id': 'adoption_001',
        'practice_id': 'practice_001',
        'user_id': 'other_user',
        'status': 'in_progress'
    }
    
    mock_aws_clients['table'].get_item.return_value = {'Item': mock_adoption}
    
    # Try to submit feedback as different user
    result = best_practice_tools.submit_feedback(
        adoption_id='adoption_001',
        user_id='test_user_001',
        success=True,
        feedback='Test',
        results={}
    )
    
    assert result['success'] is False
    assert 'Unauthorized' in result['error']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
