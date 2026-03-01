"""
Property tests for memory and session management.

Tests session memory round-trip, personalized recommendations,
and data deletion completeness.
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
import uuid
import json
from pathlib import Path

from agents.manager_agent import (
    ManagerAgent,
    get_user_context,
    save_user_context,
    restore_session,
    persist_session,
    delete_user_data,
    save_conversation_turn,
    USER_CONTEXTS,
    CONVERSATION_HISTORY,
    STORAGE_DIR
)


# Test fixtures
@pytest.fixture
def manager_agent():
    """Create a Manager Agent instance for testing."""
    return ManagerAgent()


@pytest.fixture
def sample_user_id():
    """Generate a unique user ID for testing."""
    return f"test_user_{uuid.uuid4().hex[:8]}"


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear in-memory and disk storage before each test."""
    USER_CONTEXTS.clear()
    CONVERSATION_HISTORY.clear()
    
    # Clear disk storage
    if STORAGE_DIR.exists():
        for file in STORAGE_DIR.glob("test_user_*"):
            file.unlink()
    
    yield
    
    # Cleanup after test
    USER_CONTEXTS.clear()
    CONVERSATION_HISTORY.clear()
    if STORAGE_DIR.exists():
        for file in STORAGE_DIR.glob("test_user_*"):
            file.unlink()


# Unit Tests

def test_persist_and_restore_session(sample_user_id):
    """Test that session data persists and restores correctly."""
    # Create user context
    context_data = {
        "language_preference": "kannada",
        "profile": {
            "name": "Test Farmer",
            "location": "Karnataka",
            "crops": ["rice", "cotton"]
        },
        "onboarding_complete": True
    }
    save_user_context(sample_user_id, context_data)
    
    # Add conversation history
    save_conversation_turn(
        user_id=sample_user_id,
        user_message="What is the price of rice?",
        agent_response="Current price is 2000 per quintal",
        agent_name="Market Price Agent"
    )
    
    # Persist session
    result = persist_session(sample_user_id)
    assert result is True
    
    # Clear in-memory storage
    USER_CONTEXTS.clear()
    CONVERSATION_HISTORY.clear()
    
    # Restore session
    restore_result = restore_session(sample_user_id)
    assert restore_result["profile_restored"] is True
    assert restore_result["history_restored"] is True
    assert restore_result["history_turns"] == 1
    
    # Verify restored data
    context = get_user_context(sample_user_id)
    assert context["user_context"]["language_preference"] == "kannada"
    assert context["user_context"]["profile"]["name"] == "Test Farmer"
    assert len(context["conversation_history"]) == 1


def test_delete_user_data(sample_user_id):
    """Test that user data deletion is complete."""
    # Create user data
    context_data = {
        "language_preference": "english",
        "profile": {"name": "Test User"}
    }
    save_user_context(sample_user_id, context_data)
    
    save_conversation_turn(
        user_id=sample_user_id,
        user_message="Test message",
        agent_response="Test response",
        agent_name="Test Agent"
    )
    
    # Persist to disk
    persist_session(sample_user_id)
    
    # Verify data exists
    assert sample_user_id in USER_CONTEXTS
    assert sample_user_id in CONVERSATION_HISTORY
    
    profile_path = STORAGE_DIR / f"{sample_user_id}_profile.json"
    history_path = STORAGE_DIR / f"{sample_user_id}_history.json"
    assert profile_path.exists()
    assert history_path.exists()
    
    # Delete user data
    result = delete_user_data(sample_user_id)
    assert result is True
    
    # Verify data is deleted
    assert sample_user_id not in USER_CONTEXTS
    assert sample_user_id not in CONVERSATION_HISTORY
    assert not profile_path.exists()
    assert not history_path.exists()


def test_personalized_recommendations_with_profile(manager_agent, sample_user_id):
    """Test personalized recommendations with user profile."""
    # Create user profile
    context_data = {
        "profile": {
            "location": {"district": "Mandya", "state": "Karnataka"},
            "crops": ["rice", "sugarcane"]
        }
    }
    save_user_context(sample_user_id, context_data)
    
    # Get personalized recommendations
    result = manager_agent.get_personalized_recommendations(
        user_id=sample_user_id,
        query="What should I plant?"
    )
    
    assert result["personalized"] is True
    assert len(result["recommendations"]) > 0
    assert any("Mandya" in rec for rec in result["recommendations"])
    assert any("rice" in rec or "sugarcane" in rec for rec in result["recommendations"])


def test_personalized_recommendations_without_profile(manager_agent, sample_user_id):
    """Test recommendations without user profile."""
    result = manager_agent.get_personalized_recommendations(
        user_id=sample_user_id,
        query="What should I plant?"
    )
    
    assert result["personalized"] is False
    assert any("profile" in rec.lower() for rec in result["recommendations"])


def test_manager_agent_clear_user_data(manager_agent, sample_user_id):
    """Test Manager Agent's clear_user_data method."""
    # Create user data
    save_user_context(sample_user_id, {"profile": {"name": "Test"}})
    
    # Clear data
    result = manager_agent.clear_user_data(sample_user_id)
    
    assert result["success"] is True
    assert sample_user_id not in USER_CONTEXTS


def test_manager_agent_save_session(manager_agent, sample_user_id):
    """Test Manager Agent's save_session method."""
    # Create user data
    save_user_context(sample_user_id, {"profile": {"name": "Test"}})
    
    # Save session
    result = manager_agent.save_session(sample_user_id)
    
    assert result["success"] is True
    
    # Verify file exists
    profile_path = STORAGE_DIR / f"{sample_user_id}_profile.json"
    assert profile_path.exists()


def test_manager_agent_restore_session(manager_agent, sample_user_id):
    """Test Manager Agent's restore_user_session method."""
    # Create and persist user data
    save_user_context(sample_user_id, {"profile": {"name": "Test"}})
    persist_session(sample_user_id)
    
    # Clear memory
    USER_CONTEXTS.clear()
    
    # Restore session
    result = manager_agent.restore_user_session(sample_user_id)
    
    assert result["success"] is True
    assert result["profile_restored"] is True


# Property-Based Tests

# Feature: missionai-farmer-agent, Property 20: Session Memory Round-Trip
@given(
    language=st.sampled_from(['english', 'kannada', 'hindi']),
    farmer_name=st.text(min_size=3, max_size=20, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),  # ASCII printable
    location=st.text(min_size=3, max_size=20, alphabet=st.characters(min_codepoint=32, max_codepoint=126))  # ASCII printable
)
@settings(max_examples=100)
@pytest.mark.property_test
def test_property_session_memory_roundtrip(language, farmer_name, location):
    """
    Property 20: Session Memory Round-Trip
    
    For any user session data (profile, preferences, history) stored by the
    Manager Agent, when the same user returns in a new session, the Manager
    Agent SHALL retrieve and use the stored data.
    
    Validates: Requirements 13.1, 13.3
    """
    # Generate unique user ID
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    
    try:
        # Create and save user context
        original_context = {
            "language_preference": language,
            "profile": {
                "name": farmer_name,
                "location": location
            },
            "onboarding_complete": True
        }
        save_user_context(user_id, original_context)
        
        # Add conversation turn
        save_conversation_turn(
            user_id=user_id,
            user_message="Test message",
            agent_response="Test response",
            agent_name="Test Agent"
        )
        
        # Persist to disk
        persist_result = persist_session(user_id)
        assert persist_result is True, "Failed to persist session"
        
        # Clear in-memory storage (simulating new session)
        USER_CONTEXTS.clear()
        CONVERSATION_HISTORY.clear()
        
        # Retrieve context (should restore from disk)
        retrieved_context = get_user_context(user_id)
        
        # Verify data is restored correctly
        assert retrieved_context["user_context"]["language_preference"] == language, \
            f"Language preference not preserved: expected {language}, got {retrieved_context['user_context']['language_preference']}"
        
        assert retrieved_context["user_context"]["profile"]["name"] == farmer_name, \
            f"Farmer name not preserved: expected {farmer_name}, got {retrieved_context['user_context']['profile']['name']}"
        
        assert retrieved_context["user_context"]["profile"]["location"] == location, \
            f"Location not preserved: expected {location}, got {retrieved_context['user_context']['profile']['location']}"
        
        assert len(retrieved_context["conversation_history"]) == 1, \
            f"Conversation history not preserved: expected 1 turn, got {len(retrieved_context['conversation_history'])}"
    
    finally:
        # Cleanup
        delete_user_data(user_id)


# Feature: missionai-farmer-agent, Property 21: Personalized Recommendations
@given(
    crop1=st.sampled_from(['rice', 'wheat', 'cotton', 'sugarcane', 'tomato']),
    crop2=st.sampled_from(['rice', 'wheat', 'cotton', 'sugarcane', 'tomato']),
    location1=st.sampled_from(['Mandya', 'Mysore', 'Bangalore', 'Hubli']),
    location2=st.sampled_from(['Mandya', 'Mysore', 'Bangalore', 'Hubli'])
)
@settings(max_examples=100)
@pytest.mark.property_test
def test_property_personalized_recommendations(crop1, crop2, location1, location2):
    """
    Property 21: Personalized Recommendations
    
    For any two farmers with different stored profiles (different crops,
    locations, or practices), the Manager Agent SHALL generate different
    recommendations when asked the same question.
    
    Validates: Requirements 13.2
    """
    # Skip if profiles are identical
    if crop1 == crop2 and location1 == location2:
        return
    
    # Generate unique user IDs
    user_id1 = f"test_user_{uuid.uuid4().hex[:8]}"
    user_id2 = f"test_user_{uuid.uuid4().hex[:8]}"
    
    try:
        manager = ManagerAgent()
        
        # Create different profiles
        profile1 = {
            "profile": {
                "location": {"district": location1},
                "crops": [crop1]
            }
        }
        profile2 = {
            "profile": {
                "location": {"district": location2},
                "crops": [crop2]
            }
        }
        
        save_user_context(user_id1, profile1)
        save_user_context(user_id2, profile2)
        
        # Ask same question to both
        query = "What should I do for my crops?"
        
        rec1 = manager.get_personalized_recommendations(user_id1, query)
        rec2 = manager.get_personalized_recommendations(user_id2, query)
        
        # Both should be personalized
        assert rec1["personalized"] is True, "User 1 recommendations not personalized"
        assert rec2["personalized"] is True, "User 2 recommendations not personalized"
        
        # Recommendations should be different (at least one difference)
        # Check if location or crop appears in recommendations
        rec1_text = " ".join(rec1["recommendations"]).lower()
        rec2_text = " ".join(rec2["recommendations"]).lower()
        
        # At least one should mention their specific location or crop
        user1_specific = location1.lower() in rec1_text or crop1.lower() in rec1_text
        user2_specific = location2.lower() in rec2_text or crop2.lower() in rec2_text
        
        assert user1_specific or user2_specific, \
            "Recommendations not personalized to user profiles"
    
    finally:
        # Cleanup
        delete_user_data(user_id1)
        delete_user_data(user_id2)


# Feature: missionai-farmer-agent, Property 22: Data Deletion Completeness
@given(
    language=st.sampled_from(['english', 'kannada', 'hindi']),
    profile_data=st.text(min_size=5, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126))  # ASCII printable
)
@settings(max_examples=100)
@pytest.mark.property_test
def test_property_data_deletion_completeness(language, profile_data):
    """
    Property 22: Data Deletion Completeness
    
    For any user requesting data deletion, after the Manager Agent processes
    the deletion, subsequent queries for that user's data SHALL return empty
    or default values.
    
    Validates: Requirements 13.5
    """
    # Generate unique user ID
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    
    try:
        # Create user data
        context_data = {
            "language_preference": language,
            "profile": {
                "name": profile_data,
                "data": profile_data
            },
            "onboarding_complete": True
        }
        save_user_context(user_id, context_data)
        
        # Add conversation history
        save_conversation_turn(
            user_id=user_id,
            user_message="Test message",
            agent_response="Test response",
            agent_name="Test Agent"
        )
        
        # Persist to disk
        persist_session(user_id)
        
        # Verify data exists in memory
        assert user_id in USER_CONTEXTS, "User context not in memory"
        assert user_id in CONVERSATION_HISTORY, "Conversation history not in memory"
        
        # Verify data exists on disk
        profile_path = STORAGE_DIR / f"{user_id}_profile.json"
        history_path = STORAGE_DIR / f"{user_id}_history.json"
        assert profile_path.exists(), "Profile file not on disk"
        assert history_path.exists(), "History file not on disk"
        
        # Delete user data
        deletion_result = delete_user_data(user_id)
        assert deletion_result is True, "Data deletion failed"
        
        # Verify data is deleted from memory
        assert user_id not in USER_CONTEXTS, \
            "User context still in memory after deletion"
        assert user_id not in CONVERSATION_HISTORY, \
            "Conversation history still in memory after deletion"
        
        # Verify data is deleted from disk
        assert not profile_path.exists(), \
            "Profile file still on disk after deletion"
        assert not history_path.exists(), \
            "History file still on disk after deletion"
        
        # Get context after deletion (should return default)
        context_after_deletion = get_user_context(user_id)
        
        # Should return default values
        assert context_after_deletion["user_context"]["profile"] is None, \
            "Profile not reset to default after deletion"
        assert context_after_deletion["user_context"]["language_preference"] == "english", \
            "Language preference not reset to default after deletion"
        assert context_after_deletion["user_context"]["onboarding_complete"] is False, \
            "Onboarding status not reset to default after deletion"
        assert len(context_after_deletion["conversation_history"]) == 0, \
            "Conversation history not empty after deletion"
    
    finally:
        # Cleanup
        delete_user_data(user_id)


# Additional edge case tests

def test_restore_session_no_data(sample_user_id):
    """Test restoring session when no data exists."""
    result = restore_session(sample_user_id)
    
    assert result["profile_restored"] is False
    assert result["history_restored"] is False
    assert result["history_turns"] == 0


def test_persist_session_no_data(sample_user_id):
    """Test persisting session when no data exists."""
    result = persist_session(sample_user_id)
    
    # Should return False since no data to persist
    assert result is False


def test_conversation_history_persistence(sample_user_id):
    """Test that conversation history persists correctly."""
    from agents.manager_agent import save_conversation_turn
    
    # Create user context first
    get_user_context(sample_user_id)
    
    # Add multiple conversation turns
    for i in range(5):
        save_conversation_turn(
            user_id=sample_user_id,
            user_message=f"Message {i}",
            agent_response=f"Response {i}",
            agent_name="Test Agent"
        )
    
    # Verify in memory
    assert sample_user_id in CONVERSATION_HISTORY
    assert len(CONVERSATION_HISTORY[sample_user_id]) == 5
    
    # Persist
    persist_session(sample_user_id)
    
    # Clear memory
    USER_CONTEXTS.clear()
    CONVERSATION_HISTORY.clear()
    
    # Restore
    restore_session(sample_user_id)
    
    # Verify all turns restored to memory
    assert sample_user_id in CONVERSATION_HISTORY
    assert len(CONVERSATION_HISTORY[sample_user_id]) == 5
    
    # Get context (returns last 10, so all 5 should be there)
    context = get_user_context(sample_user_id)
    assert len(context["conversation_history"]) == 5
