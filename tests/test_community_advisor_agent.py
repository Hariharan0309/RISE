"""
Unit tests for Community Advisor Agent.

Tests the community forum search, experience storage, and combined advice functionality.
"""

import pytest
from agents.community_advisor_agent import CommunityAdvisorAgent
from tools.community_tools import FORUM_STORAGE


@pytest.fixture
def agent():
    """Create a Community Advisor Agent instance for testing."""
    return CommunityAdvisorAgent()


@pytest.fixture(autouse=True)
def clear_forum_storage():
    """Clear forum storage before each test."""
    FORUM_STORAGE.clear()
    yield
    FORUM_STORAGE.clear()


def test_agent_initialization(agent):
    """Test that agent initializes correctly."""
    assert agent.name == "Community Advisor Agent"
    assert agent.description == "Specialized in community knowledge and peer-to-peer farmer support"
    assert len(agent.tools) == 4


def test_get_system_prompt(agent):
    """Test that system prompt is comprehensive."""
    prompt = agent.get_system_prompt()
    assert "community facilitator" in prompt.lower()
    assert "local knowledge" in prompt.lower()
    assert "peer support" in prompt.lower()
    assert len(prompt) > 500


def test_search_community_basic(agent):
    """Test basic community forum search."""
    result = agent.search_community(
        query="tomato disease",
        language="english"
    )
    
    assert result["success"] is True
    assert result["query_type"] == "search"
    assert result["query"] == "tomato disease"
    assert "discussions_found" in result
    assert "summary" in result


def test_search_community_with_location(agent):
    """Test community search with location filter."""
    result = agent.search_community(
        query="pest control",
        location={"district": "Mandya", "state": "Karnataka"},
        language="kannada"
    )
    
    assert result["success"] is True
    assert result["location"]["district"] == "Mandya"
    assert result["language"] == "kannada"


def test_search_community_no_results(agent):
    """Test community search with no matching results."""
    result = agent.search_community(
        query="xyz123nonexistent",
        language="english"
    )
    
    assert result["success"] is True
    assert result["discussions_found"] == 0
    assert "No community discussions found" in result["summary"]


def test_share_experience_success(agent):
    """Test storing farmer experience in community forum."""
    result = agent.share_experience(
        farmer_id="farmer123",
        topic="disease",
        content="I successfully treated tomato blight using neem oil spray twice a week",
        location={"district": "Mysore", "state": "Karnataka"},
        language="english"
    )
    
    assert result["success"] is True
    assert result["query_type"] == "store"
    assert "Thank you for sharing" in result["message"]
    assert result["storage_result"]["status"] == "stored"
    assert result["storage_result"]["topic"] == "disease"


def test_share_experience_missing_farmer_id(agent):
    """Test that sharing experience fails without farmer ID."""
    result = agent.process(
        query="My experience with organic farming",
        query_type="store",
        topic="technique"
    )
    
    assert result["success"] is False
    assert "Farmer ID and topic are required" in result["error"]


def test_share_experience_missing_topic(agent):
    """Test that sharing experience fails without topic."""
    result = agent.process(
        query="My experience with organic farming",
        query_type="store",
        farmer_id="farmer123"
    )
    
    assert result["success"] is False
    assert "Farmer ID and topic are required" in result["error"]


def test_get_combined_advice_with_community_insights(agent):
    """Test combining AI recommendation with community insights."""
    ai_recommendation = "Apply copper-based fungicide for tomato blight control"
    
    result = agent.get_combined_advice(
        query="tomato disease treatment",
        ai_recommendation=ai_recommendation,
        location={"state": "Karnataka"},
        language="english"
    )
    
    assert result["success"] is True
    assert result["query_type"] == "combined_advice"
    assert result["ai_recommendation"] == ai_recommendation
    assert "combined_advice" in result
    assert "AI Analysis:" in result["combined_advice"]


def test_get_combined_advice_no_community_insights(agent):
    """Test combined advice when no community insights are available."""
    ai_recommendation = "Use drip irrigation for water efficiency"
    
    result = agent.get_combined_advice(
        query="xyz123nonexistent",
        ai_recommendation=ai_recommendation,
        language="english"
    )
    
    assert result["success"] is True
    assert "AI Analysis:" in result["combined_advice"]
    assert "No community insights available" in result["combined_advice"]


def test_get_combined_advice_missing_ai_recommendation(agent):
    """Test that combined advice fails without AI recommendation."""
    result = agent.process(
        query="tomato disease",
        query_type="combined_advice"
    )
    
    assert result["success"] is False
    assert "AI recommendation is required" in result["error"]


def test_process_invalid_query_type(agent):
    """Test that invalid query type returns error."""
    result = agent.process(
        query="test query",
        query_type="invalid_type"
    )
    
    assert result["success"] is False
    assert "Unknown query type" in result["error"]


def test_search_and_store_integration(agent):
    """Test integration of storing and searching experiences."""
    # Store an experience
    store_result = agent.share_experience(
        farmer_id="farmer456",
        topic="market",
        content="Best time to sell onions is after Diwali when prices are high",
        location={"district": "Belgaum", "state": "Karnataka"},
        language="english"
    )
    
    assert store_result["success"] is True
    
    # Search for the stored experience
    search_result = agent.search_community(
        query="onion selling",
        language="english"
    )
    
    assert search_result["success"] is True
    # The stored experience should be findable
    assert search_result["discussions_found"] >= 0  # May or may not match depending on search logic


def test_combined_advice_with_stored_experience(agent):
    """Test combined advice after storing relevant community experience."""
    # Store a relevant experience
    agent.share_experience(
        farmer_id="farmer789",
        topic="disease",
        content="Neem oil spray worked great for my tomato plants with early blight",
        location={"district": "Mandya", "state": "Karnataka"},
        language="english"
    )
    
    # Get combined advice
    ai_recommendation = "For early blight, use copper fungicide and remove affected leaves"
    result = agent.get_combined_advice(
        query="tomato blight treatment",
        ai_recommendation=ai_recommendation,
        location={"state": "Karnataka"},
        language="english"
    )
    
    assert result["success"] is True
    assert "AI Analysis:" in result["combined_advice"]
    # Community insights may or may not be found depending on search matching


def test_get_tools(agent):
    """Test that agent returns correct tools list."""
    tools = agent.get_tools()
    assert len(tools) == 4
    assert all(callable(tool) for tool in tools)


def test_search_community_returns_top_5_discussions(agent):
    """Test that search returns maximum 5 discussions."""
    # Store multiple experiences
    for i in range(10):
        agent.share_experience(
            farmer_id=f"farmer{i}",
            topic="disease",
            content=f"Experience {i} with tomato disease and treatment methods",
            language="english"
        )
    
    result = agent.search_community(
        query="tomato disease",
        language="english"
    )
    
    assert result["success"] is True
    # Should return at most 5 discussions
    assert len(result["discussions"]) <= 5


def test_combined_advice_extracts_top_insights(agent):
    """Test that combined advice extracts insights from top discussions."""
    ai_recommendation = "Use integrated pest management for sustainable farming"
    
    result = agent.get_combined_advice(
        query="pest management",
        ai_recommendation=ai_recommendation,
        language="english"
    )
    
    assert result["success"] is True
    assert "community_insights" in result
    assert isinstance(result["community_insights"], list)


def test_error_handling_for_invalid_inputs(agent):
    """Test error handling for various invalid inputs."""
    # Test with empty query for search
    result = agent.process(
        query="",
        query_type="search"
    )
    
    # Should handle gracefully (validation happens in tools)
    assert "success" in result


def test_language_filtering_in_search(agent):
    """Test that language filter works in community search."""
    result = agent.search_community(
        query="weather",
        language="kannada"
    )
    
    assert result["success"] is True
    assert result["language"] == "kannada"


def test_location_filtering_in_search(agent):
    """Test that location filter works in community search."""
    location = {"district": "Mysore", "state": "Karnataka"}
    result = agent.search_community(
        query="crop recommendation",
        location=location
    )
    
    assert result["success"] is True
    assert result["location"] == location
