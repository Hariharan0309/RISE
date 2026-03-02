"""
AWS Lambda Function for Audio File Upload to S3
Handles audio file uploads from frontend with validation and processing
"""

import json
import boto3
import base64
import uuid
from datetime import datetime
import logging
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')

# Configuration from environment variables
S3_BUCKET = os.environ.get('S3_BUCKET', 'rise-application-data')
MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 10 * 1024 * 1024))  # 10MB default
ALLOWED_FORMATS = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/webm', 'audio/ogg']


def lambda_handler(event, context):
    """
    Lambda handler for audio file uploads
    
    Expected event structure:
    {
        "body": {
            "audio_data": "base64_encoded_audio",
            "user_id": "farmer_1234567890",
            "content_type": "audio/wav",
            "language_code": "hi"
        }
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "success": true,
            "s3_key": "audio/voice-queries/user_id/timestamp-uuid.wav",
            "s3_uri": "s3://bucket/key",
            "file_size": 12345
        }
    }
    """
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract parameters
        audio_data_base64 = body.get('audio_data')
        user_id = body.get('user_id')
        content_type = body.get('content_type', 'audio/wav')
        language_code = body.get('language_code', 'en')
        
        # Validate required fields
        if not audio_data_base64:
            return create_response(400, {
                'success': False,
                'error': 'Missing audio_data in request'
            })
        
        if not user_id:
            return create_response(400, {
                'success': False,
                'error': 'Missing user_id in request'
            })
        
        # Validate content type
        if content_type not in ALLOWED_FORMATS:
            return create_response(400, {
                'success': False,
                'error': f'Invalid content type. Allowed formats: {", ".join(ALLOWED_FORMATS)}'
            })
        
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(audio_data_base64)
        except Exception as e:
            logger.error(f"Base64 decode error: {e}")
            return create_response(400, {
                'success': False,
                'error': 'Invalid base64 audio data'
            })
        
        # Validate file size
        file_size = len(audio_bytes)
        if file_size > MAX_FILE_SIZE:
            return create_response(400, {
                'success': False,
                'error': f'File size ({file_size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)'
            })
        
        if file_size == 0:
            return create_response(400, {
                'success': False,
                'error': 'Empty audio file'
            })
        
        # Generate S3 key
        timestamp = int(datetime.now().timestamp())
        file_uuid = uuid.uuid4().hex[:8]
        file_extension = get_file_extension(content_type)
        
        s3_key = f"audio/voice-queries/{user_id}/{timestamp}-{file_uuid}.{file_extension}"
        
        # Upload to S3
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=audio_bytes,
                ContentType=content_type,
                Metadata={
                    'user_id': user_id,
                    'language_code': language_code,
                    'upload_timestamp': str(timestamp),
                    'file_size': str(file_size)
                },
                # Set lifecycle to delete after 30 days
                Tagging=f'retention=30days&user_id={user_id}'
            )
            
            logger.info(f"Successfully uploaded audio file: {s3_key} ({file_size} bytes)")
            
            # Generate S3 URI
            s3_uri = f"s3://{S3_BUCKET}/{s3_key}"
            
            # Generate presigned URL for download (valid for 1 hour)
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET, 'Key': s3_key},
                ExpiresIn=3600
            )
            
            return create_response(200, {
                'success': True,
                's3_key': s3_key,
                's3_uri': s3_uri,
                's3_bucket': S3_BUCKET,
                'file_size': file_size,
                'content_type': content_type,
                'presigned_url': presigned_url,
                'upload_timestamp': timestamp
            })
        
        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            return create_response(500, {
                'success': False,
                'error': f'Failed to upload to S3: {str(e)}'
            })
    
    except Exception as e:
        logger.error(f"Lambda handler error: {e}", exc_info=True)
        return create_response(500, {
            'success': False,
            'error': f'Internal server error: {str(e)}'
        })


def get_file_extension(content_type: str) -> str:
    """Get file extension from content type"""
    extension_map = {
        'audio/wav': 'wav',
        'audio/mp3': 'mp3',
        'audio/mpeg': 'mp3',
        'audio/webm': 'webm',
        'audio/ogg': 'ogg'
    }
    return extension_map.get(content_type, 'wav')


def create_response(status_code: int, body: dict) -> dict:
    """Create Lambda response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        },
        'body': json.dumps(body)
    }


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'body': json.dumps({
            'audio_data': base64.b64encode(b'test audio data').decode('utf-8'),
            'user_id': 'test_farmer_001',
            'content_type': 'audio/wav',
            'language_code': 'hi'
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
