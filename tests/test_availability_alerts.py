"""
Unit tests for RISE Resource Availability Alert System
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.availability_alert_tools import AvailabilityAlertTools, create_availability_alert_tools


class TestAvailabilityAlertTools(unittest.TestCase):
    """Test cases for availability alert tools"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tools = create_availability_alert_tools()
        
        # Mock AWS clients
        self.tools.dynamodb = Mock()
        self.tools.sns = Mock()
        self.tools.bedrock = Mock()
        self.tools.eventbridge = Mock()
        
        # Mock DynamoDB tables
        self.tools.resource_table = Mock()
        self.tools.booking_table = Mock()
        self.tools.groups_table = Mock()
        self.tools.user_table = Mock()
    
    def test_send_equipment_availability_alert_success(self):
        """Test successful equipment availability alert"""
        # Mock resource data
        self.tools.resource_table.get_item.return_value = {
            'Item': {
                'resource_id': 'res_test123',
                'owner_user_id': 'owner_001',
                'resource_type': 'tractor',
                'equipment_details': {
                    'name': 'John Deere 5050D',
                    'daily_rate': Decimal('2000')
                },
                'location': {
                    'district': 'Test District',
                    'state': 'Test State',
                    'latitude': Decimal('28.6139'),
                    'longitude': Decimal('77.2090')
                }
            }
        }
        
        # Mock nearby farmers
        self.tools.user_table.scan.return_value = {
            'Items': [
                {
                    'user_id': 'farmer_001',
                    'location': {
                        'latitude': Decimal('28.6200'),
                        'longitude': Decimal('77.2100')
                    },
                    'preferences': {
                        'language': 'hi',
                        'alert_preferences': {
                            'equipment_alerts': {
                                'enabled': True,
                                'equipment_types': ['tractor']
                            }
                        }
                    }
                }
            ]
        }
        
        result = self.tools.send_equipment_availability_alert('res_test123', 25)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['resource_id'], 'res_test123')
        self.assertGreaterEqual(result['alerts_sent'], 0)
    
    def test_send_bulk_buying_opportunity_alert_success(self):
        """Test successful bulk buying opportunity alert"""
        # Mock group data
        self.tools.groups_table.get_item.return_value = {
            'Item': {
                'group_id': 'grp_test123',
                'group_name': 'Test Buying Group',
                'members': ['organizer_001'],
                'target_products': ['seeds', 'fertilizers'],
                'location': {
                    'district': 'Test District',
                    'state': 'Test State',
                    'latitude': Decimal('28.6139'),
                    'longitude': Decimal('77.2090')
                },
                'bulk_pricing_achieved': {
                    'seeds': Decimal('20'),
                    'fertilizers': Decimal('25')
                }
            }
        }
        
        # Mock nearby farmers
        self.tools.user_table.scan.return_value = {
            'Items': [
                {
                    'user_id': 'farmer_002',
                    'location': {
                        'latitude': Decimal('28.6200'),
                        'longitude': Decimal('77.2100')
                    },
                    'preferences': {
                        'language': 'hi',
                        'alert_preferences': {
                            'buying_group_alerts': {
                                'enabled': True,
                                'product_interests': ['seeds']
                            }
                        }
                    }
                }
            ]
        }
        
        result = self.tools.send_bulk_buying_opportunity_alert('grp_test123', 25)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['group_id'], 'grp_test123')
        self.assertGreaterEqual(result['alerts_sent'], 0)
    
    def test_predict_seasonal_demand_success(self):
        """Test successful seasonal demand prediction"""
        # Mock user data
        self.tools.user_table.get_item.return_value = {
            'Item': {
                'user_id': 'user_test123',
                'location': {
                    'district': 'Test District',
                    'state': 'Test State'
                },
                'farm_details': {
                    'land_size': 5,
                    'crops': ['rice', 'wheat']
                }
            }
        }
        
        # Mock Bedrock response
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = b'''{
            "content": [{
                "text": "Equipment needs:\\n- Tractor for plowing\\n- Harvester for harvest season\\n\\nPeak periods:\\n- March-April for planting\\n- October-November for harvesting"
            }]
        }'''
        self.tools.bedrock.invoke_model.return_value = mock_response
        
        crop_calendar = {
            'rice': {
                'planting_date': '2024-03-15',
                'harvest_date': '2024-10-15',
                'area_acres': 3
            }
        }
        
        result = self.tools.predict_seasonal_demand('user_test123', crop_calendar)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['user_id'], 'user_test123')
        self.assertIn('predictions', result)
        self.assertIn('prediction_text', result)
    
    def test_create_advance_booking_success(self):
        """Test successful advance booking creation"""
        # Mock available equipment search
        self.tools.resource_table.scan.return_value = {
            'Items': [
                {
                    'resource_id': 'res_available',
                    'resource_type': 'tractor',
                    'availability_status': 'available',
                    'equipment_details': {
                        'name': 'Test Tractor',
                        'daily_rate': Decimal('2000')
                    },
                    'location': {
                        'latitude': Decimal('28.6139'),
                        'longitude': Decimal('77.2090')
                    },
                    'ratings': {
                        'average': Decimal('4.5')
                    }
                }
            ]
        }
        
        booking_data = {
            'equipment_type': 'tractor',
            'booking_date': (datetime.now() + timedelta(days=30)).isoformat(),
            'duration_days': 2,
            'location': {
                'district': 'Test District',
                'state': 'Test State',
                'latitude': 28.6139,
                'longitude': 77.2090
            }
        }
        
        result = self.tools.create_advance_booking('user_test123', booking_data)
        
        self.assertTrue(result['success'])
        self.assertIn('advance_booking_id', result)
        self.assertIn('estimated_cost', result)
    
    def test_generate_optimal_sharing_schedule_success(self):
        """Test successful optimal schedule generation"""
        # Mock resource data
        self.tools.resource_table.get_item.return_value = {
            'Item': {
                'resource_id': 'res_test123',
                'resource_type': 'tractor',
                'equipment_details': {
                    'name': 'Test Tractor',
                    'daily_rate': Decimal('2000')
                },
                'location': {
                    'district': 'Test District',
                    'state': 'Test State'
                }
            }
        }
        
        # Mock bookings
        self.tools.booking_table.scan.return_value = {
            'Items': []
        }
        
        # Mock Bedrock response
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = b'''{
            "content": [{
                "text": "Optimal schedule recommendations:\\n- Monday-Friday: Available for booking\\n- Weekend: Maintenance window\\n- Peak season: Increase rates by 20%"
            }]
        }'''
        self.tools.bedrock.invoke_model.return_value = mock_response
        
        result = self.tools.generate_optimal_sharing_schedule('res_test123', 30)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['resource_id'], 'res_test123')
        self.assertIn('optimal_schedule', result)
        self.assertIn('projected_monthly_revenue', result)
    
    def test_customize_alert_preferences_success(self):
        """Test successful alert preferences customization"""
        # Mock user data
        self.tools.user_table.get_item.return_value = {
            'Item': {
                'user_id': 'user_test123',
                'preferences': {}
            }
        }
        
        preferences = {
            'equipment_alerts': {
                'enabled': True,
                'equipment_types': ['tractor', 'harvester'],
                'radius_km': 30,
                'frequency': 'daily_digest'
            },
            'buying_group_alerts': {
                'enabled': True,
                'product_interests': ['seeds', 'fertilizers'],
                'min_discount': 20
            }
        }
        
        result = self.tools.customize_alert_preferences('user_test123', preferences)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['user_id'], 'user_test123')
        self.assertIn('alert_preferences', result)
        self.tools.user_table.put_item.assert_called_once()
    
    def test_get_alert_preferences_success(self):
        """Test successful alert preferences retrieval"""
        # Mock user data with preferences
        self.tools.user_table.get_item.return_value = {
            'Item': {
                'user_id': 'user_test123',
                'preferences': {
                    'alert_preferences': {
                        'equipment_alerts': {
                            'enabled': True,
                            'equipment_types': ['tractor'],
                            'radius_km': 25
                        }
                    }
                }
            }
        }
        
        result = self.tools.get_alert_preferences('user_test123')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['user_id'], 'user_test123')
        self.assertIn('alert_preferences', result)
        self.assertIn('equipment_alerts', result['alert_preferences'])
    
    def test_calculate_distance(self):
        """Test distance calculation between two locations"""
        loc1 = {'latitude': 28.6139, 'longitude': 77.2090}
        loc2 = {'latitude': 28.7041, 'longitude': 77.1025}
        
        distance = self.tools._calculate_distance(loc1, loc2)
        
        self.assertGreater(distance, 0)
        self.assertLess(distance, 20)  # Should be less than 20km
    
    def test_check_equipment_interest(self):
        """Test equipment interest checking"""
        farmer = {
            'preferences': {
                'alert_preferences': {
                    'equipment_alerts': {
                        'enabled': True,
                        'equipment_types': ['tractor', 'harvester']
                    }
                }
            }
        }
        
        # Should be interested in tractor
        self.assertTrue(self.tools._check_equipment_interest(farmer, 'tractor'))
        
        # Should not be interested in pump
        self.assertFalse(self.tools._check_equipment_interest(farmer, 'pump'))
    
    def test_check_product_interest(self):
        """Test product interest checking"""
        farmer = {
            'preferences': {
                'alert_preferences': {
                    'buying_group_alerts': {
                        'enabled': True,
                        'product_interests': ['seeds', 'fertilizers']
                    }
                }
            }
        }
        
        # Should be interested in seeds
        self.assertTrue(self.tools._check_product_interest(farmer, ['seeds', 'pesticides']))
        
        # Should not be interested in tools only
        self.assertFalse(self.tools._check_product_interest(farmer, ['tools']))
    
    def test_resource_not_found(self):
        """Test handling of non-existent resource"""
        self.tools.resource_table.get_item.return_value = {}
        
        result = self.tools.send_equipment_availability_alert('nonexistent', 25)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_user_not_found(self):
        """Test handling of non-existent user"""
        self.tools.user_table.get_item.return_value = {}
        
        result = self.tools.predict_seasonal_demand('nonexistent', {})
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class TestAvailabilityAlertIntegration(unittest.TestCase):
    """Integration tests for availability alert system"""
    
    def test_end_to_end_equipment_alert_flow(self):
        """Test complete equipment alert flow"""
        tools = create_availability_alert_tools()
        
        # Mock all dependencies
        tools.resource_table = Mock()
        tools.user_table = Mock()
        
        # Set up mock data
        tools.resource_table.get_item.return_value = {
            'Item': {
                'resource_id': 'res_integration',
                'owner_user_id': 'owner_001',
                'resource_type': 'tractor',
                'equipment_details': {
                    'name': 'Integration Test Tractor',
                    'daily_rate': Decimal('2500')
                },
                'location': {
                    'district': 'Test District',
                    'state': 'Test State',
                    'latitude': Decimal('28.6139'),
                    'longitude': Decimal('77.2090')
                }
            }
        }
        
        tools.user_table.scan.return_value = {'Items': []}
        
        # Execute alert
        result = tools.send_equipment_availability_alert('res_integration', 25)
        
        # Verify
        self.assertTrue(result['success'])
        self.assertEqual(result['equipment_type'], 'tractor')


if __name__ == '__main__':
    unittest.main()
