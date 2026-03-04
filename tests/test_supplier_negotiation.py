"""
Unit tests for Supplier Negotiation Tools
Tests all supplier negotiation functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
import json
from datetime import datetime

# Mock AWS services before importing tools
@pytest.fixture(autouse=True)
def mock_aws_services():
    """Mock all AWS services"""
    with patch('boto3.resource') as mock_resource, \
         patch('boto3.client') as mock_client:
        
        # Mock DynamoDB
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock Bedrock
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.return_value = {
            'body': Mock(read=lambda: json.dumps({
                'content': [{'text': 'AI-generated negotiation message'}]
            }).encode())
        }
        
        # Mock SNS
        mock_sns = Mock()
        
        def client_side_effect(service_name, **kwargs):
            if service_name == 'bedrock-runtime':
                return mock_bedrock
            elif service_name == 'sns':
                return mock_sns
            return Mock()
        
        mock_resource.return_value = mock_dynamodb
        mock_client.side_effect = client_side_effect
        
        yield {
            'dynamodb': mock_dynamodb,
            'table': mock_table,
            'bedrock': mock_bedrock,
            'sns': mock_sns
        }


@pytest.fixture
def supplier_tools():
    """Create supplier negotiation tools instance"""
    from tools.supplier_negotiation_tools import SupplierNegotiationTools
    return SupplierNegotiationTools()


def test_register_supplier(supplier_tools, mock_aws_services):
    """Test supplier registration"""
    supplier_data = {
        'business_name': 'Test Agro Supplies',
        'contact_person': 'John Doe',
        'phone_number': '+91-9876543210',
        'email': 'john@testagro.com',
        'supplier_type': 'seeds',
        'location': {
            'state': 'Punjab',
            'district': 'Ludhiana',
            'latitude': 30.9010,
            'longitude': 75.8573
        },
        'products_offered': ['wheat_seeds', 'rice_seeds'],
        'certifications': ['ISO 9001', 'Quality Assurance']
    }
    
    result = supplier_tools.register_supplier(supplier_data)
    
    assert result['success'] is True
    assert 'supplier_id' in result
    assert result['supplier_id'].startswith('sup_')
    assert result['verification_status'] == 'pending'
    assert 'Test Agro Supplies' in result['message']
    
    # Verify DynamoDB put_item was called
    mock_aws_services['table'].put_item.assert_called_once()


def test_find_suppliers(supplier_tools, mock_aws_services):
    """Test supplier search"""
    # Mock DynamoDB scan response
    mock_aws_services['table'].scan.return_value = {
        'Items': [
            {
                'supplier_id': 'sup_12345678',
                'business_name': 'Punjab Agro',
                'supplier_type': 'seeds',
                'contact_person': 'Rajesh Kumar',
                'phone_number': '+91-9876543210',
                'email': 'rajesh@punjabagro.com',
                'location': {
                    'state': 'Punjab',
                    'district': 'Ludhiana',
                    'latitude': Decimal('30.9010'),
                    'longitude': Decimal('75.8573')
                },
                'products_offered': ['wheat_seeds', 'fertilizer_urea'],
                'certifications': ['ISO 9001'],
                'ratings': {'average': Decimal('4.5'), 'count': 10},
                'payment_terms': ['on_delivery', 'advance_50'],
                'bulk_discount_tiers': {'500+': '15%'},
                'delivery_areas': ['Ludhiana_Punjab'],
                'minimum_order_quantity': {},
                'active': True,
                'verification_status': 'verified'
            }
        ]
    }
    
    product_requirements = {
        'wheat_seeds': 500,
        'fertilizer_urea': 300
    }
    
    location = {
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
    
    result = supplier_tools.find_suppliers(product_requirements, location)
    
    assert result['success'] is True
    assert result['count'] > 0
    assert len(result['suppliers']) > 0
    
    supplier = result['suppliers'][0]
    assert supplier['supplier_id'] == 'sup_12345678'
    assert supplier['business_name'] == 'Punjab Agro'
    assert 'match_score' in supplier
    assert supplier['meets_moq'] is True
    assert supplier['bulk_discount_available'] is True


def test_generate_bulk_pricing_request(supplier_tools, mock_aws_services):
    """Test bulk pricing request generation"""
    buyer_id = "buyer_12345"
    product_requirements = {
        'wheat_seeds': 500,
        'fertilizer_urea': 300
    }
    supplier_ids = ['sup_12345678', 'sup_87654321']
    delivery_location = {
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
    
    result = supplier_tools.generate_bulk_pricing_request(
        buyer_id,
        product_requirements,
        supplier_ids,
        delivery_location
    )
    
    assert result['success'] is True
    assert 'negotiation_id' in result
    assert result['negotiation_id'].startswith('neg_')
    assert result['suppliers_contacted'] == 2
    assert result['status'] == 'pending_quotes'
    assert 'request_message' in result
    assert 'deadline' in result
    assert len(result['next_steps']) > 0
    
    # Verify Bedrock was called
    mock_aws_services['bedrock'].invoke_model.assert_called_once()
    
    # Verify DynamoDB put_item was called
    mock_aws_services['table'].put_item.assert_called_once()


def test_submit_supplier_quote(supplier_tools, mock_aws_services):
    """Test supplier quote submission"""
    negotiation_id = "neg_12345678"
    supplier_id = "sup_12345678"
    
    # Mock negotiation exists
    mock_aws_services['table'].get_item.return_value = {
        'Item': {
            'negotiation_id': negotiation_id,
            'buyer_id': 'buyer_12345',
            'supplier_ids': [supplier_id, 'sup_87654321'],
            'quotes_received': [],
            'status': 'pending_quotes'
        }
    }
    
    quote_data = {
        'product_pricing': {
            'wheat_seeds': 45.0,
            'fertilizer_urea': 25.0
        },
        'discount_percentage': 20,
        'total_amount': 30000,
        'payment_terms': 'advance_50',
        'delivery_timeline': '7-10 days',
        'quality_certifications': ['ISO 9001', 'Quality Assurance']
    }
    
    result = supplier_tools.submit_supplier_quote(negotiation_id, supplier_id, quote_data)
    
    assert result['success'] is True
    assert 'quote_id' in result
    assert result['quote_id'].startswith('quote_')
    assert result['negotiation_id'] == negotiation_id
    assert result['status'] == 'submitted'
    assert result['quotes_received'] == 1
    assert result['total_suppliers'] == 2


def test_compare_quotes(supplier_tools, mock_aws_services):
    """Test quote comparison"""
    negotiation_id = "neg_12345678"
    
    # Mock negotiation with quotes
    mock_aws_services['table'].get_item.side_effect = [
        {
            'Item': {
                'negotiation_id': negotiation_id,
                'buyer_id': 'buyer_12345',
                'supplier_ids': ['sup_12345678', 'sup_87654321'],
                'quotes_received': ['quote_111', 'quote_222']
            }
        },
        {
            'Item': {
                'quote_id': 'quote_111',
                'supplier_id': 'sup_12345678',
                'product_pricing': {'wheat_seeds': Decimal('45.0'), 'fertilizer_urea': Decimal('25.0')},
                'discount_percentage': Decimal('20'),
                'total_amount': Decimal('30000'),
                'payment_terms': 'advance_50',
                'delivery_timeline': '7-10 days',
                'quality_certifications': ['ISO 9001', 'Quality Assurance']
            }
        },
        {
            'Item': {
                'supplier_id': 'sup_12345678',
                'business_name': 'Punjab Agro',
                'ratings': {'average': Decimal('4.5'), 'count': 10}
            }
        },
        {
            'Item': {
                'quote_id': 'quote_222',
                'supplier_id': 'sup_87654321',
                'product_pricing': {'wheat_seeds': Decimal('42.0'), 'fertilizer_urea': Decimal('27.0')},
                'discount_percentage': Decimal('25'),
                'total_amount': Decimal('29100'),
                'payment_terms': 'on_delivery',
                'delivery_timeline': '5-7 days',
                'quality_certifications': ['ISO 9001']
            }
        },
        {
            'Item': {
                'supplier_id': 'sup_87654321',
                'business_name': 'Haryana Seeds',
                'ratings': {'average': Decimal('4.2'), 'count': 8}
            }
        }
    ]
    
    result = supplier_tools.compare_quotes(negotiation_id)
    
    assert result['success'] is True
    assert result['quotes_count'] == 2
    assert len(result['quotes']) == 2
    assert len(result['ranked_quotes']) == 2
    assert 'ai_analysis' in result
    assert 'recommended_quote' in result
    assert result['best_price'] == 29100
    assert result['best_discount'] == 25
    assert result['average_price'] == 29550


def test_verify_quality_assurance(supplier_tools, mock_aws_services):
    """Test quality assurance verification"""
    supplier_id = "sup_12345678"
    product_name = "wheat_seeds"
    
    # Mock supplier data
    mock_aws_services['table'].get_item.return_value = {
        'Item': {
            'supplier_id': supplier_id,
            'business_name': 'Punjab Agro',
            'certifications': ['ISO 9001', 'Seed Certification', 'Quality Assurance'],
            'quality_standards': {
                'wheat_seeds': {'purity': '98%', 'germination': '85%'}
            },
            'verification_status': 'verified'
        }
    }
    
    result = supplier_tools.verify_quality_assurance(supplier_id, product_name)
    
    assert result['success'] is True
    assert result['supplier_id'] == supplier_id
    assert result['supplier_name'] == 'Punjab Agro'
    assert result['product_name'] == product_name
    assert len(result['certifications']) == 3
    assert 'verification_checks' in result
    assert result['overall_status'] in ['verified', 'needs_review']
    assert 'compliance_score' in result


def test_coordinate_delivery(supplier_tools, mock_aws_services):
    """Test delivery coordination"""
    negotiation_id = "neg_12345678"
    selected_quote_id = "quote_111"
    
    # Mock quote and negotiation data
    mock_aws_services['table'].get_item.side_effect = [
        {
            'Item': {
                'quote_id': selected_quote_id,
                'supplier_id': 'sup_12345678',
                'total_amount': Decimal('30000')
            }
        },
        {
            'Item': {
                'negotiation_id': negotiation_id,
                'buyer_id': 'buyer_12345',
                'delivery_location': {
                    'state': 'Punjab',
                    'district': 'Ludhiana'
                }
            }
        }
    ]
    
    delivery_details = {
        'delivery_date': '2024-01-15',
        'delivery_time_slot': 'Morning (8AM-12PM)',
        'delivery_contact': {
            'name': 'Harpreet Singh',
            'phone': '+91-9876543210'
        },
        'special_instructions': 'Call before delivery'
    }
    
    result = supplier_tools.coordinate_delivery(negotiation_id, selected_quote_id, delivery_details)
    
    assert result['success'] is True
    assert 'delivery_id' in result
    assert result['delivery_id'].startswith('del_')
    assert 'tracking_number' in result
    assert result['tracking_number'].startswith('TRK')
    assert result['delivery_status'] == 'scheduled'
    assert result['delivery_date'] == '2024-01-15'
    assert len(result['next_steps']) > 0


def test_manage_payment(supplier_tools, mock_aws_services):
    """Test payment management"""
    negotiation_id = "neg_12345678"
    
    # Mock negotiation and quote data
    mock_aws_services['table'].get_item.side_effect = [
        {
            'Item': {
                'negotiation_id': negotiation_id,
                'buyer_id': 'buyer_12345',
                'selected_quote_id': 'quote_111'
            }
        },
        {
            'Item': {
                'quote_id': 'quote_111',
                'supplier_id': 'sup_12345678',
                'total_amount': Decimal('30000'),
                'payment_terms': 'advance_50'
            }
        }
    ]
    
    payment_data = {
        'payment_method': 'bank_transfer',
        'member_contributions': {
            'farmer_001': 6000,
            'farmer_002': 6000,
            'farmer_003': 6000,
            'farmer_004': 6000,
            'farmer_005': 6000
        }
    }
    
    result = supplier_tools.manage_payment(negotiation_id, payment_data)
    
    assert result['success'] is True
    assert 'payment_id' in result
    assert result['payment_id'].startswith('pay_')
    assert result['total_amount'] == 30000
    assert result['payment_status'] == 'pending'
    assert result['payment_method'] == 'bank_transfer'
    assert result['member_count'] == 5
    assert len(result['next_steps']) > 0


def test_get_negotiation_status(supplier_tools, mock_aws_services):
    """Test negotiation status retrieval"""
    negotiation_id = "neg_12345678"
    
    # Mock negotiation data
    mock_aws_services['table'].get_item.return_value = {
        'Item': {
            'negotiation_id': negotiation_id,
            'buyer_id': 'buyer_12345',
            'status': 'delivery_scheduled',
            'product_requirements': {'wheat_seeds': 500, 'fertilizer_urea': 300},
            'supplier_ids': ['sup_12345678', 'sup_87654321'],
            'quotes_received': ['quote_111', 'quote_222'],
            'selected_quote_id': 'quote_111',
            'delivery_id': 'del_12345678',
            'payment_id': 'pay_12345678',
            'created_timestamp': 1234567890,
            'deadline': '2024-01-31'
        }
    }
    
    result = supplier_tools.get_negotiation_status(negotiation_id)
    
    assert result['success'] is True
    assert result['negotiation_id'] == negotiation_id
    assert result['buyer_id'] == 'buyer_12345'
    assert result['status'] == 'delivery_scheduled'
    assert result['suppliers_contacted'] == 2
    assert result['quotes_received'] == 2
    assert result['selected_quote_id'] == 'quote_111'
    assert result['delivery_id'] == 'del_12345678'
    assert result['payment_id'] == 'pay_12345678'


def test_supplier_not_found(supplier_tools, mock_aws_services):
    """Test error handling when supplier not found"""
    mock_aws_services['table'].get_item.return_value = {}
    
    result = supplier_tools.verify_quality_assurance('sup_nonexistent', 'wheat_seeds')
    
    assert result['success'] is False
    assert 'error' in result
    assert 'not found' in result['error'].lower()


def test_negotiation_not_found(supplier_tools, mock_aws_services):
    """Test error handling when negotiation not found"""
    mock_aws_services['table'].get_item.return_value = {}
    
    result = supplier_tools.compare_quotes('neg_nonexistent')
    
    assert result['success'] is False
    assert 'error' in result
    assert 'not found' in result['error'].lower()


def test_no_quotes_received(supplier_tools, mock_aws_services):
    """Test error handling when no quotes received"""
    mock_aws_services['table'].get_item.return_value = {
        'Item': {
            'negotiation_id': 'neg_12345678',
            'quotes_received': []
        }
    }
    
    result = supplier_tools.compare_quotes('neg_12345678')
    
    assert result['success'] is False
    assert 'error' in result
    assert 'no quotes' in result['error'].lower()


def test_calculate_supplier_match_score(supplier_tools):
    """Test supplier match score calculation"""
    supplier = {
        'products_offered': ['wheat_seeds', 'fertilizer_urea', 'rice_seeds'],
        'location': {'state': 'Punjab', 'district': 'Ludhiana'},
        'ratings': {'average': Decimal('4.5')},
        'certifications': ['ISO 9001', 'Quality Assurance', 'Seed Certification'],
        'bulk_discount_tiers': {'500+': '15%'}
    }
    
    requirements = {
        'wheat_seeds': 500,
        'fertilizer_urea': 300
    }
    
    location = {
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
    
    score = supplier_tools._calculate_supplier_match_score(supplier, requirements, location)
    
    assert 0 <= score <= 1.0
    assert score > 0.5  # Should have a good match


def test_can_deliver_to(supplier_tools):
    """Test delivery area checking"""
    supplier = {
        'location': {'state': 'Punjab', 'district': 'Ludhiana'},
        'delivery_areas': ['Ludhiana_Punjab', 'Patiala_Punjab']
    }
    
    location1 = {'state': 'Punjab', 'district': 'Ludhiana'}
    location2 = {'state': 'Haryana', 'district': 'Karnal'}
    
    assert supplier_tools._can_deliver_to(supplier, location1) is True
    assert supplier_tools._can_deliver_to(supplier, location2) is False


def test_meets_minimum_order(supplier_tools):
    """Test minimum order quantity checking"""
    supplier = {
        'minimum_order_quantity': {
            'wheat_seeds': 100,
            'fertilizer_urea': 200
        }
    }
    
    requirements1 = {'wheat_seeds': 500, 'fertilizer_urea': 300}
    requirements2 = {'wheat_seeds': 50, 'fertilizer_urea': 100}
    
    assert supplier_tools._meets_minimum_order(supplier, requirements1) is True
    assert supplier_tools._meets_minimum_order(supplier, requirements2) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
