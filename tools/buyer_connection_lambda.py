"""
RISE Direct Buyer Connection Lambda Function
AWS Lambda handler for buyer registration, crop listing, matching, and transactions
"""

import json
import logging
import os
from typing import Dict, Any
from buyer_connection_tools import BuyerConnectionTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize buyer connection tools
buyer_tools = BuyerConnectionTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for buyer connection requests
    
    Event structure:
    {
        "action": "register_buyer" | "create_listing" | "get_quality_standards" | "get_price_benchmarks" | "initiate_transaction",
        "buyer_data": {...} (for register_buyer),
        "farmer_id": str (for create_listing),
        "listing_data": {...} (for create_listing),
        "crop_name": str (for get_quality_standards, get_price_benchmarks),
        "location": {...} (for get_price_benchmarks),
        "listing_id": str (for initiate_transaction),
        "buyer_id": str (for initiate_transaction),
        "negotiation_data": {...} (for initiate_transaction)
    }
    
    Returns:
        API Gateway response with buyer connection data
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'create_listing')
        
        logger.info(f"Buyer connection request: action={action}")
        
        # Route to appropriate handler
        if action == 'register_buyer':
            result = handle_register_buyer(body)
        elif action == 'create_listing':
            result = handle_create_listing(body)
        elif action == 'get_quality_standards':
            result = handle_get_quality_standards(body)
        elif action == 'get_price_benchmarks':
            result = handle_get_price_benchmarks(body)
        elif action == 'initiate_transaction':
            result = handle_initiate_transaction(body)
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


def handle_register_buyer(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle buyer registration request"""
    try:
        buyer_data = body.get('buyer_data')
        
        if not buyer_data:
            return {
                'success': False,
                'error': 'buyer_data is required'
            }
        
        # Validate required fields
        required_fields = ['business_name', 'contact_person', 'phone_number', 'business_type', 'location']
        for field in required_fields:
            if field not in buyer_data:
                return {
                    'success': False,
                    'error': f'Missing required field: {field}'
                }
        
        result = buyer_tools.register_buyer(buyer_data)
        logger.info(f"Buyer registered: {result.get('buyer_id')}")
        return result
    
    except Exception as e:
        logger.error(f"Buyer registration error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_create_listing(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle crop listing creation request"""
    try:
        farmer_id = body.get('farmer_id')
        listing_data = body.get('listing_data')
        
        if not farmer_id:
            return {
                'success': False,
                'error': 'farmer_id is required'
            }
        
        if not listing_data:
            return {
                'success': False,
                'error': 'listing_data is required'
            }
        
        # Validate required fields
        required_fields = ['crop_name', 'quantity', 'location']
        for field in required_fields:
            if field not in listing_data:
                return {
                    'success': False,
                    'error': f'Missing required field: {field}'
                }
        
        result = buyer_tools.create_crop_listing(farmer_id, listing_data)
        logger.info(f"Crop listing created: {result.get('listing_id')}")
        return result
    
    except Exception as e:
        logger.error(f"Crop listing error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_get_quality_standards(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle quality standards request"""
    try:
        crop_name = body.get('crop_name', '').strip()
        
        if not crop_name:
            return {
                'success': False,
                'error': 'crop_name is required'
            }
        
        result = buyer_tools.get_quality_standards(crop_name)
        logger.info(f"Quality standards fetched: crop={crop_name}")
        return result
    
    except Exception as e:
        logger.error(f"Quality standards error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_get_price_benchmarks(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle price benchmarks request"""
    try:
        crop_name = body.get('crop_name', '').strip()
        location = body.get('location')
        
        if not crop_name:
            return {
                'success': False,
                'error': 'crop_name is required'
            }
        
        if not location:
            return {
                'success': False,
                'error': 'location is required'
            }
        
        result = buyer_tools.get_price_benchmarks(crop_name, location)
        logger.info(f"Price benchmarks fetched: crop={crop_name}")
        return result
    
    except Exception as e:
        logger.error(f"Price benchmarks error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_initiate_transaction(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle transaction initiation request"""
    try:
        listing_id = body.get('listing_id')
        buyer_id = body.get('buyer_id')
        negotiation_data = body.get('negotiation_data')
        
        if not listing_id:
            return {
                'success': False,
                'error': 'listing_id is required'
            }
        
        if not buyer_id:
            return {
                'success': False,
                'error': 'buyer_id is required'
            }
        
        if not negotiation_data or 'agreed_price' not in negotiation_data:
            return {
                'success': False,
                'error': 'negotiation_data with agreed_price is required'
            }
        
        result = buyer_tools.initiate_transaction(listing_id, buyer_id, negotiation_data)
        logger.info(f"Transaction initiated: {result.get('transaction_id')}")
        return result
    
    except Exception as e:
        logger.error(f"Transaction initiation error: {e}")
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
    # Test event for buyer registration
    test_event_buyer = {
        'action': 'register_buyer',
        'buyer_data': {
            'business_name': 'Fresh Produce Traders',
            'contact_person': 'Rajesh Kumar',
            'phone_number': '+919876543210',
            'email': 'rajesh@freshproduce.com',
            'business_type': 'wholesaler',
            'location': {
                'state': 'Delhi',
                'district': 'Central Delhi',
                'latitude': 28.6139,
                'longitude': 77.2090
            },
            'crop_interests': ['wheat', 'rice', 'potato'],
            'payment_terms': 'advance_50_percent'
        }
    }
    
    result = lambda_handler(test_event_buyer, None)
    print("Buyer Registration Test:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test event for crop listing
    test_event_listing = {
        'action': 'create_listing',
        'farmer_id': 'farmer_12345',
        'listing_data': {
            'crop_name': 'wheat',
            'quantity': 100,
            'unit': 'quintal',
            'quality_grade': 'grade_a',
            'expected_price': 2500,
            'harvest_date': '2024-04-15',
            'location': {
                'state': 'Uttar Pradesh',
                'district': 'Ghaziabad',
                'latitude': 28.6692,
                'longitude': 77.4538
            },
            'description': 'High quality wheat, well-maintained crop'
        }
    }
    
    result2 = lambda_handler(test_event_listing, None)
    print("\n" + "="*50 + "\n")
    print("Crop Listing Test:")
    print(json.dumps(json.loads(result2['body']), indent=2))
    
    # Test event for quality standards
    test_event_quality = {
        'action': 'get_quality_standards',
        'crop_name': 'wheat'
    }
    
    result3 = lambda_handler(test_event_quality, None)
    print("\n" + "="*50 + "\n")
    print("Quality Standards Test:")
    print(json.dumps(json.loads(result3['body']), indent=2))
