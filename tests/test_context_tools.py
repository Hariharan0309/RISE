"""
Unit tests for RISE Context Management Tools
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.context_tools import ContextTools
import time
from datetime import datetime


class TestContextTools(unittest.TestCase):
    """Test cases for context management tools"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock DynamoDB
        self.mock_dynamodb = Mock()
        self.mock_table = Mock()
        self.mock_dynamodb.Table.return_value = self.mock_table
        
        # Mock Bedrock
        self.mock_bedrock = Mock()
        
        # Patch boto3 clients
        self.dynamodb_patcher = patch('boto3.resource', return_value=self.mock_dynamodb)
        self.bedrock_patcher = patch('boto3.client', return_value=self.mock_bedrock)
        
        self.dynamodb_patcher.start()
        self.bedrock_patcher.start()
        
        # Create context tools instance
        self.context_tools = ContextTools(region='us-east-1')
    
    def tearDown(self):
        """Clean up after tests"""
        self.dynamodb_patcher.stop()
        self.bedrock_patcher.stop()
    
    def test_initialization(self):
        """Test context tools initialization"""
        self.assertIsNotNone(self.context_tools)
        self.assertEqual(self.context_tools.region, 'us-east-1')
        self.assertEqual(self.context_tools.table_name, 'RISE-ConversationHistory')
    
    def test_save_conversation_message(self):
        """Test saving a conversation message"""
        # Mock successful put_item
        self.mock_table.put_item.return_value = {}
        
        result = self.context_tools.save_conversation_message(
            session_id='test_session_001',
            user_id='test_user_001',
            role='user',
            content='What are the best practices for wheat cultivation?',
            metadata={'crop': 'wheat'}
        )
        
        self.assertTrue(result)
        self.mock_table.put_item.assert_called_once()
        
        # Verify the item structure
        call_args = self.mock_table.put_item.call_args
        item = call_args[1]['Item']
        
        self.assertEqual(item['session_id'], 'test_session_001')
        self.assertEqual(item['user_id'], 'test_user_001')
        self.assertEqual(item['role'], 'user')
        self.assertEqual(item['content'], 'What are the best practices for wheat cultivation?')
        self.assertIn('timestamp', item)
        self.assertIn('ttl', item)
        self.assertIn('metadata', item)
    
    def test_save_conversation_message_error(self):
        """Test error handling when saving message fails"""
        # Mock failed put_item
        self.mock_table.put_item.side_effect = Exception("DynamoDB error")
        
        result = self.context_tools.save_conversation_message(
            session_id='test_session_001',
            user_id='test_user_001',
            role='user',
            content='Test message'
        )
        
        self.assertFalse(result)
    
    def test_get_conversation_history(self):
        """Test retrieving conversation history"""
        # Mock query response (DynamoDB returns in reverse order, then we reverse it)
        mock_messages = [
            {
                'session_id': 'test_session_001',
                'timestamp': int(time.time() * 1000) - 1000,
                'user_id': 'test_user_001',
                'role': 'assistant',
                'content': 'Based on your soil type, I recommend wheat or rice.'
            },
            {
                'session_id': 'test_session_001',
                'timestamp': int(time.time() * 1000) - 2000,
                'user_id': 'test_user_001',
                'role': 'user',
                'content': 'What crops should I plant?'
            }
        ]
        
        self.mock_table.query.return_value = {'Items': mock_messages}
        
        messages = self.context_tools.get_conversation_history('test_session_001', limit=10)
        
        self.assertEqual(len(messages), 2)
        # After reversal, user message should be first
        self.assertEqual(messages[0]['role'], 'user')
        self.assertEqual(messages[1]['role'], 'assistant')
        
        # Verify query was called correctly
        self.mock_table.query.assert_called_once()
    
    def test_get_conversation_history_empty(self):
        """Test retrieving conversation history when no messages exist"""
        self.mock_table.query.return_value = {'Items': []}
        
        messages = self.context_tools.get_conversation_history('nonexistent_session')
        
        self.assertEqual(len(messages), 0)
    
    def test_get_user_conversations(self):
        """Test retrieving all conversations for a user"""
        mock_messages = [
            {
                'session_id': 'session_001',
                'timestamp': int(time.time() * 1000),
                'user_id': 'test_user_001',
                'role': 'user',
                'content': 'Question 1'
            },
            {
                'session_id': 'session_002',
                'timestamp': int(time.time() * 1000),
                'user_id': 'test_user_001',
                'role': 'user',
                'content': 'Question 2'
            }
        ]
        
        self.mock_table.query.return_value = {'Items': mock_messages}
        
        messages = self.context_tools.get_user_conversations('test_user_001', limit=50)
        
        self.assertEqual(len(messages), 2)
        self.mock_table.query.assert_called_once()
    
    def test_get_context_window(self):
        """Test getting formatted context window"""
        mock_messages = [
            {
                'session_id': 'test_session_001',
                'timestamp': int(time.time() * 1000) - 2000,
                'user_id': 'test_user_001',
                'role': 'user',
                'content': 'What is the best fertilizer for wheat?'
            },
            {
                'session_id': 'test_session_001',
                'timestamp': int(time.time() * 1000) - 1000,
                'user_id': 'test_user_001',
                'role': 'assistant',
                'content': 'For wheat, I recommend NPK 20-20-20 fertilizer.'
            }
        ]
        
        self.mock_table.query.return_value = {'Items': mock_messages}
        
        context = self.context_tools.get_context_window('test_session_001', window_size=5)
        
        self.assertIn('Previous conversation:', context)
        self.assertIn('Farmer:', context)
        self.assertIn('Assistant:', context)
        self.assertIn('What is the best fertilizer for wheat?', context)
        self.assertIn('NPK 20-20-20 fertilizer', context)
    
    def test_get_context_window_empty(self):
        """Test getting context window when no history exists"""
        self.mock_table.query.return_value = {'Items': []}
        
        context = self.context_tools.get_context_window('test_session_001')
        
        self.assertEqual(context, "No previous conversation context.")
    
    def test_summarize_conversation(self):
        """Test conversation summarization"""
        # Mock conversation history
        mock_messages = [
            {
                'session_id': 'test_session_001',
                'timestamp': int(time.time() * 1000) - 3000,
                'user_id': 'test_user_001',
                'role': 'user',
                'content': 'What crops should I plant?'
            },
            {
                'session_id': 'test_session_001',
                'timestamp': int(time.time() * 1000) - 2000,
                'user_id': 'test_user_001',
                'role': 'assistant',
                'content': 'I recommend wheat or rice based on your soil.'
            },
            {
                'session_id': 'test_session_001',
                'timestamp': int(time.time() * 1000) - 1000,
                'user_id': 'test_user_001',
                'role': 'user',
                'content': 'What fertilizer should I use for wheat?'
            }
        ]
        
        self.mock_table.query.return_value = {'Items': mock_messages}
        
        # Mock Bedrock response
        mock_bedrock_response = {
            'body': MagicMock()
        }
        mock_bedrock_response['body'].read.return_value = b'{"content": [{"text": "The farmer asked about crop selection and fertilizer recommendations for wheat. The assistant suggested wheat or rice based on soil conditions."}]}'
        
        self.mock_bedrock.invoke_model.return_value = mock_bedrock_response
        
        # Mock save_conversation_message for summary
        self.mock_table.put_item.return_value = {}
        
        result = self.context_tools.summarize_conversation('test_session_001')
        
        self.assertTrue(result['success'])
        self.assertIn('summary', result)
        self.assertEqual(result['message_count'], 3)
        self.assertEqual(result['session_id'], 'test_session_001')
    
    def test_summarize_conversation_no_history(self):
        """Test summarization when no conversation history exists"""
        self.mock_table.query.return_value = {'Items': []}
        
        result = self.context_tools.summarize_conversation('test_session_001')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions"""
        result = self.context_tools.cleanup_expired_sessions()
        
        self.assertTrue(result['success'])
        self.assertIn('message', result)


class TestContextToolsIntegration(unittest.TestCase):
    """Integration tests for context tools (require AWS credentials)"""
    
    @unittest.skip("Requires AWS credentials and DynamoDB table")
    def test_full_conversation_flow(self):
        """Test complete conversation flow with real DynamoDB"""
        context_tools = ContextTools(region='us-east-1')
        
        session_id = 'integration_test_session'
        user_id = 'integration_test_user'
        
        # Save messages
        context_tools.save_conversation_message(
            session_id=session_id,
            user_id=user_id,
            role='user',
            content='What are the best practices for wheat cultivation?'
        )
        
        context_tools.save_conversation_message(
            session_id=session_id,
            user_id=user_id,
            role='assistant',
            content='For wheat cultivation, follow these best practices...'
        )
        
        # Retrieve history
        messages = context_tools.get_conversation_history(session_id)
        self.assertEqual(len(messages), 2)
        
        # Get context window
        context = context_tools.get_context_window(session_id)
        self.assertIn('Previous conversation:', context)
        
        # Summarize
        summary_result = context_tools.summarize_conversation(session_id)
        self.assertTrue(summary_result['success'])


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
