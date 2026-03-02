"""
Tests for Optimal Selling Time Calculator Tools
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.selling_time_tools import SellingTimeTools, create_selling_time_tools


class TestSellingTimeTools:
    """Test suite for selling time calculator tools"""
    
    @pytest.fixture
    def selling_tools(self):
        """Create selling time tools instance for testing"""
        return create_selling_time_tools(region='us-east-1')
    
    def test_analyze_perishability_highly_perishable(self, selling_tools):
        """Test perishability analysis for highly perishable crops"""
        result = selling_tools.analyze_perishability('tomato')
        
        assert result['success'] is True
        assert result['crop_name'] == 'tomato'
        assert result['category'] == 'highly_perishable'
        assert result['shelf_life_days'] <= 14
        assert result['quality_degradation_rate'] > 0
        assert 'optimal_storage_temp' in result
        assert 'storage_requirements' in result
        assert 'recommendation' in result
    
    def test_analyze_perishability_moderately_perishable(self, selling_tools):
        """Test perishability analysis for moderately perishable crops"""
        result = selling_tools.analyze_perishability('potato')
        
        assert result['success'] is True
        assert result['category'] == 'moderately_perishable'
        assert 15 <= result['shelf_life_days'] <= 120
    
    def test_analyze_perishability_non_perishable(self, selling_tools):
        """Test perishability analysis for non-perishable crops"""
        result = selling_tools.analyze_perishability('wheat')
        
        assert result['success'] is True
        assert result['category'] == 'non_perishable'
        assert result['shelf_life_days'] > 120
        assert result['quality_degradation_rate'] < 0.01
    
    def test_analyze_perishability_unknown_crop(self, selling_tools):
        """Test perishability analysis for unknown crop"""
        result = selling_tools.analyze_perishability('unknown_crop')
        
        assert result['success'] is True
        assert result['category'] == 'moderately_perishable'  # Default
    
    def test_calculate_storage_costs_standard(self, selling_tools):
        """Test storage cost calculation with standard storage"""
        result = selling_tools.calculate_storage_costs(
            crop_name='wheat',
            quantity_quintals=100,
            storage_days=30,
            storage_type='standard'
        )
        
        assert result['success'] is True
        assert result['crop_name'] == 'wheat'
        assert result['quantity_quintals'] == 100
        assert result['storage_days'] == 30
        assert 'costs' in result
        assert 'facility_cost' in result['costs']
        assert 'handling_cost' in result['costs']
        assert 'insurance_cost' in result['costs']
        assert 'total_cost' in result['costs']
        assert result['costs']['total_cost'] > 0
        assert 'quality_impact' in result

    
    def test_calculate_storage_costs_cold_storage(self, selling_tools):
        """Test storage cost calculation with cold storage"""
        result = selling_tools.calculate_storage_costs(
            crop_name='tomato',
            quantity_quintals=50,
            storage_days=7,
            storage_type='cold'
        )
        
        assert result['success'] is True
        assert result['storage_type'] == 'cold'
        # Cold storage should be more expensive than standard
        assert result['costs']['total_cost'] > 0
    
    def test_calculate_storage_costs_quality_degradation(self, selling_tools):
        """Test quality degradation calculation"""
        result = selling_tools.calculate_storage_costs(
            crop_name='tomato',
            quantity_quintals=100,
            storage_days=5,
            storage_type='cold'
        )
        
        assert result['success'] is True
        assert 'quality_impact' in result
        assert 'degradation_percent' in result['quality_impact']
        assert 'remaining_quality' in result['quality_impact']
        assert result['quality_impact']['degradation_percent'] >= 0
        assert result['quality_impact']['remaining_quality'] <= 100
    
    def test_calculate_optimal_selling_time_no_storage(self, selling_tools):
        """Test optimal selling time without storage capacity"""
        predicted_prices = [
            {
                'date': (datetime.now() + timedelta(days=i)).isoformat(),
                'predicted_price': 2500 + i * 50
            }
            for i in range(1, 8)
        ]
        
        result = selling_tools.calculate_optimal_selling_time(
            crop_name='wheat',
            current_price=2400,
            predicted_prices=predicted_prices,
            quantity_quintals=100,
            storage_capacity=False
        )
        
        assert result['success'] is True
        assert result['recommendation']['timing'] == 'immediate'
        assert 'No storage capacity' in result['recommendation']['reason']
    
    def test_calculate_optimal_selling_time_highly_perishable(self, selling_tools):
        """Test optimal selling time for highly perishable crop"""
        predicted_prices = [
            {
                'date': (datetime.now() + timedelta(days=i)).isoformat(),
                'predicted_price': 3000 + i * 100
            }
            for i in range(1, 8)
        ]
        
        result = selling_tools.calculate_optimal_selling_time(
            crop_name='tomato',
            current_price=2800,
            predicted_prices=predicted_prices,
            quantity_quintals=50,
            storage_capacity=True
        )
        
        assert result['success'] is True
        assert result['recommendation']['timing'] == 'immediate'
        assert 'highly perishable' in result['recommendation']['reason'].lower()
    
    def test_calculate_optimal_selling_time_with_storage(self, selling_tools):
        """Test optimal selling time with storage and price increase"""
        predicted_prices = [
            {
                'date': (datetime.now() + timedelta(days=i)).isoformat(),
                'predicted_price': 2400 + i * 100
            }
            for i in range(1, 15)
        ]
        
        result = selling_tools.calculate_optimal_selling_time(
            crop_name='wheat',
            current_price=2400,
            predicted_prices=predicted_prices,
            quantity_quintals=100,
            storage_capacity=True,
            storage_type='warehouse'
        )
        
        assert result['success'] is True
        assert 'recommendation' in result
        assert 'timing' in result['recommendation']
        assert 'days_to_wait' in result['recommendation']
        assert 'net_profit' in result['recommendation']
        assert 'scenarios' in result
        assert len(result['scenarios']) > 0
    
    def test_calculate_optimal_selling_time_scenarios(self, selling_tools):
        """Test that multiple scenarios are evaluated"""
        predicted_prices = [
            {
                'date': (datetime.now() + timedelta(days=i)).isoformat(),
                'predicted_price': 2500 + i * 20
            }
            for i in range(1, 10)
        ]
        
        result = selling_tools.calculate_optimal_selling_time(
            crop_name='onion',
            current_price=2500,
            predicted_prices=predicted_prices,
            quantity_quintals=100,
            storage_capacity=True
        )
        
        assert result['success'] is True
        assert 'scenarios' in result
        # Should have immediate scenario plus predicted scenarios
        assert len(result['scenarios']) > 1
        
        # Check scenario structure
        for scenario in result['scenarios']:
            assert 'days' in scenario
            assert 'price' in scenario or 'adjusted_price' in scenario
            assert 'storage_cost' in scenario
            assert 'net_profit' in scenario
    
    def test_create_price_alert(self, selling_tools):
        """Test price alert creation"""
        result = selling_tools.create_price_alert(
            user_id='test_user_123',
            crop_name='wheat',
            target_price=2800,
            market_id='MKT001',
            phone_number='+919876543210'
        )
        
        assert result['success'] is True
        assert 'alert_id' in result
        assert result['crop_name'] == 'wheat'
        assert result['target_price'] == 2800
        assert 'message' in result
    
    def test_get_user_alerts(self, selling_tools):
        """Test retrieving user alerts"""
        # Create an alert first
        selling_tools.create_price_alert(
            user_id='test_user_456',
            crop_name='rice',
            target_price=3000,
            market_id='MKT002'
        )
        
        result = selling_tools.get_user_alerts('test_user_456')
        
        assert result['success'] is True
        assert 'alerts' in result
        assert 'count' in result
    
    def test_delete_alert(self, selling_tools):
        """Test alert deletion"""
        # Create an alert
        create_result = selling_tools.create_price_alert(
            user_id='test_user_789',
            crop_name='tomato',
            target_price=3500,
            market_id='MKT003'
        )
        
        if create_result['success']:
            alert_id = create_result['alert_id']
            
            # Delete the alert
            delete_result = selling_tools.delete_alert(alert_id)
            
            assert delete_result['success'] is True
            assert 'message' in delete_result
    
    def test_check_price_alerts(self, selling_tools):
        """Test checking price alerts against current prices"""
        current_prices = {
            'markets': [
                {
                    'market_id': 'MKT001',
                    'market_name': 'Test Market',
                    'price': 2900
                }
            ]
        }
        
        result = selling_tools.check_price_alerts('test_user_123', current_prices)
        
        assert result['success'] is True
        assert 'triggered_count' in result
        assert 'alerts' in result
    
    def test_storage_cost_increases_with_days(self, selling_tools):
        """Test that storage cost increases with storage days"""
        result_7_days = selling_tools.calculate_storage_costs(
            crop_name='wheat',
            quantity_quintals=100,
            storage_days=7,
            storage_type='standard'
        )
        
        result_30_days = selling_tools.calculate_storage_costs(
            crop_name='wheat',
            quantity_quintals=100,
            storage_days=30,
            storage_type='standard'
        )
        
        assert result_7_days['success'] is True
        assert result_30_days['success'] is True
        assert result_30_days['costs']['total_cost'] > result_7_days['costs']['total_cost']
    
    def test_storage_cost_increases_with_quantity(self, selling_tools):
        """Test that storage cost increases with quantity"""
        result_50_quintals = selling_tools.calculate_storage_costs(
            crop_name='wheat',
            quantity_quintals=50,
            storage_days=30,
            storage_type='standard'
        )
        
        result_100_quintals = selling_tools.calculate_storage_costs(
            crop_name='wheat',
            quantity_quintals=100,
            storage_days=30,
            storage_type='standard'
        )
        
        assert result_50_quintals['success'] is True
        assert result_100_quintals['success'] is True
        assert result_100_quintals['costs']['total_cost'] > result_50_quintals['costs']['total_cost']
    
    def test_perishability_recommendation_format(self, selling_tools):
        """Test that perishability recommendations are properly formatted"""
        crops = ['tomato', 'potato', 'wheat']
        
        for crop in crops:
            result = selling_tools.analyze_perishability(crop)
            assert result['success'] is True
            assert 'recommendation' in result
            assert isinstance(result['recommendation'], str)
            assert len(result['recommendation']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
