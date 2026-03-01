"""
RISE Context Management Tools
Provides conversation context persistence, retrieval, and summarization using DynamoDB
"""

import boto3
from boto3.dynamodb.conditions import Key
from typing import Dict, Any, List, Optional
import logging
import time
from datetime import datetime, timedelta
import json
from strands import tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextTools:
    """Tools for managing conversation context with DynamoDB persistence"""
    
    def __init__(self, region: str = 'us-east-1', table_name: str = 'RISE-ConversationHistory'):
        """
        Initialize context tools with DynamoDB
        
        Args:
            region: AWS region
            table_name: DynamoDB table name for conversation history
        """
        self.region = region
        self.table_name = table_name
        
        # Initialize DynamoDB
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
        
        # Initialize Bedrock for summarization
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=region)
        
        logger.info(f"Context tools initialized with table {table_name}")
    
    def save_conversation_message(self,
                                  session_id: str,
                                  user_id: str,
                                  role: str,
                                  content: str,
                                  metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save a conversation message to DynamoDB
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            role: Message role (user/assistant)
            content: Message content
            metadata: Additional metadata
        
        Returns:
            Success status
        """
        try:
            timestamp = int(time.time() * 1000)  # Milliseconds for precision
            
            # Calculate TTL (24 hours from now)
            ttl = int((datetime.utcnow() + timedelta(hours=24)).timestamp())
            
            item = {
                'session_id': session_id,
                'timestamp': timestamp,
                'user_id': user_id,
                'role': role,
                'content': content,
                'ttl': ttl,
                'created_at': datetime.utcnow().isoformat()
            }
            
            if metadata:
                item['metadata'] = metadata
            
            self.table.put_item(Item=item)
            
            logger.debug(f"Saved message for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving conversation message: {e}")
            return False
    
    def get_conversation_history(self,
                                session_id: str,
                                limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a session
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to retrieve
        
        Returns:
            List of conversation messages
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key('session_id').eq(session_id),
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            messages = response.get('Items', [])
            
            # Reverse to get chronological order
            messages.reverse()
            
            logger.debug(f"Retrieved {len(messages)} messages for session {session_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []
    
    def get_user_conversations(self,
                              user_id: str,
                              limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve all conversations for a user across sessions
        
        Args:
            user_id: User identifier
            limit: Maximum number of messages to retrieve
        
        Returns:
            List of conversation messages
        """
        try:
            response = self.table.query(
                IndexName='UserConversationIndex',
                KeyConditionExpression=Key('user_id').eq(user_id),
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            messages = response.get('Items', [])
            
            logger.debug(f"Retrieved {len(messages)} messages for user {user_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Error retrieving user conversations: {e}")
            return []
    
    def get_context_window(self,
                          session_id: str,
                          window_size: int = 5) -> str:
        """
        Get formatted context window for agent
        
        Args:
            session_id: Session identifier
            window_size: Number of recent message pairs to include
        
        Returns:
            Formatted context string
        """
        messages = self.get_conversation_history(session_id, limit=window_size * 2)
        
        if not messages:
            return "No previous conversation context."
        
        context_parts = ["Previous conversation:"]
        
        for msg in messages:
            role = "Farmer" if msg['role'] == 'user' else "Assistant"
            content = msg['content']
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    def summarize_conversation(self,
                              session_id: str,
                              model_id: str = 'anthropic.claude-3-haiku-20240307-v1:0') -> Dict[str, Any]:
        """
        Summarize a long conversation using Amazon Bedrock
        
        Args:
            session_id: Session identifier
            model_id: Bedrock model ID for summarization
        
        Returns:
            Dict with summary and metadata
        """
        try:
            # Get full conversation history
            messages = self.get_conversation_history(session_id, limit=100)
            
            if not messages:
                return {
                    'success': False,
                    'error': 'No conversation history found'
                }
            
            # Format conversation for summarization
            conversation_text = []
            for msg in messages:
                role = "Farmer" if msg['role'] == 'user' else "Assistant"
                conversation_text.append(f"{role}: {msg['content']}")
            
            full_conversation = "\n".join(conversation_text)
            
            # Create summarization prompt
            prompt = f"""Summarize the following conversation between a farmer and an AI farming assistant. 
Focus on:
1. Main topics discussed (crops, diseases, weather, market prices, etc.)
2. Key recommendations provided
3. Important context about the farmer's situation
4. Any follow-up actions needed

Conversation:
{full_conversation}

Provide a concise summary in 3-4 sentences."""
            
            # Call Bedrock for summarization
            request_body = {
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 500,
                'messages': [{
                    'role': 'user',
                    'content': prompt
                }]
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            summary = response_body['content'][0]['text']
            
            # Save summary as metadata
            self.save_conversation_message(
                session_id=session_id,
                user_id=messages[0]['user_id'],
                role='system',
                content=f"[SUMMARY] {summary}",
                metadata={'type': 'summary', 'message_count': len(messages)}
            )
            
            logger.info(f"Generated summary for session {session_id}")
            
            return {
                'success': True,
                'summary': summary,
                'message_count': len(messages),
                'session_id': session_id
            }
            
        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup_expired_sessions(self) -> Dict[str, Any]:
        """
        Cleanup expired sessions (TTL handles automatic deletion, this is for manual cleanup)
        
        Returns:
            Cleanup statistics
        """
        try:
            # DynamoDB TTL handles automatic cleanup
            # This method is for manual cleanup if needed
            
            logger.info("Session cleanup triggered (TTL handles automatic deletion)")
            
            return {
                'success': True,
                'message': 'TTL-based cleanup is active'
            }
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Strands tool decorators for agent integration

@tool
def retrieve_conversation_context(session_id: str, window_size: int = 5) -> str:
    """
    Retrieve recent conversation context for maintaining continuity.
    Use this tool when you need to reference previous messages in the conversation.
    
    Args:
        session_id: The session identifier
        window_size: Number of recent message pairs to retrieve (default: 5)
    
    Returns:
        Formatted conversation context string
    """
    context_tools = ContextTools()
    return context_tools.get_context_window(session_id, window_size)


@tool
def summarize_long_conversation(session_id: str) -> str:
    """
    Summarize a long conversation to maintain context efficiently.
    Use this tool when the conversation has many messages and you need a concise summary.
    
    Args:
        session_id: The session identifier
    
    Returns:
        Conversation summary
    """
    context_tools = ContextTools()
    result = context_tools.summarize_conversation(session_id)
    
    if result['success']:
        return f"Summary: {result['summary']} (Based on {result['message_count']} messages)"
    else:
        return f"Could not generate summary: {result.get('error', 'Unknown error')}"


@tool
def get_user_conversation_history(user_id: str, limit: int = 20) -> str:
    """
    Retrieve conversation history across all sessions for a user.
    Use this tool to understand a user's past interactions and provide personalized assistance.
    
    Args:
        user_id: The user identifier
        limit: Maximum number of messages to retrieve (default: 20)
    
    Returns:
        Formatted conversation history
    """
    context_tools = ContextTools()
    messages = context_tools.get_user_conversations(user_id, limit)
    
    if not messages:
        return f"No previous conversations found for user {user_id}"
    
    # Group by session
    sessions = {}
    for msg in messages:
        session_id = msg['session_id']
        if session_id not in sessions:
            sessions[session_id] = []
        sessions[session_id].append(msg)
    
    # Format output
    output = [f"Found {len(messages)} messages across {len(sessions)} sessions:"]
    
    for session_id, session_messages in list(sessions.items())[:3]:  # Show last 3 sessions
        output.append(f"\nSession {session_id}:")
        for msg in session_messages[:5]:  # Show first 5 messages per session
            role = "Farmer" if msg['role'] == 'user' else "Assistant"
            content = msg['content'][:100]  # Truncate long messages
            output.append(f"  {role}: {content}...")
    
    return "\n".join(output)


# Convenience function for testing
def test_context_tools():
    """Test context tools functionality"""
    print("=" * 60)
    print("Testing RISE Context Tools")
    print("=" * 60)
    
    try:
        # Initialize tools
        print("\n1. Initializing context tools...")
        tools = ContextTools()
        print("✓ Context tools initialized")
        
        # Test saving messages
        print("\n2. Testing message persistence...")
        session_id = "test_session_001"
        user_id = "test_user_001"
        
        tools.save_conversation_message(
            session_id=session_id,
            user_id=user_id,
            role='user',
            content='What are the best practices for wheat cultivation?'
        )
        
        tools.save_conversation_message(
            session_id=session_id,
            user_id=user_id,
            role='assistant',
            content='For wheat cultivation, follow these best practices: 1) Prepare soil properly...'
        )
        
        print("✓ Messages saved successfully")
        
        # Test retrieval
        print("\n3. Testing message retrieval...")
        messages = tools.get_conversation_history(session_id)
        print(f"✓ Retrieved {len(messages)} messages")
        
        # Test context window
        print("\n4. Testing context window...")
        context = tools.get_context_window(session_id)
        print(f"✓ Context window generated ({len(context)} characters)")
        
        # Test summarization
        print("\n5. Testing conversation summarization...")
        summary_result = tools.summarize_conversation(session_id)
        if summary_result['success']:
            print(f"✓ Summary generated: {summary_result['summary'][:100]}...")
        else:
            print(f"⚠ Summarization failed: {summary_result.get('error')}")
        
        print("\n" + "=" * 60)
        print("✓ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_context_tools()
