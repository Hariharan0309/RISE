"""
Tests for RISE Crop Profitability Calculator Tools
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.profitability_calculator_tools import ProfitabilityCalculatorTools


class TestProfitabilityCalculatorTools(unittest.TestCase):
    """Test cases for profitability calculator tools"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tools = ProfitabilityCalculatorTools(region='us-east-1')
        self.test_location = {
            'state': 'Punjab',
            'district': 'Ludhiana',
            'latitude': 30.9010,
            'longitude': 75.8573
        }
    
    def test_estimate_input_costs(self):
        """Test input cost estimation"""
        result = self.tools.estimate_input_costs(
            crop_name='wheat',
            farm_size_acres=5.0,
            location=self.test_location,
            soil_type='loamy',
            season='rabi'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('costs_per_acre', result)
        self.assertIn('total_cost_per_acre', result)
        self.assertIn('total_farm_cost', result)
        self.assertGreater(result['total_cost_per_acre'], 0)
        self.assertEqual(
            result['total_farm_cost'],
            result['total_cost_per_acre'] * 5.0
        )
        
        # Check cost categories
        self.assertIn('cost_categories', result)
        categories = result['cost_categories']
        self.assertIn('inputs', categories)
        self.assertIn('labor', categories)
        self.assertIn('operations', categories)
    
    def test_predict_crop_yield(self):
        """Test crop yield prediction"""
        result = self.tools.predict_crop_yield(
            crop_name='wheat',
            location=self.test_location,
            soil_type='loamy',
            season='rabi'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('yield_per_acre_quintals', result)
        
        yields = result['yield_per_acre_quintals']
        self.assertIn('average', yields)
        self.assertIn('optimistic', yields)
        self.assertIn('conservative', yields)
        
        # Verify yield relationships
        self.assertGreater(yields['optimistic'], yields['average'])
        self.assertGreater(yields['average'], yields['conservative'])
        
        # Check factors
        self.assertIn('factors_applied', result)
        factors = result['factors_applied']
        self.assertIn('soil_factor', factors)
        self.assertIn('location_factor', factors)
        self.assertIn('season_factor', factors)
    
    def test_calculate_comprehensive_profitability(self):
        """Test comprehensive profitability calculation"""
        result = self.tools.calculate_comprehensive_profitability(
            crop_name='wheat',
            farm_size_acres=5.0,
            location=self.test_location,
            soil_type='loamy',
            season='rabi'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('analysis_id', result)
        self.assertIn('cost_breakdown', result)
        self.assertIn('yield_prediction', result)
        self.assertIn('profitability_scenarios', result)
        self.assertIn('risk_assessment', result)
        self.assertIn('projections', result)
        
        # Check scenarios
        scenarios = result['profitability_scenarios']
        self.assertIn('average', scenarios)
        self.assertIn('optimistic', scenarios)
        self.assertIn('conservative', scenarios)
        
        # Verify profit calculations
        avg_scenario = scenarios['average']
        self.assertIn('total_revenue', avg_scenario)
        self.assertIn('total_cost', avg_scenario)
        self.assertIn('net_profit', avg_scenario)
        self.assertIn('roi_percent', avg_scenario)
        
        # Verify profit = revenue - cost
        expected_profit = avg_scenario['total_revenue'] - avg_scenario['total_cost']
        self.assertAlmostEqual(avg_scenario['net_profit'], expected_profit, places=1)
    
    def test_compare_crop_profitability(self):
        """Test crop profitability comparison"""
        crop_list = ['wheat', 'rice', 'maize']
        
        result = self.tools.compare_crop_profitability(
            crop_list=crop_list,
            farm_size_acres=5.0,
            location=self.test_location,
            soil_type='loamy',
            season='rabi'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('comparisons', result)
        self.assertIn('rankings', result)
        self.assertIn('best_overall', result)
        
        # Check comparisons
        comparisons = result['comparisons']
        self.assertEqual(len(comparisons), 3)
        
        for comp in comparisons:
            self.assertIn('crop_name', comp)
            self.assertIn('total_cost', comp)
            self.assertIn('average_profit', comp)
            self.assertIn('roi', comp)
            self.assertIn('risk_score', comp)
        
        # Check rankings
        rankings = result['rankings']
        self.assertIn('by_profit', rankings)
        self.assertIn('by_roi', rankings)
        self.assertIn('by_low_risk', rankings)
        
        # Verify rankings have all crops
        for ranking in rankings.values():
            self.assertEqual(len(ranking), 3)
            self.assertEqual(set(ranking), set(crop_list))
    
    def test_risk_assessment(self):
        """Test risk assessment functionality"""
        result = self.tools.calculate_comprehensive_profitability(
            crop_name='cotton',  # High-risk crop
            farm_size_acres=5.0,
            location=self.test_location,
            soil_type='loamy',
            season='kharif'
        )
        
        self.assertTrue(result['success'])
        
        risk_assessment = result['risk_assessment']
        self.assertIn('risk_factors', risk_assessment)
        self.assertIn('overall_risk_score', risk_assessment)
        self.assertIn('overall_risk_level', risk_assessment)
        self.assertIn('recommendation', risk_assessment)
        
        # Check risk factors
        risk_factors = risk_assessment['risk_factors']
        self.assertGreater(len(risk_factors), 0)
        
        for factor in risk_factors:
            self.assertIn('factor', factor)
            self.assertIn('risk_level', factor)
            self.assertIn('description', factor)
            self.assertIn('mitigation', factor)
            self.assertIn(factor['risk_level'], ['low', 'medium', 'high'])
        
        # Overall risk score should be between 1 and 10
        self.assertGreaterEqual(risk_assessment['overall_risk_score'], 1)
        self.assertLessEqual(risk_assessment['overall_risk_score'], 10)
    
    def test_projections(self):
        """Test profit/loss projections"""
        result = self.tools.calculate_comprehensive_profitability(
            crop_name='wheat',
            farm_size_acres=5.0,
            location=self.test_location,
            soil_type='loamy',
            season='rabi'
        )
        
        self.assertTrue(result['success'])
        
        projections = result['projections']
        self.assertIn('projections', projections)
        self.assertIn('expected_profit', projections)
        self.assertIn('break_even_price', projections)
        self.assertIn('break_even_yield', projections)
        
        # Check projection scenarios
        proj_scenarios = projections['projections']
        self.assertIn('best_case', proj_scenarios)
        self.assertIn('expected_case', proj_scenarios)
        self.assertIn('worst_case', proj_scenarios)
        
        # Verify probabilities sum to 1.0
        total_prob = sum(
            proj_scenarios[case]['probability']
            for case in ['best_case', 'expected_case', 'worst_case']
        )
        self.assertAlmostEqual(total_prob, 1.0, places=2)
        
        # Break-even values should be positive
        self.assertGreater(projections['break_even_price'], 0)
        self.assertGreater(projections['break_even_yield'], 0)
    
    def test_custom_input_costs(self):
        """Test profitability with custom input costs"""
        custom_costs = {
            'seeds': 1500,
            'fertilizers_npk': 4000
        }
        
        result = self.tools.calculate_comprehensive_profitability(
            crop_name='wheat',
            farm_size_acres=5.0,
            location=self.test_location,
            soil_type='loamy',
            season='rabi',
            custom_input_costs=custom_costs
        )
        
        self.assertTrue(result['success'])
        
        # Verify custom costs were applied
        costs_per_acre = result['cost_breakdown']['costs_per_acre']
        self.assertEqual(costs_per_acre['seeds'], 1500)
        self.assertEqual(costs_per_acre['fertilizers_npk'], 4000)
    
    def test_historical_data_integration(self):
        """Test yield prediction with historical data"""
        historical_data = {
            'past_yields': [18.5, 19.2, 17.8, 20.1, 18.9]
        }
        
        result = self.tools.predict_crop_yield(
            crop_name='wheat',
            location=self.test_location,
            soil_type='loamy',
            season='rabi',
            historical_data=historical_data
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['confidence'], 'high')
        
        # Historical average
        hist_avg = sum(historical_data['past_yields']) / len(historical_data['past_yields'])
        
        # Predicted yield should be influenced by historical data
        predicted_avg = result['yield_per_acre_quintals']['average']
        # Should be within reasonable range of historical average
        self.assertGreater(predicted_avg, hist_avg * 0.7)
        self.assertLess(predicted_avg, hist_avg * 1.3)
    
    def test_soil_type_adjustments(self):
        """Test that different soil types affect costs and yields"""
        soil_types = ['loamy', 'sandy', 'clay', 'black']
        results = {}
        
        for soil_type in soil_types:
            result = self.tools.calculate_comprehensive_profitability(
                crop_name='wheat',
                farm_size_acres=5.0,
                location=self.test_location,
                soil_type=soil_type,
                season='rabi'
            )
            
            self.assertTrue(result['success'])
            results[soil_type] = {
                'cost': result['cost_breakdown']['total_cost_per_acre'],
                'yield': result['yield_prediction']['yield_per_acre_quintals']['average']
            }
        
        # Verify that different soil types produce different results
        costs = [results[st]['cost'] for st in soil_types]
        yields = [results[st]['yield'] for st in soil_types]
        
        # Not all costs should be identical
        self.assertGreater(len(set(costs)), 1)
        # Not all yields should be identical
        self.assertGreater(len(set(yields)), 1)
    
    def test_season_suitability(self):
        """Test that season affects yield predictions"""
        # Wheat is optimal for rabi season
        rabi_result = self.tools.predict_crop_yield(
            crop_name='wheat',
            location=self.test_location,
            soil_type='loamy',
            season='rabi'
        )
        
        kharif_result = self.tools.predict_crop_yield(
            crop_name='wheat',
            location=self.test_location,
            soil_type='loamy',
            season='kharif'
        )
        
        self.assertTrue(rabi_result['success'])
        self.assertTrue(kharif_result['success'])
        
        # Rabi season should have better yield for wheat
        rabi_yield = rabi_result['yield_per_acre_quintals']['average']
        kharif_yield = kharif_result['yield_per_acre_quintals']['average']
        
        self.assertGreater(rabi_yield, kharif_yield)


if __name__ == '__main__':
    unittest.main()
