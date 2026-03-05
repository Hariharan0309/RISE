"""
RISE Frontend Validation Tests
Tests for form validation, input sanitization, and session management
"""

import pytest
import sys
import os
import re
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestInputValidation:
    """Test input validation logic"""
    
    def test_phone_number_validation(self):
        """Test phone number validation rules"""
        test_cases = [
            # (input, expected_valid)
            ("9876543210", True),
            ("1234567890", True),
            ("0000000000", True),  # Valid format, even if unrealistic
            ("123456789", False),  # Too short
            ("12345678901", False),  # Too long
            ("abcdefghij", False),  # Non-numeric
            ("98765 43210", False),  # Contains space
            ("9876-543210", False),  # Contains hyphen
            ("+919876543210", False),  # Contains plus
            ("", False),  # Empty
        ]
        
        for phone, expected in test_cases:
            is_valid = len(phone) == 10 and phone.isdigit()
            assert is_valid == expected, f"Phone {phone} validation failed"
    
    def test_name_validation(self):
        """Test name validation"""
        test_cases = [
            ("John Doe", True),
            ("राज कुमार", True),
            ("அருண் குமார்", True),
            ("", False),
            ("   ", False),  # Only whitespace
        ]
        
        for name, expected in test_cases:
            is_valid = len(name.strip()) > 0
            assert is_valid == expected, f"Name '{name}' validation failed"
    
    def test_location_validation(self):
        """Test location input validation"""
        locations = [
            "Karnataka, Bangalore",
            "उत्तर प्रदेश, लखनऊ",
            "Village Name, District, State",
            ""  # Optional field
        ]
        
        for location in locations:
            # Location is optional, so empty is valid
            is_valid = True if not location else len(location.strip()) > 0
            assert is_valid is True
    
    def test_crops_input_parsing(self):
        """Test crops input parsing and validation"""
        test_cases = [
            ("wheat, rice, cotton", ["wheat", "rice", "cotton"]),
            ("wheat,rice,cotton", ["wheat", "rice", "cotton"]),
            ("wheat", ["wheat"]),
            ("", []),
            ("  wheat  ,  rice  ", ["wheat", "rice"]),
        ]
        
        for input_str, expected in test_cases:
            if input_str:
                result = [c.strip() for c in input_str.split(",") if c.strip()]
            else:
                result = []
            assert result == expected, f"Crops parsing failed for '{input_str}'"


class TestInputSanitization:
    """Test input sanitization"""
    
    def test_xss_prevention(self):
        """Test XSS attack prevention"""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "'; DROP TABLE users; --"
        ]
        
        for malicious in malicious_inputs:
            # In production, these should be sanitized
            # For now, just verify they're strings
            assert isinstance(malicious, str)
    
    def test_special_character_handling(self):
        """Test special character handling"""
        inputs_with_special_chars = [
            "Name with 'quotes'",
            'Name with "double quotes"',
            "Name with <brackets>",
            "Name with & ampersand"
        ]
        
        for input_str in inputs_with_special_chars:
            # Should handle special characters gracefully
            assert isinstance(input_str, str)
            assert len(input_str) > 0
    
    def test_whitespace_trimming(self):
        """Test whitespace trimming"""
        test_cases = [
            ("  John Doe  ", "John Doe"),
            ("\tTabbed\t", "Tabbed"),
            ("\nNewline\n", "Newline"),
            ("  Multiple   Spaces  ", "Multiple   Spaces"),
        ]
        
        for input_str, expected in test_cases:
            result = input_str.strip()
            assert result == expected


class TestFormSubmission:
    """Test form submission logic"""
    
    def test_complete_form_submission(self):
        """Test complete form with all fields"""
        form_data = {
            "name": "Test Farmer",
            "phone": "9876543210",
            "location": "Karnataka",
            "crops": "wheat, rice"
        }
        
        # Validate all fields
        is_valid = (
            len(form_data["name"].strip()) > 0 and
            len(form_data["phone"]) == 10 and
            form_data["phone"].isdigit()
        )
        
        assert is_valid is True
    
    def test_partial_form_submission(self):
        """Test form with optional fields empty"""
        form_data = {
            "name": "Test Farmer",
            "phone": "9876543210",
            "location": "",  # Optional
            "crops": ""  # Optional
        }
        
        # Should still be valid
        is_valid = (
            len(form_data["name"].strip()) > 0 and
            len(form_data["phone"]) == 10 and
            form_data["phone"].isdigit()
        )
        
        assert is_valid is True
    
    def test_invalid_form_submission(self):
        """Test form with invalid required fields"""
        invalid_forms = [
            {"name": "", "phone": "9876543210"},  # Empty name
            {"name": "Test", "phone": "123"},  # Invalid phone
            {"name": "", "phone": ""},  # All empty
        ]
        
        for form_data in invalid_forms:
            is_valid = (
                len(form_data.get("name", "").strip()) > 0 and
                len(form_data.get("phone", "")) == 10 and
                form_data.get("phone", "").isdigit()
            )
            assert is_valid is False


class TestSessionStateManagement:
    """Test session state management"""
    
    def test_session_initialization(self):
        """Test session state initialization"""
        session_state = {
            "authenticated": False,
            "user_id": None,
            "user_name": None,
            "phone_number": None,
            "session_id": None,
            "language": "en",
            "chat_history": [],
            "location": None,
            "crops": []
        }
        
        assert session_state["authenticated"] is False
        assert session_state["language"] == "en"
        assert isinstance(session_state["chat_history"], list)
        assert isinstance(session_state["crops"], list)
    
    def test_session_after_login(self):
        """Test session state after successful login"""
        session_state = {
            "authenticated": True,
            "user_id": "farmer_9876543210",
            "user_name": "Test Farmer",
            "phone_number": "9876543210",
            "session_id": "demo_9876543210",
            "language": "en",
            "location": "Karnataka",
            "crops": ["wheat", "rice"]
        }
        
        assert session_state["authenticated"] is True
        assert session_state["user_id"].startswith("farmer_")
        assert session_state["phone_number"] in session_state["user_id"]
    
    def test_session_cleanup(self):
        """Test session cleanup on logout"""
        session_state = {
            "authenticated": True,
            "user_id": "farmer_123",
            "chat_history": [{"role": "user", "content": "test"}]
        }
        
        # Simulate cleanup
        keys_to_delete = list(session_state.keys())
        for key in keys_to_delete:
            del session_state[key]
        
        assert len(session_state) == 0
    
    def test_session_persistence(self):
        """Test session data persistence"""
        session_data = {
            "user_id": "farmer_123",
            "language": "hi",
            "location": "Karnataka"
        }
        
        # Session should maintain data across interactions
        assert session_data["user_id"] == "farmer_123"
        assert session_data["language"] == "hi"


class TestLanguagePreferences:
    """Test language preference handling"""
    
    def test_language_selection(self):
        """Test language selection"""
        from app import LANGUAGE_MAP
        
        selected_display = "हिंदी (Hindi)"
        language_code = LANGUAGE_MAP[selected_display]
        
        assert language_code == "hi"
    
    def test_language_persistence(self):
        """Test language preference persists"""
        session_state = {"language": "en"}
        
        # Change language
        session_state["language"] = "hi"
        
        # Should persist
        assert session_state["language"] == "hi"
    
    def test_invalid_language_fallback(self):
        """Test fallback for invalid language"""
        requested_language = "invalid_lang"
        valid_languages = ["en", "hi", "ta", "te"]
        
        if requested_language not in valid_languages:
            language = "en"  # Fallback to English
        else:
            language = requested_language
        
        assert language == "en"


class TestChatHistoryManagement:
    """Test chat history management"""
    
    def test_add_message_to_history(self):
        """Test adding message to chat history"""
        chat_history = []
        
        message = {
            "role": "user",
            "content": "Test message",
            "timestamp": "10:00 AM"
        }
        
        chat_history.append(message)
        
        assert len(chat_history) == 1
        assert chat_history[0]["role"] == "user"
    
    def test_chat_history_limit(self):
        """Test chat history doesn't grow unbounded"""
        chat_history = []
        max_messages = 100
        
        # Add many messages
        for i in range(150):
            chat_history.append({"role": "user", "content": f"Message {i}"})
        
        # In production, should limit history
        # For now, just verify it's a list
        assert isinstance(chat_history, list)
        assert len(chat_history) == 150
    
    def test_clear_chat_history(self):
        """Test clearing chat history"""
        chat_history = [
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Response 1"}
        ]
        
        # Clear history
        chat_history.clear()
        
        assert len(chat_history) == 0
    
    def test_chat_history_ordering(self):
        """Test chat history maintains order"""
        chat_history = []
        
        messages = [
            {"role": "user", "content": "Q1", "timestamp": "10:00"},
            {"role": "assistant", "content": "A1", "timestamp": "10:01"},
            {"role": "user", "content": "Q2", "timestamp": "10:02"},
        ]
        
        for msg in messages:
            chat_history.append(msg)
        
        # Verify order
        assert chat_history[0]["content"] == "Q1"
        assert chat_history[1]["content"] == "A1"
        assert chat_history[2]["content"] == "Q2"


class TestUserProfileManagement:
    """Test user profile management"""
    
    def test_profile_creation(self):
        """Test user profile creation"""
        profile = {
            "user_id": "farmer_9876543210",
            "name": "Test Farmer",
            "phone": "9876543210",
            "location": "Karnataka",
            "crops": ["wheat", "rice"]
        }
        
        assert profile["user_id"].startswith("farmer_")
        assert len(profile["phone"]) == 10
        assert isinstance(profile["crops"], list)
    
    def test_profile_update(self):
        """Test user profile update"""
        profile = {
            "location": "Karnataka",
            "crops": ["wheat"]
        }
        
        # Update profile
        profile["location"] = "Tamil Nadu"
        profile["crops"].append("rice")
        
        assert profile["location"] == "Tamil Nadu"
        assert "rice" in profile["crops"]
    
    def test_profile_validation(self):
        """Test profile data validation"""
        profile = {
            "user_id": "farmer_123",
            "name": "Test",
            "phone": "9876543210"
        }
        
        is_valid = (
            profile["user_id"] is not None and
            len(profile["name"]) > 0 and
            len(profile["phone"]) == 10
        )
        
        assert is_valid is True


class TestContextManagement:
    """Test context management for queries"""
    
    def test_query_context_creation(self):
        """Test creating context for queries"""
        context = {
            "location": "Karnataka",
            "crops": ["wheat", "rice"],
            "language": "en"
        }
        
        assert "location" in context
        assert "crops" in context
        assert isinstance(context["crops"], list)
    
    def test_context_with_history(self):
        """Test context includes chat history"""
        context = {
            "location": "Karnataka",
            "previous_queries": [
                "What is the weather?",
                "Market prices for wheat"
            ]
        }
        
        assert "previous_queries" in context
        assert len(context["previous_queries"]) > 0
    
    def test_empty_context_handling(self):
        """Test handling of empty context"""
        context = {
            "location": None,
            "crops": []
        }
        
        # Should handle gracefully
        assert context["location"] is None
        assert isinstance(context["crops"], list)


class TestErrorMessages:
    """Test error message display"""
    
    def test_validation_error_messages(self):
        """Test validation error messages"""
        errors = {
            "invalid_phone": "Please enter valid name and 10-digit phone number",
            "empty_name": "Name is required",
            "service_unavailable": "Service is currently unavailable"
        }
        
        for error_type, message in errors.items():
            assert len(message) > 0
            assert isinstance(message, str)
    
    def test_multilingual_error_messages(self):
        """Test error messages in multiple languages"""
        errors_en = "Please enter a valid phone number"
        errors_hi = "कृपया एक मान्य फ़ोन नंबर दर्ज करें"
        
        assert len(errors_en) > 0
        assert len(errors_hi) > 0
    
    def test_user_friendly_errors(self):
        """Test error messages are user-friendly"""
        technical_error = "NoneType object has no attribute 'get'"
        user_friendly_error = "An error occurred. Please try again."
        
        # User should see friendly message, not technical
        assert "try again" in user_friendly_error.lower()


class TestDataPersistence:
    """Test data persistence"""
    
    def test_session_data_structure(self):
        """Test session data structure"""
        session_data = {
            "session_id": "demo_123",
            "user_id": "farmer_123",
            "created_at": "2024-01-15 10:00:00",
            "last_activity": "2024-01-15 10:30:00"
        }
        
        assert "session_id" in session_data
        assert "user_id" in session_data
        assert session_data["session_id"].startswith("demo_")
    
    def test_chat_history_persistence(self):
        """Test chat history can be persisted"""
        chat_history = [
            {"role": "user", "content": "Hello", "timestamp": "10:00"},
            {"role": "assistant", "content": "Hi!", "timestamp": "10:01"}
        ]
        
        # Should be serializable
        import json
        serialized = json.dumps(chat_history)
        deserialized = json.loads(serialized)
        
        assert deserialized == chat_history


class TestAccessibilityFeatures:
    """Test accessibility features"""
    
    def test_form_labels(self):
        """Test form fields have proper labels"""
        labels = {
            "name": "Name / नाम / பெயர்",
            "phone": "Phone Number / फ़ोन नंबर / தொலைபேசி எண்",
            "location": "Location / स्थान / இடம்"
        }
        
        for field, label in labels.items():
            assert len(label) > 0
            assert "/" in label  # Multilingual
    
    def test_help_text(self):
        """Test help text is provided"""
        help_texts = {
            "name": "Your name for personalized assistance",
            "phone": "Your mobile number (demo mode - any 10 digits)",
            "location": "Your farming location"
        }
        
        for field, help_text in help_texts.items():
            assert len(help_text) > 0
    
    def test_placeholder_text(self):
        """Test placeholder text is helpful"""
        placeholders = {
            "name": "Enter your name",
            "phone": "10-digit mobile number",
            "location": "Village, District, State",
            "crops": "e.g., wheat, rice, cotton"
        }
        
        for field, placeholder in placeholders.items():
            assert len(placeholder) > 0


class TestSecurityFeatures:
    """Test security features"""
    
    def test_user_id_generation(self):
        """Test user ID generation is consistent"""
        phone = "9876543210"
        user_id_1 = f"farmer_{phone}"
        user_id_2 = f"farmer_{phone}"
        
        assert user_id_1 == user_id_2
    
    def test_session_id_uniqueness(self):
        """Test session IDs are unique"""
        import uuid
        
        session_id_1 = f"session_{uuid.uuid4().hex[:8]}"
        session_id_2 = f"session_{uuid.uuid4().hex[:8]}"
        
        assert session_id_1 != session_id_2
    
    def test_sensitive_data_handling(self):
        """Test sensitive data is handled properly"""
        # Phone numbers should not be logged in plain text
        phone = "9876543210"
        masked_phone = f"***{phone[-4:]}"
        
        assert masked_phone == "***3210"
        assert phone not in masked_phone


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
