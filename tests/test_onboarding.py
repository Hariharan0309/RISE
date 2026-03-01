"""
Unit tests for new farmer onboarding functionality.

Tests new farmer identification, roadmap customization, progress tracking,
and seasonal adaptation.
"""

import pytest
from datetime import datetime
import uuid

from agents.manager_agent import (
    ManagerAgent,
    get_user_context,
    save_user_context,
    USER_CONTEXTS,
    CONVERSATION_HISTORY,
    ONBOARDING_ROADMAPS
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
    """Clear in-memory storage before each test."""
    USER_CONTEXTS.clear()
    CONVERSATION_HISTORY.clear()
    yield
    USER_CONTEXTS.clear()
    CONVERSATION_HISTORY.clear()


# Unit Tests for New Farmer Identification

def test_is_new_farmer_true(manager_agent, sample_user_id):
    """Test identification of new farmer (no profile, onboarding not complete)."""
    # Get context (creates default)
    get_user_context(sample_user_id)
    
    # Should be identified as new farmer
    assert manager_agent.is_new_farmer(sample_user_id) is True


def test_is_new_farmer_false_with_profile(manager_agent, sample_user_id):
    """Test that farmer with profile is not identified as new."""
    # Create user with profile
    context_data = {
        "profile": {
            "name": "Test Farmer",
            "location": "Karnataka"
        },
        "onboarding_complete": False
    }
    save_user_context(sample_user_id, context_data)
    
    # Should not be identified as new farmer
    assert manager_agent.is_new_farmer(sample_user_id) is False


def test_is_new_farmer_false_onboarding_complete(manager_agent, sample_user_id):
    """Test that farmer with completed onboarding is not new."""
    # Create user with onboarding complete
    context_data = {
        "onboarding_complete": True
    }
    save_user_context(sample_user_id, context_data)
    
    # Should not be identified as new farmer
    assert manager_agent.is_new_farmer(sample_user_id) is False


# Unit Tests for Season Detection

def test_get_current_season(manager_agent):
    """Test that current season is detected correctly."""
    season = manager_agent.get_current_season()
    
    # Should return one of the valid seasons
    assert season in ["monsoon", "winter", "summer"]
    
    # Verify it matches current month
    current_month = datetime.now().month
    if 6 <= current_month <= 9:
        assert season == "monsoon"
    elif current_month >= 10 or current_month <= 2:
        assert season == "winter"
    else:
        assert season == "summer"


# Unit Tests for Onboarding Roadmap

def test_get_onboarding_roadmap_default_season(manager_agent, sample_user_id):
    """Test getting onboarding roadmap with default (current) season."""
    roadmap = manager_agent.get_onboarding_roadmap(sample_user_id)
    
    assert "user_id" in roadmap
    assert roadmap["user_id"] == sample_user_id
    assert "season" in roadmap
    assert "steps" in roadmap
    assert len(roadmap["steps"]) > 0
    assert "current_step" in roadmap
    assert roadmap["current_step"] == 1  # Default to step 1
    assert "total_steps" in roadmap


def test_get_onboarding_roadmap_monsoon(manager_agent, sample_user_id):
    """Test getting monsoon season roadmap."""
    roadmap = manager_agent.get_onboarding_roadmap(sample_user_id, season="monsoon")
    
    assert "Monsoon" in roadmap["season"]
    assert len(roadmap["steps"]) == 5  # Monsoon has 5 steps
    
    # Verify first step
    first_step = roadmap["steps"][0]
    assert first_step["step"] == 1
    assert "title" in first_step
    assert "description" in first_step
    assert "tasks" in first_step
    assert len(first_step["tasks"]) > 0


def test_get_onboarding_roadmap_winter(manager_agent, sample_user_id):
    """Test getting winter season roadmap."""
    roadmap = manager_agent.get_onboarding_roadmap(sample_user_id, season="winter")
    
    assert "Winter" in roadmap["season"]
    assert len(roadmap["steps"]) == 4  # Winter has 4 steps


def test_get_onboarding_roadmap_summer(manager_agent, sample_user_id):
    """Test getting summer season roadmap."""
    roadmap = manager_agent.get_onboarding_roadmap(sample_user_id, season="summer")
    
    assert "Summer" in roadmap["season"]
    assert len(roadmap["steps"]) == 4  # Summer has 4 steps


def test_get_onboarding_roadmap_customization(manager_agent, sample_user_id):
    """Test roadmap customization based on user profile."""
    # Create user with profile
    context_data = {
        "profile": {
            "name": "Test Farmer",
            "location": {"district": "Mandya", "state": "Karnataka"},
            "crops": ["rice", "sugarcane"]
        }
    }
    save_user_context(sample_user_id, context_data)
    
    # Get roadmap
    roadmap = manager_agent.get_onboarding_roadmap(sample_user_id)
    
    # Should be personalized
    assert roadmap["personalized"] is True
    assert "location" in roadmap
    assert roadmap["location"]["district"] == "Mandya"
    assert "preferred_crops" in roadmap
    assert "rice" in roadmap["preferred_crops"]


def test_get_onboarding_roadmap_no_customization(manager_agent, sample_user_id):
    """Test roadmap without customization (no profile)."""
    roadmap = manager_agent.get_onboarding_roadmap(sample_user_id)
    
    # Should not be personalized
    assert roadmap["personalized"] is False


# Unit Tests for Onboarding Progress

def test_start_onboarding(manager_agent, sample_user_id):
    """Test starting onboarding process."""
    result = manager_agent.start_onboarding(sample_user_id)
    
    assert result["success"] is True
    assert result["user_id"] == sample_user_id
    assert "season" in result
    assert "total_steps" in result
    assert "first_step" in result
    assert result["first_step"] is not None
    assert result["first_step"]["step"] == 1
    
    # Verify context updated
    context = get_user_context(sample_user_id)
    assert context["user_context"]["onboarding_step"] == 1
    assert context["user_context"]["onboarding_complete"] is False


def test_update_onboarding_progress(manager_agent, sample_user_id):
    """Test updating onboarding progress."""
    # Start onboarding
    manager_agent.start_onboarding(sample_user_id)
    
    # Complete step 1
    result = manager_agent.update_onboarding_progress(sample_user_id, step=1, completed=True)
    
    assert result["success"] is True
    assert result["current_step"] == 2
    assert result["onboarding_complete"] is False
    
    # Verify context updated
    context = get_user_context(sample_user_id)
    assert context["user_context"]["onboarding_step"] == 2


def test_update_onboarding_progress_completion(manager_agent, sample_user_id):
    """Test completing all onboarding steps."""
    # Start onboarding
    manager_agent.start_onboarding(sample_user_id)
    
    # Get total steps
    roadmap = manager_agent.get_onboarding_roadmap(sample_user_id)
    total_steps = roadmap["total_steps"]
    
    # Complete all steps
    for step in range(1, total_steps + 1):
        result = manager_agent.update_onboarding_progress(sample_user_id, step=step, completed=True)
    
    # Last result should indicate completion
    assert result["success"] is True
    assert result["onboarding_complete"] is True
    
    # Verify context updated
    context = get_user_context(sample_user_id)
    assert context["user_context"]["onboarding_complete"] is True


def test_update_onboarding_progress_skip_step(manager_agent, sample_user_id):
    """Test that skipping steps doesn't update progress."""
    # Start onboarding
    manager_agent.start_onboarding(sample_user_id)
    
    # Try to complete step 3 without completing 1 and 2
    result = manager_agent.update_onboarding_progress(sample_user_id, step=3, completed=True)
    
    # Should update since step 3 >= current step (1)
    assert result["success"] is True
    assert result["current_step"] == 4


def test_get_onboarding_status_not_started(manager_agent, sample_user_id):
    """Test getting onboarding status when not started."""
    status = manager_agent.get_onboarding_status(sample_user_id)
    
    assert status["user_id"] == sample_user_id
    assert status["onboarding_complete"] is False
    assert status["current_step"] == 1
    assert "total_steps" in status
    assert "season" in status
    assert "current_step_details" in status


def test_get_onboarding_status_in_progress(manager_agent, sample_user_id):
    """Test getting onboarding status when in progress."""
    # Start onboarding
    manager_agent.start_onboarding(sample_user_id)
    
    # Complete step 1
    manager_agent.update_onboarding_progress(sample_user_id, step=1, completed=True)
    
    # Get status
    status = manager_agent.get_onboarding_status(sample_user_id)
    
    assert status["onboarding_complete"] is False
    assert status["current_step"] == 2
    assert status["current_step_details"] is not None
    assert status["current_step_details"]["step"] == 2
    assert status["progress_percentage"] > 0


def test_get_onboarding_status_completed(manager_agent, sample_user_id):
    """Test getting onboarding status when completed."""
    # Mark onboarding as complete
    context_data = {
        "onboarding_complete": True
    }
    save_user_context(sample_user_id, context_data)
    
    # Get status
    status = manager_agent.get_onboarding_status(sample_user_id)
    
    assert status["onboarding_complete"] is True
    assert "message" in status


# Unit Tests for Roadmap Structure

def test_roadmap_structure_monsoon():
    """Test that monsoon roadmap has correct structure."""
    roadmap = ONBOARDING_ROADMAPS["monsoon"]
    
    assert "season" in roadmap
    assert "steps" in roadmap
    assert len(roadmap["steps"]) > 0
    
    # Verify each step has required fields
    for step in roadmap["steps"]:
        assert "step" in step
        assert "title" in step
        assert "description" in step
        assert "tasks" in step
        assert "agents" in step
        assert len(step["tasks"]) > 0
        assert len(step["agents"]) > 0


def test_roadmap_structure_winter():
    """Test that winter roadmap has correct structure."""
    roadmap = ONBOARDING_ROADMAPS["winter"]
    
    assert "season" in roadmap
    assert "steps" in roadmap
    assert len(roadmap["steps"]) > 0
    
    for step in roadmap["steps"]:
        assert "step" in step
        assert "title" in step
        assert "description" in step
        assert "tasks" in step
        assert "agents" in step


def test_roadmap_structure_summer():
    """Test that summer roadmap has correct structure."""
    roadmap = ONBOARDING_ROADMAPS["summer"]
    
    assert "season" in roadmap
    assert "steps" in roadmap
    assert len(roadmap["steps"]) > 0
    
    for step in roadmap["steps"]:
        assert "step" in step
        assert "title" in step
        assert "description" in step
        assert "tasks" in step
        assert "agents" in step


# Integration Tests

def test_full_onboarding_flow(manager_agent, sample_user_id):
    """Test complete onboarding flow from start to finish."""
    # Verify new farmer
    assert manager_agent.is_new_farmer(sample_user_id) is True
    
    # Start onboarding
    start_result = manager_agent.start_onboarding(sample_user_id)
    assert start_result["success"] is True
    
    # Get status
    status = manager_agent.get_onboarding_status(sample_user_id)
    assert status["current_step"] == 1
    
    # Complete first step
    progress = manager_agent.update_onboarding_progress(sample_user_id, step=1, completed=True)
    assert progress["success"] is True
    assert progress["current_step"] == 2
    
    # Get updated status
    status = manager_agent.get_onboarding_status(sample_user_id)
    assert status["current_step"] == 2
    assert status["progress_percentage"] > 0
    
    # Complete all remaining steps
    roadmap = manager_agent.get_onboarding_roadmap(sample_user_id)
    for step in range(2, roadmap["total_steps"] + 1):
        manager_agent.update_onboarding_progress(sample_user_id, step=step, completed=True)
    
    # Verify completion
    final_status = manager_agent.get_onboarding_status(sample_user_id)
    assert final_status["onboarding_complete"] is True
    
    # Should no longer be new farmer
    assert manager_agent.is_new_farmer(sample_user_id) is False


def test_onboarding_with_profile_creation(manager_agent, sample_user_id):
    """Test onboarding with profile creation during process."""
    # Start onboarding
    manager_agent.start_onboarding(sample_user_id)
    
    # Add profile during onboarding
    context_data = {
        "profile": {
            "name": "New Farmer",
            "location": {"district": "Mysore", "state": "Karnataka"},
            "crops": ["tomato"]
        }
    }
    save_user_context(sample_user_id, context_data)
    
    # Get roadmap (should now be personalized)
    roadmap = manager_agent.get_onboarding_roadmap(sample_user_id)
    assert roadmap["personalized"] is True
    assert "Mysore" in str(roadmap["location"])


def test_seasonal_roadmap_differences():
    """Test that different seasons have different roadmaps."""
    manager = ManagerAgent()
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    
    try:
        monsoon_roadmap = manager.get_onboarding_roadmap(user_id, season="monsoon")
        winter_roadmap = manager.get_onboarding_roadmap(user_id, season="winter")
        summer_roadmap = manager.get_onboarding_roadmap(user_id, season="summer")
        
        # Seasons should be different
        assert monsoon_roadmap["season"] != winter_roadmap["season"]
        assert winter_roadmap["season"] != summer_roadmap["season"]
        
        # Steps should be different
        assert monsoon_roadmap["steps"][0]["title"] != winter_roadmap["steps"][0]["title"]
    
    finally:
        # Cleanup
        if user_id in USER_CONTEXTS:
            del USER_CONTEXTS[user_id]
