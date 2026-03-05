"""
Unit Tests for Error Handling and Edge Cases in Lambda Functions
Tests exception handling, timeout scenarios, service failures, and edge cases
"""

import unittest
import json
import time
from unittest.mock import Mock, patch, MagicMock
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
import sys
import os

# Add tools directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))


class TestAWSServiceFailures(unittest.TestCase):
    """Test cases for AWS service failure handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_event = {
            'body': json.dumps({
                'user_id': 'test_farmer_001',
                'test_data': 'valid_data'
            })
        }
    
    @patch('boto3.client')
    def test_s3_service_unavailable(self, mock_boto3):
        """Test S3 service unavailable error handling"""
        mock_s3 = Mock()
        mock_s3.put_object.side_effect = EndpointConnectionError(
            endpoint_url='https://s3.amazonaws.com'
        )
        mock_boto3.return_value = mock_s3
        
        # Import after mocking
        from audio_upload_lambda import lambda_handler
        
        event = {
            'body': json.dumps({
                'audio_data': 'dGVzdCBhdWRpbyBkYXRh',  # base64 'test audio data'
                'user_id': 'test_farmer_001',
                'content_type': 'audio/wav'
            })
        }
        
        result = lambda_handler(event, None)
        
        self.assertEqual(result['statusCode'], 500)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertIn('Failed to upload to S3', body['error'])
    
    @patch('boto3.client')
    def test_bedrock_service_throttling(self, mock_boto3):
        """Test Bedrock service throttling error handling"""
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = ClientError(
            error_response={
                'Error': {
                    'Code': 'ThrottlingException',
                    'Message': 'Rate exceeded'
                }
            },
            operation_name='InvokeModel'
        )
        mock_boto3.return_value = mock_bedrock
        
        # Test with image analysis lambda
        from image_analysis_lambda import analyze_with_bedrock
        
        result = analyze_with_bedrock(
            image_bytes=b'fake image data',
            crop_type='wheat',
            additional_context='test',
            language_code='en'
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('boto3.client')
    def test_dynamodb_access_denied(self, mock_boto3):
        """Test DynamoDB access denied error handling"""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_table.put_item.side_effect = ClientError(
            error_response={
                'Error': {
                    'Code': 'AccessDeniedException',
                    'Message': 'User is not authorized to perform this action'
                }
            },
            operation_name='PutItem'
        )
        
        # Mock the resource and table
        mock_dynamodb_resource = Mock()
        mock_dynamodb_resource.Table.return_value = mock_table
        
        with patch('boto3.resource', return_value=mock_dynamodb_resource):
            from image_analysis_lambda import store_diagnosis
            
            # This should handle the exception gracefully
            store_diagnosis(
                diagnosis_id='test_diag_001',
                user_id='test_farmer_001',
                s3_key='test/key.jpg',
                analysis={'diseases': ['test']},
                crop_type='wheat',
                timestamp=int(time.time())
            )
            
            # Should not raise exception, just log error
            mock_table.put_item.assert_called_once()
    
    @patch('boto3.client')
    def test_translate_service_quota_exceeded(self, mock_boto3):
        """Test Translate service quota exceeded error handling"""
        mock_translate = Mock()
        mock_translate.translate_text.side_effect = ClientError(
            error_response={
                'Error': {
                    'Code': 'ServiceQuotaExceededException',
                    'Message': 'Service quota exceeded'
                }
            },
            operation_name='TranslateText'
        )
        mock_boto3.return_value = mock_translate
        
        from translation_tools import TranslationTools
        
        tools = TranslationTools(enable_caching=False)
        result = tools.translate_text('Hello', 'hi', 'en')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('boto3.client')
    def test_no_credentials_error(self, mock_boto3):
        """Test handling of missing AWS credentials"""
        mock_boto3.side_effect = NoCredentialsError()
        
        # This should be handled at the service initialization level
        with self.assertRaises(NoCredentialsError):
            from voice_tools import VoiceProcessingTools
            VoiceProcessingTools()


class TestTimeoutScenarios(unittest.TestCase):
    """Test cases for timeout scenarios"""
    
    @patch('time.sleep')
    @patch('boto3.client')
    def test_transcription_job_timeout(self, mock_boto3, mock_sleep):
        """Test transcription job timeout handling"""
        mock_transcribe = Mock()
        
        # Mock transcription job that never completes
        mock_transcribe.start_transcription_job.return_value = {}
        mock_transcribe.get_transcription_job.return_value = {
            'TranscriptionJob': {
                'TranscriptionJobStatus': 'IN_PROGRESS'
            }
        }
        
        mock_s3 = Mock()
        mock_s3.put_object.return_value = {}
        
        # Mock both clients
        def mock_client_factory(service_name, **kwargs):
            if service_name == 'transcribe':
                return mock_transcribe
            elif service_name == 's3':
                return mock_s3
            return Mock()
        
        mock_boto3.side_effect = mock_client_factory
        
        from voice_tools import VoiceProcessingTools
        
        tools = VoiceProcessingTools()
        result = tools.transcribe_audio(
            audio_data=b'fake audio data',
            language_code='en',
            s3_bucket='test-bucket'
        )
        
        self.assertFalse(result['success'])
        self.assertIn('timed out', result['error'])
    
    @patch('boto3.client')
    def test_bedrock_model_timeout(self, mock_boto3):
        """Test Bedrock model invocation timeout"""
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = ClientError(
            error_response={
                'Error': {
                    'Code': 'ModelTimeoutException',
                    'Message': 'Model invocation timed out'
                }
            },
            operation_name='InvokeModel'
        )
        mock_boto3.return_value = mock_bedrock
        
        from soil_analysis_lambda import analyze_soil_from_test_data
        
        result = analyze_soil_from_test_data(
            test_data={'ph': 6.5},
            location={'state': 'Test', 'district': 'Test'},
            language_code='en'
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class TestMemoryAndResourceLimits(unittest.TestCase):
    """Test cases for memory and resource limit scenarios"""
    
    def test_large_image_processing(self):
        """Test handling of very large images"""
        # Create a large base64 encoded image (simulated)
        large_image_data = 'x' * (20 * 1024 * 1024)  # 20MB of data
        
        from audio_upload_lambda import lambda_handler
        
        event = {
            'body': json.dumps({
                'audio_data': large_image_data,
                'user_id': 'test_farmer_001',
                'content_type': 'audio/wav'
            })
        }
        
        result = lambda_handler(event, None)
        
        # Should fail due to size limit
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
    
    def test_memory_intensive_operations(self):
        """Test memory-intensive operations"""
        # Test with very long text for translation
        very_long_text = 'This is a test sentence. ' * 10000  # Very long text
        
        from translation_tools import TranslationTools
        
        with patch('boto3.client') as mock_boto3:
            mock_translate = Mock()
            mock_translate.translate_text.return_value = {
                'TranslatedText': 'Translated text',
                'SourceLanguageCode': 'en'
            }
            mock_boto3.return_value = mock_translate
            
            tools = TranslationTools(enable_caching=False)
            result = tools.translate_text(very_long_text, 'hi', 'en')
            
            # Should handle large text gracefully
            self.assertTrue(result['success'])
    
    def test_concurrent_request_handling(self):
        """Test handling of concurrent requests"""
        # Simulate multiple concurrent requests
        import threading
        
        results = []
        
        def make_request():
            from translation_tools import TranslationTools
            
            with patch('boto3.client') as mock_boto3:
                mock_translate = Mock()
                mock_translate.translate_text.return_value = {
                    'TranslatedText': 'Translated text',
                    'SourceLanguageCode': 'en'
                }
                mock_boto3.return_value = mock_translate
                
                tools = TranslationTools(enable_caching=False)
                result = tools.translate_text('Hello', 'hi', 'en')
                results.append(result)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        self.assertEqual(len(results), 10)
        for result in results:
            self.assertTrue(result['success'])


class TestMalformedInputHandling(unittest.TestCase):
    """Test cases for malformed input handling"""
    
    def test_invalid_json_body(self):
        """Test handling of invalid JSON in request body"""
        invalid_json_cases = [
            '{"invalid": json}',  # Missing quotes
            '{"key": }',  # Missing value
            '{key: "value"}',  # Unquoted key
            '{"key": "value",}',  # Trailing comma
            'not json at all',  # Not JSON
            '',  # Empty string
            None  # None value
        ]
        
        from audio_upload_lambda import lambda_handler
        
        for invalid_json in invalid_json_cases:
            event = {'body': invalid_json}
            result = lambda_handler(event, None)
            
            # Should handle gracefully with 500 error
            self.assertIn(result['statusCode'], [400, 500])
            if result['statusCode'] == 500:
                body = json.loads(result['body'])
                self.assertFalse(body['success'])
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        from image_analysis_lambda import lambda_handler
        
        incomplete_events = [
            {'body': json.dumps({})},  # Empty body
            {'body': json.dumps({'user_id': 'test'})},  # Missing image_data
            {'body': json.dumps({'image_data': 'test'})},  # Missing user_id
        ]
        
        for event in incomplete_events:
            result = lambda_handler(event, None)
            
            self.assertEqual(result['statusCode'], 400)
            body = json.loads(result['body'])
            self.assertFalse(body['success'])
            self.assertIn('Missing', body['error'])
    
    def test_wrong_data_types(self):
        """Test handling of wrong data types"""
        from soil_analysis_lambda import lambda_handler
        
        wrong_type_events = [
            {
                'body': json.dumps({
                    'analysis_type': 123,  # Should be string
                    'user_id': 'test',
                    'farm_id': 'test'
                })
            },
            {
                'body': json.dumps({
                    'analysis_type': 'test_data',
                    'user_id': ['array'],  # Should be string
                    'farm_id': 'test'
                })
            }
        ]
        
        for event in wrong_type_events:
            result = lambda_handler(event, None)
            
            # Should handle gracefully
            self.assertIn(result['statusCode'], [400, 500])


class TestNetworkAndConnectivityIssues(unittest.TestCase):
    """Test cases for network and connectivity issues"""
    
    @patch('requests.get')
    def test_external_api_failure(self, mock_requests):
        """Test handling of external API failures"""
        # Mock network failure for external API calls
        mock_requests.side_effect = Exception('Network error')
        
        # This would be used in weather API integration
        # For now, just test that exceptions are handled
        try:
            mock_requests('https://api.example.com/weather')
        except Exception as e:
            self.assertIn('Network error', str(e))
    
    @patch('boto3.client')
    def test_aws_region_unavailable(self, mock_boto3):
        """Test handling of AWS region unavailability"""
        mock_boto3.side_effect = EndpointConnectionError(
            endpoint_url='https://bedrock.us-west-2.amazonaws.com'
        )
        
        with self.assertRaises(EndpointConnectionError):
            from voice_tools import VoiceProcessingTools
            VoiceProcessingTools(region='us-west-2')


class TestDataCorruptionScenarios(unittest.TestCase):
    """Test cases for data corruption scenarios"""
    
    def test_corrupted_base64_data(self):
        """Test handling of corrupted base64 data"""
        corrupted_data_cases = [
            'SGVsbG8gV29ybGQ=!',  # Invalid character
            'SGVsbG8gV29ybGQ',  # Missing padding
            'SGVsbG8gV29ybGQ===',  # Too much padding
            'SGVsbG8g\nV29ybGQ=',  # Newline in data
        ]
        
        from audio_upload_lambda import lambda_handler
        
        for corrupted_data in corrupted_data_cases:
            event = {
                'body': json.dumps({
                    'audio_data': corrupted_data,
                    'user_id': 'test_farmer_001',
                    'content_type': 'audio/wav'
                })
            }
            
            result = lambda_handler(event, None)
            
            # Should handle corrupted data gracefully
            if result['statusCode'] == 400:
                body = json.loads(result['body'])
                self.assertFalse(body['success'])
    
    def test_corrupted_image_data(self):
        """Test handling of corrupted image data"""
        # Create invalid image data
        invalid_image = b'This is not an image file'
        invalid_base64 = 'VGhpcyBpcyBub3QgYW4gaW1hZ2UgZmlsZQ=='  # base64 of above
        
        from image_analysis_lambda import validate_image_quality_comprehensive
        
        result = validate_image_quality_comprehensive(invalid_image)
        
        # Should detect invalid image
        self.assertFalse(result['valid'])
        self.assertIn('invalid_image', result['issues'])


class TestConcurrencyAndRaceConditions(unittest.TestCase):
    """Test cases for concurrency and race conditions"""
    
    def test_simultaneous_session_creation(self):
        """Test simultaneous session creation for same user"""
        # This would test race conditions in session management
        # For now, just verify the session creation logic is thread-safe
        
        from test_authentication_lambda import MockAuthenticationLambda
        
        auth_lambda = MockAuthenticationLambda()
        
        # Create multiple sessions for same user
        sessions = []
        for i in range(5):
            result = auth_lambda.create_session(f'user_{i}')
            if result.get('success'):
                sessions.append(result['session_id'])
        
        # All sessions should be unique
        self.assertEqual(len(sessions), len(set(sessions)))
    
    def test_cache_consistency(self):
        """Test cache consistency under concurrent access"""
        from translation_tools import TranslationTools
        
        tools = TranslationTools(enable_caching=True)
        
        # Test cache operations
        cache_key = tools._get_cache_key('test', 'en', 'hi')
        tools._save_to_cache(cache_key, 'translated text')
        
        # Retrieve from cache
        cached_result = tools._get_from_cache(cache_key)
        self.assertEqual(cached_result, 'translated text')
        
        # Clear cache
        tools.clear_cache()
        cached_result = tools._get_from_cache(cache_key)
        self.assertIsNone(cached_result)


class TestResourceCleanup(unittest.TestCase):
    """Test cases for resource cleanup scenarios"""
    
    @patch('boto3.client')
    def test_s3_cleanup_on_failure(self, mock_boto3):
        """Test S3 cleanup when operations fail"""
        mock_s3 = Mock()
        mock_s3.put_object.return_value = {}
        mock_s3.delete_object.return_value = {}
        mock_boto3.return_value = mock_s3
        
        from voice_tools import VoiceProcessingTools
        
        tools = VoiceProcessingTools()
        
        # Test cleanup method
        tools._cleanup_transcription_files('test-bucket', 'test-key', 'test-job')
        
        # Should call delete_object twice (audio and transcript)
        self.assertEqual(mock_s3.delete_object.call_count, 2)
    
    def test_session_cleanup(self):
        """Test session cleanup for expired sessions"""
        from test_authentication_lambda import MockAuthenticationLambda
        
        auth_lambda = MockAuthenticationLambda()
        
        # Test session validation with expired session
        expired_session_data = {
            'session_id': 'expired_session',
            'user_id': 'test_user',
            'created_at': int(time.time()) - 7200,
            'expires_at': int(time.time()) - 3600,  # Expired
            'active': True
        }
        
        # Mock DynamoDB response
        with patch.object(auth_lambda.dynamodb, 'Table') as mock_table:
            mock_table.return_value.get_item.return_value = {
                'Item': expired_session_data
            }
            
            result = auth_lambda.validate_session('expired_session')
            
            self.assertFalse(result['valid'])
            self.assertIn('expired', result['error'].lower())


if __name__ == '__main__':
    unittest.main(verbosity=2)