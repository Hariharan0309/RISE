# RISE Voice Processing Tools

## Overview

The RISE voice processing tools provide comprehensive speech-to-text, text-to-speech, and language detection capabilities for the farming assistant. These tools enable voice-first interaction for farmers with low literacy levels across 9 Indic languages.

## Features

### 🎤 Speech-to-Text (Amazon Transcribe)
- Automatic language detection from 9 supported languages
- Background noise reduction for rural environments
- Accent variation handling (>85% accuracy target)
- Support for multiple audio formats (WAV, MP3, FLAC, WebM, OGG)
- Maximum 60-second recording duration
- Automatic cleanup of temporary S3 files

### 🔊 Text-to-Speech (Amazon Polly)
- Natural-sounding neural voices for Indic languages
- Support for 9 Indic languages + English
- High-quality MP3 audio output
- Base64 encoding for easy transmission
- Optimized for mobile and web playback

### 🌐 Language Detection (Amazon Comprehend)
- Automatic language identification from text
- Confidence scoring for detection accuracy
- Mapping to supported language codes
- Fallback to English for unsupported languages

## Supported Languages

| Code | Language | Transcribe | Polly Voice | Status |
|------|----------|------------|-------------|--------|
| en   | English  | en-IN      | Aditi       | ✅ Active |
| hi   | Hindi    | hi-IN      | Aditi       | ✅ Active |
| ta   | Tamil    | ta-IN      | Aditi       | ✅ Active |
| te   | Telugu   | te-IN      | Aditi       | ✅ Active |
| kn   | Kannada  | kn-IN      | Aditi       | ✅ Active |
| bn   | Bengali  | bn-IN      | Aditi       | ✅ Active |
| gu   | Gujarati | gu-IN      | Aditi       | ✅ Active |
| mr   | Marathi  | mr-IN      | Aditi       | ✅ Active |
| pa   | Punjabi  | pa-IN      | Aditi       | ✅ Active |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Voice Processing Flow                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. User speaks query                                   │
│     ↓                                                   │
│  2. Frontend captures audio (voice_recorder.py)         │
│     ↓                                                   │
│  3. Audio uploaded to S3 (audio_upload_lambda.py)       │
│     ↓                                                   │
│  4. Amazon Transcribe → Text                            │
│     ↓                                                   │
│  5. Amazon Comprehend → Language Detection              │
│     ↓                                                   │
│  6. Orchestrator processes query                        │
│     ↓                                                   │
│  7. Amazon Polly → Speech                               │
│     ↓                                                   │
│  8. Frontend plays audio response                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Usage

### Basic Usage

```python
from tools.voice_tools import VoiceProcessingTools

# Initialize tools
voice_tools = VoiceProcessingTools(region="us-east-1")

# Transcribe audio
result = voice_tools.transcribe_audio(
    audio_data=audio_bytes,
    language_code="hi",  # Optional, will auto-detect if not provided
    enable_noise_reduction=True
)

if result['success']:
    print(f"Transcribed: {result['text']}")
    print(f"Language: {result['language_code']}")
    print(f"Confidence: {result['confidence']}")

# Synthesize speech
result = voice_tools.synthesize_speech(
    text="नमस्ते! मैं आपकी मदद के लिए यहाँ हूँ।",
    language_code="hi"
)

if result['success']:
    audio_base64 = result['audio_data']
    # Use audio_base64 for playback

# Detect language
result = voice_tools.detect_language(
    text="मेरी गेहूं की फसल में समस्या है"
)

if result['success']:
    print(f"Detected: {result['language_name']}")
    print(f"Confidence: {result['confidence']:.2%}")
```

### Integration with Orchestrator

```python
from agents.orchestrator import get_orchestrator

# Initialize orchestrator
orchestrator = get_orchestrator()

# Create session
session_id = orchestrator.create_session(
    user_id="farmer_001",
    language="hi"
)

# Process voice query
response = orchestrator.process_voice_query(
    session_id=session_id,
    audio_data=audio_bytes,
    language="hi"
)

if response['success']:
    print(f"Transcribed: {response['transcribed_text']}")
    print(f"Response: {response['text_response']}")
    print(f"Audio: {response['audio_response']}")  # Base64 encoded
```

### Streamlit Integration

```python
from ui.voice_recorder import create_voice_input_ui

# In your Streamlit app
transcribed_text = create_voice_input_ui(
    session_id=st.session_state.session_id,
    orchestrator=st.session_state.orchestrator,
    language=st.session_state.language
)

if transcribed_text:
    # Process the transcribed text
    st.write(f"You said: {transcribed_text}")
```

## Lambda Function Deployment

### Audio Upload Lambda

The `audio_upload_lambda.py` function handles audio file uploads to S3.

**Environment Variables:**
```bash
S3_BUCKET=rise-application-data
MAX_FILE_SIZE=10485760  # 10MB
```

**API Gateway Integration:**
```
POST /api/v1/voice/upload
Content-Type: application/json

{
  "audio_data": "base64_encoded_audio",
  "user_id": "farmer_1234567890",
  "content_type": "audio/wav",
  "language_code": "hi"
}
```

**Response:**
```json
{
  "success": true,
  "s3_key": "audio/voice-queries/farmer_1234567890/1234567890-abc123.wav",
  "s3_uri": "s3://rise-application-data/audio/...",
  "file_size": 123456,
  "presigned_url": "https://..."
}
```

## Frontend Components

### Voice Recorder Component

The voice recorder component (`ui/voice_recorder.py`) provides:

- **Real-time audio visualization** with waveform display
- **Recording controls** (start/stop/play)
- **Duration tracking** with auto-stop at 60 seconds
- **Multilingual UI** (English, Hindi, and other Indic languages)
- **Error handling** with user-friendly messages
- **Audio playback** for verification before submission

**Features:**
- Microphone access with permission handling
- WebRTC-based audio capture
- Base64 encoding for transmission
- Responsive design for mobile and desktop
- Agricultural theme styling

## Configuration

### AWS Services Required

1. **Amazon Transcribe**
   - Enable Indic language support
   - Configure custom vocabulary for agricultural terms
   - Set up noise reduction settings

2. **Amazon Polly**
   - Enable neural engine for better quality
   - Configure Aditi voice for Indic languages
   - Set up SSML support for pronunciation

3. **Amazon Comprehend**
   - Enable language detection
   - Configure for Indic language support

4. **Amazon S3**
   - Create bucket: `rise-application-data`
   - Configure lifecycle policy: delete audio after 30 days
   - Set up CORS for frontend uploads

### Environment Variables

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# S3 Configuration
S3_BUCKET=rise-application-data

# Bedrock Configuration
BEDROCK_REGION=us-east-1
```

## Performance Optimization

### Transcription
- **Timeout:** 60 seconds maximum
- **Polling interval:** 2 seconds
- **Cleanup:** Automatic deletion of temporary files
- **Caching:** Not implemented (real-time processing)

### Speech Synthesis
- **Format:** MP3 for optimal size/quality balance
- **Engine:** Neural for natural-sounding voices
- **Encoding:** Base64 for easy transmission
- **Caching:** Consider implementing for common phrases

### Network Optimization
- **Audio compression:** Use appropriate formats (MP3, OGG)
- **Batch processing:** Not applicable for real-time voice
- **Progressive loading:** Not applicable for voice
- **2G/3G support:** Optimize audio quality vs. size

## Error Handling

### Common Errors

1. **Microphone Access Denied**
   - User-friendly message in UI
   - Instructions to enable microphone
   - Fallback to text input

2. **Transcription Timeout**
   - 60-second timeout protection
   - Retry mechanism with shorter clips
   - Error message with guidance

3. **Language Detection Failure**
   - Fallback to user's preferred language
   - Default to English if unknown
   - Confidence threshold checking

4. **S3 Upload Failure**
   - Retry logic (3 attempts)
   - Error logging for debugging
   - User notification with retry option

### Error Response Format

```python
{
    "success": False,
    "error": "Detailed error message",
    "error_code": "TRANSCRIPTION_TIMEOUT",
    "retry_possible": True
}
```

## Testing

### Unit Tests

```python
# Test transcription
def test_transcribe_audio():
    tools = VoiceProcessingTools()
    result = tools.transcribe_audio(sample_audio, "hi")
    assert result['success'] == True
    assert 'text' in result

# Test speech synthesis
def test_synthesize_speech():
    tools = VoiceProcessingTools()
    result = tools.synthesize_speech("Test", "en")
    assert result['success'] == True
    assert 'audio_data' in result

# Test language detection
def test_detect_language():
    tools = VoiceProcessingTools()
    result = tools.detect_language("नमस्ते")
    assert result['language_code'] == 'hi'
```

### Integration Tests

Run the example script:
```bash
python examples/voice_integration_example.py
```

## Monitoring

### CloudWatch Metrics

- **Transcription duration:** Average time for speech-to-text
- **Synthesis duration:** Average time for text-to-speech
- **Error rates:** Failed transcriptions/syntheses
- **Language distribution:** Usage by language
- **Audio file sizes:** Average upload sizes

### Logging

```python
import logging
logger = logging.getLogger(__name__)

# Log transcription
logger.info(f"Transcribed audio: {len(audio_data)} bytes, language: {lang}")

# Log errors
logger.error(f"Transcription failed: {error}", exc_info=True)
```

## Future Enhancements

### Phase 2 Improvements
- [ ] Custom vocabulary for agricultural terms
- [ ] Speaker identification for multi-user scenarios
- [ ] Real-time streaming transcription
- [ ] Offline voice processing for poor connectivity
- [ ] Voice biometrics for authentication

### Phase 3 Features
- [ ] Emotion detection from voice
- [ ] Dialect-specific models
- [ ] Voice-based crop disease diagnosis
- [ ] Multi-turn conversation optimization
- [ ] Voice command shortcuts

## Troubleshooting

### Issue: Transcription accuracy is low
**Solution:**
- Enable noise reduction
- Use better quality microphone
- Record in quieter environment
- Add custom vocabulary for agricultural terms

### Issue: Audio upload fails
**Solution:**
- Check S3 bucket permissions
- Verify CORS configuration
- Check file size limits
- Ensure valid audio format

### Issue: Language detection is incorrect
**Solution:**
- Provide explicit language code
- Use longer text samples
- Check language code mapping
- Verify Comprehend service availability

## Support

For issues or questions:
- Check the examples: `examples/voice_integration_example.py`
- Review logs in CloudWatch
- Test with the provided unit tests
- Consult AWS service documentation

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) project.
