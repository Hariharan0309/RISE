"""
Lambda functions for security operations
"""

import json
import os
from security_hardening import (
    FieldLevelEncryption,
    AuditLogger,
    RateLimiter,
    ConsentManagement,
    DataPortability,
    DataAnonymization
)


def data_access_handler(event, context):
    """
    Lambda handler for data access with audit logging
    """
    audit_logger = AuditLogger()
    encryption = FieldLevelEncryption()
    
    try:
        # Extract request details
        user_id = event['requestContext']['authorizer']['claims']['sub']
        action = event['httpMethod']
        resource_type = event['pathParameters']['resource_type']
        resource_id = event['pathParameters']['resource_id']
        ip_address = event['requestContext']['identity']['sourceIp']
        user_agent = event['requestContext']['identity']['userAgent']
        
        # Log access
        audit_logger.log_data_access(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Retrieve and decrypt data if needed
        # Implementation depends on resource type
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Access logged'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def rate_limit_handler(event, context):
    """
    Lambda handler for rate limiting checks
    """
    rate_limiter = RateLimiter()
    
    try:
        # Extract identifier (user ID or IP)
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        ip_address = event.get('requestContext', {}).get('identity', {}).get('sourceIp')
        
        identifier = user_id or ip_address
        limit_type = event['pathParameters']['limit_type']
        
        # Define limits based on type
        limits = {
            'api_call': {'max': 100, 'window': 60},  # 100 per minute
            'image_upload': {'max': 10, 'window': 3600},  # 10 per hour
            'voice_query': {'max': 50, 'window': 3600}  # 50 per hour
        }
        
        limit_config = limits.get(limit_type, {'max': 100, 'window': 60})
        
        # Check rate limit
        result = rate_limiter.check_rate_limit(
            identifier=identifier,
            limit_type=limit_type,
            max_requests=limit_config['max'],
            window_seconds=limit_config['window']
        )
        
        if not result['allowed']:
            return {
                'statusCode': 429,
                'body': json.dumps({
                    'error': 'Rate limit exceeded',
                    'retry_after': result['retry_after']
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def consent_management_handler(event, context):
    """
    Lambda handler for consent management
    """
    consent_mgmt = ConsentManagement()
    
    try:
        user_id = event['requestContext']['authorizer']['claims']['sub']
        ip_address = event['requestContext']['identity']['sourceIp']
        
        if event['httpMethod'] == 'POST':
            # Record consent
            body = json.loads(event['body'])
            result = consent_mgmt.record_consent(
                user_id=user_id,
                consent_type=body['consent_type'],
                granted=body['granted'],
                ip_address=ip_address,
                consent_text=body['consent_text']
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
        
        elif event['httpMethod'] == 'GET':
            # Get consents
            consents = consent_mgmt.get_user_consents(user_id)
            
            return {
                'statusCode': 200,
                'body': json.dumps(consents)
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def data_export_handler(event, context):
    """
    Lambda handler for data export (data portability)
    """
    data_portability = DataPortability()
    
    try:
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # Export user data
        result = data_portability.export_user_data(user_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def data_deletion_handler(event, context):
    """
    Lambda handler for data deletion (right to be forgotten)
    """
    data_portability = DataPortability()
    
    try:
        user_id = event['requestContext']['authorizer']['claims']['sub']
        body = json.loads(event['body'])
        deletion_reason = body.get('reason', 'user_requested')
        
        # Delete user data
        result = data_portability.delete_user_data(user_id, deletion_reason)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def anonymize_analytics_handler(event, context):
    """
    Lambda handler for anonymizing data for analytics
    """
    anonymizer = DataAnonymization()
    
    try:
        # Process batch of user data for analytics
        records = event.get('Records', [])
        anonymized_records = []
        
        for record in records:
            user_data = json.loads(record['body'])
            anonymized = anonymizer.anonymize_for_analytics(user_data)
            anonymized_records.append(anonymized)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'processed': len(anonymized_records),
                'records': anonymized_records
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
