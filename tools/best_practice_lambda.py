"""
RISE Best Practice Sharing Lambda Function
AWS Lambda handler for best practice operations
"""

import json
import logging
import os
from typing import Dict, Any
from best_practice_tools import BestPracticeTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize best practice tools
best_practice_tools = BestPracticeTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for best practice requests
    
    Event structure:
    {
        "action": "submit_practice" | "get_practices" | "get_practice" | 
                  "adopt_practice" | "submit_feedback" | "get_analytics" | 
                  "search_practices" | "translate_practice" | "get_contributions",
        "practice_id": str,
        "user_id": str,
        "title": str,
        "description": str,
        "language": str,
        "category": dict,
        "steps": list,
        "expected_benefits": dict,
        "resources_needed": list,
        "images": list,
        "implementation_date": str,
        "notes": str,
        "success": bool,
        "feedback": str,
        "results": dict,
        "adoption_id": str,
        "query": str,
        "target_language": str,
        "sort_by": str,
        "limit": int
    }
    
    Returns:
        API Gateway response with best practice data
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'get_practices')
        
        logger.info(f"Best practice request: action={action}")
        
        # Route to appropriate handler
        if action == 'submit_practice':
            result = handle_submit_practice(body)
        elif action == 'get_practices':
            result = handle_get_practices(body)
        elif action == 'get_practice':
            result = handle_get_practice(body)
        elif action == 'adopt_practice':
            result = handle_adopt_practice(body)
        elif action == 'submit_feedback':
            result = handle_submit_feedback(body)
        elif action == 'get_analytics':
            result = handle_get_analytics(body)
        elif action == 'search_practices':
            result = handle_search_practices(body)
        elif action == 'translate_practice':
            result = handle_translate_practice(body)
        elif action == 'get_contributions':
            result = handle_get_contributions(body)
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


def handle_submit_practice(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle submit practice request"""
    try:
        user_id = body.get('user_id')
        title = body.get('title', '').strip()
        description = body.get('description', '').strip()
        language = body.get('language', 'en')
        category = body.get('category', {})
        steps = body.get('steps', [])
        expected_benefits = body.get('expected_benefits', {})
        resources_needed = body.get('resources_needed')
        images = body.get('images')
        
        # Validate required fields
        if not user_id:
            return {'success': False, 'error': 'user_id is required'}
        if not title:
            return {'success': False, 'error': 'title is required'}
        if not description:
            return {'success': False, 'error': 'description is required'}
        if not steps:
            return {'success': False, 'error': 'steps are required'}
        if not expected_benefits:
            return {'success': False, 'error': 'expected_benefits are required'}
        
        result = best_practice_tools.submit_practice(
            user_id=user_id,
            title=title,
            description=description,
            language=language,
            category=category,
            steps=steps,
            expected_benefits=expected_benefits,
            resources_needed=resources_needed,
            images=images
        )
        
        logger.info(f"Practice submitted: success={result.get('success')}")
        return result
    
    except Exception as e:
        logger.error(f"Submit practice error: {e}")
        return {'success': False, 'error': str(e)}


def handle_get_practices(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get practices request"""
    try:
        category = body.get('category')
        sort_by = body.get('sort_by', 'recent')
        limit = int(body.get('limit', 20))
        last_evaluated_key = body.get('last_evaluated_key')
        
        result = best_practice_tools.get_practices(
            category=category,
            sort_by=sort_by,
            limit=limit,
            last_evaluated_key=last_evaluated_key
        )
        
        logger.info(f"Practices retrieved: count={result.get('count', 0)}")
        return result
    
    except Exception as e:
        logger.error(f"Get practices error: {e}")
        return {'success': False, 'error': str(e)}


def handle_get_practice(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get single practice request"""
    try:
        practice_id = body.get('practice_id')
        
        if not practice_id:
            return {'success': False, 'error': 'practice_id is required'}
        
        result = best_practice_tools.get_practice(practice_id)
        
        logger.info(f"Practice retrieved: practice_id={practice_id}")
        return result
    
    except Exception as e:
        logger.error(f"Get practice error: {e}")
        return {'success': False, 'error': str(e)}


def handle_adopt_practice(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle adopt practice request"""
    try:
        practice_id = body.get('practice_id')
        user_id = body.get('user_id')
        implementation_date = body.get('implementation_date')
        notes = body.get('notes')
        
        if not practice_id:
            return {'success': False, 'error': 'practice_id is required'}
        if not user_id:
            return {'success': False, 'error': 'user_id is required'}
        if not implementation_date:
            return {'success': False, 'error': 'implementation_date is required'}
        
        result = best_practice_tools.adopt_practice(
            practice_id=practice_id,
            user_id=user_id,
            implementation_date=implementation_date,
            notes=notes
        )
        
        logger.info(f"Practice adopted: practice_id={practice_id}")
        return result
    
    except Exception as e:
        logger.error(f"Adopt practice error: {e}")
        return {'success': False, 'error': str(e)}


def handle_submit_feedback(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle submit feedback request"""
    try:
        adoption_id = body.get('adoption_id')
        user_id = body.get('user_id')
        success = body.get('success')
        feedback = body.get('feedback', '').strip()
        results = body.get('results', {})
        
        if not adoption_id:
            return {'success': False, 'error': 'adoption_id is required'}
        if not user_id:
            return {'success': False, 'error': 'user_id is required'}
        if success is None:
            return {'success': False, 'error': 'success status is required'}
        if not feedback:
            return {'success': False, 'error': 'feedback is required'}
        
        result = best_practice_tools.submit_feedback(
            adoption_id=adoption_id,
            user_id=user_id,
            success=success,
            feedback=feedback,
            results=results
        )
        
        logger.info(f"Feedback submitted: adoption_id={adoption_id}")
        return result
    
    except Exception as e:
        logger.error(f"Submit feedback error: {e}")
        return {'success': False, 'error': str(e)}


def handle_get_analytics(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get analytics request"""
    try:
        practice_id = body.get('practice_id')
        
        if not practice_id:
            return {'success': False, 'error': 'practice_id is required'}
        
        result = best_practice_tools.get_adoption_analytics(practice_id)
        
        logger.info(f"Analytics retrieved: practice_id={practice_id}")
        return result
    
    except Exception as e:
        logger.error(f"Get analytics error: {e}")
        return {'success': False, 'error': str(e)}


def handle_search_practices(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle search practices request"""
    try:
        query = body.get('query', '').strip()
        category = body.get('category')
        limit = int(body.get('limit', 20))
        
        if not query:
            return {'success': False, 'error': 'query is required'}
        
        result = best_practice_tools.search_practices(
            query=query,
            category=category,
            limit=limit
        )
        
        logger.info(f"Practices searched: query={query}, count={result.get('count', 0)}")
        return result
    
    except Exception as e:
        logger.error(f"Search practices error: {e}")
        return {'success': False, 'error': str(e)}


def handle_translate_practice(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle translate practice request"""
    try:
        practice_id = body.get('practice_id')
        target_language = body.get('target_language', 'en')
        
        if not practice_id:
            return {'success': False, 'error': 'practice_id is required'}
        
        result = best_practice_tools.translate_practice(
            practice_id=practice_id,
            target_language=target_language
        )
        
        logger.info(f"Practice translated: practice_id={practice_id}, target={target_language}")
        return result
    
    except Exception as e:
        logger.error(f"Translate practice error: {e}")
        return {'success': False, 'error': str(e)}


def handle_get_contributions(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get user contributions request"""
    try:
        user_id = body.get('user_id')
        
        if not user_id:
            return {'success': False, 'error': 'user_id is required'}
        
        result = best_practice_tools.get_user_contributions(user_id)
        
        logger.info(f"Contributions retrieved: user_id={user_id}")
        return result
    
    except Exception as e:
        logger.error(f"Get contributions error: {e}")
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
    # Test event for submitting a practice
    test_event = {
        'action': 'submit_practice',
        'user_id': 'test_user_001',
        'title': 'जैविक खाद से गेहूं की उपज बढ़ाना',
        'description': 'यह विधि जैविक खाद का उपयोग करके गेहूं की उपज में 20-25% की वृद्धि करती है।',
        'language': 'hi',
        'category': {
            'crop_type': 'wheat',
            'practice_type': 'organic_farming',
            'region': 'north_india'
        },
        'steps': [
            'खेत की तैयारी के समय 5 टन प्रति एकड़ गोबर की खाद मिलाएं',
            'बुवाई से पहले बीजों को जैविक कल्चर से उपचारित करें',
            'फसल की वृद्धि के दौरान वर्मीकम्पोस्ट का छिड़काव करें',
            'नीम की खली का उपयोग कीट नियंत्रण के लिए करें'
        ],
        'expected_benefits': {
            'yield_increase': 22.5,
            'cost_reduction': 15,
            'soil_health_improvement': 'high',
            'sustainability_score': 9
        },
        'resources_needed': ['गोबर की खाद', 'वर्मीकम्पोस्ट', 'नीम की खली', 'जैविक कल्चर'],
        'images': []
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2, ensure_ascii=False))
