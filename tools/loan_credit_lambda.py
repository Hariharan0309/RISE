"""
RISE Loan and Credit Planning Lambda Function
AWS Lambda handler for loan product recommendations and financing needs assessment
"""

import json
import logging
import os
from typing import Dict, Any
from loan_credit_tools import LoanCreditTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize loan and credit tools
loan_tools = LoanCreditTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for loan and credit planning requests
    
    Event structure:
    {
        "action": "assess_needs" | "recommend_products" | "generate_schedule" | "compile_documents" | "calculate_affordability",
        "farmer_profile": dict,
        "farm_details": dict,
        "purpose": str,
        "required_amount": float,
        "location": dict,
        "loan_amount": float,
        "interest_rate": float,
        "tenure_months": int,
        "crop_cycle": dict (optional),
        "income_pattern": list (optional)
    }
    
    Returns:
        API Gateway response with loan and credit analysis
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'assess_needs')
        
        logger.info(f"Loan credit request: action={action}")
        
        # Route to appropriate handler
        if action == 'assess_needs':
            result = handle_assess_needs(body)
        elif action == 'recommend_products':
            result = handle_recommend_products(body)
        elif action == 'generate_schedule':
            result = handle_generate_schedule(body)
        elif action == 'compile_documents':
            result = handle_compile_documents(body)
        elif action == 'calculate_affordability':
            result = handle_calculate_affordability(body)
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


def handle_assess_needs(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle financing needs assessment request"""
    try:
        farmer_profile = body.get('farmer_profile', {})
        farm_details = body.get('farm_details', {})
        purpose = body.get('purpose', '').strip()
        
        if not purpose:
            return {
                'success': False,
                'error': 'purpose is required'
            }
        
        crop_plan = body.get('crop_plan')
        
        result = loan_tools.assess_financing_needs(
            farmer_profile=farmer_profile,
            farm_details=farm_details,
            purpose=purpose,
            crop_plan=crop_plan
        )
        
        logger.info(f"Financing needs assessed: purpose={purpose}")
        return result
    
    except Exception as e:
        logger.error(f"Financing needs assessment error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_recommend_products(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle loan product recommendation request"""
    try:
        required_amount = float(body.get('required_amount', 0))
        purpose = body.get('purpose', '').strip()
        farmer_profile = body.get('farmer_profile', {})
        location = body.get('location', {})
        
        if required_amount <= 0:
            return {
                'success': False,
                'error': 'valid required_amount is required'
            }
        
        if not purpose:
            return {
                'success': False,
                'error': 'purpose is required'
            }
        
        repayment_period = body.get('repayment_period_months')
        
        result = loan_tools.recommend_loan_products(
            required_amount=required_amount,
            purpose=purpose,
            farmer_profile=farmer_profile,
            location=location,
            repayment_period_months=repayment_period
        )
        
        logger.info(f"Loan products recommended: amount={required_amount}, purpose={purpose}")
        return result
    
    except Exception as e:
        logger.error(f"Loan product recommendation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_generate_schedule(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle repayment schedule generation request"""
    try:
        loan_amount = float(body.get('loan_amount', 0))
        interest_rate = float(body.get('interest_rate', 0))
        tenure_months = int(body.get('tenure_months', 0))
        
        if loan_amount <= 0 or interest_rate < 0 or tenure_months <= 0:
            return {
                'success': False,
                'error': 'valid loan_amount, interest_rate, and tenure_months are required'
            }
        
        crop_cycle = body.get('crop_cycle')
        income_pattern = body.get('income_pattern')
        
        result = loan_tools.generate_repayment_schedule(
            loan_amount=loan_amount,
            interest_rate=interest_rate,
            tenure_months=tenure_months,
            crop_cycle=crop_cycle,
            income_pattern=income_pattern
        )
        
        logger.info(f"Repayment schedule generated: amount={loan_amount}, tenure={tenure_months}")
        return result
    
    except Exception as e:
        logger.error(f"Repayment schedule generation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_compile_documents(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle document compilation request"""
    try:
        farmer_profile = body.get('farmer_profile', {})
        farm_details = body.get('farm_details', {})
        loan_purpose = body.get('loan_purpose', '').strip()
        loan_amount = float(body.get('loan_amount', 0))
        
        if not loan_purpose or loan_amount <= 0:
            return {
                'success': False,
                'error': 'loan_purpose and valid loan_amount are required'
            }
        
        result = loan_tools.compile_financial_documents(
            farmer_profile=farmer_profile,
            farm_details=farm_details,
            loan_purpose=loan_purpose,
            loan_amount=loan_amount
        )
        
        logger.info(f"Documents compiled: purpose={loan_purpose}, amount={loan_amount}")
        return result
    
    except Exception as e:
        logger.error(f"Document compilation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_calculate_affordability(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle affordability calculation request"""
    try:
        monthly_income = float(body.get('monthly_income', 0))
        monthly_expenses = float(body.get('monthly_expenses', 0))
        existing_loans = body.get('existing_loans', [])
        interest_rate = float(body.get('interest_rate', 0))
        tenure_months = int(body.get('tenure_months', 0))
        
        if monthly_income <= 0 or interest_rate < 0 or tenure_months <= 0:
            return {
                'success': False,
                'error': 'valid monthly_income, interest_rate, and tenure_months are required'
            }
        
        result = loan_tools.calculate_loan_affordability(
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            existing_loans=existing_loans,
            interest_rate=interest_rate,
            tenure_months=tenure_months
        )
        
        logger.info(f"Affordability calculated: income={monthly_income}")
        return result
    
    except Exception as e:
        logger.error(f"Affordability calculation error: {e}")
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
    # Test event for financing needs assessment
    test_event = {
        'action': 'assess_needs',
        'farmer_profile': {
            'name': 'Ravi Kumar',
            'age': 35,
            'annual_farm_income': 250000,
            'other_income': 50000,
            'annual_expenses': 180000,
            'credit_score': 680,
            'land_ownership': True
        },
        'farm_details': {
            'farm_size_acres': 5.0,
            'soil_type': 'loamy',
            'crops': ['wheat', 'rice']
        },
        'purpose': 'equipment_purchase'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2))
