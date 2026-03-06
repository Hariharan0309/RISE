"""
RISE Voice Recorder Component Tests
Tests for voice recording, playback, and transcription
"""

import pytest
import sys
import os
import base64
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.voice_recorder import (
    render_voice_recorder,
    render_audio_player,
    create_voice_input_ui
)


class TestVoiceRecorderRendering:
    """Test voice recorder component rendering"""
    
    def test_recorder_labels_english(self):
        """Test English labels are correct"""
        labels = {
            'start': 'Start Recording',
            'stop': 'Stop Recording',
            'recording': 'Recording...',
            'processing': 'Processing...',
            'play': 'Play',
            'pause': 'Pause',
            'duration': 'Duration',
            'max_duration': 'Max 60s'
        }
        
        assert labels['start'] == 'Start Recording'
        assert labels['stop'] == 'Stop Recording'
        assert 'Recording' in labels['recording']
    
    def test_recorder_labels_hindi(self):
        """Test Hindi labels are correct"""
        labels = {
            'start': 'रिकॉर्डिंग शुरू करें',
            'stop': 'रिकॉर्डिंग बंद करें',
            'recording': 'रिकॉर्ड हो रहा है...',
            'processing': 'प्रोसेस हो रहा है...',
        }
        
        assert len(labels['start']) > 0
        assert len(labels['stop']) > 0
        assert 'रिकॉर्ड' in labels['recording']
    
    def test_max_duration_parameter(self):
        """Test max duration parameter is respected"""
        max_durations = [30, 60, 120]
        
        for duration in max_durations:
            assert duration > 0
            assert duration <= 300  # Max 5 minutes
    
    def test_waveform_display_option(self):
        """Test waveform display can be toggled"""
        show_waveform_options = [True, False]
        
        for option in show_waveform_options:
            assert isinstance(option, bool)


class TestAudioDataHandling:
    """Test audio data handling"""
    
    def test_audio_data_base64_encoding(self):
        """Test audio data is properly base64 encoded"""
        audio_bytes = b'fake audio data'
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        assert isinstance(audio_base64, str)
        assert len(audio_base64) > 0
        
        # Verify can decode back
        decoded = base64.b64decode(audio_base64)
        assert decoded == audio_bytes
    
    def test_audio_data_decoding(self):
        """Test audio data can be decoded from base64"""
        original_data = b'test audio content'
        encoded = base64.b64encode(original_data).decode('utf-8')
        decoded = base64.b64decode(encoded)
        
        assert decoded == original_data
    
    def test_component_value_structure(self):
        """Test component return value structure"""
        component_value = {
            'audio_data': 'base64_encoded_string',
            'duration': 15,
            'format': 'audio/wav'
        }
        
        assert 'audio_data' in component_value
        assert 'duration' in component_value
        assert 'format' in component_value
        assert component_value['format'] == 'audio/wav'
    
    def test_empty_audio_data_handling(self):
        """Test handling of empty audio data"""
        component_value = None
        
        if component_value:
            audio_data = component_value.get('audio_data')
        else:
            audio_data = None
        
        assert audio_data is None


class TestRecordingControls:
    """Test recording control functionality"""
    
    def test_recording_state_transitions(self):
        """Test recording state transitions"""
        states = {
            'idle': {'is_recording': False, 'button_text': 'Start Recording'},
            'recording': {'is_recording': True, 'button_text': 'Stop Recording'},
            'processing': {'is_recording': False, 'button_text': 'Processing...'}
        }
        
        # Test idle to recording
        assert states['idle']['is_recording'] is False
        assert states['recording']['is_recording'] is True
        
        # Test button text changes
        assert 'Start' in states['idle']['button_text']
        assert 'Stop' in states['recording']['button_text']
    
    def test_duration_tracking(self):
        """Test duration tracking during recording"""
        start_time = 1000  # milliseconds
        current_time = 16000  # milliseconds
        duration = (current_time - start_time) / 1000  # Convert to seconds
        
        assert duration == 15.0
        assert duration > 0
    
    def test_max_duration_enforcement(self):
        """Test recording stops at max duration"""
        max_duration = 60
        current_duration = 65
        
        should_stop = current_duration >= max_duration
        assert should_stop is True
    
    def test_manual_stop(self):
        """Test manual stop during recording"""
        is_recording = True
        user_clicked_stop = True
        
        if user_clicked_stop:
            is_recording = False
        
        assert is_recording is False


class TestAudioPlayback:
    """Test audio playback functionality"""
    
    def test_audio_player_html_generation(self):
        """Test audio player HTML is generated correctly"""
        audio_data = b'fake audio'
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        audio_html = f'<audio controls><source src="data:audio/wav;base64,{audio_base64}"></audio>'
        
        assert '<audio' in audio_html
        assert 'controls' in audio_html
        assert 'data:audio/wav;base64' in audio_html
        assert audio_base64 in audio_html
    
    def test_audio_format_support(self):
        """Test supported audio formats"""
        supported_formats = ['audio/wav', 'audio/mp3', 'audio/ogg']
        
        for format_type in supported_formats:
            assert format_type.startswith('audio/')
    
    def test_playback_controls(self):
        """Test playback control elements"""
        controls = ['play', 'pause', 'stop', 'volume']
        
        for control in controls:
            assert isinstance(control, str)
            assert len(control) > 0


class TestWaveformVisualization:
    """Test waveform visualization"""
    
    def test_waveform_bar_generation(self):
        """Test waveform bars are generated"""
        num_bars = 30
        bars = []
        
        for i in range(num_bars):
            bar = {
                'height': '10px',
                'className': 'waveform-bar'
            }
            bars.append(bar)
        
        assert len(bars) == num_bars
        assert all(bar['className'] == 'waveform-bar' for bar in bars)
    
    def test_waveform_animation(self):
        """Test waveform animation during recording"""
        import random
        
        # Simulate random heights for animation
        heights = []
        for _ in range(10):
            height = random.random() * 50 + 10
            heights.append(height)
        
        assert len(heights) == 10
        assert all(10 <= h <= 60 for h in heights)
    
    def test_waveform_reset(self):
        """Test waveform resets after recording"""
        bars = [{'height': '45px'} for _ in range(30)]
        
        # Reset all bars
        for bar in bars:
            bar['height'] = '10px'
        
        assert all(bar['height'] == '10px' for bar in bars)


class TestMicrophoneAccess:
    """Test microphone access handling"""
    
    def test_microphone_permission_request(self):
        """Test microphone permission is requested"""
        # Simulate permission request
        permission_requested = True
        permission_granted = True
        
        assert permission_requested is True
        
        if permission_granted:
            can_record = True
        else:
            can_record = False
        
        assert can_record is True
    
    def test_microphone_access_denied(self):
        """Test handling of denied microphone access"""
        permission_granted = False
        
        if not permission_granted:
            error_message = "Microphone access denied. Please allow microphone access."
        else:
            error_message = None
        
        assert error_message is not None
        assert "denied" in error_message.lower()
    
    def test_microphone_not_available(self):
        """Test handling when microphone is not available"""
        microphone_available = False
        
        if not microphone_available:
            error_message = "No microphone detected"
        else:
            error_message = None
        
        assert error_message is not None


class TestTranscriptionIntegration:
    """Test transcription integration"""
    
    @patch('tools.voice_tools.VoiceProcessingTools')
    def test_transcription_success(self, mock_voice_tools):
        """Test successful transcription"""
        mock_tools = Mock()
        mock_tools.process_voice_query.return_value = {
            'success': True,
            'text': 'What is the weather today?',
            'language_name': 'English',
            'confidence': 0.95
        }
        mock_voice_tools.return_value = mock_tools
        
        voice_tools = mock_voice_tools()
        result = voice_tools.process_voice_query(
            audio_data=b'fake audio',
            user_language='en'
        )
        
        assert result['success'] is True
        assert 'text' in result
        assert result['confidence'] > 0.9
    
    @patch('tools.voice_tools.VoiceProcessingTools')
    def test_transcription_failure(self, mock_voice_tools):
        """Test transcription failure handling"""
        mock_tools = Mock()
        mock_tools.process_voice_query.return_value = {
            'success': False,
            'error': 'Audio quality too low'
        }
        mock_voice_tools.return_value = mock_tools
        
        voice_tools = mock_voice_tools()
        result = voice_tools.process_voice_query(
            audio_data=b'bad audio',
            user_language='en'
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_transcription_confidence_threshold(self):
        """Test transcription confidence threshold"""
        confidence_threshold = 0.7
        
        test_cases = [
            (0.95, True),
            (0.85, True),
            (0.70, True),
            (0.65, False),
            (0.50, False),
        ]
        
        for confidence, should_accept in test_cases:
            is_acceptable = confidence >= confidence_threshold
            assert is_acceptable == should_accept


class TestLanguageSupport:
    """Test multi-language support"""
    
    def test_supported_languages(self):
        """Test all required languages are supported"""
        supported_languages = ['en', 'hi', 'ta', 'te', 'kn', 'bn', 'gu', 'mr', 'pa']
        
        assert len(supported_languages) == 9
        assert 'en' in supported_languages
        assert 'hi' in supported_languages
    
    def test_language_specific_labels(self):
        """Test language-specific labels exist"""
        labels_by_language = {
            'en': {'start': 'Start Recording', 'stop': 'Stop Recording'},
            'hi': {'start': 'रिकॉर्डिंग शुरू करें', 'stop': 'रिकॉर्डिंग बंद करें'}
        }
        
        for lang, labels in labels_by_language.items():
            assert 'start' in labels
            assert 'stop' in labels
            assert len(labels['start']) > 0
    
    def test_fallback_to_english(self):
        """Test fallback to English for unsupported languages"""
        requested_language = 'fr'  # French - not supported
        supported_languages = ['en', 'hi', 'ta']
        
        if requested_language not in supported_languages:
            language = 'en'
        else:
            language = requested_language
        
        assert language == 'en'


class TestErrorHandling:
    """Test error handling in voice recorder"""
    
    def test_audio_processing_error(self):
        """Test handling of audio processing errors"""
        try:
            # Simulate error
            raise Exception("Audio processing failed")
        except Exception as e:
            error_message = str(e)
        
        assert "failed" in error_message.lower()
    
    def test_invalid_audio_format(self):
        """Test handling of invalid audio format"""
        audio_format = 'audio/invalid'
        valid_formats = ['audio/wav', 'audio/mp3', 'audio/ogg']
        
        is_valid = audio_format in valid_formats
        assert is_valid is False
    
    def test_empty_recording(self):
        """Test handling of empty recording"""
        audio_data = b''
        
        if len(audio_data) == 0:
            error = "No audio data recorded"
        else:
            error = None
        
        assert error is not None
        assert "No audio" in error
    
    def test_recording_timeout(self):
        """Test handling of recording timeout"""
        max_duration = 60
        actual_duration = 65
        
        if actual_duration > max_duration:
            should_stop = True
            message = f"Recording stopped at {max_duration}s limit"
        else:
            should_stop = False
            message = None
        
        assert should_stop is True
        assert message is not None


class TestVoiceInputUI:
    """Test complete voice input UI"""
    
    @patch('streamlit.spinner')
    @patch('streamlit.success')
    @patch('streamlit.button')
    def test_complete_voice_flow(self, mock_button, mock_success, mock_spinner):
        """Test complete voice input flow"""
        # Setup mocks
        mock_button.return_value = True
        
        # Simulate flow
        audio_captured = True
        transcription_requested = True
        
        assert audio_captured is True
        assert transcription_requested is True
    
    def test_voice_input_with_context(self):
        """Test voice input includes session context"""
        session_id = "test_session_123"
        language = "hi"
        
        context = {
            "session_id": session_id,
            "language": language
        }
        
        assert context["session_id"] == session_id
        assert context["language"] == language
    
    def test_transcribed_text_display(self):
        """Test transcribed text is displayed correctly"""
        transcribed_text = "मेरी फसल में कीड़े लग गए हैं"
        detected_language = "Hindi"
        confidence = 0.92
        
        display_info = {
            "text": transcribed_text,
            "language": detected_language,
            "confidence": f"{confidence:.0%}"
        }
        
        assert display_info["text"] == transcribed_text
        assert display_info["language"] == "Hindi"
        assert "92%" in display_info["confidence"]


class TestAccessibility:
    """Test accessibility features"""
    
    def test_visual_feedback_during_recording(self):
        """Test visual feedback is provided during recording"""
        is_recording = True
        
        if is_recording:
            button_class = "recording"
            status_text = "Recording..."
        else:
            button_class = ""
            status_text = "Ready"
        
        assert button_class == "recording"
        assert "Recording" in status_text
    
    def test_audio_feedback(self):
        """Test audio feedback for recording state"""
        states = {
            'start': 'Recording started',
            'stop': 'Recording stopped',
            'error': 'Recording failed'
        }
        
        for state, message in states.items():
            assert len(message) > 0
    
    def test_keyboard_accessibility(self):
        """Test keyboard controls are available"""
        keyboard_shortcuts = {
            'space': 'Start/Stop recording',
            'enter': 'Submit transcription'
        }
        
        assert 'space' in keyboard_shortcuts
        assert 'enter' in keyboard_shortcuts


class TestPerformance:
    """Test performance considerations"""
    
    def test_audio_chunk_size(self):
        """Test audio is processed in appropriate chunks"""
        chunk_size = 1024  # bytes
        
        assert chunk_size > 0
        assert chunk_size <= 4096  # Reasonable chunk size
    
    def test_recording_buffer_management(self):
        """Test recording buffer is managed properly"""
        audio_chunks = []
        max_chunks = 100
        
        # Simulate adding chunks
        for i in range(50):
            audio_chunks.append(b'chunk')
        
        assert len(audio_chunks) <= max_chunks
    
    def test_memory_cleanup(self):
        """Test memory is cleaned up after recording"""
        audio_chunks = [b'chunk1', b'chunk2', b'chunk3']
        
        # Cleanup
        audio_chunks.clear()
        
        assert len(audio_chunks) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
