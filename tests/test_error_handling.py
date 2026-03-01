"""
Property-Based Tests for Error Handling

Feature: missionai-farmer-agent
Property 24: Error Handling for Tool Failures

For any tool call that fails (API timeout, invalid response, service error),
the calling agent SHALL catch the error and return a user-friendly error
message rather than crashing.

Validates: Requirements 11.6, 14.5
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from tools.aws_services import (
    safe_text_to_speech,
    safe_translate_text,
    safe_transcribe_audio,
    get_circuit_breaker_status,
    reset_circuit_breaker,
    CircuitBreaker
)


# Feature: missionai-farmer-agent, Property 24: Error Handling for Tool Failures
@given(
    text=st.text(min_size=1, max_size=200),
    language=st.sampled_from(['kannada', 'english', 'hindi'])
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
def test_error_handling_tts_graceful_failure(text, language):
    """
    Property 24: Error Handling - Text-to-Speech Graceful Failure
    
    For any TTS call that fails, the function should return a dict with
    success=False and a user-friendly message, not crash.
    """
    # Mock Polly to raise an error
    with patch('tools.aws_services.AWSServiceClients') as mock_clients:
        mock_polly = MagicMock()
        mock_polly.synthesize_speech.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
            'synthesize_speech'
        )
        mock_clients.return_value.polly = mock_polly
        
        # Call safe TTS function
        result = safe_text_to_speech(text, language)
        
        # Should not crash, should return error response
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'success' in result, "Result should have 'success' field"
        assert result['success'] is False, "Result should indicate failure"
        assert 'message' in result or 'error' in result, "Result should have error message"


# Feature: missionai-farmer-agent, Property 24: Error Handling for Tool Failures
@given(
    text=st.text(min_size=1, max_size=200),
    source_lang=st.sampled_from(['kannada', 'english', 'hindi']),
    target_lang=st.sampled_from(['kannada', 'english', 'hindi'])
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
def test_error_handling_translate_graceful_failure(text, source_lang, target_lang):
    """
    Property 24: Error Handling - Translation Graceful Failure
    
    For any translation call that fails, the function should return a dict
    with success=False and fallback to original text.
    """
    # Mock Translate to raise an error
    with patch('tools.aws_services.AWSServiceClients') as mock_clients:
        mock_translate = MagicMock()
        mock_translate.translate_text.side_effect = ClientError(
            {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
            'translate_text'
        )
        mock_clients.return_value.translate = mock_translate
        
        # Call safe translate function
        result = safe_translate_text(text, source_lang, target_lang)
        
        # Should not crash, should return error response with fallback
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'success' in result, "Result should have 'success' field"
        # In fallback mode, it returns the original text
        assert 'translated_text' in result, "Result should have translated_text field"
        assert 'message' in result or 'error' in result, "Result should have error message"


# Feature: missionai-farmer-agent, Property 24: Error Handling for Tool Failures
@given(language=st.sampled_from(['kannada', 'english', 'hindi']))
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
def test_error_handling_transcribe_graceful_failure(language):
    """
    Property 24: Error Handling - Transcription Graceful Failure
    
    For any transcription call that fails, the function should return a dict
    with success=False and a helpful message.
    """
    # Create dummy audio bytes
    audio_bytes = b'dummy_audio_data'
    
    # Mock Transcribe to raise an error
    with patch('tools.aws_services.AWSServiceClients') as mock_clients:
        mock_transcribe = MagicMock()
        mock_transcribe.list_transcription_jobs.side_effect = ClientError(
            {'Error': {'Code': 'InternalFailure', 'Message': 'Internal error'}},
            'list_transcription_jobs'
        )
        mock_clients.return_value.transcribe = mock_transcribe
        
        # Call safe transcribe function
        result = safe_transcribe_audio(audio_bytes, language)
        
        # Should not crash, should return error response
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'success' in result, "Result should have 'success' field"
        assert 'message' in result or 'error' in result, "Result should have error message"


# Feature: missionai-farmer-agent, Property 24: Error Handling for Tool Failures
@given(failure_count=st.integers(min_value=0, max_value=10))
@settings(max_examples=100)
@pytest.mark.property_test
def test_circuit_breaker_state_transitions(failure_count):
    """
    Property 24: Error Handling - Circuit Breaker State Transitions
    
    For any number of failures, the circuit breaker should transition states
    correctly and never crash.
    """
    cb = CircuitBreaker(failure_threshold=5, timeout=1)
    
    # Simulate failures
    for i in range(failure_count):
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))
        except Exception:
            pass  # Expected
    
    # Circuit breaker should be in a valid state
    assert cb.state in ['CLOSED', 'OPEN', 'HALF_OPEN'], \
        f"Circuit breaker in invalid state: {cb.state}"
    
    # If failures exceed threshold, should be OPEN
    if failure_count >= 5:
        assert cb.state == 'OPEN', \
            f"Circuit breaker should be OPEN after {failure_count} failures"
    
    # Failure count should be tracked
    assert cb.failure_count >= 0, "Failure count should be non-negative"


# Unit tests for specific error scenarios

def test_circuit_breaker_opens_after_threshold():
    """Test that circuit breaker opens after reaching failure threshold."""
    cb = CircuitBreaker(failure_threshold=3, timeout=1)
    
    # Cause 3 failures
    for i in range(3):
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))
        except Exception:
            pass
    
    # Circuit should be OPEN
    assert cb.state == 'OPEN'
    assert cb.failure_count == 3


def test_circuit_breaker_blocks_when_open():
    """Test that circuit breaker blocks calls when OPEN."""
    cb = CircuitBreaker(failure_threshold=2, timeout=1)
    
    # Cause failures to open circuit
    for i in range(2):
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))
        except Exception:
            pass
    
    # Circuit should be OPEN
    assert cb.state == 'OPEN'
    
    # Next call should be blocked
    with pytest.raises(Exception, match="Circuit breaker is OPEN"):
        cb.call(lambda: "success")


def test_circuit_breaker_recovers_after_timeout():
    """Test that circuit breaker enters HALF_OPEN after timeout."""
    import time
    
    cb = CircuitBreaker(failure_threshold=2, timeout=1)
    
    # Cause failures to open circuit
    for i in range(2):
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))
        except Exception:
            pass
    
    assert cb.state == 'OPEN'
    
    # Wait for timeout
    time.sleep(1.1)
    
    # Next call should enter HALF_OPEN
    try:
        cb.call(lambda: "success")
    except:
        pass
    
    # Should have attempted HALF_OPEN state
    assert cb.state in ['HALF_OPEN', 'CLOSED']


def test_circuit_breaker_resets_on_success():
    """Test that circuit breaker resets failure count on success."""
    cb = CircuitBreaker(failure_threshold=5, timeout=1)
    
    # Cause some failures
    for i in range(3):
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))
        except Exception:
            pass
    
    assert cb.failure_count == 3
    
    # Successful call should reset
    result = cb.call(lambda: "success")
    assert result == "success"
    assert cb.failure_count == 0
    assert cb.state == 'CLOSED'


def test_get_circuit_breaker_status():
    """Test getting circuit breaker status."""
    status = get_circuit_breaker_status('polly')
    
    assert status['exists'] is True
    assert status['service'] == 'polly'
    assert 'state' in status
    assert 'failure_count' in status


def test_reset_circuit_breaker():
    """Test manually resetting a circuit breaker."""
    # Get initial status
    status_before = get_circuit_breaker_status('polly')
    
    # Reset
    result = reset_circuit_breaker('polly')
    
    assert result['success'] is True
    assert result['service'] == 'polly'
    
    # Check status after reset
    status_after = get_circuit_breaker_status('polly')
    assert status_after['state'] == 'CLOSED'
    assert status_after['failure_count'] == 0


def test_safe_tts_returns_fallback_on_error():
    """Test that safe_text_to_speech returns fallback response on error."""
    with patch('tools.aws_services.text_to_speech_with_retry') as mock_tts:
        mock_tts.side_effect = Exception("Service unavailable")
        
        result = safe_text_to_speech("Hello", "english", fallback_text="Hello (text only)")
        
        assert result['success'] is False
        assert result['fallback_mode'] is True
        assert 'text' in result
        assert 'message' in result


def test_safe_translate_returns_original_on_error():
    """Test that safe_translate_text returns original text on error."""
    with patch('tools.aws_services.translate_text_with_retry') as mock_translate:
        mock_translate.side_effect = Exception("Service unavailable")
        
        original_text = "Hello farmer"
        result = safe_translate_text(original_text, "english", "hindi")
        
        assert result['success'] is False
        assert result['fallback_mode'] is True
        assert result['translated_text'] == original_text


def test_safe_transcribe_returns_helpful_message_on_error():
    """Test that safe_transcribe_audio returns helpful message on error."""
    with patch('tools.aws_services.transcribe_audio_with_retry') as mock_transcribe:
        mock_transcribe.side_effect = Exception("Service unavailable")
        
        result = safe_transcribe_audio(b'audio_data', "english")
        
        assert result['success'] is False
        assert result['fallback_mode'] is True
        assert 'message' in result
        assert 'try again' in result['message'].lower() or 'text input' in result['message'].lower()
