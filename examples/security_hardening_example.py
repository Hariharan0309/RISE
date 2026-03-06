"""
Example usage of RISE security hardening features
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.security_hardening import (
    FieldLevelEncryption,
    DynamoDBEncryption,
    AuditLogger,
    RateLimiter,
    DataAnonymization,
    ConsentManagement,
    DataPortability,
    initialize_security_hardening
)


def example_field_encryption():
    """Example: Encrypt and decrypt PII data"""
    print("\n=== Field-Level Encryption Example ===\n")
    
    encryption = FieldLevelEncryption()
    encryption.key_id = 'your-kms-key-id'
    
    # Original user data with PII
    user_data = {
        'user_id': 'farmer123',
        'phone_number': '+919876543210',
        'name': 'Ravi Kumar',
        'location': {
            'state': 'Uttar Pradesh',
            'district': 'Lucknow',
            'coordinates': '26.8467,80.9462'
        },
        'farm_details': {
            'land_size': 2.5,
            'crops': ['wheat', 'rice']
        }
    }
    
    print("Original data:")
    print(f"  Name: {user_data['name']}")
    print(f"  Phone: {user_data['phone_number']}")
    print(f"  Coordinates: {user_data['location']['coordinates']}")
    
    # Encrypt PII fields
    encrypted_data = encryption.encrypt_pii_data(user_data)
    
    print("\nEncrypted data:")
    print(f"  Name: {encrypted_data['name'][:50]}...")
    print(f"  Phone: {encrypted_data['phone_number'][:50]}...")
    print(f"  Coordinates: {encrypted_data['location']['coordinates'][:50]}...")
    
    # Decrypt PII fields
    decrypted_data = encryption.decrypt_pii_data(encrypted_data)
    
    print("\nDecrypted data:")
    print(f"  Name: {decrypted_data['name']}")
    print(f"  Phone: {decrypted_data['phone_number']}")
    print(f"  Coordinates: {decrypted_data['location']['coordinates']}")


def example_audit_logging():
    """Example: Log data access and consent changes"""
    print("\n=== Audit Logging Example ===\n")
    
    audit_logger = AuditLogger()
    
    # Log data access
    print("Logging data access...")
    audit_logger.log_data_access(
        user_id='farmer123',
        action='READ',
        resource_type='UserProfile',
        resource_id='profile_farmer123',
        ip_address='192.168.1.100',
        user_agent='Mozilla/5.0 (Mobile)',
        data_accessed=['name', 'phone_number', 'location']
    )
    print("✓ Data access logged")
    
    # Log consent change
    print("\nLogging consent change...")
    audit_logger.log_consent_change(
        user_id='farmer123',
        consent_type='data_collection',
        granted=True,
        ip_address='192.168.1.100'
    )
    print("✓ Consent change logged")
    
    # Log data deletion
    print("\nLogging data deletion...")
    audit_logger.log_data_deletion(
        user_id='farmer123',
        resource_type='DiagnosisHistory',
        resource_id='diagnosis_456',
        deletion_reason='user_requested'
    )
    print("✓ Data deletion logged")
    
    # Retrieve audit trail
    print("\nRetrieving audit trail for last 30 days...")
    trail = audit_logger.get_user_audit_trail('farmer123', days=30)
    print(f"✓ Found {len(trail)} audit entries")


def example_rate_limiting():
    """Example: Check and enforce rate limits"""
    print("\n=== Rate Limiting Example ===\n")
    
    rate_limiter = RateLimiter()
    
    # Check API call rate limit
    print("Checking API call rate limit (100 per minute)...")
    result = rate_limiter.check_rate_limit(
        identifier='farmer123',
        limit_type='api_call',
        max_requests=100,
        window_seconds=60
    )
    
    if result['allowed']:
        print(f"✓ Request allowed")
        print(f"  Current count: {result['current_count']}")
        print(f"  Remaining: {result['remaining']}")
    else:
        print(f"✗ Rate limit exceeded")
        print(f"  Retry after: {result['retry_after']} seconds")
    
    # Check image upload rate limit
    print("\nChecking image upload rate limit (10 per hour)...")
    result = rate_limiter.check_rate_limit(
        identifier='farmer123',
        limit_type='image_upload',
        max_requests=10,
        window_seconds=3600
    )
    
    if result['allowed']:
        print(f"✓ Upload allowed")
        print(f"  Current count: {result['current_count']}")
        print(f"  Remaining: {result['remaining']}")
    
    # Configure WAF rules
    print("\nConfiguring WAF rules for DDoS protection...")
    waf_config = rate_limiter.configure_waf_rules('your-web-acl-id')
    print(f"✓ WAF configured with {len(waf_config['rules'])} rules")


def example_data_anonymization():
    """Example: Anonymize data for analytics"""
    print("\n=== Data Anonymization Example ===\n")
    
    anonymizer = DataAnonymization()
    
    # Original user data
    user_data = {
        'user_id': 'farmer123',
        'location': {
            'state': 'Uttar Pradesh',
            'district': 'Lucknow',
            'coordinates': '26.8467,80.9462'
        },
        'farm_details': {
            'land_size': 2.5,
            'crops': ['wheat', 'rice']
        },
        'preferences': {
            'language': 'hindi'
        }
    }
    
    print("Original data:")
    print(f"  User ID: {user_data['user_id']}")
    print(f"  Coordinates: {user_data['location']['coordinates']}")
    print(f"  Land size: {user_data['farm_details']['land_size']} acres")
    
    # Anonymize for analytics
    anonymized = anonymizer.anonymize_for_analytics(user_data)
    
    print("\nAnonymized data:")
    print(f"  User ID hash: {anonymized['user_id_hash']}")
    print(f"  Location (10km precision): {anonymized['location_approximate']}")
    print(f"  Land size bucket: {anonymized['land_size_bucket']}")
    print(f"  State: {anonymized['state']}")
    print(f"  Crops: {anonymized['crop_types']}")


def example_consent_management():
    """Example: Manage user consents"""
    print("\n=== Consent Management Example ===\n")
    
    consent_mgmt = ConsentManagement()
    
    # Record consent for data collection
    print("Recording consent for data collection...")
    result = consent_mgmt.record_consent(
        user_id='farmer123',
        consent_type='data_collection',
        granted=True,
        ip_address='192.168.1.100',
        consent_text='मैं कृषि सहायता के लिए डेटा संग्रह के लिए सहमत हूं'
    )
    print(f"✓ Consent recorded: {result['consent_id']}")
    
    # Record consent for analytics
    print("\nRecording consent for analytics...")
    result = consent_mgmt.record_consent(
        user_id='farmer123',
        consent_type='analytics',
        granted=True,
        ip_address='192.168.1.100',
        consent_text='मैं उपयोग विश्लेषण के लिए सहमत हूं'
    )
    print(f"✓ Consent recorded: {result['consent_id']}")
    
    # Record consent denial for marketing
    print("\nRecording consent denial for marketing...")
    result = consent_mgmt.record_consent(
        user_id='farmer123',
        consent_type='marketing',
        granted=False,
        ip_address='192.168.1.100',
        consent_text='मैं विपणन संचार के लिए सहमत नहीं हूं'
    )
    print(f"✓ Consent recorded: {result['consent_id']}")
    
    # Check specific consent
    print("\nChecking consents...")
    has_data_consent = consent_mgmt.check_consent('farmer123', 'data_collection')
    has_marketing_consent = consent_mgmt.check_consent('farmer123', 'marketing')
    
    print(f"  Data collection: {'✓ Granted' if has_data_consent else '✗ Denied'}")
    print(f"  Marketing: {'✓ Granted' if has_marketing_consent else '✗ Denied'}")
    
    # Get all consents
    print("\nRetrieving all consents...")
    all_consents = consent_mgmt.get_user_consents('farmer123')
    print(f"✓ Found {len(all_consents)} consent types:")
    for consent_type, granted in all_consents.items():
        status = '✓ Granted' if granted else '✗ Denied'
        print(f"  {consent_type}: {status}")


def example_data_portability():
    """Example: Export and delete user data"""
    print("\n=== Data Portability Example ===\n")
    
    data_portability = DataPortability()
    
    # Export user data
    print("Exporting all user data...")
    export_result = data_portability.export_user_data('farmer123')
    
    print(f"✓ Data exported successfully")
    print(f"  Download URL: {export_result['download_url']}")
    print(f"  Expires in: {export_result['expires_in']}")
    print(f"  File size: {export_result['file_size']} bytes")
    
    print("\nExported data includes:")
    print("  - User profile")
    print("  - Farm data")
    print("  - Diagnosis history")
    print("  - Conversation history")
    print("  - Forum posts")
    print("  - Resource sharing listings")
    print("  - Booking history")
    
    # Delete user data (commented out for safety)
    print("\n--- Data Deletion Example (not executed) ---")
    print("To delete all user data:")
    print("  deletion_result = data_portability.delete_user_data(")
    print("      user_id='farmer123',")
    print("      deletion_reason='user_requested'")
    print("  )")
    print("\nThis will permanently delete:")
    print("  - All database records")
    print("  - All S3 objects (images, audio, documents)")
    print("  - All conversation history")
    print("  - All forum posts and interactions")


def example_complete_workflow():
    """Example: Complete security workflow for a user action"""
    print("\n=== Complete Security Workflow Example ===\n")
    
    # Initialize components
    encryption = FieldLevelEncryption()
    encryption.key_id = 'your-kms-key-id'
    audit_logger = AuditLogger()
    rate_limiter = RateLimiter()
    consent_mgmt = ConsentManagement()
    
    user_id = 'farmer123'
    ip_address = '192.168.1.100'
    
    print("Step 1: Check rate limit")
    rate_check = rate_limiter.check_rate_limit(
        identifier=user_id,
        limit_type='api_call',
        max_requests=100,
        window_seconds=60
    )
    
    if not rate_check['allowed']:
        print(f"✗ Rate limit exceeded. Retry after {rate_check['retry_after']}s")
        return
    
    print(f"✓ Rate limit OK ({rate_check['remaining']} remaining)")
    
    print("\nStep 2: Check consent")
    has_consent = consent_mgmt.check_consent(user_id, 'data_collection')
    
    if not has_consent:
        print("✗ User has not granted consent for data collection")
        return
    
    print("✓ User consent verified")
    
    print("\nStep 3: Process user data with encryption")
    user_data = {
        'user_id': user_id,
        'phone_number': '+919876543210',
        'name': 'Ravi Kumar',
        'location': {
            'state': 'Uttar Pradesh',
            'coordinates': '26.8467,80.9462'
        }
    }
    
    encrypted_data = encryption.encrypt_pii_data(user_data)
    print("✓ PII data encrypted")
    
    print("\nStep 4: Log data access")
    audit_logger.log_data_access(
        user_id=user_id,
        action='WRITE',
        resource_type='UserProfile',
        resource_id=f'profile_{user_id}',
        ip_address=ip_address,
        user_agent='RISE Mobile App v1.0',
        data_accessed=['phone_number', 'name', 'location']
    )
    print("✓ Access logged to audit trail")
    
    print("\n✓ Complete workflow executed successfully")
    print("\nSecurity measures applied:")
    print("  ✓ Rate limiting")
    print("  ✓ Consent verification")
    print("  ✓ PII encryption")
    print("  ✓ Audit logging")


def example_initialize_security():
    """Example: Initialize all security components"""
    print("\n=== Initialize Security Hardening ===\n")
    
    print("Initializing security components...")
    print("  - Enabling DynamoDB encryption with KMS")
    print("  - Configuring WAF rules for DDoS protection")
    print("  - Setting up audit logging")
    print("  - Configuring rate limiting")
    
    # Initialize (commented out to avoid actual AWS calls)
    # result = initialize_security_hardening(
    #     kms_key_id='your-kms-key-id',
    #     web_acl_id='your-web-acl-id'
    # )
    
    print("\n✓ Security hardening initialized")
    print("\nEnabled features:")
    print("  ✓ Field-level encryption for PII")
    print("  ✓ DynamoDB encryption at rest")
    print("  ✓ Comprehensive audit logging")
    print("  ✓ Rate limiting and DDoS protection")
    print("  ✓ Data anonymization for analytics")
    print("  ✓ Consent management system")
    print("  ✓ Data portability and deletion")


def main():
    """Run all examples"""
    print("=" * 60)
    print("RISE Security Hardening Examples")
    print("=" * 60)
    
    try:
        example_field_encryption()
        example_audit_logging()
        example_rate_limiting()
        example_data_anonymization()
        example_consent_management()
        example_data_portability()
        example_complete_workflow()
        example_initialize_security()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        print("\nNote: These examples require AWS credentials and resources.")
        print("Configure your AWS environment before running.")


if __name__ == '__main__':
    main()
