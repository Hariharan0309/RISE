"""
Unit tests for security hardening components
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.security_hardening import (
    FieldLevelEncryption,
    DynamoDBEncryption,
    AuditLogger,
    RateLimiter,
    DataAnonymization,
    ConsentManagement,
    DataPortability
)


class TestFieldLevelEncryption:
    """Test field-level encryption functionality"""
    
    @patch('infrastructure.security_hardening.boto3')
    def test_encrypt_pii_data(self, mock_boto3):
        """Test PII data encryption"""
        # Mock KMS client
        mock_kms = Mock()
        mock_kms.generate_data_key.return_value = {
            'Plaintext': b'0' * 32,
            'CiphertextBlob': b'encrypted_key'
        }
        mock_boto3.client.return_value = mock_kms
        
        encryption = FieldLevelEncryption()
        encryption.key_id = 'test-key-id'
        
        user_data = {
            'user_id': 'test123',
            'phone_number': '+919876543210',
            'name': 'Test User',
            'location': {
                'state': 'Test State',
                'coordinates': '28.6139,77.2090'
            }
        }
        
        encrypted = encryption.encrypt_pii_data(user_data)
        
        # Verify sensitive fields are encrypted
        assert encrypted['phone_number'] != user_data['phone_number']
        assert encrypted['name'] != user_data['name']
        assert encrypted['location']['coordinates'] != user_data['location']['coordinates']
        assert '_encrypted_key' in encrypted
        assert '_encryption_version' in encrypted
    
    @patch('infrastructure.security_hardening.boto3')
    def test_decrypt_pii_data(self, mock_boto3):
        """Test PII data decryption"""
        # Mock KMS client
        mock_kms = Mock()
        mock_kms.generate_data_key.return_value = {
            'Plaintext': b'0' * 32,
            'CiphertextBlob': b'encrypted_key'
        }
        mock_kms.decrypt.return_value = {
            'Plaintext': b'0' * 32
        }
        mock_boto3.client.return_value = mock_kms
        
        encryption = FieldLevelEncryption()
        encryption.key_id = 'test-key-id'
        
        original_data = {
            'user_id': 'test123',
            'phone_number': '+919876543210',
            'name': 'Test User'
        }
        
        # Encrypt then decrypt
        encrypted = encryption.encrypt_pii_data(original_data)
        decrypted = encryption.decrypt_pii_data(encrypted)
        
        # Verify decryption works
        assert decrypted['phone_number'] == original_data['phone_number']
        assert decrypted['name'] == original_data['name']
        assert '_encrypted_key' not in decrypted


class TestAuditLogger:
    """Test audit logging functionality"""
    
    @patch('infrastructure.security_hardening.boto3')
    def test_log_data_access(self, mock_boto3):
        """Test data access logging"""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        mock_boto3.client.return_value = Mock()
        
        audit_logger = AuditLogger()
        
        audit_logger.log_data_access(
            user_id='test123',
            action='READ',
            resource_type='UserProfile',
            resource_id='profile123',
            ip_address='192.168.1.1',
            user_agent='TestAgent',
            data_accessed=['name', 'phone_number']
        )
        
        # Verify DynamoDB put_item was called
        assert mock_table.put_item.called
        call_args = mock_table.put_item.call_args[1]
        item = call_args['Item']
        
        assert item['user_id'] == 'test123'
        assert item['action'] == 'READ'
        assert item['resource_type'] == 'UserProfile'
        assert item['compliance_flags']['pii_accessed'] == True
    
    @patch('infrastructure.security_hardening.boto3')
    def test_log_consent_change(self, mock_boto3):
        """Test consent change logging"""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        mock_boto3.client.return_value = Mock()
        
        audit_logger = AuditLogger()
        
        audit_logger.log_consent_change(
            user_id='test123',
            consent_type='data_collection',
            granted=True,
            ip_address='192.168.1.1'
        )
        
        assert mock_table.put_item.called
        call_args = mock_table.put_item.call_args[1]
        item = call_args['Item']
        
        assert item['action'] == 'CONSENT_CHANGE'
        assert item['consent_type'] == 'data_collection'
        assert item['consent_granted'] == True


class TestRateLimiter:
    """Test rate limiting functionality"""
    
    @patch('infrastructure.security_hardening.boto3')
    def test_rate_limit_allowed(self, mock_boto3):
        """Test rate limit allows requests within limit"""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_table.get_item.return_value = {}  # No existing record
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        mock_boto3.client.return_value = Mock()
        
        rate_limiter = RateLimiter()
        
        result = rate_limiter.check_rate_limit(
            identifier='test123',
            limit_type='api_call',
            max_requests=10,
            window_seconds=60
        )
        
        assert result['allowed'] == True
        assert result['current_count'] == 1
        assert result['remaining'] == 9
    
    @patch('infrastructure.security_hardening.boto3')
    def test_rate_limit_exceeded(self, mock_boto3):
        """Test rate limit blocks requests over limit"""
        mock_dynamodb = Mock()
        mock_table = Mock()
        
        # Simulate existing requests at limit
        current_time = int(time.time())
        existing_requests = [current_time - i for i in range(10)]
        
        mock_table.get_item.return_value = {
            'Item': {
                'limit_key': 'test123:api_call',
                'requests': existing_requests
            }
        }
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        mock_boto3.client.return_value = Mock()
        
        rate_limiter = RateLimiter()
        
        result = rate_limiter.check_rate_limit(
            identifier='test123',
            limit_type='api_call',
            max_requests=10,
            window_seconds=60
        )
        
        assert result['allowed'] == False
        assert result['reason'] == 'rate_limit_exceeded'
        assert 'retry_after' in result


class TestDataAnonymization:
    """Test data anonymization functionality"""
    
    def test_anonymize_user_id(self):
        """Test user ID anonymization"""
        anonymizer = DataAnonymization()
        
        user_id = 'test123'
        anon_id = anonymizer.anonymize_user_id(user_id)
        
        assert anon_id.startswith('anon_')
        assert len(anon_id) == 21  # 'anon_' + 16 hex chars
        
        # Same input should produce same output
        anon_id2 = anonymizer.anonymize_user_id(user_id)
        assert anon_id == anon_id2
    
    def test_anonymize_location(self):
        """Test location anonymization"""
        anonymizer = DataAnonymization()
        
        coordinates = '28.6139,77.2090'
        anon_coords = anonymizer.anonymize_location(coordinates, precision_km=10)
        
        # Verify coordinates are rounded
        assert anon_coords != coordinates
        lat, lon = map(float, anon_coords.split(','))
        assert abs(lat - 28.6139) < 1  # Within reasonable range
        assert abs(lon - 77.2090) < 1
    
    def test_anonymize_for_analytics(self):
        """Test full data anonymization for analytics"""
        anonymizer = DataAnonymization()
        
        user_data = {
            'user_id': 'test123',
            'location': {
                'state': 'Test State',
                'district': 'Test District',
                'coordinates': '28.6139,77.2090'
            },
            'farm_details': {
                'land_size': 3.5,
                'crops': ['wheat', 'rice']
            },
            'preferences': {
                'language': 'hindi'
            }
        }
        
        anonymized = anonymizer.anonymize_for_analytics(user_data)
        
        assert 'user_id_hash' in anonymized
        assert anonymized['user_id_hash'].startswith('anon_')
        assert anonymized['state'] == 'Test State'
        assert anonymized['land_size_bucket'] == '2-5_acres'
        assert anonymized['crop_types'] == ['wheat', 'rice']
        assert 'anonymized_at' in anonymized


class TestConsentManagement:
    """Test consent management functionality"""
    
    @patch('infrastructure.security_hardening.boto3')
    @patch('infrastructure.security_hardening.AuditLogger')
    def test_record_consent(self, mock_audit_logger, mock_boto3):
        """Test consent recording"""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        
        consent_mgmt = ConsentManagement()
        
        result = consent_mgmt.record_consent(
            user_id='test123',
            consent_type='data_collection',
            granted=True,
            ip_address='192.168.1.1',
            consent_text='I agree to data collection'
        )
        
        assert result['status'] == 'recorded'
        assert 'consent_id' in result
        assert mock_table.put_item.called
    
    @patch('infrastructure.security_hardening.boto3')
    @patch('infrastructure.security_hardening.AuditLogger')
    def test_check_consent(self, mock_audit_logger, mock_boto3):
        """Test consent checking"""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_table.query.return_value = {
            'Items': [
                {
                    'consent_type': 'data_collection',
                    'granted': True
                }
            ]
        }
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        
        consent_mgmt = ConsentManagement()
        
        has_consent = consent_mgmt.check_consent('test123', 'data_collection')
        assert has_consent == True
        
        no_consent = consent_mgmt.check_consent('test123', 'marketing')
        assert no_consent == False


class TestDataPortability:
    """Test data portability functionality"""
    
    @patch('infrastructure.security_hardening.boto3')
    @patch('infrastructure.security_hardening.AuditLogger')
    def test_export_user_data(self, mock_audit_logger, mock_boto3):
        """Test user data export"""
        mock_dynamodb = Mock()
        mock_s3 = Mock()
        
        # Mock DynamoDB responses
        mock_table = Mock()
        mock_table.get_item.return_value = {'Item': {'user_id': 'test123'}}
        mock_table.query.return_value = {'Items': []}
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock S3 responses
        mock_s3.put_object.return_value = {}
        mock_s3.generate_presigned_url.return_value = 'https://s3.amazonaws.com/export.json'
        
        mock_boto3.resource.return_value = mock_dynamodb
        mock_boto3.client.return_value = mock_s3
        
        data_portability = DataPortability()
        
        result = data_portability.export_user_data('test123')
        
        assert result['status'] == 'exported'
        assert 'download_url' in result
        assert result['expires_in'] == '7 days'
        assert mock_s3.put_object.called
    
    @patch('infrastructure.security_hardening.boto3')
    @patch('infrastructure.security_hardening.AuditLogger')
    def test_delete_user_data(self, mock_audit_logger, mock_boto3):
        """Test user data deletion"""
        mock_dynamodb = Mock()
        mock_s3 = Mock()
        
        # Mock DynamoDB responses
        mock_table = Mock()
        mock_table.query.return_value = {'Items': [{'user_id': 'test123'}]}
        mock_table.key_schema = [{'AttributeName': 'user_id'}]
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock S3 responses
        mock_s3.list_objects_v2.return_value = {
            'Contents': [{'Key': 'users/test123/file1.jpg'}]
        }
        mock_s3.delete_objects.return_value = {}
        
        mock_boto3.resource.return_value = mock_dynamodb
        mock_boto3.client.return_value = mock_s3
        
        data_portability = DataPortability()
        
        result = data_portability.delete_user_data('test123', 'user_requested')
        
        assert result['user_id'] == 'test123'
        assert result['reason'] == 'user_requested'
        assert len(result['deleted_items']) > 0


def test_integration_encryption_and_audit():
    """Integration test for encryption with audit logging"""
    with patch('infrastructure.security_hardening.boto3') as mock_boto3:
        # Setup mocks
        mock_kms = Mock()
        mock_kms.generate_data_key.return_value = {
            'Plaintext': b'0' * 32,
            'CiphertextBlob': b'encrypted_key'
        }
        
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        mock_boto3.client.return_value = mock_kms
        mock_boto3.resource.return_value = mock_dynamodb
        
        # Test workflow
        encryption = FieldLevelEncryption()
        encryption.key_id = 'test-key-id'
        audit_logger = AuditLogger()
        
        user_data = {
            'user_id': 'test123',
            'phone_number': '+919876543210',
            'name': 'Test User'
        }
        
        # Encrypt data
        encrypted = encryption.encrypt_pii_data(user_data)
        
        # Log access
        audit_logger.log_data_access(
            user_id='test123',
            action='WRITE',
            resource_type='UserProfile',
            resource_id='test123',
            ip_address='192.168.1.1',
            user_agent='TestAgent',
            data_accessed=['phone_number', 'name']
        )
        
        # Verify both operations completed
        assert encrypted['phone_number'] != user_data['phone_number']
        assert mock_table.put_item.called


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
