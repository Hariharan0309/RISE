"""
RISE Weather Data Lambda Function
AWS Lambda handler for weather data fetching and caching
"""

import json
import logging
import os
from typing import Dict, Any
from weather_tools import WeatherTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize weather tools
weather_tools = WeatherTools(
    region=os.environ.get('AWS_REGION', 'us-east-1'),
    api_key=os.environ.get('OPENWEATHER_API_KEY', '')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for weather data requests
    
    Event structure:
    {
        "action": "current" | "forecast" | "insights",
        "latitude": float,
        "longitude": float,
        "location_name": str (optional),
        "days": int (optional, for forecast)
    }
    
    Returns:
        API Gateway response with weather data
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'current')
        latitude = float(body.get('latitude'))
        longitude = float(body.get('longitude'))
        location_name = body.get('location_name')
        
        logger.info(f"Weather request: action={action}, lat={latitude}, lon={longitude}")
        
        # Route to appropriate handler
        if action == 'current':
            result = handle_current_weather(latitude, longitude, location_name)
        elif action == 'forecast':
            days = int(body.get('days', 5))
            result = handle_forecast(latitude, longitude, days, location_name)
        elif action == 'insights':
            result = handle_farming_insights(latitude, longitude, location_name)
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'Invalid action: {action}'
                })
            }
        
        # Return response
        status_code = 200 if result.get('success') else 500
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'max-age=21600'  # 6 hours
            },
            'body': json.dumps(result)
        }
    
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'Invalid input: {str(e)}'
            })
        }
    
    except Exception as e:
        logger.error(f"Lambda error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error'
            })
        }


def handle_current_weather(latitude: float, 
                          longitude: float, 
                          location_name: str = None) -> Dict[str, Any]:
    """Handle current weather request"""
    try:
        result = weather_tools.get_current_weather(latitude, longitude, location_name)
        logger.info(f"Current weather fetched: from_cache={result.get('from_cache', False)}")
        return result
    except Exception as e:
        logger.error(f"Current weather error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_forecast(latitude: float,
                   longitude: float,
                   days: int,
                   location_name: str = None) -> Dict[str, Any]:
    """Handle forecast request"""
    try:
        # Validate days
        if days < 1 or days > 5:
            return {
                'success': False,
                'error': 'Days must be between 1 and 5'
            }
        
        result = weather_tools.get_forecast(latitude, longitude, days, location_name)
        logger.info(f"Forecast fetched: days={days}, from_cache={result.get('from_cache', False)}")
        return result
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_farming_insights(latitude: float,
                           longitude: float,
                           location_name: str = None) -> Dict[str, Any]:
    """Handle farming insights request"""
    try:
        result = weather_tools.get_farming_weather_insights(latitude, longitude, location_name)
        logger.info(f"Farming insights generated for ({latitude}, {longitude})")
        return result
    except Exception as e:
        logger.error(f"Farming insights error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# For local testing
if __name__ == '__main__':
    # Test event
    test_event = {
        'action': 'insights',
        'latitude': 28.6139,  # New Delhi
        'longitude': 77.2090,
        'location_name': 'New Delhi'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2))
