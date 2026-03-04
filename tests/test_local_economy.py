"""
Unit tests for RISE Local Economy Tracking
"""

import unittest
import json
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.local_economy_tools import LocalEconomyTools
from tools.local_economy_lambda import lambda_handler


class TestLocalEconomyTools(unittest.TestCase):
    """Test cases for LocalEconomyTools"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_dynamodb = Mock()
        self.mock_resource_table = Mock()
        self.mock_booking_table = Mock()
        self.mock_groups_table = Mock()
        self.mock_user_profiles_table = Mock()
        
        with patch('boto3.resource') as mock_resource:
            mock_resource.return_value = self.mock_dynamodb
            self.mock_dynamodb.Table.side_effect = lambda name: {
                'RISE-ResourceSharing': self.mock_resource_table,
                'RISE-ResourceBookings': self.mock_booking_table,
                'RISE-BuyingGroups': self.mock_groups_table,
                'RISE-UserProfiles': self.mock_user_profiles_table
            }.get(name)
            
            self.tools = LocalEconomyTools(region='us-east-1')
    
    def test_calculate_economic_impact_success(self):
        """Test successful economic impact calculation"""
        # Mock data
        location = {'state': 'Punjab', 'district': 'Ludhiana'}
        time_period = {
            'start': '2024-01-01T00:00:00',
            'end': '2024-01-31T23:59:59'
        }
        
        # Mock resource table response
        self.mock_resource_table.scan.return_value = {
            'Items': [
                {
                    'resource_id': 'res_123',
                    'resource_type': 'tractor',
                    'location': {'state': 'Punjab', 'district': 'Ludhiana'},
                    'last_used_timestamp': int(datetime.now().timestamp())
                }
            ]
        }
        
        # Mock booking table response
        self.mock_booking_table.scan.return_value = {
            'Items': [
                {
                    'booking_id': 'book_123',
                    'resource_id': 'res_123',
                    'owner_user_id': 'farmer_1',
                    'renter_user_id': 'farmer_2',
                    'total_cost': Decimal('3000'),
                    'payment_status': 'completed',
                    'created_timestamp': int(datetime.now().timestamp())
                }
            ]
        }
        
        # Mock groups table response
        self.mock_groups_table.scan.return_value = {
            'Items': [
                {
                    'group_id': 'grp_123',
                    'location_area': 'Ludhiana_Punjab',
                    'bulk_pricing_achieved': {'wheat_seeds': Decimal('20')},
                    'total_quantity_needed': {'wheat_seeds': Decimal('500')}
                }
            ]
        }
        
        result = self.tools.calculate_economic_impact(location, time_period)
        
        self.assertTrue(result['success'])
        self.assertIn('metrics', result)
        self.assertIn('summary', result)
        self.assertIn('equipment_utilization_rate', result['metrics'])
        self.assertIn('cost_savings', result['metrics'])
        self.assertIn('additional_income', result['metrics'])
    
    def test_calculate_economic_impact_no_time_period(self):
        """Test economic impact calculation with default time period"""
        location = {'state': 'Punjab', 'district': 'Ludhiana'}
        
        # Mock empty responses
        self.mock_resource_table.scan.return_value = {'Items': []}
        self.mock_booking_table.scan.return_value = {'Items': []}
        self.mock_groups_table.scan.return_value = {'Items': []}
        
        result = self.tools.calculate_economic_impact(location)
        
        self.assertTrue(result['success'])
        self.assertIn('time_period', result)
    
    def test_track_cost_savings_success(self):
        """Test successful cost savings tracking"""
        user_id = 'farmer_123'
        time_period = {
            'start': '2024-01-01T00:00:00',
            'end': '2024-01-31T23:59:59'
        }
        
        # Mock booking table response (as renter)
        self.mock_booking_table.scan.return_value = {
            'Items': [
                {
                    'booking_id': 'book_123',
                    'renter_user_id': user_id,
                    'total_cost': Decimal('3000'),
                    'created_timestamp': int(datetime.now().timestamp())
                }
            ]
        }
        
        # Mock groups table response
        self.mock_groups_table.scan.return_value = {
            'Items': [
                {
                    'group_id': 'grp_123',
                    'members': [user_id],
                    'member_requirements': {
                        user_id: {'wheat_seeds': 100}
                    },
                    'bulk_pricing_achieved': {'wheat_seeds': Decimal('20')}
                }
            ]
        }
        
        result = self.tools.track_cost_savings(user_id, time_period)
        
        self.assertTrue(result['success'])
        self.assertIn('savings_breakdown', result)
        self.assertIn('equipment_rental_savings', result['savings_breakdown'])
        self.assertIn('cooperative_buying_savings', result['savings_breakdown'])
    
    def test_track_additional_income_success(self):
        """Test successful additional income tracking"""
        user_id = 'farmer_123'
        time_period = {
            'start': '2024-01-01T00:00:00',
            'end': '2024-01-31T23:59:59'
        }
        
        # Mock booking table response (as owner)
        self.mock_booking_table.scan.return_value = {
            'Items': [
                {
                    'booking_id': 'book_123',
                    'owner_user_id': user_id,
                    'resource_id': 'res_123',
                    'total_cost': Decimal('3000'),
                    'payment_status': 'completed',
                    'created_timestamp': int(datetime.now().timestamp())
                },
                {
                    'booking_id': 'book_124',
                    'owner_user_id': user_id,
                    'resource_id': 'res_123',
                    'total_cost': Decimal('2500'),
                    'payment_status': 'pending',
                    'created_timestamp': int(datetime.now().timestamp())
                }
            ]
        }
        
        # Mock resource table response
        self.mock_resource_table.get_item.return_value = {
            'Item': {
                'resource_id': 'res_123',
                'resource_type': 'tractor'
            }
        }
        
        result = self.tools.track_additional_income(user_id, time_period)
        
        self.assertTrue(result['success'])
        self.assertIn('income_breakdown', result)
        self.assertIn('projections', result)
        self.assertEqual(result['income_breakdown']['total_bookings'], 2)
        self.assertEqual(result['income_breakdown']['completed_bookings'], 1)
    
    def test_calculate_resource_utilization_success(self):
        """Test successful resource utilization calculation"""
        location = {'state': 'Punjab', 'district': 'Ludhiana'}
        
        # Mock resource table response
        self.mock_resource_table.scan.return_value = {
            'Items': [
                {
                    'resource_id': 'res_123',
                    'resource_type': 'tractor',
                    'location': {'state': 'Punjab', 'district': 'Ludhiana'},
                    'last_used_timestamp': int(datetime.now().timestamp())
                },
                {
                    'resource_id': 'res_124',
                    'resource_type': 'pump',
                    'location': {'state': 'Punjab', 'district': 'Ludhiana'},
                    'last_used_timestamp': 0
                }
            ]
        }
        
        result = self.tools.calculate_resource_utilization(location)
        
        self.assertTrue(result['success'])
        self.assertIn('utilization_metrics', result)
        self.assertIn('overall_rate', result['utilization_metrics'])
        self.assertIn('by_type', result['utilization_metrics'])
    
    def test_generate_sustainability_metrics_success(self):
        """Test successful sustainability metrics generation"""
        location = {'state': 'Punjab', 'district': 'Ludhiana'}
        
        # Mock resource table response
        self.mock_resource_table.scan.return_value = {
            'Items': [
                {
                    'resource_id': 'res_123',
                    'resource_type': 'tractor',
                    'location': {'state': 'Punjab', 'district': 'Ludhiana'},
                    'last_used_timestamp': int(datetime.now().timestamp())
                }
            ]
        }
        
        result = self.tools.generate_sustainability_metrics(location)
        
        self.assertTrue(result['success'])
        self.assertIn('sustainability_metrics', result)
        metrics = result['sustainability_metrics']
        self.assertIn('equipment_purchases_avoided', metrics)
        self.assertIn('estimated_co2_savings_kg', metrics)
        self.assertIn('resource_efficiency_score', metrics)
        self.assertIn('sustainability_level', metrics)
    
    def test_get_community_network_data_success(self):
        """Test successful community network data retrieval"""
        location = {'state': 'Punjab', 'district': 'Ludhiana'}
        
        # Mock user profiles response
        self.mock_user_profiles_table.scan.return_value = {
            'Items': [
                {
                    'user_id': 'farmer_1',
                    'name': 'Farmer One',
                    'location': {'state': 'Punjab', 'district': 'Ludhiana'}
                },
                {
                    'user_id': 'farmer_2',
                    'name': 'Farmer Two',
                    'location': {'state': 'Punjab', 'district': 'Ludhiana'}
                }
            ]
        }
        
        # Mock booking table response
        self.mock_booking_table.scan.return_value = {
            'Items': [
                {
                    'owner_user_id': 'farmer_1',
                    'renter_user_id': 'farmer_2',
                    'total_cost': Decimal('3000')
                }
            ]
        }
        
        # Mock groups table response
        self.mock_groups_table.scan.return_value = {
            'Items': [
                {
                    'group_id': 'grp_123',
                    'organizer_user_id': 'farmer_1',
                    'members': ['farmer_1', 'farmer_2']
                }
            ]
        }
        
        result = self.tools.get_community_network_data(location)
        
        self.assertTrue(result['success'])
        self.assertIn('network', result)
        self.assertIn('statistics', result)
        self.assertIn('nodes', result['network'])
        self.assertIn('connections', result['network'])


class TestLocalEconomyLambda(unittest.TestCase):
    """Test cases for Local Economy Lambda handler"""
    
    @patch('tools.local_economy_lambda.economy_tools')
    def test_calculate_impact_success(self, mock_tools):
        """Test successful economic impact calculation via Lambda"""
        mock_tools.calculate_economic_impact.return_value = {
            'success': True,
            'metrics': {
                'total_economic_benefit': 50000
            }
        }
        
        event = {
            'action': 'calculate_impact',
            'location': {
                'state': 'Punjab',
                'district': 'Ludhiana'
            }
        }
        
        response = lambda_handler(event, None)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertTrue(body['success'])
    
    @patch('tools.local_economy_lambda.economy_tools')
    def test_calculate_impact_missing_location(self, mock_tools):
        """Test economic impact calculation with missing location"""
        event = {
            'action': 'calculate_impact'
        }
        
        response = lambda_handler(event, None)
        
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertFalse(body['success'])
    
    @patch('tools.local_economy_lambda.economy_tools')
    def test_track_savings_success(self, mock_tools):
        """Test successful cost savings tracking via Lambda"""
        mock_tools.track_cost_savings.return_value = {
            'success': True,
            'savings_breakdown': {
                'total_savings': 10000
            }
        }
        
        event = {
            'action': 'track_savings',
            'user_id': 'farmer_123'
        }
        
        response = lambda_handler(event, None)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertTrue(body['success'])
    
    @patch('tools.local_economy_lambda.economy_tools')
    def test_track_income_success(self, mock_tools):
        """Test successful income tracking via Lambda"""
        mock_tools.track_additional_income.return_value = {
            'success': True,
            'income_breakdown': {
                'total_income': 15000
            }
        }
        
        event = {
            'action': 'track_income',
            'user_id': 'farmer_123'
        }
        
        response = lambda_handler(event, None)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertTrue(body['success'])
    
    @patch('tools.local_economy_lambda.economy_tools')
    def test_invalid_action(self, mock_tools):
        """Test Lambda handler with invalid action"""
        event = {
            'action': 'invalid_action'
        }
        
        response = lambda_handler(event, None)
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertFalse(body['success'])
        self.assertIn('Invalid action', body['error'])


class TestEconomicCalculations(unittest.TestCase):
    """Test cases for economic calculation methods"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('boto3.resource'):
            self.tools = LocalEconomyTools(region='us-east-1')
    
    def test_get_engagement_level(self):
        """Test engagement level classification"""
        self.assertEqual(self.tools._get_engagement_level(85), 'Excellent')
        self.assertEqual(self.tools._get_engagement_level(65), 'Good')
        self.assertEqual(self.tools._get_engagement_level(45), 'Moderate')
        self.assertEqual(self.tools._get_engagement_level(25), 'Low')
        self.assertEqual(self.tools._get_engagement_level(10), 'Very Low')
    
    def test_get_sustainability_level(self):
        """Test sustainability level classification"""
        self.assertEqual(self.tools._get_sustainability_level(85), 'Highly Sustainable')
        self.assertEqual(self.tools._get_sustainability_level(65), 'Sustainable')
        self.assertEqual(self.tools._get_sustainability_level(45), 'Moderately Sustainable')
        self.assertEqual(self.tools._get_sustainability_level(25), 'Needs Improvement')


if __name__ == '__main__':
    unittest.main()
