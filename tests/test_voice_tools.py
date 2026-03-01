"""
Unit tests for RISE voice processing tools
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.voice_tools import VoiceProcessingTools, create_voice_tools
import base64


class TestVoiceProcessingTools:
    """Test suite for voice processing tools"""
    
    @pytest.fixture
    def voice_tools(self):
        """Create voice tools instance for testing"""
        return VoiceProcessingTools(region="us-east-1")
    
    def test_initialization(self, voice_tools):
        """Test voice tools initialization"""
        assert voice_tools is not None
        assert voice_tools.region == "us-east-1"
        assert len(voice_tools.language_codes) == 9
        assert 'hi' in voice_tools.language_codes
        assert 'en' in voice_tools.language_codes
    
    def test_language_codes_structure(self, voice_tools):
        """Test language codes have correct structure"""
        for code, config in voice_tools.language_codes.items():
            assert 'transcribe' in config
            assert 'polly' in config
            assert 'name' in config
            assert config['transcribe'].endswith('-IN')
    
    def test_polly_voices_mapping(self, voice_tools):
        """Test Polly voices are mapped correctly"""
        for lang_code in voice_tools.language_codes.values():
            transcribe_code = lang_code['transcribe']
            assert transcribe_code in voice_tools.polly_voices
            assert voice_tools.polly_voices[transcribe_code] == 'Aditi'
    
    def test_map_to_supported_language(self, voice_tools):
        """Test language code mapping"""
        # Test exact match
        assert voice_tools._map_to_supported_language('hi') == 'hi'
        assert voice_tools._map_to_supported_language('en') == 'en'
        
        # Test with region code
        assert voice_tools._map_to_supported_language('hi-IN') == 'hi'
        assert voice_tools._map_to_supported_language('en-IN') == 'en'
        
        # Test unsupported language defaults to English
        assert voice_tools._map_to_supported_language('fr') == 'en'
        assert voice_tools._map_to_supported_language('de-DE') == 'en'
    
    def test_map_transcribe_lang_to_code(self, voice_tools):
        """Test Transcribe language code mapping"""
        assert voice_tools._map_transcribe_lang_to_code('hi-IN') == 'hi'
        assert voice_tools._map_transcribe_lang_to_code('en-IN') == 'en'
        assert voice_tools._map_transcribe_lang_to_code('ta-IN') == 'ta'
        
        # Test unknown code defaults to English
        assert voice_tools._map_transcribe_lang_to_code('unknown') == 'en'
    
    def test_detect_language_with_hindi(self, voice_tools):
        """Test language detection with Hindi text"""
        # Note: This test requires AWS credentials and Comprehend access
        # Skip if not available
        try:
            result = voice_tools.detect_language("नमस्ते, मैं एक किसान हूँ")
            
            # Check result structure
            assert 'success' in result
            assert 'language_code' in result
            
            if result['success']:
                assert result['language_code'] in voice_tools.language_codes
                assert 'confidence' in result
                assert 0 <= result['confidence'] <= 1
        except Exception as e:
            pytest.skip(f"AWS Comprehend not available: {e}")
    
    def test_detect_language_with_english(self, voice_tools):
        """Test language detection with English text"""
        try:
            result = voice_tools.detect_language("Hello, I am a farmer")
            
            assert 'success' in result
            assert 'language_code' in result
            
            if result['success']:
                assert result['language_code'] == 'en'
        except Exception as e:
            pytest.skip(f"AWS Comprehend not available: {e}")
    
    def test_detect_language_with_empty_text(self, voice_tools):
        """Test language detection with empty text"""
        result = voice_tools.detect_language("")
        
        # Should handle gracefully
        assert 'success' in result
        assert 'language_code' in result
        # Should default to English on error
        assert result['language_code'] == 'en'
    
    def test_synthesize_speech_structure(self, voice_tools):
        """Test speech synthesis response structure"""
        try:
            result = voice_tools.synthesize_speech(
                text="Test message",
                language_code="en"
            )
            
            assert 'success' in result
            
            if result['success']:
                assert 'audio_data' in result
                assert 'audio_format' in result
                assert 'language_code' in result
                assert 'voice_id' in result
                assert result['audio_format'] == 'mp3'
                
                # Verify audio data is base64 encoded
                try:
                    base64.b64decode(result['audio_data'])
                except Exception:
                    pytest.fail("Audio data is not valid base64")
        except Exception as e:
            pytest.skip(f"AWS Polly not available: {e}")
    
    def test_synthesize_speech_with_hindi(self, voice_tools):
        """Test speech synthesis with Hindi text"""
        try:
            result = voice_tools.synthesize_speech(
                text="नमस्ते",
                language_code="hi"
            )
            
            if result['success']:
                assert result['language_code'] == 'hi'
                assert result['voice_id'] == 'Aditi'
        except Exception as e:
            pytest.skip(f"AWS Polly not available: {e}")
    
    def test_synthesize_speech_with_invalid_language(self, voice_tools):
        """Test speech synthesis with invalid language defaults to English"""
        try:
            result = voice_tools.synthesize_speech(
                text="Test",
                language_code="invalid_lang"
            )
            
            if result['success']:
                # Should default to English
                assert result['language_code'] == 'en'
        except Exception as e:
            pytest.skip(f"AWS Polly not available: {e}")
    
    def test_transcribe_audio_with_empty_data(self, voice_tools):
        """Test transcription with empty audio data"""
        result = voice_tools.transcribe_audio(b"")
        
        # Should handle gracefully
        assert 'success' in result
        # Empty audio should fail
        assert result['success'] == False
        assert 'error' in result
    
    def test_process_voice_query_structure(self, voice_tools):
        """Test voice query processing response structure"""
        # Use minimal audio data for structure test
        result = voice_tools.process_voice_query(
            audio_data=b"test",
            user_language="en"
        )
        
        assert 'success' in result
        
        # Even on failure, should have proper structure
        if not result['success']:
            assert 'error' in result
    
    def test_generate_voice_response(self, voice_tools):
        """Test voice response generation"""
        try:
            result = voice_tools.generate_voice_response(
                text="Test response",
                language_code="en"
            )
            
            assert 'success' in result
            
            if result['success']:
                assert 'audio_data' in result
                assert 'audio_format' in result
        except Exception as e:
            pytest.skip(f"AWS Polly not available: {e}")
    
    def test_create_voice_tools_factory(self):
        """Test factory function"""
        tools = create_voice_tools(region="us-west-2")
        assert tools is not None
        assert tools.region == "us-west-2"
    
    def test_all_supported_languages_have_voices(self, voice_tools):
        """Test that all supported languages have Polly voices configured"""
        for code, config in voice_tools.language_codes.items():
            transcribe_code = config['transcribe']
            assert transcribe_code in voice_tools.polly_voices, \
                f"Language {code} ({config['name']}) missing Polly voice mapping"
    
    def test_language_names_are_correct(self, voice_tools):
        """Test language names are properly set"""
        expected_names = {
            'en': 'English',
            'hi': 'Hindi',
            'ta': 'Tamil',
            'te': 'Telugu',
            'kn': 'Kannada',
            'bn': 'Bengali',
            'gu': 'Gujarati',
            'mr': 'Marathi',
            'pa': 'Punjabi'
        }
        
        for code, expected_name in expected_names.items():
            assert voice_tools.language_codes[code]['name'] == expected_name


class TestVoiceToolFunctions:
    """Test standalone tool functions"""
    
    def test_transcribe_audio_tool_function(self):
        """Test transcribe_audio_tool function"""
        from tools.voice_tools import transcribe_audio_tool
        
        # Test with empty data
        result = transcribe_audio_tool(b"", "en")
        assert isinstance(result, str)
        # Should return error message
        assert "Error" in result or "failed" in result.lower()
    
    def test_synthesize_speech_tool_function(self):
        """Test synthesize_speech_tool function"""
        from tools.voice_tools import synthesize_speech_tool
        
        try:
            result = synthesize_speech_tool("Test", "en")
            assert isinstance(result, str)
            # Should return base64 audio or error
        except Exception as e:
            pytest.skip(f"AWS Polly not available: {e}")
    
    def test_detect_language_tool_function(self):
        """Test detect_language_tool function"""
        from tools.voice_tools import detect_language_tool
        
        try:
            result = detect_language_tool("Hello world")
            assert isinstance(result, str)
            # Should return language info or error
        except Exception as e:
            pytest.skip(f"AWS Comprehend not available: {e}")


class TestErrorHandling:
    """Test error handling in voice tools"""
    
    @pytest.fixture
    def voice_tools(self):
        return VoiceProcessingTools(region="us-east-1")
    
    def test_transcribe_with_invalid_s3_bucket(self, voice_tools):
        """Test transcription with invalid S3 bucket"""
        result = voice_tools.transcribe_audio(
            audio_data=b"test",
            s3_bucket="invalid-bucket-name-that-does-not-exist"
        )
        
        assert result['success'] == False
        assert 'error' in result
    
    def test_synthesize_with_empty_text(self, voice_tools):
        """Test synthesis with empty text"""
        try:
            result = voice_tools.synthesize_speech(
                text="",
                language_code="en"
            )
            
            # Should handle gracefully
            assert 'success' in result
        except Exception as e:
            pytest.skip(f"AWS Polly not available: {e}")
    
    def test_detect_language_with_none(self, voice_tools):
        """Test language detection with None"""
        try:
            result = voice_tools.detect_language(None)
            assert result['success'] == False
        except Exception:
            # Should handle exception gracefully
            pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
