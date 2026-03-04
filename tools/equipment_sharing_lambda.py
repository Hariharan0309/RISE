"""
RISE Equipment Sharing Marketplace Lambda Function
AWS Lambda handler for equipment listing, search, booking, and management
"""

import json
import logging
import os
from typing import Dict, Any
from equipment_sharing_tools import EquipmentSharingTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize equipment sharing tools
equipment_tools = EquipmentSharingTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for equipment sharing requests
    
    Event structure:
    {
        "action": "list_equipment" | "search_equipment" | "book_equipment" | "get_details" | "rate_equipment" | "send_alerts",
        "owner_id": str (for list_equipment),
        "equipment_data": {...} (for list_equipment),
        "location": {...} (for search_equipment),
        "equipment_type": str (for search_equipment, optional),
        "date_range": {...} (for search_equipment, optional),
        "radius_km": int (for search_equipment, optional),
        "renter_id": str (for book_equipment),
        "resource_id": str (for book_equipment, get_details),
        "booking_details": {...} (for book_equipment),
        "booking_id": str (for rate_equipment),
        "rating_data": {...} (for rate_equipment),
        "days_threshold": int (for send_alerts, optional)
    }
    
    Returns:
        API Gateway response with equipment sharing data
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'search_equipment')
        
        logger.info(f"Equipment sharing request: action={action}")
        
        # Route to appropriate handler
        if action == 'list_equipment':
            result = handle_list_equipment(body)
        elif action == 'search_equipment':
            result = handle_search_equipment(body)
        elif action == 'book_equipment':
            result = handle_book_equipment(body)
        elif action == 'get_details':
            result = handle_get_details(body)
        elif action == 'rate_equipment':
            result = handle_rate_equipment(body)
        elif action == 'send_alerts':
            result = handle_send_alerts(body)
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


def handle_list_equipment(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle equipment listing request"""
    try:
        owner_id = body.get('owner_id')
        equipment_data = body.get('equipment_data')
        
        if not owner_id:
            return {
                'success': False,
                'error': 'owner_id is required'
            }
        
        if not equipment_data:
            return {
                'success': False,
                'error': 'equipment_data is required'
            }
        
        # Validate required fields
        required_fields = ['name', 'type', 'location']
        for field in required_fields:
            if field not in equipment_data:
                return {
                    'success': False,
                    'error': f'Missing required field: {field}'
                }
        
        result = equipment_tools.list_equipment(owner_id, equipment_data)
        logger.info(f"Equipment listed: {result.get('resource_id')}")
        return result
    
    except Exception as e:
        logger.error(f"Equipment listing error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_search_equipment(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle equipment search request"""
    try:
        location = body.get('location')
        equipment_type = body.get('equipment_type')
        date_range = body.get('date_range')
        radius_km = body.get('radius_km', 25)
        
        if not location:
            return {
                'success': False,
                'error': 'location is required'
            }
        
        result = equipment_tools.search_equipment(
            location,
            equipment_type,
            date_range,
            radius_km
        )
        logger.info(f"Equipment search: found {result.get('count', 0)} results")
        return result
    
    except Exception as e:
        logger.error(f"Equipment search error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_book_equipment(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle equipment booking request"""
    try:
        renter_id = body.get('renter_id')
        resource_id = body.get('resource_id')
        booking_details = body.get('booking_details')
        
        if not renter_id:
            return {
                'success': False,
                'error': 'renter_id is required'
            }
        
        if not resource_id:
            return {
                'success': False,
                'error': 'resource_id is required'
            }
        
        if not booking_details:
            return {
                'success': False,
                'error': 'booking_details is required'
            }
        
        # Validate required booking fields
        required_fields = ['start_time', 'end_time']
        for field in required_fields:
            if field not in booking_details:
                return {
                    'success': False,
                    'error': f'Missing required field: {field}'
                }
        
        result = equipment_tools.book_equipment(renter_id, resource_id, booking_details)
        logger.info(f"Equipment booked: {result.get('booking_id')}")
        return result
    
    except Exception as e:
        logger.error(f"Equipment booking error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_get_details(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get equipment details request"""
    try:
        resource_id = body.get('resource_id')
        
        if not resource_id:
            return {
                'success': False,
                'error': 'resource_id is required'
            }
        
        result = equipment_tools.get_equipment_details(resource_id)
        logger.info(f"Equipment details fetched: {resource_id}")
        return result
    
    except Exception as e:
        logger.error(f"Get equipment details error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_rate_equipment(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle equipment rating request"""
    try:
        booking_id = body.get('booking_id')
        rating_data = body.get('rating_data')
        
        if not booking_id:
            return {
                'success': False,
                'error': 'booking_id is required'
            }
        
        if not rating_data or 'equipment_rating' not in rating_data:
            return {
                'success': False,
                'error': 'rating_data with equipment_rating is required'
            }
        
        result = equipment_tools.rate_equipment(booking_id, rating_data)
        logger.info(f"Equipment rated: booking {booking_id}")
        return result
    
    except Exception as e:
        logger.error(f"Equipment rating error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_send_alerts(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle send unused equipment alerts request"""
    try:
        days_threshold = body.get('days_threshold', 30)
        
        result = equipment_tools.send_unused_equipment_alerts(days_threshold)
        logger.info(f"Unused equipment alerts sent: {result.get('alerts_sent', 0)}")
        return result
    
    except Exception as e:
        logger.error(f"Send alerts error: {e}")
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
    # Test event for equipment listing
    test_event_list = {
        'action': 'list_equipment',
        'owner_id': 'farmer_12345',
        'equipment_data': {
            'name': 'John Deere Tractor',
            'type': 'tractor',
            'model': '5075E',
            'condition': 'excellent',
            'hourly_rate': 500,
            'daily_rate': 3000,
            'year': '2020',
            'capacity': '75 HP',
            'specifications': {
                'engine': '4-cylinder diesel',
                'transmission': 'PowrReverser',
                'pto_hp': '62'
            },
            'location': {
                'state': 'Punjab',
                'district': 'Ludhiana',
                'address': 'Village Khanna',
                'latitude': 30.9010,
                'longitude': 75.8573
            },
            'photos': ['tractor_1.jpg', 'tractor_2.jpg'],
            'pickup_instructions': 'Contact 1 day before pickup. Fuel not included.'
        }
    }
    
    result = lambda_handler(test_event_list, None)
    print("Equipment Listing Test:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test event for equipment search
    test_event_search = {
        'action': 'search_equipment',
        'location': {
            'state': 'Punjab',
            'district': 'Jalandhar',
            'latitude': 31.3260,
            'longitude': 75.5762
        },
        'equipment_type': 'tractor',
        'radius_km': 50
    }
    
    result2 = lambda_handler(test_event_search, None)
    print("\n" + "="*50 + "\n")
    print("Equipment Search Test:")
    print(json.dumps(json.loads(result2['body']), indent=2))


def handle_process_payment(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle payment processing request"""
    try:
        booking_id = body.get('booking_id')
        payment_details = body.get('payment_details')
        
        if not booking_id:
            return {
                'success': False,
                'error': 'booking_id is required'
            }
        
        if not payment_details:
            return {
                'success': False,
                'error': 'payment_details is required'
            }
        
        result = equipment_tools.process_payment(booking_id, payment_details)
        logger.info(f"Payment processed: {result.get('transaction_id')}")
        return result
    
    except Exception as e:
        logger.error(f"Payment processing error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_update_usage(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle usage tracking update request"""
    try:
        booking_id = body.get('booking_id')
        usage_data = body.get('usage_data')
        
        if not booking_id:
            return {
                'success': False,
                'error': 'booking_id is required'
            }
        
        if not usage_data:
            return {
                'success': False,
                'error': 'usage_data is required'
            }
        
        result = equipment_tools.update_usage_tracking(booking_id, usage_data)
        logger.info(f"Usage tracking updated: {booking_id}")
        return result
    
    except Exception as e:
        logger.error(f"Usage tracking update error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_get_booking(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get booking details request"""
    try:
        booking_id = body.get('booking_id')
        
        if not booking_id:
            return {
                'success': False,
                'error': 'booking_id is required'
            }
        
        result = equipment_tools.get_booking_details(booking_id)
        logger.info(f"Booking details fetched: {booking_id}")
        return result
    
    except Exception as e:
        logger.error(f"Get booking details error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_get_user_bookings(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get user bookings request"""
    try:
        user_id = body.get('user_id')
        booking_type = body.get('booking_type', 'renter')
        
        if not user_id:
            return {
                'success': False,
                'error': 'user_id is required'
            }
        
        result = equipment_tools.get_user_bookings(user_id, booking_type)
        logger.info(f"User bookings fetched: {user_id}, count: {result.get('count', 0)}")
        return result
    
    except Exception as e:
        logger.error(f"Get user bookings error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_cancel_booking(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle booking cancellation request"""
    try:
        booking_id = body.get('booking_id')
        cancellation_reason = body.get('cancellation_reason', '')
        
        if not booking_id:
            return {
                'success': False,
                'error': 'booking_id is required'
            }
        
        result = equipment_tools.cancel_booking(booking_id, cancellation_reason)
        logger.info(f"Booking cancelled: {booking_id}")
        return result
    
    except Exception as e:
        logger.error(f"Booking cancellation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# Update lambda_handler to include new actions
def lambda_handler_extended(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Extended lambda handler with booking management features"""
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'search_equipment')
        
        logger.info(f"Equipment sharing request: action={action}")
        
        # Route to appropriate handler
        if action == 'list_equipment':
            result = handle_list_equipment(body)
        elif action == 'search_equipment':
            result = handle_search_equipment(body)
        elif action == 'book_equipment':
            result = handle_book_equipment(body)
        elif action == 'get_details':
            result = handle_get_details(body)
        elif action == 'rate_equipment':
            result = handle_rate_equipment(body)
        elif action == 'send_alerts':
            result = handle_send_alerts(body)
        elif action == 'process_payment':
            result = handle_process_payment(body)
        elif action == 'update_usage':
            result = handle_update_usage(body)
        elif action == 'get_booking':
            result = handle_get_booking(body)
        elif action == 'get_user_bookings':
            result = handle_get_user_bookings(body)
        elif action == 'cancel_booking':
            result = handle_cancel_booking(body)
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
