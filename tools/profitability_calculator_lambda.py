"""
RISE Crop Profitability Calculator Lambda Function
AWS Lambda handler for comprehensive crop profitability analysis
"""

import json
import logging
import os
from typing import Dict, Any
from profitability_calculator_tools import ProfitabilityCalculatorTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize profitability calculator tools
profitability_tools = ProfitabilityCalculatorTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for crop profitability analysis requests
    
    Event structure:
    {
        "action": "calculate_profitability" | "compare_crops" | "estimate_costs" | "predict_yield",
        "crop_name": str,
        "farm_size_acres": float,
        "location": {"state": str, "district": str, "latitude": float, "longitude": float},
        "soil_type": str (optional),
        "season": str (optional),
        "input_costs": dict (optional),
        "crop_list": list (for compare_crops),
        "historical_data": dict (optional)
    }
    
    Returns:
        API Gateway response with profitability analysis
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'calculate_profitability')
        
        logger.info(f"Profitability request: action={action}")
        
        # Route to appropriate handler
        if action == 'calculate_profitability':
            result = handle_calculate_profitability(body)
        elif action == 'compare_crops':
            result = handle_compare_crops(body)
        elif action == 'estimate_costs':
            result = handle_estimate_costs(body)
        elif action == 'predict_yield':
            result = handle_predict_yield(body)
        else:
            return error_response(400, f'Invalid action: {action}')
        
        # Return response
        status_code = 200 if result.get('success') else 500
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'max-age=3600'  # 1 hour
            },
            'body': json.dumps(result, default=str)
        }
    
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return error_response(400, f'Invalid input: {str(e)}')
    
    except Exception as e:
        logger.error(f"Lambda error: {e}", exc_info=True)
        return error_response(500, 'Internal server error')


def handle_calculate_profitability(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle comprehensive profitability calculation request"""
    try:
        crop_name = body.get('crop_name', '').strip()
        farm_size_acres = float(body.get('farm_size_acres', 0))
        location = body.get('location', {})
        
        if not crop_name or farm_size_acres <= 0:
            return {
                'success': False,
                'error': 'crop_name and valid farm_size_acres are required'
            }
        
        if not location or 'latitude' not in location or 'longitude' not in location:
            return {
                'success': False,
                'error': 'location with latitude and longitude is required'
            }
        
        soil_type = body.get('soil_type', 'loamy')
        season = body.get('season')
        input_costs = body.get('input_costs')
        historical_data = body.get('historical_data')
        
        result = profitability_tools.calculate_comprehensive_profitability(
            crop_name=crop_name,
            farm_size_acres=farm_size_acres,
            location=location,
            soil_type=soil_type,
            season=season,
            custom_input_costs=input_costs,
            historical_data=historical_data
        )
        
        logger.info(f"Profitability calculated: crop={crop_name}, farm_size={farm_size_acres}")
        return result
    
    except KeyError as e:
        return {
            'success': False,
            'error': f'Missing required parameter: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Profitability calculation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_compare_crops(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle crop profitability comparison request"""
    try:
        crop_list = body.get('crop_list', [])
        farm_size_acres = float(body.get('farm_size_acres', 0))
        location = body.get('location', {})
        
        if not crop_list or len(crop_list) < 2:
            return {
                'success': False,
                'error': 'crop_list with at least 2 crops is required'
            }
        
        if farm_size_acres <= 0:
            return {
                'success': False,
                'error': 'valid farm_size_acres is required'
            }
        
        soil_type = body.get('soil_type', 'loamy')
        season = body.get('season')
        
        result = profitability_tools.compare_crop_profitability(
            crop_list=crop_list,
            farm_size_acres=farm_size_acres,
            location=location,
            soil_type=soil_type,
            season=season
        )
        
        logger.info(f"Crops compared: {', '.join(crop_list)}")
        return result
    
    except Exception as e:
        logger.error(f"Crop comparison error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_estimate_costs(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle cost estimation request"""
    try:
        crop_name = body.get('crop_name', '').strip()
        farm_size_acres = float(body.get('farm_size_acres', 0))
        location = body.get('location', {})
        
        if not crop_name or farm_size_acres <= 0:
            return {
                'success': False,
                'error': 'crop_name and valid farm_size_acres are required'
            }
        
        soil_type = body.get('soil_type', 'loamy')
        season = body.get('season')
        
        result = profitability_tools.estimate_input_costs(
            crop_name=crop_name,
            farm_size_acres=farm_size_acres,
            location=location,
            soil_type=soil_type,
            season=season
        )
        
        logger.info(f"Costs estimated: crop={crop_name}")
        return result
    
    except Exception as e:
        logger.error(f"Cost estimation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_predict_yield(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle yield prediction request"""
    try:
        crop_name = body.get('crop_name', '').strip()
        location = body.get('location', {})
        
        if not crop_name:
            return {
                'success': False,
                'error': 'crop_name is required'
            }
        
        soil_type = body.get('soil_type', 'loamy')
        season = body.get('season')
        historical_data = body.get('historical_data')
        
        result = profitability_tools.predict_crop_yield(
            crop_name=crop_name,
            location=location,
            soil_type=soil_type,
            season=season,
            historical_data=historical_data
        )
        
        logger.info(f"Yield predicted: crop={crop_name}")
        return result
    
    except Exception as e:
        logger.error(f"Yield prediction error: {e}")
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
    # Test event for profitability calculation
    test_event = {
        'action': 'calculate_profitability',
        'crop_name': 'wheat',
        'farm_size_acres': 5.0,
        'location': {
            'state': 'Punjab',
            'district': 'Ludhiana',
            'latitude': 30.9010,
            'longitude': 75.8573
        },
        'soil_type': 'loamy',
        'season': 'rabi'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2))
