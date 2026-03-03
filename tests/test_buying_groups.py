"""
Unit tests for RISE Cooperative Buying Groups Tools
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.buying_group_tools import BuyingGroupTools
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def buying_group_tools():
    """Create BuyingGroupTools instance with mocked AWS clients"""
    with patch('boto3.resource'), patch('boto3.client'):
        tools = BuyingGroupTools(region='us-east-1')
        
        # Mock DynamoDB tables
        tools.groups_table = Mock()
        tools.user_profiles_table = Mock()
        
        # Mock AWS clients
        tools.sns = Mock()
        tools.bedrock = Mock()
        
        return tools


def test_create_buying_group(buying_group_tools):
    """Test buying group creation"""
    # Mock DynamoDB put_item
    buying_group_tools.groups_table.put_item = Mock(return_value={})
    
    organizer_id = "farmer_12345"
    group_data = {
        'group_name': 'Test Buying Group',
        'target_products': ['wheat_seeds', 'fertilizer_urea'],
        'location': {
            'state': 'Punjab',
            'district': 'Ludhiana',
            'radius_km': 25
        },
        'max_members': 30,
        'min_members': 5
    }
    
    result = buying_group_tools.create_buying_group(organizer_id, group_data)
    
    assert result['success'] is True
    assert 'group_id' in result
    assert result['group_name'] == 'Test Buying Group'
    assert result['status'] == 'forming'
    assert result['target_discount'] == '15-30%'
    
    # Verify DynamoDB was called
    buying_group_tools.groups_table.put_item.assert_called_once()


def test_find_matching_groups(buying_group_tools):
    """Test finding matching buying groups"""
    # Mock user profile
    buying_group_tools.user_profiles_table.get_item = Mock(return_value={
        'Item': {
            'user_id': 'farmer_67890',
            'location': {
                'state': 'Punjab',
                'district': 'Ludhiana'
            }
        }
    })
    
    # Mock groups scan
    buying_group_tools.groups_table.scan = Mock(return_value={
        'Items': [
            {
                'group_id': 'grp_test123',
                'group_name': 'Ludhiana Seed Buyers',
                'organizer_user_id': 'farmer_12345',
                'members': ['farmer_12345'],
                'target_products': ['wheat_seeds', 'fertilizer_urea', 'pesticide_spray'],
                'location_area': 'Ludhiana_Punjab',
                'location': {
                    'state': 'Punjab',
                    'district': 'Ludhiana',
                    'radius_km': 25
                },
                'group_status': 'forming',
                'max_members': 30,
                'target_discount_min': Decimal('15'),
                'target_discount_max': Decimal('30'),
                'deadline': (datetime.now() + timedelta(days=14)).isoformat()
            }
        ]
    })
    
    user_id = 'farmer_67890'
    requirements = {
        'products': ['wheat_seeds', 'fertilizer_urea'],
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
    
    result = buying_group_tools.find_matching_groups(user_id, requirements)
    
    assert result['success'] is True
    assert result['count'] == 1
    assert len(result['groups']) == 1
    
    group = result['groups'][0]
    assert group['group_id'] == 'grp_test123'
    assert group['group_name'] == 'Ludhiana Seed Buyers'
    assert 'wheat_seeds' in group['matching_products']
    assert 'fertilizer_urea' in group['matching_products']
    assert group['match_score'] == 100.0  # Both products match


def test_join_buying_group(buying_group_tools):
    """Test joining a buying group"""
    # Mock group retrieval
    buying_group_tools.groups_table.get_item = Mock(return_value={
        'Item': {
            'group_id': 'grp_test123',
            'group_name': 'Test Group',
            'organizer_user_id': 'farmer_12345',
            'members': ['farmer_12345'],
            'target_products': ['wheat_seeds', 'fertilizer_urea'],
            'group_status': 'forming',
            'max_members': 30,
            'min_members': 5,
            'member_requirements': {
                'farmer_12345': {
                    'wheat_seeds': 100,
                    'fertilizer_urea': 50
                }
            },
            'total_quantity_needed': {
                'wheat_seeds': Decimal('100'),
                'fertilizer_urea': Decimal('50')
            }
        }
    })
    
    # Mock DynamoDB put_item
    buying_group_tools.groups_table.put_item = Mock(return_value={})
    
    user_id = 'farmer_67890'
    group_id = 'grp_test123'
    member_requirements = {
        'wheat_seeds': 150,
        'fertilizer_urea': 75
    }
    
    result = buying_group_tools.join_buying_group(user_id, group_id, member_requirements)
    
    assert result['success'] is True
    assert result['group_id'] == 'grp_test123'
    assert result['total_members'] == 2
    assert result['total_quantities']['wheat_seeds'] == 250.0
    assert result['total_quantities']['fertilizer_urea'] == 125.0
    assert 'potential_savings' in result


def test_join_full_group(buying_group_tools):
    """Test joining a full buying group"""
    # Mock group retrieval with full members
    members = [f'farmer_{i}' for i in range(30)]
    
    buying_group_tools.groups_table.get_item = Mock(return_value={
        'Item': {
            'group_id': 'grp_test123',
            'group_name': 'Full Group',
            'organizer_user_id': 'farmer_0',
            'members': members,
            'target_products': ['wheat_seeds'],
            'group_status': 'forming',
            'max_members': 30,
            'min_members': 5,
            'member_requirements': {}
        }
    })
    
    user_id = 'farmer_new'
    group_id = 'grp_test123'
    member_requirements = {'wheat_seeds': 100}
    
    result = buying_group_tools.join_buying_group(user_id, group_id, member_requirements)
    
    assert result['success'] is False
    assert 'full' in result['error'].lower()


def test_calculate_bulk_pricing(buying_group_tools):
    """Test bulk pricing calculation"""
    # Mock group retrieval
    buying_group_tools.groups_table.get_item = Mock(return_value={
        'Item': {
            'group_id': 'grp_test123',
            'group_name': 'Test Group',
            'members': ['farmer_1', 'farmer_2', 'farmer_3'],
            'total_quantity_needed': {
                'wheat_seeds': Decimal('1000'),
                'fertilizer_urea': Decimal('500')
            },
            'member_requirements': {
                'farmer_1': {'wheat_seeds': 400, 'fertilizer_urea': 200},
                'farmer_2': {'wheat_seeds': 300, 'fertilizer_urea': 150},
                'farmer_3': {'wheat_seeds': 300, 'fertilizer_urea': 150}
            }
        }
    })
    
    # Mock DynamoDB put_item
    buying_group_tools.groups_table.put_item = Mock(return_value={})
    
    group_id = 'grp_test123'
    
    result = buying_group_tools.calculate_bulk_pricing(group_id)
    
    assert result['success'] is True
    assert 'pricing_breakdown' in result
    assert 'wheat_seeds' in result['pricing_breakdown']
    assert 'fertilizer_urea' in result['pricing_breakdown']
    
    # Check wheat_seeds pricing (quantity >= 1000, should get 30% discount)
    wheat_pricing = result['pricing_breakdown']['wheat_seeds']
    assert wheat_pricing['quantity'] == 1000.0
    assert wheat_pricing['discount_percentage'] == 30
    
    # Check fertilizer_urea pricing (quantity >= 500, should get 25% discount)
    urea_pricing = result['pricing_breakdown']['fertilizer_urea']
    assert urea_pricing['quantity'] == 500.0
    assert urea_pricing['discount_percentage'] == 25
    
    # Check member costs
    assert 'member_costs' in result
    assert len(result['member_costs']) == 3


def test_negotiate_with_vendors(buying_group_tools):
    """Test AI-powered vendor negotiation"""
    # Mock group retrieval
    buying_group_tools.groups_table.get_item = Mock(return_value={
        'Item': {
            'group_id': 'grp_test123',
            'group_name': 'Test Group',
            'members': ['farmer_1', 'farmer_2', 'farmer_3'],
            'total_quantity_needed': {
                'wheat_seeds': Decimal('1000'),
                'fertilizer_urea': Decimal('500')
            },
            'location': {
                'state': 'Punjab',
                'district': 'Ludhiana'
            }
        }
    })
    
    # Mock Bedrock response
    buying_group_tools.bedrock.invoke_model = Mock(return_value={
        'body': Mock(read=Mock(return_value=b'{"content": [{"text": "Dear Supplier, We are a cooperative buying group..."}]}'))
    })
    
    # Mock DynamoDB put_item
    buying_group_tools.groups_table.put_item = Mock(return_value={})
    
    group_id = 'grp_test123'
    vendor_list = ['Vendor A', 'Vendor B', 'Vendor C']
    
    result = buying_group_tools.negotiate_with_vendors(group_id, vendor_list)
    
    assert result['success'] is True
    assert 'negotiation_message' in result
    assert result['vendors_contacted'] == 3
    assert result['status'] == 'negotiating'
    assert 'next_steps' in result


def test_get_group_details(buying_group_tools):
    """Test getting group details"""
    # Mock group retrieval
    buying_group_tools.groups_table.get_item = Mock(return_value={
        'Item': {
            'group_id': 'grp_test123',
            'group_name': 'Test Group',
            'organizer_user_id': 'farmer_12345',
            'members': ['farmer_12345', 'farmer_67890'],
            'target_products': ['wheat_seeds', 'fertilizer_urea'],
            'location': {
                'state': 'Punjab',
                'district': 'Ludhiana',
                'radius_km': 25
            },
            'group_status': 'active',
            'total_quantity_needed': {
                'wheat_seeds': Decimal('500'),
                'fertilizer_urea': Decimal('250')
            },
            'bulk_pricing_achieved': {
                'wheat_seeds': Decimal('25'),
                'fertilizer_urea': Decimal('20')
            },
            'vendor_details': {},
            'deadline': (datetime.now() + timedelta(days=7)).isoformat(),
            'created_timestamp': int(datetime.now().timestamp()),
            'min_members': 5,
            'max_members': 30
        }
    })
    
    group_id = 'grp_test123'
    
    result = buying_group_tools.get_group_details(group_id)
    
    assert result['success'] is True
    assert result['group_id'] == 'grp_test123'
    assert result['group_name'] == 'Test Group'
    assert result['member_count'] == 2
    assert result['status'] == 'active'
    assert result['total_quantities']['wheat_seeds'] == 500.0
    assert result['bulk_pricing']['wheat_seeds'] == 25.0


def test_get_user_groups(buying_group_tools):
    """Test getting user's groups"""
    # Mock groups scan
    buying_group_tools.groups_table.scan = Mock(return_value={
        'Items': [
            {
                'group_id': 'grp_test1',
                'group_name': 'Group 1',
                'organizer_user_id': 'farmer_12345',
                'members': ['farmer_12345', 'farmer_67890'],
                'target_products': ['wheat_seeds'],
                'group_status': 'active',
                'deadline': datetime.now().isoformat()
            },
            {
                'group_id': 'grp_test2',
                'group_name': 'Group 2',
                'organizer_user_id': 'farmer_99999',
                'members': ['farmer_99999', 'farmer_67890'],
                'target_products': ['fertilizer_urea'],
                'group_status': 'forming',
                'deadline': datetime.now().isoformat()
            },
            {
                'group_id': 'grp_test3',
                'group_name': 'Group 3',
                'organizer_user_id': 'farmer_11111',
                'members': ['farmer_11111', 'farmer_22222'],
                'target_products': ['pesticide_spray'],
                'group_status': 'active',
                'deadline': datetime.now().isoformat()
            }
        ]
    })
    
    user_id = 'farmer_67890'
    
    result = buying_group_tools.get_user_groups(user_id)
    
    assert result['success'] is True
    assert result['count'] == 2  # User is in 2 groups
    assert len(result['groups']) == 2
    
    # Check that user is in both groups
    group_ids = [g['group_id'] for g in result['groups']]
    assert 'grp_test1' in group_ids
    assert 'grp_test2' in group_ids
    assert 'grp_test3' not in group_ids


def test_calculate_total_quantities(buying_group_tools):
    """Test total quantities calculation"""
    member_requirements = {
        'farmer_1': {'wheat_seeds': 100, 'fertilizer_urea': 50},
        'farmer_2': {'wheat_seeds': 150, 'fertilizer_urea': 75},
        'farmer_3': {'wheat_seeds': 200, 'pesticide_spray': 25}
    }
    
    totals = buying_group_tools._calculate_total_quantities(member_requirements)
    
    assert totals['wheat_seeds'] == Decimal('450')
    assert totals['fertilizer_urea'] == Decimal('125')
    assert totals['pesticide_spray'] == Decimal('25')


def test_calculate_potential_savings(buying_group_tools):
    """Test potential savings calculation"""
    member_requirements = {
        'wheat_seeds': 100,
        'fertilizer_urea': 50
    }
    
    total_quantities = {
        'wheat_seeds': Decimal('1000'),  # Should get 30% discount
        'fertilizer_urea': Decimal('500')  # Should get 25% discount
    }
    
    savings = buying_group_tools._calculate_potential_savings(member_requirements, total_quantities)
    
    assert 'wheat_seeds' in savings
    assert 'fertilizer_urea' in savings
    
    # wheat_seeds: 100 units * 1000 price * 30% = 30,000
    assert savings['wheat_seeds'] == 30000.0
    
    # fertilizer_urea: 50 units * 1000 price * 25% = 12,500
    assert savings['fertilizer_urea'] == 12500.0


def test_group_not_found(buying_group_tools):
    """Test handling of non-existent group"""
    buying_group_tools.groups_table.get_item = Mock(return_value={})
    
    result = buying_group_tools.get_group_details('nonexistent_group')
    
    assert result['success'] is False
    assert 'not found' in result['error'].lower()


def test_user_profile_not_found(buying_group_tools):
    """Test handling of non-existent user profile"""
    buying_group_tools.user_profiles_table.get_item = Mock(return_value={})
    
    result = buying_group_tools.find_matching_groups('nonexistent_user', {'products': ['wheat_seeds']})
    
    assert result['success'] is False
    assert 'not found' in result['error'].lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
