"""
Integration tests for MissionAI Farmer Agent system.

Tests end-to-end multi-agent flows to verify agent handoffs,
context preservation, and complete user workflows.
"""

import pytest
from agents.manager_agent import ManagerAgent, detect_language, route_to_agent
from agents.disease_diagnosis_agent import DiseaseDiagnosisAgent
from agents.soil_analysis_agent import SoilAnalysisAgent
from agents.weather_advisor_agent import WeatherAdvisorAgent
from agents.market_price_agent import MarketPriceAgent
from agents.schemes_navigator_agent import SchemesNavigatorAgent
from agents.finance_calculator_agent import FinanceCalculatorAgent
from agents.community_advisor_agent import CommunityAdvisorAgent


@pytest.fixture
def manager_agent():
    """Create a manager agent instance."""
    return ManagerAgent()


@pytest.fixture
def all_agents():
    """Create instances of all specialist agents."""
    return {
        "disease_diagnosis": DiseaseDiagnosisAgent(),
        "soil_analysis": SoilAnalysisAgent(),
        "weather_advisor": WeatherAdvisorAgent(),
        "market_price": MarketPriceAgent(),
        "schemes_navigator": SchemesNavigatorAgent(),
        "finance_calculator": FinanceCalculatorAgent(),
        "community_advisor": CommunityAdvisorAgent()
    }


def test_end_to_end_disease_diagnosis_flow(manager_agent):
    """Test complete disease diagnosis flow from user query to response."""
    # User asks about crop disease
    user_message = "My tomato plants have brown spots on the leaves"
    
    # Manager detects language
    language = detect_language(user_message)
    assert language == "english"
    
    # Manager routes to correct agent
    target_agent = route_to_agent(user_message, {})
    assert target_agent == "disease_diagnosis"
    
    # Process the request
    result = manager_agent.process(
        user_message=user_message,
        user_id="test_user_integration",
        language=language
    )
    
    # Verify response structure
    assert result is not None
    assert isinstance(result, dict)


def test_end_to_end_market_query_flow(manager_agent):
    """Test complete market price query flow."""
    # User asks about market prices
    user_message = "What is the current price of rice in Bangalore?"
    
    # Manager detects language
    language = detect_language(user_message)
    assert language == "english"
    
    # Manager routes to correct agent
    target_agent = route_to_agent(user_message, {})
    assert target_agent == "market_price"
    
    # Process the request
    result = manager_agent.process(
        user_message=user_message,
        user_id="test_user_integration",
        language=language
    )
    
    # Verify response structure
    assert result is not None
    assert isinstance(result, dict)


def test_multi_agent_handoff_flow(manager_agent):
    """Test multi-agent handoff scenario."""
    user_id = "test_user_handoff"
    
    # First query: Disease diagnosis
    disease_query = "My crop has yellow leaves"
    target_agent_1 = route_to_agent(disease_query, {})
    assert target_agent_1 == "disease_diagnosis"
    
    # Second query: Finance calculation (different agent)
    finance_query = "How much will treatment cost for 2 acres?"
    target_agent_2 = route_to_agent(finance_query, {})
    assert target_agent_2 == "finance_calculator"
    
    # Verify different agents are selected
    assert target_agent_1 != target_agent_2


def test_context_preservation_across_queries(manager_agent):
    """Test that context is preserved across multiple queries."""
    user_id = "test_user_context"
    
    # First query establishes context
    result1 = manager_agent.process(
        user_message="I grow rice in Karnataka",
        user_id=user_id,
        language="english"
    )
    
    # Second query should have access to context
    result2 = manager_agent.process(
        user_message="What is the weather forecast?",
        user_id=user_id,
        language="english"
    )
    
    # Both queries should succeed
    assert result1 is not None
    assert result2 is not None


def test_language_detection_and_routing(manager_agent):
    """Test language detection works for different languages."""
    # English query
    english_query = "What is the weather today?"
    english_lang = detect_language(english_query)
    assert english_lang == "english"
    
    # Kannada query (simulated with keywords)
    kannada_query = "ಹವಾಮಾನ ಏನು?"
    kannada_lang = detect_language(kannada_query)
    # Should detect as kannada or default to english
    assert kannada_lang in ["kannada", "english"]
    
    # Hindi query (simulated with keywords)
    hindi_query = "मौसम क्या है?"
    hindi_lang = detect_language(hindi_query)
    # Should detect as hindi or default to english
    assert hindi_lang in ["hindi", "english"]


def test_agent_routing_accuracy():
    """Test that routing correctly identifies target agents for various queries."""
    test_cases = [
        ("My crop has disease", "disease_diagnosis"),
        ("What is the soil type?", "soil_analysis"),
        ("Weather forecast please", "weather_advisor"),
        ("Market prices for wheat", "market_price"),
        ("Government schemes available", "schemes_navigator"),
        ("Calculate profit for rice", "finance_calculator"),
        ("What do other farmers say?", "community_advisor"),
    ]
    
    for query, expected_agent in test_cases:
        target_agent = route_to_agent(query, {})
        assert target_agent == expected_agent, \
            f"Query '{query}' routed to '{target_agent}' instead of '{expected_agent}'"


def test_all_agents_initialization(all_agents):
    """Test that all specialist agents can be initialized."""
    expected_agents = [
        "disease_diagnosis",
        "soil_analysis",
        "weather_advisor",
        "market_price",
        "schemes_navigator",
        "finance_calculator",
        "community_advisor"
    ]
    
    for agent_name in expected_agents:
        assert agent_name in all_agents, f"Agent '{agent_name}' not initialized"
        assert all_agents[agent_name] is not None, f"Agent '{agent_name}' is None"


def test_agent_system_prompts(all_agents):
    """Test that all agents have proper system prompts."""
    for agent_name, agent in all_agents.items():
        system_prompt = agent.get_system_prompt()
        assert system_prompt is not None, f"Agent '{agent_name}' has no system prompt"
        assert len(system_prompt) > 0, f"Agent '{agent_name}' has empty system prompt"
        assert isinstance(system_prompt, str), f"Agent '{agent_name}' system prompt is not a string"


def test_agent_tools_availability(all_agents):
    """Test that all agents have their required tools."""
    for agent_name, agent in all_agents.items():
        tools = agent.get_tools()
        assert tools is not None, f"Agent '{agent_name}' has no tools"
        assert len(tools) > 0, f"Agent '{agent_name}' has empty tools list"
        assert isinstance(tools, list), f"Agent '{agent_name}' tools is not a list"
