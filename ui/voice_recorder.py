"""
RISE Voice Recorder Component
Streamlit component for voice recording and playback
"""

import streamlit as st
import streamlit.components.v1 as components
import base64
import json
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def render_voice_recorder(
    key: str = "voice_recorder",
    language: str = "en",
    max_duration: int = 60,
    show_waveform: bool = True
) -> Optional[bytes]:
    """
    Render voice recorder component with audio visualization
    
    Args:
        key: Unique key for the component
        language: Current language for UI labels
        max_duration: Maximum recording duration in seconds
        show_waveform: Show audio waveform visualization
    
    Returns:
        Audio data as bytes if recording is complete, None otherwise
    """
    
    # Language-specific labels
    labels = {
        'en': {
            'start': 'Start Recording',
            'stop': 'Stop Recording',
            'recording': 'Recording...',
            'processing': 'Processing...',
            'play': 'Play',
            'pause': 'Pause',
            'duration': 'Duration',
            'max_duration': f'Max {max_duration}s'
        },
        'hi': {
            'start': 'रिकॉर्डिंग शुरू करें',
            'stop': 'रिकॉर्डिंग बंद करें',
            'recording': 'रिकॉर्ड हो रहा है...',
            'processing': 'प्रोसेस हो रहा है...',
            'play': 'चलाएं',
            'pause': 'रोकें',
            'duration': 'अवधि',
            'max_duration': f'अधिकतम {max_duration}s'
        }
    }
    
    current_labels = labels.get(language, labels['en'])
    
    # HTML/JavaScript for voice recorder
    recorder_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .voice-recorder {{
                background: linear-gradient(135deg, #2E7D32 0%, #66BB6A 100%);
                border-radius: 15px;
                padding: 20px;
                color: white;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            
            .recorder-controls {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 15px;
            }}
            
            .record-button {{
                width: 80px;
                height: 80px;
                border-radius: 50%;
                border: none;
                background: white;
                color: #2E7D32;
                font-size: 14px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }}
            
            .record-button:hover {{
                transform: scale(1.05);
                box-shadow: 0 6px 12px rgba(0,0,0,0.3);
            }}
            
            .record-button.recording {{
                background: #f44336;
                color: white;
                animation: pulse 1.5s infinite;
            }}
            
            @keyframes pulse {{
                0%, 100% {{ transform: scale(1); }}
                50% {{ transform: scale(1.1); }}
            }}
            
            .status-text {{
                font-size: 16px;
                font-weight: 500;
                margin: 10px 0;
            }}
            
            .duration-text {{
                font-size: 14px;
                opacity: 0.9;
            }}
            
            .waveform {{
                width: 100%;
                height: 60px;
                background: rgba(255,255,255,0.1);
                border-radius: 10px;
                margin: 10px 0;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
            }}
            
            .waveform-bar {{
                width: 3px;
                background: white;
                margin: 0 2px;
                border-radius: 2px;
                transition: height 0.1s;
            }}
            
            .playback-controls {{
                display: flex;
                gap: 10px;
                margin-top: 10px;
            }}
            
            .play-button {{
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                background: white;
                color: #2E7D32;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
            }}
            
            .play-button:hover {{
                background: #f0f0f0;
            }}
            
            .error-message {{
                background: #f44336;
                color: white;
                padding: 10px;
                border-radius: 8px;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="voice-recorder">
            <div class="recorder-controls">
                <button id="recordButton" class="record-button">
                    {current_labels['start']}
                </button>
                
                <div class="status-text" id="statusText">
                    {current_labels['max_duration']}
                </div>
                
                <div class="duration-text" id="durationText">
                    {current_labels['duration']}: 0s
                </div>
                
                {'<div class="waveform" id="waveform"></div>' if show_waveform else ''}
                
                <div class="playback-controls" id="playbackControls" style="display: none;">
                    <button class="play-button" id="playButton">
                        {current_labels['play']}
                    </button>
                </div>
                
                <div class="error-message" id="errorMessage" style="display: none;"></div>
            </div>
        </div>
        
        <script>
            let mediaRecorder;
            let audioChunks = [];
            let isRecording = false;
            let recordingStartTime;
            let durationInterval;
            let audioBlob;
            let audioUrl;
            
            const recordButton = document.getElementById('recordButton');
            const statusText = document.getElementById('statusText');
            const durationText = document.getElementById('durationText');
            const playbackControls = document.getElementById('playbackControls');
            const playButton = document.getElementById('playButton');
            const errorMessage = document.getElementById('errorMessage');
            const waveform = document.getElementById('waveform');
            
            const maxDuration = {max_duration};
            
            // Initialize waveform bars
            if (waveform) {{
                for (let i = 0; i < 30; i++) {{
                    const bar = document.createElement('div');
                    bar.className = 'waveform-bar';
                    bar.style.height = '10px';
                    waveform.appendChild(bar);
                }}
            }}
            
            recordButton.addEventListener('click', async () => {{
                if (!isRecording) {{
                    await startRecording();
                }} else {{
                    stopRecording();
                }}
            }});
            
            playButton.addEventListener('click', () => {{
                if (audioUrl) {{
                    const audio = new Audio(audioUrl);
                    audio.play();
                }}
            }});
            
            async function startRecording() {{
                try {{
                    const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                    
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];
                    
                    mediaRecorder.ondataavailable = (event) => {{
                        audioChunks.push(event.data);
                    }};
                    
                    mediaRecorder.onstop = async () => {{
                        audioBlob = new Blob(audioChunks, {{ type: 'audio/wav' }});
                        audioUrl = URL.createObjectURL(audioBlob);
                        
                        // Convert to base64 and send to Streamlit
                        const reader = new FileReader();
                        reader.onloadend = () => {{
                            const base64Audio = reader.result.split(',')[1];
                            
                            // Send to Streamlit
                            window.parent.postMessage({{
                                type: 'streamlit:setComponentValue',
                                value: {{
                                    audio_data: base64Audio,
                                    duration: Math.floor((Date.now() - recordingStartTime) / 1000),
                                    format: 'audio/wav'
                                }}
                            }}, '*');
                        }};
                        reader.readAsDataURL(audioBlob);
                        
                        // Show playback controls
                        playbackControls.style.display = 'flex';
                        statusText.textContent = '{current_labels['processing']}';
                    }};
                    
                    mediaRecorder.start();
                    isRecording = true;
                    recordingStartTime = Date.now();
                    
                    recordButton.textContent = '{current_labels['stop']}';
                    recordButton.classList.add('recording');
                    statusText.textContent = '{current_labels['recording']}';
                    
                    // Update duration
                    durationInterval = setInterval(() => {{
                        const duration = Math.floor((Date.now() - recordingStartTime) / 1000);
                        durationText.textContent = `{current_labels['duration']}: ${{duration}}s`;
                        
                        // Animate waveform
                        if (waveform) {{
                            const bars = waveform.querySelectorAll('.waveform-bar');
                            bars.forEach(bar => {{
                                const height = Math.random() * 50 + 10;
                                bar.style.height = height + 'px';
                            }});
                        }}
                        
                        // Auto-stop at max duration
                        if (duration >= maxDuration) {{
                            stopRecording();
                        }}
                    }}, 100);
                    
                }} catch (error) {{
                    showError('Microphone access denied. Please allow microphone access.');
                    console.error('Error accessing microphone:', error);
                }}
            }}
            
            function stopRecording() {{
                if (mediaRecorder && isRecording) {{
                    mediaRecorder.stop();
                    mediaRecorder.stream.getTracks().forEach(track => track.stop());
                    
                    isRecording = false;
                    clearInterval(durationInterval);
                    
                    recordButton.textContent = '{current_labels['start']}';
                    recordButton.classList.remove('recording');
                    
                    // Reset waveform
                    if (waveform) {{
                        const bars = waveform.querySelectorAll('.waveform-bar');
                        bars.forEach(bar => {{
                            bar.style.height = '10px';
                        }});
                    }}
                }}
            }}
            
            function showError(message) {{
                errorMessage.textContent = message;
                errorMessage.style.display = 'block';
                setTimeout(() => {{
                    errorMessage.style.display = 'none';
                }}, 5000);
            }}
        </script>
    </body>
    </html>
    """
    
    # Render component
    component_value = components.html(
        recorder_html,
        height=300,
        key=key
    )
    
    # Process returned audio data
    if component_value:
        try:
            audio_data_base64 = component_value.get('audio_data')
            if audio_data_base64:
                audio_bytes = base64.b64decode(audio_data_base64)
                return audio_bytes
        except Exception as e:
            logger.error(f"Error processing audio data: {e}")
            st.error(f"Error processing audio: {e}")
    
    return None


def render_audio_player(audio_data: bytes, key: str = "audio_player") -> None:
    """
    Render audio player for playback
    
    Args:
        audio_data: Audio bytes to play
        key: Unique key for the component
    """
    
    # Convert to base64 for embedding
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
    
    audio_html = f"""
    <audio controls style="width: 100%; margin: 10px 0;">
        <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
        Your browser does not support the audio element.
    </audio>
    """
    
    st.markdown(audio_html, unsafe_allow_html=True)


def create_voice_input_ui(
    session_id: str,
    orchestrator,
    language: str = "en"
) -> Optional[str]:
    """
    Create complete voice input UI with recording and transcription
    
    Args:
        session_id: Current session ID
        orchestrator: Orchestrator instance
        language: Current language
    
    Returns:
        Transcribed text if available, None otherwise
    """
    
    st.markdown("### 🎤 Voice Input")
    
    # Voice recorder
    audio_data = render_voice_recorder(
        key=f"voice_recorder_{session_id}",
        language=language,
        max_duration=60,
        show_waveform=True
    )
    
    if audio_data:
        st.success("✅ Recording captured!")
        
        # Show audio player
        with st.expander("🔊 Play Recording"):
            render_audio_player(audio_data, key=f"audio_player_{session_id}")
        
        # Transcribe button
        if st.button("📝 Transcribe to Text", key=f"transcribe_{session_id}"):
            with st.spinner("Transcribing..."):
                try:
                    # Import voice tools
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from tools.voice_tools import VoiceProcessingTools
                    
                    # Create voice tools instance
                    voice_tools = VoiceProcessingTools()
                    
                    # Process voice query
                    result = voice_tools.process_voice_query(
                        audio_data=audio_data,
                        user_language=language
                    )
                    
                    if result['success']:
                        transcribed_text = result['text']
                        detected_lang = result['language_name']
                        confidence = result['confidence']
                        
                        st.success(f"✅ Transcribed ({detected_lang}, {confidence:.0%} confidence)")
                        st.info(f"**Text:** {transcribed_text}")
                        
                        return transcribed_text
                    else:
                        st.error(f"❌ Transcription failed: {result.get('error', 'Unknown error')}")
                        return None
                
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    logger.error(f"Transcription error: {e}", exc_info=True)
                    return None
    
    return None
