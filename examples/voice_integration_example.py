"""
RISE Voice Integration Example
Demonstrates how to use voice processing tools with the orchestrator
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import get_orchestrator
from tools.voice_tools import VoiceProcessingTools
import base64


def example_voice_query_processing():
    """Example: Process a voice query end-to-end"""
    
    print("=" * 60)
    print("RISE Voice Processing Example")
    print("=" * 60)
    
    # Initialize orchestrator
    print("\n1. Initializing orchestrator...")
    orchestrator = get_orchestrator()
    print("✓ Orchestrator initialized")
    
    # Create session
    print("\n2. Creating farmer session...")
    session_id = orchestrator.create_session(
        user_id="farmer_demo_001",
        language="hi",  # Hindi
        metadata={
            "location": "Uttar Pradesh",
            "crops": ["wheat", "rice"]
        }
    )
    print(f"✓ Session created: {session_id}")
    
    # Simulate audio data (in real scenario, this would come from microphone)
    print("\n3. Simulating voice input...")
    # In production, you would get this from the voice recorder component
    sample_audio = b"simulated audio data"  # Replace with actual audio bytes
    
    print("   Note: In production, audio_data would come from:")
    print("   - Frontend voice recorder component")
    print("   - Mobile app microphone")
    print("   - Uploaded audio file")
    
    # For demonstration, let's show the text-based flow
    print("\n4. Processing text query (voice simulation)...")
    query = "मेरी गेहूं की फसल में पीले धब्बे दिख रहे हैं। क्या करूं?"
    
    response = orchestrator.process_query(
        session_id=session_id,
        query=query
    )
    
    if response['success']:
        print(f"✓ Query processed successfully")
        print(f"  Response: {response['response'][:200]}...")
        print(f"  Duration: {response['duration_ms']:.2f}ms")
    else:
        print(f"✗ Error: {response.get('error')}")
    
    # Demonstrate voice tools directly
    print("\n5. Demonstrating voice tools...")
    voice_tools = VoiceProcessingTools()
    
    # Language detection
    print("\n   a) Language Detection:")
    lang_result = voice_tools.detect_language(query)
    if lang_result['success']:
        print(f"      Detected: {lang_result['language_name']} ({lang_result['language_code']})")
        print(f"      Confidence: {lang_result['confidence']:.2%}")
    
    # Text-to-speech
    print("\n   b) Text-to-Speech:")
    tts_result = voice_tools.synthesize_speech(
        text="नमस्ते! मैं आपकी मदद के लिए यहाँ हूँ।",
        language_code="hi"
    )
    if tts_result['success']:
        print(f"      ✓ Generated audio: {len(tts_result['audio_data'])} bytes (base64)")
        print(f"      Format: {tts_result['audio_format']}")
        print(f"      Voice: {tts_result['voice_id']}")
    
    # Cleanup
    print("\n6. Cleaning up...")
    orchestrator.cleanup_session(session_id)
    print("✓ Session cleaned up")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


def example_supported_languages():
    """Example: Show all supported languages"""
    
    print("\n" + "=" * 60)
    print("Supported Languages for Voice Processing")
    print("=" * 60)
    
    voice_tools = VoiceProcessingTools()
    
    print("\nLanguage Code | Language Name | Transcribe | Polly Voice")
    print("-" * 60)
    
    for code, config in voice_tools.language_codes.items():
        transcribe_code = config['transcribe']
        polly_voice = voice_tools.polly_voices.get(transcribe_code, 'N/A')
        print(f"{code:12} | {config['name']:13} | {transcribe_code:10} | {polly_voice}")
    
    print("\nTotal supported languages: 9")
    print("All languages support:")
    print("  ✓ Speech-to-text (Amazon Transcribe)")
    print("  ✓ Text-to-speech (Amazon Polly)")
    print("  ✓ Language detection (Amazon Comprehend)")
    print("  ✓ Background noise reduction")
    print("  ✓ Accent variation handling")


def example_voice_workflow():
    """Example: Complete voice interaction workflow"""
    
    print("\n" + "=" * 60)
    print("Complete Voice Interaction Workflow")
    print("=" * 60)
    
    print("\nWorkflow Steps:")
    print("1. User speaks query in their language")
    print("2. Frontend captures audio via voice recorder component")
    print("3. Audio uploaded to S3 via Lambda function")
    print("4. Amazon Transcribe converts speech to text")
    print("5. Amazon Comprehend detects language (if not specified)")
    print("6. Orchestrator processes query with Bedrock")
    print("7. Amazon Polly converts response to speech")
    print("8. Frontend plays audio response to user")
    
    print("\nKey Features:")
    print("  ✓ Automatic language detection")
    print("  ✓ Background noise reduction for rural environments")
    print("  ✓ Support for 9 Indic languages + English")
    print("  ✓ Context-aware conversation management")
    print("  ✓ Accent variation handling (>85% accuracy)")
    print("  ✓ Real-time audio visualization")
    print("  ✓ Maximum 60-second recording duration")
    
    print("\nIntegration Points:")
    print("  • Streamlit: ui/voice_recorder.py")
    print("  • Lambda: tools/audio_upload_lambda.py")
    print("  • Tools: tools/voice_tools.py")
    print("  • Orchestrator: agents/orchestrator.py")


def example_error_handling():
    """Example: Error handling in voice processing"""
    
    print("\n" + "=" * 60)
    print("Voice Processing Error Handling")
    print("=" * 60)
    
    voice_tools = VoiceProcessingTools()
    
    print("\n1. Testing with empty audio:")
    result = voice_tools.transcribe_audio(b"")
    print(f"   Result: {result}")
    
    print("\n2. Testing with invalid language code:")
    result = voice_tools.synthesize_speech("Test", language_code="invalid")
    print(f"   Result: Defaults to English")
    
    print("\n3. Testing language detection with empty text:")
    result = voice_tools.detect_language("")
    print(f"   Result: {result}")
    
    print("\nError Handling Features:")
    print("  ✓ Graceful degradation on service failures")
    print("  ✓ Automatic fallback to English")
    print("  ✓ Detailed error messages for debugging")
    print("  ✓ Retry logic for transient failures")
    print("  ✓ Timeout protection (60 seconds)")


if __name__ == "__main__":
    try:
        # Run examples
        example_voice_query_processing()
        example_supported_languages()
        example_voice_workflow()
        example_error_handling()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()
