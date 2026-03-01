"""
Property-based tests for financial calculator tools.

Tests Properties 12, 13, and 23 from the design document.
"""

import pytest
from hypothesis import given, strategies as st, assume
from tools.financial_tools import (
    calculate_profit,
    estimate_costs,
    compare_crops,
    project_returns,
    CROP_COST_DATABASE
)


# Feature: missionai-farmer-agent, Property 12: Financial Calculation Accuracy
@given(
    crop=st.sampled_from(list(CROP_COST_DATABASE.keys())),
    area=st.floats(min_value=0.1, max_value=100.0),
    selling_price=st.floats(min_value=1.0, max_value=1000.0)
)
@pytest.mark.property_test
def test_financial_calculation_accuracy(crop, area, selling_price):
    """
    **Validates: Requirements 7.1**
    
    Property 12: Financial Calculation Accuracy
    For any profit calculation with crop details and selling price,
    the Finance_Calculator_Agent SHALL return a result where
    profit equals revenue minus total costs.
    """
    result = calculate_profit(crop, area, selling_price)
    
    # Extract values
    revenue = result["revenue"]["total"]
    total_costs = result["costs"]["total"]
    profit_loss = result["profit_loss"]
    
    # Verify: profit = revenue - costs (with floating point tolerance)
    assert abs(profit_loss - (revenue - total_costs)) < 0.01, \
        f"Profit calculation incorrect: {profit_loss} != {revenue} - {total_costs}"


# Feature: missionai-farmer-agent, Property 13: Cost Estimation Completeness
@given(
    crop=st.sampled_from(list(CROP_COST_DATABASE.keys())),
    area=st.floats(min_value=0.1, max_value=100.0)
)
@pytest.mark.property_test
def test_cost_estimation_completeness(crop, area):
    """
    **Validates: Requirements 7.2**
    
    Property 13: Cost Estimation Completeness
    For any crop cost estimation request, the Finance_Calculator_Agent
    SHALL include costs for seeds, fertilizers, labor, and water in the breakdown.
    """
    result = estimate_costs(crop, area)
    
    # Verify all required cost fields are present
    required_fields = ["seeds", "fertilizers", "labor", "water"]
    costs = result["costs"]
    
    for field in required_fields:
        assert field in costs, f"Missing required cost field: {field}"
        assert costs[field] >= 0, f"Cost for {field} should be non-negative"
    
    # Verify total is sum of all costs
    calculated_total = sum(costs[k] for k in costs if k != "total")
    assert abs(costs["total"] - calculated_total) < 0.01, \
        "Total cost should equal sum of individual costs"


# Feature: missionai-farmer-agent, Property 23: Input Validation for Calculations
@given(
    area=st.one_of(
        st.floats(max_value=0.0),  # Zero or negative
        st.floats(min_value=-1000.0, max_value=-0.1)  # Negative
    ),
    selling_price=st.one_of(
        st.floats(max_value=0.0),  # Zero or negative
        st.floats(min_value=-1000.0, max_value=-0.1)  # Negative
    )
)
@pytest.mark.property_test
def test_input_validation_for_calculations(area, selling_price):
    """
    **Validates: Requirements 14.3**
    
    Property 23: Input Validation for Calculations
    For any financial calculation request with invalid inputs
    (negative quantities, zero prices, missing required fields),
    the Finance_Calculator_Agent SHALL reject the request with
    a descriptive error message.
    """
    crop = "tomato"
    
    # Test invalid area
    if area <= 0:
        with pytest.raises(ValueError) as exc_info:
            calculate_profit(crop, area, 25.0)
        assert "area" in str(exc_info.value).lower() or "greater than zero" in str(exc_info.value).lower()
    
    # Test invalid selling price
    if selling_price <= 0:
        with pytest.raises(ValueError) as exc_info:
            calculate_profit(crop, 1.0, selling_price)
        assert "price" in str(exc_info.value).lower() or "greater than zero" in str(exc_info.value).lower()


# Additional unit tests for specific scenarios
def test_calculate_profit_with_custom_costs():
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
    
    result = calculate_profit("tomato", 2.0, 30.0, custom_costs)
    
    assert result["costs"]["total"] == 33000
    assert result["area_acres"] == 2.0
    assert "profit_loss" in result
    assert "roi_percentage" in result


def test_estimate_costs_unknown_crop():
    """Test cost estimation for unknown crop."""
    with pytest.raises(ValueError) as exc_info:
        estimate_costs("unknown_crop", 1.0)
    assert "not found" in str(exc_info.value).lower()


def test_compare_crops_minimum_two_crops():
    """Test that crop comparison requires at least two crops."""
    with pytest.raises(ValueError) as exc_info:
        compare_crops(["tomato"], 1.0, "kharif")
    assert "at least two" in str(exc_info.value).lower()


def test_compare_crops_valid():
    """Test valid crop comparison."""
    result = compare_crops(["tomato", "onion", "potato"], 2.0, "kharif")
    
    assert len(result) == 3
    for crop_data in result:
        assert "crop" in crop_data
        assert "estimated_profit" in crop_data
        assert "roi_percentage" in crop_data
        assert crop_data["area_acres"] == 2.0
    
    # Verify sorted by profit (descending)
    profits = [c["estimated_profit"] for c in result]
    assert profits == sorted(profits, reverse=True)


def test_project_returns_with_trends():
    """Test return projection with different market trends."""
    rising = project_returns("tomato", 1.0, "rising", "kharif")
    stable = project_returns("tomato", 1.0, "stable", "kharif")
    falling = project_returns("tomato", 1.0, "falling", "kharif")
    
    # Rising trend should have higher projected price
    assert rising["projected_price_per_kg"] > stable["projected_price_per_kg"]
    assert stable["projected_price_per_kg"] > falling["projected_price_per_kg"]
    
    # Risk levels should match trends
    assert rising["risk_level"] == "low"
    assert stable["risk_level"] == "medium"
    assert falling["risk_level"] == "high"


def test_invalid_season():
    """Test that invalid season is rejected."""
    with pytest.raises(ValueError) as exc_info:
        compare_crops(["tomato", "onion"], 1.0, "invalid_season")
    assert "season" in str(exc_info.value).lower()


def test_invalid_market_trend():
    """Test that invalid market trend is rejected."""
    with pytest.raises(ValueError) as exc_info:
        project_returns("tomato", 1.0, "invalid_trend", "kharif")
    assert "trend" in str(exc_info.value).lower()


def test_missing_cost_fields():
    """Test that missing cost fields are rejected."""
    incomplete_costs = {
        "seeds": 5000,
        "fertilizers": 8000
        # Missing other required fields
    }
    
    with pytest.raises(ValueError) as exc_info:
        calculate_profit("tomato", 1.0, 30.0, incomplete_costs)
    assert "missing" in str(exc_info.value).lower()


def test_negative_costs():
    """Test that negative costs are rejected."""
    negative_costs = {
        "seeds": -5000,
        "fertilizers": 8000,
        "pesticides": 4000,
        "labor": 10000,
        "water": 3000,
        "equipment": 2000
    }
    
    with pytest.raises(ValueError) as exc_info:
        calculate_profit("tomato", 1.0, 30.0, negative_costs)
    assert "negative" in str(exc_info.value).lower()
