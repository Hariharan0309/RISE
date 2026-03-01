"""
Unit tests for Schemes Navigator Agent.

Tests scheme listing, details retrieval, eligibility checking,
and application guidance functionality.
"""

import pytest
from agents.schemes_navigator_agent import SchemesNavigatorAgent


@pytest.fixture
def agent():
    """Create a Schemes Navigator Agent instance for testing."""
    return SchemesNavigatorAgent()


@pytest.fixture
def sample_farmer_profile():
    """Create a sample farmer profile for testing."""
    return {
        "user_id": "farmer123",
        "name": "Test Farmer",
        "location": {
            "state": "Karnataka",
            "district": "Mysuru",
            "village": "Test Village"
        },
        "farm": {
            "size_acres": 5.0,
            "soil_type": "loam",
            "current_crops": ["rice", "tomato"],
            "irrigation": "drip"
        },
        "income": 200000,
        "language_preference": "kannada"
    }


@pytest.fixture
def small_farmer_profile():
    """Create a small farmer profile for testing."""
    return {
        "user_id": "farmer456",
        "name": "Small Farmer",
        "location": {
            "state": "Karnataka",
            "district": "Bengaluru Rural"
        },
        "farm": {
            "size_acres": 1.5,
            "current_crops": ["vegetables"]
        },
        "income": 100000
    }


def test_agent_initialization(agent):
    """Test that agent initializes correctly."""
    assert agent.name == "Schemes Navigator Agent"
    assert agent.description == "Specialized in government schemes and eligibility checking"
    assert len(agent.tools) == 4


def test_get_system_prompt(agent):
    """Test that system prompt is comprehensive."""
    prompt = agent.get_system_prompt()
    
    assert "government schemes" in prompt.lower()
    assert "eligibility" in prompt.lower()
    assert "application" in prompt.lower()
    assert "pm-kisan" in prompt.lower()


def test_list_all_schemes(agent):
    """Test listing all schemes without filters."""
    result = agent.list_available_schemes()
    
    assert result["success"] is True
    assert result["query_type"] == "list"
    assert result["total_schemes"] > 0
    assert "schemes" in result
    assert len(result["schemes"]) > 0


def test_list_schemes_by_category(agent):
    """Test listing schemes filtered by category."""
    result = agent.list_available_schemes(category="subsidy")
    
    assert result["success"] is True
    assert result["category"] == "subsidy"
    assert all(s["category"] == "subsidy" for s in result["schemes"])


def test_list_schemes_by_state(agent):
    """Test listing schemes filtered by state."""
    result = agent.list_available_schemes(state="Karnataka")
    
    assert result["success"] is True
    assert result["state"] == "Karnataka"
    # Should include both central and Karnataka state schemes
    assert any(s["level"] == "central" for s in result["schemes"])
    assert any(s["state"] == "Karnataka" for s in result["schemes"])


def test_list_schemes_by_category_and_state(agent):
    """Test listing schemes with multiple filters."""
    result = agent.list_available_schemes(category="insurance", state="Karnataka")
    
    assert result["success"] is True
    assert result["category"] == "insurance"
    assert result["state"] == "Karnataka"


def test_get_scheme_details_pm_kisan(agent):
    """Test getting details for PM-KISAN scheme."""
    result = agent.get_scheme_information("pm-kisan")
    
    assert result["success"] is True
    assert result["query_type"] == "details"
    assert "scheme" in result
    
    scheme = result["scheme"]
    assert scheme["scheme_id"] == "pm-kisan"
    assert scheme["name"] == "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)"
    assert scheme["level"] == "central"
    assert "benefits" in scheme
    assert "eligibility_criteria" in scheme
    assert "application_process" in scheme
    assert "documents_required" in scheme


def test_get_scheme_details_invalid_id(agent):
    """Test getting details for non-existent scheme."""
    result = agent.get_scheme_information("invalid-scheme-id")
    
    assert result["success"] is False
    assert "error" in result


def test_check_eligibility_pm_kisan_eligible(agent, sample_farmer_profile):
    """Test eligibility check for PM-KISAN (should be eligible)."""
    result = agent.check_farmer_eligibility("pm-kisan", sample_farmer_profile)
    
    assert result["success"] is True
    assert result["query_type"] == "eligibility"
    assert "eligibility" in result
    
    eligibility = result["eligibility"]
    assert eligibility["scheme_id"] == "pm-kisan"
    assert eligibility["eligible"] is True
    assert len(eligibility["reasons"]) > 0


def test_check_eligibility_krishi_bhagya_eligible(agent, sample_farmer_profile):
    """Test eligibility for Krishi Bhagya scheme (Karnataka farmer with 5 acres)."""
    result = agent.check_farmer_eligibility("karnataka-krishi-bhagya", sample_farmer_profile)
    
    assert result["success"] is True
    eligibility = result["eligibility"]
    
    # Should be eligible: Karnataka farmer with 5 acres (within 0.5-20 range)
    assert eligibility["eligible"] is True
    assert "5.0 acres" in str(eligibility["reasons"])


def test_check_eligibility_krishi_bhagya_too_small(agent):
    """Test eligibility for Krishi Bhagya with land too small."""
    tiny_farmer = {
        "location": {"state": "Karnataka"},
        "farm": {"size_acres": 0.3}  # Below 0.5 acre minimum
    }
    
    result = agent.check_farmer_eligibility("karnataka-krishi-bhagya", tiny_farmer)
    
    assert result["success"] is True
    eligibility = result["eligibility"]
    
    # Should not be eligible due to land size
    assert eligibility["eligible"] is False
    assert any("below minimum" in str(reason).lower() for reason in eligibility["reasons"])


def test_check_eligibility_missing_scheme_id(agent, sample_farmer_profile):
    """Test eligibility check without scheme ID."""
    result = agent.check_farmer_eligibility("", sample_farmer_profile)
    
    assert result["success"] is False
    assert "error" in result


def test_check_eligibility_missing_profile(agent):
    """Test eligibility check without farmer profile."""
    result = agent.check_farmer_eligibility("pm-kisan", None)
    
    assert result["success"] is False
    assert "error" in result


def test_get_application_guidance_pm_kisan(agent):
    """Test getting application guidance for PM-KISAN."""
    result = agent.get_application_guidance("pm-kisan")
    
    assert result["success"] is True
    assert result["query_type"] == "application"
    assert "application" in result
    
    app_info = result["application"]
    assert app_info["scheme_id"] == "pm-kisan"
    assert "application_process" in app_info
    assert "documents_required" in app_info
    assert "website" in app_info
    assert "helpline" in app_info
    assert "tips" in app_info
    assert len(app_info["application_process"]) > 0
    assert len(app_info["documents_required"]) > 0


def test_get_application_guidance_kcc(agent):
    """Test getting application guidance for Kisan Credit Card."""
    result = agent.get_application_guidance("kcc")
    
    assert result["success"] is True
    app_info = result["application"]
    
    assert app_info["scheme_name"] == "Kisan Credit Card (KCC)"
    assert "bank" in str(app_info["application_process"]).lower()
    assert any("aadhaar" in doc.lower() for doc in app_info["documents_required"])


def test_get_application_guidance_invalid_id(agent):
    """Test getting application guidance for invalid scheme."""
    result = agent.get_application_guidance("invalid-scheme")
    
    assert result["success"] is False
    assert "error" in result


def test_find_schemes_for_farmer(agent, sample_farmer_profile):
    """Test finding all eligible schemes for a farmer."""
    result = agent.find_schemes_for_farmer(sample_farmer_profile)
    
    assert result["success"] is True
    assert "eligible_schemes" in result
    assert "potentially_eligible" in result
    assert result["farmer_state"] == "Karnataka"
    assert result["total_schemes_checked"] > 0
    
    # Should find at least PM-KISAN (universal scheme)
    eligible_ids = [s["scheme"]["scheme_id"] for s in result["eligible_schemes"]]
    assert "pm-kisan" in eligible_ids


def test_find_schemes_for_small_farmer(agent, small_farmer_profile):
    """Test finding schemes for a small farmer."""
    result = agent.find_schemes_for_farmer(small_farmer_profile)
    
    assert result["success"] is True
    assert len(result["eligible_schemes"]) > 0
    
    # Small farmers should be eligible for PM-KISAN
    eligible_ids = [s["scheme"]["scheme_id"] for s in result["eligible_schemes"]]
    assert "pm-kisan" in eligible_ids


def test_process_invalid_query_type(agent):
    """Test processing with invalid query type."""
    result = agent.process(query_type="invalid_type")
    
    assert result["success"] is False
    assert "unknown query type" in result["error"].lower()


def test_list_schemes_invalid_category(agent):
    """Test listing schemes with invalid category."""
    result = agent.list_available_schemes(category="invalid_category")
    
    assert result["success"] is False
    assert "error" in result


def test_eligibility_check_with_crop_requirements(agent):
    """Test eligibility checking for schemes with crop requirements."""
    # NFSM requires specific crops (rice, wheat, pulses, coarse cereals)
    rice_farmer = {
        "location": {"state": "Karnataka"},
        "farm": {
            "size_acres": 3.0,
            "current_crops": ["rice", "wheat"]
        }
    }
    
    result = agent.check_farmer_eligibility("nfsm", rice_farmer)
    
    assert result["success"] is True
    eligibility = result["eligibility"]
    
    # Should be eligible because farmer grows rice
    assert eligibility["eligible"] is True


def test_eligibility_check_without_required_crops(agent):
    """Test eligibility for scheme when farmer doesn't grow required crops."""
    vegetable_farmer = {
        "location": {"state": "Karnataka"},
        "farm": {
            "size_acres": 3.0,
            "current_crops": ["tomato", "potato"]
        }
    }
    
    result = agent.check_farmer_eligibility("nfsm", vegetable_farmer)
    
    assert result["success"] is True
    eligibility = result["eligibility"]
    
    # Should not be eligible because NFSM requires rice/wheat/pulses/cereals
    assert eligibility["eligible"] is False
    assert any("does not grow required crops" in str(reason).lower() 
              for reason in eligibility["reasons"])


def test_state_specific_scheme_for_karnataka_farmer(agent, sample_farmer_profile):
    """Test that Karnataka farmers can access Karnataka-specific schemes."""
    result = agent.list_available_schemes(state="Karnataka")
    
    assert result["success"] is True
    
    # Should include Karnataka-specific schemes
    scheme_ids = [s["scheme_id"] for s in result["schemes"]]
    assert "karnataka-raitha-shakti" in scheme_ids
    assert "karnataka-krishi-bhagya" in scheme_ids


def test_central_schemes_available_to_all_states(agent):
    """Test that central schemes are available regardless of state filter."""
    result = agent.list_available_schemes(state="Karnataka")
    
    assert result["success"] is True
    
    # Should include central schemes
    central_schemes = [s for s in result["schemes"] if s["level"] == "central"]
    assert len(central_schemes) > 0
    
    # PM-KISAN should be available
    scheme_ids = [s["scheme_id"] for s in result["schemes"]]
    assert "pm-kisan" in scheme_ids


def test_get_tools(agent):
    """Test that agent returns its tools."""
    tools = agent.get_tools()
    
    assert len(tools) == 4
    assert callable(tools[0])
