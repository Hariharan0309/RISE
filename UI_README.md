# MissionAI Streamlit UI

## Overview

This is the Streamlit-based user interface for the MissionAI Farmer Agent system. It provides a mobile-first, voice-enabled interface with offline capabilities.

## Features

### ✅ Implemented (Task 9)

1. **Main App Structure** (9.1)
   - Mobile-responsive layout with custom CSS
   - Tab navigation (Chat, Diagnose, Weather, Market, Schemes, Finance, Community)
   - Session state management
   - Clean, farmer-friendly design

2. **Voice Input** (9.2)
   - Audio recording with streamlit-audio-recorder
   - Integration with Amazon Transcribe
   - Language selection (Kannada, English, Hindi)
   - Visual recording feedback
   - Audio upload to S3

3. **Image Upload** (9.3)
   - Camera/file upload support
   - Image preview and quality validation
   - Automatic quality checks (resolution, brightness, blur)
   - S3 upload integration
   - Helpful tips for better photos

4. **Chat Interface** (9.4)
   - Message history with speaker identification
   - Timestamps for all messages
   - Auto-scroll to latest message
   - Chat controls (clear, export)
   - Conversation statistics

5. **Audio Playback** (9.5)
   - Text-to-speech with Amazon Polly
   - Audio caching for offline playback
   - Player controls
   - Download audio option

6. **Tab-Specific Features** (9.6)
   - **Diagnose**: Image upload + disease results display
   - **Weather**: Location input + forecast display with farming advice
   - **Market**: Price comparison table + listing forms
   - **Schemes**: Scheme cards + eligibility checker
   - **Finance**: Profit calculator + cost estimator + crop comparison
   - **Community**: Forum search + post display + share experience

7. **Offline & PWA** (9.7)
   - Network status detection
   - Offline indicator banner
   - PWA manifest.json
   - Service worker for caching
   - Offline data status display
   - Action queuing for sync
   - Install prompt

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up AWS credentials in `.env`:
```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=missionai-bucket
```

3. Run the app:
```bash
streamlit run streamlit_app.py
```

## File Structure

```
streamlit_app.py          # Main application entry point
manifest.json             # PWA manifest
service-worker.js         # Service worker for offline support
offline.html              # Offline fallback page

ui/
├── voice_components.py   # Voice input/output components
├── image_components.py   # Image upload and validation
├── chat_components.py    # Chat interface components
├── tab_components.py     # Tab-specific features
└── offline_components.py # Offline functionality
```

## Usage

### Voice Interaction

1. Select your language (Kannada, English, Hindi)
2. Click the microphone button to record
3. Speak your question or command
4. Audio is automatically transcribed and sent to the agent

### Image Diagnosis

1. Go to the "Diagnose" tab
2. Upload a photo of your crop
3. System validates image quality
4. Click "Use this image" to analyze
5. View diagnosis results

### Offline Mode

- App automatically detects network status
- Cached data remains accessible offline
- Actions are queued and synced when online
- Audio responses are cached for offline playback

### PWA Installation

On mobile devices:
1. Open the app in your browser
2. Look for "Add to Home Screen" prompt
3. Or use browser menu → "Install App"
4. App will work like a native app

## Next Steps (Task 10)

The UI is ready for integration with the agent system:

1. Connect Manager Agent to handle user messages
2. Integrate Disease Diagnosis Agent with image upload
3. Wire Weather, Market, Schemes, Finance, Community agents
4. Implement end-to-end voice flow
5. Add real-time agent responses
6. Enable offline sync with backend

## Development Notes

- All UI components are modular and reusable
- Session state manages all application state
- Mobile-first responsive design
- Accessibility-friendly with large touch targets
- Supports low-bandwidth connections
- PWA-ready for offline use

## Testing

To test the UI without agent integration:

1. Run `streamlit run streamlit_app.py`
2. Test voice recording (requires AWS credentials)
3. Test image upload and validation
4. Test chat interface with placeholder responses
5. Explore all tabs and features
6. Test offline mode (use sidebar toggle)

## Browser Support

- Chrome/Edge (recommended)
- Firefox
- Safari (iOS/macOS)
- Mobile browsers (Android/iOS)

## Performance

- Lazy loading for images
- Audio caching to reduce API calls
- Efficient session state management
- Minimal external dependencies
- Optimized for mobile networks
