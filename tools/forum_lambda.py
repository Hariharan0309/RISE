"""
RISE Multilingual Farmer Forums Lambda Function
AWS Lambda handler for forum operations with translation and moderation
"""

import json
import logging
import os
from typing import Dict, Any
from forum_tools import ForumTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize forum tools
forum_tools = ForumTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for forum requests
    
    Event structure:
    {
        "action": "create_post" | "get_posts" | "get_post" | "translate_post" | 
                  "add_reply" | "like_post" | "search_posts" | "get_reputation",
        "post_id": str (for get_post, translate_post, add_reply, like_post),
        "user_id": str (for create_post, add_reply, like_post, get_reputation),
        "title": str (for create_post),
        "content": str (for create_post, add_reply),
        "language": str (for create_post, add_reply),
        "target_language": str (for translate_post),
        "category": dict (for create_post, get_posts, search_posts),
        "tags": list (for create_post),
        "query": str (for search_posts),
        "limit": int (optional)
    }
    
    Returns:
        API Gateway response with forum data
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'get_posts')
        
        logger.info(f"Forum request: action={action}")
        
        # Route to appropriate handler
        if action == 'create_post':
            result = handle_create_post(body)
        elif action == 'get_posts':
            result = handle_get_posts(body)
        elif action == 'get_post':
            result = handle_get_post(body)
        elif action == 'translate_post':
            result = handle_translate_post(body)
        elif action == 'add_reply':
            result = handle_add_reply(body)
        elif action == 'like_post':
            result = handle_like_post(body)
        elif action == 'search_posts':
            result = handle_search_posts(body)
        elif action == 'get_reputation':
            result = handle_get_reputation(body)
        elif action == 'get_top_experts':
            result = handle_get_top_experts(body)
        elif action == 'mark_solution':
            result = handle_mark_solution(body)
        elif action == 'get_expert_directory':
            result = handle_get_expert_directory(body)
        else:
            return error_response(400, f'Invalid action: {action}')
        
        # Return response
        status_code = 200 if result.get('success') else 500
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result, default=str)
        }
    
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return error_response(400, f'Invalid input: {str(e)}')
    
    except Exception as e:
        logger.error(f"Lambda error: {e}", exc_info=True)
        return error_response(500, 'Internal server error')


def handle_create_post(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle create post request"""
    try:
        user_id = body.get('user_id')
        title = body.get('title', '').strip()
        content = body.get('content', '').strip()
        language = body.get('language', 'en')
        category = body.get('category', {})
        tags = body.get('tags', [])
        
        # Validate required fields
        if not user_id:
            return {'success': False, 'error': 'user_id is required'}
        if not title:
            return {'success': False, 'error': 'title is required'}
        if not content:
            return {'success': False, 'error': 'content is required'}
        
        result = forum_tools.create_post(
            user_id=user_id,
            title=title,
            content=content,
            language=language,
            category=category,
            tags=tags
        )
        
        logger.info(f"Post created: success={result.get('success')}")
        return result
    
    except Exception as e:
        logger.error(f"Create post error: {e}")
        return {'success': False, 'error': str(e)}


def handle_get_posts(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get posts request"""
    try:
        category = body.get('category')
        limit = int(body.get('limit', 20))
        last_evaluated_key = body.get('last_evaluated_key')
        
        result = forum_tools.get_posts(
            category=category,
            limit=limit,
            last_evaluated_key=last_evaluated_key
        )
        
        logger.info(f"Posts retrieved: count={result.get('count', 0)}")
        return result
    
    except Exception as e:
        logger.error(f"Get posts error: {e}")
        return {'success': False, 'error': str(e)}


def handle_get_post(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get single post request"""
    try:
        post_id = body.get('post_id')
        
        if not post_id:
            return {'success': False, 'error': 'post_id is required'}
        
        result = forum_tools.get_post(post_id)
        
        logger.info(f"Post retrieved: post_id={post_id}")
        return result
    
    except Exception as e:
        logger.error(f"Get post error: {e}")
        return {'success': False, 'error': str(e)}


def handle_translate_post(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle translate post request"""
    try:
        post_id = body.get('post_id')
        target_language = body.get('target_language', 'en')
        
        if not post_id:
            return {'success': False, 'error': 'post_id is required'}
        
        result = forum_tools.translate_post(
            post_id=post_id,
            target_language=target_language
        )
        
        logger.info(f"Post translated: post_id={post_id}, target={target_language}")
        return result
    
    except Exception as e:
        logger.error(f"Translate post error: {e}")
        return {'success': False, 'error': str(e)}


def handle_add_reply(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle add reply request"""
    try:
        post_id = body.get('post_id')
        user_id = body.get('user_id')
        content = body.get('content', '').strip()
        language = body.get('language', 'en')
        
        if not post_id:
            return {'success': False, 'error': 'post_id is required'}
        if not user_id:
            return {'success': False, 'error': 'user_id is required'}
        if not content:
            return {'success': False, 'error': 'content is required'}
        
        result = forum_tools.add_reply(
            post_id=post_id,
            user_id=user_id,
            content=content,
            language=language
        )
        
        logger.info(f"Reply added: post_id={post_id}")
        return result
    
    except Exception as e:
        logger.error(f"Add reply error: {e}")
        return {'success': False, 'error': str(e)}


def handle_like_post(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle like post request"""
    try:
        post_id = body.get('post_id')
        user_id = body.get('user_id')
        
        if not post_id:
            return {'success': False, 'error': 'post_id is required'}
        if not user_id:
            return {'success': False, 'error': 'user_id is required'}
        
        result = forum_tools.like_post(
            post_id=post_id,
            user_id=user_id
        )
        
        logger.info(f"Post liked: post_id={post_id}")
        return result
    
    except Exception as e:
        logger.error(f"Like post error: {e}")
        return {'success': False, 'error': str(e)}


def handle_search_posts(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle search posts request"""
    try:
        query = body.get('query', '').strip()
        category = body.get('category')
        limit = int(body.get('limit', 20))
        
        if not query:
            return {'success': False, 'error': 'query is required'}
        
        result = forum_tools.search_posts(
            query=query,
            category=category,
            limit=limit
        )
        
        logger.info(f"Posts searched: query={query}, count={result.get('count', 0)}")
        return result
    
    except Exception as e:
        logger.error(f"Search posts error: {e}")
        return {'success': False, 'error': str(e)}


def handle_get_reputation(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get user reputation request"""
    try:
        user_id = body.get('user_id')
        
        if not user_id:
            return {'success': False, 'error': 'user_id is required'}
        
        result = forum_tools.get_user_reputation(user_id)
        
        logger.info(f"Reputation retrieved: user_id={user_id}")
        return result
    
    except Exception as e:
        logger.error(f"Get reputation error: {e}")
        return {'success': False, 'error': str(e)}


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Generate error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'success': False,
            'error': message
        })
    }


# For local testing
if __name__ == '__main__':
    # Test event for creating a post
    test_event = {
        'action': 'create_post',
        'user_id': 'test_user_001',
        'title': 'गेहूं की खेती के लिए सर्वोत्तम प्रथाएं',
        'content': 'मैं अपने खेत में गेहूं उगा रहा हूं। क्या कोई मुझे सर्वोत्तम प्रथाओं के बारे में बता सकता है?',
        'language': 'hi',
        'category': {
            'crop_type': 'wheat',
            'region': 'north_india',
            'method': 'traditional'
        },
        'tags': ['wheat', 'best_practices', 'advice']
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2, ensure_ascii=False))


def handle_get_top_experts(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get top experts request"""
    try:
        limit = int(body.get('limit', 10))
        expertise_area = body.get('expertise_area')
        
        result = forum_tools.get_top_experts(
            limit=limit,
            expertise_area=expertise_area
        )
        
        logger.info(f"Top experts retrieved: count={result.get('count', 0)}")
        return result
    
    except Exception as e:
        logger.error(f"Get top experts error: {e}")
        return {'success': False, 'error': str(e)}


def handle_mark_solution(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mark post as solution request"""
    try:
        post_id = body.get('post_id')
        marked_by_user_id = body.get('marked_by_user_id')
        
        if not post_id:
            return {'success': False, 'error': 'post_id is required'}
        if not marked_by_user_id:
            return {'success': False, 'error': 'marked_by_user_id is required'}
        
        result = forum_tools.mark_post_as_solution(
            post_id=post_id,
            marked_by_user_id=marked_by_user_id
        )
        
        logger.info(f"Post marked as solution: post_id={post_id}")
        return result
    
    except Exception as e:
        logger.error(f"Mark solution error: {e}")
        return {'success': False, 'error': str(e)}


def handle_get_expert_directory(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get expert directory request"""
    try:
        result = forum_tools.get_expert_directory()
        
        logger.info(f"Expert directory retrieved")
        return result
    
    except Exception as e:
        logger.error(f"Get expert directory error: {e}")
        return {'success': False, 'error': str(e)}
