"""
Test Configuration for RISE Lambda Function Unit Tests
Provides common test fixtures, mocks, and utilities
"""

import os
import json
import base64
import boto3
from moto import mock_dynamodb, mock_s3, mock_cognito_idp
from unittest.mock import Mock, patch
import tempfile
import shutil


class TestConfig:
    """Test configuration and utilities"""
    
    # Test data constants
    TEST_USER_ID = 'test_farmer_001'
    TEST_FARM_ID = 'farm_test_001'
    TEST_S3_BUCKET = 'rise-test-bucket'
    TEST_REGION = 'us-east-1'
    
    # Sample test data
    SAMPLE_AUDIO_DATA = base64.b64encode(b'fake audio data for testing').decode('utf-8')
    SAMPLE_IMAGE_DATA = base64.b64encode(b'fake image data for testing').decode('utf-8')
    
    SAMPLE_LOCATION = {
        'state': 'Karnataka',
        'district': 'Bangalore',
        'coordinates': '12.9716,77.5946'
    }
    
    SAMPLE_SOIL_TEST_DATA = {
        'ph': 6.5,
        'nitrogen': 'medium',
        'phosphorus': 'low',
        'potassium': 'high',
        'organic_matter': 2.8
    }
    
    # AWS service mocks
    @staticmethod
    def mock_aws_services():
        """Set up AWS service mocks"""
        # Set environment variables for testing
        os.environ.update({
            'AWS_ACCESS_KEY_ID': 'testing',
            'AWS_SECRET_ACCESS_KEY': 'testing',
            'AWS_SECURITY_TOKEN': 'testing',
            'AWS_SESSION_TOKEN': 'testing',
            'AWS_DEFAULT_REGION': TestConfig.TEST_REGION,
            'S3_BUCKET': TestConfig.TEST_S3_BUCKET,
            'DIAGNOSIS_TABLE': 'RISE-DiagnosisHistory-Test',
            'FARM_DATA_TABLE': 'RISE-FarmData-Test',
            'USER_PROFILES_TABLE': 'RISE-UserProfiles-Test'
        })
    
    @staticmethod
    def create_mock_dynamodb_tables():
        """Create mock DynamoDB tables for testing"""
        dynamodb = boto3.resource('dynamodb', region_name=TestConfig.TEST_REGION)
        
        # User Profiles table
        user_profiles_table = dynamodb.create_table(
            TableName='RISE-UserProfiles-Test',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Farm Data table
        farm_data_table = dynamodb.create_table(
            TableName='RISE-FarmData-Test',
            KeySchema=[
                {'AttributeName': 'farm_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'farm_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Diagnosis History table
        diagnosis_table = dynamodb.create_table(
            TableName='RISE-DiagnosisHistory-Test',
            KeySchema=[
                {'AttributeName': 'diagnosis_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'diagnosis_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # User Sessions table
        sessions_table = dynamodb.create_table(
            TableName='RISE-UserSessions-Test',
            KeySchema=[
                {'AttributeName': 'session_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'session_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        return {
            'user_profiles': user_profiles_table,
            'farm_data': farm_data_table,
            'diagnosis': diagnosis_table,
            'sessions': sessions_table
        }
    
    @staticmethod
    def create_mock_s3_bucket():
        """Create mock S3 bucket for testing"""
        s3 = boto3.client('s3', region_name=TestConfig.TEST_REGION)
        s3.create_bucket(Bucket=TestConfig.TEST_S3_BUCKET)
        return s3
    
    @staticmethod
    def create_test_user_data():
        """Create test user data"""
        return {
            'user_id': TestConfig.TEST_USER_ID,
            'name': 'Test Farmer',
            'phone_number': '+91-9876543210',
            'location': TestConfig.SAMPLE_LOCATION,
            'farm_details': {
                'land_size': 2.5,
                'soil_type': 'loam',
                'crops': ['wheat', 'rice'],
                'farming_experience': '5-10 years'
            },
            'preferences': {
                'language': 'hi',
                'notification_settings': {
                    'weather_alerts': True,
                    'market_updates': True
                }
            },
            'role': 'farmer'
        }
    
    @staticmethod
    def create_mock_bedrock_response(analysis_type='disease'):
        """Create mock Bedrock response"""
        if analysis_type == 'disease':
            return {
                'body': Mock(read=lambda: json.dumps({
                    'content': [{
                        'text': '''
                        1. DISEASES DETECTED:
                           - Disease Name: Leaf Rust
                           - Confidence: 85%
                           - Severity: medium
                        
                        2. SYMPTOMS OBSERVED:
                           - Brown spots on leaves
                           - Yellowing of leaf edges
                        
                        3. TREATMENT RECOMMENDATIONS:
                           - Chemical Treatment: Apply fungicide spray
                           - Organic Alternative: Neem oil application
                        '''
                    }]
                }).encode())
            }
        elif analysis_type == 'pest':
            return {
                'body': Mock(read=lambda: json.dumps({
                    'content': [{
                        'text': '''
                        1. PESTS IDENTIFIED:
                           - Pest Species: Aphids (Aphis gossypii)
                           - Confidence: 90%
                           - Lifecycle Stage: adult
                           - Population Density: medium
                           - Severity: medium
                        
                        2. INTEGRATED PEST MANAGEMENT:
                           A. BIOLOGICAL CONTROLS:
                              - Ladybird beetles as natural predators
                              - Neem-based biopesticides
                        '''
                    }]
                }).encode())
            }
        elif analysis_type == 'soil':
            return {
                'body': Mock(read=lambda: json.dumps({
                    'content': [{
                        'text': '''
                        1. SOIL TYPE CLASSIFICATION:
                           - Primary Type: loam
                           - Texture: Well-balanced clay, silt, and sand
                           - Color: Dark brown indicating good organic matter
                        
                        2. FERTILITY ASSESSMENT:
                           - Overall Fertility Level: medium
                           - Estimated Organic Matter: 2.5%
                        
                        3. ESTIMATED NPK LEVELS:
                           - Nitrogen (N): medium
                           - Phosphorus (P): low
                           - Potassium (K): high
                        '''
                    }]
                }).encode())
            }
    
    @staticmethod
    def create_mock_translate_response(source_text, target_lang='hi'):
        """Create mock AWS Translate response"""
        translations = {
            'en_to_hi': {
                'Hello farmer': 'नमस्ते किसान',
                'How can I help you?': 'मैं आपकी कैसे मदद कर सकता हूं?',
                'Your crop looks healthy': 'आपकी फसल स्वस्थ दिखती है'
            },
            'hi_to_en': {
                'नमस्ते': 'Hello',
                'धन्यवाद': 'Thank you',
                'फसल': 'crop'
            }
        }
        
        # Simple mock translation
        if target_lang == 'hi':
            translated = translations['en_to_hi'].get(source_text, f'[HI]{source_text}')
        else:
            translated = translations['hi_to_en'].get(source_text, f'[EN]{source_text}')
        
        return {
            'TranslatedText': translated,
            'SourceLanguageCode': 'en' if target_lang == 'hi' else 'hi'
        }
    
    @staticmethod
    def create_mock_polly_response(text):
        """Create mock AWS Polly response"""
        # Create fake audio data
        fake_audio = f"[AUDIO:{text}]".encode('utf-8')
        
        mock_stream = Mock()
        mock_stream.read.return_value = fake_audio
        
        return {
            'AudioStream': mock_stream
        }
    
    @staticmethod
    def create_mock_transcribe_response(audio_data):
        """Create mock AWS Transcribe response"""
        # Simple mock transcription
        transcriptions = {
            b'fake audio data': 'Hello, this is a test transcription',
            b'hindi audio': 'नमस्ते, यह एक परीक्षण है',
            b'crop question': 'What disease does my wheat crop have?'
        }
        
        transcribed_text = transcriptions.get(audio_data, 'Mock transcription result')
        
        return {
            'results': {
                'transcripts': [{'transcript': transcribed_text}],
                'items': [
                    {
                        'alternatives': [{'confidence': 0.95}]
                    }
                ]
            }
        }


class MockLambdaContext:
    """Mock Lambda context for testing"""
    
    def __init__(self, function_name='test_function', timeout_ms=30000):
        self.function_name = function_name
        self.function_version = '$LATEST'
        self.invoked_function_arn = f'arn:aws:lambda:us-east-1:123456789012:function:{function_name}'
        self.memory_limit_in_mb = 128
        self.remaining_time_in_millis = timeout_ms
        self.log_group_name = f'/aws/lambda/{function_name}'
        self.log_stream_name = '2023/01/01/[$LATEST]test'
        self.aws_request_id = 'test-request-id-123'
    
    def get_remaining_time_in_millis(self):
        return self.remaining_time_in_millis


class TestEventBuilder:
    """Builder for creating test events"""
    
    @staticmethod
    def audio_upload_event(audio_data=None, user_id=None, content_type='audio/wav', language_code='en'):
        """Build audio upload event"""
        return {
            'body': json.dumps({
                'audio_data': audio_data or TestConfig.SAMPLE_AUDIO_DATA,
                'user_id': user_id or TestConfig.TEST_USER_ID,
                'content_type': content_type,
                'language_code': language_code
            })
        }
    
    @staticmethod
    def image_analysis_event(image_data=None, user_id=None, crop_type='wheat', context=None):
        """Build image analysis event"""
        return {
            'body': json.dumps({
                'image_data': image_data or TestConfig.SAMPLE_IMAGE_DATA,
                'user_id': user_id or TestConfig.TEST_USER_ID,
                'crop_type': crop_type,
                'additional_context': context or 'Leaves have brown spots',
                'language_code': 'en'
            })
        }
    
    @staticmethod
    def soil_analysis_event(analysis_type='test_data', user_id=None, farm_id=None, test_data=None):
        """Build soil analysis event"""
        return {
            'body': json.dumps({
                'analysis_type': analysis_type,
                'user_id': user_id or TestConfig.TEST_USER_ID,
                'farm_id': farm_id or TestConfig.TEST_FARM_ID,
                'test_data': test_data or TestConfig.SAMPLE_SOIL_TEST_DATA,
                'location': TestConfig.SAMPLE_LOCATION,
                'language_code': 'en'
            })
        }
    
    @staticmethod
    def pest_analysis_event(image_data=None, user_id=None, crop_type='wheat', context=None):
        """Build pest analysis event"""
        return {
            'body': json.dumps({
                'image_data': image_data or TestConfig.SAMPLE_IMAGE_DATA,
                'user_id': user_id or TestConfig.TEST_USER_ID,
                'crop_type': crop_type,
                'additional_context': context or 'Small insects on leaves',
                'language_code': 'en'
            })
        }


class TestAssertions:
    """Custom assertions for RISE tests"""
    
    @staticmethod
    def assert_lambda_response(test_case, response, expected_status=200, should_succeed=True):
        """Assert Lambda response format and status"""
        test_case.assertIsInstance(response, dict)
        test_case.assertIn('statusCode', response)
        test_case.assertIn('headers', response)
        test_case.assertIn('body', response)
        
        test_case.assertEqual(response['statusCode'], expected_status)
        
        # Check CORS headers
        headers = response['headers']
        test_case.assertIn('Access-Control-Allow-Origin', headers)
        test_case.assertEqual(headers['Access-Control-Allow-Origin'], '*')
        
        # Parse and check body
        body = json.loads(response['body'])
        test_case.assertIn('success', body)
        test_case.assertEqual(body['success'], should_succeed)
        
        if not should_succeed:
            test_case.assertIn('error', body)
        
        return body
    
    @staticmethod
    def assert_diagnosis_result(test_case, result):
        """Assert diagnosis result structure"""
        test_case.assertIn('diagnosis_id', result)
        test_case.assertIn('diseases', result)
        test_case.assertIn('confidence_score', result)
        test_case.assertIn('severity', result)
        
        # Check data types
        test_case.assertIsInstance(result['diseases'], list)
        test_case.assertIsInstance(result['confidence_score'], (int, float))
        test_case.assertIn(result['severity'], ['low', 'medium', 'high', 'critical', 'unknown'])
    
    @staticmethod
    def assert_soil_analysis_result(test_case, result):
        """Assert soil analysis result structure"""
        test_case.assertIn('analysis_id', result)
        test_case.assertIn('soil_type', result)
        test_case.assertIn('fertility_level', result)
        
        # Check optional fields
        if 'ph_level' in result:
            test_case.assertIsInstance(result['ph_level'], (int, float, type(None)))
        
        if 'npk_levels' in result:
            test_case.assertIsInstance(result['npk_levels'], dict)
    
    @staticmethod
    def assert_pest_analysis_result(test_case, result):
        """Assert pest analysis result structure"""
        test_case.assertIn('diagnosis_id', result)
        test_case.assertIn('pests', result)
        test_case.assertIn('confidence_score', result)
        test_case.assertIn('severity', result)
        test_case.assertIn('lifecycle_stage', result)
        
        # Check data types
        test_case.assertIsInstance(result['pests'], list)
        test_case.assertIsInstance(result['confidence_score'], (int, float))


# Test utilities
def create_temp_directory():
    """Create temporary directory for test files"""
    return tempfile.mkdtemp()


def cleanup_temp_directory(temp_dir):
    """Clean up temporary directory"""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def load_test_data(filename):
    """Load test data from JSON file"""
    test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    file_path = os.path.join(test_data_dir, filename)
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    
    return {}


# Environment setup for tests
def setup_test_environment():
    """Set up test environment"""
    TestConfig.mock_aws_services()


def teardown_test_environment():
    """Clean up test environment"""
    # Remove test environment variables
    test_env_vars = [
        'S3_BUCKET', 'DIAGNOSIS_TABLE', 'FARM_DATA_TABLE', 'USER_PROFILES_TABLE'
    ]
    
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]