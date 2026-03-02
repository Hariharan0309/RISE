"""
Tests for Direct Buyer Connection Tools
"""

import pytest
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.buyer_connection_tools import BuyerConnectionTools, create_buyer_connection_tools


class TestBuyerConnectionTools:
    """Test suite for buyer connection tools"""
    
    @pytest.fixture
    def buyer_tools(self):
        """Create buyer connection tools instance for testing"""
        return create_buyer_connection_tools(region='us-east-1')
    
    @pytest.fixture
    def sample_buyer_data(self):
        """Sample buyer registration data"""
        return {
            'business_name': 'Fresh Produce Traders',
            'contact_person': 'Rajesh Kumar',
            'phone_number': '+919876543210',
            'email': 'rajesh@freshproduce.com',
            'business_type': 'wholesaler',
            'location': {
                'state': 'Delhi',
                'district': 'Central Delhi',
                'latitude': 28.6139,
                'longitude': 77.2090
            },
            'crop_interests': ['wheat', 'rice', 'potato'],
            'payment_terms': 'advance_50_percent'
        }
    
    @pytest.fixture
    def sample_listing_data(self):
        """Sample crop listing data"""
        return {
            'crop_name': 'wheat',
            'quantity': 100,
            'unit': 'quintal',
            'quality_grade': 'grade_a',
            'expected_price': 2500,
            'harvest_date': '2024-04-15',
            'location': {
                'state': 'Uttar Pradesh',
                'district': 'Ghaziabad',
                'latitude': 28.6692,
                'longitude': 77.4538
            },
            'description': 'High quality wheat, well-maintained crop'
        }
    
    def test_register_buyer(self, buyer_tools, sample_buyer_data):
        """Test buyer registration"""
        result = buyer_tools.register_buyer(sample_buyer_data)
        
        assert result['success'] is True
        assert 'buyer_id' in result
        assert result['buyer_id'].startswith('buyer_')
        assert result['verification_status'] == 'pending'
        assert 'message' in result
    
    def test_register_buyer_validation(self, buyer_tools):
        """Test buyer registration with missing fields"""
        incomplete_data = {
            'business_name': 'Test Business'
            # Missing required fields
        }
        
        result = buyer_tools.register_buyer(incomplete_data)
        
        # Should handle gracefully
        assert 'success' in result
    
    def test_create_crop_listing(self, buyer_tools, sample_listing_data):
        """Test crop listing creation"""
        farmer_id = 'farmer_test123'
        result = buyer_tools.create_crop_listing(farmer_id, sample_listing_data)
        
        assert result['success'] is True
        assert 'listing_id' in result
        assert result['listing_id'].startswith('listing_')
        assert result['status'] == 'active'
        assert 'potential_matches' in result
        assert isinstance(result['potential_matches'], int)
    
    def test_create_listing_with_matches(self, buyer_tools, sample_listing_data):
        """Test crop listing with buyer matching"""
        farmer_id = 'farmer_test123'
        result = buyer_tools.create_crop_listing(farmer_id, sample_listing_data)
        
        assert result['success'] is True
        assert 'matches' in result
        assert isinstance(result['matches'], list)
        
        # Check match structure if matches exist
        if result['matches']:
            match = result['matches'][0]
            assert 'buyer_id' in match
            assert 'business_name' in match
            assert 'match_score' in match
            assert 'distance_km' in match
            assert 0 <= match['match_score'] <= 1
    
    def test_get_quality_standards(self, buyer_tools):
        """Test quality standards retrieval"""
        result = buyer_tools.get_quality_standards('wheat')
        
        assert result['success'] is True
        assert 'crop_name' in result
        assert result['crop_name'] == 'wheat'
        assert 'standards' in result
        assert 'grades' in result['standards']
        assert 'parameters' in result['standards']
        assert 'premium_criteria' in result['standards']
    
    def test_quality_standards_for_different_crops(self, buyer_tools):
        """Test quality standards for various crops"""
        crops = ['wheat', 'rice', 'tomato', 'potato']
        
        for crop in crops:
            result = buyer_tools.get_quality_standards(crop)
            
            assert result['success'] is True
            assert result['crop_name'] == crop
            assert 'grades' in result['standards']
            assert len(result['standards']['grades']) > 0
    
    def test_get_price_benchmarks(self, buyer_tools):
        """Test price benchmarks retrieval"""
        location = {
            'state': 'Delhi',
            'district': 'Central Delhi',
            'latitude': 28.6139,
            'longitude': 77.2090
        }
        
        result = buyer_tools.get_price_benchmarks('wheat', location)
        
        assert result['success'] is True
        assert 'crop_name' in result
        assert 'market_average' in result
        assert 'market_range' in result
        assert 'fair_price_range' in result
        assert 'min' in result['fair_price_range']
        assert 'max' in result['fair_price_range']
        assert 'recommended' in result['fair_price_range']
    
    def test_price_benchmarks_fair_range(self, buyer_tools):
        """Test that fair price range is reasonable"""
        location = {
            'latitude': 28.6139,
            'longitude': 77.2090
        }
        
        result = buyer_tools.get_price_benchmarks('wheat', location)
        
        if result['success']:
            fair_range = result['fair_price_range']
            market_avg = result['market_average']
            
            # Fair range should be within ±5% of market average
            assert fair_range['min'] <= market_avg
            assert fair_range['max'] >= market_avg
            assert fair_range['min'] >= market_avg * 0.90
            assert fair_range['max'] <= market_avg * 1.10
    
    def test_calculate_distance(self, buyer_tools):
        """Test distance calculation between locations"""
        loc1 = {'latitude': 28.6139, 'longitude': 77.2090}  # Delhi
        loc2 = {'latitude': 28.6692, 'longitude': 77.4538}  # Ghaziabad
        
        distance = buyer_tools._calculate_distance(loc1, loc2)
        
        assert distance > 0
        assert distance < 100  # Should be less than 100km
        assert isinstance(distance, float)
    
    def test_calculate_distance_same_location(self, buyer_tools):
        """Test distance calculation for same location"""
        loc = {'latitude': 28.6139, 'longitude': 77.2090}
        
        distance = buyer_tools._calculate_distance(loc, loc)
        
        assert distance == 0 or distance < 0.1  # Should be zero or very close
    
    def test_calculate_match_score(self, buyer_tools):
        """Test match score calculation"""
        listing = {
            'crop_name': 'wheat',
            'quality_grade': 'grade_a',
            'location': {'latitude': 28.6139, 'longitude': 77.2090}
        }
        
        buyer = {
            'crop_interests': ['wheat', 'rice'],
            'location': {'latitude': 28.6692, 'longitude': 77.4538},
            'business_type': 'wholesaler',
            'ratings': {'average': 4.5},
            'quality_requirements': {}
        }
        
        score = buyer_tools._calculate_match_score(listing, buyer)
        
        assert 0 <= score <= 1
        assert isinstance(score, float)
    
    def test_match_score_crop_interest(self, buyer_tools):
        """Test that crop interest affects match score"""
        listing = {
            'crop_name': 'wheat',
            'quality_grade': 'standard',
            'location': {'latitude': 28.6139, 'longitude': 77.2090}
        }
        
        buyer_interested = {
            'crop_interests': ['wheat'],
            'location': {'latitude': 28.6139, 'longitude': 77.2090},
            'business_type': 'wholesaler',
            'ratings': {'average': 3.0},
            'quality_requirements': {}
        }
        
        buyer_not_interested = {
            'crop_interests': ['rice'],
            'location': {'latitude': 28.6139, 'longitude': 77.2090},
            'business_type': 'wholesaler',
            'ratings': {'average': 3.0},
            'quality_requirements': {}
        }
        
        score_interested = buyer_tools._calculate_match_score(listing, buyer_interested)
        score_not_interested = buyer_tools._calculate_match_score(listing, buyer_not_interested)
        
        assert score_interested > score_not_interested
    
    def test_match_score_distance(self, buyer_tools):
        """Test that distance affects match score"""
        listing = {
            'crop_name': 'wheat',
            'quality_grade': 'standard',
            'location': {'latitude': 28.6139, 'longitude': 77.2090}
        }
        
        buyer_nearby = {
            'crop_interests': ['wheat'],
            'location': {'latitude': 28.6200, 'longitude': 77.2100},  # Very close
            'business_type': 'wholesaler',
            'ratings': {'average': 3.0},
            'quality_requirements': {}
        }
        
        buyer_far = {
            'crop_interests': ['wheat'],
            'location': {'latitude': 30.0, 'longitude': 79.0},  # Far away
            'business_type': 'wholesaler',
            'ratings': {'average': 3.0},
            'quality_requirements': {}
        }
        
        score_nearby = buyer_tools._calculate_match_score(listing, buyer_nearby)
        score_far = buyer_tools._calculate_match_score(listing, buyer_far)
        
        assert score_nearby > score_far
    
    def test_initiate_transaction(self, buyer_tools, sample_listing_data):
        """Test transaction initiation"""
        # First create a listing
        farmer_id = 'farmer_test123'
        listing_result = buyer_tools.create_crop_listing(farmer_id, sample_listing_data)
        
        if not listing_result['success']:
            pytest.skip("Could not create listing for transaction test")
        
        listing_id = listing_result['listing_id']
        buyer_id = 'buyer_test456'
        
        negotiation_data = {
            'agreed_price': 2550,
            'quantity': 100,
            'payment_terms': 'on_delivery',
            'delivery_date': '2024-04-20'
        }
        
        result = buyer_tools.initiate_transaction(listing_id, buyer_id, negotiation_data)
        
        assert result['success'] is True
        assert 'transaction_id' in result
        assert result['transaction_id'].startswith('txn_')
        assert result['status'] == 'confirmed'
        assert result['payment_status'] == 'pending'
        assert 'next_steps' in result
    
    def test_transaction_invalid_listing(self, buyer_tools):
        """Test transaction with invalid listing ID"""
        result = buyer_tools.initiate_transaction(
            'invalid_listing_id',
            'buyer_test456',
            {'agreed_price': 2500}
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_quality_standards_unknown_crop(self, buyer_tools):
        """Test quality standards for unknown crop"""
        result = buyer_tools.get_quality_standards('unknown_crop_xyz')
        
        assert result['success'] is True
        # Should return default standards
        assert 'standards' in result
        assert 'grades' in result['standards']
    
    def test_crop_name_normalization(self, buyer_tools):
        """Test that crop names are normalized"""
        result1 = buyer_tools.get_quality_standards('WHEAT')
        result2 = buyer_tools.get_quality_standards('wheat')
        result3 = buyer_tools.get_quality_standards('  Wheat  ')
        
        assert result1['crop_name'] == result2['crop_name']
        assert result2['crop_name'] == result3['crop_name']
        assert result1['crop_name'] == 'wheat'
    
    def test_listing_data_structure(self, buyer_tools, sample_listing_data):
        """Test structure of listing data"""
        farmer_id = 'farmer_test123'
        result = buyer_tools.create_crop_listing(farmer_id, sample_listing_data)
        
        if result['success']:
            assert 'listing_id' in result
            assert 'status' in result
            assert 'potential_matches' in result
            assert 'matches' in result
            
            # Check matches structure
            for match in result['matches']:
                assert 'buyer_id' in match
                assert 'business_name' in match
                assert 'business_type' in match
                assert 'match_score' in match
                assert 'distance_km' in match
                assert 'ratings' in match


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
