"""
Tests for Soil Analysis Agent.

Includes property-based tests and unit tests for soil analysis functionality.
"""

import pytest
from hypothesis import given, strategies as st, settings
from agents.soil_analysis_agent import (
    SoilAnalysisAgent,
    classify_soil,
    assess_fertility,
    recommend_crops,
    get_soil_improvement_tips
)


# Feature: missionai-farmer-agent, Property 3: Soil Analysis Output Completeness
@given(
    description=st.text(min_size=10, max_size=200),
    season=st.sampled_from(['kharif', 'rabi', 'summer'])
)
@settings(max_examples=100)
@pytest.mark.property_test
def test_property_soil_analysis_output_completeness(description, season):
    """
    Property 3: Soil Analysis Output Completeness
    
    For any soil analysis request (image or description), when the Soil_Analysis_Agent
    completes analysis, the response SHALL include soil type classification, fertility
    assessment, and crop recommendations.
    
    Validates: Requirements 3.1, 3.2, 3.3, 3.4
    """
    # Create agent and process soil analysis
    agent = SoilAnalysisAgent()
    result = agent.process(description=description, season=season)
    
    # If analysis was successful, verify completeness
    if result.get("success", False):
        # Requirement 3.1: Must include soil type classification
        assert "soil_type" in result, "Response must include soil_type"
        assert result["soil_type"], "Soil type must not be empty"
        
        # Requirement 3.2: Must include fertility assessment
        assert "fertility" in result, "Response must include fertility assessment"
        assert result["fertility"] in ["low", "medium", "high"], \
            "Fertility must be one of: low, medium, high"
        
        # Must include pH level as part of fertility assessment
        assert "ph_level" in result, "Response must include ph_level"
        assert isinstance(result["ph_level"], (int, float)), "pH level must be numeric"
        
        # Must include nutrient status
        assert "nutrients" in result, "Response must include nutrients"
        assert isinstance(result["nutrients"], dict), "Nutrients must be a dictionary"
        
        # Nutrients should include key elements
        nutrients = result["nutrients"]
        required_nutrients = ["nitrogen", "phosphorus", "potassium", "organic_matter"]
        for nutrient in required_nutrients:
            assert nutrient in nutrients, f"Nutrients must include {nutrient}"
        
        # Requirement 3.3: Must include crop recommendations
        assert "recommended_crops" in result, "Response must include recommended_crops"
        assert isinstance(result["recommended_crops"], list), \
            "Recommended crops must be a list"
        assert len(result["recommended_crops"]) > 0, \
            "At least one crop recommendation must be provided"
        
        # Requirement 3.4: Crop recommendations must include expected yield and care requirements
        for crop_rec in result["recommended_crops"]:
            assert "crop" in crop_rec, "Crop recommendation must include crop name"
            assert "expected_yield" in crop_rec, \
                "Crop recommendation must include expected_yield"
            assert "care_requirements" in crop_rec, \
                "Crop recommendation must include care_requirements"
            assert isinstance(crop_rec["care_requirements"], list), \
                "Care requirements must be a list"


# Unit Tests

def test_classify_soil_with_description():
    """Test soil classification with text description."""
    result = classify_soil(description="The soil is sticky and forms clumps when wet")
    
    assert result["success"] is True
    assert "soil_type" in result
    assert "confidence" in result
    assert "characteristics" in result


def test_classify_soil_clay_detection():
    """Test that clay soil is correctly detected from description."""
    result = classify_soil(description="sticky clay soil that is heavy")
    
    assert result["success"] is True
    assert result["soil_type"] == "clay"


def test_classify_soil_sandy_detection():
    """Test that sandy soil is correctly detected from description."""
    result = classify_soil(description="gritty sandy soil that drains quickly")
    
    assert result["success"] is True
    assert result["soil_type"] == "sandy"


def test_classify_soil_laterite_detection():
    """Test that laterite soil is correctly detected from description."""
    result = classify_soil(description="red laterite soil common in tropical areas")
    
    assert result["success"] is True
    assert result["soil_type"] == "laterite"


def test_assess_fertility_for_loam():
    """Test fertility assessment for loam soil."""
    result = assess_fertility("loam")
    
    assert result["success"] is True
    assert result["fertility"] == "high"
    assert "nutrients" in result
    assert "ph_level" in result


def test_assess_fertility_for_sandy():
    """Test fertility assessment for sandy soil."""
    result = assess_fertility("sandy")
    
    assert result["success"] is True
    assert result["fertility"] == "low"


def test_assess_fertility_with_indicators():
    """Test fertility assessment with pH indicators."""
    result = assess_fertility("clay", indicators={"ph": 5.0})
    
    assert result["success"] is True
    assert result["ph_level"] == 5.0
    # Low pH should affect fertility
    assert result["fertility"] == "low"


def test_recommend_crops_for_loam():
    """Test crop recommendations for loam soil."""
    result = recommend_crops("loam", "kharif")
    
    assert isinstance(result, list)
    assert len(result) > 0
    
    # Check structure of recommendations
    for crop in result:
        assert "crop" in crop
        assert "suitability" in crop
        assert "expected_yield" in crop
        assert "care_requirements" in crop


def test_recommend_crops_for_clay():
    """Test crop recommendations for clay soil."""
    result = recommend_crops("clay", "rabi")
    
    assert isinstance(result, list)
    assert len(result) > 0
    
    # Clay soil should recommend rice, wheat, etc.
    crop_names = [c["crop"] for c in result]
    assert any(crop in crop_names for crop in ["rice", "wheat", "sugarcane", "cotton"])


def test_recommend_crops_for_sandy():
    """Test crop recommendations for sandy soil."""
    result = recommend_crops("sandy", "summer")
    
    assert isinstance(result, list)
    assert len(result) > 0
    
    # Sandy soil should recommend groundnut, millet, etc.
    crop_names = [c["crop"] for c in result]
    assert any(crop in crop_names for crop in ["groundnut", "watermelon", "millet"])


def test_recommend_crops_seasonal_variation():
    """Test that crop recommendations vary by season."""
    kharif_crops = recommend_crops("loam", "kharif")
    rabi_crops = recommend_crops("loam", "rabi")
    
    # Both should have recommendations
    assert len(kharif_crops) > 0
    assert len(rabi_crops) > 0
    
    # Expected yields should differ by season
    kharif_yields = [c["expected_yield"] for c in kharif_crops]
    rabi_yields = [c["expected_yield"] for c in rabi_crops]
    assert kharif_yields != rabi_yields


def test_get_soil_improvement_tips_for_clay():
    """Test improvement tips for clay soil."""
    result = get_soil_improvement_tips("clay")
    
    assert isinstance(result, list)
    assert len(result) > 0
    
    # Should mention drainage improvement
    tips_text = " ".join(result).lower()
    assert "drainage" in tips_text or "organic" in tips_text


def test_get_soil_improvement_tips_for_sandy():
    """Test improvement tips for sandy soil."""
    result = get_soil_improvement_tips("sandy")
    
    assert isinstance(result, list)
    assert len(result) > 0
    
    # Should mention water retention
    tips_text = " ".join(result).lower()
    assert "water" in tips_text or "organic" in tips_text or "compost" in tips_text


def test_get_soil_improvement_tips_with_deficiencies():
    """Test improvement tips with specific nutrient deficiencies."""
    result = get_soil_improvement_tips("loam", deficiencies=["nitrogen", "phosphorus"])
    
    assert isinstance(result, list)
    assert len(result) > 0
    
    # Should address the deficiencies
    tips_text = " ".join(result).lower()
    assert "nitrogen" in tips_text or "phosphorus" in tips_text


def test_soil_analysis_agent_initialization():
    """Test Soil Analysis Agent initialization."""
    agent = SoilAnalysisAgent()
    
    assert agent.name == "Soil Analysis Agent"
    assert agent.description is not None
    assert len(agent.tools) > 0


def test_soil_analysis_agent_system_prompt():
    """Test agent system prompt is properly defined."""
    agent = SoilAnalysisAgent()
    prompt = agent.get_system_prompt()
    
    assert isinstance(prompt, str)
    assert len(prompt) > 100
    assert "soil" in prompt.lower()
    assert "crop" in prompt.lower()


def test_soil_analysis_agent_process():
    """Test agent process method with complete workflow."""
    agent = SoilAnalysisAgent()
    result = agent.process(
        description="loamy soil with good drainage",
        season="kharif"
    )
    
    assert isinstance(result, dict)
    assert result.get("success") is True
    assert "analysis_id" in result
    assert "soil_type" in result
    assert "fertility" in result
    assert "recommended_crops" in result


def test_soil_analysis_includes_all_required_fields():
    """Test that successful analysis includes all required fields."""
    agent = SoilAnalysisAgent()
    result = agent.process(
        description="clay soil",
        season="rabi"
    )
    
    if result.get("success"):
        required_fields = [
            "analysis_id",
            "soil_type",
            "fertility",
            "ph_level",
            "nutrients",
            "recommended_crops",
            "improvement_tips",
            "timestamp"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"


def test_crop_recommendations_have_suitability():
    """Test that crop recommendations include suitability ratings."""
    result = recommend_crops("loam", "kharif")
    
    for crop in result:
        assert "suitability" in crop
        assert crop["suitability"] in ["highly_suitable", "moderately_suitable"]


def test_crop_recommendations_sorted_by_suitability():
    """Test that highly suitable crops appear first."""
    result = recommend_crops("clay", "kharif")
    
    if len(result) > 1:
        # First crop should be highly suitable if any exist
        highly_suitable_exists = any(c["suitability"] == "highly_suitable" for c in result)
        if highly_suitable_exists:
            assert result[0]["suitability"] == "highly_suitable"


def test_fertility_assessment_includes_recommendations():
    """Test that fertility assessment includes improvement recommendations."""
    result = assess_fertility("sandy")
    
    assert "recommendations" in result
    assert isinstance(result["recommendations"], list)
    assert len(result["recommendations"]) > 0


def test_ph_level_in_valid_range():
    """Test that pH levels are in valid range."""
    result = assess_fertility("loam")
    
    if result.get("success") and "ph_level" in result:
        ph = result["ph_level"]
        assert 3.0 <= ph <= 10.0, "pH level should be in realistic range"


def test_nutrients_have_valid_status():
    """Test that nutrient status values are valid."""
    result = assess_fertility("clay")
    
    if result.get("success") and "nutrients" in result:
        nutrients = result["nutrients"]
        valid_statuses = ["deficient", "adequate", "excess", "low", "medium", "high"]
        
        for nutrient, status in nutrients.items():
            assert status in valid_statuses, \
                f"Nutrient status must be valid, got: {status}"


def test_empty_description_handled_gracefully():
    """Test that empty description is handled gracefully."""
    result = classify_soil(description="")
    
    # Should still return a result (default to loam or similar)
    assert isinstance(result, dict)
    assert "soil_type" in result


def test_unknown_soil_type_in_fertility():
    """Test fertility assessment with unknown soil type."""
    result = assess_fertility("unknown_soil_type")
    
    # Should handle gracefully with default
    assert isinstance(result, dict)
    if result.get("success"):
        assert "fertility" in result


def test_unknown_soil_type_in_crop_recommendations():
    """Test crop recommendations with unknown soil type."""
    result = recommend_crops("unknown_soil_type", "kharif")
    
    # Should return empty list or handle gracefully
    assert isinstance(result, list)


def test_invalid_season_handled():
    """Test that invalid season is handled gracefully."""
    result = recommend_crops("loam", "invalid_season")
    
    # Should still return recommendations
    assert isinstance(result, list)


def test_care_requirements_not_empty():
    """Test that care requirements are provided for crops."""
    result = recommend_crops("clay", "kharif")
    
    for crop in result:
        care_reqs = crop.get("care_requirements", [])
        assert isinstance(care_reqs, list)
        # Most crops should have at least some care requirements
        if crop["crop"] in ["rice", "wheat", "tomato", "potato"]:
            assert len(care_reqs) > 0


def test_expected_yield_format():
    """Test that expected yield has proper format."""
    result = recommend_crops("loam", "rabi")
    
    for crop in result:
        expected_yield = crop.get("expected_yield", "")
        # Should contain numeric value and unit
        assert "kg" in expected_yield.lower() or "acre" in expected_yield.lower()


def test_improvement_tips_for_all_soil_types():
    """Test that improvement tips are available for all soil types."""
    soil_types = ["clay", "loam", "sandy", "silt", "laterite"]
    
    for soil_type in soil_types:
        result = get_soil_improvement_tips(soil_type)
        assert isinstance(result, list)
        assert len(result) > 0, f"No improvement tips for {soil_type}"


def test_soil_classification_confidence_in_range():
    """Test that classification confidence is in valid range."""
    result = classify_soil(description="sandy soil")
    
    if result.get("success") and "confidence" in result:
        confidence = result["confidence"]
        assert 0.0 <= confidence <= 1.0, "Confidence must be between 0 and 1"


def test_soil_characteristics_provided():
    """Test that soil characteristics are provided in classification."""
    result = classify_soil(description="clay soil")
    
    if result.get("success"):
        assert "characteristics" in result
        assert isinstance(result["characteristics"], list)
        assert len(result["characteristics"]) > 0
