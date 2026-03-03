"""
RISE Climate-Adaptive Recommendations Lambda Function
AWS Lambda handler for climate data analysis and adaptive recommendations
"""

import json
import logging
import os
from typing import Dict, Any
from tools.climate_adaptive_tools import ClimateAdaptiveTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize climate-adaptive tools
climate_tools = ClimateAdaptiveTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for climate-adaptive recommendation requests
    
    Event structure:
    {
        "action": "analyze_climate" | "crop_varieties" | "water_techniques" | "seasonal_advice",
        "location": {"name": str, "latitude": float, "longitude": float},
        "historical_weather": [...] (for analyze_climate),
        "current_season": str (for analyze_climate, seasonal_advice),
        "climate_risks": [...] (for crop_varieties),
        "soil_type": str (optional, for crop_varieties),
        "water_scarcity_level": str (for water_techniques),
        "crop_type": str (optional),
        "climate_trends": {...} (for seasonal_advice),
        "farmer_profile": {...} (optional, for seasonal_advice)
    }
    
    Returns:
        API Gateway response with climate-adaptive recommendations
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'analyze_climate')
        location = body.get('location', {})
        
        logger.info(f"Climate-adaptive request: action={action}, location={location.get('name')}")
        
        # Route to appropriate handler
        if action == 'analyze_climate':
            result = handle_climate_analysis(body)
        elif action == 'crop_varieties':
            result = handle_crop_varieties(body)
        elif action == 'water_techniques':
            result = handle_water_techniques(body)
        elif action == 'seasonal_advice':
            result = handle_seasonal_advice(body)
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
                'Cache-Control': 'max-age=86400'  # 24 hours
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


def handle_climate_analysis(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle climate data analysis request"""
    try:
        location = body.get('location', {})
        historical_weather = body.get('historical_weather', [])
        current_season = body.get('current_season', 'Kharif')
        
        # Validate inputs
        if not location or not historical_weather:
            return {
                'success': False,
                'error': 'Location and historical weather data are required'
            }
        
        result = climate_tools.analyze_climate_data(
            location, historical_weather, current_season
        )
        
        logger.info(f"Climate analysis completed: {result.get('analysis_id')}")
        return result
    
    except Exception as e:
        logger.error(f"Climate analysis error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_crop_varieties(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle resilient crop variety recommendations"""
    try:
        location = body.get('location', {})
        climate_risks = body.get('climate_risks', [])
        soil_type = body.get('soil_type')
        
        # Validate inputs
        if not location or not climate_risks:
            return {
                'success': False,
                'error': 'Location and climate risks are required'
            }
        
        result = climate_tools.get_resilient_crop_varieties(
            location, climate_risks, soil_type
        )
        
        logger.info(f"Crop variety recommendations generated for {location.get('name')}")
        return result
    
    except Exception as e:
        logger.error(f"Crop variety recommendation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_water_techniques(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle water-efficient technique recommendations"""
    try:
        location = body.get('location', {})
        water_scarcity_level = body.get('water_scarcity_level', 'medium')
        crop_type = body.get('crop_type')
        
        # Validate inputs
        if not location:
            return {
                'success': False,
                'error': 'Location is required'
            }
        
        # Validate water scarcity level
        valid_levels = ['low', 'medium', 'high', 'severe']
        if water_scarcity_level not in valid_levels:
            return {
                'success': False,
                'error': f'Water scarcity level must be one of: {", ".join(valid_levels)}'
            }
        
        result = climate_tools.get_water_efficient_techniques(
            location, water_scarcity_level, crop_type
        )
        
        logger.info(f"Water-efficient techniques recommended for {location.get('name')}")
        return result
    
    except Exception as e:
        logger.error(f"Water technique recommendation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_seasonal_advice(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle seasonal farming advice generation"""
    try:
        location = body.get('location', {})
        season = body.get('current_season', 'Kharif')
        climate_trends = body.get('climate_trends', {})
        farmer_profile = body.get('farmer_profile')
        
        # Validate inputs
        if not location or not climate_trends:
            return {
                'success': False,
                'error': 'Location and climate trends are required'
            }
        
        result = climate_tools.generate_seasonal_advice(
            location, season, climate_trends, farmer_profile
        )
        
        logger.info(f"Seasonal advice generated for {location.get('name')}, season: {season}")
        return result
    
    except Exception as e:
        logger.error(f"Seasonal advice generation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# For local testing
if __name__ == '__main__':
    # Test event for climate analysis
    test_event = {
        'action': 'analyze_climate',
        'location': {
            'name': 'Pune, Maharashtra',
            'latitude': 18.5204,
            'longitude': 73.8567
        },
        'historical_weather': [
            {'date': '2024-01-01', 'temp_avg': 28, 'temp_max': 35, 'temp_min': 22, 'rainfall': 0},
            {'date': '2024-01-02', 'temp_avg': 29, 'temp_max': 36, 'temp_min': 23, 'rainfall': 0},
            {'date': '2024-01-03', 'temp_avg': 30, 'temp_max': 37, 'temp_min': 24, 'rainfall': 2},
            {'date': '2024-01-04', 'temp_avg': 31, 'temp_max': 38, 'temp_min': 25, 'rainfall': 0},
            {'date': '2024-01-05', 'temp_avg': 32, 'temp_max': 39, 'temp_min': 26, 'rainfall': 0}
        ],
        'current_season': 'Rabi'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2))
