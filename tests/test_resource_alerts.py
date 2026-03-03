"""
RISE Resource Alert System Tests
Unit tests for unused equipment monitoring and alert generation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.resource_alert_tools import ResourceAlertTools


class TestResourceAlertTools(unittest.TestCase):
    """Test cases for ResourceAlertTools"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_dynamodb = Mock()
        self.mock_sns = Mock()
        self.mock_eventbridge = Mock()
        
        with patch('boto3.resource'), patch('boto3.client'):
            self.alert_tools = ResourceAlertTools(region='us-east-1')
            self.alert_tools.dynamodb = self.mock_dynamodb
            self.alert_tools.sns = self.mock_sns
            self.alert_tools.eventbridge = self.mock_eventbridge
            
            # Mock tables
            self.alert_tools.resource_table = Mock()
            self.alert_tools.booking_table = Mock()
            self.alert_tools.user_table = Mock()
    
    def test_find_unused_resources_success(self):
        """Test finding unused resources successfully"""
        # Mock resource data
        current_time = int(datetime.now().timestamp())
        old_time = current_time - (40 * 24 * 60 * 60)  # 40 days ago
        
        mock_resources = [
            {
                'resource_id': 'res_12345',
                'owner_user_id': 'farmer_001',
                'resource_type': 'tractor',
                'equipment_details': {
                    'name': 'John Deere Tractor',
                    'daily_rate': Decimal('3000')
                },
                'location': {
                    'state': 'Punjab',
                    'district': 'Ludhiana'
                },
                'last_used_timestamp': old_time,
                'created_timestamp': old_time - (10 * 24 * 60 * 60)
            }
        ]
        
        self.alert_tools.resource_table.scan.return_value = {
            'Items': mock_resources
        }
        
        # Mock no recent bookings
        self.alert_tools.booking_table.scan.return_value = {
            'Items': []
        }
        
        # Test
        result = self.alert_tools.find_unused_resources(days_threshold=30)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 1)
        self.assertEqual(len(result['unused_resources']), 1)
        self.assertEqual(result['unused_resources'][0]['resource_id'], 'res_12345')
        self.assertGreaterEqual(result['unused_resources'][0]['days_unused'], 30)
    
    def test_find_unused_resources_excludes_new_equipment(self):
        """Test that newly created equipment is excluded"""
        current_time = int(datetime.now().timestamp())
        recent_time = current_time - (5 * 24 * 60 * 60)  # 5 days ago
        
        mock_resources = [
            {
                'resource_id': 'res_new',
                'owner_user_id': 'farmer_002',
                'resource_type': 'pump',
                'equipment_details': {
                    'name': 'Water Pump',
                    'daily_rate': Decimal('500')
                },
                'location': {
                    'state': 'Punjab',
                    'district': 'Ludhiana'
                },
                'last_used_timestamp': 0,
                'created_timestamp': recent_time  # Created recently
            }
        ]
        
        self.alert_tools.resource_table.scan.return_value = {
            'Items': mock_resources
        }
        
        # Test
        result = self.alert_tools.find_unused_resources(days_threshold=30)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 0)  # Should be excluded
    
    def test_calculate_potential_income_tractor(self):
        """Test income calculation for tractor"""
        resource = {
            'daily_rate': 3000,
            'equipment_type': 'tractor',
            'days_unused': 30
        }
        
        result = self.alert_tools.calculate_potential_income(resource)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['daily_rate'], 3000)
        self.assertEqual(result['utilization_rate'], 0.6)  # 60% for tractor
        self.assertEqual(result['estimated_monthly_income'], 54000.0)  # 3000 * 30 * 0.6
        self.assertEqual(result['estimated_yearly_income'], 648000.0)  # 54000 * 12
        self.assertEqual(result['opportunity_cost'], 54000.0)  # 3000 * 30 * 0.6
    
    def test_calculate_potential_income_pump(self):
        """Test income calculation for pump"""
        resource = {
            'daily_rate': 500,
            'equipment_type': 'pump',
            'days_unused': 45
        }
        
        result = self.alert_tools.calculate_potential_income(resource)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['utilization_rate'], 0.4)  # 40% for pump
        self.assertEqual(result['estimated_monthly_income'], 6000.0)  # 500 * 30 * 0.4
        self.assertEqual(result['opportunity_cost'], 9000.0)  # 500 * 45 * 0.4
    
    def test_generate_alert_message_hindi(self):
        """Test alert message generation in Hindi"""
        resource = {
            'equipment_name': 'John Deere Tractor',
            'days_unused': 30
        }
        
        income_data = {
            'estimated_monthly_income': 54000.0,
            'opportunity_cost': 54000.0
        }
        
        message = self.alert_tools._generate_alert_message(resource, income_data, 'hi')
        
        # Assertions
        self.assertIn('John Deere Tractor', message)
        self.assertIn('30', message)
        self.assertIn('54000', message)
        self.assertIn('उपकरण साझाकरण', message)
    
    def test_generate_alert_message_english(self):
        """Test alert message generation in English"""
        resource = {
            'equipment_name': 'Water Pump',
            'days_unused': 45
        }
        
        income_data = {
            'estimated_monthly_income': 6000.0,
            'opportunity_cost': 9000.0
        }
        
        message = self.alert_tools._generate_alert_message(resource, income_data, 'en')
        
        # Assertions
        self.assertIn('Water Pump', message)
        self.assertIn('45', message)
        self.assertIn('6000', message)
        self.assertIn('Equipment Sharing Opportunity', message)
    
    def test_send_unused_resource_alert_success(self):
        """Test sending alert successfully"""
        resource = {
            'resource_id': 'res_12345',
            'owner_user_id': 'farmer_001',
            'equipment_name': 'Tractor',
            'equipment_type': 'tractor',
            'daily_rate': 3000,
            'days_unused': 30
        }
        
        # Mock user data
        self.alert_tools.user_table.get_item.return_value = {
            'Item': {
                'user_id': 'farmer_001',
                'preferences': {
                    'language': 'hi'
                }
            }
        }
        
        result = self.alert_tools.send_unused_resource_alert(resource)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['resource_id'], 'res_12345')
        self.assertEqual(result['owner_user_id'], 'farmer_001')
        self.assertIn('alert_message', result)
        self.assertIn('potential_monthly_income', result)
        self.assertIn('opportunity_cost', result)
    
    def test_send_unused_resource_alert_user_not_found(self):
        """Test alert when user not found"""
        resource = {
            'resource_id': 'res_12345',
            'owner_user_id': 'farmer_999',
            'equipment_name': 'Tractor',
            'equipment_type': 'tractor',
            'daily_rate': 3000,
            'days_unused': 30
        }
        
        # Mock user not found
        self.alert_tools.user_table.get_item.return_value = {}
        
        result = self.alert_tools.send_unused_resource_alert(resource)
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_get_alert_preferences_success(self):
        """Test getting alert preferences successfully"""
        # Mock user data with preferences
        self.alert_tools.user_table.get_item.return_value = {
            'Item': {
                'user_id': 'farmer_001',
                'preferences': {
                    'alert_preferences': {
                        'unused_equipment_alerts': True,
                        'alert_frequency': 'weekly',
                        'alert_threshold_days': 30,
                        'alert_channels': ['voice', 'sms']
                    }
                }
            }
        }
        
        result = self.alert_tools.get_alert_preferences('farmer_001')
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['user_id'], 'farmer_001')
        self.assertTrue(result['alert_preferences']['unused_equipment_alerts'])
        self.assertEqual(result['alert_preferences']['alert_frequency'], 'weekly')
    
    def test_get_alert_preferences_default_values(self):
        """Test getting default preferences when not set"""
        # Mock user data without alert preferences
        self.alert_tools.user_table.get_item.return_value = {
            'Item': {
                'user_id': 'farmer_002',
                'preferences': {}
            }
        }
        
        result = self.alert_tools.get_alert_preferences('farmer_002')
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertTrue(result['alert_preferences']['unused_equipment_alerts'])
        self.assertEqual(result['alert_preferences']['alert_frequency'], 'weekly')
        self.assertEqual(result['alert_preferences']['alert_threshold_days'], 30)
    
    def test_update_alert_preferences_success(self):
        """Test updating alert preferences successfully"""
        # Mock existing user data
        self.alert_tools.user_table.get_item.return_value = {
            'Item': {
                'user_id': 'farmer_001',
                'preferences': {
                    'language': 'hi',
                    'alert_preferences': {
                        'unused_equipment_alerts': True
                    }
                }
            }
        }
        
        new_preferences = {
            'alert_frequency': 'daily',
            'alert_threshold_days': 15,
            'alert_channels': ['voice']
        }
        
        result = self.alert_tools.update_alert_preferences('farmer_001', new_preferences)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['alert_preferences']['alert_frequency'], 'daily')
        self.assertEqual(result['alert_preferences']['alert_threshold_days'], 15)
        self.alert_tools.user_table.put_item.assert_called_once()
    
    def test_send_batch_alerts_success(self):
        """Test sending batch alerts successfully"""
        current_time = int(datetime.now().timestamp())
        old_time = current_time - (40 * 24 * 60 * 60)
        
        # Mock unused resources
        mock_resources = [
            {
                'resource_id': 'res_001',
                'owner_user_id': 'farmer_001',
                'resource_type': 'tractor',
                'equipment_details': {
                    'name': 'Tractor 1',
                    'daily_rate': Decimal('3000')
                },
                'location': {'state': 'Punjab', 'district': 'Ludhiana'},
                'last_used_timestamp': old_time,
                'created_timestamp': old_time - (10 * 24 * 60 * 60)
            },
            {
                'resource_id': 'res_002',
                'owner_user_id': 'farmer_002',
                'resource_type': 'pump',
                'equipment_details': {
                    'name': 'Pump 1',
                    'daily_rate': Decimal('500')
                },
                'location': {'state': 'Punjab', 'district': 'Jalandhar'},
                'last_used_timestamp': old_time,
                'created_timestamp': old_time - (10 * 24 * 60 * 60)
            }
        ]
        
        self.alert_tools.resource_table.scan.return_value = {
            'Items': mock_resources
        }
        
        self.alert_tools.booking_table.scan.return_value = {
            'Items': []
        }
        
        # Mock user data
        self.alert_tools.user_table.get_item.side_effect = [
            {'Item': {'user_id': 'farmer_001', 'preferences': {'language': 'hi'}}},
            {'Item': {'user_id': 'farmer_002', 'preferences': {'language': 'en'}}}
        ]
        
        result = self.alert_tools.send_batch_alerts(days_threshold=30)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['total_unused'], 2)
        self.assertEqual(result['alerts_sent'], 2)
        self.assertEqual(result['alerts_failed'], 0)


class TestResourceAlertIntegration(unittest.TestCase):
    """Integration tests for resource alert system"""
    
    def test_end_to_end_alert_flow(self):
        """Test complete alert flow from detection to notification"""
        # This would be an integration test with actual AWS services
        # For now, we'll skip it in unit tests
        pass


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
