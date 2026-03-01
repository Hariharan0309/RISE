"""
RISE Tools Module
Strands Agent tools for agricultural operations
"""

__version__ = "0.1.0"

from .voice_tools import (
    VoiceProcessingTools,
    create_voice_tools,
    transcribe_audio_tool,
    synthesize_speech_tool,
    detect_language_tool
)

__all__ = [
    'VoiceProcessingTools',
    'create_voice_tools',
    'transcribe_audio_tool',
    'synthesize_speech_tool',
    'detect_language_tool'
]
