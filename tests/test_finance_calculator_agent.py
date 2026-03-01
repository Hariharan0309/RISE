"""
Tests for Finance Calculator Agent.
"""

import pytest
from agents.finance_calculator_agent import FinanceCalculatorAgent


@pytest.fixture
def finance_agent():
    """Create a Finance Calculator Agent instance."""
    return FinanceCalculatorAgent()


def test_finance_calculator_agent_initialization(finance_agent):
    """Test that Finance Calculator Agent initializes correctly."""
    assert finance_agent.name == "Finance Calculator Agent"
    assert finance_agent.description == "Specialized in financial planning and profitability analysis"
    assert len(finance_agent.tools) == 4


def test_get_system_prompt(finance_agent):
    """Test that system prompt is comprehensive."""
    prompt = finance_agent.get_system_prompt()
    
    assert "financial" in prompt.lower()
    assert "profit" in prompt.lower()
    assert "cost" in prompt.lower()
    assert "roi" in prompt.lower()


def test_calculate_profit_basic(finance_agent):
    """Test basic profit calculation for a crop."""
    result = finance_agent.calculate_crop_profit(
        crop="tomato",
        area=2.0,
        selling_price=30.0
    )
    
    assert result["success"] is True
    assert result["query_type"] == "profit"
    assert "calculation" in result
    assert "insights" in result
    
    calc = result["calculation"]
    assert calc["crop"] == "tomato"
    assert calc["area_acres"] == 2.0
    assert calc["revenue"]["price_per_kg"] == 30.0
    assert "profit_loss" in calc
    assert "roi_percentage" in calc
    assert "break_even_price" in calc


def test_calculate_profit_with_custom_costs(finance_agent):
    """Test profit calculation with custom cost breakdown."""
    custom_costs = {
        "seeds": 5000,
        "fertilizers": 8000,
        "pesticides": 4000,
        "labor": 10000,
        "water": 3000,
        "equipment": 2000,
        "other": 1000
    }
    
    result = finance_agent.calculate_crop_profit(
        crop="onion",
        area=3.0,
        selling_price=22.0,
        costs=custom_costs
    )
    
    assert result["success"] is True
    calc = result["calculation"]
    assert calc["costs"]["total"] == 33000


def test_estimate_costs(finance_agent):
    """Test cost estimation for a crop."""
    result = finance_agent.estimate_cultivation_costs(
        crop="rice",
        area=5.0
    )
    
    assert result["success"] is True
    assert result["query_type"] == "costs"
    assert "estimation" in result
    assert "suggestions" in result
    
    estimation = result["estimation"]
    assert estimation["crop"] == "rice"
    assert estimation["area_acres"] == 5.0
    assert "costs" in estimation
    assert estimation["costs"]["total"] > 0
    assert "cost_per_acre" in estimation


def test_compare_crops(finance_agent):
    """Test comparing multiple crop options."""
    result = finance_agent.compare_crop_options(
        crop_options=["tomato", "onion", "potato"],
        area=2.0,
        season="kharif"
    )
    
    assert result["success"] is True
    assert result["query_type"] == "compare"
    assert "comparison" in result
    assert "analysis" in result
    
    comparison = result["comparison"]
    assert len(comparison) == 3
    
    # Check that each crop has required fields
    for crop_data in comparison:
        assert "crop" in crop_data
        assert "total_cost" in crop_data
        assert "expected_yield_kg" in crop_data
        assert "estimated_profit" in crop_data
        assert "roi_percentage" in crop_data
    
    # Results should be sorted by profit (descending)
    profits = [c["estimated_profit"] for c in comparison]
    assert profits == sorted(profits, reverse=True)


def test_project_returns(finance_agent):
    """Test return projection with market trends."""
    result = finance_agent.project_crop_returns(
        crop="wheat",
        area=4.0,
        market_trend="rising",
        season="rabi"
    )
    
    assert result["success"] is True
    assert result["query_type"] == "project"
    assert "projection" in result
    assert "insights" in result
    
    projection = result["projection"]
    assert projection["crop"] == "wheat"
    assert projection["market_trend"] == "rising"
    assert projection["season"] == "rabi"
    assert "projected_profit" in projection
    assert "risk_level" in projection
    assert "price_change_percentage" in projection


def test_profit_insights_generation(finance_agent):
    """Test that profit insights are generated correctly."""
    result = finance_agent.calculate_crop_profit(
        crop="tomato",
        area=2.0,
        selling_price=30.0
    )
    
    insights = result["insights"]
    assert "profitability" in insights
    assert "roi_assessment" in insights
    assert "price_margin" in insights
    assert "recommendations" in insights
    assert len(insights["recommendations"]) > 0


def test_cost_suggestions_generation(finance_agent):
    """Test that cost optimization suggestions are generated."""
    result = finance_agent.estimate_cultivation_costs(
        crop="cotton",
        area=3.0
    )
    
    suggestions = result["suggestions"]
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0
    # Should include suggestion about government schemes
    assert any("scheme" in s.lower() for s in suggestions)


def test_comparative_analysis_generation(finance_agent):
    """Test that comparative analysis is generated for crop comparison."""
    result = finance_agent.compare_crop_options(
        crop_options=["rice", "wheat"],
        area=3.0,
        season="rabi"
    )
    
    analysis = result["analysis"]
    assert "total_crops_compared" in analysis
    assert "best_by_profit" in analysis
    assert "best_by_roi" in analysis
    assert "recommended" in analysis
    assert "recommendation" in analysis


def test_projection_insights_generation(finance_agent):
    """Test that projection insights are generated."""
    result = finance_agent.project_crop_returns(
        crop="chilli",
        area=2.0,
        market_trend="falling",
        season="kharif"
    )
    
    insights = result["insights"]
    assert "market_outlook" in insights
    assert "risk_assessment" in insights
    assert "recommendations" in insights
    assert len(insights["recommendations"]) > 0


def test_missing_required_fields_profit(finance_agent):
    """Test error handling for missing required fields in profit calculation."""
    result = finance_agent.process(
        query_type="profit",
        crop="tomato",
        area=2.0
        # Missing selling_price
    )
    
    assert result["success"] is False
    assert "error" in result


def test_missing_required_fields_compare(finance_agent):
    """Test error handling for missing required fields in comparison."""
    result = finance_agent.process(
        query_type="compare",
        crop_options=["tomato", "onion"],
        area=2.0
        # Missing season
    )
    
    assert result["success"] is False
    assert "error" in result


def test_invalid_query_type(finance_agent):
    """Test handling of invalid query type."""
    result = finance_agent.process(query_type="invalid_type")
    
    assert result["success"] is False
    assert "error" in result
    assert "Unknown query type" in result["error"]


def test_roi_assessment(finance_agent):
    """Test ROI assessment categorization."""
    assert finance_agent._assess_roi(150) == "excellent"
    assert finance_agent._assess_roi(75) == "good"
    assert finance_agent._assess_roi(35) == "moderate"
    assert finance_agent._assess_roi(10) == "low"
    assert finance_agent._assess_roi(-5) == "negative"


def test_market_trend_assessment(finance_agent):
    """Test market trend assessment."""
    assert finance_agent._assess_market_trend("rising") == "positive"
    assert finance_agent._assess_market_trend("stable") == "neutral"
    assert finance_agent._assess_market_trend("falling") == "negative"


def test_risk_assessment(finance_agent):
    """Test risk level assessment."""
    low_risk = finance_agent._assess_risk("low")
    assert "Low risk" in low_risk
    
    medium_risk = finance_agent._assess_risk("medium")
    assert "Moderate risk" in medium_risk
    
    high_risk = finance_agent._assess_risk("high")
    assert "High risk" in high_risk


def test_compare_single_crop_error(finance_agent):
    """Test that comparison requires at least 2 crops."""
    result = finance_agent.compare_crop_options(
        crop_options=["tomato"],
        area=2.0,
        season="kharif"
    )
    
    assert result["success"] is False
    assert "error" in result


def test_projection_with_different_trends(finance_agent):
    """Test projections with different market trends."""
    # Rising trend
    rising_result = finance_agent.project_crop_returns(
        crop="tomato",
        area=2.0,
        market_trend="rising",
        season="kharif"
    )
    
    # Falling trend
    falling_result = finance_agent.project_crop_returns(
        crop="tomato",
        area=2.0,
        market_trend="falling",
        season="kharif"
    )
    
    # Stable trend
    stable_result = finance_agent.project_crop_returns(
        crop="tomato",
        area=2.0,
        market_trend="stable",
        season="kharif"
    )
    
    assert rising_result["success"] is True
    assert falling_result["success"] is True
    assert stable_result["success"] is True
    
    # Rising should have highest projected profit
    rising_profit = rising_result["projection"]["projected_profit"]
    falling_profit = falling_result["projection"]["projected_profit"]
    stable_profit = stable_result["projection"]["projected_profit"]
    
    assert rising_profit > stable_profit > falling_profit


def test_get_tools(finance_agent):
    """Test that agent returns its tools."""
    tools = finance_agent.get_tools()
    assert len(tools) == 4
