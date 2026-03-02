"""
RISE Optimal Selling Time Lambda Function
AWS Lambda handler for selling time recommendations and price alerts
"""

import json
import logging
import os
from typing import Dict, Any
from selling_time_tools import SellingTimeTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize selling time tools
selling_tools = SellingTimeTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for selling time requests
    
    Event structure:
    {
        "action": "analyze_perishability" | "calculate_storage_costs" | 
                  "calculate_optimal_time" | "create_alert" | "check_alerts" | 
                  "get_alerts" | "delete_alert",
        "crop_name": str,
        "quantity_quintals": float (optional),
        "storage_days": int (optional),
        "storage_type": str (optional),
        "current_price": float (optional),
        "predicted_prices": list (optional),
        "storage_capacity": bool (optional),
        "user_id": str (for alerts),
        "target_price": float (for create_alert),
        "market_id": str (for alerts),
        "alert_id": str (for delete_alert)
    }
    
    Returns:
        API Gateway response with selling time data
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'analyze_perishability')
        
        logger.info(f"Selling time request: action={action}")
        
        # Route to appropriate handler
        if action == 'analyze_perishability':
            result = handle_analyze_perishability(body)
        elif action == 'calculate_storage_costs':
            result = handle_calculate_storage_costs(body)
        elif action == 'calculate_optimal_time':
            result = handle_calculate_optimal_time(body)
        elif action == 'create_alert':
            result = handle_create_alert(body)
        elif action == 'check_alerts':
            result = handle_check_alerts(body)
        elif action == 'get_alerts':
            result = handle_get_alerts(body)
        elif action == 'delete_alert':
            result = handle_delete_alert(body)
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


def handle_analyze_perishability(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle perishability analysis request"""
    try:
        crop_name = body.get('crop_name', '').strip()
        
        if not crop_name:
            return {
                'success': False,
                'error': 'crop_name is required'
            }
        
        result = selling_tools.analyze_perishability(crop_name)
        logger.info(f"Perishability analyzed: crop={crop_name}")
        return result
    
    except Exception as e:
        logger.error(f"Perishability analysis error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_calculate_storage_costs(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle storage cost calculation request"""
    try:
        crop_name = body.get('crop_name', '').strip()
        quantity_quintals = float(body.get('quantity_quintals', 0))
        storage_days = int(body.get('storage_days', 0))
        storage_type = body.get('storage_type', 'standard')
        
        if not crop_name:
            return {
                'success': False,
                'error': 'crop_name is required'
            }
        
        if quantity_quintals <= 0:
            return {
                'success': False,
                'error': 'quantity_quintals must be greater than 0'
            }
        
        if storage_days <= 0:
            return {
                'success': False,
                'error': 'storage_days must be greater than 0'
            }
        
        result = selling_tools.calculate_storage_costs(
            crop_name,
            quantity_quintals,
            storage_days,
            storage_type
        )
        logger.info(f"Storage costs calculated: crop={crop_name}, days={storage_days}")
        return result
    
    except ValueError as e:
        return {
            'success': False,
            'error': f'Invalid numeric value: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Storage cost calculation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_calculate_optimal_time(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle optimal selling time calculation request"""
    try:
        crop_name = body.get('crop_name', '').strip()
        current_price = float(body.get('current_price', 0))
        predicted_prices = body.get('predicted_prices', [])
        quantity_quintals = float(body.get('quantity_quintals', 100))
        storage_capacity = body.get('storage_capacity', True)
        storage_type = body.get('storage_type', 'standard')
        
        if not crop_name:
            return {
                'success': False,
                'error': 'crop_name is required'
            }
        
        if current_price <= 0:
            return {
                'success': False,
                'error': 'current_price must be greater than 0'
            }
        
        result = selling_tools.calculate_optimal_selling_time(
            crop_name,
            current_price,
            predicted_prices,
            quantity_quintals,
            storage_capacity,
            storage_type
        )
        logger.info(f"Optimal selling time calculated: crop={crop_name}")
        return result
    
    except ValueError as e:
        return {
            'success': False,
            'error': f'Invalid numeric value: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Optimal selling time calculation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_create_alert(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle price alert creation request"""
    try:
        user_id = body.get('user_id', '').strip()
        crop_name = body.get('crop_name', '').strip()
        target_price = float(body.get('target_price', 0))
        market_id = body.get('market_id', '').strip()
        phone_number = body.get('phone_number')
        email = body.get('email')
        
        if not user_id:
            return {
                'success': False,
                'error': 'user_id is required'
            }
        
        if not crop_name:
            return {
                'success': False,
                'error': 'crop_name is required'
            }
        
        if target_price <= 0:
            return {
                'success': False,
                'error': 'target_price must be greater than 0'
            }
        
        if not market_id:
            return {
                'success': False,
                'error': 'market_id is required'
            }
        
        result = selling_tools.create_price_alert(
            user_id,
            crop_name,
            target_price,
            market_id,
            phone_number,
            email
        )
        logger.info(f"Price alert created: user={user_id}, crop={crop_name}")
        return result
    
    except ValueError as e:
        return {
            'success': False,
            'error': f'Invalid numeric value: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Price alert creation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_check_alerts(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle price alert checking request"""
    try:
        user_id = body.get('user_id', '').strip()
        current_prices = body.get('current_prices', {})
        
        if not user_id:
            return {
                'success': False,
                'error': 'user_id is required'
            }
        
        result = selling_tools.check_price_alerts(user_id, current_prices)
        logger.info(f"Price alerts checked: user={user_id}")
        return result
    
    except Exception as e:
        logger.error(f"Price alert check error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_get_alerts(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get user alerts request"""
    try:
        user_id = body.get('user_id', '').strip()
        
        if not user_id:
            return {
                'success': False,
                'error': 'user_id is required'
            }
        
        result = selling_tools.get_user_alerts(user_id)
        logger.info(f"User alerts retrieved: user={user_id}")
        return result
    
    except Exception as e:
        logger.error(f"Get alerts error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_delete_alert(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle alert deletion request"""
    try:
        alert_id = body.get('alert_id', '').strip()
        
        if not alert_id:
            return {
                'success': False,
                'error': 'alert_id is required'
            }
        
        result = selling_tools.delete_alert(alert_id)
        logger.info(f"Alert deleted: alert_id={alert_id}")
        return result
    
    except Exception as e:
        logger.error(f"Alert deletion error: {e}")
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
    # Test perishability analysis
    test_event1 = {
        'action': 'analyze_perishability',
        'crop_name': 'tomato'
    }
    
    result1 = lambda_handler(test_event1, None)
    print("Perishability Analysis:")
    print(json.dumps(json.loads(result1['body']), indent=2))
    
    # Test storage cost calculation
    test_event2 = {
        'action': 'calculate_storage_costs',
        'crop_name': 'wheat',
        'quantity_quintals': 100,
        'storage_days': 30,
        'storage_type': 'warehouse'
    }
    
    result2 = lambda_handler(test_event2, None)
    print("\n" + "="*50 + "\n")
    print("Storage Costs:")
    print(json.dumps(json.loads(result2['body']), indent=2))
