"""
AWS Lambda Handler for Supplier Negotiation Operations
Handles API Gateway requests for supplier negotiation functionality
"""

import json
import logging
from typing import Dict, Any
from supplier_negotiation_tools import create_supplier_negotiation_tools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for supplier negotiation operations
    
    Args:
        event: API Gateway event
        context: Lambda context
    
    Returns:
        API Gateway response
    """
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        operation = body.get('operation')
        
        logger.info(f"Processing operation: {operation}")
        
        # Initialize tools
        tools = create_supplier_negotiation_tools()
        
        # Route to appropriate handler
        handlers = {
            'register_supplier': handle_register_supplier,
            'find_suppliers': handle_find_suppliers,
            'generate_request': handle_generate_request,
            'submit_quote': handle_submit_quote,
            'compare_quotes': handle_compare_quotes,
            'verify_quality': handle_verify_quality,
            'coordinate_delivery': handle_coordinate_delivery,
            'manage_payment': handle_manage_payment,
            'get_status': handle_get_status
        }
        
        handler = handlers.get(operation)
        if not handler:
            return create_response(400, {
                'success': False,
                'error': f'Unknown operation: {operation}'
            })
        
        result = handler(tools, body)
        return create_response(200, result)
    
    except Exception as e:
        logger.error(f"Lambda handler error: {e}", exc_info=True)
        return create_response(500, {
            'success': False,
            'error': str(e)
        })


def handle_register_supplier(tools, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle supplier registration"""
    try:
        supplier_data = body.get('supplier_data', {})
        
        if not supplier_data:
            return {
                'success': False,
                'error': 'supplier_data is required'
            }
        
        # Validate required fields
        required_fields = ['business_name', 'contact_person', 'phone_number', 'supplier_type', 'location']
        for field in required_fields:
            if field not in supplier_data:
                return {
                    'success': False,
                    'error': f'Missing required field: {field}'
                }
        
        result = tools.register_supplier(supplier_data)
        return result
    
    except Exception as e:
        logger.error(f"Register supplier error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_find_suppliers(tools, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle supplier search"""
    try:
        product_requirements = body.get('product_requirements', {})
        location = body.get('location', {})
        
        if not product_requirements:
            return {
                'success': False,
                'error': 'product_requirements is required'
            }
        
        if not location:
            return {
                'success': False,
                'error': 'location is required'
            }
        
        result = tools.find_suppliers(product_requirements, location)
        return result
    
    except Exception as e:
        logger.error(f"Find suppliers error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_generate_request(tools, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle bulk pricing request generation"""
    try:
        buyer_id = body.get('buyer_id')
        product_requirements = body.get('product_requirements', {})
        supplier_ids = body.get('supplier_ids', [])
        delivery_location = body.get('delivery_location', {})
        
        if not buyer_id:
            return {
                'success': False,
                'error': 'buyer_id is required'
            }
        
        if not product_requirements:
            return {
                'success': False,
                'error': 'product_requirements is required'
            }
        
        if not supplier_ids:
            return {
                'success': False,
                'error': 'supplier_ids is required'
            }
        
        result = tools.generate_bulk_pricing_request(
            buyer_id,
            product_requirements,
            supplier_ids,
            delivery_location
        )
        return result
    
    except Exception as e:
        logger.error(f"Generate request error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_submit_quote(tools, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle supplier quote submission"""
    try:
        negotiation_id = body.get('negotiation_id')
        supplier_id = body.get('supplier_id')
        quote_data = body.get('quote_data', {})
        
        if not negotiation_id:
            return {
                'success': False,
                'error': 'negotiation_id is required'
            }
        
        if not supplier_id:
            return {
                'success': False,
                'error': 'supplier_id is required'
            }
        
        if not quote_data:
            return {
                'success': False,
                'error': 'quote_data is required'
            }
        
        result = tools.submit_supplier_quote(negotiation_id, supplier_id, quote_data)
        return result
    
    except Exception as e:
        logger.error(f"Submit quote error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_compare_quotes(tools, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle quote comparison"""
    try:
        negotiation_id = body.get('negotiation_id')
        
        if not negotiation_id:
            return {
                'success': False,
                'error': 'negotiation_id is required'
            }
        
        result = tools.compare_quotes(negotiation_id)
        return result
    
    except Exception as e:
        logger.error(f"Compare quotes error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_verify_quality(tools, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle quality verification"""
    try:
        supplier_id = body.get('supplier_id')
        product_name = body.get('product_name')
        
        if not supplier_id:
            return {
                'success': False,
                'error': 'supplier_id is required'
            }
        
        if not product_name:
            return {
                'success': False,
                'error': 'product_name is required'
            }
        
        result = tools.verify_quality_assurance(supplier_id, product_name)
        return result
    
    except Exception as e:
        logger.error(f"Verify quality error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_coordinate_delivery(tools, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle delivery coordination"""
    try:
        negotiation_id = body.get('negotiation_id')
        selected_quote_id = body.get('selected_quote_id')
        delivery_details = body.get('delivery_details', {})
        
        if not negotiation_id:
            return {
                'success': False,
                'error': 'negotiation_id is required'
            }
        
        if not selected_quote_id:
            return {
                'success': False,
                'error': 'selected_quote_id is required'
            }
        
        result = tools.coordinate_delivery(negotiation_id, selected_quote_id, delivery_details)
        return result
    
    except Exception as e:
        logger.error(f"Coordinate delivery error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_manage_payment(tools, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle payment management"""
    try:
        negotiation_id = body.get('negotiation_id')
        payment_data = body.get('payment_data', {})
        
        if not negotiation_id:
            return {
                'success': False,
                'error': 'negotiation_id is required'
            }
        
        result = tools.manage_payment(negotiation_id, payment_data)
        return result
    
    except Exception as e:
        logger.error(f"Manage payment error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_get_status(tools, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle negotiation status retrieval"""
    try:
        negotiation_id = body.get('negotiation_id')
        
        if not negotiation_id:
            return {
                'success': False,
                'error': 'negotiation_id is required'
            }
        
        result = tools.get_negotiation_status(negotiation_id)
        return result
    
    except Exception as e:
        logger.error(f"Get status error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create API Gateway response
    
    Args:
        status_code: HTTP status code
        body: Response body
    
    Returns:
        API Gateway response dict
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(body)
    }


# For local testing
if __name__ == '__main__':
    # Test event
    test_event = {
        'body': json.dumps({
            'operation': 'find_suppliers',
            'product_requirements': {
                'wheat_seeds': 500,
                'fertilizer_urea': 300
            },
            'location': {
                'state': 'Punjab',
                'district': 'Ludhiana'
            }
        })
    }
    
    response = lambda_handler(test_event, None)
    print(json.dumps(json.loads(response['body']), indent=2))
