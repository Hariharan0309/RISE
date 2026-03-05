# RISE Security Hardening Implementation

## Overview

This document describes the comprehensive security hardening implementation for the RISE platform, covering encryption, audit logging, rate limiting, DDoS protection, data anonymization, consent management, and data portability.

## Components

### 1. Field-Level Encryption

**Purpose:** Protect PII (Personally Identifiable Information) data at the application level.

**Implementation:**
- Uses AWS KMS for key management
- Fernet symmetric encryption for field-level encryption
- Encrypts sensitive fields: phone_number, name, location coordinates

**Usage:**
```python
from security_hardening import FieldLevelEncryption

encryption = FieldLevelEncryption()
encryption.key_id = 'your-kms-key-id'

# Encrypt user data
encrypted_data = encryption.encrypt_pii_data(user_data)

# Decrypt user data
decrypted_data = encryption.decrypt_pii_data(encrypted_data)
```

**Protected Fields:**
- `phone_number` - User contact information
- `name` - User full name
- `location.coordinates` - Precise GPS coordinates
- Additional PII fields as needed

### 2. DynamoDB Encryption with KMS

**Purpose:** Enable encryption at rest for all DynamoDB tables.

**Implementation:**
- Server-side encryption using AWS KMS
- Customer-managed keys for enhanced control
- Automatic encryption for all new items

**Tables Encrypted:**
- RISE-UserProfiles
- RISE-FarmData
- RISE-DiagnosisHistory
- RISE-ResourceSharing
- RISE-BuyingGroups
- RISE-ResourceBookings
- RISE-ConversationHistory
- RISE-ForumPosts
- RISE-GovernmentSchemes

**Setup:**
```python
from security_hardening import DynamoDBEncryption

db_encryption = DynamoDBEncryption()
results = db_encryption.enable_encryption_all_tables('your-kms-key-id')
```

### 3. Audit Logging

**Purpose:** Comprehensive logging of all data access and modifications for compliance.

**Implementation:**
- Dual logging: DynamoDB + CloudWatch Logs
- Tracks all data access, modifications, and deletions
- Includes consent changes and sensitive operations

**Logged Events:**
- Data access (READ operations)
- Data modifications (WRITE operations)
- Data deletions (DELETE operations)
- Consent changes
- Data exports
- Authentication events

**Usage:**
```python
from security_hardening import AuditLogger

audit_logger = AuditLogger()

# Log data access
audit_logger.log_data_access(
    user_id='user123',
    action='READ',
    resource_type='UserProfile',
    resource_id='profile123',
    ip_address='192.168.1.1',
    user_agent='Mozilla/5.0...',
    data_accessed=['name', 'phone_number']
)

# Log consent change
audit_logger.log_consent_change(
    user_id='user123',
    consent_type='data_collection',
    granted=True,
    ip_address='192.168.1.1'
)

# Retrieve audit trail
trail = audit_logger.get_user_audit_trail('user123', days=30)
```

**Audit Log Schema:**
```json
{
  "audit_id": "audit_1234567890_user123",
  "timestamp": 1234567890,
  "user_id": "user123",
  "action": "READ",
  "resource_type": "UserProfile",
  "resource_id": "profile123",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "data_fields_accessed": ["name", "phone_number"],
  "compliance_flags": {
    "pii_accessed": true,
    "sensitive_data": true
  }
}
```

### 4. Rate Limiting and DDoS Protection

**Purpose:** Prevent abuse and protect against DDoS attacks.

**Implementation:**
- Application-level rate limiting using DynamoDB
- AWS WAF rules for network-level protection
- Configurable limits per operation type

**Rate Limits:**
- API calls: 100 requests per minute per user
- Image uploads: 10 per hour per user
- Voice queries: 50 per hour per user
- Custom limits per endpoint

**Usage:**
```python
from security_hardening import RateLimiter

rate_limiter = RateLimiter()

# Check rate limit
result = rate_limiter.check_rate_limit(
    identifier='user123',
    limit_type='api_call',
    max_requests=100,
    window_seconds=60
)

if not result['allowed']:
    # Rate limit exceeded
    retry_after = result['retry_after']
    # Return 429 Too Many Requests
```

**WAF Rules:**
1. **Rate Limit Rule:** 2000 requests per 5 minutes per IP
2. **Geo Block Rule:** Allow only traffic from India
3. **SQL Injection Protection:** AWS Managed Rules
4. **XSS Protection:** AWS Managed Rules

**WAF Configuration:**
```python
rate_limiter.configure_waf_rules('your-web-acl-id')
```

### 5. Data Anonymization for Analytics

**Purpose:** Protect user privacy while enabling analytics and insights.

**Implementation:**
- Hash-based user ID anonymization
- Location precision reduction
- Data bucketing for sensitive fields

**Anonymization Techniques:**
- User IDs: SHA-256 hashing with salt
- Locations: Rounded to 10km precision
- Land size: Bucketed into ranges
- Timestamps: Rounded to day/week

**Usage:**
```python
from security_hardening import DataAnonymization

anonymizer = DataAnonymization()

# Anonymize user data
anonymized = anonymizer.anonymize_for_analytics(user_data)

# Anonymized output
{
  "user_id_hash": "anon_a1b2c3d4e5f6g7h8",
  "state": "Uttar Pradesh",
  "district": "Lucknow",
  "location_approximate": "26.85,80.95",
  "land_size_bucket": "2-5_acres",
  "crop_types": ["wheat", "rice"],
  "language": "hindi",
  "anonymized_at": 1234567890
}
```

### 6. Consent Management System

**Purpose:** Manage user consent for data collection and processing (GDPR/Privacy compliance).

**Implementation:**
- Granular consent types
- Versioned consent records
- Audit trail for all consent changes

**Consent Types:**
- `data_collection` - Basic data collection
- `data_sharing` - Sharing with third parties
- `analytics` - Usage analytics
- `marketing` - Marketing communications
- `location_tracking` - GPS location tracking

**Usage:**
```python
from security_hardening import ConsentManagement

consent_mgmt = ConsentManagement()

# Record consent
consent_mgmt.record_consent(
    user_id='user123',
    consent_type='data_collection',
    granted=True,
    ip_address='192.168.1.1',
    consent_text='I agree to data collection for farming assistance'
)

# Check consent
has_consent = consent_mgmt.check_consent('user123', 'analytics')

# Get all consents
consents = consent_mgmt.get_user_consents('user123')
```

**Consent Record Schema:**
```json
{
  "consent_id": "consent_1234567890_user123",
  "user_id": "user123",
  "consent_type": "data_collection",
  "granted": true,
  "timestamp": 1234567890,
  "ip_address": "192.168.1.1",
  "consent_text": "I agree to...",
  "consent_version": "1.0"
}
```

### 7. Data Portability and Deletion

**Purpose:** Enable users to export and delete their data (Right to be Forgotten).

**Implementation:**
- Complete data export in JSON format
- Secure deletion across all services
- Audit trail for all operations

**Data Export:**
```python
from security_hardening import DataPortability

data_portability = DataPortability()

# Export all user data
result = data_portability.export_user_data('user123')

# Returns:
{
  "status": "exported",
  "download_url": "https://s3.amazonaws.com/...",
  "expires_in": "7 days",
  "file_size": 1234567
}
```

**Exported Data Includes:**
- User profile
- Farm data
- Diagnosis history
- Conversation history
- Forum posts
- Resource sharing listings
- Booking history

**Data Deletion:**
```python
# Delete all user data
result = data_portability.delete_user_data(
    user_id='user123',
    deletion_reason='user_requested'
)

# Returns:
{
  "user_id": "user123",
  "deletion_timestamp": "2024-01-15T10:30:00",
  "reason": "user_requested",
  "deleted_items": [
    {"table": "RISE-UserProfiles", "count": 1},
    {"table": "RISE-FarmData", "count": 45},
    ...
  ],
  "s3_objects_deleted": 123
}
```

## Lambda Functions

### Security Lambda Handlers

**1. Data Access Handler**
- Endpoint: `/api/v1/data/{resource_type}/{resource_id}`
- Purpose: Log all data access with audit trail
- Authentication: Required

**2. Rate Limit Handler**
- Endpoint: `/api/v1/rate-limit/{limit_type}`
- Purpose: Check and enforce rate limits
- Returns: 429 if limit exceeded

**3. Consent Management Handler**
- Endpoint: `/api/v1/consent`
- Methods: GET (retrieve), POST (update)
- Purpose: Manage user consents

**4. Data Export Handler**
- Endpoint: `/api/v1/data/export`
- Method: POST
- Purpose: Export all user data
- Returns: Presigned S3 URL

**5. Data Deletion Handler**
- Endpoint: `/api/v1/data/delete`
- Method: DELETE
- Purpose: Permanently delete user data
- Requires: Confirmation token

**6. Anonymize Analytics Handler**
- Trigger: SQS queue
- Purpose: Anonymize data for analytics pipeline
- Batch processing

## Infrastructure Setup

### Required AWS Resources

**1. KMS Keys:**
```bash
# Create KMS key for encryption
aws kms create-key --description "RISE data encryption key"
```

**2. DynamoDB Tables:**
```bash
# Audit logs table
aws dynamodb create-table \
  --table-name RISE-AuditLogs \
  --attribute-definitions \
    AttributeName=audit_id,AttributeType=S \
    AttributeName=user_id,AttributeType=S \
    AttributeName=timestamp,AttributeType=N \
  --key-schema \
    AttributeName=audit_id,KeyType=HASH \
  --global-secondary-indexes \
    IndexName=UserAuditIndex,KeySchema=[{AttributeName=user_id,KeyType=HASH},{AttributeName=timestamp,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

# Rate limits table
aws dynamodb create-table \
  --table-name RISE-RateLimits \
  --attribute-definitions AttributeName=limit_key,AttributeType=S \
  --key-schema AttributeName=limit_key,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

# User consents table
aws dynamodb create-table \
  --table-name RISE-UserConsents \
  --attribute-definitions \
    AttributeName=consent_id,AttributeType=S \
    AttributeName=user_id,AttributeType=S \
  --key-schema AttributeName=consent_id,KeyType=HASH \
  --global-secondary-indexes \
    IndexName=UserConsentIndex,KeySchema=[{AttributeName=user_id,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

**3. S3 Buckets:**
```bash
# Data exports bucket
aws s3 mb s3://rise-data-exports
aws s3api put-bucket-encryption \
  --bucket rise-data-exports \
  --server-side-encryption-configuration \
    '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
```

**4. CloudWatch Log Groups:**
```bash
aws logs create-log-group --log-group-name /aws/rise/audit-logs
```

**5. WAF Web ACL:**
```bash
# Create WAF Web ACL (use AWS Console or CloudFormation)
```

## CDK Infrastructure Code

Add to `rise_stack.py`:

```python
from aws_cdk import (
    aws_kms as kms,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_wafv2 as waf,
    aws_logs as logs
)

# KMS Key
encryption_key = kms.Key(
    self, "RISEEncryptionKey",
    description="RISE data encryption key",
    enable_key_rotation=True
)

# Audit Logs Table
audit_table = dynamodb.Table(
    self, "AuditLogs",
    table_name="RISE-AuditLogs",
    partition_key=dynamodb.Attribute(
        name="audit_id",
        type=dynamodb.AttributeType.STRING
    ),
    encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
    encryption_key=encryption_key,
    point_in_time_recovery=True
)

audit_table.add_global_secondary_index(
    index_name="UserAuditIndex",
    partition_key=dynamodb.Attribute(
        name="user_id",
        type=dynamodb.AttributeType.STRING
    ),
    sort_key=dynamodb.Attribute(
        name="timestamp",
        type=dynamodb.AttributeType.NUMBER
    )
)

# Data Exports Bucket
exports_bucket = s3.Bucket(
    self, "DataExports",
    bucket_name="rise-data-exports",
    encryption=s3.BucketEncryption.S3_MANAGED,
    versioned=True,
    lifecycle_rules=[
        s3.LifecycleRule(
            expiration=Duration.days(30)
        )
    ]
)

# CloudWatch Log Group
log_group = logs.LogGroup(
    self, "AuditLogGroup",
    log_group_name="/aws/rise/audit-logs",
    retention=logs.RetentionDays.ONE_YEAR
)
```

## Security Best Practices

### 1. Encryption
- ✅ All data encrypted at rest (DynamoDB, S3)
- ✅ All data encrypted in transit (TLS 1.2+)
- ✅ Field-level encryption for PII
- ✅ KMS key rotation enabled

### 2. Access Control
- ✅ IAM roles with least privilege
- ✅ API Gateway authorization
- ✅ Resource-based policies
- ✅ VPC endpoints for private access

### 3. Monitoring
- ✅ CloudWatch alarms for security events
- ✅ Audit logging for all operations
- ✅ Real-time alerting for anomalies
- ✅ Regular security audits

### 4. Compliance
- ✅ GDPR-compliant consent management
- ✅ Right to be forgotten implementation
- ✅ Data portability support
- ✅ Audit trail for compliance

### 5. DDoS Protection
- ✅ AWS WAF rules
- ✅ Rate limiting per user/IP
- ✅ CloudFront for DDoS mitigation
- ✅ AWS Shield Standard

## Testing

### Unit Tests

```python
# Test encryption
def test_field_encryption():
    encryption = FieldLevelEncryption()
    encryption.key_id = 'test-key-id'
    
    user_data = {
        'user_id': 'test123',
        'phone_number': '+919876543210',
        'name': 'Test User'
    }
    
    encrypted = encryption.encrypt_pii_data(user_data)
    assert encrypted['phone_number'] != user_data['phone_number']
    
    decrypted = encryption.decrypt_pii_data(encrypted)
    assert decrypted['phone_number'] == user_data['phone_number']

# Test rate limiting
def test_rate_limiting():
    rate_limiter = RateLimiter()
    
    # First request should succeed
    result = rate_limiter.check_rate_limit('user123', 'api_call', 5, 60)
    assert result['allowed'] == True
    
    # Exceed limit
    for i in range(5):
        rate_limiter.check_rate_limit('user123', 'api_call', 5, 60)
    
    result = rate_limiter.check_rate_limit('user123', 'api_call', 5, 60)
    assert result['allowed'] == False

# Test consent management
def test_consent_management():
    consent_mgmt = ConsentManagement()
    
    consent_mgmt.record_consent(
        user_id='test123',
        consent_type='data_collection',
        granted=True,
        ip_address='127.0.0.1',
        consent_text='Test consent'
    )
    
    has_consent = consent_mgmt.check_consent('test123', 'data_collection')
    assert has_consent == True
```

## Monitoring and Alerts

### CloudWatch Alarms

1. **High Rate Limit Violations**
   - Metric: Rate limit exceeded count
   - Threshold: > 100 per 5 minutes
   - Action: SNS notification

2. **Unusual Data Access Patterns**
   - Metric: Data access count per user
   - Threshold: > 1000 per hour
   - Action: Security team alert

3. **Failed Authentication Attempts**
   - Metric: Auth failures
   - Threshold: > 10 per minute
   - Action: Block IP temporarily

4. **Data Deletion Requests**
   - Metric: Deletion request count
   - Threshold: > 0
   - Action: Admin notification

## Compliance Checklist

- [x] Data encryption at rest
- [x] Data encryption in transit
- [x] Field-level encryption for PII
- [x] Comprehensive audit logging
- [x] Rate limiting and DDoS protection
- [x] Consent management system
- [x] Data portability (export)
- [x] Right to be forgotten (deletion)
- [x] Data anonymization for analytics
- [x] Access control and authentication
- [x] Security monitoring and alerting
- [x] Regular security audits

## Maintenance

### Regular Tasks

1. **Weekly:**
   - Review audit logs for anomalies
   - Check rate limit violations
   - Monitor encryption key usage

2. **Monthly:**
   - Security audit report
   - Update WAF rules if needed
   - Review consent records

3. **Quarterly:**
   - Penetration testing
   - Compliance audit
   - Update security policies

## Support

For security issues or questions:
- Email: security@rise-platform.in
- Emergency: security-emergency@rise-platform.in
- Documentation: https://docs.rise-platform.in/security

## References

- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)
- [GDPR Compliance Guide](https://gdpr.eu/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [AWS KMS Documentation](https://docs.aws.amazon.com/kms/)
- [AWS WAF Documentation](https://docs.aws.amazon.com/waf/)
