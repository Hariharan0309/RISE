"""
RISE Resource Availability Alert Lambda Function
AWS Lambda handler for resource availability alerts
"""

import json
import logging
from typing import Dict, Any
from availability_alert_tools import create_availability_alert_tools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for resource availability alerts
    
    Args:
        event: Lambda event data
        context: Lambda context
    
    Returns:
        API Gateway response
    """
    try:
        # Parse request
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '')
        body = json.loads(event.get('body', '{}'))
        
        # Initialize tools
        tools = create_availability_alert_tools()
        
        # Route to appropriate handler
        if path.endswith('/equipment-availability-alert'):
            result = handle_equipment_availability_alert(tools, body)
        
        elif path.endswith('/bulk-buying-alert'):
            result = handle_bulk_buying_alert(tools, body)
        
        elif path.endswith('/seasonal-demand-prediction'):
            result = handle_seasonal_demand_prediction(tools, body)
        
        elif path.endswith('/advance-booking'):
            result = handle_advance_booking(tools, body)
        
        elif path.endswith('/optimal-schedule'):
            result = handle_optimal_schedule(tools, body)
        
        elif path.endswith('/alert-preferences'):
            if http_method == 'GET':
                result = handle_get_alert_preferences(tools, body)
            else:
                result = handle_customize_alert_preferences(tools, body)
        
        else:
            result = {
                'success': False,
                'error': f'Unknown endpoint: {path}'
            }
        
        # Return response
        return {
            'statusCode': 200 if result.get('success') else 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
    
    except Exception as e:
        logger.error(f"Lambda handler error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }


def handle_equipment_availability_alert(tools, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle equipment availability alert request"""
    resource_id = body.get('resource_id')
    radius_km = body.get('radius_km', 25)
    
    if not resource_id:
        return {
            'success': False,
            'error': 'resource_id is required'
        }
    
    return tools.send_equipment_availability_alert(resource_id, radius_km)


def handle_bulk_buying_alert(tools, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle bulk buying opportunity alert request"""
    group_id = body.get('group_id')
    radius_km = body.get('radius_km', 25)
    
    if not group_id:
        return {
            'success': False,
            'error': 'group_id is required'
        }
    
    return tools.send_bulk_buying_opportunity_alert(group_id, radius_km)


def handle_seasonal_demand_prediction(tools, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle seasonal demand prediction request"""
    user_id = body.get('user_id')
    crop_calendar = body.get('crop_calendar')
    
    if not user_id:
        return {
            'success': False,
            'error': 'user_id is required'
        }
    
    return tools.predict_seasonal_demand(user_id, crop_calendar)


def handle_advance_booking(tools, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle advance booking request"""
    user_id = body.get('user_id')
    booking_data = body.get('booking_data', {})
    
    if not user_id or not booking_data:
        return {
            'success': False,
            'error': 'user_id and booking_data are required'
        }
    
    return tools.create_advance_booking(user_id, booking_data)


def handle_optimal_schedule(tools, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle optimal schedule generation request"""
    resource_id = body.get('resource_id')
    time_period_days = body.get('time_period_days', 30)
    
    if not resource_id:
        return {
            'success': False,
            'error': 'resource_id is required'
        }
    
    return tools.generate_optimal_sharing_schedule(resource_id, time_period_days)


def handle_customize_alert_preferences(tools, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle alert preferences customization request"""
    user_id = body.get('user_id')
    preferences = body.get('preferences', {})
    
    if not user_id:
        return {
            'success': False,
            'error': 'user_id is required'
        }
    
    return tools.customize_alert_preferences(user_id, preferences)


def handle_get_alert_preferences(tools, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get alert preferences request"""
    user_id = body.get('user_id')
    
    if not user_id:
        return {
            'success': False,
            'error': 'user_id is required'
        }
    
    return tools.get_alert_preferences(user_id)
