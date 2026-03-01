"""
Tests for RISE Translation Tools
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.translation_tools import (
    TranslationTools,
    create_translation_tools,
    translate_tool,
    translate_with_fallback_tool,
    context_aware_translate_tool,
    batch_translate_tool
)
from unittest.mock import Mock, patch, MagicMock
import json


class TestTranslationTools:
    """Test suite for TranslationTools class"""
    
    @pytest.fixture
    def mock_aws_clients(self):
        """Mock AWS clients"""
        with patch('boto3.client') as mock_client:
            # Mock Translate client
            mock_translate = Mock()
            mock_s3 = Mock()
            
            def client_factory(service_name, **kwargs):
                if service_name == 'translate':
                    return mock_translate
                elif service_name == 's3':
                    return mock_s3
                return Mock()
            
            mock_client.side_effect = client_factory
            
            yield {
                'translate': mock_translate,
                's3': mock_s3
            }
    
    @pytest.fixture
    def translation_tools(self, mock_aws_clients):
        """Create TranslationTools instance with mocked clients"""
        return TranslationTools(region='us-east-1', enable_caching=True)
    
    def test_initialization(self, translation_tools):
        """Test TranslationTools initialization"""
        assert translation_tools.region == 'us-east-1'
        assert translation_tools.enable_caching is True
        assert len(translation_tools.language_codes) == 9
        assert 'hi' in translation_tools.language_codes
        assert 'en' in translation_tools.language_codes
    
    def test_language_codes_mapping(self, translation_tools):
        """Test language code mappings"""
        assert translation_tools.language_codes['hi']['name'] == 'Hindi'
        assert translation_tools.language_codes['en']['name'] == 'English'
        assert translation_tools.language_codes['ta']['name'] == 'Tamil'
    
    def test_cache_key_generation(self, translation_tools):
        """Test cache key generation"""
        key1 = translation_tools._get_cache_key("Hello", "en", "hi")
        key2 = translation_tools._get_cache_key("Hello", "en", "hi")
        key3 = translation_tools._get_cache_key("Hello", "en", "ta")
        
        assert key1 == key2  # Same input should generate same key
        assert key1 != key3  # Different target language should generate different key
    
    def test_translate_text_success(self, translation_tools, mock_aws_clients):
        """Test successful text translation"""
        # Mock AWS Translate response
        mock_aws_clients['translate'].translate_text.return_value = {
            'TranslatedText': 'नमस्ते',
            'SourceLanguageCode': 'en'
        }
        
        result = translation_tools.translate_text(
            text="Hello",
            target_language="hi",
            source_language="en"
        )
        
        assert result['success'] is True
        assert result['translated_text'] == 'नमस्ते'
        assert result['source_language'] == 'en'
        assert result['target_language'] == 'hi'
        assert result['from_cache'] is False
    
    def test_translate_text_with_auto_detect(self, translation_tools, mock_aws_clients):
        """Test translation with automatic language detection"""
        mock_aws_clients['translate'].translate_text.return_value = {
            'TranslatedText': 'नमस्ते',
            'SourceLanguageCode': 'en'
        }
        
        result = translation_tools.translate_text(
            text="Hello",
            target_language="hi",
            source_language="auto"
        )
        
        assert result['success'] is True
        assert result['source_language'] == 'en'
    
    def test_translate_text_unsupported_language(self, translation_tools):
        """Test translation with unsupported language"""
        result = translation_tools.translate_text(
            text="Hello",
            target_language="fr",  # French not supported
            source_language="en"
        )
        
        assert result['success'] is False
        assert 'Unsupported target language' in result['error']
    
    def test_translate_text_with_caching(self, translation_tools, mock_aws_clients):
        """Test translation caching mechanism"""
        mock_aws_clients['translate'].translate_text.return_value = {
            'TranslatedText': 'नमस्ते',
            'SourceLanguageCode': 'en'
        }
        
        # First call - should hit AWS
        result1 = translation_tools.translate_text("Hello", "hi", "en")
        assert result1['from_cache'] is False
        
        # Second call - should hit cache
        result2 = translation_tools.translate_text("Hello", "hi", "en")
        assert result2['from_cache'] is True
        assert result2['translated_text'] == 'नमस्ते'
        
        # AWS should only be called once
        assert mock_aws_clients['translate'].translate_text.call_count == 1
    
    def test_translate_text_cache_disabled(self, mock_aws_clients):
        """Test translation with caching disabled"""
        tools = TranslationTools(region='us-east-1', enable_caching=False)
        
        mock_aws_clients['translate'].translate_text.return_value = {
            'TranslatedText': 'नमस्ते',
            'SourceLanguageCode': 'en'
        }
        
        # Multiple calls should all hit AWS
        result1 = tools.translate_text("Hello", "hi", "en")
        result2 = tools.translate_text("Hello", "hi", "en")
        
        assert result1['from_cache'] is False
        assert result2['from_cache'] is False
        assert mock_aws_clients['translate'].translate_text.call_count == 2
    
    def test_translate_with_fallback_success(self, translation_tools, mock_aws_clients):
        """Test translation with fallback - primary succeeds"""
        mock_aws_clients['translate'].translate_text.return_value = {
            'TranslatedText': 'வணக்கம்',
            'SourceLanguageCode': 'en'
        }
        
        result = translation_tools.translate_with_fallback("Hello", "ta", "en")
        
        assert result['success'] is True
        assert result['translated_text'] == 'வணக்கம்'
        assert 'fallback_used' not in result or result['fallback_used'] is False
    
    def test_translate_with_fallback_uses_fallback(self, translation_tools, mock_aws_clients):
        """Test translation with fallback - primary fails, fallback succeeds"""
        call_count = [0]
        
        def mock_translate(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call fails
                raise Exception("Translation failed")
            else:
                # Second call (fallback) succeeds
                return {
                    'TranslatedText': 'नमस्ते',
                    'SourceLanguageCode': 'en'
                }
        
        mock_aws_clients['translate'].translate_text.side_effect = mock_translate
        
        result = translation_tools.translate_with_fallback("Hello", "ta", "en", "hi")
        
        assert result['success'] is True
        assert result['fallback_used'] is True
        assert result['original_target'] == 'ta'
        assert result['target_language'] == 'hi'
    
    def test_translate_with_context(self, translation_tools, mock_aws_clients):
        """Test context-aware translation"""
        mock_aws_clients['translate'].translate_text.return_value = {
            'TranslatedText': 'धान की फसल',
            'SourceLanguageCode': 'en'
        }
        
        context = {
            'crop_type': 'rice',
            'region': 'punjab',
            'adapt_measurements': True
        }
        
        result = translation_tools.translate_with_context(
            "Rice crop",
            "hi",
            context=context,
            source_language="en"
        )
        
        assert result['success'] is True
        assert result['context_adapted'] is True
        assert result['context_used'] == context
    
    def test_batch_translate_success(self, translation_tools, mock_aws_clients):
        """Test batch translation"""
        translations = ['नमस्ते', 'धन्यवाद', 'अलविदा']
        call_count = [0]
        
        def mock_translate(**kwargs):
            result = {
                'TranslatedText': translations[call_count[0]],
                'SourceLanguageCode': 'en'
            }
            call_count[0] += 1
            return result
        
        mock_aws_clients['translate'].translate_text.side_effect = mock_translate
        
        texts = ["Hello", "Thank you", "Goodbye"]
        result = translation_tools.batch_translate(texts, "hi", "en")
        
        assert result['success'] is True
        assert result['total_count'] == 3
        assert result['success_count'] == 3
        assert result['error_count'] == 0
        assert len(result['translations']) == 3
    
    def test_batch_translate_partial_failure(self, translation_tools, mock_aws_clients):
        """Test batch translation with some failures"""
        call_count = [0]
        
        def mock_translate(**kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Translation failed")
            return {
                'TranslatedText': f'Translation {call_count[0]}',
                'SourceLanguageCode': 'en'
            }
        
        mock_aws_clients['translate'].translate_text.side_effect = mock_translate
        
        texts = ["Text 1", "Text 2", "Text 3"]
        result = translation_tools.batch_translate(texts, "hi", "en")
        
        assert result['success'] is False
        assert result['success_count'] == 2
        assert result['error_count'] == 1
        assert len(result['errors']) == 1
    
    def test_create_custom_terminology(self, translation_tools, mock_aws_clients):
        """Test custom terminology creation"""
        mock_aws_clients['s3'].put_object.return_value = {}
        mock_aws_clients['translate'].delete_terminology.side_effect = \
            mock_aws_clients['translate'].exceptions.ResourceNotFoundException()
        mock_aws_clients['translate'].import_terminology.return_value = {
            'TerminologyProperties': {
                'TermCount': 10,
                'SourceLanguageCode': 'en',
                'TargetLanguageCodes': ['hi', 'ta']
            }
        }
        
        terminology_data = {
            'en': {'fertilizer': 'fertilizer', 'crop': 'crop'},
            'hi': {'fertilizer': 'उर्वरक', 'crop': 'फसल'}
        }
        
        result = translation_tools.create_custom_terminology(terminology_data)
        
        assert result['success'] is True
        assert result['term_count'] == 10
        assert 'hi' in result['target_languages']
    
    def test_language_preference_management(self, translation_tools):
        """Test language preference get/set"""
        # Get preference (default)
        lang = translation_tools.get_language_preference('user123')
        assert lang == 'hi'  # Default
        
        # Set preference
        result = translation_tools.set_language_preference('user123', 'ta')
        assert result['success'] is True
        assert result['language_code'] == 'ta'
        
        # Set invalid preference
        result = translation_tools.set_language_preference('user123', 'fr')
        assert result['success'] is False
    
    def test_cache_management(self, translation_tools, mock_aws_clients):
        """Test cache management functions"""
        mock_aws_clients['translate'].translate_text.return_value = {
            'TranslatedText': 'नमस्ते',
            'SourceLanguageCode': 'en'
        }
        
        # Add some translations to cache
        translation_tools.translate_text("Hello", "hi", "en")
        translation_tools.translate_text("World", "hi", "en")
        
        # Check cache stats
        stats = translation_tools.get_cache_stats()
        assert stats['enabled'] is True
        assert stats['total_entries'] == 2
        
        # Clear cache
        translation_tools.clear_cache()
        stats = translation_tools.get_cache_stats()
        assert stats['total_entries'] == 0
    
    def test_map_aws_lang_to_code(self, translation_tools):
        """Test AWS language code mapping"""
        assert translation_tools._map_aws_lang_to_code('hi') == 'hi'
        assert translation_tools._map_aws_lang_to_code('en') == 'en'
        assert translation_tools._map_aws_lang_to_code('ta') == 'ta'
        assert translation_tools._map_aws_lang_to_code('unknown') == 'en'  # Default


class TestToolFunctions:
    """Test suite for Strands tool functions"""
    
    @pytest.fixture
    def mock_translation_tools(self):
        """Mock TranslationTools instance"""
        with patch('tools.translation_tools.create_translation_tools') as mock_create:
            mock_tools = Mock()
            mock_create.return_value = mock_tools
            yield mock_tools
    
    def test_translate_tool_success(self, mock_translation_tools):
        """Test translate_tool function"""
        mock_translation_tools.translate_text.return_value = {
            'success': True,
            'translated_text': 'नमस्ते'
        }
        
        result = translate_tool("Hello", "hi", "en")
        assert result == 'नमस्ते'
    
    def test_translate_tool_failure(self, mock_translation_tools):
        """Test translate_tool function with failure"""
        mock_translation_tools.translate_text.return_value = {
            'success': False,
            'error': 'Translation failed'
        }
        
        result = translate_tool("Hello", "hi", "en")
        assert 'Error' in result
    
    def test_translate_with_fallback_tool(self, mock_translation_tools):
        """Test translate_with_fallback_tool function"""
        mock_translation_tools.translate_with_fallback.return_value = {
            'success': True,
            'translated_text': 'नमस्ते',
            'fallback_used': False
        }
        
        result = translate_with_fallback_tool("Hello", "hi", "en")
        assert result == 'नमस्ते'
    
    def test_translate_with_fallback_tool_with_fallback(self, mock_translation_tools):
        """Test translate_with_fallback_tool with fallback used"""
        mock_translation_tools.translate_with_fallback.return_value = {
            'success': True,
            'translated_text': 'नमस्ते',
            'fallback_used': True
        }
        
        result = translate_with_fallback_tool("Hello", "ta", "en")
        assert 'नमस्ते' in result
        assert 'fallback' in result.lower()
    
    def test_context_aware_translate_tool(self, mock_translation_tools):
        """Test context_aware_translate_tool function"""
        mock_translation_tools.translate_with_context.return_value = {
            'success': True,
            'translated_text': 'धान की फसल'
        }
        
        result = context_aware_translate_tool(
            "Rice crop",
            "hi",
            crop_type="rice",
            region="punjab"
        )
        assert result == 'धान की फसल'
    
    def test_batch_translate_tool(self, mock_translation_tools):
        """Test batch_translate_tool function"""
        mock_translation_tools.batch_translate.return_value = {
            'success': True,
            'translations': [
                {'translated': 'नमस्ते'},
                {'translated': 'धन्यवाद'}
            ],
            'success_count': 2
        }
        
        result = batch_translate_tool(["Hello", "Thank you"], "hi")
        result_data = json.loads(result)
        
        assert result_data['count'] == 2
        assert len(result_data['translations']) == 2


class TestIntegration:
    """Integration tests for translation tools"""
    
    @pytest.fixture
    def mock_aws_clients(self):
        """Mock AWS clients for integration tests"""
        with patch('boto3.client') as mock_client:
            mock_translate = Mock()
            mock_s3 = Mock()
            
            def client_factory(service_name, **kwargs):
                if service_name == 'translate':
                    return mock_translate
                elif service_name == 's3':
                    return mock_s3
                return Mock()
            
            mock_client.side_effect = client_factory
            
            yield {
                'translate': mock_translate,
                's3': mock_s3
            }
    
    def test_end_to_end_translation_workflow(self, mock_aws_clients):
        """Test complete translation workflow"""
        # Setup mock responses
        mock_aws_clients['translate'].translate_text.return_value = {
            'TranslatedText': 'आपकी फसल स्वस्थ दिखती है',
            'SourceLanguageCode': 'en'
        }
        
        # Create tools
        tools = TranslationTools(region='us-east-1')
        
        # Translate agricultural advice
        result = tools.translate_text(
            text="Your crop looks healthy",
            target_language="hi",
            source_language="en"
        )
        
        assert result['success'] is True
        assert 'फसल' in result['translated_text']  # 'crop' in Hindi
    
    def test_multilingual_conversation_flow(self, mock_aws_clients):
        """Test multilingual conversation flow"""
        responses = [
            {'TranslatedText': 'नमस्ते, मैं आपकी कैसे मदद कर सकता हूं?', 'SourceLanguageCode': 'en'},
            {'TranslatedText': 'Hello, how can I help you?', 'SourceLanguageCode': 'hi'}
        ]
        
        call_count = [0]
        
        def mock_translate(**kwargs):
            result = responses[call_count[0]]
            call_count[0] += 1
            return result
        
        mock_aws_clients['translate'].translate_text.side_effect = mock_translate
        
        tools = TranslationTools(region='us-east-1')
        
        # English to Hindi
        result1 = tools.translate_text("Hello, how can I help you?", "hi", "en")
        assert result1['success'] is True
        
        # Hindi to English
        result2 = tools.translate_text("नमस्ते, मैं आपकी कैसे मदद कर सकता हूं?", "en", "hi")
        assert result2['success'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
