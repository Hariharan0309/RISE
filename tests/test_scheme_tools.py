"""
Property-based tests for government scheme navigator tools.

Tests Properties 10 and 11 from the design document.
"""

import pytest
from hypothesis import given, strategies as st, assume
from tools.scheme_tools import (
    list_schemes,
    get_scheme_details,
    check_eligibility,
    get_application_steps,
    load_schemes
)


# Get available scheme IDs for testing
def get_available_scheme_ids():
    """Get list of available scheme IDs from data."""
    schemes = load_schemes()
    return [s["scheme_id"] for s in schemes] if schemes else ["pm-kisan"]


# Feature: missionai-farmer-agent, Property 10: Scheme Information Completeness
@given(
    scheme_id=st.sampled_from(get_available_scheme_ids())
)
@pytest.mark.property_test
def test_scheme_information_completeness(scheme_id):
    """
    **Validates: Requirements 6.2**
    
    Property 10: Scheme Information Completeness
    For any government scheme query, when the Schemes_Navigator_Agent
    provides scheme details, the response SHALL include benefits,
    eligibility criteria, and application process.
    """
    result = get_scheme_details(scheme_id)
    
    # Verify all required fields are present
    assert "benefits" in result, "Scheme details must include benefits"
    assert isinstance(result["benefits"], list), "Benefits must be a list"
    assert len(result["benefits"]) > 0, "Benefits list must not be empty"
    
    assert "eligibility_criteria" in result, "Scheme details must include eligibility criteria"
    assert isinstance(result["eligibility_criteria"], dict), "Eligibility criteria must be a dict"
    
    assert "application_process" in result, "Scheme details must include application process"
    assert isinstance(result["application_process"], list), "Application process must be a list"
    assert len(result["application_process"]) > 0, "Application process must not be empty"


# Feature: missionai-farmer-agent, Property 11: Eligibility Determination Accuracy
@given(
    scheme_id=st.sampled_from(get_available_scheme_ids()),
    land_size=st.floats(min_value=0.1, max_value=100.0),
    income=st.floats(min_value=10000.0, max_value=5000000.0)
)
@pytest.mark.property_test
def test_eligibility_determination_accuracy(scheme_id, land_size, income):
    """
    **Validates: Requirements 6.3**
    
    Property 11: Eligibility Determination Accuracy
    For any farmer profile and scheme combination, the Schemes_Navigator_Agent
    SHALL produce consistent eligibility results when given the same input parameters.
    """
    # Create farmer profile
    farmer_profile = {
        "farm": {
            "size_acres": land_size,
            "current_crops": ["rice", "wheat"]
        },
        "income": income
    }
    
    # Check eligibility twice with same inputs
    result1 = check_eligibility(scheme_id, farmer_profile)
    result2 = check_eligibility(scheme_id, farmer_profile)
    
    # Verify consistency
    assert result1["eligible"] == result2["eligible"], \
        "Eligibility determination must be consistent for same inputs"
    
    # Verify result structure
    assert "scheme_id" in result1
    assert "eligible" in result1
    assert isinstance(result1["eligible"], bool)
    assert "reasons" in result1
    assert isinstance(result1["reasons"], list)


# Additional unit tests
def test_list_schemes_no_filter():
    """Test listing all schemes without filters."""
    results = list_schemes()
    
    assert isinstance(results, list)
    if len(results) > 0:
        for scheme in results:
            assert "scheme_id" in scheme
            assert "name" in scheme
            assert "category" in scheme
            assert "description" in scheme


def test_list_schemes_with_category():
    """Test listing schemes with category filter."""
    results = list_schemes(category="subsidy")
    
    assert isinstance(results, list)
    for scheme in results:
        assert scheme["category"] == "subsidy"


def test_list_schemes_with_state():
    """Test listing schemes with state filter."""
    results = list_schemes(state="Karnataka")
    
    assert isinstance(results, list)
    # Should include central schemes (state="all") and Karnataka schemes
    for scheme in results:
        assert scheme["level"] == "central" or scheme["state"] == "Karnataka"


def test_list_schemes_invalid_category():
    """Test that invalid category raises error."""
    with pytest.raises(ValueError) as exc_info:
        list_schemes(category="invalid_category")
    assert "category" in str(exc_info.value).lower()


def test_get_scheme_details_not_found():
    """Test getting details for non-existent scheme."""
    with pytest.raises(ValueError) as exc_info:
        get_scheme_details("non_existent_scheme")
    assert "not found" in str(exc_info.value).lower()


def test_get_scheme_details_valid():
    """Test getting details for valid scheme."""
    schemes = load_schemes()
    if len(schemes) > 0:
        scheme_id = schemes[0]["scheme_id"]
        result = get_scheme_details(scheme_id)
        
        assert result["scheme_id"] == scheme_id
        assert "name" in result
        assert "benefits" in result
        assert "eligibility_criteria" in result
        assert "application_process" in result
        assert "documents_required" in result


def test_check_eligibility_land_size():
    """Test eligibility checking based on land size."""
    schemes = load_schemes()
    if len(schemes) > 0:
        scheme_id = schemes[0]["scheme_id"]
        
        # Test with very small land
        small_profile = {
            "farm": {"size_acres": 0.1, "current_crops": ["rice"]},
            "income": 50000
        }
        result_small = check_eligibility(scheme_id, small_profile)
        
        # Test with large land
        large_profile = {
            "farm": {"size_acres": 50.0, "current_crops": ["rice"]},
            "income": 50000
        }
        result_large = check_eligibility(scheme_id, large_profile)
        
        # Both should have eligibility determination
        assert "eligible" in result_small
        assert "eligible" in result_large
        assert isinstance(result_small["eligible"], bool)
        assert isinstance(result_large["eligible"], bool)


def test_check_eligibility_invalid_scheme():
    """Test eligibility check with invalid scheme ID."""
    farmer_profile = {
        "farm": {"size_acres": 5.0, "current_crops": ["rice"]},
        "income": 100000
    }
    
    with pytest.raises(ValueError) as exc_info:
        check_eligibility("invalid_scheme", farmer_profile)
    assert "not found" in str(exc_info.value).lower()


def test_check_eligibility_invalid_profile():
    """Test eligibility check with invalid farmer profile."""
    schemes = load_schemes()
    if len(schemes) > 0:
        scheme_id = schemes[0]["scheme_id"]
        
        with pytest.raises(ValueError) as exc_info:
            check_eligibility(scheme_id, None)
        assert "profile" in str(exc_info.value).lower()


def test_get_application_steps_valid():
    """Test getting application steps for valid scheme."""
    schemes = load_schemes()
    if len(schemes) > 0:
        scheme_id = schemes[0]["scheme_id"]
        result = get_application_steps(scheme_id)
        
        assert result["scheme_id"] == scheme_id
        assert "application_process" in result
        assert isinstance(result["application_process"], list)
        assert len(result["application_process"]) > 0
        
        assert "documents_required" in result
        assert isinstance(result["documents_required"], list)
        
        assert "tips" in result
        assert isinstance(result["tips"], list)


def test_get_application_steps_invalid_scheme():
    """Test getting application steps for invalid scheme."""
    with pytest.raises(ValueError) as exc_info:
        get_application_steps("invalid_scheme")
    assert "not found" in str(exc_info.value).lower()


def test_check_eligibility_with_crop_types():
    """Test eligibility checking with crop type requirements."""
    schemes = load_schemes()
    
    # Find a scheme with specific crop requirements (if any)
    for scheme in schemes:
        criteria = scheme.get("eligibility_criteria", {})
        crop_types = criteria.get("crop_types", [])
        
        if crop_types and crop_types != ["all"]:
            scheme_id = scheme["scheme_id"]
            
            # Test with matching crop
            matching_profile = {
                "farm": {
                    "size_acres": 5.0,
                    "current_crops": [crop_types[0]]
                },
                "income": 100000
            }
            result_match = check_eligibility(scheme_id, matching_profile)
            
            # Test with non-matching crop
            non_matching_profile = {
                "farm": {
                    "size_acres": 5.0,
                    "current_crops": ["unknown_crop"]
                },
                "income": 100000
            }
            result_no_match = check_eligibility(scheme_id, non_matching_profile)
            
            # Matching should be more likely eligible than non-matching
            assert "eligible" in result_match
            assert "eligible" in result_no_match
            break


def test_list_schemes_combined_filters():
    """Test listing schemes with multiple filters."""
    results = list_schemes(category="subsidy", state="Karnataka")
    
    assert isinstance(results, list)
    for scheme in results:
        assert scheme["category"] == "subsidy"
        # Should be central or Karnataka-specific
        assert scheme["level"] == "central" or scheme["state"] == "Karnataka"
