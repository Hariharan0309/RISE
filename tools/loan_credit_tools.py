"""
RISE Loan and Credit Planning Tools
Comprehensive tools for loan product recommendations, financing needs assessment, and repayment planning
"""

import boto3
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class LoanCreditTools:
    """Loan and credit planning tools with financing needs assessment and repayment scheduling"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize loan and credit planning tools
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        
        # DynamoDB tables
        self.loan_products_table = self.dynamodb.Table('RISE-LoanProducts')
        self.loan_applications_table = self.dynamodb.Table('RISE-LoanApplications')
        
        logger.info(f"Loan and credit tools initialized in region {region}")

    def assess_financing_needs(self,
                              farmer_profile: Dict[str, Any],
                              farm_details: Dict[str, Any],
                              purpose: str,
                              crop_plan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Assess farmer's financing needs based on profile and farming plans
        
        Args:
            farmer_profile: Farmer's profile with income, assets, liabilities
            farm_details: Farm size, soil type, location, current crops
            purpose: Purpose of loan (crop_cultivation, equipment, land_improvement, etc.)
            crop_plan: Optional crop cultivation plan with costs
        
        Returns:
            Dict with financing needs assessment
        """
        try:
            # Calculate required financing amount
            required_amount = self._calculate_required_amount(purpose, farm_details, crop_plan)
            
            # Assess repayment capacity
            repayment_capacity = self._assess_repayment_capacity(farmer_profile, farm_details)
            
            # Determine loan eligibility
            eligibility = self._determine_eligibility(farmer_profile, required_amount, repayment_capacity)
            
            # Generate financing recommendation
            recommendation = self._generate_financing_recommendation(
                required_amount, repayment_capacity, eligibility, purpose
            )
            
            assessment_id = f"assess_{uuid.uuid4().hex[:12]}"
            
            return {
                'success': True,
                'assessment_id': assessment_id,
                'required_amount': required_amount,
                'repayment_capacity': repayment_capacity,
                'eligibility': eligibility,
                'recommendation': recommendation,
                'purpose': purpose,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Financing needs assessment error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def recommend_loan_products(self,
                               required_amount: float,
                               purpose: str,
                               farmer_profile: Dict[str, Any],
                               location: Dict[str, Any],
                               repayment_period_months: Optional[int] = None) -> Dict[str, Any]:
        """
        Recommend appropriate loan products from banks and NBFCs
        
        Args:
            required_amount: Loan amount needed
            purpose: Purpose of loan
            farmer_profile: Farmer's profile
            location: Location information
            repayment_period_months: Desired repayment period
        
        Returns:
            Dict with recommended loan products
        """
        try:
            # Get available loan products
            loan_products = self._get_loan_products_database(purpose, location)
            
            # Filter products by amount eligibility
            eligible_products = [
                p for p in loan_products 
                if p['min_amount'] <= required_amount <= p['max_amount']
            ]
            
            # Score and rank products
            scored_products = []
            for product in eligible_products:
                score = self._score_loan_product(
                    product, required_amount, farmer_profile, repayment_period_months
                )
                product['suitability_score'] = score
                scored_products.append(product)
            
            # Sort by suitability score
            scored_products.sort(key=lambda x: x['suitability_score'], reverse=True)
            
            # Get top 5 recommendations
            recommendations = scored_products[:5]
            
            # Calculate EMI for each product
            for product in recommendations:
                tenure = repayment_period_months or product['default_tenure_months']
                product['calculated_emi'] = self._calculate_emi(
                    required_amount, product['interest_rate'], tenure
                )
                product['total_interest'] = (product['calculated_emi'] * tenure) - required_amount
                product['total_repayment'] = product['calculated_emi'] * tenure
            
            return {
                'success': True,
                'required_amount': required_amount,
                'purpose': purpose,
                'recommendations': recommendations,
                'total_products_found': len(eligible_products),
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Loan product recommendation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def generate_repayment_schedule(self,
                                   loan_amount: float,
                                   interest_rate: float,
                                   tenure_months: int,
                                   crop_cycle: Optional[Dict[str, Any]] = None,
                                   income_pattern: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate crop-cycle aligned repayment schedule
        
        Args:
            loan_amount: Principal loan amount
            interest_rate: Annual interest rate (percentage)
            tenure_months: Loan tenure in months
            crop_cycle: Crop cultivation cycle with harvest months
            income_pattern: Expected income pattern by month
        
        Returns:
            Dict with detailed repayment schedule
        """
        try:
            monthly_rate = interest_rate / 12 / 100
            emi = self._calculate_emi(loan_amount, interest_rate, tenure_months)
            
            schedule = []
            balance = loan_amount
            total_interest = 0
            
            for month in range(1, tenure_months + 1):
                interest_component = balance * monthly_rate
                principal_component = emi - interest_component
                balance -= principal_component
                total_interest += interest_component
                
                # Determine if this is a harvest month
                is_harvest_month = False
                expected_income = 0
                if crop_cycle and 'harvest_months' in crop_cycle:
                    is_harvest_month = month in crop_cycle['harvest_months']
                    if is_harvest_month and 'harvest_income' in crop_cycle:
                        expected_income = crop_cycle['harvest_income']
                
                # Check income pattern
                if income_pattern:
                    for pattern in income_pattern:
                        if pattern['month'] == month:
                            expected_income = pattern['income']
                            break
                
                schedule.append({
                    'month': month,
                    'emi': round(emi, 2),
                    'principal': round(principal_component, 2),
                    'interest': round(interest_component, 2),
                    'balance': round(max(0, balance), 2),
                    'is_harvest_month': is_harvest_month,
                    'expected_income': round(expected_income, 2),
                    'payment_feasibility': 'high' if expected_income >= emi else 'medium' if expected_income > 0 else 'low'
                })
            
            # Identify challenging months
            challenging_months = [s for s in schedule if s['payment_feasibility'] == 'low']
            
            # Generate recommendations for challenging periods
            recommendations = self._generate_repayment_recommendations(
                schedule, crop_cycle, challenging_months
            )
            
            return {
                'success': True,
                'loan_amount': loan_amount,
                'interest_rate': interest_rate,
                'tenure_months': tenure_months,
                'monthly_emi': round(emi, 2),
                'total_interest': round(total_interest, 2),
                'total_repayment': round(loan_amount + total_interest, 2),
                'schedule': schedule,
                'challenging_months': len(challenging_months),
                'recommendations': recommendations
            }
        
        except Exception as e:
            logger.error(f"Repayment schedule generation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def compile_financial_documents(self,
                                   farmer_profile: Dict[str, Any],
                                   farm_details: Dict[str, Any],
                                   loan_purpose: str,
                                   loan_amount: float) -> Dict[str, Any]:
        """
        Help compile required financial documents for loan application
        
        Args:
            farmer_profile: Farmer's profile information
            farm_details: Farm details
            loan_purpose: Purpose of loan
            loan_amount: Requested loan amount
        
        Returns:
            Dict with document checklist and guidance
        """
        try:
            # Generate document checklist based on loan type and amount
            documents = self._generate_document_checklist(loan_purpose, loan_amount)
            
            # Generate financial summary
            financial_summary = self._generate_financial_summary(
                farmer_profile, farm_details, loan_amount
            )
            
            # Generate application guidance
            guidance = self._generate_application_guidance(loan_purpose, loan_amount)
            
            # Create document compilation helper
            compilation_id = f"doc_{uuid.uuid4().hex[:12]}"
            
            return {
                'success': True,
                'compilation_id': compilation_id,
                'required_documents': documents,
                'financial_summary': financial_summary,
                'application_guidance': guidance,
                'estimated_processing_time': self._estimate_processing_time(loan_amount),
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Document compilation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def calculate_loan_affordability(self,
                                    monthly_income: float,
                                    monthly_expenses: float,
                                    existing_loans: List[Dict[str, Any]],
                                    interest_rate: float,
                                    tenure_months: int) -> Dict[str, Any]:
        """
        Calculate maximum affordable loan amount
        
        Args:
            monthly_income: Average monthly income
            monthly_expenses: Average monthly expenses
            existing_loans: List of existing loan EMIs
            interest_rate: Proposed interest rate
            tenure_months: Proposed tenure
        
        Returns:
            Dict with affordability analysis
        """
        try:
            # Calculate disposable income
            existing_emi_total = sum(loan.get('emi', 0) for loan in existing_loans)
            disposable_income = monthly_income - monthly_expenses - existing_emi_total
            
            # Apply 40% FOIR (Fixed Obligation to Income Ratio) rule
            max_affordable_emi = disposable_income * 0.4
            
            # Calculate maximum loan amount
            if max_affordable_emi > 0:
                monthly_rate = interest_rate / 12 / 100
                if monthly_rate > 0:
                    max_loan_amount = (max_affordable_emi * (1 - (1 + monthly_rate) ** -tenure_months)) / monthly_rate
                else:
                    max_loan_amount = max_affordable_emi * tenure_months
            else:
                max_loan_amount = 0
            
            # Calculate debt-to-income ratio
            dti_ratio = ((existing_emi_total + max_affordable_emi) / monthly_income * 100) if monthly_income > 0 else 0
            
            # Determine affordability status
            if dti_ratio <= 40:
                affordability_status = 'excellent'
            elif dti_ratio <= 50:
                affordability_status = 'good'
            elif dti_ratio <= 60:
                affordability_status = 'moderate'
            else:
                affordability_status = 'poor'
            
            return {
                'success': True,
                'monthly_income': monthly_income,
                'monthly_expenses': monthly_expenses,
                'existing_emi_total': round(existing_emi_total, 2),
                'disposable_income': round(disposable_income, 2),
                'max_affordable_emi': round(max_affordable_emi, 2),
                'max_loan_amount': round(max_loan_amount, 2),
                'debt_to_income_ratio': round(dti_ratio, 2),
                'affordability_status': affordability_status,
                'recommendation': self._get_affordability_recommendation(affordability_status)
            }
        
        except Exception as e:
            logger.error(f"Affordability calculation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    # Helper methods
    
    def _calculate_required_amount(self, purpose: str, farm_details: Dict[str, Any], 
                                   crop_plan: Optional[Dict[str, Any]]) -> float:
        """Calculate required financing amount based on purpose"""
        
        if crop_plan and 'total_cost' in crop_plan:
            return crop_plan['total_cost']
        
        # Default estimates by purpose
        farm_size = farm_details.get('farm_size_acres', 5)
        
        estimates = {
            'crop_cultivation': farm_size * 20000,  # ₹20,000 per acre
            'equipment_purchase': 150000,  # Tractor/equipment
            'land_improvement': farm_size * 30000,
            'irrigation_setup': farm_size * 25000,
            'livestock': 100000,
            'storage_facility': 200000,
            'working_capital': farm_size * 15000
        }
        
        return estimates.get(purpose, farm_size * 20000)
    
    def _assess_repayment_capacity(self, farmer_profile: Dict[str, Any], 
                                   farm_details: Dict[str, Any]) -> Dict[str, Any]:
        """Assess farmer's repayment capacity"""
        
        # Get income sources
        annual_farm_income = farmer_profile.get('annual_farm_income', 0)
        other_income = farmer_profile.get('other_income', 0)
        total_annual_income = annual_farm_income + other_income
        
        # Get expenses
        annual_expenses = farmer_profile.get('annual_expenses', total_annual_income * 0.6)
        
        # Calculate surplus
        annual_surplus = total_annual_income - annual_expenses
        monthly_surplus = annual_surplus / 12
        
        # Assess capacity
        if monthly_surplus > 10000:
            capacity_level = 'high'
        elif monthly_surplus > 5000:
            capacity_level = 'medium'
        elif monthly_surplus > 2000:
            capacity_level = 'low'
        else:
            capacity_level = 'very_low'
        
        return {
            'annual_income': total_annual_income,
            'annual_expenses': annual_expenses,
            'annual_surplus': annual_surplus,
            'monthly_surplus': round(monthly_surplus, 2),
            'capacity_level': capacity_level,
            'max_monthly_emi': round(monthly_surplus * 0.4, 2)  # 40% FOIR
        }
    
    def _determine_eligibility(self, farmer_profile: Dict[str, Any], 
                              required_amount: float, 
                              repayment_capacity: Dict[str, Any]) -> Dict[str, Any]:
        """Determine loan eligibility"""
        
        eligibility_factors = []
        eligible = True
        
        # Age check
        age = farmer_profile.get('age', 40)
        if 21 <= age <= 65:
            eligibility_factors.append({'factor': 'age', 'status': 'eligible', 'detail': f'Age {age} is within range'})
        else:
            eligibility_factors.append({'factor': 'age', 'status': 'not_eligible', 'detail': f'Age {age} outside 21-65 range'})
            eligible = False
        
        # Land ownership check
        has_land = farmer_profile.get('land_ownership', True)
        if has_land:
            eligibility_factors.append({'factor': 'land_ownership', 'status': 'eligible', 'detail': 'Owns agricultural land'})
        else:
            eligibility_factors.append({'factor': 'land_ownership', 'status': 'warning', 'detail': 'No land ownership - may need guarantor'})
        
        # Repayment capacity check
        capacity_level = repayment_capacity['capacity_level']
        if capacity_level in ['high', 'medium']:
            eligibility_factors.append({'factor': 'repayment_capacity', 'status': 'eligible', 'detail': f'{capacity_level.title()} repayment capacity'})
        elif capacity_level == 'low':
            eligibility_factors.append({'factor': 'repayment_capacity', 'status': 'warning', 'detail': 'Low repayment capacity - smaller loan recommended'})
        else:
            eligibility_factors.append({'factor': 'repayment_capacity', 'status': 'not_eligible', 'detail': 'Insufficient repayment capacity'})
            eligible = False
        
        # Credit history check (if available)
        credit_score = farmer_profile.get('credit_score', 650)
        if credit_score >= 700:
            eligibility_factors.append({'factor': 'credit_score', 'status': 'eligible', 'detail': f'Good credit score: {credit_score}'})
        elif credit_score >= 600:
            eligibility_factors.append({'factor': 'credit_score', 'status': 'warning', 'detail': f'Fair credit score: {credit_score}'})
        else:
            eligibility_factors.append({'factor': 'credit_score', 'status': 'not_eligible', 'detail': f'Poor credit score: {credit_score}'})
            eligible = False
        
        return {
            'eligible': eligible,
            'eligibility_factors': eligibility_factors,
            'recommended_amount': required_amount if eligible else repayment_capacity['max_monthly_emi'] * 12 * 3
        }
    
    def _generate_financing_recommendation(self, required_amount: float, 
                                          repayment_capacity: Dict[str, Any],
                                          eligibility: Dict[str, Any], 
                                          purpose: str) -> Dict[str, Any]:
        """Generate financing recommendation"""
        
        if not eligibility['eligible']:
            return {
                'recommendation_type': 'not_recommended',
                'message': 'Loan not recommended due to eligibility issues',
                'alternatives': [
                    'Improve credit score before applying',
                    'Consider smaller loan amount',
                    'Explore government subsidy schemes',
                    'Look for cooperative society loans'
                ]
            }
        
        max_emi = repayment_capacity['max_monthly_emi']
        
        # Recommend loan structure
        if purpose in ['crop_cultivation', 'working_capital']:
            recommended_tenure = 12  # Short-term for crop loans
            loan_type = 'crop_loan'
        elif purpose in ['equipment_purchase', 'irrigation_setup']:
            recommended_tenure = 60  # Medium-term for equipment
            loan_type = 'term_loan'
        else:
            recommended_tenure = 84  # Long-term for infrastructure
            loan_type = 'term_loan'
        
        return {
            'recommendation_type': 'recommended',
            'loan_type': loan_type,
            'recommended_amount': required_amount,
            'recommended_tenure_months': recommended_tenure,
            'estimated_emi': round(required_amount / recommended_tenure * 1.08, 2),  # Rough estimate with interest
            'max_affordable_emi': max_emi,
            'message': f'Eligible for {loan_type} with {recommended_tenure} months tenure',
            'next_steps': [
                'Compare loan products from multiple lenders',
                'Prepare required documents',
                'Check for government interest subsidy schemes',
                'Consider crop insurance for risk mitigation'
            ]
        }
    
    def _calculate_emi(self, principal: float, annual_rate: float, tenure_months: int) -> float:
        """Calculate EMI using reducing balance method"""
        
        if annual_rate == 0:
            return principal / tenure_months
        
        monthly_rate = annual_rate / 12 / 100
        emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure_months) / (((1 + monthly_rate) ** tenure_months) - 1)
        
        return emi
    
    def _get_loan_products_database(self, purpose: str, location: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get loan products database (banks and NBFCs)"""
        
        products = [
            # Nationalized Banks
            {
                'lender_name': 'State Bank of India',
                'lender_type': 'bank',
                'product_name': 'SBI Kisan Credit Card',
                'purpose': 'crop_cultivation',
                'min_amount': 10000,
                'max_amount': 300000,
                'interest_rate': 7.0,
                'default_tenure_months': 12,
                'processing_fee_percent': 0.5,
                'features': ['Interest subvention available', 'Flexible repayment', 'Crop insurance linked'],
                'eligibility': 'Farmers with land ownership'
            },
            {
                'lender_name': 'State Bank of India',
                'lender_type': 'bank',
                'product_name': 'SBI Agricultural Term Loan',
                'purpose': 'equipment_purchase',
                'min_amount': 50000,
                'max_amount': 2000000,
                'interest_rate': 9.5,
                'default_tenure_months': 60,
                'processing_fee_percent': 1.0,
                'features': ['Up to 85% financing', 'Moratorium period available', 'Collateral required'],
                'eligibility': 'Farmers with land ownership and good credit'
            },
            {
                'lender_name': 'Punjab National Bank',
                'lender_type': 'bank',
                'product_name': 'PNB Kisan Credit Card',
                'purpose': 'crop_cultivation',
                'min_amount': 10000,
                'max_amount': 300000,
                'interest_rate': 7.0,
                'default_tenure_months': 12,
                'processing_fee_percent': 0.5,
                'features': ['Interest subvention', 'ATM facility', 'Insurance coverage'],
                'eligibility': 'All farmers'
            },
            {
                'lender_name': 'HDFC Bank',
                'lender_type': 'bank',
                'product_name': 'HDFC Tractor Loan',
                'purpose': 'equipment_purchase',
                'min_amount': 100000,
                'max_amount': 2500000,
                'interest_rate': 10.5,
                'default_tenure_months': 84,
                'processing_fee_percent': 1.5,
                'features': ['Up to 90% financing', 'Quick approval', 'Flexible tenure'],
                'eligibility': 'Farmers with stable income'
            },
            # NBFCs
            {
                'lender_name': 'Mahindra Finance',
                'lender_type': 'nbfc',
                'product_name': 'Mahindra Tractor Loan',
                'purpose': 'equipment_purchase',
                'min_amount': 100000,
                'max_amount': 3000000,
                'interest_rate': 11.5,
                'default_tenure_months': 72,
                'processing_fee_percent': 2.0,
                'features': ['Minimal documentation', 'Fast approval', 'Doorstep service'],
                'eligibility': 'Farmers and agricultural entrepreneurs'
            },
            {
                'lender_name': 'Tata Capital',
                'lender_type': 'nbfc',
                'product_name': 'Tata Capital Farm Equipment Loan',
                'purpose': 'equipment_purchase',
                'min_amount': 50000,
                'max_amount': 2000000,
                'interest_rate': 12.0,
                'default_tenure_months': 60,
                'processing_fee_percent': 2.0,
                'features': ['Quick disbursal', 'Flexible repayment', 'Minimal paperwork'],
                'eligibility': 'Farmers with land or income proof'
            },
            {
                'lender_name': 'NABARD',
                'lender_type': 'development_bank',
                'product_name': 'NABARD Refinance Scheme',
                'purpose': 'land_improvement',
                'min_amount': 50000,
                'max_amount': 1000000,
                'interest_rate': 6.5,
                'default_tenure_months': 84,
                'processing_fee_percent': 0.5,
                'features': ['Subsidized interest', 'Long tenure', 'Government backed'],
                'eligibility': 'Small and marginal farmers'
            },
            {
                'lender_name': 'Canara Bank',
                'lender_type': 'bank',
                'product_name': 'Canara Kisan Credit Card',
                'purpose': 'working_capital',
                'min_amount': 10000,
                'max_amount': 300000,
                'interest_rate': 7.0,
                'default_tenure_months': 12,
                'processing_fee_percent': 0.5,
                'features': ['Interest subvention', 'Revolving credit', 'Insurance'],
                'eligibility': 'All categories of farmers'
            },
            {
                'lender_name': 'Bank of Baroda',
                'lender_type': 'bank',
                'product_name': 'Baroda Kisan Tatkal Scheme',
                'purpose': 'crop_cultivation',
                'min_amount': 10000,
                'max_amount': 500000,
                'interest_rate': 7.5,
                'default_tenure_months': 12,
                'processing_fee_percent': 0.5,
                'features': ['Quick processing', 'Flexible repayment', 'Crop insurance'],
                'eligibility': 'Farmers with Kisan Credit Card'
            }
        ]
        
        # Filter by purpose
        filtered = [p for p in products if p['purpose'] == purpose or purpose == 'general']
        
        return filtered if filtered else products
    
    def _score_loan_product(self, product: Dict[str, Any], required_amount: float,
                           farmer_profile: Dict[str, Any], 
                           repayment_period: Optional[int]) -> float:
        """Score loan product based on suitability"""
        
        score = 0.0
        
        # Interest rate score (lower is better) - 40% weight
        if product['interest_rate'] <= 7.0:
            score += 40
        elif product['interest_rate'] <= 9.0:
            score += 30
        elif product['interest_rate'] <= 11.0:
            score += 20
        else:
            score += 10
        
        # Processing fee score (lower is better) - 20% weight
        if product['processing_fee_percent'] <= 0.5:
            score += 20
        elif product['processing_fee_percent'] <= 1.0:
            score += 15
        elif product['processing_fee_percent'] <= 1.5:
            score += 10
        else:
            score += 5
        
        # Lender type preference - 20% weight
        if product['lender_type'] == 'bank':
            score += 20
        elif product['lender_type'] == 'development_bank':
            score += 18
        else:
            score += 15
        
        # Features score - 20% weight
        feature_count = len(product.get('features', []))
        score += min(20, feature_count * 5)
        
        return score
    
    def _generate_repayment_recommendations(self, schedule: List[Dict[str, Any]],
                                          crop_cycle: Optional[Dict[str, Any]],
                                          challenging_months: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for repayment management"""
        
        recommendations = []
        
        if challenging_months:
            recommendations.append(f'Plan for {len(challenging_months)} months with low income - consider building emergency fund')
        
        if crop_cycle:
            recommendations.append('Align major payments with harvest months for easier repayment')
            recommendations.append('Consider requesting moratorium period during crop growth phase')
        
        recommendations.extend([
            'Maintain 3-month EMI buffer in savings account',
            'Consider crop insurance to protect against yield loss',
            'Explore interest subvention schemes for agricultural loans',
            'Set up auto-debit to avoid missing payments',
            'Track expenses and income monthly to ensure repayment capacity'
        ])
        
        return recommendations
    
    def _generate_document_checklist(self, loan_purpose: str, loan_amount: float) -> List[Dict[str, Any]]:
        """Generate required documents checklist"""
        
        base_documents = [
            {
                'document': 'Identity Proof',
                'examples': ['Aadhaar Card', 'PAN Card', 'Voter ID', 'Passport'],
                'mandatory': True,
                'format': 'Original + Photocopy'
            },
            {
                'document': 'Address Proof',
                'examples': ['Aadhaar Card', 'Electricity Bill', 'Ration Card'],
                'mandatory': True,
                'format': 'Original + Photocopy'
            },
            {
                'document': 'Land Ownership Documents',
                'examples': ['7/12 Extract', 'Land Revenue Records', 'Property Tax Receipt'],
                'mandatory': True,
                'format': 'Certified Copy'
            },
            {
                'document': 'Bank Statements',
                'examples': ['Last 6 months bank statements'],
                'mandatory': True,
                'format': 'Original stamped by bank'
            },
            {
                'document': 'Income Proof',
                'examples': ['ITR', 'Form 16', 'Income Certificate'],
                'mandatory': False,
                'format': 'Certified Copy'
            },
            {
                'document': 'Passport Size Photographs',
                'examples': ['Recent photographs'],
                'mandatory': True,
                'format': '4 copies'
            }
        ]
        
        # Add purpose-specific documents
        if loan_purpose == 'equipment_purchase':
            base_documents.append({
                'document': 'Equipment Quotation',
                'examples': ['Proforma invoice from dealer'],
                'mandatory': True,
                'format': 'Original'
            })
        
        if loan_amount > 500000:
            base_documents.append({
                'document': 'Collateral Documents',
                'examples': ['Property papers', 'Asset valuation report'],
                'mandatory': True,
                'format': 'Certified Copy'
            })
        
        return base_documents
    
    def _generate_financial_summary(self, farmer_profile: Dict[str, Any],
                                   farm_details: Dict[str, Any],
                                   loan_amount: float) -> Dict[str, Any]:
        """Generate financial summary for application"""
        
        return {
            'applicant_details': {
                'name': farmer_profile.get('name', 'Farmer'),
                'age': farmer_profile.get('age', 40),
                'farming_experience': farmer_profile.get('farming_experience', '10 years')
            },
            'farm_details': {
                'total_land': farm_details.get('farm_size_acres', 5),
                'soil_type': farm_details.get('soil_type', 'loamy'),
                'current_crops': farm_details.get('crops', ['wheat', 'rice'])
            },
            'financial_position': {
                'annual_income': farmer_profile.get('annual_farm_income', 200000),
                'assets_value': farmer_profile.get('assets_value', 500000),
                'existing_liabilities': farmer_profile.get('existing_liabilities', 0),
                'net_worth': farmer_profile.get('assets_value', 500000) - farmer_profile.get('existing_liabilities', 0)
            },
            'loan_request': {
                'amount': loan_amount,
                'purpose': 'Agricultural development',
                'repayment_source': 'Farm income'
            }
        }
    
    def _generate_application_guidance(self, loan_purpose: str, loan_amount: float) -> List[str]:
        """Generate step-by-step application guidance"""
        
        guidance = [
            '1. Gather all required documents and make certified copies',
            '2. Visit the bank/NBFC branch or apply online through their portal',
            '3. Fill the loan application form completely and accurately',
            '4. Submit documents along with application form',
            '5. Bank will conduct field verification of land and assets',
            '6. Credit appraisal will be done by the bank',
            '7. Loan sanction letter will be issued if approved',
            '8. Complete documentation and sign loan agreement',
            '9. Loan amount will be disbursed to your account',
            '10. Start EMI payments as per schedule'
        ]
        
        if loan_amount > 500000:
            guidance.insert(5, '5a. Property valuation will be conducted for collateral')
        
        return guidance
    
    def _estimate_processing_time(self, loan_amount: float) -> str:
        """Estimate loan processing time"""
        
        if loan_amount <= 100000:
            return '7-10 working days'
        elif loan_amount <= 500000:
            return '15-20 working days'
        else:
            return '20-30 working days'
    
    def _get_affordability_recommendation(self, status: str) -> str:
        """Get recommendation based on affordability status"""
        
        recommendations = {
            'excellent': 'You have excellent loan affordability. You can comfortably take the loan.',
            'good': 'You have good loan affordability. Proceed with the loan application.',
            'moderate': 'Your affordability is moderate. Consider reducing loan amount or increasing tenure.',
            'poor': 'Your current affordability is poor. Focus on increasing income or reducing expenses before taking loan.'
        }
        
        return recommendations.get(status, 'Assess your financial situation carefully.')


# Tool functions for agent integration

def create_loan_credit_tools(region: str = "us-east-1") -> LoanCreditTools:
    """Factory function to create loan and credit tools instance"""
    return LoanCreditTools(region=region)


def assess_financing_needs_tool(farmer_profile: Dict[str, Any], farm_details: Dict[str, Any], 
                                purpose: str) -> str:
    """Tool for assessing financing needs"""
    tools = create_loan_credit_tools()
    result = tools.assess_financing_needs(farmer_profile, farm_details, purpose)
    
    if result['success']:
        return f"""Financing Needs Assessment:

Required Amount: ₹{result['required_amount']:,.2f}
Monthly Surplus: ₹{result['repayment_capacity']['monthly_surplus']:,.2f}
Repayment Capacity: {result['repayment_capacity']['capacity_level'].upper()}
Eligibility: {'ELIGIBLE' if result['eligibility']['eligible'] else 'NOT ELIGIBLE'}
Recommendation: {result['recommendation']['recommendation_type'].upper()}
"""
    else:
        return f"Error: {result.get('error', 'Failed to assess financing needs')}"
