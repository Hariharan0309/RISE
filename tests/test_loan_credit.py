"""
RISE Loan and Credit Planning - Unit Tests
Comprehensive tests for loan and credit planning functionality
"""

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.loan_credit_tools import LoanCreditTools


class TestLoanCreditTools(unittest.TestCase):
    """Test cases for loan and credit planning tools"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tools = LoanCreditTools(region='us-east-1')
        
        self.farmer_profile = {
            'name': 'Test Farmer',
            'age': 35,
            'annual_farm_income': 250000,
            'other_income': 50000,
            'annual_expenses': 180000,
            'credit_score': 680,
            'land_ownership': True
        }
        
        self.farm_details = {
            'farm_size_acres': 5.0,
            'soil_type': 'loamy',
            'crops': ['wheat', 'rice']
        }
    
    def test_assess_financing_needs_success(self):
        """Test successful financing needs assessment"""
        result = self.tools.assess_financing_needs(
            farmer_profile=self.farmer_profile,
            farm_details=self.farm_details,
            purpose='equipment_purchase'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('assessment_id', result)
        self.assertIn('required_amount', result)
        self.assertIn('repayment_capacity', result)
        self.assertIn('eligibility', result)
        self.assertIn('recommendation', result)
        
        # Check repayment capacity structure
        capacity = result['repayment_capacity']
        self.assertIn('annual_income', capacity)
        self.assertIn('monthly_surplus', capacity)
        self.assertIn('capacity_level', capacity)
        
        # Check eligibility structure
        eligibility = result['eligibility']
        self.assertIn('eligible', eligibility)
        self.assertIn('eligibility_factors', eligibility)
    
    def test_assess_financing_needs_different_purposes(self):
        """Test financing needs for different purposes"""
        purposes = ['crop_cultivation', 'equipment_purchase', 'land_improvement', 'irrigation_setup']
        
        for purpose in purposes:
            result = self.tools.assess_financing_needs(
                farmer_profile=self.farmer_profile,
                farm_details=self.farm_details,
                purpose=purpose
            )
            
            self.assertTrue(result['success'])
            self.assertGreater(result['required_amount'], 0)
    
    def test_recommend_loan_products_success(self):
        """Test successful loan product recommendations"""
        result = self.tools.recommend_loan_products(
            required_amount=200000,
            purpose='equipment_purchase',
            farmer_profile=self.farmer_profile,
            location={'state': 'Punjab'},
            repayment_period_months=60
        )
        
        self.assertTrue(result['success'])
        self.assertIn('recommendations', result)
        self.assertIn('total_products_found', result)
        self.assertGreater(len(result['recommendations']), 0)
        
        # Check product structure
        product = result['recommendations'][0]
        self.assertIn('lender_name', product)
        self.assertIn('interest_rate', product)
        self.assertIn('calculated_emi', product)
        self.assertIn('total_interest', product)
        self.assertIn('suitability_score', product)
    
    def test_recommend_loan_products_filtering(self):
        """Test loan product filtering by amount"""
        # Test with small amount
        result_small = self.tools.recommend_loan_products(
            required_amount=50000,
            purpose='crop_cultivation',
            farmer_profile=self.farmer_profile,
            location={'state': 'Punjab'}
        )
        
        # Test with large amount
        result_large = self.tools.recommend_loan_products(
            required_amount=1000000,
            purpose='equipment_purchase',
            farmer_profile=self.farmer_profile,
            location={'state': 'Punjab'}
        )
        
        self.assertTrue(result_small['success'])
        self.assertTrue(result_large['success'])
    
    def test_generate_repayment_schedule_basic(self):
        """Test basic repayment schedule generation"""
        result = self.tools.generate_repayment_schedule(
            loan_amount=200000,
            interest_rate=9.5,
            tenure_months=60
        )
        
        self.assertTrue(result['success'])
        self.assertIn('schedule', result)
        self.assertIn('monthly_emi', result)
        self.assertIn('total_interest', result)
        self.assertIn('total_repayment', result)
        
        # Check schedule length
        self.assertEqual(len(result['schedule']), 60)
        
        # Check EMI consistency
        for month_data in result['schedule']:
            self.assertAlmostEqual(month_data['emi'], result['monthly_emi'], places=2)
    
    def test_generate_repayment_schedule_with_crop_cycle(self):
        """Test repayment schedule with crop cycle alignment"""
        crop_cycle = {
            'harvest_months': [6, 12, 18, 24],
            'harvest_income': 100000
        }
        
        result = self.tools.generate_repayment_schedule(
            loan_amount=200000,
            interest_rate=9.5,
            tenure_months=24,
            crop_cycle=crop_cycle
        )
        
        self.assertTrue(result['success'])
        
        # Check harvest months are marked
        harvest_months = [m for m in result['schedule'] if m['is_harvest_month']]
        self.assertEqual(len(harvest_months), 4)
        
        # Check expected income is set for harvest months
        for month_data in harvest_months:
            self.assertEqual(month_data['expected_income'], 100000)
    
    def test_compile_financial_documents(self):
        """Test financial document compilation"""
        result = self.tools.compile_financial_documents(
            farmer_profile=self.farmer_profile,
            farm_details=self.farm_details,
            loan_purpose='equipment_purchase',
            loan_amount=200000
        )
        
        self.assertTrue(result['success'])
        self.assertIn('compilation_id', result)
        self.assertIn('required_documents', result)
        self.assertIn('financial_summary', result)
        self.assertIn('application_guidance', result)
        self.assertIn('estimated_processing_time', result)
        
        # Check documents structure
        self.assertGreater(len(result['required_documents']), 0)
        for doc in result['required_documents']:
            self.assertIn('document', doc)
            self.assertIn('mandatory', doc)
            self.assertIn('format', doc)
    
    def test_compile_documents_large_loan(self):
        """Test document compilation for large loan (requires collateral)"""
        result = self.tools.compile_financial_documents(
            farmer_profile=self.farmer_profile,
            farm_details=self.farm_details,
            loan_purpose='land_improvement',
            loan_amount=600000  # Large amount
        )
        
        self.assertTrue(result['success'])
        
        # Check for collateral documents
        doc_names = [doc['document'] for doc in result['required_documents']]
        self.assertIn('Collateral Documents', doc_names)
    
    def test_calculate_loan_affordability_good(self):
        """Test affordability calculation with good financial position"""
        result = self.tools.calculate_loan_affordability(
            monthly_income=30000,
            monthly_expenses=15000,
            existing_loans=[],
            interest_rate=9.5,
            tenure_months=60
        )
        
        self.assertTrue(result['success'])
        self.assertIn('max_affordable_emi', result)
        self.assertIn('max_loan_amount', result)
        self.assertIn('debt_to_income_ratio', result)
        self.assertIn('affordability_status', result)
        
        # Should have good affordability
        self.assertIn(result['affordability_status'], ['excellent', 'good'])
        self.assertGreater(result['max_loan_amount'], 0)
    
    def test_calculate_loan_affordability_with_existing_loans(self):
        """Test affordability with existing loans"""
        existing_loans = [
            {'emi': 5000},
            {'emi': 3000}
        ]
        
        result = self.tools.calculate_loan_affordability(
            monthly_income=30000,
            monthly_expenses=15000,
            existing_loans=existing_loans,
            interest_rate=9.5,
            tenure_months=60
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['existing_emi_total'], 8000)
        
        # Disposable income should account for existing EMIs
        expected_disposable = 30000 - 15000 - 8000
        self.assertEqual(result['disposable_income'], expected_disposable)
    
    def test_calculate_loan_affordability_poor(self):
        """Test affordability with poor financial position"""
        result = self.tools.calculate_loan_affordability(
            monthly_income=10000,
            monthly_expenses=8000,
            existing_loans=[{'emi': 1500}],
            interest_rate=9.5,
            tenure_months=60
        )
        
        self.assertTrue(result['success'])
        
        # Check that affordability calculation returns valid status
        self.assertIn(result['affordability_status'], ['excellent', 'good', 'moderate', 'poor'])
        
        # With limited disposable income, max loan should be relatively small
        self.assertLess(result['max_loan_amount'], 50000)
    
    def test_emi_calculation(self):
        """Test EMI calculation accuracy"""
        # Known EMI calculation
        principal = 100000
        rate = 12.0  # 12% annual
        tenure = 12  # 12 months
        
        emi = self.tools._calculate_emi(principal, rate, tenure)
        
        # EMI should be reasonable
        self.assertGreater(emi, principal / tenure)  # More than simple division
        self.assertLess(emi, principal / tenure * 1.1)  # But not too much more
    
    def test_emi_calculation_zero_interest(self):
        """Test EMI calculation with zero interest"""
        principal = 100000
        rate = 0.0
        tenure = 12
        
        emi = self.tools._calculate_emi(principal, rate, tenure)
        
        # Should equal simple division
        self.assertAlmostEqual(emi, principal / tenure, places=2)
    
    def test_eligibility_age_check(self):
        """Test eligibility age restrictions"""
        # Test with valid age
        profile_valid = self.farmer_profile.copy()
        profile_valid['age'] = 35
        
        result_valid = self.tools.assess_financing_needs(
            farmer_profile=profile_valid,
            farm_details=self.farm_details,
            purpose='crop_cultivation'
        )
        
        # Test with invalid age (too young)
        profile_young = self.farmer_profile.copy()
        profile_young['age'] = 18
        
        result_young = self.tools.assess_financing_needs(
            farmer_profile=profile_young,
            farm_details=self.farm_details,
            purpose='crop_cultivation'
        )
        
        # Test with invalid age (too old)
        profile_old = self.farmer_profile.copy()
        profile_old['age'] = 70
        
        result_old = self.tools.assess_financing_needs(
            farmer_profile=profile_old,
            farm_details=self.farm_details,
            purpose='crop_cultivation'
        )
        
        self.assertTrue(result_valid['eligibility']['eligible'])
        self.assertFalse(result_young['eligibility']['eligible'])
        self.assertFalse(result_old['eligibility']['eligible'])
    
    def test_loan_product_scoring(self):
        """Test loan product scoring logic"""
        product1 = {
            'interest_rate': 7.0,
            'processing_fee_percent': 0.5,
            'lender_type': 'bank',
            'features': ['Feature1', 'Feature2', 'Feature3']
        }
        
        product2 = {
            'interest_rate': 12.0,
            'processing_fee_percent': 2.0,
            'lender_type': 'nbfc',
            'features': ['Feature1']
        }
        
        score1 = self.tools._score_loan_product(product1, 200000, self.farmer_profile, 60)
        score2 = self.tools._score_loan_product(product2, 200000, self.farmer_profile, 60)
        
        # Product 1 should score higher (lower interest, lower fees, bank)
        self.assertGreater(score1, score2)
    
    def test_repayment_schedule_balance_decreases(self):
        """Test that loan balance decreases over time"""
        result = self.tools.generate_repayment_schedule(
            loan_amount=100000,
            interest_rate=10.0,
            tenure_months=12
        )
        
        self.assertTrue(result['success'])
        
        # Check balance decreases
        for i in range(len(result['schedule']) - 1):
            current_balance = result['schedule'][i]['balance']
            next_balance = result['schedule'][i + 1]['balance']
            self.assertGreaterEqual(current_balance, next_balance)
        
        # Final balance should be near zero
        final_balance = result['schedule'][-1]['balance']
        self.assertLess(final_balance, 10)  # Allow small rounding error


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
