"""
Tests for Disease Diagnosis Agent.

Includes property-based tests and unit tests for disease diagnosis functionality.
"""

import pytest
from hypothesis import given, strategies as st, settings
from agents.disease_diagnosis_agent import (
    DiseaseDiagnosisAgent,
    analyze_crop_image,
    get_treatment_options,
    check_image_quality
)


# Feature: missionai-farmer-agent, Property 2: Multimodal Diagnosis Completeness
@given(
    image_url=st.text(min_size=10, max_size=200),
    crop_type=st.sampled_from(['tomato', 'potato', 'chilli', 'cucumber', 'rice', 'wheat'])
)
@settings(max_examples=100)
@pytest.mark.property_test
def test_property_multimodal_diagnosis_completeness(image_url, crop_type):
    """
    Property 2: Multimodal Diagnosis Completeness
    
    For any crop image uploaded for disease diagnosis, when the Disease_Diagnosis_Agent
    completes analysis, the response SHALL include disease name, severity assessment,
    and treatment recommendations.
    
    Validates: Requirements 2.1, 2.2
    """
    # Analyze the crop image
    result = analyze_crop_image(image_url, crop_type)
    
    # If diagnosis was successful, verify completeness
    if result.get("success", False):
        # Must include disease name
        assert "disease_name" in result, "Response must include disease_name"
        assert result["disease_name"], "Disease name must not be empty"
        
        # Must include severity assessment
        assert "severity" in result, "Response must include severity"
        assert result["severity"] in ["low", "medium", "high"], \
            "Severity must be one of: low, medium, high"
        
        # Must include treatment recommendations
        assert "treatments" in result, "Response must include treatments"
        assert isinstance(result["treatments"], dict), "Treatments must be a dictionary"
        
        # Treatments must have organic and chemical options
        assert "organic" in result["treatments"], "Treatments must include organic options"
        assert "chemical" in result["treatments"], "Treatments must include chemical options"
        
        # At least one treatment option should be provided
        assert len(result["treatments"]["organic"]) > 0 or len(result["treatments"]["chemical"]) > 0, \
            "At least one treatment option must be provided"


# Unit Tests

def test_analyze_crop_image_with_valid_input():
    """Test disease diagnosis with valid crop image."""
    result = analyze_crop_image(
        image_url="s3://test-bucket/tomato_disease.jpg",
        crop_type="tomato",
        description="Brown spots on leaves"
    )
    
    assert result["success"] is True
    assert "diagnosis_id" in result
    assert "disease_name" in result
    assert "severity" in result
    assert "treatments" in result


def test_analyze_crop_image_without_crop_type():
    """Test disease diagnosis without specifying crop type."""
    result = analyze_crop_image(
        image_url="s3://test-bucket/unknown_crop.jpg"
    )
    
    # Should still attempt diagnosis
    assert "diagnosis_id" in result
    if result.get("success"):
        assert result.get("crop_type") == "unknown"


def test_get_treatment_options_for_known_disease():
    """Test getting treatment options for a known disease."""
    result = get_treatment_options("Late Blight", "high")
    
    assert result["disease"] == "Late Blight"
    assert result["severity"] == "high"
    assert "treatments" in result
    assert "organic" in result["treatments"]
    assert "chemical" in result["treatments"]
    assert len(result["treatments"]["organic"]) > 0
    assert len(result["treatments"]["chemical"]) > 0


def test_get_treatment_options_for_unknown_disease():
    """Test getting treatment options for unknown disease."""
    result = get_treatment_options("Unknown Disease", "medium")
    
    assert result["disease"] == "Unknown Disease"
    assert "message" in result
    assert result["message"] == "Disease not found in database"


def test_get_treatment_options_severity_levels():
    """Test treatment recommendations vary by severity."""
    low_severity = get_treatment_options("Late Blight", "low")
    high_severity = get_treatment_options("Late Blight", "high")
    
    assert low_severity["severity"] == "low"
    assert high_severity["severity"] == "high"
    assert low_severity["recommendation"] != high_severity["recommendation"]


def test_check_image_quality():
    """Test image quality checking."""
    result = check_image_quality("s3://test-bucket/good_image.jpg")
    
    assert "sufficient" in result
    assert "quality_score" in result
    assert "issues" in result
    assert "recommendations" in result
    assert isinstance(result["sufficient"], bool)
    assert isinstance(result["quality_score"], float)


def test_disease_diagnosis_agent_initialization():
    """Test Disease Diagnosis Agent initialization."""
    agent = DiseaseDiagnosisAgent()
    
    assert agent.name == "Disease Diagnosis Agent"
    assert agent.description is not None
    assert len(agent.tools) > 0


def test_disease_diagnosis_agent_system_prompt():
    """Test agent system prompt is properly defined."""
    agent = DiseaseDiagnosisAgent()
    prompt = agent.get_system_prompt()
    
    assert isinstance(prompt, str)
    assert len(prompt) > 100
    assert "disease" in prompt.lower()
    assert "diagnosis" in prompt.lower()


def test_disease_diagnosis_agent_process():
    """Test agent process method."""
    agent = DiseaseDiagnosisAgent()
    result = agent.process(
        image_url="s3://test-bucket/tomato_blight.jpg",
        crop_type="tomato",
        description="Dark spots on leaves"
    )
    
    assert isinstance(result, dict)
    assert "diagnosis_id" in result


def test_diagnosis_includes_all_required_fields():
    """Test that successful diagnosis includes all required fields."""
    result = analyze_crop_image(
        image_url="s3://test-bucket/crop_disease.jpg",
        crop_type="potato"
    )
    
    if result.get("success"):
        required_fields = [
            "diagnosis_id",
            "crop_type",
            "image_url",
            "disease_name",
            "confidence",
            "severity",
            "symptoms",
            "causes",
            "treatments",
            "prevention",
            "timestamp"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"


def test_treatment_options_structure():
    """Test that treatment options have correct structure."""
    result = get_treatment_options("Powdery Mildew", "medium")
    
    assert "treatments" in result
    treatments = result["treatments"]
    
    # Check organic treatments structure
    if len(treatments["organic"]) > 0:
        organic_treatment = treatments["organic"][0]
        assert "name" in organic_treatment
        assert "application" in organic_treatment
        assert "timing" in organic_treatment
    
    # Check chemical treatments structure
    if len(treatments["chemical"]) > 0:
        chemical_treatment = treatments["chemical"][0]
        assert "name" in chemical_treatment
        assert "application" in chemical_treatment
        assert "timing" in chemical_treatment


# Edge Case Tests (Requirement 2.3)

def test_poor_image_quality_handling():
    """
    Test handling of poor image quality.
    
    Validates: Requirement 2.3 - Poor image quality handling
    """
    # Mock a scenario where image quality is insufficient
    # In production, this would be detected by actual image analysis
    
    # Test with various image URLs that might indicate poor quality
    result = analyze_crop_image(
        image_url="s3://test-bucket/blurry_image.jpg",
        crop_type="tomato"
    )
    
    # The system should handle this gracefully
    assert "diagnosis_id" in result
    
    # If quality check fails, should provide guidance
    if not result.get("success"):
        assert "quality_issues" in result or "recommendations" in result or "message" in result


def test_image_quality_insufficient_provides_recommendations():
    """Test that insufficient image quality provides clear recommendations."""
    # Simulate poor quality check
    quality_result = check_image_quality("s3://test-bucket/poor_quality.jpg")
    
    # Should always provide recommendations
    assert "recommendations" in quality_result
    assert isinstance(quality_result["recommendations"], list)
    assert len(quality_result["recommendations"]) > 0


def test_unsupported_crop_type_handling():
    """
    Test handling of unsupported crop types.
    
    Validates: Requirement 2.3 - Unsupported crop types
    """
    # Test with a crop type that might not be in the database
    unsupported_crops = ["dragon_fruit", "kiwi", "avocado", "exotic_berry"]
    
    for crop in unsupported_crops:
        result = analyze_crop_image(
            image_url="s3://test-bucket/unknown_crop.jpg",
            crop_type=crop
        )
        
        # Should handle gracefully without crashing
        assert "diagnosis_id" in result
        assert isinstance(result, dict)
        
        # Should either succeed with generic diagnosis or provide helpful message
        if not result.get("success"):
            assert "message" in result or "error" in result


def test_empty_image_url_handling():
    """Test handling of empty or invalid image URL."""
    # Test with empty URL
    result = analyze_crop_image(image_url="", crop_type="tomato")
    
    # Should handle gracefully
    assert isinstance(result, dict)
    assert "diagnosis_id" in result


def test_missing_crop_type_still_processes():
    """Test that diagnosis works even without crop type specified."""
    result = analyze_crop_image(
        image_url="s3://test-bucket/disease_image.jpg",
        crop_type=None
    )
    
    # Should still attempt diagnosis
    assert isinstance(result, dict)
    assert "diagnosis_id" in result


def test_diagnosis_with_farmer_description():
    """Test that farmer's description is accepted and processed."""
    result = analyze_crop_image(
        image_url="s3://test-bucket/crop.jpg",
        crop_type="potato",
        description="Leaves are turning yellow and have brown spots"
    )
    
    # Should process successfully with description
    assert isinstance(result, dict)
    assert "diagnosis_id" in result


def test_diagnosis_handles_various_image_formats():
    """Test that various image URL formats are handled."""
    image_urls = [
        "s3://bucket/image.jpg",
        "https://example.com/image.png",
        "/local/path/image.jpeg",
        "image.jpg"
    ]
    
    for url in image_urls:
        result = analyze_crop_image(image_url=url, crop_type="tomato")
        
        # Should handle all formats without crashing
        assert isinstance(result, dict)
        assert "diagnosis_id" in result


def test_confidence_score_in_valid_range():
    """Test that confidence scores are in valid range [0, 1]."""
    result = analyze_crop_image(
        image_url="s3://test-bucket/crop.jpg",
        crop_type="tomato"
    )
    
    if result.get("success") and "confidence" in result:
        confidence = result["confidence"]
        assert 0.0 <= confidence <= 1.0, "Confidence must be between 0 and 1"


def test_severity_levels_are_valid():
    """Test that severity levels are always valid values."""
    result = analyze_crop_image(
        image_url="s3://test-bucket/crop.jpg",
        crop_type="chilli"
    )
    
    if result.get("success") and "severity" in result:
        severity = result["severity"]
        assert severity in ["low", "medium", "high"], \
            f"Severity must be low, medium, or high, got: {severity}"


def test_treatment_recommendations_not_empty():
    """Test that treatment recommendations are never completely empty."""
    result = analyze_crop_image(
        image_url="s3://test-bucket/diseased_crop.jpg",
        crop_type="potato"
    )
    
    if result.get("success") and "treatments" in result:
        treatments = result["treatments"]
        organic = treatments.get("organic", [])
        chemical = treatments.get("chemical", [])
        
        # At least one type of treatment should be available
        assert len(organic) > 0 or len(chemical) > 0, \
            "At least one treatment option must be provided"
