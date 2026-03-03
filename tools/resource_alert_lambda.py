"""
RISE Resource Alert System Lambda Function
AWS Lambda handler for unused equipment monitoring and alert generation
"""

import json
import logging
import os
from typing import Dict, Any
from resource_alert_tools import ResourceAlertTools
from voice_tools import VoiceProcessingTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize tools
alert_tools = ResourceAlertTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)

voice_tools = VoiceProcessingTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for resource alert requests
    
    Event structure:
    {
        "action": "find_unused" | "send_alert" | "send_batch_alerts" | "get_preferences" | "update_preferences",
        "days_threshold": int (optional, default 30),
        "resource": {...} (for send_alert),
        "user_id": str (for get_preferences, update_preferences),
        "preferences": {...} (for update_preferences)
    }
    
    Returns:
        API Gateway response with alert data
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'find_unused')
        
        logger.info(f"Resource alert request: action={action}")
        
        # Route to appropriate handler
        if action == 'find_unused':
            result = handle_find_unused(body)
        elif action == 'send_alert':
            result = handle_send_alert(body)
        elif action == 'send_batch_alerts':
            result = handle_send_batch_alerts(body)
        elif action == 'get_preferences':
            result = handle_get_preferences(body)
        elif action == 'update_preferences':
            result = handle_update_preferences(body)
        elif action == 'calculate_income':
            result = handle_calculate_income(body)
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


def handle_find_unused(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle find unused resources request"""
    try:
        days_threshold = body.get('days_threshold', 30)
        
        result = alert_tools.find_unused_resources(days_threshold)
        logger.info(f"Found {result.get('count', 0)} unused resources")
        return result
    
    except Exception as e:
        logger.error(f"Find unused error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_send_alert(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle send single alert request"""
    try:
        resource = body.get('resource')
        user_language = body.get('user_language', 'hi')
        
        if not resource:
            return {
                'success': False,
                'error': 'resource is required'
            }
        
        # Send alert
        result = alert_tools.send_unused_resource_alert(resource, user_language)
        
        if result['success']:
            # Generate voice notification
            alert_message = result['alert_message']
            voice_result = voice_tools.synthesize_speech(alert_message, user_language)
            
            if voice_result['success']:
                result['voice_notification'] = {
                    'audio_data': voice_result['audio_data'],
                    'audio_format': voice_result['audio_format']
                }
        
        logger.info(f"Alert sent for resource: {resource.get('resource_id')}")
        return result
    
    except Exception as e:
        logger.error(f"Send alert error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_send_batch_alerts(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle send batch alerts request"""
    try:
        days_threshold = body.get('days_threshold', 30)
        
        result = alert_tools.send_batch_alerts(days_threshold)
        
        # Generate voice notifications for each alert
        if result['success'] and result.get('alerts'):
            for alert in result['alerts']:
                try:
                    # Get user language from preferences
                    prefs_result = alert_tools.get_alert_preferences(alert['owner_user_id'])
                    
                    if prefs_result['success']:
                        alert_prefs = prefs_result['alert_preferences']
                        
                        # Check if voice alerts are enabled
                        if 'voice' in alert_prefs.get('alert_channels', ['voice']):
                            # Get user language
                            user_response = alert_tools.user_table.get_item(
                                Key={'user_id': alert['owner_user_id']}
                            )
                            
                            if 'Item' in user_response:
                                user_language = user_response['Item'].get('preferences', {}).get('language', 'hi')
                                
                                # Generate voice notification
                                voice_result = voice_tools.synthesize_speech(
                                    alert['alert_message'],
                                    user_language
                                )
                                
                                if voice_result['success']:
                                    alert['voice_notification_generated'] = True
                
                except Exception as voice_error:
                    logger.warning(f"Voice notification error for alert: {voice_error}")
                    continue
        
        logger.info(f"Batch alerts sent: {result.get('alerts_sent', 0)}")
        return result
    
    except Exception as e:
        logger.error(f"Batch alerts error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_get_preferences(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get alert preferences request"""
    try:
        user_id = body.get('user_id')
        
        if not user_id:
            return {
                'success': False,
                'error': 'user_id is required'
            }
        
        result = alert_tools.get_alert_preferences(user_id)
        logger.info(f"Alert preferences fetched for user: {user_id}")
        return result
    
    except Exception as e:
        logger.error(f"Get preferences error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_update_preferences(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle update alert preferences request"""
    try:
        user_id = body.get('user_id')
        preferences = body.get('preferences')
        
        if not user_id:
            return {
                'success': False,
                'error': 'user_id is required'
            }
        
        if not preferences:
            return {
                'success': False,
                'error': 'preferences is required'
            }
        
        result = alert_tools.update_alert_preferences(user_id, preferences)
        logger.info(f"Alert preferences updated for user: {user_id}")
        return result
    
    except Exception as e:
        logger.error(f"Update preferences error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_calculate_income(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle calculate potential income request"""
    try:
        resource = body.get('resource')
        
        if not resource:
            return {
                'success': False,
                'error': 'resource is required'
            }
        
        result = alert_tools.calculate_potential_income(resource)
        logger.info(f"Income calculated for resource: {resource.get('resource_id')}")
        return result
    
    except Exception as e:
        logger.error(f"Calculate income error: {e}")
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
    # Test event for finding unused resources
    test_event_find = {
        'action': 'find_unused',
        'days_threshold': 30
    }
    
    result = lambda_handler(test_event_find, None)
    print("Find Unused Resources Test:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test event for batch alerts
    test_event_batch = {
        'action': 'send_batch_alerts',
        'days_threshold': 30
    }
    
    result2 = lambda_handler(test_event_batch, None)
    print("\n" + "="*50 + "\n")
    print("Send Batch Alerts Test:")
    print(json.dumps(json.loads(result2['body']), indent=2))
    
    # Test event for alert preferences
    test_event_prefs = {
        'action': 'get_preferences',
        'user_id': 'farmer_12345'
    }
    
    result3 = lambda_handler(test_event_prefs, None)
    print("\n" + "="*50 + "\n")
    print("Get Alert Preferences Test:")
    print(json.dumps(json.loads(result3['body']), indent=2))
