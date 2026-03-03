"""
RISE Loan and Credit Planning - Example Usage
Demonstrates comprehensive loan and credit planning features
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.loan_credit_tools import LoanCreditTools
import json


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def example_1_assess_financing_needs():
    """Example 1: Assess financing needs for equipment purchase"""
    print_section("Example 1: Assess Financing Needs")
    
    tools = LoanCreditTools()
    
    farmer_profile = {
        'name': 'Ravi Kumar',
        'age': 35,
        'annual_farm_income': 250000,
        'other_income': 50000,
        'annual_expenses': 180000,
        'credit_score': 680,
        'land_ownership': True,
        'farming_experience': '10 years'
    }
    
    farm_details = {
        'farm_size_acres': 5.0,
        'soil_type': 'loamy',
        'crops': ['wheat', 'rice']
    }
    
    result = tools.assess_financing_needs(
        farmer_profile=farmer_profile,
        farm_details=farm_details,
        purpose='equipment_purchase'
    )
    
    if result['success']:
        print(f"Assessment ID: {result['assessment_id']}")
        print(f"Required Amount: ₹{result['required_amount']:,.2f}")
        print(f"\nRepayment Capacity:")
        print(f"  Annual Income: ₹{result['repayment_capacity']['annual_income']:,.2f}")
        print(f"  Annual Surplus: ₹{result['repayment_capacity']['annual_surplus']:,.2f}")
        print(f"  Monthly Surplus: ₹{result['repayment_capacity']['monthly_surplus']:,.2f}")
        print(f"  Capacity Level: {result['repayment_capacity']['capacity_level'].upper()}")
        print(f"  Max Monthly EMI: ₹{result['repayment_capacity']['max_monthly_emi']:,.2f}")
        
        print(f"\nEligibility: {'ELIGIBLE' if result['eligibility']['eligible'] else 'NOT ELIGIBLE'}")
        print("\nEligibility Factors:")
        for factor in result['eligibility']['eligibility_factors']:
            status_icon = '✅' if factor['status'] == 'eligible' else '⚠️' if factor['status'] == 'warning' else '❌'
            print(f"  {status_icon} {factor['factor']}: {factor['detail']}")
        
        print(f"\nRecommendation: {result['recommendation']['recommendation_type'].upper()}")
        print(f"Message: {result['recommendation']['message']}")
        
        if result['recommendation']['recommendation_type'] == 'recommended':
            print(f"\nLoan Details:")
            print(f"  Type: {result['recommendation']['loan_type']}")
            print(f"  Tenure: {result['recommendation']['recommended_tenure_months']} months")
            print(f"  Estimated EMI: ₹{result['recommendation']['estimated_emi']:,.2f}")
    else:
        print(f"Error: {result['error']}")


def example_2_recommend_loan_products():
    """Example 2: Get loan product recommendations"""
    print_section("Example 2: Recommend Loan Products")
    
    tools = LoanCreditTools()
    
    result = tools.recommend_loan_products(
        required_amount=200000,
        purpose='equipment_purchase',
        farmer_profile={'credit_score': 680},
        location={'state': 'Punjab'},
        repayment_period_months=60
    )
    
    if result['success']:
        print(f"Total Products Found: {result['total_products_found']}")
        print(f"\nTop {len(result['recommendations'])} Recommendations:\n")
        
        for idx, product in enumerate(result['recommendations'], 1):
            print(f"{idx}. {product['lender_name']} - {product['product_name']}")
            print(f"   Suitability Score: {product['suitability_score']:.0f}/100")
            print(f"   Interest Rate: {product['interest_rate']}% p.a.")
            print(f"   Monthly EMI: ₹{product['calculated_emi']:,.2f}")
            print(f"   Total Interest: ₹{product['total_interest']:,.2f}")
            print(f"   Total Repayment: ₹{product['total_repayment']:,.2f}")
            print(f"   Processing Fee: {product['processing_fee_percent']}%")
            print(f"   Lender Type: {product['lender_type'].upper()}")
            print(f"   Features: {', '.join(product['features'])}")
            print()
    else:
        print(f"Error: {result['error']}")


def example_3_generate_repayment_schedule():
    """Example 3: Generate crop-cycle aligned repayment schedule"""
    print_section("Example 3: Generate Repayment Schedule")
    
    tools = LoanCreditTools()
    
    # Define crop cycle with harvest months
    crop_cycle = {
        'harvest_months': [6, 12, 18, 24, 30, 36, 42, 48, 54, 60],  # Every 6 months
        'harvest_income': 100000  # ₹1 lakh per harvest
    }
    
    result = tools.generate_repayment_schedule(
        loan_amount=200000,
        interest_rate=9.5,
        tenure_months=60,
        crop_cycle=crop_cycle
    )
    
    if result['success']:
        print(f"Loan Amount: ₹{result['loan_amount']:,.2f}")
        print(f"Interest Rate: {result['interest_rate']}% p.a.")
        print(f"Tenure: {result['tenure_months']} months")
        print(f"Monthly EMI: ₹{result['monthly_emi']:,.2f}")
        print(f"Total Interest: ₹{result['total_interest']:,.2f}")
        print(f"Total Repayment: ₹{result['total_repayment']:,.2f}")
        print(f"Challenging Months: {result['challenging_months']}")
        
        print("\nFirst 12 Months Schedule:")
        print(f"{'Month':<6} {'EMI':<12} {'Principal':<12} {'Interest':<12} {'Balance':<12} {'Harvest':<8} {'Feasibility':<12}")
        print("-" * 80)
        
        for month_data in result['schedule'][:12]:
            harvest_icon = '🌾' if month_data['is_harvest_month'] else '  '
            print(f"{month_data['month']:<6} "
                  f"₹{month_data['emi']:<11,.0f} "
                  f"₹{month_data['principal']:<11,.0f} "
                  f"₹{month_data['interest']:<11,.0f} "
                  f"₹{month_data['balance']:<11,.0f} "
                  f"{harvest_icon:<8} "
                  f"{month_data['payment_feasibility']:<12}")
        
        print("\nRecommendations:")
        for rec in result['recommendations']:
            print(f"  • {rec}")
    else:
        print(f"Error: {result['error']}")


def example_4_compile_documents():
    """Example 4: Compile financial documents for loan application"""
    print_section("Example 4: Compile Financial Documents")
    
    tools = LoanCreditTools()
    
    farmer_profile = {
        'name': 'Ravi Kumar',
        'age': 35,
        'farming_experience': '10 years',
        'annual_farm_income': 250000,
        'assets_value': 500000,
        'existing_liabilities': 50000
    }
    
    farm_details = {
        'farm_size_acres': 5.0,
        'soil_type': 'loamy',
        'crops': ['wheat', 'rice']
    }
    
    result = tools.compile_financial_documents(
        farmer_profile=farmer_profile,
        farm_details=farm_details,
        loan_purpose='equipment_purchase',
        loan_amount=200000
    )
    
    if result['success']:
        print(f"Compilation ID: {result['compilation_id']}")
        print(f"Estimated Processing Time: {result['estimated_processing_time']}")
        
        print("\nRequired Documents:")
        for doc in result['required_documents']:
            mandatory = '🔴 MANDATORY' if doc['mandatory'] else '🟡 OPTIONAL'
            print(f"\n{mandatory} - {doc['document']}")
            print(f"  Format: {doc['format']}")
            print(f"  Examples: {', '.join(doc['examples'])}")
        
        print("\nFinancial Summary:")
        summary = result['financial_summary']
        print(f"  Applicant: {summary['applicant_details']['name']}, Age {summary['applicant_details']['age']}")
        print(f"  Farm Size: {summary['farm_details']['total_land']} acres")
        print(f"  Annual Income: ₹{summary['financial_position']['annual_income']:,}")
        print(f"  Net Worth: ₹{summary['financial_position']['net_worth']:,}")
        print(f"  Loan Amount: ₹{summary['loan_request']['amount']:,}")
        
        print("\nApplication Process:")
        for step in result['application_guidance']:
            print(f"  {step}")
    else:
        print(f"Error: {result['error']}")


def example_5_calculate_affordability():
    """Example 5: Calculate loan affordability"""
    print_section("Example 5: Calculate Loan Affordability")
    
    tools = LoanCreditTools()
    
    existing_loans = [
        {'emi': 3000, 'type': 'personal_loan'},
        {'emi': 2000, 'type': 'vehicle_loan'}
    ]
    
    result = tools.calculate_loan_affordability(
        monthly_income=25000,
        monthly_expenses=12000,
        existing_loans=existing_loans,
        interest_rate=9.5,
        tenure_months=60
    )
    
    if result['success']:
        print(f"Monthly Income: ₹{result['monthly_income']:,.2f}")
        print(f"Monthly Expenses: ₹{result['monthly_expenses']:,.2f}")
        print(f"Existing EMI Total: ₹{result['existing_emi_total']:,.2f}")
        print(f"Disposable Income: ₹{result['disposable_income']:,.2f}")
        print(f"\nMax Affordable EMI: ₹{result['max_affordable_emi']:,.2f}")
        print(f"Max Loan Amount: ₹{result['max_loan_amount']:,.2f}")
        print(f"\nDebt-to-Income Ratio: {result['debt_to_income_ratio']:.2f}%")
        print(f"Affordability Status: {result['affordability_status'].upper()}")
        print(f"\nRecommendation: {result['recommendation']}")
    else:
        print(f"Error: {result['error']}")


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("  RISE Loan and Credit Planning - Comprehensive Examples")
    print("=" * 80)
    
    try:
        example_1_assess_financing_needs()
        example_2_recommend_loan_products()
        example_3_generate_repayment_schedule()
        example_4_compile_documents()
        example_5_calculate_affordability()
        
        print("\n" + "=" * 80)
        print("  All examples completed successfully!")
        print("=" * 80 + "\n")
    
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
