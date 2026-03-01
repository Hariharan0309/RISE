"""
Property-Based Tests for Language Consistency

Feature: missionai-farmer-agent
Property 1: Language Consistency

For any user input in a supported language (Kannada, English, Hindi),
when the system generates a response, the output language SHALL match
the input language unless explicitly requested otherwise.

Validates: Requirements 1.2, 1.3
"""

import pytest
from hypothesis import given, strategies as st, settings
from tools.aws_services import detect_language, translate_text, text_to_speech


# Custom strategies for generating text in different languages
@st.composite
def kannada_text(draw):
    """Generate text with Kannada characters."""
    # Kannada Unicode range: 0C80-0CFF
    kannada_chars = ''.join(chr(draw(st.integers(min_value=0x0C80, max_value=0x0CFF))) for _ in range(draw(st.integers(min_value=5, max_value=20))))
    return kannada_chars


@st.composite
def hindi_text(draw):
    """Generate text with Devanagari (Hindi) characters."""
    # Devanagari Unicode range: 0900-097F
    devanagari_chars = ''.join(chr(draw(st.integers(min_value=0x0900, max_value=0x097F))) for _ in range(draw(st.integers(min_value=5, max_value=20))))
    return devanagari_chars


@st.composite
def english_text(draw):
    """Generate English text."""
    return draw(st.text(alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')), min_size=10, max_size=100))


# Feature: missionai-farmer-agent, Property 1: Language Consistency
@given(language=st.sampled_from(['kannada', 'english', 'hindi']))
@settings(max_examples=100)
@pytest.mark.property_test
def test_language_consistency_detect(language):
    """
    Property 1: Language Consistency - Detection
    
    For any supported language, the detect_language function should
    correctly identify text in that language.
    """
    # Generate sample text based on language
    if language == 'kannada':
        # Kannada sample text
        sample_texts = [
            'ನಮಸ್ಕಾರ',  # Hello
            'ಕೃಷಿ ಸಲಹೆ',  # Farming advice
            'ಬೆಳೆ ರೋಗ'  # Crop disease
        ]
    elif language == 'hindi':
        # Hindi sample text
        sample_texts = [
            'नमस्ते',  # Hello
            'कृषि सलाह',  # Farming advice
            'फसल रोग'  # Crop disease
        ]
    else:  # english
        sample_texts = [
            'Hello farmer',
            'Crop disease diagnosis',
            'Weather forecast'
        ]
    
    for text in sample_texts:
        detected = detect_language(text)
        # The detected language should match the input language
        assert detected == language, f"Expected {language}, but detected {detected} for text: {text}"


# Feature: missionai-farmer-agent, Property 1: Language Consistency
@given(
    text=st.text(min_size=10, max_size=200),
    language=st.sampled_from(['kannada', 'english', 'hindi'])
)
@settings(max_examples=100, deadline=None)  # Disable deadline for AWS API calls
@pytest.mark.property_test
def test_language_consistency_tts(text, language):
    """
    Property 1: Language Consistency - Text-to-Speech
    
    For any text and language, the text_to_speech function should
    return a response indicating the same language as input.
    """
    result = text_to_speech(text, language)
    
    # If successful, the returned language should match input
    if result['success']:
        assert result['language'] == language, \
            f"TTS language mismatch: input={language}, output={result.get('language')}"


# Feature: missionai-farmer-agent, Property 1: Language Consistency
@given(
    text=st.text(min_size=10, max_size=200),
    source_lang=st.sampled_from(['kannada', 'english', 'hindi']),
    target_lang=st.sampled_from(['kannada', 'english', 'hindi'])
)
@settings(max_examples=100, deadline=None)  # Disable deadline for AWS API calls
@pytest.mark.property_test
def test_language_consistency_translation(text, source_lang, target_lang):
    """
    Property 1: Language Consistency - Translation
    
    For any text translation, the function should correctly report
    source and target languages.
    """
    result = translate_text(text, source_lang, target_lang)
    
    # If successful, the returned languages should match input
    if result['success']:
        assert result['source_language'] == source_lang, \
            f"Source language mismatch: input={source_lang}, output={result.get('source_language')}"
        assert result['target_language'] == target_lang, \
            f"Target language mismatch: input={target_lang}, output={result.get('target_language')}"


# Feature: missionai-farmer-agent, Property 1: Language Consistency
@given(language=st.sampled_from(['kannada', 'english', 'hindi']))
@settings(max_examples=100, deadline=None)  # Disable deadline for AWS API calls
@pytest.mark.property_test
def test_language_consistency_round_trip(language):
    """
    Property 1: Language Consistency - Round Trip
    
    For any language, if we translate from that language to another and back,
    the language labels should remain consistent.
    """
    original_text = "Hello farmer, how can I help you today?"
    
    # Translate from English to target language
    result1 = translate_text(original_text, 'english', language)
    
    if result1['success'] and language != 'english':
        # Translate back to English
        result2 = translate_text(result1['translated_text'], language, 'english')
        
        if result2['success']:
            # Language consistency should be maintained
            assert result2['source_language'] == language
            assert result2['target_language'] == 'english'


# Unit test for specific language detection examples
def test_detect_language_kannada():
    """Test Kannada language detection with specific examples."""
    kannada_samples = [
        'ನಮಸ್ಕಾರ',
        'ಕೃಷಿ ಸಲಹೆ ಬೇಕು',
        'ನನ್ನ ಬೆಳೆಗೆ ರೋಗ ಬಂದಿದೆ'
    ]
    for text in kannada_samples:
        assert detect_language(text) == 'kannada', f"Failed to detect Kannada in: {text}"


def test_detect_language_hindi():
    """Test Hindi language detection with specific examples."""
    hindi_samples = [
        'नमस्ते',
        'कृषि सलाह चाहिए',
        'मेरी फसल में बीमारी है'
    ]
    for text in hindi_samples:
        assert detect_language(text) == 'hindi', f"Failed to detect Hindi in: {text}"


def test_detect_language_english():
    """Test English language detection with specific examples."""
    english_samples = [
        'Hello',
        'I need farming advice',
        'My crop has a disease'
    ]
    for text in english_samples:
        assert detect_language(text) == 'english', f"Failed to detect English in: {text}"


def test_detect_language_empty():
    """Test language detection with empty input."""
    assert detect_language('') == 'english'  # Should default to English
    assert detect_language('   ') == 'english'  # Should default to English


def test_text_to_speech_empty():
    """Test TTS with empty input."""
    result = text_to_speech('', 'english')
    assert result['success'] is False
    assert 'empty' in result['message'].lower()


def test_translate_text_same_language():
    """Test translation when source and target are the same."""
    text = "Hello farmer"
    result = translate_text(text, 'english', 'english')
    assert result['success'] is True
    assert result['translated_text'] == text
    assert 'same language' in result['message'].lower()


def test_translate_text_empty():
    """Test translation with empty input."""
    result = translate_text('', 'english', 'hindi')
    assert result['success'] is False
    assert 'empty' in result['message'].lower()
