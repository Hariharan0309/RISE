"""
Unit tests for RISE Multilingual Farmer Forums
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.forum_tools import ForumTools, create_forum_tools


class TestForumTools:
    """Test suite for ForumTools class"""
    
    @pytest.fixture
    def mock_aws_clients(self):
        """Mock AWS clients"""
        with patch('boto3.resource') as mock_dynamodb, \
             patch('boto3.client') as mock_client:
            
            # Mock DynamoDB table
            mock_table = MagicMock()
            mock_dynamodb.return_value.Table.return_value = mock_table
            
            # Mock AWS clients
            mock_translate = MagicMock()
            mock_comprehend = MagicMock()
            mock_bedrock = MagicMock()
            
            mock_client.side_effect = lambda service, **kwargs: {
                'translate': mock_translate,
                'comprehend': mock_comprehend,
                'bedrock-runtime': mock_bedrock
            }.get(service)
            
            yield {
                'dynamodb': mock_dynamodb,
                'table': mock_table,
                'translate': mock_translate,
                'comprehend': mock_comprehend,
                'bedrock': mock_bedrock
            }
    
    @pytest.fixture
    def forum_tools(self, mock_aws_clients):
        """Create ForumTools instance with mocked clients"""
        return ForumTools(region='us-east-1')
    
    def test_create_post_success(self, forum_tools, mock_aws_clients):
        """Test successful post creation"""
        # Mock spam check
        mock_aws_clients['comprehend'].detect_sentiment.return_value = {
            'Sentiment': 'POSITIVE',
            'SentimentScore': {
                'Positive': 0.8,
                'Negative': 0.1,
                'Neutral': 0.1,
                'Mixed': 0.0
            }
        }
        
        # Mock Bedrock toxicity check
        mock_aws_clients['bedrock'].invoke_model.return_value = {
            'body': MagicMock(read=lambda: json.dumps({
                'content': [{
                    'text': '{"is_toxic": false, "toxicity_score": 0.1, "reason": "Content is safe"}'
                }]
            }).encode())
        }
        
        # Mock DynamoDB put_item
        mock_aws_clients['table'].put_item.return_value = {}
        
        # Create post
        result = forum_tools.create_post(
            user_id='test_user_001',
            title='Best practices for wheat cultivation',
            content='I am growing wheat on my farm. Can anyone share best practices?',
            language='en',
            category={'crop_type': 'wheat', 'region': 'north_india', 'method': 'traditional'},
            tags=['wheat', 'best_practices']
        )
        
        # Assertions
        assert result['success'] is True
        assert 'post_id' in result
        assert result['post_id'].startswith('post_')
        assert 'timestamp' in result
        assert mock_aws_clients['table'].put_item.called
    
    def test_create_post_spam_detected(self, forum_tools, mock_aws_clients):
        """Test post creation with spam detection"""
        # Mock spam check - highly negative
        mock_aws_clients['comprehend'].detect_sentiment.return_value = {
            'Sentiment': 'NEGATIVE',
            'SentimentScore': {
                'Positive': 0.1,
                'Negative': 0.9,
                'Neutral': 0.0,
                'Mixed': 0.0
            }
        }
        
        # Mock Bedrock toxicity check - toxic
        mock_aws_clients['bedrock'].invoke_model.return_value = {
            'body': MagicMock(read=lambda: json.dumps({
                'content': [{
                    'text': '{"is_toxic": true, "toxicity_score": 0.9, "reason": "Offensive language detected"}'
                }]
            }).encode())
        }
        
        # Create post
        result = forum_tools.create_post(
            user_id='test_user_001',
            title='Spam post',
            content='This is spam content with offensive language',
            language='en',
            category={'crop_type': 'wheat'},
            tags=[]
        )
        
        # Assertions
        assert result['success'] is False
        assert 'error' in result
        assert 'spam' in result['error'].lower() or 'inappropriate' in result['error'].lower()
    
    def test_create_post_unsupported_language(self, forum_tools, mock_aws_clients):
        """Test post creation with unsupported language"""
        result = forum_tools.create_post(
            user_id='test_user_001',
            title='Test post',
            content='Test content',
            language='fr',  # French - not supported
            category={'crop_type': 'wheat'},
            tags=[]
        )
        
        # Assertions
        assert result['success'] is False
        assert 'Unsupported language' in result['error']
    
    def test_get_posts_success(self, forum_tools, mock_aws_clients):
        """Test getting posts"""
        # Mock DynamoDB scan
        mock_aws_clients['table'].scan.return_value = {
            'Items': [
                {
                    'post_id': 'post_001',
                    'timestamp': 1234567890000,
                    'user_id': 'user_001',
                    'title': 'Test Post 1',
                    'content': 'Content 1',
                    'original_language': 'en',
                    'category': {'crop_type': 'wheat'},
                    'tags': ['wheat'],
                    'status': 'active',
                    'replies_count': 5,
                    'likes_count': 10,
                    'views_count': 50
                },
                {
                    'post_id': 'post_002',
                    'timestamp': 1234567891000,
                    'user_id': 'user_002',
                    'title': 'Test Post 2',
                    'content': 'Content 2',
                    'original_language': 'hi',
                    'category': {'crop_type': 'rice'},
                    'tags': ['rice'],
                    'status': 'active',
                    'replies_count': 3,
                    'likes_count': 7,
                    'views_count': 30
                }
            ]
        }
        
        # Get posts
        result = forum_tools.get_posts(limit=20)
        
        # Assertions
        assert result['success'] is True
        assert len(result['posts']) == 2
        assert result['count'] == 2
        assert result['posts'][0]['post_id'] == 'post_002'  # Most recent first
    
    def test_get_post_success(self, forum_tools, mock_aws_clients):
        """Test getting a single post"""
        # Mock DynamoDB get_item
        mock_aws_clients['table'].get_item.return_value = {
            'Item': {
                'post_id': 'post_001',
                'timestamp': 1234567890000,
                'user_id': 'user_001',
                'title': 'Test Post',
                'content': 'Test content',
                'original_language': 'en',
                'category': {'crop_type': 'wheat'},
                'tags': ['wheat'],
                'status': 'active',
                'views_count': 50
            }
        }
        
        # Mock update_item for view count
        mock_aws_clients['table'].update_item.return_value = {}
        
        # Get post
        result = forum_tools.get_post('post_001')
        
        # Assertions
        assert result['success'] is True
        assert result['post']['post_id'] == 'post_001'
        assert mock_aws_clients['table'].update_item.called  # View count incremented
    
    def test_get_post_not_found(self, forum_tools, mock_aws_clients):
        """Test getting non-existent post"""
        # Mock DynamoDB get_item - no item
        mock_aws_clients['table'].get_item.return_value = {}
        
        # Get post
        result = forum_tools.get_post('nonexistent_post')
        
        # Assertions
        assert result['success'] is False
        assert 'not found' in result['error'].lower()
    
    def test_translate_post_success(self, forum_tools, mock_aws_clients):
        """Test post translation"""
        # Mock get_post
        mock_aws_clients['table'].get_item.return_value = {
            'Item': {
                'post_id': 'post_001',
                'timestamp': 1234567890000,
                'user_id': 'user_001',
                'title': 'गेहूं की खेती',
                'content': 'गेहूं की खेती के लिए सर्वोत्तम प्रथाएं',
                'original_language': 'hi',
                'category': {'crop_type': 'wheat'},
                'tags': ['wheat'],
                'status': 'active',
                'views_count': 50
            }
        }
        
        # Mock update_item for view count
        mock_aws_clients['table'].update_item.return_value = {}
        
        # Mock translate
        mock_aws_clients['translate'].translate_text.side_effect = [
            {'TranslatedText': 'Wheat Cultivation'},
            {'TranslatedText': 'Best practices for wheat cultivation'}
        ]
        
        # Translate post
        result = forum_tools.translate_post('post_001', 'en')
        
        # Assertions
        assert result['success'] is True
        assert result['translated'] is True
        assert result['post']['title'] == 'Wheat Cultivation'
        assert result['post']['content'] == 'Best practices for wheat cultivation'
        assert result['post']['translated_to'] == 'en'
        assert result['source_language'] == 'hi'
    
    def test_translate_post_same_language(self, forum_tools, mock_aws_clients):
        """Test translating post to same language"""
        # Mock get_post
        mock_aws_clients['table'].get_item.return_value = {
            'Item': {
                'post_id': 'post_001',
                'timestamp': 1234567890000,
                'user_id': 'user_001',
                'title': 'Wheat Cultivation',
                'content': 'Best practices for wheat',
                'original_language': 'en',
                'category': {'crop_type': 'wheat'},
                'tags': ['wheat'],
                'status': 'active',
                'views_count': 50
            }
        }
        
        # Mock update_item for view count
        mock_aws_clients['table'].update_item.return_value = {}
        
        # Translate post to same language
        result = forum_tools.translate_post('post_001', 'en')
        
        # Assertions
        assert result['success'] is True
        assert result['translated'] is False  # No translation needed
        assert result['post']['title'] == 'Wheat Cultivation'
    
    def test_add_reply_success(self, forum_tools, mock_aws_clients):
        """Test adding a reply"""
        # Mock spam check
        mock_aws_clients['comprehend'].detect_sentiment.return_value = {
            'Sentiment': 'POSITIVE',
            'SentimentScore': {
                'Positive': 0.7,
                'Negative': 0.1,
                'Neutral': 0.2,
                'Mixed': 0.0
            }
        }
        
        # Mock Bedrock toxicity check
        mock_aws_clients['bedrock'].invoke_model.return_value = {
            'body': MagicMock(read=lambda: json.dumps({
                'content': [{
                    'text': '{"is_toxic": false, "toxicity_score": 0.1, "reason": "Content is safe"}'
                }]
            }).encode())
        }
        
        # Mock update_item
        mock_aws_clients['table'].update_item.return_value = {}
        
        # Add reply
        result = forum_tools.add_reply(
            post_id='post_001',
            user_id='user_002',
            content='Great advice! Thank you for sharing.',
            language='en'
        )
        
        # Assertions
        assert result['success'] is True
        assert 'reply_id' in result
        assert result['reply_id'].startswith('reply_')
        assert mock_aws_clients['table'].update_item.called
    
    def test_like_post_success(self, forum_tools, mock_aws_clients):
        """Test liking a post"""
        # Mock update_item
        mock_aws_clients['table'].update_item.return_value = {}
        
        # Like post
        result = forum_tools.like_post('post_001', 'user_002')
        
        # Assertions
        assert result['success'] is True
        assert 'liked successfully' in result['message'].lower()
        assert mock_aws_clients['table'].update_item.called
    
    def test_search_posts_success(self, forum_tools, mock_aws_clients):
        """Test searching posts"""
        # Mock DynamoDB scan
        mock_aws_clients['table'].scan.return_value = {
            'Items': [
                {
                    'post_id': 'post_001',
                    'timestamp': 1234567890000,
                    'user_id': 'user_001',
                    'title': 'Wheat cultivation tips',
                    'content': 'Best practices for growing wheat',
                    'original_language': 'en',
                    'category': {'crop_type': 'wheat'},
                    'tags': ['wheat'],
                    'status': 'active'
                },
                {
                    'post_id': 'post_002',
                    'timestamp': 1234567891000,
                    'user_id': 'user_002',
                    'title': 'Rice farming guide',
                    'content': 'How to grow rice efficiently',
                    'original_language': 'en',
                    'category': {'crop_type': 'rice'},
                    'tags': ['rice'],
                    'status': 'active'
                }
            ]
        }
        
        # Search posts
        result = forum_tools.search_posts('wheat', limit=20)
        
        # Assertions
        assert result['success'] is True
        assert len(result['posts']) == 1  # Only wheat post
        assert result['posts'][0]['post_id'] == 'post_001'
        assert result['query'] == 'wheat'
    
    def test_get_user_reputation_success(self, forum_tools, mock_aws_clients):
        """Test getting user reputation"""
        # Mock DynamoDB scan
        mock_aws_clients['table'].scan.return_value = {
            'Items': [
                {
                    'post_id': 'post_001',
                    'user_id': 'user_001',
                    'likes_count': 10,
                    'replies_count': 5,
                    'sentiment_score': 0.7,
                    'status': 'active'
                },
                {
                    'post_id': 'post_002',
                    'user_id': 'user_001',
                    'likes_count': 15,
                    'replies_count': 8,
                    'sentiment_score': 0.8,
                    'status': 'active'
                }
            ]
        }
        
        # Get reputation
        result = forum_tools.get_user_reputation('user_001')
        
        # Assertions
        assert result['success'] is True
        assert result['user_id'] == 'user_001'
        assert result['reputation_score'] > 0
        assert result['badge'] in ['newcomer', 'contributor', 'experienced', 'expert']
        assert 'metrics' in result
        assert result['metrics']['total_posts'] == 2
        assert result['metrics']['total_likes'] == 25
        assert result['metrics']['total_replies'] == 13
    
    def test_factory_function(self):
        """Test factory function"""
        with patch('boto3.resource'), patch('boto3.client'):
            tools = create_forum_tools(region='us-west-2')
            assert isinstance(tools, ForumTools)
            assert tools.region == 'us-west-2'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


class TestExpertRecognitionSystem:
    """Test suite for Expert Recognition System"""
    
    @pytest.fixture
    def mock_aws_clients(self):
        """Mock AWS clients"""
        with patch('boto3.resource') as mock_dynamodb, \
             patch('boto3.client') as mock_client:
            
            # Mock DynamoDB table
            mock_table = MagicMock()
            mock_dynamodb.return_value.Table.return_value = mock_table
            
            # Mock AWS clients
            mock_translate = MagicMock()
            mock_comprehend = MagicMock()
            mock_bedrock = MagicMock()
            
            mock_client.side_effect = lambda service, **kwargs: {
                'translate': mock_translate,
                'comprehend': mock_comprehend,
                'bedrock-runtime': mock_bedrock
            }.get(service)
            
            yield {
                'dynamodb': mock_dynamodb,
                'table': mock_table,
                'translate': mock_translate,
                'comprehend': mock_comprehend,
                'bedrock': mock_bedrock
            }
    
    @pytest.fixture
    def forum_tools(self, mock_aws_clients):
        """Create ForumTools instance with mocked clients"""
        return ForumTools(region='us-east-1')
    
    @pytest.fixture
    def sample_posts(self):
        """Sample posts for testing"""
        return [
            {
                'post_id': 'post_001',
                'user_id': 'expert_user',
                'title': 'Wheat cultivation tips',
                'content': 'Here are some tips...',
                'timestamp': 1700000000000,
                'likes_count': 15,
                'replies_count': 8,
                'views_count': 100,
                'sentiment_score': 0.7,
                'is_solution': True,
                'category': {'crop_type': 'wheat'},
                'status': 'active'
            },
            {
                'post_id': 'post_002',
                'user_id': 'expert_user',
                'title': 'Rice farming guide',
                'content': 'Rice farming best practices...',
                'timestamp': 1700100000000,
                'likes_count': 12,
                'replies_count': 6,
                'views_count': 80,
                'sentiment_score': 0.6,
                'is_solution': True,
                'category': {'crop_type': 'rice'},
                'status': 'active'
            },
            {
                'post_id': 'post_003',
                'user_id': 'expert_user',
                'title': 'Pest control methods',
                'content': 'Effective pest control...',
                'timestamp': 1700200000000,
                'likes_count': 20,
                'replies_count': 10,
                'views_count': 150,
                'sentiment_score': 0.8,
                'is_solution': False,
                'category': {'crop_type': 'wheat'},
                'status': 'active'
            },
            {
                'post_id': 'post_004',
                'user_id': 'expert_user',
                'title': 'Wheat irrigation tips',
                'content': 'Best irrigation practices...',
                'timestamp': 1700300000000,
                'likes_count': 10,
                'replies_count': 5,
                'views_count': 75,
                'sentiment_score': 0.6,
                'is_solution': False,
                'category': {'crop_type': 'wheat'},
                'status': 'active'
            }
        ]
    
    def test_get_user_reputation_expert_level(self, forum_tools, mock_aws_clients, sample_posts):
        """Test reputation calculation for expert-level user"""
        # Mock DynamoDB scan to return sample posts
        mock_aws_clients['table'].scan.return_value = {
            'Items': sample_posts
        }
        
        # Get reputation
        result = forum_tools.get_user_reputation('expert_user')
        
        # Assertions
        assert result['success'] is True
        assert result['user_id'] == 'expert_user'
        assert result['reputation_score'] > 0
        assert 'badge' in result
        assert 'badge_emoji' in result
        assert 'badge_description' in result
        assert 'is_verified_expert' in result
        assert 'expertise_areas' in result
        assert 'metrics' in result
        assert 'achievements' in result
        
        # Check metrics
        metrics = result['metrics']
        assert metrics['total_posts'] == 4
        assert metrics['total_likes'] == 57
        assert metrics['total_replies'] == 29
        assert metrics['verified_solutions'] == 2
        assert metrics['helpful_answers'] > 0
        
        # Check expertise areas (should have wheat with 3 posts)
        assert len(result['expertise_areas']) > 0
        assert any(area['area'] == 'wheat' for area in result['expertise_areas'])
    
    def test_get_user_reputation_beginner(self, forum_tools, mock_aws_clients):
        """Test reputation calculation for beginner user"""
        # Mock DynamoDB scan to return no posts
        mock_aws_clients['table'].scan.return_value = {
            'Items': []
        }
        
        # Get reputation
        result = forum_tools.get_user_reputation('new_user')
        
        # Assertions
        assert result['success'] is True
        assert result['badge'] == 'beginner'
        assert result['badge_emoji'] == '🌱'
        assert result['is_verified_expert'] is False
        assert result['reputation_score'] == 0
        assert result['metrics']['total_posts'] == 0
    
    def test_badge_determination_master_farmer(self, forum_tools, mock_aws_clients):
        """Test badge determination for master farmer level"""
        # Create posts that qualify for master farmer
        master_posts = []
        for i in range(60):
            master_posts.append({
                'post_id': f'post_{i:03d}',
                'user_id': 'master_user',
                'title': f'Expert advice {i}',
                'content': 'Detailed expert content...',
                'timestamp': 1700000000000 + (i * 86400000),  # One per day
                'likes_count': 10,
                'replies_count': 5,
                'views_count': 100,
                'sentiment_score': 0.8,
                'is_solution': i < 25,  # 25 verified solutions
                'category': {'crop_type': 'wheat' if i % 2 == 0 else 'rice'},
                'status': 'active'
            })
        
        mock_aws_clients['table'].scan.return_value = {
            'Items': master_posts
        }
        
        result = forum_tools.get_user_reputation('master_user')
        
        # Should be master farmer or expert
        assert result['success'] is True
        assert result['badge'] in ['master_farmer', 'expert']
        assert result['is_verified_expert'] is True
        assert result['badge_emoji'] in ['🏆', '🌟']
    
    def test_expertise_areas_calculation(self, forum_tools, mock_aws_clients):
        """Test expertise areas calculation"""
        # Create posts in multiple areas
        diverse_posts = [
            {
                'post_id': f'post_wheat_{i}',
                'user_id': 'diverse_user',
                'title': f'Wheat post {i}',
                'content': 'Wheat content',
                'timestamp': 1700000000000 + (i * 1000000),
                'likes_count': 5,
                'replies_count': 3,
                'sentiment_score': 0.6,
                'category': {'crop_type': 'wheat'},
                'status': 'active'
            }
            for i in range(5)
        ] + [
            {
                'post_id': f'post_rice_{i}',
                'user_id': 'diverse_user',
                'title': f'Rice post {i}',
                'content': 'Rice content',
                'timestamp': 1700000000000 + (i * 1000000),
                'likes_count': 4,
                'replies_count': 2,
                'sentiment_score': 0.5,
                'category': {'crop_type': 'rice'},
                'status': 'active'
            }
            for i in range(4)
        ]
        
        mock_aws_clients['table'].scan.return_value = {
            'Items': diverse_posts
        }
        
        result = forum_tools.get_user_reputation('diverse_user')
        
        # Check expertise areas
        assert result['success'] is True
        assert len(result['expertise_areas']) == 2
        
        # Wheat should be first (more posts)
        assert result['expertise_areas'][0]['area'] == 'wheat'
        assert result['expertise_areas'][0]['posts_count'] == 5
        
        # Rice should be second
        assert result['expertise_areas'][1]['area'] == 'rice'
        assert result['expertise_areas'][1]['posts_count'] == 4
    
    def test_get_top_experts(self, forum_tools, mock_aws_clients, sample_posts):
        """Test getting top experts"""
        # Mock scan to return posts from multiple users
        all_posts = sample_posts + [
            {
                'post_id': 'post_004',
                'user_id': 'another_expert',
                'title': 'Cotton farming',
                'content': 'Cotton tips...',
                'timestamp': 1700300000000,
                'likes_count': 25,
                'replies_count': 12,
                'views_count': 200,
                'sentiment_score': 0.9,
                'is_solution': True,
                'category': {'crop_type': 'cotton'},
                'status': 'active'
            }
        ]
        
        mock_aws_clients['table'].scan.return_value = {
            'Items': all_posts
        }
        
        result = forum_tools.get_top_experts(limit=10)
        
        # Assertions
        assert result['success'] is True
        assert 'experts' in result
        assert 'count' in result
        assert len(result['experts']) <= 10
        
        # Experts should be sorted by reputation
        if len(result['experts']) > 1:
            for i in range(len(result['experts']) - 1):
                assert result['experts'][i]['reputation_score'] >= result['experts'][i+1]['reputation_score']
    
    def test_get_top_experts_filtered_by_area(self, forum_tools, mock_aws_clients, sample_posts):
        """Test getting top experts filtered by expertise area"""
        mock_aws_clients['table'].scan.return_value = {
            'Items': sample_posts
        }
        
        result = forum_tools.get_top_experts(limit=10, expertise_area='wheat')
        
        # Assertions
        assert result['success'] is True
        assert result['expertise_filter'] == 'wheat'
        
        # All returned experts should have wheat expertise
        for expert in result['experts']:
            has_wheat = any(
                area['area'] == 'wheat' 
                for area in expert['expertise_areas']
            )
            assert has_wheat
    
    def test_mark_post_as_solution(self, forum_tools, mock_aws_clients):
        """Test marking a post as verified solution"""
        mock_aws_clients['table'].update_item.return_value = {}
        
        result = forum_tools.mark_post_as_solution('post_123', 'user_456')
        
        # Assertions
        assert result['success'] is True
        assert 'message' in result
        assert mock_aws_clients['table'].update_item.called
        
        # Check update expression
        call_args = mock_aws_clients['table'].update_item.call_args
        assert 'is_solution' in str(call_args)
    
    def test_get_expert_directory(self, forum_tools, mock_aws_clients, sample_posts):
        """Test getting expert directory"""
        # Create posts from multiple expert users
        directory_posts = sample_posts + [
            {
                'post_id': f'post_expert2_{i}',
                'user_id': 'expert_user_2',
                'title': f'Expert post {i}',
                'content': 'Expert content',
                'timestamp': 1700000000000 + (i * 1000000),
                'likes_count': 8,
                'replies_count': 4,
                'sentiment_score': 0.7,
                'is_solution': i < 2,
                'category': {'crop_type': 'rice'},
                'status': 'active'
            }
            for i in range(5)
        ]
        
        mock_aws_clients['table'].scan.return_value = {
            'Items': directory_posts
        }
        
        result = forum_tools.get_expert_directory()
        
        # Assertions
        assert result['success'] is True
        assert 'directory' in result
        
        directory = result['directory']
        assert 'verified_experts' in directory
        assert 'by_expertise' in directory
        assert 'total_experts' in directory
        assert 'total_verified' in directory
        
        # Check expertise organization
        assert 'wheat' in directory['by_expertise'] or 'rice' in directory['by_expertise']
    
    def test_achievements_unlocking(self, forum_tools, mock_aws_clients):
        """Test achievement unlocking based on contributions"""
        # Create posts that unlock multiple achievements
        achievement_posts = [
            {
                'post_id': f'post_{i:03d}',
                'user_id': 'achiever_user',
                'title': f'Post {i}',
                'content': 'Content',
                'timestamp': 1700000000000 + (i * 1000000),
                'likes_count': 6 if i < 15 else 3,  # 15 helpful answers
                'replies_count': 3,
                'sentiment_score': 0.5 if i < 15 else 0.2,
                'is_solution': i < 5,  # 5 verified solutions
                'category': {'crop_type': ['wheat', 'rice', 'cotton'][i % 3]},
                'status': 'active'
            }
            for i in range(20)
        ]
        
        mock_aws_clients['table'].scan.return_value = {
            'Items': achievement_posts
        }
        
        result = forum_tools.get_user_reputation('achiever_user')
        
        # Check achievements
        assert result['success'] is True
        assert len(result['achievements']) > 0
        
        # Should have posting milestone
        achievement_titles = [a['title'] for a in result['achievements']]
        assert any('Active Member' in title or 'Prolific' in title for title in achievement_titles)
    
    def test_consistency_score_calculation(self, forum_tools, mock_aws_clients):
        """Test consistency score calculation"""
        # Create posts with regular intervals (one per week)
        consistent_posts = [
            {
                'post_id': f'post_{i:03d}',
                'user_id': 'consistent_user',
                'title': f'Weekly post {i}',
                'content': 'Regular content',
                'timestamp': 1700000000000 + (i * 7 * 86400000),  # One per week
                'likes_count': 5,
                'replies_count': 2,
                'sentiment_score': 0.6,
                'category': {'crop_type': 'wheat'},
                'status': 'active'
            }
            for i in range(10)
        ]
        
        mock_aws_clients['table'].scan.return_value = {
            'Items': consistent_posts
        }
        
        result = forum_tools.get_user_reputation('consistent_user')
        
        # Check consistency score
        assert result['success'] is True
        assert 'consistency_score' in result['metrics']
        # Weekly posting should get high consistency score
        assert result['metrics']['consistency_score'] >= 8.0
    
    def test_reputation_error_handling(self, forum_tools, mock_aws_clients):
        """Test error handling in reputation calculation"""
        # Mock DynamoDB to raise exception
        mock_aws_clients['table'].scan.side_effect = Exception('DynamoDB error')
        
        result = forum_tools.get_user_reputation('error_user')
        
        # Should return error gracefully
        assert result['success'] is False
        assert 'error' in result
    
    def test_expertise_level_calculation(self, forum_tools, mock_aws_clients, sample_posts):
        """Test expertise level percentage calculation"""
        mock_aws_clients['table'].scan.return_value = {
            'Items': sample_posts
        }
        
        result = forum_tools.get_user_reputation('expert_user')
        
        # Check expertise level
        assert result['success'] is True
        assert 'expertise_level' in result
        assert 0 <= result['expertise_level'] <= 100
        assert isinstance(result['expertise_level'], int)


def test_create_forum_tools():
    """Test factory function for creating forum tools"""
    with patch('boto3.resource'), patch('boto3.client'):
        tools = create_forum_tools(region='us-west-2')
        assert tools is not None
        assert isinstance(tools, ForumTools)
        assert tools.region == 'us-west-2'
