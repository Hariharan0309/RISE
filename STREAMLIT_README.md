# RISE Streamlit Frontend

## Overview

This is the fully functional Streamlit frontend for the RISE (Rural Innovation and Sustainable Ecosystem) farming assistant. It provides a chat-based interface for farmers to interact with the AI-powered agricultural advisor.

## Features Implemented

### ✅ Task 4 Requirements - All Complete

1. **Main Streamlit App (app.py)**
   - Enhanced from basic placeholder to fully functional chat interface
   - Integrated with RISEOrchestrator agent
   - Session state management for persistent conversations
   - Error handling and graceful degradation

2. **Chat Interface**
   - Built with `st.chat_message()` and `st.chat_input()`
   - Real-time message display with timestamps
   - User and assistant message differentiation
   - Suggested questions for new users
   - Chat history persistence during session

3. **Sidebar Features**
   - User profile display (name, phone, location, crops)
   - Language selector with 9 Indic languages
   - System status indicators
   - Quick actions (Clear Chat, Session Stats, Logout)
   - Real-time orchestrator health monitoring

4. **Session State Management**
   - Persistent user authentication state
   - Chat history storage
   - Language preference tracking
   - User context (location, crops) management
   - Orchestrator session integration

5. **Simple Authentication**
   - Demo authentication with `st.text_input()`
   - Name, phone number, location, and crops collection
   - Form validation (10-digit phone number)
   - Session creation with orchestrator
   - User-friendly error messages

6. **Language Selector**
   - Dropdown with 9 Indic languages:
     - English
     - हिंदी (Hindi)
     - தமிழ் (Tamil)
     - తెలుగు (Telugu)
     - ಕನ್ನಡ (Kannada)
     - বাংলা (Bengali)
     - ગુજરાતી (Gujarati)
     - मराठी (Marathi)
     - ਪੰਜਾਬੀ (Punjabi)
   - Language preference stored in session state
   - Updates orchestrator session context on change

7. **Agricultural Theme Styling**
   - Custom CSS with agricultural color scheme
   - Green and earth-tone palette
   - Responsive design
   - Feature badges for capabilities
   - Professional card-based layout
   - Hover effects and transitions

## Architecture

### Integration with Orchestrator

The Streamlit app integrates seamlessly with the RISEOrchestrator agent:

```python
from agents.orchestrator import get_orchestrator

# Initialize orchestrator (singleton pattern)
orchestrator = get_orchestrator()

# Create session
session_id = orchestrator.create_session(
    user_id=user_id,
    language=language_code,
    metadata={...}
)

# Process queries
response = orchestrator.process_query(
    session_id=session_id,
    query=user_input,
    context={...}
)
```

### Session State Management

The app uses Streamlit's session state to maintain:
- User authentication status
- User profile information
- Chat history
- Language preferences
- Orchestrator instance
- Active session ID

### Error Handling

The app includes comprehensive error handling:
- Graceful degradation when AWS is not configured
- Fallback messages when orchestrator is unavailable
- User-friendly error messages
- System status indicators in sidebar

## Running the Application

### Prerequisites

1. Python 3.8+ installed
2. All dependencies from `requirements.txt` installed
3. AWS credentials configured (optional for demo mode)

### Installation

```bash
# Navigate to RISE directory
cd RISE

# Install dependencies (if not already installed)
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the RISE directory:

```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Amazon Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1

# Application Configuration
APP_NAME=RISE
APP_ENV=development
DEBUG=True
```

### Running the App

```bash
# From RISE directory
streamlit run app.py

# Or specify port
streamlit run app.py --server.port 8501
```

The app will open in your default browser at `http://localhost:8501`

## Usage Guide

### First Time Setup

1. **Authentication Screen**
   - Enter your name
   - Enter 10-digit phone number (any digits for demo)
   - Enter location (optional)
   - Enter crops you grow (optional, comma-separated)
   - Click "Start Farming Assistant"

2. **Main Chat Interface**
   - Type questions in the chat input
   - Or click suggested questions
   - View responses with timestamps
   - Chat history persists during session

3. **Sidebar Features**
   - View your profile
   - Change language preference
   - Check system status
   - Clear chat history
   - View session statistics
   - Logout when done

### Example Questions

- "How can I identify diseases in my wheat crop?"
- "What's the weather forecast for my area?"
- "What are the current market prices for rice?"
- "Which fertilizer should I use for my soil?"
- "Are there any government schemes for farmers?"

## Features by Phase

### ✅ Phase 1 Complete (Task 4)
- Streamlit frontend with chat interface
- User authentication
- Session management
- Language selector
- Agricultural theme
- Orchestrator integration

### 🔄 Coming in Phase 2
- Voice input/output
- Real-time translation
- Audio recording and playback

### 🔄 Coming in Phase 3
- Image upload for crop diagnosis
- Photo analysis with Bedrock
- Disease identification
- Treatment recommendations

### 🔄 Coming in Phase 4+
- Weather integration
- Market prices
- Government schemes
- Community features
- Resource sharing

## Technical Details

### File Structure

```
RISE/
├── app.py                      # Main Streamlit application
├── agents/
│   └── orchestrator.py         # RISEOrchestrator agent
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── STREAMLIT_README.md         # This file
```

### Key Components

1. **apply_custom_css()** - Applies agricultural theme styling
2. **initialize_session_state()** - Sets up session variables
3. **render_authentication()** - Login/signup interface
4. **render_sidebar()** - User profile and settings
5. **render_chat_interface()** - Main chat UI
6. **main()** - Application entry point

### Session State Variables

- `authenticated` - User login status
- `user_id` - Unique user identifier
- `user_name` - User's name
- `phone_number` - User's phone
- `session_id` - Orchestrator session ID
- `language` - Selected language code
- `chat_history` - Message history
- `location` - User's location
- `crops` - User's crops
- `orchestrator` - Orchestrator instance

## Troubleshooting

### Orchestrator Not Available

If you see "Orchestrator unavailable" warnings:
1. Check AWS credentials in `.env`
2. Verify Bedrock access is enabled
3. Check network connectivity
4. Review logs for specific errors

### Chat Not Working

If chat input doesn't work:
1. Ensure you're authenticated
2. Check session_id is created
3. Verify orchestrator is initialized
4. Check browser console for errors

### Language Selector Issues

If language changes don't persist:
1. Check session state is initialized
2. Verify orchestrator session update
3. Clear browser cache and reload

## Performance Considerations

- Chat history stored in memory (session state)
- Orchestrator uses singleton pattern
- AWS SDK connections are reused
- CSS is applied once per page load
- Session cleanup on logout

## Security Notes

- Demo authentication (not production-ready)
- Phone numbers not validated against real database
- No password protection in demo mode
- AWS credentials should be in `.env` (not committed)
- Session data cleared on logout

## Future Enhancements

1. **Authentication**
   - Real user database
   - Password protection
   - OTP verification
   - Social login

2. **Chat Features**
   - Message editing
   - Message deletion
   - Export chat history
   - Search messages

3. **UI Improvements**
   - Dark mode
   - Custom themes
   - Accessibility features
   - Mobile optimization

4. **Performance**
   - Message pagination
   - Lazy loading
   - Caching strategies
   - Database persistence

## Support

For issues or questions:
1. Check this README
2. Review orchestrator logs
3. Check AWS service status
4. Verify configuration in `.env`

## License

Part of the RISE project for AI for Bharat Hackathon.

---

**Status:** ✅ Task 4 Complete - Fully Functional Streamlit Frontend

**Last Updated:** 2025
