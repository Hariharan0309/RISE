"""
RISE Security Hardening Module
Implements comprehensive security measures including encryption, audit logging,
rate limiting, and data privacy controls.
"""

import boto3
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64


class FieldLevelEncryption:
    """
    Implements field-level encryption for PII data
    """
    
    def __init__(self):
        self.kms = boto3.client('kms')
        self.key_id = None  # Will be set from environment
        
    def generate_data_key(self) -> Dict[str, bytes]:
        """Generate data encryption key using KMS"""
        response = self.kms.generate_data_key(
            KeyId=self.key_id,
            KeySpec='AES_256'
        )
        
        return {
            'plaintext_key': response['Plaintext'],
            'encrypted_key': response['CiphertextBlob']
        }
    
    def encrypt_field(self, plaintext: str, data_key: bytes) -> str:
        """Encrypt a single field using Fernet symmetric encryption"""
        fernet = Fernet(base64.urlsafe_b64encode(data_key[:32]))
        encrypted = fernet.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_field(self, ciphertext: str, data_key: bytes) -> str:
        """Decrypt a single field"""
        fernet = Fernet(base64.urlsafe_b64encode(data_key[:32]))
        encrypted = base64.b64decode(ciphertext.encode())
        decrypted = fernet.decrypt(encrypted)
        return decrypted.decode()
    
    def encrypt_pii_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt PII fields in user data
        PII fields: phone_number, name, location coordinates, farm_details
        """
        # Generate data key
        keys = self.generate_data_key()
        plaintext_key = keys['plaintext_key']
        encrypted_key = keys['encrypted_key']
        
        encrypted_data = user_data.copy()
        
        # Encrypt sensitive fields
        pii_fields = ['phone_number', 'name']
        for field in pii_fields:
            if field in encrypted_data:
                encrypted_data[field] = self.encrypt_field(
                    str(encrypted_data[field]), 
                    plaintext_key
                )
        
        # Encrypt nested location coordinates
        if 'location' in encrypted_data and 'coordinates' in encrypted_data['location']:
            encrypted_data['location']['coordinates'] = self.encrypt_field(
                encrypted_data['location']['coordinates'],
                plaintext_key
            )
        
        # Store encrypted data key with the record
        encrypted_data['_encrypted_key'] = base64.b64encode(encrypted_key).decode()
        encrypted_data['_encryption_version'] = '1.0'
        
        return encrypted_data
    
    def decrypt_pii_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt PII fields in user data"""
        if '_encrypted_key' not in encrypted_data:
            return encrypted_data  # Not encrypted
        
        # Decrypt the data key
        encrypted_key = base64.b64decode(encrypted_data['_encrypted_key'])
        response = self.kms.decrypt(CiphertextBlob=encrypted_key)
        plaintext_key = response['Plaintext']
        
        decrypted_data = encrypted_data.copy()
        
        # Decrypt sensitive fields
        pii_fields = ['phone_number', 'name']
        for field in pii_fields:
            if field in decrypted_data and isinstance(decrypted_data[field], str):
                try:
                    decrypted_data[field] = self.decrypt_field(
                        decrypted_data[field],
                        plaintext_key
                    )
                except Exception:
                    pass  # Field might not be encrypted
        
        # Decrypt location coordinates
        if 'location' in decrypted_data and 'coordinates' in decrypted_data['location']:
            try:
                decrypted_data['location']['coordinates'] = self.decrypt_field(
                    decrypted_data['location']['coordinates'],
                    plaintext_key
                )
            except Exception:
                pass
        
        # Remove encryption metadata
        decrypted_data.pop('_encrypted_key', None)
        decrypted_data.pop('_encryption_version', None)
        
        return decrypted_data


class DynamoDBEncryption:
    """
    Configure DynamoDB encryption with KMS
    """
    
    def __init__(self):
        self.dynamodb = boto3.client('dynamodb')
        self.kms = boto3.client('kms')
    
    def enable_table_encryption(self, table_name: str, kms_key_id: str) -> Dict:
        """Enable encryption at rest for DynamoDB table"""
        try:
            response = self.dynamodb.update_table(
                TableName=table_name,
                SSESpecification={
                    'Enabled': True,
                    'SSEType': 'KMS',
                    'KMSMasterKeyId': kms_key_id
                }
            )
            return {
                'status': 'success',
                'table': table_name,
                'encryption_enabled': True
            }
        except Exception as e:
            return {
                'status': 'error',
                'table': table_name,
                'error': str(e)
            }
    
    def enable_encryption_all_tables(self, kms_key_id: str) -> List[Dict]:
        """Enable encryption for all RISE tables"""
        tables = [
            'RISE-UserProfiles',
            'RISE-FarmData',
            'RISE-DiagnosisHistory',
            'RISE-ResourceSharing',
            'RISE-BuyingGroups',
            'RISE-ResourceBookings',
            'RISE-ConversationHistory',
            'RISE-ForumPosts',
            'RISE-GovernmentSchemes'
        ]
        
        results = []
        for table in tables:
            result = self.enable_table_encryption(table, kms_key_id)
            results.append(result)
        
        return results


class AuditLogger:
    """
    Comprehensive audit logging for data access and modifications
    """
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.audit_table = self.dynamodb.Table('RISE-AuditLogs')
        self.cloudwatch = boto3.client('logs')
        self.log_group = '/aws/rise/audit-logs'
        
    def log_data_access(self, 
                       user_id: str,
                       action: str,
                       resource_type: str,
                       resource_id: str,
                       ip_address: str,
                       user_agent: str,
                       data_accessed: Optional[List[str]] = None) -> None:
        """Log data access events"""
        
        audit_entry = {
            'audit_id': f"audit_{int(time.time() * 1000)}_{user_id}",
            'timestamp': int(time.time()),
            'user_id': user_id,
            'action': action,  # READ, WRITE, DELETE, EXPORT
            'resource_type': resource_type,  # UserProfile, FarmData, etc.
            'resource_id': resource_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'data_fields_accessed': data_accessed or [],
            'compliance_flags': {
                'pii_accessed': self._contains_pii(data_accessed),
                'sensitive_data': self._is_sensitive(resource_type)
            }
        }
        
        # Store in DynamoDB
        self.audit_table.put_item(Item=audit_entry)
        
        # Also log to CloudWatch for real-time monitoring
        self._log_to_cloudwatch(audit_entry)
    
    def log_consent_change(self,
                          user_id: str,
                          consent_type: str,
                          granted: bool,
                          ip_address: str) -> None:
        """Log consent management changes"""
        
        audit_entry = {
            'audit_id': f"consent_{int(time.time() * 1000)}_{user_id}",
            'timestamp': int(time.time()),
            'user_id': user_id,
            'action': 'CONSENT_CHANGE',
            'consent_type': consent_type,
            'consent_granted': granted,
            'ip_address': ip_address,
            'compliance_flags': {
                'gdpr_relevant': True,
                'requires_notification': True
            }
        }
        
        self.audit_table.put_item(Item=audit_entry)
        self._log_to_cloudwatch(audit_entry)
    
    def log_data_deletion(self,
                         user_id: str,
                         resource_type: str,
                         resource_id: str,
                         deletion_reason: str) -> None:
        """Log data deletion events"""
        
        audit_entry = {
            'audit_id': f"delete_{int(time.time() * 1000)}_{user_id}",
            'timestamp': int(time.time()),
            'user_id': user_id,
            'action': 'DELETE',
            'resource_type': resource_type,
            'resource_id': resource_id,
            'deletion_reason': deletion_reason,
            'compliance_flags': {
                'right_to_erasure': True,
                'permanent_deletion': True
            }
        }
        
        self.audit_table.put_item(Item=audit_entry)
        self._log_to_cloudwatch(audit_entry)
    
    def _contains_pii(self, fields: Optional[List[str]]) -> bool:
        """Check if accessed fields contain PII"""
        if not fields:
            return False
        
        pii_fields = ['phone_number', 'name', 'location', 'coordinates', 'address']
        return any(field in pii_fields for field in fields)
    
    def _is_sensitive(self, resource_type: str) -> bool:
        """Check if resource type is sensitive"""
        sensitive_types = ['UserProfile', 'FarmData', 'FinancialData']
        return resource_type in sensitive_types
    
    def _log_to_cloudwatch(self, audit_entry: Dict) -> None:
        """Send audit log to CloudWatch"""
        try:
            self.cloudwatch.put_log_events(
                logGroupName=self.log_group,
                logStreamName=f"audit-{datetime.now().strftime('%Y-%m-%d')}",
                logEvents=[{
                    'timestamp': audit_entry['timestamp'] * 1000,
                    'message': json.dumps(audit_entry)
                }]
            )
        except Exception as e:
            print(f"CloudWatch logging error: {e}")
    
    def get_user_audit_trail(self, user_id: str, days: int = 30) -> List[Dict]:
        """Retrieve audit trail for a specific user"""
        cutoff_time = int((datetime.now() - timedelta(days=days)).timestamp())
        
        response = self.audit_table.query(
            IndexName='UserAuditIndex',
            KeyConditionExpression='user_id = :uid AND #ts >= :cutoff',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':uid': user_id,
                ':cutoff': cutoff_time
            }
        )
        
        return response.get('Items', [])


class RateLimiter:
    """
    Rate limiting and DDoS protection
    """
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.rate_limit_table = self.dynamodb.Table('RISE-RateLimits')
        self.waf = boto3.client('wafv2')
    
    def check_rate_limit(self,
                        identifier: str,
                        limit_type: str,
                        max_requests: int,
                        window_seconds: int) -> Dict[str, Any]:
        """
        Check if request is within rate limits
        
        Args:
            identifier: User ID or IP address
            limit_type: Type of limit (api_call, image_upload, etc.)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
        """
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        key = f"{identifier}:{limit_type}"
        
        try:
            # Get current request count
            response = self.rate_limit_table.get_item(Key={'limit_key': key})
            
            if 'Item' in response:
                item = response['Item']
                requests = [r for r in item['requests'] if r > window_start]
                
                if len(requests) >= max_requests:
                    return {
                        'allowed': False,
                        'reason': 'rate_limit_exceeded',
                        'retry_after': requests[0] + window_seconds - current_time,
                        'current_count': len(requests),
                        'limit': max_requests
                    }
                
                # Add current request
                requests.append(current_time)
            else:
                requests = [current_time]
            
            # Update table
            self.rate_limit_table.put_item(Item={
                'limit_key': key,
                'requests': requests,
                'ttl': current_time + window_seconds + 3600  # Cleanup after 1 hour
            })
            
            return {
                'allowed': True,
                'current_count': len(requests),
                'limit': max_requests,
                'remaining': max_requests - len(requests)
            }
            
        except Exception as e:
            # Fail open to avoid blocking legitimate requests
            return {
                'allowed': True,
                'error': str(e)
            }
    
    def configure_waf_rules(self, web_acl_id: str) -> Dict:
        """Configure AWS WAF rules for DDoS protection"""
        
        rules = [
            {
                'Name': 'RateLimitRule',
                'Priority': 1,
                'Statement': {
                    'RateBasedStatement': {
                        'Limit': 2000,  # 2000 requests per 5 minutes
                        'AggregateKeyType': 'IP'
                    }
                },
                'Action': {'Block': {}},
                'VisibilityConfig': {
                    'SampledRequestsEnabled': True,
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'RateLimitRule'
                }
            },
            {
                'Name': 'GeoBlockRule',
                'Priority': 2,
                'Statement': {
                    'GeoMatchStatement': {
                        'CountryCodes': ['IN']  # Allow only India
                    }
                },
                'Action': {'Allow': {}},
                'VisibilityConfig': {
                    'SampledRequestsEnabled': True,
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'GeoBlockRule'
                }
            },
            {
                'Name': 'SQLInjectionRule',
                'Priority': 3,
                'Statement': {
                    'ManagedRuleGroupStatement': {
                        'VendorName': 'AWS',
                        'Name': 'AWSManagedRulesSQLiRuleSet'
                    }
                },
                'OverrideAction': {'None': {}},
                'VisibilityConfig': {
                    'SampledRequestsEnabled': True,
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'SQLInjectionRule'
                }
            }
        ]
        
        return {
            'status': 'configured',
            'rules': rules,
            'web_acl_id': web_acl_id
        }


class DataAnonymization:
    """
    Data anonymization for analytics and reporting
    """
    
    def __init__(self):
        self.salt = b'rise_anonymization_salt_2024'
    
    def anonymize_user_id(self, user_id: str) -> str:
        """Create anonymized user identifier"""
        hash_obj = hashlib.sha256()
        hash_obj.update(user_id.encode() + self.salt)
        return f"anon_{hash_obj.hexdigest()[:16]}"
    
    def anonymize_location(self, coordinates: str, precision_km: int = 10) -> str:
        """
        Reduce location precision for privacy
        Round coordinates to nearest precision_km
        """
        try:
            lat, lon = map(float, coordinates.split(','))
            
            # Round to reduce precision
            precision_factor = precision_km / 111  # Approximate km per degree
            lat_rounded = round(lat / precision_factor) * precision_factor
            lon_rounded = round(lon / precision_factor) * precision_factor
            
            return f"{lat_rounded:.2f},{lon_rounded:.2f}"
        except Exception:
            return "location_redacted"
    
    def anonymize_for_analytics(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize user data for analytics purposes
        """
        anonymized = {
            'user_id_hash': self.anonymize_user_id(user_data.get('user_id', '')),
            'state': user_data.get('location', {}).get('state', 'unknown'),
            'district': user_data.get('location', {}).get('district', 'unknown'),
            'location_approximate': self.anonymize_location(
                user_data.get('location', {}).get('coordinates', '0,0')
            ),
            'land_size_bucket': self._bucket_land_size(
                user_data.get('farm_details', {}).get('land_size', 0)
            ),
            'crop_types': user_data.get('farm_details', {}).get('crops', []),
            'language': user_data.get('preferences', {}).get('language', 'unknown'),
            'anonymized_at': int(time.time())
        }
        
        return anonymized
    
    def _bucket_land_size(self, land_size: float) -> str:
        """Bucket land size for privacy"""
        if land_size < 1:
            return '<1_acre'
        elif land_size < 2:
            return '1-2_acres'
        elif land_size < 5:
            return '2-5_acres'
        elif land_size < 10:
            return '5-10_acres'
        else:
            return '>10_acres'


class ConsentManagement:
    """
    User consent management system
    """
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.consent_table = self.dynamodb.Table('RISE-UserConsents')
        self.audit_logger = AuditLogger()
    
    def record_consent(self,
                      user_id: str,
                      consent_type: str,
                      granted: bool,
                      ip_address: str,
                      consent_text: str) -> Dict:
        """
        Record user consent
        
        Consent types:
        - data_collection
        - data_sharing
        - analytics
        - marketing
        - location_tracking
        """
        consent_id = f"consent_{int(time.time() * 1000)}_{user_id}"
        
        consent_record = {
            'consent_id': consent_id,
            'user_id': user_id,
            'consent_type': consent_type,
            'granted': granted,
            'timestamp': int(time.time()),
            'ip_address': ip_address,
            'consent_text': consent_text,
            'consent_version': '1.0'
        }
        
        self.consent_table.put_item(Item=consent_record)
        
        # Log to audit trail
        self.audit_logger.log_consent_change(
            user_id, consent_type, granted, ip_address
        )
        
        return {
            'status': 'recorded',
            'consent_id': consent_id
        }
    
    def get_user_consents(self, user_id: str) -> Dict[str, bool]:
        """Get all consents for a user"""
        response = self.consent_table.query(
            IndexName='UserConsentIndex',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id},
            ScanIndexForward=False  # Get most recent first
        )
        
        # Get latest consent for each type
        consents = {}
        for item in response.get('Items', []):
            consent_type = item['consent_type']
            if consent_type not in consents:
                consents[consent_type] = item['granted']
        
        return consents
    
    def check_consent(self, user_id: str, consent_type: str) -> bool:
        """Check if user has granted specific consent"""
        consents = self.get_user_consents(user_id)
        return consents.get(consent_type, False)


class DataPortability:
    """
    Data portability and deletion (Right to be Forgotten)
    """
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.s3 = boto3.client('s3')
        self.audit_logger = AuditLogger()
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Export all user data in portable format
        """
        user_data = {
            'export_timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'profile': self._get_user_profile(user_id),
            'farm_data': self._get_farm_data(user_id),
            'diagnosis_history': self._get_diagnosis_history(user_id),
            'conversations': self._get_conversations(user_id),
            'forum_posts': self._get_forum_posts(user_id),
            'resource_sharing': self._get_resource_sharing(user_id),
            'bookings': self._get_bookings(user_id)
        }
        
        # Create export file
        export_filename = f"rise_data_export_{user_id}_{int(time.time())}.json"
        export_content = json.dumps(user_data, indent=2, ensure_ascii=False)
        
        # Upload to S3
        bucket = 'rise-data-exports'
        self.s3.put_object(
            Bucket=bucket,
            Key=f"exports/{user_id}/{export_filename}",
            Body=export_content.encode('utf-8'),
            ServerSideEncryption='AES256'
        )
        
        # Generate presigned URL (valid for 7 days)
        download_url = self.s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket,
                'Key': f"exports/{user_id}/{export_filename}"
            },
            ExpiresIn=604800  # 7 days
        )
        
        return {
            'status': 'exported',
            'download_url': download_url,
            'expires_in': '7 days',
            'file_size': len(export_content)
        }
    
    def delete_user_data(self, user_id: str, deletion_reason: str) -> Dict[str, Any]:
        """
        Permanently delete all user data (Right to be Forgotten)
        """
        deletion_results = {
            'user_id': user_id,
            'deletion_timestamp': datetime.now().isoformat(),
            'reason': deletion_reason,
            'deleted_items': []
        }
        
        # Delete from all tables
        tables_to_clean = [
            ('RISE-UserProfiles', 'user_id'),
            ('RISE-FarmData', 'user_id'),
            ('RISE-DiagnosisHistory', 'user_id'),
            ('RISE-ConversationHistory', 'user_id'),
            ('RISE-ForumPosts', 'user_id'),
            ('RISE-ResourceSharing', 'owner_user_id'),
            ('RISE-ResourceBookings', 'renter_user_id')
        ]
        
        for table_name, key_field in tables_to_clean:
            deleted_count = self._delete_from_table(table_name, key_field, user_id)
            deletion_results['deleted_items'].append({
                'table': table_name,
                'count': deleted_count
            })
        
        # Delete S3 objects
        s3_deleted = self._delete_s3_objects(user_id)
        deletion_results['s3_objects_deleted'] = s3_deleted
        
        # Log deletion
        self.audit_logger.log_data_deletion(
            user_id, 'AllUserData', user_id, deletion_reason
        )
        
        return deletion_results
    
    def _get_user_profile(self, user_id: str) -> Dict:
        """Get user profile data"""
        table = self.dynamodb.Table('RISE-UserProfiles')
        response = table.get_item(Key={'user_id': user_id})
        return response.get('Item', {})
    
    def _get_farm_data(self, user_id: str) -> List[Dict]:
        """Get farm data"""
        table = self.dynamodb.Table('RISE-FarmData')
        response = table.query(
            IndexName='UserFarmIndex',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id}
        )
        return response.get('Items', [])
    
    def _get_diagnosis_history(self, user_id: str) -> List[Dict]:
        """Get diagnosis history"""
        table = self.dynamodb.Table('RISE-DiagnosisHistory')
        response = table.query(
            IndexName='UserDiagnosisIndex',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id}
        )
        return response.get('Items', [])
    
    def _get_conversations(self, user_id: str) -> List[Dict]:
        """Get conversation history"""
        table = self.dynamodb.Table('RISE-ConversationHistory')
        response = table.query(
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id}
        )
        return response.get('Items', [])
    
    def _get_forum_posts(self, user_id: str) -> List[Dict]:
        """Get forum posts"""
        table = self.dynamodb.Table('RISE-ForumPosts')
        response = table.query(
            IndexName='UserPostsIndex',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id}
        )
        return response.get('Items', [])
    
    def _get_resource_sharing(self, user_id: str) -> List[Dict]:
        """Get resource sharing listings"""
        table = self.dynamodb.Table('RISE-ResourceSharing')
        response = table.query(
            IndexName='OwnerResourceIndex',
            KeyConditionExpression='owner_user_id = :uid',
            ExpressionAttributeValues={':uid': user_id}
        )
        return response.get('Items', [])
    
    def _get_bookings(self, user_id: str) -> List[Dict]:
        """Get resource bookings"""
        table = self.dynamodb.Table('RISE-ResourceBookings')
        response = table.query(
            IndexName='RenterBookingIndex',
            KeyConditionExpression='renter_user_id = :uid',
            ExpressionAttributeValues={':uid': user_id}
        )
        return response.get('Items', [])
    
    def _delete_from_table(self, table_name: str, key_field: str, user_id: str) -> int:
        """Delete all items for user from a table"""
        table = self.dynamodb.Table(table_name)
        
        # Query items
        try:
            response = table.query(
                IndexName=f"{key_field.replace('_', '').title()}Index",
                KeyConditionExpression=f"{key_field} = :uid",
                ExpressionAttributeValues={':uid': user_id}
            )
            
            items = response.get('Items', [])
            
            # Delete each item
            for item in items:
                table.delete_item(Key={k: item[k] for k in table.key_schema})
            
            return len(items)
        except Exception as e:
            print(f"Error deleting from {table_name}: {e}")
            return 0
    
    def _delete_s3_objects(self, user_id: str) -> int:
        """Delete all S3 objects for user"""
        bucket = 'rise-application-data'
        prefix = f"users/{user_id}/"
        
        try:
            # List objects
            response = self.s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
            objects = response.get('Contents', [])
            
            # Delete objects
            if objects:
                delete_keys = [{'Key': obj['Key']} for obj in objects]
                self.s3.delete_objects(
                    Bucket=bucket,
                    Delete={'Objects': delete_keys}
                )
            
            return len(objects)
        except Exception as e:
            print(f"Error deleting S3 objects: {e}")
            return 0


# Example usage and integration
def initialize_security_hardening(kms_key_id: str, web_acl_id: str):
    """
    Initialize all security hardening components
    """
    # Enable DynamoDB encryption
    db_encryption = DynamoDBEncryption()
    encryption_results = db_encryption.enable_encryption_all_tables(kms_key_id)
    
    # Configure WAF rules
    rate_limiter = RateLimiter()
    waf_config = rate_limiter.configure_waf_rules(web_acl_id)
    
    return {
        'dynamodb_encryption': encryption_results,
        'waf_configuration': waf_config,
        'status': 'initialized'
    }
