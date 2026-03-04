"""
RISE Cooperative Buying Groups Lambda Function
AWS Lambda handler for buying group formation, matching, and management
"""

import json
import logging
import os
from typing import Dict, Any
from buying_group_tools import BuyingGroupTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize buying group tools
buying_group_tools = BuyingGroupTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for buying group requests
    
    Event structure:
    {
        "action": "create_group" | "find_groups" | "join_group" | "calculate_pricing" | "negotiate" | "get_details" | "get_user_groups",
        "organizer_id": str (for create_group),
        "group_data": {...} (for create_group),
        "user_id": str (for find_groups, join_group, get_user_groups),
        "requirements": {...} (for find_groups, join_group),
        "group_id": str (for join_group, calculate_pricing, negotiate, get_details),
        "member_requirements": {...} (for join_group),
        "vendor_quotes": {...} (for calculate_pricing, optional),
        "vendor_list": [...] (for negotiate, optional)
    }
    
    Returns:
        API Gateway response with buying group data
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'find_groups')
        
        logger.info(f"Buying group request: action={action}")
        
        # Route to appropriate handler
        if action == 'create_group':
            result = handle_create_group(body)
        elif action == 'find_groups':
            result = handle_find_groups(body)
        elif action == 'join_group':
            result = handle_join_group(body)
        elif action == 'calculate_pricing':
            result = handle_calculate_pricing(body)
        elif action == 'negotiate':
            result = handle_negotiate(body)
        elif action == 'get_details':
            result = handle_get_details(body)
        elif action == 'get_user_groups':
            result = handle_get_user_groups(body)
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


def handle_create_group(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle buying group creation request"""
    try:
        organizer_id = body.get('organizer_id')
        group_data = body.get('group_data')
        
        if not organizer_id:
            return {
                'success': False,
                'error': 'organizer_id is required'
            }
        
        if not group_data:
            return {
                'success': False,
                'error': 'group_data is required'
            }
        
        # Validate required fields
        required_fields = ['group_name', 'target_products', 'location']
        for field in required_fields:
            if field not in group_data:
                return {
                    'success': False,
                    'error': f'Missing required field: {field}'
                }
        
        result = buying_group_tools.create_buying_group(organizer_id, group_data)
        logger.info(f"Buying group created: {result.get('group_id')}")
        return result
    
    except Exception as e:
        logger.error(f"Group creation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_find_groups(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle find matching groups request"""
    try:
        user_id = body.get('user_id')
        requirements = body.get('requirements')
        
        if not user_id:
            return {
                'success': False,
                'error': 'user_id is required'
            }
        
        if not requirements:
            return {
                'success': False,
                'error': 'requirements is required'
            }
        
        result = buying_group_tools.find_matching_groups(user_id, requirements)
        logger.info(f"Found {result.get('count', 0)} matching groups")
        return result
    
    except Exception as e:
        logger.error(f"Find groups error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_join_group(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle join group request"""
    try:
        user_id = body.get('user_id')
        group_id = body.get('group_id')
        member_requirements = body.get('member_requirements')
        
        if not user_id:
            return {
                'success': False,
                'error': 'user_id is required'
            }
        
        if not group_id:
            return {
                'success': False,
                'error': 'group_id is required'
            }
        
        if not member_requirements:
            return {
                'success': False,
                'error': 'member_requirements is required'
            }
        
        result = buying_group_tools.join_buying_group(user_id, group_id, member_requirements)
        logger.info(f"User {user_id} joined group {group_id}")
        return result
    
    except Exception as e:
        logger.error(f"Join group error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_calculate_pricing(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle bulk pricing calculation request"""
    try:
        group_id = body.get('group_id')
        vendor_quotes = body.get('vendor_quotes')
        
        if not group_id:
            return {
                'success': False,
                'error': 'group_id is required'
            }
        
        result = buying_group_tools.calculate_bulk_pricing(group_id, vendor_quotes)
        logger.info(f"Bulk pricing calculated for group {group_id}")
        return result
    
    except Exception as e:
        logger.error(f"Calculate pricing error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_negotiate(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle vendor negotiation request"""
    try:
        group_id = body.get('group_id')
        vendor_list = body.get('vendor_list')
        
        if not group_id:
            return {
                'success': False,
                'error': 'group_id is required'
            }
        
        result = buying_group_tools.negotiate_with_vendors(group_id, vendor_list)
        logger.info(f"Vendor negotiation initiated for group {group_id}")
        return result
    
    except Exception as e:
        logger.error(f"Negotiate error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_get_details(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get group details request"""
    try:
        group_id = body.get('group_id')
        
        if not group_id:
            return {
                'success': False,
                'error': 'group_id is required'
            }
        
        result = buying_group_tools.get_group_details(group_id)
        logger.info(f"Group details fetched: {group_id}")
        return result
    
    except Exception as e:
        logger.error(f"Get details error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_get_user_groups(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get user groups request"""
    try:
        user_id = body.get('user_id')
        
        if not user_id:
            return {
                'success': False,
                'error': 'user_id is required'
            }
        
        result = buying_group_tools.get_user_groups(user_id)
        logger.info(f"User groups fetched: {user_id}, count: {result.get('count', 0)}")
        return result
    
    except Exception as e:
        logger.error(f"Get user groups error: {e}")
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
    # Test event for group creation
    test_event_create = {
        'action': 'create_group',
        'organizer_id': 'farmer_12345',
        'group_data': {
            'group_name': 'Ludhiana Seed Buyers Group',
            'target_products': ['wheat_seeds', 'fertilizer_urea', 'pesticide_spray'],
            'location': {
                'state': 'Punjab',
                'district': 'Ludhiana',
                'radius_km': 25
            },
            'max_members': 30,
            'min_members': 5
        }
    }
    
    result = lambda_handler(test_event_create, None)
    print("Group Creation Test:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test event for finding groups
    test_event_find = {
        'action': 'find_groups',
        'user_id': 'farmer_67890',
        'requirements': {
            'products': ['wheat_seeds', 'fertilizer_urea'],
            'state': 'Punjab',
            'district': 'Ludhiana'
        }
    }
    
    result2 = lambda_handler(test_event_find, None)
    print("\n" + "="*50 + "\n")
    print("Find Groups Test:")
    print(json.dumps(json.loads(result2['body']), indent=2))
