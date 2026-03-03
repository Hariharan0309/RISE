"""
Unit tests for Government Scheme Tools
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta
from decimal import Decimal
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

from government_scheme_tools import GovernmentSchemeTools


class TestGovernmentSchemeTools(unittest.TestCase):
    """Test cases for Government Scheme Tools"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_dynamodb = Mock()
        self.mock_bedrock = Mock()
        self.mock_table = Mock()
        
        with patch('boto3.resource') as mock_resource, \
             patch('boto3.client') as mock_client:
            mock_resource.return_value = self.mock_dynamodb
            mock_client.return_value = self.mock_bedrock
            self.mock_dynamodb.Table.return_value = self.mock_table
            
            self.tools = GovernmentSchemeTools(region='us-east-1')
            self.tools.schemes_table = self.mock_table
    
    def test_ingest_scheme_data_success(self):
        """Test successful scheme data ingestion"""
        scheme_data = {
            'scheme_name': 'Test Scheme',
            'scheme_type': 'central',
            'state': 'central',
            'category': 'subsidies',
            'description': 'Test description',
            'benefit_amount': 5000
        }
        
        self.mock_table.put_item.return_value = {}
        
        result = self.tools.ingest_scheme_data(scheme_data)
        
        self.assertTrue(result['success'])
        self.assertIn('scheme_id', result)
        self.assertEqual(result['scheme_name'], 'Test Scheme')
        self.mock_table.put_item.assert_called_once()
    
    def test_ingest_scheme_data_missing_fields(self):
        """Test scheme ingestion with missing required fields"""
        scheme_data = {
            'scheme_name': 'Test Scheme'
            # Missing required fields
        }
        
        result = self.tools.ingest_scheme_data(scheme_data)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('Missing required field', result['error'])
    
    def test_search_schemes_by_state(self):
        """Test searching schemes by state"""
        mock_schemes = [
            {
                'scheme_id': 'SCH001',
                'scheme_name': 'State Scheme 1',
                'state': 'uttar pradesh',
                'scheme_type': 'state',
                'active_status': 'active',
                'benefit_amount': Decimal('10000')
            }
        ]
        
        self.mock_table.query.return_value = {'Items': mock_schemes}
        
        result = self.tools.search_schemes(state='uttar pradesh', scheme_type='state')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['schemes'][0]['scheme_name'], 'State Scheme 1')
        self.mock_table.query.assert_called_once()
    
    def test_search_schemes_by_category(self):
        """Test searching schemes by category"""
        mock_schemes = [
            {
                'scheme_id': 'SCH002',
                'scheme_name': 'Insurance Scheme',
                'category': 'crop_insurance',
                'active_status': 'active',
                'benefit_amount': Decimal('50000')
            }
        ]
        
        self.mock_table.query.return_value = {'Items': mock_schemes}
        
        result = self.tools.search_schemes(category='crop_insurance')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['schemes'][0]['category'], 'crop_insurance')
    
    def test_search_schemes_active_only_filter(self):
        """Test filtering for active schemes only"""
        mock_schemes = [
            {
                'scheme_id': 'SCH003',
                'scheme_name': 'Active Scheme',
                'active_status': 'active',
                'benefit_amount': Decimal('5000')
            },
            {
                'scheme_id': 'SCH004',
                'scheme_name': 'Inactive Scheme',
                'active_status': 'inactive',
                'benefit_amount': Decimal('3000')
            }
        ]
        
        self.mock_table.scan.return_value = {'Items': mock_schemes}
        
        result = self.tools.search_schemes(active_only=True)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['schemes'][0]['active_status'], 'active')
    
    def test_get_scheme_details_success(self):
        """Test getting scheme details successfully"""
        mock_scheme = {
            'scheme_id': 'SCH005',
            'scheme_name': 'PM-KISAN',
            'description': 'Direct income support',
            'benefit_amount': Decimal('6000'),
            'active_status': 'active'
        }
        
        self.mock_table.get_item.return_value = {'Item': mock_scheme}
        
        result = self.tools.get_scheme_details('SCH005')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['scheme']['scheme_name'], 'PM-KISAN')
        self.assertEqual(result['scheme']['benefit_amount'], 6000.0)
    
    def test_get_scheme_details_not_found(self):
        """Test getting details for non-existent scheme"""
        self.mock_table.get_item.return_value = {}
        
        result = self.tools.get_scheme_details('INVALID_ID')
        
        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'])
    
    def test_update_scheme_status_success(self):
        """Test updating scheme status successfully"""
        self.mock_table.update_item.return_value = {}
        
        result = self.tools.update_scheme_status('SCH006', 'inactive')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['new_status'], 'inactive')
        self.mock_table.update_item.assert_called_once()
    
    def test_update_scheme_status_invalid(self):
        """Test updating scheme with invalid status"""
        result = self.tools.update_scheme_status('SCH007', 'invalid_status')
        
        self.assertFalse(result['success'])
        self.assertIn('Invalid status', result['error'])
    
    def test_scrape_government_schemes(self):
        """Test scraping government schemes"""
        self.mock_table.put_item.return_value = {}
        
        result = self.tools.scrape_government_schemes('all')
        
        self.assertTrue(result['success'])
        self.assertGreater(result['ingested_count'], 0)
        self.assertEqual(result['source'], 'all')
    
    def test_monitor_scheme_updates(self):
        """Test monitoring scheme updates"""
        current_time = int(datetime.now().timestamp())
        expired_deadline = int((datetime.now() - timedelta(days=1)).timestamp())
        
        mock_schemes = [
            {
                'scheme_id': 'SCH008',
                'scheme_name': 'Active Scheme',
                'application_deadline': int((datetime.now() + timedelta(days=30)).timestamp()),
                'active_status': 'active'
            },
            {
                'scheme_id': 'SCH009',
                'scheme_name': 'Expired Scheme',
                'application_deadline': expired_deadline,
                'active_status': 'active'
            }
        ]
        
        self.mock_table.query.return_value = {'Items': mock_schemes}
        self.mock_table.update_item.return_value = {}
        
        result = self.tools.monitor_scheme_updates()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['total_schemes_monitored'], 2)
        self.assertEqual(result['expired_schemes'], 1)
    
    def test_categorize_scheme(self):
        """Test AI-based scheme categorization"""
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{
                'text': json.dumps({
                    'primary_category': 'crop_insurance',
                    'secondary_categories': ['subsidies'],
                    'target_beneficiaries': ['small_farmers'],
                    'key_benefits': 'Crop protection',
                    'tags': ['insurance', 'protection']
                })
            }]
        }).encode()
        
        self.mock_bedrock.invoke_model.return_value = mock_response
        
        result = self.tools.categorize_scheme('Test scheme description')
        
        self.assertTrue(result['success'])
        self.assertIn('categorization', result)
        self.assertEqual(result['categorization']['primary_category'], 'crop_insurance')
    
    def test_enrich_scheme_data(self):
        """Test scheme data enrichment"""
        scheme_data = {
            'scheme_name': 'Test Scheme',
            'state': 'DELHI',
            'category': 'SUBSIDIES',
            'benefit_amount': 5000
        }
        
        enriched = self.tools._enrich_scheme_data(scheme_data)
        
        self.assertEqual(enriched['state'], 'delhi')
        self.assertEqual(enriched['category'], 'subsidies')
        self.assertIsInstance(enriched['benefit_amount'], Decimal)
        self.assertIn('created_at', enriched)
        self.assertIn('last_updated', enriched)
        self.assertIn('tags', enriched)
    
    def test_generate_tags(self):
        """Test tag generation for schemes"""
        scheme_data = {
            'category': 'crop_insurance',
            'state': 'punjab',
            'scheme_type': 'central',
            'eligibility_criteria': {
                'land_size': 1.5
            }
        }
        
        tags = self.tools._generate_tags(scheme_data)
        
        self.assertIn('crop_insurance', tags)
        self.assertIn('punjab', tags)
        self.assertIn('central', tags)
        self.assertIn('small_farmer', tags)
    
    def test_convert_decimals(self):
        """Test Decimal to float conversion"""
        data = {
            'amount': Decimal('1000.50'),
            'nested': {
                'value': Decimal('500.25')
            },
            'list': [Decimal('100'), Decimal('200')]
        }
        
        converted = self.tools._convert_decimals(data)
        
        self.assertEqual(converted['amount'], 1000.50)
        self.assertEqual(converted['nested']['value'], 500.25)
        self.assertEqual(converted['list'], [100.0, 200.0])
    
    def test_get_mock_schemes(self):
        """Test mock scheme data generation"""
        mock_schemes = self.tools._get_mock_schemes()
        
        self.assertIsInstance(mock_schemes, list)
        self.assertGreater(len(mock_schemes), 0)
        
        for scheme in mock_schemes:
            self.assertIn('scheme_name', scheme)
            self.assertIn('scheme_type', scheme)
            self.assertIn('category', scheme)
            self.assertIn('eligibility_criteria', scheme)


class TestGovernmentSchemeToolFunctions(unittest.TestCase):
    """Test cases for tool functions"""
    
    @patch('government_scheme_tools.create_government_scheme_tools')
    def test_search_schemes_tool(self, mock_create):
        """Test search schemes tool function"""
        from government_scheme_tools import search_schemes_tool
        
        mock_tools = Mock()
        mock_tools.search_schemes.return_value = {
            'success': True,
            'count': 2,
            'schemes': [
                {
                    'scheme_name': 'PM-KISAN',
                    'scheme_type': 'central',
                    'category': 'subsidies',
                    'benefit_amount': 6000,
                    'active_status': 'active'
                },
                {
                    'scheme_name': 'PMFBY',
                    'scheme_type': 'central',
                    'category': 'crop_insurance',
                    'benefit_amount': 200000,
                    'active_status': 'active'
                }
            ]
        }
        mock_create.return_value = mock_tools
        
        result = search_schemes_tool(category='subsidies')
        
        self.assertIn('PM-KISAN', result)
        self.assertIn('2 government schemes', result)
    
    @patch('government_scheme_tools.create_government_scheme_tools')
    def test_get_scheme_details_tool(self, mock_create):
        """Test get scheme details tool function"""
        from government_scheme_tools import get_scheme_details_tool
        
        mock_tools = Mock()
        mock_tools.get_scheme_details.return_value = {
            'success': True,
            'scheme': {
                'scheme_name': 'PM-KISAN',
                'scheme_type': 'central',
                'category': 'subsidies',
                'description': 'Direct income support',
                'benefit_amount': 6000,
                'active_status': 'active',
                'eligibility_criteria': {
                    'land_ownership': 'required'
                },
                'required_documents': ['Aadhaar', 'Bank Account'],
                'application_process': 'Online through portal',
                'official_website': 'https://pmkisan.gov.in'
            }
        }
        mock_create.return_value = mock_tools
        
        result = get_scheme_details_tool('SCH001')
        
        self.assertIn('PM-KISAN', result)
        self.assertIn('Direct income support', result)
        self.assertIn('Aadhaar', result)
    
    @patch('government_scheme_tools.create_government_scheme_tools')
    def test_ingest_scheme_tool(self, mock_create):
        """Test ingest scheme tool function"""
        from government_scheme_tools import ingest_scheme_tool
        
        mock_tools = Mock()
        mock_tools.ingest_scheme_data.return_value = {
            'success': True,
            'scheme_id': 'SCH_NEW001',
            'scheme_name': 'New Test Scheme'
        }
        mock_create.return_value = mock_tools
        
        scheme_data = {
            'scheme_name': 'New Test Scheme',
            'scheme_type': 'state',
            'state': 'maharashtra',
            'category': 'irrigation'
        }
        
        result = ingest_scheme_tool(scheme_data)
        
        self.assertIn('Successfully ingested', result)
        self.assertIn('New Test Scheme', result)


if __name__ == '__main__':
    unittest.main()
