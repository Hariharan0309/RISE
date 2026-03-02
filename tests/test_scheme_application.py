"""
Unit tests for RISE Scheme Application Tools
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.scheme_application_tools import SchemeApplicationTools
from decimal import Decimal


class TestSchemeApplicationTools(unittest.TestCase):
    """Test cases for scheme application tools"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tools = SchemeApplicationTools(region='us-east-1')
        
        # Mock AWS clients
        self.tools.dynamodb = Mock()
        self.tools.bedrock = Mock()
        self.tools.translate = Mock()
        self.tools.polly = Mock()
        self.tools.sns = Mock()
        self.tools.s3 = Mock()
        
        # Mock tables
        self.tools.applications_table = Mock()
        self.tools.schemes_table = Mock()
        self.tools.user_profiles_table = Mock()
    
    def test_generate_application_wizard_success(self):
        """Test successful wizard generation"""
        # Mock scheme data
        self.tools.schemes_table.get_item.return_value = {
            'Item': {
                'scheme_id': 'SCH_PM_KISAN',
                'scheme_name': 'PM-KISAN',
                'category': 'subsidies',
                'benefit_amount': Decimal('6000'),
                'required_documents': ['Aadhaar Card', 'Land Records', 'Bank Passbook']
            }
        }
        
        # Mock user profile
        self.tools.user_profiles_table.get_item.return_value = {
            'Item': {
                'user_id': 'user_123',
                'name': 'Test Farmer',
                'preferences': {'language': 'hi'}
            }
        }
        
        result = self.tools.generate_application_wizard('user_123', 'SCH_PM_KISAN', 'hi')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['scheme_id'], 'SCH_PM_KISAN')
        self.assertIn('wizard_steps', result)
        self.assertGreater(len(result['wizard_steps']), 0)
        self.assertEqual(result['language'], 'hi')
    
    def test_generate_application_wizard_scheme_not_found(self):
        """Test wizard generation with non-existent scheme"""
        self.tools.schemes_table.get_item.return_value = {}
        
        result = self.tools.generate_application_wizard('user_123', 'INVALID_SCHEME', 'hi')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_validate_documents_all_valid(self):
        """Test document validation with all valid documents"""
        # Mock scheme data
        self.tools.schemes_table.get_item.return_value = {
            'Item': {
                'scheme_id': 'SCH_TEST',
                'required_documents': ['Aadhaar Card', 'Bank Passbook']
            }
        }
        
        documents = [
            {'name': 'Aadhaar Card', 'format': 'pdf', 'size_mb': 1.5},
            {'name': 'Bank Passbook', 'format': 'jpg', 'size_mb': 1.0}
        ]
        
        result = self.tools.validate_documents(documents, 'SCH_TEST')
        
        self.assertTrue(result['success'])
        self.assertTrue(result['all_valid'])
        self.assertEqual(len(result['validation_results']), 2)
        self.assertEqual(len(result['missing_documents']), 0)
    
    def test_validate_documents_invalid_format(self):
        """Test document validation with invalid format"""
        self.tools.schemes_table.get_item.return_value = {
            'Item': {
                'scheme_id': 'SCH_TEST',
                'required_documents': ['Aadhaar Card']
            }
        }
        
        documents = [
            {'name': 'Aadhaar Card', 'format': 'txt', 'size_mb': 1.0}
        ]
        
        result = self.tools.validate_documents(documents, 'SCH_TEST')
        
        self.assertTrue(result['success'])
        self.assertFalse(result['all_valid'])
        self.assertFalse(result['validation_results'][0]['valid'])
        self.assertGreater(len(result['validation_results'][0]['issues']), 0)
    
    def test_validate_documents_file_too_large(self):
        """Test document validation with oversized file"""
        self.tools.schemes_table.get_item.return_value = {
            'Item': {
                'scheme_id': 'SCH_TEST',
                'required_documents': ['Aadhaar Card']
            }
        }
        
        documents = [
            {'name': 'Aadhaar Card', 'format': 'pdf', 'size_mb': 10.0}
        ]
        
        result = self.tools.validate_documents(documents, 'SCH_TEST')
        
        self.assertTrue(result['success'])
        self.assertFalse(result['all_valid'])
        self.assertIn('too large', result['validation_results'][0]['issues'][0].lower())
    
    def test_validate_documents_missing_documents(self):
        """Test document validation with missing documents"""
        self.tools.schemes_table.get_item.return_value = {
            'Item': {
                'scheme_id': 'SCH_TEST',
                'required_documents': ['Aadhaar Card', 'Land Records', 'Bank Passbook']
            }
        }
        
        documents = [
            {'name': 'Aadhaar Card', 'format': 'pdf', 'size_mb': 1.0}
        ]
        
        result = self.tools.validate_documents(documents, 'SCH_TEST')
        
        self.assertTrue(result['success'])
        self.assertFalse(result['all_valid'])
        self.assertEqual(len(result['missing_documents']), 2)
        self.assertIn('Land Records', result['missing_documents'])
        self.assertIn('Bank Passbook', result['missing_documents'])
    
    def test_submit_application_success(self):
        """Test successful application submission"""
        # Mock scheme data
        self.tools.schemes_table.get_item.return_value = {
            'Item': {
                'scheme_id': 'SCH_TEST',
                'scheme_name': 'Test Scheme',
                'required_documents': ['Aadhaar Card']
            }
        }
        
        # Mock validation to return valid
        with patch.object(self.tools, 'validate_documents') as mock_validate:
            mock_validate.return_value = {'success': True, 'all_valid': True}
            
            application_data = {
                'personal_info': {'name': 'Test Farmer'},
                'documents': [{'name': 'Aadhaar Card', 'format': 'pdf', 'size_mb': 1.0}]
            }
            
            result = self.tools.submit_application('user_123', 'SCH_TEST', application_data)
            
            self.assertTrue(result['success'])
            self.assertIn('application_id', result)
            self.assertIn('tracking_number', result)
            self.assertEqual(result['status'], 'submitted')
            self.assertIn('receipt', result)
    
    def test_submit_application_validation_failed(self):
        """Test application submission with validation failure"""
        # Mock validation to return invalid
        with patch.object(self.tools, 'validate_documents') as mock_validate:
            mock_validate.return_value = {'success': True, 'all_valid': False}
            
            application_data = {
                'documents': [{'name': 'Invalid Doc', 'format': 'txt', 'size_mb': 1.0}]
            }
            
            result = self.tools.submit_application('user_123', 'SCH_TEST', application_data)
            
            self.assertFalse(result['success'])
            self.assertIn('validation failed', result['error'].lower())
    
    def test_track_application_status_success(self):
        """Test successful status tracking"""
        # Mock application data
        self.tools.applications_table.get_item.return_value = {
            'Item': {
                'application_id': 'APP_123',
                'tracking_number': 'RISE-1234-5678',
                'scheme_name': 'Test Scheme',
                'status': 'under_review',
                'submission_timestamp': 1700000000,
                'last_updated': 1700100000,
                'status_history': [
                    {'status': 'submitted', 'timestamp': 1700000000, 'notes': 'Submitted'},
                    {'status': 'under_review', 'timestamp': 1700100000, 'notes': 'Under review'}
                ]
            }
        }
        
        result = self.tools.track_application_status('APP_123')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['application_id'], 'APP_123')
        self.assertEqual(result['current_status'], 'under_review')
        self.assertEqual(result['progress_percentage'], 40)
        self.assertIn('status_timeline', result)
        self.assertEqual(len(result['status_timeline']), 2)
    
    def test_track_application_status_not_found(self):
        """Test status tracking with non-existent application"""
        self.tools.applications_table.get_item.return_value = {}
        
        result = self.tools.track_application_status('INVALID_APP')
        
        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'].lower())
    
    def test_send_application_notification_success(self):
        """Test successful notification sending"""
        # Mock user profile
        self.tools.user_profiles_table.get_item.return_value = {
            'Item': {
                'user_id': 'user_123',
                'phone_number': '+919876543210',
                'preferences': {'language': 'hi'}
            }
        }
        
        # Mock application
        self.tools.applications_table.get_item.return_value = {
            'Item': {
                'application_id': 'APP_123',
                'tracking_number': 'RISE-1234-5678',
                'scheme_name': 'Test Scheme',
                'status': 'approved'
            }
        }
        
        result = self.tools.send_application_notification(
            'user_123', 'APP_123', 'submission_confirmation'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['notification_type'], 'submission_confirmation')
        self.assertIn('message', result)
    
    def test_generate_tracking_number(self):
        """Test tracking number generation"""
        app_id = 'APP_ABCD1234EFGH'
        tracking_number = self.tools._generate_tracking_number(app_id)
        
        self.assertTrue(tracking_number.startswith('RISE-'))
        self.assertEqual(len(tracking_number), 14)  # RISE-XXXX-XXXX
    
    def test_get_next_action(self):
        """Test next action generation"""
        actions = {
            'submitted': self.tools._get_next_action('submitted'),
            'under_review': self.tools._get_next_action('under_review'),
            'approved': self.tools._get_next_action('approved'),
            'rejected': self.tools._get_next_action('rejected')
        }
        
        for status, action in actions.items():
            self.assertIsInstance(action, str)
            self.assertGreater(len(action), 0)
    
    def test_wizard_steps_generation(self):
        """Test wizard steps generation"""
        scheme = {
            'scheme_name': 'Test Scheme',
            'category': 'subsidies',
            'required_documents': ['Aadhaar Card', 'Bank Passbook']
        }
        
        user_profile = {
            'name': 'Test Farmer',
            'farm_details': {'land_size': 2.0}
        }
        
        steps = self.tools._generate_wizard_steps(scheme, user_profile, 'hi')
        
        self.assertIsInstance(steps, list)
        self.assertGreater(len(steps), 0)
        
        # Check step structure
        for step in steps:
            self.assertIn('step_number', step)
            self.assertIn('title', step)
            self.assertIn('description', step)
            self.assertIn('instructions', step)
            self.assertIn('action_required', step)
            self.assertIn('estimated_time_minutes', step)
    
    def test_document_format_validation(self):
        """Test individual document format validation"""
        # Valid document
        valid_doc = {
            'name': 'Aadhaar Card',
            'format': 'pdf',
            'size_mb': 1.5
        }
        
        result = self.tools._validate_document_format(valid_doc, 'Aadhaar Card')
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['issues']), 0)
        
        # Invalid format
        invalid_format_doc = {
            'name': 'Aadhaar Card',
            'format': 'txt',
            'size_mb': 1.0
        }
        
        result = self.tools._validate_document_format(invalid_format_doc, 'Aadhaar Card')
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['issues']), 0)
        
        # Oversized file
        oversized_doc = {
            'name': 'Aadhaar Card',
            'format': 'pdf',
            'size_mb': 10.0
        }
        
        result = self.tools._validate_document_format(oversized_doc, 'Aadhaar Card')
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['issues']), 0)


class TestApplicationWorkflow(unittest.TestCase):
    """Integration tests for complete application workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tools = SchemeApplicationTools(region='us-east-1')
        
        # Mock AWS clients
        self.tools.dynamodb = Mock()
        self.tools.bedrock = Mock()
        self.tools.translate = Mock()
        self.tools.polly = Mock()
        self.tools.sns = Mock()
        
        # Mock tables
        self.tools.applications_table = Mock()
        self.tools.schemes_table = Mock()
        self.tools.user_profiles_table = Mock()
    
    def test_complete_application_workflow(self):
        """Test complete application workflow from wizard to submission"""
        user_id = 'user_123'
        scheme_id = 'SCH_TEST'
        
        # Step 1: Generate wizard
        self.tools.schemes_table.get_item.return_value = {
            'Item': {
                'scheme_id': scheme_id,
                'scheme_name': 'Test Scheme',
                'category': 'subsidies',
                'benefit_amount': Decimal('5000'),
                'required_documents': ['Aadhaar Card', 'Bank Passbook']
            }
        }
        
        self.tools.user_profiles_table.get_item.return_value = {
            'Item': {
                'user_id': user_id,
                'name': 'Test Farmer'
            }
        }
        
        wizard_result = self.tools.generate_application_wizard(user_id, scheme_id, 'hi')
        self.assertTrue(wizard_result['success'])
        
        # Step 2: Validate documents
        documents = [
            {'name': 'Aadhaar Card', 'format': 'pdf', 'size_mb': 1.5},
            {'name': 'Bank Passbook', 'format': 'jpg', 'size_mb': 1.0}
        ]
        
        validation_result = self.tools.validate_documents(documents, scheme_id)
        self.assertTrue(validation_result['success'])
        self.assertTrue(validation_result['all_valid'])
        
        # Step 3: Submit application
        with patch.object(self.tools, 'validate_documents') as mock_validate:
            mock_validate.return_value = {'success': True, 'all_valid': True}
            
            application_data = {
                'personal_info': {'name': 'Test Farmer'},
                'documents': documents
            }
            
            submission_result = self.tools.submit_application(user_id, scheme_id, application_data)
            self.assertTrue(submission_result['success'])
            
            application_id = submission_result['application_id']
            
            # Step 4: Track status
            self.tools.applications_table.get_item.return_value = {
                'Item': {
                    'application_id': application_id,
                    'tracking_number': 'RISE-1234-5678',
                    'scheme_name': 'Test Scheme',
                    'status': 'submitted',
                    'submission_timestamp': 1700000000,
                    'last_updated': 1700000000,
                    'status_history': [
                        {'status': 'submitted', 'timestamp': 1700000000, 'notes': 'Submitted'}
                    ]
                }
            }
            
            status_result = self.tools.track_application_status(application_id)
            self.assertTrue(status_result['success'])
            self.assertEqual(status_result['current_status'], 'submitted')


if __name__ == '__main__':
    unittest.main()
