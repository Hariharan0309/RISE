"""
RISE Scheme Discovery Lambda Function
AWS Lambda handler for scheme discovery and eligibility checking
"""

import json
import logging
import os
from typing import Dict, Any
from scheme_discovery_tools import SchemeDiscoveryTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize scheme discovery tools
discovery_tools = SchemeDiscoveryTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for scheme discovery requests
    
    Event structure:
    {
        "action": "analyze_profile" | "check_eligibility" | "recommend_schemes" | "calculate_benefits" | "prioritize_schemes",
        "farmer_profile": dict (for analyze_profile, check_eligibility, recommend_schemes),
        "scheme_id": str (for check_eligibility, calculate_benefits),
        "schemes": list (for prioritize_schemes)
    }
    
    Returns:
        API Gateway response with discovery data
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'recommend_schemes')
        
        logger.info(f"Scheme discovery request: action={action}")
        
        # Route to appropriate handler
        if action == 'analyze_profile':
            result = handle_analyze_profile(body)
        elif action == 'check_eligibility':
            result = handle_check_eligibility(body)
        elif action == 'recommend_schemes':
            result = handle_recommend_schemes(body)
        elif action == 'calculate_benefits':
            result = handle_calculate_benefits(body)
        elif action == 'prioritize_schemes':
            result = handle_prioritize_schemes(body)
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


def handle_analyze_profile(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle farmer profile analysis request"""
    try:
        farmer_profile = body.get('farmer_profile')
        
        if not farmer_profile:
            return {
                'success': False,
                'error': 'farmer_profile is required'
            }
        
        result = discovery_tools.analyze_farmer_profile(farmer_profile)
        
        logger.info(f"Profile analysis completed for farmer: {farmer_profile.get('name', 'unknown')}")
        return result
    
    except Exception as e:
        logger.error(f"Profile analysis error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_check_eligibility(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle eligibility checking request"""
    try:
        farmer_profile = body.get('farmer_profile')
        scheme_id = body.get('scheme_id')
        
        if not farmer_profile or not scheme_id:
            return {
                'success': False,
                'error': 'farmer_profile and scheme_id are required'
            }
        
        result = discovery_tools.check_eligibility(farmer_profile, scheme_id)
        
        logger.info(f"Eligibility check completed: {scheme_id} - {result.get('eligible', False)}")
        return result
    
    except Exception as e:
        logger.error(f"Eligibility check error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_recommend_schemes(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle scheme recommendation request"""
    try:
        farmer_profile = body.get('farmer_profile')
        
        if not farmer_profile:
            return {
                'success': False,
                'error': 'farmer_profile is required'
            }
        
        result = discovery_tools.recommend_schemes(farmer_profile)
        
        logger.info(f"Scheme recommendations generated: {result.get('count', 0)} schemes")
        return result
    
    except Exception as e:
        logger.error(f"Scheme recommendation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_calculate_benefits(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle benefit calculation request"""
    try:
        farmer_profile = body.get('farmer_profile')
        scheme_id = body.get('scheme_id')
        
        if not farmer_profile or not scheme_id:
            return {
                'success': False,
                'error': 'farmer_profile and scheme_id are required'
            }
        
        result = discovery_tools.calculate_benefit_amount(farmer_profile, scheme_id)
        
        logger.info(f"Benefit calculation completed: {scheme_id}")
        return result
    
    except Exception as e:
        logger.error(f"Benefit calculation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_prioritize_schemes(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle scheme prioritization request"""
    try:
        schemes = body.get('schemes')
        
        if not schemes:
            return {
                'success': False,
                'error': 'schemes list is required'
            }
        
        result = discovery_tools.prioritize_schemes(schemes)
        
        logger.info(f"Scheme prioritization completed: {len(schemes)} schemes")
        return result
    
    except Exception as e:
        logger.error(f"Scheme prioritization error: {e}")
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
    # Test event for profile analysis
    test_profile = {
        'name': 'Ravi Kumar',
        'location': {
            'state': 'uttar pradesh',
            'district': 'lucknow'
        },
        'farm_details': {
            'land_size': 2.0,
            'soil_type': 'loamy',
            'crops': ['wheat', 'rice'],
            'farming_experience': '10 years'
        },
        'annual_income': 150000,
        'farmer_category': 'small'
    }
    
    test_event = {
        'action': 'recommend_schemes',
        'farmer_profile': test_profile
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2))
