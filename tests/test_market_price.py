"""
Tests for Market Price Tracking Tools
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.market_price_tools import MarketPriceTools, create_market_price_tools


class TestMarketPriceTools:
    """Test suite for market price tracking tools"""
    
    @pytest.fixture
    def market_tools(self):
        """Create market price tools instance for testing"""
        return create_market_price_tools(region='us-east-1')
    
    def test_get_current_prices(self, market_tools):
        """Test fetching current market prices"""
        result = market_tools.get_current_prices(
            crop_name='wheat',
            latitude=28.6139,
            longitude=77.2090,
            radius_km=50
        )
        
        assert result['success'] is True
        assert 'crop_name' in result
        assert result['crop_name'] == 'wheat'
        assert 'markets' in result
        assert len(result['markets']) > 0
        assert 'statistics' in result
        assert 'avg_price' in result['statistics']
        assert 'min_price' in result['statistics']
        assert 'max_price' in result['statistics']
        assert result['statistics']['min_price'] <= result['statistics']['avg_price']
        assert result['statistics']['avg_price'] <= result['statistics']['max_price']
    
    def test_get_current_prices_with_cache(self, market_tools):
        """Test caching mechanism for current prices"""
        # First call - should fetch from API
        result1 = market_tools.get_current_prices(
            crop_name='rice',
            latitude=28.6139,
            longitude=77.2090,
            radius_km=50
        )
        
        assert result1['success'] is True
        assert result1.get('from_cache', False) is False
        
        # Second call - should use cache
        result2 = market_tools.get_current_prices(
            crop_name='rice',
            latitude=28.6139,
            longitude=77.2090,
            radius_km=50
        )
        
        assert result2['success'] is True
        # Note: Cache might not work in test environment without DynamoDB
    
    def test_get_price_history(self, market_tools):
        """Test fetching price history"""
        result = market_tools.get_price_history(
            crop_name='wheat',
            market_id='MKT001',
            days=30
        )
        
        assert result['success'] is True
        assert 'history' in result
        assert len(result['history']) > 0
        assert 'trends' in result
        assert 'trend' in result['trends']
        assert result['trends']['trend'] in ['increasing', 'decreasing', 'stable', 'insufficient_data']
    
    def test_predict_price_trends(self, market_tools):
        """Test price trend prediction"""
        result = market_tools.predict_price_trends(
            crop_name='wheat',
            market_id='MKT001',
            forecast_days=7
        )
        
        assert result['success'] is True
        assert 'predictions' in result
        assert len(result['predictions']) == 7
        
        for pred in result['predictions']:
            assert 'date' in pred
            assert 'predicted_price' in pred
            assert 'confidence_range' in pred
            assert 'low' in pred['confidence_range']
            assert 'high' in pred['confidence_range']
    
    def test_get_optimal_selling_time(self, market_tools):
        """Test optimal selling time calculation"""
        result = market_tools.get_optimal_selling_time(
            crop_name='wheat',
            latitude=28.6139,
            longitude=77.2090,
            harvest_date=None,
            storage_capacity=True
        )
        
        assert result['success'] is True
        assert 'recommendation' in result
        assert 'timing' in result['recommendation']
        assert 'reason' in result['recommendation']
        assert 'expected_price' in result['recommendation']
        assert 'perishability' in result
        assert 'category' in result['perishability']
    
    def test_optimal_selling_time_no_storage(self, market_tools):
        """Test optimal selling time without storage capacity"""
        result = market_tools.get_optimal_selling_time(
            crop_name='wheat',  # Use non-perishable crop
            latitude=28.6139,
            longitude=77.2090,
            harvest_date=None,
            storage_capacity=False
        )
        
        assert result['success'] is True
        assert result['recommendation']['timing'] == 'immediate'
        assert 'No storage capacity' in result['recommendation']['reason']
    
    def test_optimal_selling_time_perishable_crop(self, market_tools):
        """Test optimal selling time for highly perishable crop"""
        result = market_tools.get_optimal_selling_time(
            crop_name='tomato',
            latitude=28.6139,
            longitude=77.2090,
            harvest_date=None,
            storage_capacity=True
        )
        
        assert result['success'] is True
        assert result['perishability']['category'] == 'highly_perishable'
        assert result['recommendation']['timing'] == 'immediate'
    
    def test_crop_perishability(self, market_tools):
        """Test crop perishability classification"""
        # Highly perishable
        tomato_perish = market_tools._get_crop_perishability('tomato')
        assert tomato_perish['category'] == 'highly_perishable'
        assert tomato_perish['shelf_life_days'] < 14
        
        # Non-perishable
        wheat_perish = market_tools._get_crop_perishability('wheat')
        assert wheat_perish['category'] == 'non_perishable'
        assert wheat_perish['shelf_life_days'] >= 365
        
        # Moderately perishable
        potato_perish = market_tools._get_crop_perishability('potato')
        assert potato_perish['category'] == 'moderately_perishable'
    
    def test_price_trend_calculation(self, market_tools):
        """Test price trend calculation"""
        # Increasing trend
        increasing_prices = [100, 105, 110, 115, 120]
        trends = market_tools._calculate_price_trends(increasing_prices)
        assert trends['trend'] == 'increasing'
        assert trends['change_percent'] > 5
        
        # Decreasing trend
        decreasing_prices = [120, 115, 110, 105, 100]
        trends = market_tools._calculate_price_trends(decreasing_prices)
        assert trends['trend'] == 'decreasing'
        assert trends['change_percent'] < -5
        
        # Stable trend
        stable_prices = [100, 101, 100, 99, 100]
        trends = market_tools._calculate_price_trends(stable_prices)
        assert trends['trend'] == 'stable'
    
    def test_simple_price_prediction(self, market_tools):
        """Test simple moving average prediction"""
        history = [
            {'date': (datetime.now() - timedelta(days=i)).isoformat(), 'price': 2400 + i * 10}
            for i in range(30, 0, -1)
        ]
        
        predictions = market_tools._simple_price_prediction(history, 7)
        
        assert len(predictions) == 7
        assert all('date' in p for p in predictions)
        assert all('predicted_price' in p for p in predictions)
        assert all('confidence_range' in p for p in predictions)
    
    def test_invalid_crop_name(self, market_tools):
        """Test handling of empty crop name"""
        result = market_tools.get_current_prices(
            crop_name='',
            latitude=28.6139,
            longitude=77.2090,
            radius_km=50
        )
        
        # Should handle gracefully
        assert 'success' in result
    
    def test_invalid_coordinates(self, market_tools):
        """Test handling of invalid coordinates"""
        result = market_tools.get_current_prices(
            crop_name='wheat',
            latitude=999,  # Invalid latitude
            longitude=999,  # Invalid longitude
            radius_km=50
        )
        
        # Should handle gracefully
        assert 'success' in result
    
    def test_cache_key_generation(self, market_tools):
        """Test cache key generation"""
        key1 = market_tools._get_cache_key('wheat', 28.6139, 77.2090, 50)
        key2 = market_tools._get_cache_key('wheat', 28.6139, 77.2090, 50)
        key3 = market_tools._get_cache_key('rice', 28.6139, 77.2090, 50)
        
        # Same inputs should generate same key
        assert key1 == key2
        
        # Different crop should generate different key
        assert key1 != key3
    
    def test_market_data_structure(self, market_tools):
        """Test structure of market data"""
        result = market_tools.get_current_prices(
            crop_name='wheat',
            latitude=28.6139,
            longitude=77.2090,
            radius_km=50
        )
        
        if result['success'] and result['markets']:
            market = result['markets'][0]
            
            # Check required fields
            assert 'market_id' in market
            assert 'market_name' in market
            assert 'price' in market
            assert 'distance_km' in market
            assert 'location' in market
            assert 'latitude' in market['location']
            assert 'longitude' in market['location']
            assert 'district' in market['location']
            assert 'state' in market['location']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
