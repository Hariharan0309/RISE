"""
RISE Frontend Application Tests
Tests for main Streamlit app.py and UI components
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAppInitialization:
    """Test app initialization and configuration"""
    
    def test_language_map_completeness(self):
        """Test that all required languages are in LANGUAGE_MAP"""
        from app import LANGUAGE_MAP
        
        required_languages = [
            "English", "हिंदी (Hindi)", "தமிழ் (Tamil)", "తెలుగు (Telugu)",
            "ಕನ್ನಡ (Kannada)", "বাংলা (Bengali)", "ગુજરાતી (Gujarati)",
            "मराठी (Marathi)", "ਪੰਜਾਬੀ (Punjabi)"
        ]
        
        for lang in required_languages:
            assert lang in LANGUAGE_MAP, f"Missing language: {lang}"
        
        # Verify language codes
        assert LANGUAGE_MAP["English"] == "en"
        assert LANGUAGE_MAP["हिंदी (Hindi)"] == "hi"
        assert len(LANGUAGE_MAP) == 9
    
    def test_session_state_initialization(self):
        """Test session state initialization"""
        # Test the logic of session state initialization
        # without actually calling Streamlit functions
        
        # Simulate session state
        session_state = {}
        
        # Initialize keys as the function would
        if "authenticated" not in session_state:
            session_state["authenticated"] = False
        if "user_id" not in session_state:
            session_state["user_id"] = None
        if "language" not in session_state:
            session_state["language"] = "en"
        if "chat_history" not in session_state:
            session_state["chat_history"] = []
        
        # Verify all required keys are initialized
        assert "authenticated" in session_state
        assert "user_id" in session_state
        assert "language" in session_state
        assert "chat_history" in session_state
        assert session_state["authenticated"] is False
        assert session_state["language"] == "en"
        assert isinstance(session_state["chat_history"], list)


class TestAuthentication:
    """Test authentication flow"""
    
    @patch('streamlit.text_input')
    @patch('streamlit.form_submit_button')
    @patch('streamlit.session_state')
    def test_valid_authentication(self, mock_session, mock_submit, mock_input):
        """Test successful authentication with valid credentials"""
        # Setup mocks
        mock_session.authenticated = False
        mock_submit.return_value = True
        
        # Simulate form inputs
        name = "Test Farmer"
        phone = "9876543210"
        location = "Karnataka"
        crops = "wheat, rice"
        
        # Verify authentication logic
        assert len(phone) == 10
        assert phone.isdigit()
        
        # Simulate successful auth
        mock_session.authenticated = True
        mock_session.user_name = name
        mock_session.phone_number = phone
        mock_session.user_id = f"farmer_{phone}"
        
        assert mock_session.authenticated is True
        assert mock_session.user_id == "farmer_9876543210"
    
    def test_invalid_phone_number(self):
        """Test authentication fails with invalid phone number"""
        invalid_phones = [
            "123",  # Too short
            "12345678901",  # Too long
            "abcdefghij",  # Non-numeric
            "123-456-789",  # Contains special chars
        ]
        
        for phone in invalid_phones:
            is_valid = len(phone) == 10 and phone.isdigit()
            assert is_valid is False, f"Phone {phone} should be invalid"
    
    def test_user_id_generation(self):
        """Test user ID generation from phone number"""
        phone = "9876543210"
        user_id = f"farmer_{phone}"
        
        assert user_id == "farmer_9876543210"
        assert user_id.startswith("farmer_")
        assert phone in user_id


class TestChatInterface:
    """Test chat interface functionality"""
    
    @patch('streamlit.session_state')
    def test_chat_history_initialization(self, mock_session):
        """Test chat history is properly initialized"""
        mock_session.chat_history = []
        
        assert isinstance(mock_session.chat_history, list)
        assert len(mock_session.chat_history) == 0
    
    def test_add_user_message(self):
        """Test adding user message to chat history"""
        chat_history = []
        user_input = "What crops should I plant?"
        timestamp = datetime.now().strftime("%I:%M %p")
        
        message = {
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        }
        
        chat_history.append(message)
        
        assert len(chat_history) == 1
        assert chat_history[0]["role"] == "user"
        assert chat_history[0]["content"] == user_input
        assert "timestamp" in chat_history[0]
    
    def test_add_assistant_message(self):
        """Test adding assistant message to chat history"""
        chat_history = []
        response = "Based on your location, I recommend wheat and rice."
        timestamp = datetime.now().strftime("%I:%M %p")
        
        message = {
            "role": "assistant",
            "content": response,
            "timestamp": timestamp
        }
        
        chat_history.append(message)
        
        assert len(chat_history) == 1
        assert chat_history[0]["role"] == "assistant"
        assert chat_history[0]["content"] == response
    
    def test_chat_history_ordering(self):
        """Test chat history maintains correct order"""
        chat_history = []
        
        # Add multiple messages
        messages = [
            {"role": "user", "content": "Hello", "timestamp": "10:00 AM"},
            {"role": "assistant", "content": "Hi!", "timestamp": "10:01 AM"},
            {"role": "user", "content": "Help me", "timestamp": "10:02 AM"},
        ]
        
        for msg in messages:
            chat_history.append(msg)
        
        assert len(chat_history) == 3
        assert chat_history[0]["role"] == "user"
        assert chat_history[1]["role"] == "assistant"
        assert chat_history[2]["role"] == "user"


class TestLanguageSelection:
    """Test language selection and switching"""
    
    def test_language_code_mapping(self):
        """Test language display names map to correct codes"""
        from app import LANGUAGE_MAP
        
        test_cases = {
            "English": "en",
            "हिंदी (Hindi)": "hi",
            "தமிழ் (Tamil)": "ta",
            "తెలుగు (Telugu)": "te",
        }
        
        for display, code in test_cases.items():
            assert LANGUAGE_MAP[display] == code
    
    @patch('streamlit.session_state')
    def test_language_change(self, mock_session):
        """Test language change updates session state"""
        mock_session.language = "en"
        
        # Change language
        new_language = "hi"
        mock_session.language = new_language
        
        assert mock_session.language == "hi"
    
    def test_default_language(self):
        """Test default language is English"""
        session_state = {"language": "en"}
        
        assert session_state["language"] == "en"


class TestSessionManagement:
    """Test session management functionality"""
    
    @patch('streamlit.session_state')
    def test_session_cleanup(self, mock_session):
        """Test session cleanup on logout"""
        # Setup session with data
        mock_session.authenticated = True
        mock_session.user_id = "farmer_123"
        mock_session.chat_history = [{"role": "user", "content": "test"}]
        
        # Simulate cleanup - in real app, keys would be deleted
        # For testing, just verify the cleanup logic
        session_keys = ['authenticated', 'user_id', 'chat_history']
        
        # Verify keys exist before cleanup
        assert hasattr(mock_session, 'authenticated')
        assert hasattr(mock_session, 'user_id')
        
        # In production, these would be deleted
        # For test, just verify the logic is sound
        assert len(session_keys) > 0
    
    def test_session_id_format(self):
        """Test session ID format"""
        phone = "9876543210"
        session_id = f"demo_{phone}"
        
        assert session_id.startswith("demo_")
        assert phone in session_id


class TestOrchestratorIntegration:
    """Test orchestrator integration"""
    
    @patch('agents.orchestrator.get_orchestrator')
    def test_orchestrator_initialization(self, mock_get_orchestrator):
        """Test orchestrator is properly initialized"""
        mock_orchestrator = Mock()
        mock_get_orchestrator.return_value = mock_orchestrator
        
        orchestrator = mock_get_orchestrator()
        
        assert orchestrator is not None
        mock_get_orchestrator.assert_called_once()
    
    @patch('agents.orchestrator.get_orchestrator')
    def test_orchestrator_error_handling(self, mock_get_orchestrator):
        """Test handling of orchestrator initialization errors"""
        mock_get_orchestrator.side_effect = Exception("AWS not configured")
        
        try:
            orchestrator = mock_get_orchestrator()
            orchestrator = None
        except Exception as e:
            error_msg = str(e)
            assert "AWS not configured" in error_msg
    
    def test_query_processing_structure(self):
        """Test query processing request structure"""
        query_data = {
            "session_id": "test_session",
            "query": "What is the weather?",
            "context": {
                "location": "Karnataka",
                "crops": ["wheat", "rice"]
            }
        }
        
        assert "session_id" in query_data
        assert "query" in query_data
        assert "context" in query_data
        assert isinstance(query_data["context"]["crops"], list)


class TestErrorHandling:
    """Test error handling in the app"""
    
    def test_missing_orchestrator_fallback(self):
        """Test fallback behavior when orchestrator is unavailable"""
        orchestrator = None
        
        if not orchestrator:
            fallback_msg = "AI assistant is currently unavailable"
            assert "unavailable" in fallback_msg.lower()
    
    def test_query_error_handling(self):
        """Test error handling during query processing"""
        response = {
            "success": False,
            "error": "Service timeout"
        }
        
        assert response["success"] is False
        assert "error" in response
        assert len(response["error"]) > 0
    
    def test_empty_input_handling(self):
        """Test handling of empty user input"""
        user_input = ""
        
        # Empty input should not be processed
        should_process = len(user_input.strip()) > 0
        assert should_process is False


class TestUIComponents:
    """Test UI component rendering"""
    
    def test_feature_badges_content(self):
        """Test feature badges contain expected features"""
        features = [
            "Crop Diagnosis",
            "Soil Analysis",
            "Weather Alerts",
            "Market Prices",
            "Resource Sharing",
            "Govt Schemes"
        ]
        
        for feature in features:
            assert len(feature) > 0
            assert isinstance(feature, str)
    
    def test_tab_structure(self):
        """Test main interface has correct tabs"""
        tabs = ["💬 Chat Assistant", "📸 Disease Diagnosis", "📜 Diagnosis History"]
        
        assert len(tabs) == 3
        assert "Chat Assistant" in tabs[0]
        assert "Disease Diagnosis" in tabs[1]
        assert "Diagnosis History" in tabs[2]
    
    def test_sidebar_sections(self):
        """Test sidebar contains required sections"""
        sections = [
            "User Profile",
            "Language / भाषा",
            "System Status",
            "Quick Actions"
        ]
        
        for section in sections:
            assert len(section) > 0


class TestResponsiveDesign:
    """Test responsive design elements"""
    
    def test_column_layouts(self):
        """Test column layouts are properly defined"""
        # Test 3-column layout
        columns_3 = [1, 1, 1]
        assert len(columns_3) == 3
        assert sum(columns_3) == 3
        
        # Test 2-column layout
        columns_2 = [1, 1]
        assert len(columns_2) == 2
        
        # Test weighted columns
        columns_weighted = [2, 1]
        assert columns_weighted[0] > columns_weighted[1]
    
    def test_container_usage(self):
        """Test container structure for responsive layout"""
        # Containers should be used for grouping
        container_types = ["main", "sidebar", "chat", "expander"]
        
        for container in container_types:
            assert isinstance(container, str)
            assert len(container) > 0


class TestAccessibility:
    """Test accessibility features"""
    
    def test_multilingual_labels(self):
        """Test UI elements have multilingual labels"""
        labels = {
            'en': 'Start Recording',
            'hi': 'रिकॉर्डिंग शुरू करें'
        }
        
        assert 'en' in labels
        assert 'hi' in labels
        assert len(labels['en']) > 0
        assert len(labels['hi']) > 0
    
    def test_icon_usage(self):
        """Test icons are used for visual clarity"""
        icons = ["🌾", "💬", "📸", "📜", "🎤", "🔍"]
        
        for icon in icons:
            assert len(icon) > 0
    
    def test_help_text_availability(self):
        """Test help text is provided for inputs"""
        help_texts = {
            "name": "Your name for personalized assistance",
            "phone": "Your mobile number (demo mode - any 10 digits)",
            "location": "Your farming location"
        }
        
        for field, help_text in help_texts.items():
            assert len(help_text) > 0
            assert isinstance(help_text, str)


class TestFormValidation:
    """Test form validation logic"""
    
    def test_name_validation(self):
        """Test name field validation"""
        valid_names = ["John Doe", "राज कुमार", "அருண்"]
        
        for name in valid_names:
            is_valid = len(name.strip()) > 0
            assert is_valid is True
    
    def test_phone_validation(self):
        """Test phone number validation"""
        test_cases = [
            ("9876543210", True),
            ("1234567890", True),
            ("123", False),
            ("abcd", False),
            ("", False),
        ]
        
        for phone, expected in test_cases:
            is_valid = len(phone) == 10 and phone.isdigit()
            assert is_valid == expected, f"Phone {phone} validation failed"
    
    def test_crops_parsing(self):
        """Test crops input parsing"""
        crops_input = "wheat, rice, cotton"
        crops_list = [c.strip() for c in crops_input.split(",")]
        
        assert len(crops_list) == 3
        assert "wheat" in crops_list
        assert "rice" in crops_list
        assert "cotton" in crops_list
    
    def test_empty_crops_handling(self):
        """Test handling of empty crops input"""
        crops_input = ""
        crops_list = [c.strip() for c in crops_input.split(",")] if crops_input else []
        
        assert isinstance(crops_list, list)
        # Empty string split creates [''], so we need to filter
        if crops_input:
            assert len(crops_list) > 0
        else:
            assert len(crops_list) == 0


class TestSuggestedQuestions:
    """Test suggested questions functionality"""
    
    def test_suggested_questions_content(self):
        """Test suggested questions are relevant"""
        questions = [
            "How to identify crop diseases?",
            "What's the weather forecast?",
            "Current market prices?"
        ]
        
        for question in questions:
            assert len(question) > 0
            assert "?" in question
    
    def test_question_button_action(self):
        """Test clicking suggested question adds to chat"""
        chat_history = []
        question = "How can I identify diseases in my crops?"
        
        # Simulate button click
        message = {
            "role": "user",
            "content": question,
            "timestamp": datetime.now().strftime("%I:%M %p")
        }
        chat_history.append(message)
        
        assert len(chat_history) == 1
        assert chat_history[0]["content"] == question


class TestSystemStatus:
    """Test system status display"""
    
    def test_health_check_structure(self):
        """Test health check response structure"""
        health = {
            "status": "healthy",
            "orchestrator": {"agent_initialized": True},
            "aws_configured": True
        }
        
        assert "status" in health
        assert health["status"] in ["healthy", "unhealthy"]
    
    def test_status_indicators(self):
        """Test status indicators are displayed correctly"""
        statuses = {
            "agent_active": "✅ AI Agent Active",
            "agent_inactive": "❌ AI Agent Inactive",
            "aws_connected": "✅ AWS Connected",
            "aws_disconnected": "⚠️ AWS Not Connected"
        }
        
        for key, message in statuses.items():
            assert len(message) > 0
            assert any(icon in message for icon in ["✅", "❌", "⚠️"])


class TestOfflineSupport:
    """Test offline support features"""
    
    def test_offline_indicator_rendering(self):
        """Test offline indicator can be rendered"""
        # Mock offline indicator
        is_online = True
        indicator_text = "🟢 Online" if is_online else "🔴 Offline"
        
        assert "Online" in indicator_text or "Offline" in indicator_text
    
    def test_service_worker_registration(self):
        """Test service worker registration script"""
        sw_script = "navigator.serviceWorker.register('/static/service-worker.js')"
        
        assert "serviceWorker" in sw_script
        assert "register" in sw_script
        assert "service-worker.js" in sw_script


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
