"""
RISE Market Price Tracking Lambda Function
AWS Lambda handler for market price data aggregation and analysis
"""

import json
import logging
import os
from typing import Dict, Any
from market_price_tools import MarketPriceTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize market price tools
market_tools = MarketPriceTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for market price requests
    
    Event structure:
    {
        "action": "current_prices" | "price_history" | "predict_trends" | "optimal_selling_time",
        "crop_name": str,
        "latitude": float (for current_prices, optimal_selling_time),
        "longitude": float (for current_prices, optimal_selling_time),
        "radius_km": int (optional, default 50),
        "market_id": str (for price_history, predict_trends),
        "days": int (optional, for price_history),
        "forecast_days": int (optional, for predict_trends),
        "storage_capacity": bool (optional, for optimal_selling_time),
        "harvest_date": str (optional, ISO format)
    }
    
    Returns:
        API Gateway response with market price data
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'current_prices')
        crop_name = body.get('crop_name', '').strip()
        
        if not crop_name:
            return error_response(400, 'crop_name is required')
        
        logger.info(f"Market price request: action={action}, crop={crop_name}")
        
        # Route to appropriate handler
        if action == 'current_prices':
            result = handle_current_prices(body)
        elif action == 'price_history':
            result = handle_price_history(body)
        elif action == 'predict_trends':
            result = handle_predict_trends(body)
        elif action == 'optimal_selling_time':
            result = handle_optimal_selling_time(body)
        else:
            return error_response(400, f'Invalid action: {action}')
        
        # Return response
        status_code = 200 if result.get('success') else 500
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'max-age=21600'  # 6 hours
            },
            'body': json.dumps(result, default=str)
        }
    
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return error_response(400, f'Invalid input: {str(e)}')
    
    except Exception as e:
        logger.error(f"Lambda error: {e}", exc_info=True)
        return error_response(500, 'Internal server error')


def handle_current_prices(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle current market prices request"""
    try:
        crop_name = body['crop_name']
        latitude = float(body.get('latitude'))
        longitude = float(body.get('longitude'))
        radius_km = int(body.get('radius_km', 50))
        
        # Validate radius
        if radius_km < 1 or radius_km > 200:
            return {
                'success': False,
                'error': 'radius_km must be between 1 and 200'
            }
        
        result = market_tools.get_current_prices(crop_name, latitude, longitude, radius_km)
        logger.info(f"Current prices fetched: from_cache={result.get('from_cache', False)}")
        return result
    
    except KeyError as e:
        return {
            'success': False,
            'error': f'Missing required parameter: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Current prices error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_price_history(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle price history request"""
    try:
        crop_name = body['crop_name']
        market_id = body.get('market_id')
        
        if not market_id:
            return {
                'success': False,
                'error': 'market_id is required for price history'
            }
        
        days = int(body.get('days', 30))
        
        # Validate days
        if days < 1 or days > 365:
            return {
                'success': False,
                'error': 'days must be between 1 and 365'
            }
        
        result = market_tools.get_price_history(crop_name, market_id, days)
        logger.info(f"Price history fetched: crop={crop_name}, market={market_id}, days={days}")
        return result
    
    except KeyError as e:
        return {
            'success': False,
            'error': f'Missing required parameter: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Price history error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_predict_trends(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle price trend prediction request"""
    try:
        crop_name = body['crop_name']
        market_id = body.get('market_id')
        
        if not market_id:
            return {
                'success': False,
                'error': 'market_id is required for price predictions'
            }
        
        forecast_days = int(body.get('forecast_days', 7))
        
        # Validate forecast days
        if forecast_days < 1 or forecast_days > 30:
            return {
                'success': False,
                'error': 'forecast_days must be between 1 and 30'
            }
        
        result = market_tools.predict_price_trends(crop_name, market_id, forecast_days)
        logger.info(f"Price trends predicted: crop={crop_name}, market={market_id}, days={forecast_days}")
        return result
    
    except KeyError as e:
        return {
            'success': False,
            'error': f'Missing required parameter: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Price prediction error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_optimal_selling_time(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle optimal selling time calculation request"""
    try:
        crop_name = body['crop_name']
        latitude = float(body.get('latitude'))
        longitude = float(body.get('longitude'))
        harvest_date = body.get('harvest_date')
        storage_capacity = body.get('storage_capacity', True)
        
        result = market_tools.get_optimal_selling_time(
            crop_name,
            latitude,
            longitude,
            harvest_date,
            storage_capacity
        )
        logger.info(f"Optimal selling time calculated: crop={crop_name}")
        return result
    
    except KeyError as e:
        return {
            'success': False,
            'error': f'Missing required parameter: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Optimal selling time error: {e}")
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
    # Test event for current prices
    test_event = {
        'action': 'current_prices',
        'crop_name': 'wheat',
        'latitude': 28.6139,
        'longitude': 77.2090,
        'radius_km': 50
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test event for optimal selling time
    test_event2 = {
        'action': 'optimal_selling_time',
        'crop_name': 'wheat',
        'latitude': 28.6139,
        'longitude': 77.2090,
        'storage_capacity': True
    }
    
    result2 = lambda_handler(test_event2, None)
    print("\n" + "="*50 + "\n")
    print(json.dumps(json.loads(result2['body']), indent=2))
