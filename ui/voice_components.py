"""
Voice input components for Streamlit UI
Handles audio recording, transcription, and TTS
"""

import streamlit as st
from audio_recorder_streamlit import audio_recorder
import boto3
from typing import Optional, Tuple
import io
import os
from datetime import datetime
import base64

# Import AWS services
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.aws_services import transcribe_audio, text_to_speech


def render_voice_input(language: str = 'english') -> Optional[str]:
    """
    Render voice input component with recording button
    
    Args:
        language: Language for transcription (english, kannada, hindi)
    
    Returns:
        Transcribed text if audio was recorded, None otherwise
    """
    st.markdown("### 🎤 Voice Input")
    
    # Language code mapping
    language_codes = {
        'english': 'en-IN',
        'kannada': 'kn-IN',
        'hindi': 'hi-IN'
    }
    
    # Audio recorder component
    audio_bytes = audio_recorder(
        text="Click to record",
        recording_color="#e74c3c",
        neutral_color="#3498db",
        icon_name="microphone",
        icon_size="3x",
        pause_threshold=2.0,
        sample_rate=16000
    )
    
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        
        # Show processing indicator
        with st.spinner("Transcribing your voice..."):
            try:
                # Transcribe audio
                lang_code = language_codes.get(language, 'en-IN')
                transcribed_text = transcribe_audio(audio_bytes, lang_code)
                
                if transcribed_text:
                    st.success("✅ Transcription complete!")
                    st.info(f"**You said:** {transcribed_text}")
                    return transcribed_text
                else:
                    st.error("Could not transcribe audio. Please try again.")
                    return None
                    
            except Exception as e:
                st.error(f"Transcription error: {str(e)}")
                st.info("Please check your AWS credentials and try again.")
                return None
    
    return None


def render_language_selector() -> str:
    """
    Render language selection dropdown
    
    Returns:
        Selected language code
    """
    languages = {
        'English': 'english',
        'ಕನ್ನಡ (Kannada)': 'kannada',
        'हिंदी (Hindi)': 'hindi'
    }
    
    selected = st.selectbox(
        "Select Language / ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ / भाषा चुनें",
        options=list(languages.keys()),
        index=0
    )
    
    return languages[selected]


def upload_audio_to_s3(audio_bytes: bytes, user_id: str) -> Optional[str]:
    """
    Upload audio file to S3 for processing
    
    Args:
        audio_bytes: Audio data as bytes
        user_id: User identifier
    
    Returns:
        S3 URL if successful, None otherwise
    """
    try:
        s3_client = boto3.client('s3')
        bucket_name = os.getenv('S3_BUCKET_NAME', 'missionai-audio')
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"audio/{user_id}/{timestamp}.wav"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=audio_bytes,
            ContentType='audio/wav'
        )
        
        # Generate URL
        url = f"s3://{bucket_name}/{filename}"
        return url
        
    except Exception as e:
        st.error(f"Failed to upload audio: {str(e)}")
        return None


def render_audio_playback(text: str, language: str, message_id: str) -> None:
    """
    Render audio playback button for text-to-speech with caching
    
    Args:
        text: Text to convert to speech
        language: Language for TTS
        message_id: Unique identifier for caching
    """
    # Initialize audio cache if not exists
    if 'audio_cache' not in st.session_state:
        st.session_state.audio_cache = {}
    
    # Check cache first
    cache_key = f"audio_{message_id}"
    
    if st.button(f"🔊 Listen", key=f"listen_btn_{message_id}"):
        # Check if audio is already cached in session state
        if cache_key in st.session_state.audio_cache:
            audio_bytes = st.session_state.audio_cache[cache_key]
            st.audio(audio_bytes, format="audio/mp3")
            st.caption("🔄 Playing from cache (offline available)")
        else:
            # Generate audio
            with st.spinner("Generating audio..."):
                try:
                    audio_bytes = text_to_speech(text, language)
                    
                    if audio_bytes:
                        # Cache for future use (both online and offline)
                        st.session_state.audio_cache[cache_key] = audio_bytes
                        st.audio(audio_bytes, format="audio/mp3")
                        st.caption("✅ Audio cached for offline playback")
                    else:
                        st.error("Could not generate audio")
                        
                except Exception as e:
                    st.error(f"TTS error: {str(e)}")
                    st.info("Audio playback requires AWS credentials. Check your .env file.")


def render_voice_feedback(is_recording: bool) -> None:
    """
    Render visual feedback during voice recording
    
    Args:
        is_recording: Whether recording is in progress
    """
    if is_recording:
        st.markdown("""
        <div style="
            background-color: #e74c3c;
            color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            text-align: center;
            font-weight: 600;
            animation: pulse 1.5s infinite;
        ">
            🔴 Recording... Speak now
        </div>
        <style>
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.6; }
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.info("👆 Click the microphone button to start recording")


def get_audio_duration(audio_bytes: bytes) -> float:
    """
    Get duration of audio in seconds
    
    Args:
        audio_bytes: Audio data
    
    Returns:
        Duration in seconds
    """
    try:
        import wave
        with wave.open(io.BytesIO(audio_bytes), 'rb') as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            duration = frames / float(rate)
            return duration
    except:
        return 0.0



def render_audio_player_controls(audio_bytes: bytes, message_id: str) -> None:
    """
    Render audio player with playback controls
    
    Args:
        audio_bytes: Audio data
        message_id: Unique identifier
    """
    # Display audio player
    st.audio(audio_bytes, format="audio/mp3")
    
    # Additional controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⏸️ Pause", key=f"pause_{message_id}"):
            st.info("Pause control (browser native)")
    
    with col2:
        if st.button("⏭️ Skip", key=f"skip_{message_id}"):
            st.info("Skip to next message")
    
    with col3:
        # Download audio for offline use
        st.download_button(
            label="💾 Save",
            data=audio_bytes,
            file_name=f"audio_{message_id}.mp3",
            mime="audio/mp3",
            key=f"download_{message_id}"
        )


def get_cached_audio_count() -> int:
    """
    Get count of cached audio files
    
    Returns:
        Number of cached audio files
    """
    if 'audio_cache' not in st.session_state:
        return 0
    return len(st.session_state.audio_cache)


def clear_audio_cache() -> None:
    """Clear all cached audio files"""
    if 'audio_cache' in st.session_state:
        st.session_state.audio_cache = {}


def get_audio_cache_size() -> float:
    """
    Get total size of cached audio in MB
    
    Returns:
        Cache size in MB
    """
    if 'audio_cache' not in st.session_state:
        return 0.0
    
    total_bytes = sum(len(audio) for audio in st.session_state.audio_cache.values())
    return total_bytes / (1024 * 1024)  # Convert to MB
