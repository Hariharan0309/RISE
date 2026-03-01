"""
AWS Lambda handler for crop selection recommendations
"""

import json
import logging
from typing import Dict, Any
from crop_selection_tools import CropSelectionTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize tools
crop_tools = CropSelectionTools()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for crop selection operations
    
    Event structure:
    {
        "operation": "recommend_crops" | "calculate_profitability" | "generate_calendar" | "compare_crops",
        "parameters": {
            // Operation-specific parameters
        }
    }
    
    Args:
        event: Lambda event
        context: Lambda context
    
    Returns:
        Response with operation results
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract operation and parameters
        operation = event.get('operation')
        parameters = event.get('parameters', {})
        
        if not operation:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing operation parameter'
                })
            }
        
        # Route to appropriate operation
        if operation == 'recommend_crops':
            result = handle_recommend_crops(parameters)
        
        elif operation == 'calculate_profitability':
            result = handle_calculate_profitability(parameters)
        
        elif operation == 'generate_calendar':
            result = handle_generate_calendar(parameters)
        
        elif operation == 'compare_crops':
            result = handle_compare_crops(parameters)
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f'Unknown operation: {operation}'
                })
            }
        
        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
    
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


def handle_recommend_crops(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle crop recommendation request"""
    
    soil_analysis = parameters.get('soil_analysis')
    location = parameters.get('location')
    farm_size_acres = parameters.get('farm_size_acres')
    climate_data = parameters.get('climate_data')
    market_preferences = parameters.get('market_preferences')
    farmer_experience = parameters.get('farmer_experience')
    
    if not all([soil_analysis, location, farm_size_acres]):
        raise ValueError('Missing required parameters: soil_analysis, location, farm_size_acres')
    
    result = crop_tools.recommend_crops(
        soil_analysis=soil_analysis,
        location=location,
        farm_size_acres=farm_size_acres,
        climate_data=climate_data,
        market_preferences=market_preferences,
        farmer_experience=farmer_experience
    )
    
    return result


def handle_calculate_profitability(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle profitability calculation request"""
    
    crop_name = parameters.get('crop_name')
    farm_size_acres = parameters.get('farm_size_acres')
    location = parameters.get('location')
    soil_type = parameters.get('soil_type')
    input_costs = parameters.get('input_costs')
    market_price = parameters.get('market_price')
    
    if not all([crop_name, farm_size_acres, location, soil_type]):
        raise ValueError('Missing required parameters: crop_name, farm_size_acres, location, soil_type')
    
    result = crop_tools.calculate_crop_profitability(
        crop_name=crop_name,
        farm_size_acres=farm_size_acres,
        location=location,
        soil_type=soil_type,
        input_costs=input_costs,
        market_price=market_price
    )
    
    return result


def handle_generate_calendar(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle seasonal calendar generation request"""
    
    location = parameters.get('location')
    soil_type = parameters.get('soil_type')
    farm_size_acres = parameters.get('farm_size_acres')
    selected_crops = parameters.get('selected_crops')
    
    if not all([location, soil_type, farm_size_acres]):
        raise ValueError('Missing required parameters: location, soil_type, farm_size_acres')
    
    result = crop_tools.generate_seasonal_calendar(
        location=location,
        soil_type=soil_type,
        farm_size_acres=farm_size_acres,
        selected_crops=selected_crops
    )
    
    return result


def handle_compare_crops(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle crop comparison request"""
    
    crop_list = parameters.get('crop_list')
    soil_analysis = parameters.get('soil_analysis')
    location = parameters.get('location')
    farm_size_acres = parameters.get('farm_size_acres')
    comparison_criteria = parameters.get('comparison_criteria')
    
    if not all([crop_list, soil_analysis, location, farm_size_acres]):
        raise ValueError('Missing required parameters: crop_list, soil_analysis, location, farm_size_acres')
    
    result = crop_tools.compare_crop_options(
        crop_list=crop_list,
        soil_analysis=soil_analysis,
        location=location,
        farm_size_acres=farm_size_acres,
        comparison_criteria=comparison_criteria
    )
    
    return result
