"""
AWS Lambda Function for Fertilizer Recommendations
Handles NPK calculations and precision fertilizer recommendations using Amazon Bedrock
"""

import json
import boto3
import uuid
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

# Configuration from environment variables
FARM_DATA_TABLE = os.environ.get('FARM_DATA_TABLE', 'RISE-FarmData')
BEDROCK_MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'

# DynamoDB table
farm_data_table = dynamodb.Table(FARM_DATA_TABLE)


def lambda_handler(event, context):
    """
    Lambda handler for fertilizer recommendations
    
    Expected event structure:
    {
        "body": {
            "action": "calculate_npk" | "get_recommendations" | "get_timing" | "track_growth",
            "soil_analysis": {...},
            "target_crop": "wheat",
            "farm_size_acres": 2.5,
            "growth_stage": "vegetative",
            "weather_forecast": {...},
            "budget_constraint": 15000,
            "user_id": "farmer_1234567890",
            "farm_id": "farm_abc123",
            "location": {"state": "...", "district": "..."}
        }
    }
    """
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract parameters
        action = body.get('action', 'calculate_npk')
        user_id = body.get('user_id')
        farm_id = body.get('farm_id')
        location = body.get('location', {})
        
        # Validate required fields
        if not user_id:
            return create_response(400, {
                'success': False,
                'error': 'Missing user_id in request'
            })
        
        if not farm_id:
            return create_response(400, {
                'success': False,
                'error': 'Missing farm_id in request'
            })
        
        # Route to appropriate handler
        if action == 'calculate_npk':
            result = handle_npk_calculation(body, user_id, farm_id, location)
        elif action == 'get_recommendations':
            result = handle_recommendations(body, user_id, farm_id, location)
        elif action == 'get_timing':
            result = handle_timing(body, user_id, farm_id, location)
        elif action == 'track_growth':
            result = handle_growth_tracking(body, user_id, farm_id, location)
        else:
            return create_response(400, {
                'success': False,
                'error': f'Invalid action: {action}'
            })
        
        return create_response(200, result)
    
    except Exception as e:
        logger.error(f"Lambda handler error: {e}", exc_info=True)
        return create_response(500, {
            'success': False,
            'error': f'Internal server error: {str(e)}'
        })


def handle_npk_calculation(body: Dict[str, Any],
                          user_id: str,
                          farm_id: str,
                          location: Dict[str, str]) -> Dict[str, Any]:
    """Handle NPK calculation request"""
    
    soil_analysis = body.get('soil_analysis')
    target_crop = body.get('target_crop')
    farm_size_acres = body.get('farm_size_acres')
    
    if not soil_analysis:
        return {'success': False, 'error': 'Missing soil_analysis'}
    if not target_crop:
        return {'success': False, 'error': 'Missing target_crop'}
    if not farm_size_acres:
        return {'success': False, 'error': 'Missing farm_size_acres'}
    
    # Build prompt
    prompt = build_npk_calculation_prompt(
        soil_analysis, target_crop, farm_size_acres, location
    )
    
    # Call Bedrock
    try:
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 3000,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.3
            })
        )
        
        response_body = json.loads(response['body'].read())
        calculation_text = response_body['content'][0]['text']
        
        # Parse NPK data
        npk_data = parse_npk_calculations(calculation_text)
        
        # Store calculation
        calc_id = f"npk_{uuid.uuid4().hex[:12]}"
        store_npk_calculation(
            calc_id, user_id, farm_id, target_crop,
            farm_size_acres, npk_data, location
        )
        
        return {
            'success': True,
            'calculation_id': calc_id,
            'target_crop': target_crop,
            'farm_size_acres': farm_size_acres,
            **npk_data,
            'full_calculation': calculation_text
        }
    
    except Exception as e:
        logger.error(f"NPK calculation error: {e}")
        return {'success': False, 'error': str(e)}


def handle_recommendations(body: Dict[str, Any],
                          user_id: str,
                          farm_id: str,
                          location: Dict[str, str]) -> Dict[str, Any]:
    """Handle fertilizer recommendations request"""
    
    npk_requirements = body.get('npk_requirements')
    soil_analysis = body.get('soil_analysis')
    target_crop = body.get('target_crop')
    growth_stage = body.get('growth_stage', 'vegetative')
    weather_forecast = body.get('weather_forecast')
    budget_constraint = body.get('budget_constraint')
    
    if not npk_requirements:
        return {'success': False, 'error': 'Missing npk_requirements'}
    if not soil_analysis:
        return {'success': False, 'error': 'Missing soil_analysis'}
    if not target_crop:
        return {'success': False, 'error': 'Missing target_crop'}
    
    # Build prompt
    prompt = build_precision_recommendation_prompt(
        npk_requirements, soil_analysis, target_crop,
        growth_stage, weather_forecast, budget_constraint
    )
    
    # Call Bedrock
    try:
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 3500,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.3
            })
        )
        
        response_body = json.loads(response['body'].read())
        recommendations_text = response_body['content'][0]['text']
        
        # Parse recommendations
        recommendations = parse_precision_recommendations(recommendations_text)
        
        # Store recommendations
        rec_id = f"rec_{uuid.uuid4().hex[:12]}"
        store_recommendations(
            rec_id, user_id, farm_id, target_crop,
            growth_stage, recommendations, location
        )
        
        return {
            'success': True,
            'recommendation_id': rec_id,
            'target_crop': target_crop,
            'growth_stage': growth_stage,
            **recommendations,
            'full_recommendations': recommendations_text
        }
    
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        return {'success': False, 'error': str(e)}


def handle_timing(body: Dict[str, Any],
                 user_id: str,
                 farm_id: str,
                 location: Dict[str, str]) -> Dict[str, Any]:
    """Handle application timing request"""
    
    target_crop = body.get('target_crop')
    growth_stage = body.get('growth_stage', 'vegetative')
    weather_forecast = body.get('weather_forecast')
    
    if not target_crop:
        return {'success': False, 'error': 'Missing target_crop'}
    if not weather_forecast:
        return {'success': False, 'error': 'Missing weather_forecast'}
    
    # Build prompt
    prompt = build_timing_prompt(target_crop, growth_stage, weather_forecast, location)
    
    # Call Bedrock
    try:
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 2000,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.3
            })
        )
        
        response_body = json.loads(response['body'].read())
        timing_text = response_body['content'][0]['text']
        
        # Parse timing
        timing_data = parse_timing_recommendations(timing_text)
        
        return {
            'success': True,
            'target_crop': target_crop,
            'growth_stage': growth_stage,
            **timing_data,
            'full_timing_analysis': timing_text
        }
    
    except Exception as e:
        logger.error(f"Timing error: {e}")
        return {'success': False, 'error': str(e)}


def handle_growth_tracking(body: Dict[str, Any],
                          user_id: str,
                          farm_id: str,
                          location: Dict[str, str]) -> Dict[str, Any]:
    """Handle growth stage tracking request"""
    
    crop_name = body.get('crop_name')
    planting_date = body.get('planting_date')
    current_observations = body.get('current_observations')
    
    if not crop_name:
        return {'success': False, 'error': 'Missing crop_name'}
    if not planting_date:
        return {'success': False, 'error': 'Missing planting_date'}
    
    # Calculate days since planting
    try:
        planting_dt = datetime.fromisoformat(planting_date)
        days_since_planting = (datetime.now() - planting_dt).days
    except:
        return {'success': False, 'error': 'Invalid planting_date format (use ISO format)'}
    
    # Build prompt
    prompt = build_growth_stage_prompt(crop_name, days_since_planting, current_observations)
    
    # Call Bedrock
    try:
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1500,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.3
            })
        )
        
        response_body = json.loads(response['body'].read())
        stage_text = response_body['content'][0]['text']
        
        # Parse growth stage
        stage_data = parse_growth_stage(stage_text)
        
        # Store tracking
        tracking_id = f"growth_{uuid.uuid4().hex[:12]}"
        store_growth_tracking(
            tracking_id, user_id, farm_id, crop_name,
            planting_date, days_since_planting, stage_data
        )
        
        return {
            'success': True,
            'tracking_id': tracking_id,
            'crop_name': crop_name,
            'days_since_planting': days_since_planting,
            **stage_data
        }
    
    except Exception as e:
        logger.error(f"Growth tracking error: {e}")
        return {'success': False, 'error': str(e)}


def build_npk_calculation_prompt(soil_analysis: Dict[str, Any],
                                 target_crop: str,
                                 farm_size_acres: float,
                                 location: Dict[str, str]) -> str:
    """Build prompt for NPK calculation"""
    
    return f"""You are an expert agricultural scientist specializing in soil fertility and crop nutrition.
Calculate precise NPK (Nitrogen, Phosphorus, Potassium) requirements for:

TARGET CROP: {target_crop}
FARM SIZE: {farm_size_acres} acres
LOCATION: {location.get('district', 'Unknown')}, {location.get('state', 'Unknown')}

CURRENT SOIL ANALYSIS:
- Soil Type: {soil_analysis.get('soil_type', 'unknown')}
- Fertility Level: {soil_analysis.get('fertility_level', 'unknown')}
- pH Level: {soil_analysis.get('ph_level', 'not tested')}
- Current NPK Levels:
  * Nitrogen (N): {soil_analysis.get('npk_levels', {}).get('nitrogen', 'unknown')}
  * Phosphorus (P): {soil_analysis.get('npk_levels', {}).get('phosphorus', 'unknown')}
  * Potassium (K): {soil_analysis.get('npk_levels', {}).get('potassium', 'unknown')}
- Organic Matter: {soil_analysis.get('organic_matter', 'not tested')}%

Provide calculations in this format:

1. CROP NPK REQUIREMENTS:
   - Total Nitrogen (N) needed: [kg per acre]
   - Total Phosphorus (P2O5) needed: [kg per acre]
   - Total Potassium (K2O) needed: [kg per acre]

2. NET REQUIREMENTS:
   - Additional N needed: [kg per acre]
   - Additional P needed: [kg per acre]
   - Additional K needed: [kg per acre]

3. TOTAL FARM REQUIREMENTS ({farm_size_acres} acres):
   - Total N: [kg]
   - Total P2O5: [kg]
   - Total K2O: [kg]

4. SPLIT APPLICATION SCHEDULE:
   - Basal dose: [NPK quantities]
   - First top-dressing: [NPK quantities]
   - Second top-dressing: [NPK quantities]

Provide specific quantities based on scientific crop nutrition principles.
"""


def build_precision_recommendation_prompt(npk_requirements: Dict[str, Any],
                                         soil_analysis: Dict[str, Any],
                                         target_crop: str,
                                         growth_stage: str,
                                         weather_forecast: Optional[Dict[str, Any]],
                                         budget_constraint: Optional[float]) -> str:
    """Build prompt for precision recommendations"""
    
    prompt = f"""Provide detailed fertilizer recommendations for:

CROP: {target_crop}
GROWTH STAGE: {growth_stage}
SOIL TYPE: {soil_analysis.get('soil_type', 'unknown')}

NPK REQUIREMENTS:
{json.dumps(npk_requirements, indent=2)}
"""
    
    if weather_forecast:
        prompt += f"\nWEATHER FORECAST:\n{json.dumps(weather_forecast, indent=2)}\n"
    
    if budget_constraint:
        prompt += f"\nBUDGET: ₹{budget_constraint}\n"
    
    prompt += """
Provide recommendations in this format:

1. ORGANIC FERTILIZER OPTIONS:
   - Name, NPK content, Quantity per acre, Cost, Application method

2. CHEMICAL FERTILIZER OPTIONS:
   - Name, NPK ratio, Quantity per acre, Cost, Timing, Safety precautions

3. COMBINED APPROACH:
   - Integrated plan with quantities and costs

4. APPLICATION TIMING:
   - Optimal dates and weather considerations

Prioritize cost-effective, sustainable solutions.
"""
    
    return prompt


def build_timing_prompt(target_crop: str,
                       growth_stage: str,
                       weather_forecast: Dict[str, Any],
                       location: Dict[str, str]) -> str:
    """Build prompt for timing recommendations"""
    
    return f"""Determine optimal fertilizer application timing for:

CROP: {target_crop}
GROWTH STAGE: {growth_stage}
LOCATION: {location.get('district', 'Unknown')}, {location.get('state', 'Unknown')}

WEATHER FORECAST:
{json.dumps(weather_forecast, indent=2)}

Provide timing recommendations:

1. OPTIMAL APPLICATION WINDOW:
   - Best dates and rationale
   - Weather conditions needed

2. WEATHER CONSIDERATIONS:
   - Rainfall, temperature, wind, soil moisture

3. TIME OF DAY:
   - Best time and reason

4. RISK ASSESSMENT:
   - Weather risks and mitigation

Be specific with dates and provide clear reasoning.
"""


def build_growth_stage_prompt(crop_name: str,
                              days_since_planting: int,
                              current_observations: Optional[Dict[str, Any]]) -> str:
    """Build prompt for growth stage determination"""
    
    prompt = f"""Determine the current growth stage for:

CROP: {crop_name}
DAYS SINCE PLANTING: {days_since_planting}
"""
    
    if current_observations:
        prompt += f"\nCURRENT OBSERVATIONS:\n{json.dumps(current_observations, indent=2)}\n"
    
    prompt += """
Provide growth stage analysis:

1. CURRENT GROWTH STAGE:
   - Stage name: [seedling/vegetative/flowering/fruiting/maturity]
   - Confidence: [high/medium/low]

2. NUTRITIONAL NEEDS:
   - Primary nutrient priority
   - Application recommendations

3. NEXT STAGE PREDICTION:
   - Expected transition date
   - Signs to watch for

Be specific and provide actionable guidance.
"""
    
    return prompt


def parse_npk_calculations(calculation_text: str) -> Dict[str, Any]:
    """Parse NPK calculations from AI response"""
    
    npk_data = {
        'nitrogen_per_acre': 0,
        'phosphorus_per_acre': 0,
        'potassium_per_acre': 0,
        'total_nitrogen': 0,
        'total_phosphorus': 0,
        'total_potassium': 0
    }
    
    lines = calculation_text.split('\n')
    
    for line in lines:
        line_lower = line.lower().strip()
        
        if 'additional n needed' in line_lower or 'nitrogen needed' in line_lower:
            try:
                import re
                match = re.search(r'(\d+\.?\d*)\s*kg', line)
                if match:
                    npk_data['nitrogen_per_acre'] = float(match.group(1))
            except:
                pass
        
        if 'additional p needed' in line_lower or 'phosphorus needed' in line_lower:
            try:
                import re
                match = re.search(r'(\d+\.?\d*)\s*kg', line)
                if match:
                    npk_data['phosphorus_per_acre'] = float(match.group(1))
            except:
                pass
        
        if 'additional k needed' in line_lower or 'potassium needed' in line_lower:
            try:
                import re
                match = re.search(r'(\d+\.?\d*)\s*kg', line)
                if match:
                    npk_data['potassium_per_acre'] = float(match.group(1))
            except:
                pass
        
        if 'total n:' in line_lower:
            try:
                import re
                match = re.search(r'(\d+\.?\d*)\s*kg', line)
                if match:
                    npk_data['total_nitrogen'] = float(match.group(1))
            except:
                pass
        
        if 'total p' in line_lower and ':' in line:
            try:
                import re
                match = re.search(r'(\d+\.?\d*)\s*kg', line)
                if match:
                    npk_data['total_phosphorus'] = float(match.group(1))
            except:
                pass
        
        if 'total k' in line_lower and ':' in line:
            try:
                import re
                match = re.search(r'(\d+\.?\d*)\s*kg', line)
                if match:
                    npk_data['total_potassium'] = float(match.group(1))
            except:
                pass
    
    return npk_data


def parse_precision_recommendations(recommendations_text: str) -> Dict[str, Any]:
    """Parse precision recommendations from AI response"""
    
    return {
        'organic_options': extract_section(recommendations_text, 'ORGANIC FERTILIZER OPTIONS'),
        'chemical_options': extract_section(recommendations_text, 'CHEMICAL FERTILIZER OPTIONS'),
        'combined_approach': extract_section(recommendations_text, 'COMBINED APPROACH'),
        'application_timing': extract_section(recommendations_text, 'APPLICATION TIMING')
    }


def parse_timing_recommendations(timing_text: str) -> Dict[str, Any]:
    """Parse timing recommendations from AI response"""
    
    return {
        'optimal_window': extract_section(timing_text, 'OPTIMAL APPLICATION WINDOW'),
        'weather_considerations': extract_section(timing_text, 'WEATHER CONSIDERATIONS'),
        'time_of_day': extract_section(timing_text, 'TIME OF DAY'),
        'risk_assessment': extract_section(timing_text, 'RISK ASSESSMENT')
    }


def parse_growth_stage(stage_text: str) -> Dict[str, Any]:
    """Parse growth stage from AI response"""
    
    stage_data = {
        'current_stage': 'unknown',
        'confidence': 'medium',
        'nutritional_needs': '',
        'next_stage_prediction': ''
    }
    
    lines = stage_text.split('\n')
    
    for line in lines:
        line_lower = line.lower().strip()
        
        if 'stage name:' in line_lower:
            stage_str = line.split(':', 1)[1].strip().lower()
            for stage in ['seedling', 'vegetative', 'flowering', 'fruiting', 'maturity']:
                if stage in stage_str:
                    stage_data['current_stage'] = stage
                    break
        
        if 'confidence:' in line_lower:
            conf_str = line.split(':', 1)[1].strip().lower()
            if 'high' in conf_str:
                stage_data['confidence'] = 'high'
            elif 'low' in conf_str:
                stage_data['confidence'] = 'low'
    
    return stage_data


def extract_section(text: str, section_name: str) -> str:
    """Extract a section from text"""
    
    if section_name in text:
        start = text.find(section_name)
        # Find next numbered section or end
        next_section = len(text)
        for i in range(start + len(section_name), len(text)):
            if text[i:i+2].strip() and text[i:i+2][0].isdigit() and text[i:i+2][1] == '.':
                next_section = i
                break
        return text[start:next_section].strip()
    return ''


def store_npk_calculation(calc_id: str,
                         user_id: str,
                         farm_id: str,
                         target_crop: str,
                         farm_size_acres: float,
                         npk_data: Dict[str, Any],
                         location: Dict[str, str]) -> None:
    """Store NPK calculation in DynamoDB"""
    
    try:
        item = {
            'farm_id': farm_id,
            'timestamp': int(datetime.now().timestamp()),
            'calculation_id': calc_id,
            'user_id': user_id,
            'data_type': 'npk_calculation',
            'target_crop': target_crop,
            'farm_size_acres': farm_size_acres,
            'npk_data': npk_data,
            'location': location
        }
        
        farm_data_table.put_item(Item=item)
        logger.info(f"NPK calculation stored: {calc_id}")
    
    except Exception as e:
        logger.error(f"Error storing NPK calculation: {e}")


def store_recommendations(rec_id: str,
                         user_id: str,
                         farm_id: str,
                         target_crop: str,
                         growth_stage: str,
                         recommendations: Dict[str, Any],
                         location: Dict[str, str]) -> None:
    """Store recommendations in DynamoDB"""
    
    try:
        item = {
            'farm_id': farm_id,
            'timestamp': int(datetime.now().timestamp()),
            'recommendation_id': rec_id,
            'user_id': user_id,
            'data_type': 'fertilizer_recommendation',
            'target_crop': target_crop,
            'growth_stage': growth_stage,
            'recommendations': recommendations,
            'location': location
        }
        
        farm_data_table.put_item(Item=item)
        logger.info(f"Recommendations stored: {rec_id}")
    
    except Exception as e:
        logger.error(f"Error storing recommendations: {e}")


def store_growth_tracking(tracking_id: str,
                         user_id: str,
                         farm_id: str,
                         crop_name: str,
                         planting_date: str,
                         days_since_planting: int,
                         stage_data: Dict[str, Any]) -> None:
    """Store growth tracking in DynamoDB"""
    
    try:
        item = {
            'farm_id': farm_id,
            'timestamp': int(datetime.now().timestamp()),
            'tracking_id': tracking_id,
            'user_id': user_id,
            'data_type': 'growth_tracking',
            'crop_name': crop_name,
            'planting_date': planting_date,
            'days_since_planting': days_since_planting,
            'growth_stage_data': stage_data
        }
        
        farm_data_table.put_item(Item=item)
        logger.info(f"Growth tracking stored: {tracking_id}")
    
    except Exception as e:
        logger.error(f"Error storing growth tracking: {e}")


def create_response(status_code: int, body: dict) -> dict:
    """Create Lambda response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        },
        'body': json.dumps(body)
    }


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'body': json.dumps({
            'action': 'calculate_npk',
            'soil_analysis': {
                'soil_type': 'loam',
                'fertility_level': 'medium',
                'ph_level': 6.5,
                'npk_levels': {
                    'nitrogen': 'low',
                    'phosphorus': 'medium',
                    'potassium': 'high'
                },
                'organic_matter': 2.5
            },
            'target_crop': 'wheat',
            'farm_size_acres': 2.5,
            'user_id': 'test_farmer_001',
            'farm_id': 'farm_test_001',
            'location': {'state': 'Punjab', 'district': 'Ludhiana'}
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
