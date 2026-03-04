"""
Tests for Equipment Sharing Marketplace Tools
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.equipment_sharing_tools import EquipmentSharingTools, create_equipment_sharing_tools


class TestEquipmentSharingTools:
    """Test suite for equipment sharing tools"""
    
    @pytest.fixture
    def equipment_tools(self):
        """Create equipment sharing tools instance for testing"""
        return create_equipment_sharing_tools(region='us-east-1')
    
    @pytest.fixture
    def sample_equipment_data(self):
        """Sample equipment listing data"""
        return {
            'name': 'John Deere Tractor',
            'type': 'tractor',
            'model': '5075E',
            'condition': 'excellent',
            'hourly_rate': 500,
            'daily_rate': 3000,
            'year': '2020',
            'capacity': '75 HP',
            'specifications': {
                'engine': '4-cylinder diesel',
                'transmission': 'PowrReverser',
                'pto_hp': '62'
            },
            'location': {
                'state': 'Punjab',
                'district': 'Ludhiana',
                'address': 'Village Khanna',
                'latitude': 30.9010,
                'longitude': 75.8573
            },
            'photos': ['tractor_1.jpg', 'tractor_2.jpg'],
            'pickup_instructions': 'Contact 1 day before pickup. Fuel not included.'
        }
    
    @pytest.fixture
    def sample_booking_details(self):
        """Sample booking details"""
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(days=2)
        
        return {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'notes': 'Need for wheat harvesting'
        }
    
    def test_list_equipment(self, equipment_tools, sample_equipment_data):
        """Test equipment listing"""
        owner_id = 'owner_test123'
        result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        assert result['success'] is True
        assert 'resource_id' in result
        assert result['resource_id'].startswith('res_')
        assert result['status'] == 'listed_successfully'
        assert 'estimated_monthly_income' in result
        assert result['estimated_monthly_income'] > 0
    
    def test_list_equipment_validation(self, equipment_tools):
        """Test equipment listing with missing fields"""
        incomplete_data = {
            'name': 'Test Equipment'
            # Missing required fields
        }
        
        owner_id = 'owner_test123'
        result = equipment_tools.list_equipment(owner_id, incomplete_data)
        
        # Should handle gracefully
        assert 'success' in result
    
    def test_search_equipment(self, equipment_tools):
        """Test equipment search"""
        location = {
            'state': 'Punjab',
            'district': 'Jalandhar',
            'latitude': 31.3260,
            'longitude': 75.5762
        }
        
        result = equipment_tools.search_equipment(location, radius_km=50)
        
        assert result['success'] is True
        assert 'count' in result
        assert 'equipment' in result
        assert isinstance(result['equipment'], list)
        assert 'search_params' in result
    
    def test_search_equipment_with_type_filter(self, equipment_tools):
        """Test equipment search with type filter"""
        location = {
            'latitude': 30.9010,
            'longitude': 75.8573
        }
        
        result = equipment_tools.search_equipment(
            location,
            equipment_type='tractor',
            radius_km=25
        )
        
        assert result['success'] is True
        assert isinstance(result['equipment'], list)
        
        # All results should be tractors
        for equipment in result['equipment']:
            assert equipment['type'] == 'tractor'
    
    def test_search_equipment_with_date_range(self, equipment_tools):
        """Test equipment search with date range filter"""
        location = {
            'latitude': 30.9010,
            'longitude': 75.8573
        }
        
        start_date = datetime.now() + timedelta(days=1)
        end_date = start_date + timedelta(days=3)
        
        date_range = {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        }
        
        result = equipment_tools.search_equipment(
            location,
            date_range=date_range,
            radius_km=25
        )
        
        assert result['success'] is True
        assert isinstance(result['equipment'], list)
    
    def test_search_equipment_radius_filter(self, equipment_tools, sample_equipment_data):
        """Test that radius filter works correctly"""
        # List equipment at a known location
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for radius test")
        
        # Search with small radius (should not find)
        location_far = {
            'latitude': 28.6139,  # Delhi - far from Punjab
            'longitude': 77.2090
        }
        
        result_far = equipment_tools.search_equipment(location_far, radius_km=10)
        
        # Search with large radius from nearby location
        location_near = {
            'latitude': 30.9010,  # Same as equipment location
            'longitude': 75.8573
        }
        
        result_near = equipment_tools.search_equipment(location_near, radius_km=50)
        
        # Nearby search should find more or equal equipment
        assert result_near['count'] >= result_far['count']
    
    def test_book_equipment(self, equipment_tools, sample_equipment_data, sample_booking_details):
        """Test equipment booking"""
        # First list equipment
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for booking test")
        
        resource_id = list_result['resource_id']
        renter_id = 'renter_test456'
        
        result = equipment_tools.book_equipment(renter_id, resource_id, sample_booking_details)
        
        assert result['success'] is True
        assert 'booking_id' in result
        assert result['booking_id'].startswith('book_')
        assert result['status'] == 'confirmed'
        assert result['payment_status'] == 'pending'
        assert 'total_cost' in result
        assert result['total_cost'] > 0
        assert 'insurance_premium' in result
        assert 'pickup_instructions' in result
        assert 'next_steps' in result
    
    def test_book_equipment_invalid_resource(self, equipment_tools, sample_booking_details):
        """Test booking with invalid resource ID"""
        result = equipment_tools.book_equipment(
            'renter_test456',
            'invalid_resource_id',
            sample_booking_details
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_booking_cost_calculation(self, equipment_tools, sample_equipment_data):
        """Test booking cost calculation"""
        # List equipment
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for cost test")
        
        resource_id = list_result['resource_id']
        
        # Book for 2 full days
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(days=2)
        
        booking_details = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        result = equipment_tools.book_equipment('renter_test456', resource_id, booking_details)
        
        if result['success']:
            # Cost should be 2 days * daily_rate
            expected_cost = sample_equipment_data['daily_rate'] * 2
            assert result['total_cost'] == expected_cost
    
    def test_get_equipment_details(self, equipment_tools, sample_equipment_data):
        """Test getting equipment details"""
        # First list equipment
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for details test")
        
        resource_id = list_result['resource_id']
        
        result = equipment_tools.get_equipment_details(resource_id)
        
        assert result['success'] is True
        assert result['resource_id'] == resource_id
        assert 'equipment' in result
        assert 'pricing' in result
        assert 'location' in result
        assert 'availability_status' in result
        assert 'ratings' in result
        assert 'total_bookings' in result
    
    def test_get_equipment_details_invalid_id(self, equipment_tools):
        """Test getting details for invalid equipment ID"""
        result = equipment_tools.get_equipment_details('invalid_resource_id')
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_rate_equipment(self, equipment_tools, sample_equipment_data, sample_booking_details):
        """Test equipment rating"""
        # List equipment and create booking
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for rating test")
        
        resource_id = list_result['resource_id']
        renter_id = 'renter_test456'
        
        booking_result = equipment_tools.book_equipment(renter_id, resource_id, sample_booking_details)
        
        if not booking_result['success']:
            pytest.skip("Could not create booking for rating test")
        
        booking_id = booking_result['booking_id']
        
        # Rate the equipment
        rating_data = {
            'equipment_rating': 4,
            'owner_rating': 5,
            'review': 'Excellent equipment, well-maintained'
        }
        
        result = equipment_tools.rate_equipment(booking_id, rating_data)
        
        assert result['success'] is True
        assert 'new_average_rating' in result
        assert 'total_ratings' in result
        assert result['new_average_rating'] == 4.0
        assert result['total_ratings'] == 1
    
    def test_rate_equipment_invalid_booking(self, equipment_tools):
        """Test rating with invalid booking ID"""
        rating_data = {
            'equipment_rating': 4,
            'review': 'Test review'
        }
        
        result = equipment_tools.rate_equipment('invalid_booking_id', rating_data)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_rating_average_calculation(self, equipment_tools, sample_equipment_data, sample_booking_details):
        """Test that rating average is calculated correctly"""
        # List equipment
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for rating average test")
        
        resource_id = list_result['resource_id']
        
        # Create multiple bookings and rate them
        ratings = [5, 4, 3]
        
        for i, rating_value in enumerate(ratings):
            # Create booking
            booking_result = equipment_tools.book_equipment(
                f'renter_test{i}',
                resource_id,
                sample_booking_details
            )
            
            if booking_result['success']:
                # Rate the booking
                rating_data = {'equipment_rating': rating_value}
                equipment_tools.rate_equipment(booking_result['booking_id'], rating_data)
        
        # Get equipment details to check average
        details = equipment_tools.get_equipment_details(resource_id)
        
        if details['success']:
            # Average should be (5+4+3)/3 = 4.0
            expected_avg = sum(ratings) / len(ratings)
            assert abs(details['ratings']['average'] - expected_avg) < 0.1
    
    def test_send_unused_equipment_alerts(self, equipment_tools):
        """Test sending unused equipment alerts"""
        result = equipment_tools.send_unused_equipment_alerts(days_threshold=30)
        
        assert result['success'] is True
        assert 'alerts_sent' in result
        assert isinstance(result['alerts_sent'], int)
        assert result['alerts_sent'] >= 0
    
    def test_calculate_distance(self, equipment_tools):
        """Test distance calculation"""
        loc1 = {'latitude': 30.9010, 'longitude': 75.8573}  # Ludhiana
        loc2 = {'latitude': 31.3260, 'longitude': 75.5762}  # Jalandhar
        
        distance = equipment_tools._calculate_distance(loc1, loc2)
        
        assert distance > 0
        assert distance < 100  # Should be less than 100km
        assert isinstance(distance, float)
    
    def test_calculate_distance_same_location(self, equipment_tools):
        """Test distance calculation for same location"""
        loc = {'latitude': 30.9010, 'longitude': 75.8573}
        
        distance = equipment_tools._calculate_distance(loc, loc)
        
        assert distance == 0 or distance < 0.1
    
    def test_check_availability(self, equipment_tools, sample_equipment_data):
        """Test availability checking"""
        # List equipment
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for availability test")
        
        resource_id = list_result['resource_id']
        
        # Check availability for future dates
        start_date = datetime.now() + timedelta(days=10)
        end_date = start_date + timedelta(days=2)
        
        date_range = {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        }
        
        is_available = equipment_tools._check_availability(resource_id, date_range)
        
        assert isinstance(is_available, bool)
        assert is_available is True  # Should be available for future dates
    
    def test_calculate_potential_income(self, equipment_tools, sample_equipment_data):
        """Test potential income calculation"""
        # Create a mock resource item
        resource = {
            'equipment_details': {
                'daily_rate': 3000,
                'hourly_rate': 500
            }
        }
        
        potential_income = equipment_tools._calculate_potential_income(resource)
        
        assert potential_income > 0
        # Should be daily_rate * 30 days * 0.5 utilization
        expected = 3000 * 30 * 0.5
        assert potential_income == expected
    
    def test_equipment_types(self, equipment_tools):
        """Test different equipment types"""
        equipment_types = ['tractor', 'pump', 'drone', 'harvester', 'plough', 'sprayer']
        
        for eq_type in equipment_types:
            equipment_data = {
                'name': f'Test {eq_type}',
                'type': eq_type,
                'hourly_rate': 100,
                'daily_rate': 500,
                'location': {
                    'state': 'Punjab',
                    'district': 'Ludhiana',
                    'latitude': 30.9010,
                    'longitude': 75.8573
                }
            }
            
            result = equipment_tools.list_equipment('owner_test', equipment_data)
            
            assert result['success'] is True
            assert 'resource_id' in result
    
    def test_search_results_sorted_by_distance(self, equipment_tools):
        """Test that search results are sorted by distance"""
        location = {
            'latitude': 30.9010,
            'longitude': 75.8573
        }
        
        result = equipment_tools.search_equipment(location, radius_km=100)
        
        if result['success'] and len(result['equipment']) > 1:
            distances = [eq['distance_km'] for eq in result['equipment']]
            
            # Check if sorted in ascending order
            assert distances == sorted(distances)
    
    def test_insurance_premium_calculation(self, equipment_tools, sample_equipment_data, sample_booking_details):
        """Test insurance premium calculation"""
        # List equipment and book
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for insurance test")
        
        resource_id = list_result['resource_id']
        
        booking_result = equipment_tools.book_equipment(
            'renter_test456',
            resource_id,
            sample_booking_details
        )
        
        if booking_result['success']:
            # Insurance should be 5% of total cost
            expected_premium = booking_result['total_cost'] * 0.05
            assert abs(booking_result['insurance_premium'] - expected_premium) < 0.01


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


    def test_process_payment(self, equipment_tools, sample_equipment_data, sample_booking_details):
        """Test payment processing"""
        # Create booking first
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for payment test")
        
        resource_id = list_result['resource_id']
        booking_result = equipment_tools.book_equipment('renter_test456', resource_id, sample_booking_details)
        
        if not booking_result['success']:
            pytest.skip("Could not create booking for payment test")
        
        booking_id = booking_result['booking_id']
        
        # Process payment
        payment_details = {
            'amount': booking_result['total_cost'],
            'payment_method': 'upi',
            'reference': 'UPI123456789'
        }
        
        result = equipment_tools.process_payment(booking_id, payment_details)
        
        assert result['success'] is True
        assert 'transaction_id' in result
        assert result['transaction_id'].startswith('TXN_')
        assert result['payment_status'] == 'completed'
        assert result['amount_paid'] == payment_details['amount']
    
    def test_process_payment_amount_mismatch(self, equipment_tools, sample_equipment_data, sample_booking_details):
        """Test payment with incorrect amount"""
        # Create booking
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for payment mismatch test")
        
        resource_id = list_result['resource_id']
        booking_result = equipment_tools.book_equipment('renter_test456', resource_id, sample_booking_details)
        
        if not booking_result['success']:
            pytest.skip("Could not create booking for payment mismatch test")
        
        booking_id = booking_result['booking_id']
        
        # Try to pay wrong amount
        payment_details = {
            'amount': booking_result['total_cost'] - 100,  # Wrong amount
            'payment_method': 'upi'
        }
        
        result = equipment_tools.process_payment(booking_id, payment_details)
        
        assert result['success'] is False
        assert 'mismatch' in result['error'].lower()
    
    def test_update_usage_tracking(self, equipment_tools, sample_equipment_data, sample_booking_details):
        """Test usage tracking update"""
        # Create and pay for booking
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for usage tracking test")
        
        resource_id = list_result['resource_id']
        booking_result = equipment_tools.book_equipment('renter_test456', resource_id, sample_booking_details)
        
        if not booking_result['success']:
            pytest.skip("Could not create booking for usage tracking test")
        
        booking_id = booking_result['booking_id']
        
        # Update start reading
        usage_data = {
            'start_reading': 1000,
            'actual_start_time': datetime.now().isoformat()
        }
        
        result = equipment_tools.update_usage_tracking(booking_id, usage_data)
        
        assert result['success'] is True
        assert result['usage_tracking']['start_reading'] == 1000
        
        # Update end reading
        usage_data = {
            'end_reading': 1050,
            'actual_end_time': (datetime.now() + timedelta(hours=5)).isoformat()
        }
        
        result = equipment_tools.update_usage_tracking(booking_id, usage_data)
        
        assert result['success'] is True
        assert result['usage_tracking']['end_reading'] == 1050
        assert result['usage_tracking']['hours_used'] == 50
    
    def test_get_booking_details(self, equipment_tools, sample_equipment_data, sample_booking_details):
        """Test getting booking details"""
        # Create booking
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for booking details test")
        
        resource_id = list_result['resource_id']
        booking_result = equipment_tools.book_equipment('renter_test456', resource_id, sample_booking_details)
        
        if not booking_result['success']:
            pytest.skip("Could not create booking for booking details test")
        
        booking_id = booking_result['booking_id']
        
        # Get booking details
        result = equipment_tools.get_booking_details(booking_id)
        
        assert result['success'] is True
        assert result['booking_id'] == booking_id
        assert 'booking' in result
        assert 'equipment' in result
        assert result['booking']['booking_id'] == booking_id
        assert result['equipment']['name'] == sample_equipment_data['name']
    
    def test_get_user_bookings(self, equipment_tools, sample_equipment_data, sample_booking_details):
        """Test getting user bookings"""
        # Create multiple bookings
        owner_id = 'owner_test123'
        renter_id = 'renter_test456'
        
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for user bookings test")
        
        resource_id = list_result['resource_id']
        
        # Create 2 bookings
        for i in range(2):
            start_time = datetime.now() + timedelta(days=i*5)
            end_time = start_time + timedelta(days=1)
            
            booking_details = {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
            
            equipment_tools.book_equipment(renter_id, resource_id, booking_details)
        
        # Get renter's bookings
        result = equipment_tools.get_user_bookings(renter_id, 'renter')
        
        assert result['success'] is True
        assert result['count'] >= 2
        assert isinstance(result['bookings'], list)
        
        # Get owner's bookings
        owner_result = equipment_tools.get_user_bookings(owner_id, 'owner')
        
        assert owner_result['success'] is True
        assert owner_result['count'] >= 2
    
    def test_cancel_booking(self, equipment_tools, sample_equipment_data, sample_booking_details):
        """Test booking cancellation"""
        # Create booking
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for cancellation test")
        
        resource_id = list_result['resource_id']
        
        # Create booking far in future for full refund
        start_time = datetime.now() + timedelta(days=10)
        end_time = start_time + timedelta(days=1)
        
        booking_details = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        booking_result = equipment_tools.book_equipment('renter_test456', resource_id, booking_details)
        
        if not booking_result['success']:
            pytest.skip("Could not create booking for cancellation test")
        
        booking_id = booking_result['booking_id']
        
        # Cancel booking
        result = equipment_tools.cancel_booking(booking_id, 'Plans changed')
        
        assert result['success'] is True
        assert result['status'] == 'cancelled'
        assert 'refund_amount' in result
    
    def test_cancel_booking_with_payment(self, equipment_tools, sample_equipment_data, sample_booking_details):
        """Test cancellation with refund calculation"""
        # Create and pay for booking
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for cancellation with payment test")
        
        resource_id = list_result['resource_id']
        
        # Create booking 48 hours in future
        start_time = datetime.now() + timedelta(hours=48)
        end_time = start_time + timedelta(days=1)
        
        booking_details = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        booking_result = equipment_tools.book_equipment('renter_test456', resource_id, booking_details)
        
        if not booking_result['success']:
            pytest.skip("Could not create booking for cancellation with payment test")
        
        booking_id = booking_result['booking_id']
        
        # Process payment
        payment_details = {
            'amount': booking_result['total_cost'],
            'payment_method': 'upi'
        }
        
        payment_result = equipment_tools.process_payment(booking_id, payment_details)
        
        if not payment_result['success']:
            pytest.skip("Could not process payment for cancellation test")
        
        # Cancel booking (should get full refund as it's 48 hours before)
        cancel_result = equipment_tools.cancel_booking(booking_id, 'Emergency')
        
        assert cancel_result['success'] is True
        assert cancel_result['refund_amount'] == booking_result['total_cost']
    
    def test_cancel_completed_booking(self, equipment_tools, sample_equipment_data, sample_booking_details):
        """Test that completed bookings cannot be cancelled"""
        # Create booking
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for completed booking test")
        
        resource_id = list_result['resource_id']
        booking_result = equipment_tools.book_equipment('renter_test456', resource_id, sample_booking_details)
        
        if not booking_result['success']:
            pytest.skip("Could not create booking for completed booking test")
        
        booking_id = booking_result['booking_id']
        
        # Mark as completed by updating usage
        usage_data = {
            'start_reading': 1000,
            'end_reading': 1050
        }
        
        equipment_tools.update_usage_tracking(booking_id, usage_data)
        
        # Try to cancel
        result = equipment_tools.cancel_booking(booking_id, 'Test')
        
        assert result['success'] is False
        assert 'cannot cancel' in result['error'].lower()
    
    def test_booking_with_transport_cost(self, equipment_tools, sample_equipment_data):
        """Test booking with transport cost included"""
        # Create booking with transport cost
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for transport cost test")
        
        resource_id = list_result['resource_id']
        
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(days=1)
        
        booking_details = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'transport_cost': 500
        }
        
        result = equipment_tools.book_equipment('renter_test456', resource_id, booking_details)
        
        if result['success']:
            assert 'transport_cost' in result
            assert result['transport_cost'] == 500
            assert result['final_amount'] == result['total_cost'] + result['insurance_premium'] + 500
    
    def test_insurance_verification(self, equipment_tools, sample_equipment_data, sample_booking_details):
        """Test insurance verification in booking"""
        # Create booking
        owner_id = 'owner_test123'
        list_result = equipment_tools.list_equipment(owner_id, sample_equipment_data)
        
        if not list_result['success']:
            pytest.skip("Could not list equipment for insurance test")
        
        resource_id = list_result['resource_id']
        booking_result = equipment_tools.book_equipment('renter_test456', resource_id, sample_booking_details)
        
        if not booking_result['success']:
            pytest.skip("Could not create booking for insurance test")
        
        booking_id = booking_result['booking_id']
        
        # Get booking details to check insurance
        details = equipment_tools.get_booking_details(booking_id)
        
        if details['success']:
            insurance = details['booking']['insurance_details']
            
            assert 'policy_number' in insurance
            assert insurance['policy_number'].startswith('INS_')
            assert insurance['verified'] is True
            assert float(insurance['coverage_amount']) == booking_result['total_cost'] * 2
            assert float(insurance['premium']) == booking_result['insurance_premium']
