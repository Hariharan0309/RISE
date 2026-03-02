"""
RISE Weather Alert Lambda Function
AWS Lambda handler for scheduled weather monitoring and alert generation
Triggered by EventBridge scheduled rules
"""

import json
import logging
import os
from typing import Dict, Any, List
from weather_alert_tools import WeatherAlertTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize weather alert tools
weather_alert_tools = WeatherAlertTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for weather alert monitoring
    
    Event types:
    1. EventBridge scheduled event (monitors all users)
    2. API Gateway request (monitors specific user)
    
    Event structure for API Gateway:
    {
        "action": "monitor" | "get_alerts",
        "user_id": str
    }
    
    Returns:
        API Gateway response or EventBridge result
    """
    try:
        # Check if this is an EventBridge scheduled event
        if event.get('source') == 'aws.events':
            return handle_scheduled_monitoring(event, context)
        
        # Otherwise, handle as API Gateway request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'monitor')
        user_id = body.get('user_id')
        
        if not user_id:
            return {
                'statusCode': 400,
                'headers': get_response_headers(),
                'body': json.dumps({
                    'success': False,
                    'error': 'user_id is required'
                })
            }
        
        logger.info(f"Weather alert request: action={action}, user_id={user_id}")
        
        # Route to appropriate handler
        if action == 'monitor':
            result = handle_user_monitoring(user_id)
        elif action == 'get_alerts':
            days = int(body.get('days', 7))
            result = handle_get_alerts(user_id, days)
        else:
            return {
                'statusCode': 400,
                'headers': get_response_headers(),
                'body': json.dumps({
                    'success': False,
                    'error': f'Invalid action: {action}'
                })
            }
        
        # Return response
        status_code = 200 if result.get('success') else 500
        
        return {
            'statusCode': status_code,
            'headers': get_response_headers(),
            'body': json.dumps(result)
        }
    
    except Exception as e:
        logger.error(f"Lambda error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': get_response_headers(),
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error'
            })
        }


def handle_scheduled_monitoring(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle scheduled weather monitoring for all active users
    Triggered by EventBridge every 6 hours
    
    Args:
        event: EventBridge event
        context: Lambda context
    
    Returns:
        Monitoring results
    """
    try:
        logger.info("Starting scheduled weather monitoring for all users")
        
        # Get list of active users
        active_users = get_active_users()
        
        logger.info(f"Found {len(active_users)} active users to monitor")
        
        results = {
            'total_users': len(active_users),
            'successful': 0,
            'failed': 0,
            'alerts_generated': 0,
            'critical_alerts': 0
        }
        
        # Monitor weather for each user
        for user_id in active_users:
            try:
                result = weather_alert_tools.monitor_weather_conditions(user_id)
                
                if result['success']:
                    results['successful'] += 1
                    results['alerts_generated'] += len(result.get('alerts', []))
                    
                    # Count critical alerts
                    critical = sum(1 for a in result.get('alerts', []) 
                                 if a.get('severity') == 'high')
                    results['critical_alerts'] += critical
                    
                    logger.info(f"Monitored user {user_id}: {len(result.get('alerts', []))} alerts")
                else:
                    results['failed'] += 1
                    logger.warning(f"Failed to monitor user {user_id}: {result.get('error')}")
            
            except Exception as e:
                results['failed'] += 1
                logger.error(f"Error monitoring user {user_id}: {e}")
        
        logger.info(f"Scheduled monitoring complete: {results}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(results)
        }
    
    except Exception as e:
        logger.error(f"Scheduled monitoring error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


def handle_user_monitoring(user_id: str) -> Dict[str, Any]:
    """
    Handle weather monitoring for a specific user
    
    Args:
        user_id: User identifier
    
    Returns:
        Monitoring result
    """
    try:
        result = weather_alert_tools.monitor_weather_conditions(user_id)
        logger.info(f"User monitoring complete for {user_id}")
        return result
    except Exception as e:
        logger.error(f"User monitoring error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_get_alerts(user_id: str, days: int) -> Dict[str, Any]:
    """
    Handle request to get user's recent alerts
    
    Args:
        user_id: User identifier
        days: Number of days to look back
    
    Returns:
        User's alerts
    """
    try:
        result = weather_alert_tools.get_user_alerts(user_id, days)
        logger.info(f"Retrieved alerts for user {user_id}: {result.get('count', 0)} alerts")
        return result
    except Exception as e:
        logger.error(f"Get alerts error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def get_active_users() -> List[str]:
    """
    Get list of active users who should receive weather monitoring
    
    Returns:
        List of user IDs
    """
    try:
        import boto3
        
        dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        user_table = dynamodb.Table('RISE-UserProfiles')
        
        # Scan for users with location data
        response = user_table.scan(
            FilterExpression='attribute_exists(#loc)',
            ExpressionAttributeNames={'#loc': 'location'},
            ProjectionExpression='user_id'
        )
        
        user_ids = [item['user_id'] for item in response.get('Items', [])]
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = user_table.scan(
                FilterExpression='attribute_exists(#loc)',
                ExpressionAttributeNames={'#loc': 'location'},
                ProjectionExpression='user_id',
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            user_ids.extend([item['user_id'] for item in response.get('Items', [])])
        
        return user_ids
    
    except Exception as e:
        logger.error(f"Error fetching active users: {e}")
        return []


def get_response_headers() -> Dict[str, str]:
    """Get standard response headers"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    }


# For local testing
if __name__ == '__main__':
    # Test scheduled monitoring
    test_event = {
        'source': 'aws.events',
        'detail-type': 'Scheduled Event',
        'time': '2024-01-01T12:00:00Z'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test user monitoring
    test_event_user = {
        'action': 'monitor',
        'user_id': 'test_user_123'
    }
    
    result = lambda_handler(test_event_user, None)
    print(json.dumps(json.loads(result['body']), indent=2))
