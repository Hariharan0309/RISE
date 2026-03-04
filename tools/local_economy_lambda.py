"""
RISE Local Economy Tracking Lambda Function
AWS Lambda handler for economic impact analytics and community metrics
"""

import json
import logging
import os
from typing import Dict, Any

try:
    from local_economy_tools import LocalEconomyTools
except ImportError:
    from tools.local_economy_tools import LocalEconomyTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize local economy tools
economy_tools = LocalEconomyTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for local economy tracking requests
    
    Event structure:
    {
        "action": "calculate_impact" | "track_savings" | "track_income" | "resource_utilization" | "sustainability" | "network_data",
        "location": {...} (for calculate_impact, resource_utilization, sustainability, network_data),
        "user_id": str (for track_savings, track_income),
        "time_period": {...} (optional)
    }
    
    Returns:
        API Gateway response with economic metrics
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'calculate_impact')
        
        logger.info(f"Local economy tracking request: action={action}")
        
        # Route to appropriate handler
        if action == 'calculate_impact':
            result = handle_calculate_impact(body)
        elif action == 'track_savings':
            result = handle_track_savings(body)
        elif action == 'track_income':
            result = handle_track_income(body)
        elif action == 'resource_utilization':
            result = handle_resource_utilization(body)
        elif action == 'sustainability':
            result = handle_sustainability(body)
        elif action == 'network_data':
            result = handle_network_data(body)
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


def handle_calculate_impact(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle economic impact calculation request"""
    try:
        location = body.get('location')
        time_period = body.get('time_period')
        
        if not location:
            return {
                'success': False,
                'error': 'location is required'
            }
        
        # Validate location fields
        if 'state' not in location or 'district' not in location:
            return {
                'success': False,
                'error': 'location must include state and district'
            }
        
        result = economy_tools.calculate_economic_impact(location, time_period)
        logger.info(f"Economic impact calculated for {location['district']}, {location['state']}")
        return result
    
    except Exception as e:
        logger.error(f"Calculate impact error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_track_savings(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle cost savings tracking request"""
    try:
        user_id = body.get('user_id')
        time_period = body.get('time_period')
        
        if not user_id:
            return {
                'success': False,
                'error': 'user_id is required'
            }
        
        result = economy_tools.track_cost_savings(user_id, time_period)
        logger.info(f"Cost savings tracked for user {user_id}")
        return result
    
    except Exception as e:
        logger.error(f"Track savings error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_track_income(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle additional income tracking request"""
    try:
        user_id = body.get('user_id')
        time_period = body.get('time_period')
        
        if not user_id:
            return {
                'success': False,
                'error': 'user_id is required'
            }
        
        result = economy_tools.track_additional_income(user_id, time_period)
        logger.info(f"Additional income tracked for user {user_id}")
        return result
    
    except Exception as e:
        logger.error(f"Track income error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_resource_utilization(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle resource utilization calculation request"""
    try:
        location = body.get('location')
        time_period = body.get('time_period')
        
        if not location:
            return {
                'success': False,
                'error': 'location is required'
            }
        
        result = economy_tools.calculate_resource_utilization(location, time_period)
        logger.info(f"Resource utilization calculated for {location['district']}, {location['state']}")
        return result
    
    except Exception as e:
        logger.error(f"Resource utilization error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_sustainability(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle sustainability metrics generation request"""
    try:
        location = body.get('location')
        time_period = body.get('time_period')
        
        if not location:
            return {
                'success': False,
                'error': 'location is required'
            }
        
        result = economy_tools.generate_sustainability_metrics(location, time_period)
        logger.info(f"Sustainability metrics generated for {location['district']}, {location['state']}")
        return result
    
    except Exception as e:
        logger.error(f"Sustainability metrics error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_network_data(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle community network data request"""
    try:
        location = body.get('location')
        
        if not location:
            return {
                'success': False,
                'error': 'location is required'
            }
        
        result = economy_tools.get_community_network_data(location)
        logger.info(f"Community network data generated for {location['district']}, {location['state']}")
        return result
    
    except Exception as e:
        logger.error(f"Network data error: {e}")
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
    # Test event for economic impact calculation
    test_event_impact = {
        'action': 'calculate_impact',
        'location': {
            'state': 'Punjab',
            'district': 'Ludhiana'
        },
        'time_period': {
            'start': '2024-01-01T00:00:00',
            'end': '2024-01-31T23:59:59'
        }
    }
    
    result = lambda_handler(test_event_impact, None)
    print("Economic Impact Calculation Test:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test event for cost savings tracking
    test_event_savings = {
        'action': 'track_savings',
        'user_id': 'farmer_12345',
        'time_period': {
            'start': '2024-01-01T00:00:00',
            'end': '2024-01-31T23:59:59'
        }
    }
    
    result2 = lambda_handler(test_event_savings, None)
    print("\n" + "="*50 + "\n")
    print("Cost Savings Tracking Test:")
    print(json.dumps(json.loads(result2['body']), indent=2))
    
    # Test event for additional income tracking
    test_event_income = {
        'action': 'track_income',
        'user_id': 'farmer_12345',
        'time_period': {
            'start': '2024-01-01T00:00:00',
            'end': '2024-01-31T23:59:59'
        }
    }
    
    result3 = lambda_handler(test_event_income, None)
    print("\n" + "="*50 + "\n")
    print("Additional Income Tracking Test:")
    print(json.dumps(json.loads(result3['body']), indent=2))
