"""
RISE Scheme Application Lambda Function
AWS Lambda handler for scheme application assistance and tracking
"""

import json
import logging
import os
from typing import Dict, Any
from scheme_application_tools import SchemeApplicationTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize application tools
application_tools = SchemeApplicationTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for scheme application requests
    
    Event structure:
    {
        "action": "generate_wizard" | "validate_documents" | "submit_application" | "track_status" | "send_notification",
        "user_id": str,
        "scheme_id": str,
        "application_data": dict (for generate_wizard, submit_application),
        "documents": list (for validate_documents),
        "application_id": str (for track_status, send_notification)
    }
    
    Returns:
        API Gateway response with application assistance data
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'generate_wizard')
        
        logger.info(f"Application assistance request: action={action}")
        
        # Route to appropriate handler
        if action == 'generate_wizard':
            result = handle_generate_wizard(body)
        elif action == 'validate_documents':
            result = handle_validate_documents(body)
        elif action == 'submit_application':
            result = handle_submit_application(body)
        elif action == 'track_status':
            result = handle_track_status(body)
        elif action == 'send_notification':
            result = handle_send_notification(body)
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


def handle_generate_wizard(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle application wizard generation request"""
    try:
        user_id = body.get('user_id')
        scheme_id = body.get('scheme_id')
        language = body.get('language', 'hi')
        
        if not user_id or not scheme_id:
            return {
                'success': False,
                'error': 'user_id and scheme_id are required'
            }
        
        result = application_tools.generate_application_wizard(user_id, scheme_id, language)
        
        logger.info(f"Application wizard generated for scheme: {scheme_id}")
        return result
    
    except Exception as e:
        logger.error(f"Wizard generation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_validate_documents(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle document validation request"""
    try:
        documents = body.get('documents')
        scheme_id = body.get('scheme_id')
        
        if not documents or not scheme_id:
            return {
                'success': False,
                'error': 'documents and scheme_id are required'
            }
        
        result = application_tools.validate_documents(documents, scheme_id)
        
        logger.info(f"Document validation completed: {len(documents)} documents")
        return result
    
    except Exception as e:
        logger.error(f"Document validation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_submit_application(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle application submission request"""
    try:
        user_id = body.get('user_id')
        scheme_id = body.get('scheme_id')
        application_data = body.get('application_data')
        
        if not user_id or not scheme_id or not application_data:
            return {
                'success': False,
                'error': 'user_id, scheme_id, and application_data are required'
            }
        
        result = application_tools.submit_application(user_id, scheme_id, application_data)
        
        logger.info(f"Application submitted: {result.get('application_id', 'unknown')}")
        return result
    
    except Exception as e:
        logger.error(f"Application submission error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_track_status(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle application status tracking request"""
    try:
        application_id = body.get('application_id')
        
        if not application_id:
            return {
                'success': False,
                'error': 'application_id is required'
            }
        
        result = application_tools.track_application_status(application_id)
        
        logger.info(f"Status tracked for application: {application_id}")
        return result
    
    except Exception as e:
        logger.error(f"Status tracking error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_send_notification(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle notification sending request"""
    try:
        user_id = body.get('user_id')
        application_id = body.get('application_id')
        notification_type = body.get('notification_type', 'status_update')
        
        if not user_id or not application_id:
            return {
                'success': False,
                'error': 'user_id and application_id are required'
            }
        
        result = application_tools.send_application_notification(
            user_id, application_id, notification_type
        )
        
        logger.info(f"Notification sent for application: {application_id}")
        return result
    
    except Exception as e:
        logger.error(f"Notification error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


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
    # Test event for wizard generation
    test_event = {
        'action': 'generate_wizard',
        'user_id': 'user_12345',
        'scheme_id': 'SCH_PM_KISAN',
        'language': 'hi'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2))
