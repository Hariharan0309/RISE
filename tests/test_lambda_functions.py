"""
Comprehensive Unit Tests for RISE Lambda Functions
Tests authentication, voice processing, AI integration, data validation, and error handling
"""

import unittest
import json
import base64
import boto3
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime

# Add tools directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

# Import Lambda functions
from audio_upload_lambda import lambda_handler as audio_upload_handler
from audio_upload_lambda import get_file_extension, create_response
from voice_tools import VoiceProcessingTools, create_voice_tools
from translation_tools import TranslationTools, create_translation_tools
from image_analysis_lambda import lambda_handler as image_analysis_handler
from image_analysis_lambda import analyze_with_bedrock, build_disease_prompt, parse_diagnosis
from soil_analysis_lambda import lambda_handler as soil_analysis_handler
from pest_analysis_lambda import lambda_handler as pest_analysis_handler


class TestAudioUploadLambda(unittest.TestCase):
    """Test cases for audio upload Lambda function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_audio_data = base64.b64encode(b'fake audio data').decode('utf-8')
        self.valid_event = {
            'body': json.dumps({
                'audio_data': self.valid_audio_data,
                'user_id': 'test_farmer_001',
                'content_type': 'audio/wav',
                'language_code': 'hi'
            })
        }
    
    @patch('audio_upload_lambda.s3_client')
    def test_valid_audio_upload(self, mock_s3):
        """Test successful audio upload"""
        # Mock S3 put_object and generate_presigned_url
        mock_s3.put_object.return_value = {}
        mock_s3.generate_presigned_url.return_value = 'https://test-url.com'
        
        result = audio_upload_handler(self.valid_event, None)
        
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertTrue(body['success'])
        self.assertIn('s3_key', body)
        self.assertIn('presigned_url', body)
        mock_s3.put_object.assert_called_once()
    
    def test_missing_audio_data(self):
        """Test error when audio_data is missing"""
        event = {
            'body': json.dumps({
                'user_id': 'test_farmer_001',
                'content_type': 'audio/wav'
            })
        }
        
        result = audio_upload_handler(event, None)
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertIn('Missing audio_data', body['error'])
    
    def test_missing_user_id(self):
        """Test error when user_id is missing"""
        event = {
            'body': json.dumps({
                'audio_data': self.valid_audio_data,
                'content_type': 'audio/wav'
            })
        }
        
        result = audio_upload_handler(event, None)
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertIn('Missing user_id', body['error'])
    
    def test_invalid_content_type(self):
        """Test error with invalid content type"""
        event = {
            'body': json.dumps({
                'audio_data': self.valid_audio_data,
                'user_id': 'test_farmer_001',
                'content_type': 'audio/invalid'
            })
        }
        
        result = audio_upload_handler(event, None)
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertIn('Invalid content type', body['error'])
    
    def test_invalid_base64_data(self):
        """Test error with invalid base64 data"""
        event = {
            'body': json.dumps({
                'audio_data': 'invalid_base64_data!@#',
                'user_id': 'test_farmer_001',
                'content_type': 'audio/wav'
            })
        }
        
        result = audio_upload_handler(event, None)
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertIn('Invalid base64 audio data', body['error'])
    
    def test_empty_audio_file(self):
        """Test error with empty audio file"""
        empty_audio = base64.b64encode(b'').decode('utf-8')
        event = {
            'body': json.dumps({
                'audio_data': empty_audio,
                'user_id': 'test_farmer_001',
                'content_type': 'audio/wav'
            })
        }
        
        result = audio_upload_handler(event, None)
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertIn('Empty audio file', body['error'])
    
    @patch.dict(os.environ, {'MAX_FILE_SIZE': '100'})
    def test_file_size_limit(self):
        """Test file size limit enforcement"""
        large_audio = base64.b64encode(b'x' * 200).decode('utf-8')
        event = {
            'body': json.dumps({
                'audio_data': large_audio,
                'user_id': 'test_farmer_001',
                'content_type': 'audio/wav'
            })
        }
        
        result = audio_upload_handler(event, None)
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertIn('exceeds maximum allowed size', body['error'])
    
    @patch('audio_upload_lambda.s3_client')
    def test_s3_upload_failure(self, mock_s3):
        """Test S3 upload failure handling"""
        mock_s3.put_object.side_effect = Exception('S3 error')
        
        result = audio_upload_handler(self.valid_event, None)
        
        self.assertEqual(result['statusCode'], 500)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertIn('Failed to upload to S3', body['error'])
    
    def test_get_file_extension(self):
        """Test file extension mapping"""
        self.assertEqual(get_file_extension('audio/wav'), 'wav')
        self.assertEqual(get_file_extension('audio/mp3'), 'mp3')
        self.assertEqual(get_file_extension('audio/mpeg'), 'mp3')
        self.assertEqual(get_file_extension('audio/webm'), 'webm')
        self.assertEqual(get_file_extension('audio/ogg'), 'ogg')
        self.assertEqual(get_file_extension('unknown'), 'wav')  # Default
    
    def test_create_response(self):
        """Test response creation with CORS headers"""
        response = create_response(200, {'success': True})
        
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Access-Control-Allow-Origin', response['headers'])
        self.assertEqual(response['headers']['Access-Control-Allow-Origin'], '*')
        self.assertIn('Content-Type', response['headers'])
        
        body = json.loads(response['body'])
        self.assertTrue(body['success'])


class TestVoiceProcessingTools(unittest.TestCase):
    """Test cases for voice processing tools"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.voice_tools = VoiceProcessingTools(region='us-east-1')
        self.test_text = "Hello, this is a test message"
        self.test_audio_data = b'fake audio data'
    
    def test_initialization(self):
        """Test voice tools initialization"""
        self.assertIsNotNone(self.voice_tools.transcribe_client)
        self.assertIsNotNone(self.voice_tools.polly_client)
        self.assertIsNotNone(self.voice_tools.comprehend_client)
        self.assertEqual(self.voice_tools.region, 'us-east-1')
        self.assertIn('hi', self.voice_tools.language_codes)
        self.assertIn('en', self.voice_tools.language_codes)
    
    @patch('voice_tools.boto3.client')
    def test_detect_language_success(self, mock_boto3):
        """Test successful language detection"""
        mock_comprehend = Mock()
        mock_comprehend.detect_dominant_language.return_value = {
            'Languages': [{'LanguageCode': 'hi', 'Score': 0.95}]
        }
        mock_boto3.return_value = mock_comprehend
        
        tools = VoiceProcessingTools()
        result = tools.detect_language(self.test_text)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['language_code'], 'hi')
        self.assertEqual(result['confidence'], 0.95)
    
    @patch('voice_tools.boto3.client')
    def test_detect_language_no_result(self, mock_boto3):
        """Test language detection with no results"""
        mock_comprehend = Mock()
        mock_comprehend.detect_dominant_language.return_value = {'Languages': []}
        mock_boto3.return_value = mock_comprehend
        
        tools = VoiceProcessingTools()
        result = tools.detect_language(self.test_text)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['language_code'], 'en')  # Default fallback
    
    def test_map_to_supported_language(self):
        """Test language code mapping"""
        self.assertEqual(self.voice_tools._map_to_supported_language('hi-IN'), 'hi')
        self.assertEqual(self.voice_tools._map_to_supported_language('en-US'), 'en')
        self.assertEqual(self.voice_tools._map_to_supported_language('fr-FR'), 'en')  # Unsupported
    
    @patch('voice_tools.boto3.client')
    def test_synthesize_speech_success(self, mock_boto3):
        """Test successful speech synthesis"""
        mock_polly = Mock()
        mock_audio_stream = Mock()
        mock_audio_stream.read.return_value = b'fake audio data'
        mock_polly.synthesize_speech.return_value = {'AudioStream': mock_audio_stream}
        mock_boto3.return_value = mock_polly
        
        tools = VoiceProcessingTools()
        result = tools.synthesize_speech(self.test_text, 'hi')
        
        self.assertTrue(result['success'])
        self.assertIn('audio_data', result)
        self.assertEqual(result['language_code'], 'hi')
        self.assertEqual(result['voice_id'], 'Aditi')
    
    @patch('voice_tools.boto3.client')
    def test_synthesize_speech_error(self, mock_boto3):
        """Test speech synthesis error handling"""
        mock_polly = Mock()
        mock_polly.synthesize_speech.side_effect = Exception('Polly error')
        mock_boto3.return_value = mock_polly
        
        tools = VoiceProcessingTools()
        result = tools.synthesize_speech(self.test_text, 'hi')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class TestTranslationTools(unittest.TestCase):
    """Test cases for translation tools"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.translation_tools = TranslationTools(region='us-east-1', enable_caching=True)
        self.test_text = "Hello farmer, how can I help you today?"
    
    def test_initialization(self):
        """Test translation tools initialization"""
        self.assertIsNotNone(self.translation_tools.translate_client)
        self.assertEqual(self.translation_tools.region, 'us-east-1')
        self.assertTrue(self.translation_tools.enable_caching)
        self.assertIn('hi', self.translation_tools.language_codes)
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        key1 = self.translation_tools._get_cache_key("hello", "en", "hi")
        key2 = self.translation_tools._get_cache_key("hello", "en", "hi")
        key3 = self.translation_tools._get_cache_key("hello", "en", "ta")
        
        self.assertEqual(key1, key2)  # Same inputs should generate same key
        self.assertNotEqual(key1, key3)  # Different inputs should generate different keys
    
    @patch('translation_tools.boto3.client')
    def test_translate_text_success(self, mock_boto3):
        """Test successful text translation"""
        mock_translate = Mock()
        mock_translate.translate_text.return_value = {
            'TranslatedText': 'नमस्ते किसान, आज मैं आपकी कैसे मदद कर सकता हूं?',
            'SourceLanguageCode': 'en'
        }
        mock_boto3.return_value = mock_translate
        
        tools = TranslationTools(enable_caching=False)
        result = tools.translate_text(self.test_text, 'hi', 'en')
        
        self.assertTrue(result['success'])
        self.assertIn('translated_text', result)
        self.assertEqual(result['source_language'], 'en')
        self.assertEqual(result['target_language'], 'hi')
    
    @patch('translation_tools.boto3.client')
    def test_translate_text_error(self, mock_boto3):
        """Test translation error handling"""
        mock_translate = Mock()
        mock_translate.translate_text.side_effect = Exception('Translation error')
        mock_boto3.return_value = mock_translate
        
        tools = TranslationTools(enable_caching=False)
        result = tools.translate_text(self.test_text, 'hi', 'en')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_unsupported_language(self):
        """Test unsupported language handling"""
        result = self.translation_tools.translate_text(self.test_text, 'unsupported')
        
        self.assertFalse(result['success'])
        self.assertIn('Unsupported target language', result['error'])
    
    @patch('translation_tools.boto3.client')
    def test_translate_with_fallback(self, mock_boto3):
        """Test translation with fallback mechanism"""
        mock_translate = Mock()
        # First call fails, second succeeds
        mock_translate.translate_text.side_effect = [
            Exception('Translation failed'),
            {
                'TranslatedText': 'नमस्ते किसान',
                'SourceLanguageCode': 'en'
            }
        ]
        mock_boto3.return_value = mock_translate
        
        tools = TranslationTools(enable_caching=False)
        result = tools.translate_with_fallback(self.test_text, 'unsupported', 'en', 'hi')
        
        self.assertTrue(result['success'])
        self.assertTrue(result.get('fallback_used', False))
        self.assertEqual(result['original_target'], 'unsupported')
    
    def test_batch_translate(self):
        """Test batch translation functionality"""
        texts = ["Hello", "Goodbye", "Thank you"]
        
        with patch.object(self.translation_tools, 'translate_text') as mock_translate:
            mock_translate.side_effect = [
                {'success': True, 'translated_text': 'नमस्ते'},
                {'success': True, 'translated_text': 'अलविदा'},
                {'success': True, 'translated_text': 'धन्यवाद'}
            ]
            
            result = self.translation_tools.batch_translate(texts, 'hi')
            
            self.assertTrue(result['success'])
            self.assertEqual(result['success_count'], 3)
            self.assertEqual(result['error_count'], 0)
            self.assertEqual(len(result['translations']), 3)


class TestImageAnalysisLambda(unittest.TestCase):
    """Test cases for image analysis Lambda function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_image_data = base64.b64encode(b'fake image data').decode('utf-8')
        self.valid_event = {
            'body': json.dumps({
                'image_data': self.valid_image_data,
                'user_id': 'test_farmer_001',
                'crop_type': 'wheat',
                'additional_context': 'Leaves have brown spots',
                'language_code': 'en'
            })
        }
    
    @patch('image_analysis_lambda.s3_client')
    @patch('image_analysis_lambda.bedrock_runtime')
    @patch('image_analysis_lambda.diagnosis_table')
    @patch('image_analysis_lambda.validate_image_quality_comprehensive')
    def test_successful_image_analysis(self, mock_validate, mock_table, mock_bedrock, mock_s3):
        """Test successful image analysis"""
        # Mock image validation
        mock_validate.return_value = {'valid': True}
        
        # Mock S3 upload
        mock_s3.put_object.return_value = {}
        
        # Mock Bedrock response
        mock_bedrock.invoke_model.return_value = {
            'body': Mock(read=lambda: json.dumps({
                'content': [{'text': 'Disease Name: Leaf Rust\nConfidence: 85%\nSeverity: medium'}]
            }).encode())
        }
        
        # Mock DynamoDB
        mock_table.put_item.return_value = {}
        
        result = image_analysis_handler(self.valid_event, None)
        
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertTrue(body['success'])
        self.assertIn('diagnosis_id', body)
        self.assertIn('diseases', body)
    
    def test_missing_image_data(self):
        """Test error when image_data is missing"""
        event = {
            'body': json.dumps({
                'user_id': 'test_farmer_001',
                'crop_type': 'wheat'
            })
        }
        
        result = image_analysis_handler(event, None)
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertIn('Missing image_data', body['error'])
    
    @patch('image_analysis_lambda.validate_image_quality_comprehensive')
    def test_poor_image_quality(self, mock_validate):
        """Test poor image quality handling"""
        mock_validate.return_value = {
            'valid': False,
            'issues': ['low_resolution', 'blurry'],
            'guidance': ['Take higher resolution photo', 'Ensure better focus']
        }
        
        result = image_analysis_handler(self.valid_event, None)
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertEqual(body['error'], 'poor_image_quality')
        self.assertIn('validation', body)
    
    def test_build_disease_prompt(self):
        """Test disease prompt building"""
        prompt = build_disease_prompt('wheat', 'brown spots on leaves', 'en')
        
        self.assertIn('wheat', prompt)
        self.assertIn('brown spots on leaves', prompt)
        self.assertIn('DISEASES DETECTED', prompt)
        self.assertIn('TREATMENT RECOMMENDATIONS', prompt)
    
    def test_parse_diagnosis(self):
        """Test diagnosis parsing"""
        analysis_text = """
        1. DISEASES DETECTED:
           - Disease Name: Leaf Rust
           - Confidence: 85%
           - Severity: medium
        
        2. TREATMENT RECOMMENDATIONS:
           - Chemical Treatment: Apply fungicide
        """
        
        diagnosis = parse_diagnosis(analysis_text)
        
        self.assertIn('Leaf Rust', diagnosis['diseases'])
        self.assertEqual(diagnosis['confidence_score'], 0.85)
        self.assertEqual(diagnosis['severity'], 'medium')
        self.assertFalse(diagnosis['multiple_issues'])


class TestSoilAnalysisLambda(unittest.TestCase):
    """Test cases for soil analysis Lambda function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_image_event = {
            'body': json.dumps({
                'analysis_type': 'image',
                'image_data': base64.b64encode(b'fake soil image').decode('utf-8'),
                'user_id': 'test_farmer_001',
                'farm_id': 'farm_test_001',
                'location': {'state': 'Karnataka', 'district': 'Bangalore'},
                'language_code': 'en'
            })
        }
        
        self.valid_test_data_event = {
            'body': json.dumps({
                'analysis_type': 'test_data',
                'test_data': {
                    'ph': 6.5,
                    'nitrogen': 'low',
                    'phosphorus': 'medium',
                    'potassium': 'high',
                    'organic_matter': 2.5
                },
                'user_id': 'test_farmer_001',
                'farm_id': 'farm_test_001',
                'location': {'state': 'Karnataka', 'district': 'Bangalore'},
                'language_code': 'en'
            })
        }
    
    def test_missing_user_id(self):
        """Test error when user_id is missing"""
        event = {
            'body': json.dumps({
                'analysis_type': 'image',
                'farm_id': 'farm_test_001'
            })
        }
        
        result = soil_analysis_handler(event, None)
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertIn('Missing user_id', body['error'])
    
    def test_missing_farm_id(self):
        """Test error when farm_id is missing"""
        event = {
            'body': json.dumps({
                'analysis_type': 'image',
                'user_id': 'test_farmer_001'
            })
        }
        
        result = soil_analysis_handler(event, None)
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertIn('Missing farm_id', body['error'])
    
    def test_invalid_analysis_type(self):
        """Test error with invalid analysis type"""
        event = {
            'body': json.dumps({
                'analysis_type': 'invalid',
                'user_id': 'test_farmer_001',
                'farm_id': 'farm_test_001'
            })
        }
        
        result = soil_analysis_handler(event, None)
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertIn('Invalid analysis_type', body['error'])
    
    def test_missing_image_data_for_image_analysis(self):
        """Test error when image_data is missing for image analysis"""
        event = {
            'body': json.dumps({
                'analysis_type': 'image',
                'user_id': 'test_farmer_001',
                'farm_id': 'farm_test_001'
            })
        }
        
        result = soil_analysis_handler(event, None)
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertIn('Missing image_data for image analysis', body['error'])
    
    def test_missing_test_data_for_test_analysis(self):
        """Test error when test_data is missing for test data analysis"""
        event = {
            'body': json.dumps({
                'analysis_type': 'test_data',
                'user_id': 'test_farmer_001',
                'farm_id': 'farm_test_001'
            })
        }
        
        result = soil_analysis_handler(event, None)
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertIn('Missing test_data for test data analysis', body['error'])


class TestPestAnalysisLambda(unittest.TestCase):
    """Test cases for pest analysis Lambda function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_image_data = base64.b64encode(b'fake pest image').decode('utf-8')
        self.valid_event = {
            'body': json.dumps({
                'image_data': self.valid_image_data,
                'user_id': 'test_farmer_001',
                'crop_type': 'wheat',
                'additional_context': 'Small insects on leaves',
                'language_code': 'en'
            })
        }
    
    @patch('pest_analysis_lambda.s3_client')
    @patch('pest_analysis_lambda.bedrock_runtime')
    @patch('pest_analysis_lambda.pest_diagnosis_table')
    @patch('pest_analysis_lambda.validate_image_quality')
    def test_successful_pest_analysis(self, mock_validate, mock_table, mock_bedrock, mock_s3):
        """Test successful pest analysis"""
        # Mock image validation
        mock_validate.return_value = {'valid': True}
        
        # Mock S3 upload
        mock_s3.put_object.return_value = {}
        
        # Mock Bedrock response
        mock_bedrock.invoke_model.return_value = {
            'body': Mock(read=lambda: json.dumps({
                'content': [{'text': 'Pest Species: Aphids\nConfidence: 90%\nSeverity: medium\nLifecycle Stage: adult'}]
            }).encode())
        }
        
        # Mock DynamoDB
        mock_table.put_item.return_value = {}
        
        result = pest_analysis_handler(self.valid_event, None)
        
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertTrue(body['success'])
        self.assertIn('diagnosis_id', body)
        self.assertIn('pests', body)
    
    def test_missing_image_data(self):
        """Test error when image_data is missing"""
        event = {
            'body': json.dumps({
                'user_id': 'test_farmer_001',
                'crop_type': 'wheat'
            })
        }
        
        result = pest_analysis_handler(event, None)
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertIn('Missing image_data', body['error'])


class TestErrorHandlingAndEdgeCases(unittest.TestCase):
    """Test cases for error handling and edge cases across all Lambda functions"""
    
    def test_malformed_json_body(self):
        """Test handling of malformed JSON in request body"""
        event = {'body': 'invalid json {'}
        
        # Test with audio upload lambda
        result = audio_upload_handler(event, None)
        self.assertEqual(result['statusCode'], 500)
        
        # Test with image analysis lambda
        result = image_analysis_handler(event, None)
        self.assertEqual(result['statusCode'], 500)
    
    def test_empty_request_body(self):
        """Test handling of empty request body"""
        event = {}
        
        # Test with audio upload lambda
        result = audio_upload_handler(event, None)
        self.assertEqual(result['statusCode'], 400)
        
        # Test with image analysis lambda
        result = image_analysis_handler(event, None)
        self.assertEqual(result['statusCode'], 400)
    
    def test_string_body_parsing(self):
        """Test parsing of string body vs dict body"""
        # String body
        string_event = {
            'body': json.dumps({
                'user_id': 'test_farmer_001'
            })
        }
        
        # Dict body
        dict_event = {
            'body': {
                'user_id': 'test_farmer_001'
            }
        }
        
        # Both should be handled correctly (though may fail validation for other reasons)
        result1 = audio_upload_handler(string_event, None)
        result2 = audio_upload_handler(dict_event, None)
        
        # Both should parse without JSON errors
        self.assertIsInstance(result1, dict)
        self.assertIsInstance(result2, dict)
    
    @patch('audio_upload_lambda.logger')
    def test_exception_logging(self, mock_logger):
        """Test that exceptions are properly logged"""
        event = {'body': 'invalid json'}
        
        audio_upload_handler(event, None)
        
        # Verify that error was logged
        mock_logger.error.assert_called()


class TestDataValidationAndTransformation(unittest.TestCase):
    """Test cases for data validation and transformation logic"""
    
    def test_language_code_validation(self):
        """Test language code validation in voice tools"""
        tools = VoiceProcessingTools()
        
        # Valid language codes
        self.assertIn('hi', tools.language_codes)
        self.assertIn('en', tools.language_codes)
        self.assertIn('ta', tools.language_codes)
        
        # Language code mapping
        self.assertEqual(tools.language_codes['hi']['transcribe'], 'hi-IN')
        self.assertEqual(tools.language_codes['hi']['polly'], 'hi-IN')
    
    def test_file_size_validation(self):
        """Test file size validation logic"""
        # Test with different file sizes
        small_data = base64.b64encode(b'x' * 100).decode('utf-8')
        large_data = base64.b64encode(b'x' * (10 * 1024 * 1024 + 1)).decode('utf-8')  # > 10MB
        
        small_event = {
            'body': json.dumps({
                'audio_data': small_data,
                'user_id': 'test_farmer_001',
                'content_type': 'audio/wav'
            })
        }
        
        large_event = {
            'body': json.dumps({
                'audio_data': large_data,
                'user_id': 'test_farmer_001',
                'content_type': 'audio/wav'
            })
        }
        
        # Small file should pass size validation (may fail S3 upload in test)
        with patch('audio_upload_lambda.s3_client'):
            result_small = audio_upload_handler(small_event, None)
            # Should not fail due to size
            if result_small['statusCode'] == 400:
                body = json.loads(result_small['body'])
                self.assertNotIn('exceeds maximum', body.get('error', ''))
        
        # Large file should fail size validation
        result_large = audio_upload_handler(large_event, None)
        self.assertEqual(result_large['statusCode'], 400)
        body = json.loads(result_large['body'])
        self.assertIn('exceeds maximum', body['error'])
    
    def test_content_type_validation(self):
        """Test content type validation"""
        valid_types = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/webm', 'audio/ogg']
        invalid_types = ['audio/invalid', 'video/mp4', 'text/plain']
        
        for content_type in valid_types:
            event = {
                'body': json.dumps({
                    'audio_data': base64.b64encode(b'test').decode('utf-8'),
                    'user_id': 'test_farmer_001',
                    'content_type': content_type
                })
            }
            
            with patch('audio_upload_lambda.s3_client'):
                result = audio_upload_handler(event, None)
                # Should not fail due to content type
                if result['statusCode'] == 400:
                    body = json.loads(result['body'])
                    self.assertNotIn('Invalid content type', body.get('error', ''))
        
        for content_type in invalid_types:
            event = {
                'body': json.dumps({
                    'audio_data': base64.b64encode(b'test').decode('utf-8'),
                    'user_id': 'test_farmer_001',
                    'content_type': content_type
                })
            }
            
            result = audio_upload_handler(event, None)
            self.assertEqual(result['statusCode'], 400)
            body = json.loads(result['body'])
            self.assertIn('Invalid content type', body['error'])


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)