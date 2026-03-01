"""
Government scheme navigator tools for MissionAI Farmer Agent.

This module provides tools for scheme discovery, eligibility checking,
and application guidance.
"""

from typing import Dict, List, Optional
import json
from data_models import GovernmentScheme


# Load schemes from JSON
def load_schemes() -> List[Dict]:
    """Load government schemes from data file."""
    try:
        with open("data/schemes.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def list_schemes(
    category: Optional[str] = None,
    state: Optional[str] = None
) -> List[Dict]:
    """
    List government schemes with optional filtering.
    
    Args:
        category: Optional category filter (subsidy, insurance, loan, training)
        state: Optional state filter
    
    Returns:
        List of scheme dictionaries with basic information
    
    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    valid_categories = ["subsidy", "insurance", "loan", "training", None]
    if category and category.lower() not in [c for c in valid_categories if c]:
        raise ValueError(f"Category must be one of: subsidy, insurance, loan, training")
    
    schemes_data = load_schemes()
    results = []
    
    for scheme in schemes_data:
        # Apply category filter
        if category and scheme["category"].lower() != category.lower():
            continue
        
        # Apply state filter (include central schemes and matching state schemes)
        if state:
            state_lower = state.lower()
            scheme_state_lower = scheme["state"].lower()
            if scheme["level"] == "state" and scheme_state_lower != state_lower:
                continue
        
        # Add basic scheme info
        results.append({
            "scheme_id": scheme["scheme_id"],
            "name": scheme["name"],
            "category": scheme["category"],
            "level": scheme["level"],
            "state": scheme["state"],
            "description": scheme["description"][:200] + "..." if len(scheme["description"]) > 200 else scheme["description"]
        })
    
    return results


def get_scheme_details(scheme_id: str) -> Dict:
    """
    Get detailed information about a specific scheme.
    
    Args:
        scheme_id: Scheme identifier
    
    Returns:
        Dictionary with complete scheme details
    
    Raises:
        ValueError: If scheme not found
    """
    # Input validation
    if not scheme_id or not isinstance(scheme_id, str):
        raise ValueError("Scheme ID must be a non-empty string")
    
    schemes_data = load_schemes()
    
    # Find scheme
    for scheme in schemes_data:
        if scheme["scheme_id"] == scheme_id:
            # Return complete scheme information
            return {
                "scheme_id": scheme["scheme_id"],
                "name": scheme["name"],
                "name_vernacular": scheme.get("name_vernacular", {}),
                "level": scheme["level"],
                "state": scheme["state"],
                "category": scheme["category"],
                "description": scheme["description"],
                "benefits": scheme["benefits"],
                "eligibility_criteria": scheme["eligibility_criteria"],
                "application_process": scheme["application_process"],
                "documents_required": scheme["documents_required"],
                "website": scheme.get("website", ""),
                "helpline": scheme.get("helpline", "")
            }
    
    raise ValueError(f"Scheme with ID '{scheme_id}' not found")


def check_eligibility(
    scheme_id: str,
    farmer_profile: Dict
) -> Dict:
    """
    Check farmer eligibility for a scheme.
    
    Args:
        scheme_id: Scheme identifier
        farmer_profile: Farmer profile with land size, income, crops, etc.
    
    Returns:
        Dictionary with eligibility status and reasoning
    
    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    if not scheme_id or not isinstance(scheme_id, str):
        raise ValueError("Scheme ID must be a non-empty string")
    if not farmer_profile or not isinstance(farmer_profile, dict):
        raise ValueError("Farmer profile must be a dictionary")
    
    # Get scheme details
    scheme = get_scheme_details(scheme_id)
    criteria = scheme["eligibility_criteria"]
    
    # Check eligibility
    eligible = True
    reasons = []
    failed_criteria = []
    
    # Check land size
    if "farm" in farmer_profile and "size_acres" in farmer_profile["farm"]:
        land_size = farmer_profile["farm"]["size_acres"]
        min_land = criteria.get("min_land_acres", 0)
        max_land = criteria.get("max_land_acres", float('inf'))
        
        if land_size < min_land:
            eligible = False
            failed_criteria.append(f"Land size {land_size} acres is below minimum {min_land} acres")
        elif land_size > max_land:
            eligible = False
            failed_criteria.append(f"Land size {land_size} acres exceeds maximum {max_land} acres")
        else:
            reasons.append(f"Land size {land_size} acres meets requirement ({min_land}-{max_land} acres)")
    
    # Check income limit (if applicable)
    if "income_limit" in criteria and criteria["income_limit"] > 0:
        if "income" in farmer_profile:
            income = farmer_profile["income"]
            if income > criteria["income_limit"]:
                eligible = False
                failed_criteria.append(f"Income {income} exceeds limit {criteria['income_limit']}")
            else:
                reasons.append(f"Income {income} is within limit {criteria['income_limit']}")
    
    # Check crop types (if specified)
    if criteria.get("crop_types") and len(criteria["crop_types"]) > 0:
        required_crops = [c.lower() for c in criteria["crop_types"]]
        
        # Check if "all" is in required crops (means any crop is eligible)
        if "all" in required_crops or "all crops" in required_crops or "all notified crops" in required_crops or "all storable crops" in required_crops:
            reasons.append("All crops are eligible for this scheme")
        elif "farm" in farmer_profile and "current_crops" in farmer_profile["farm"]:
            farmer_crops = [c.lower() for c in farmer_profile["farm"]["current_crops"]]
            
            # Check if farmer grows any of the required crops
            matching_crops = [c for c in farmer_crops if c in required_crops]
            if matching_crops:
                reasons.append(f"Grows eligible crops: {', '.join(matching_crops)}")
            else:
                eligible = False
                failed_criteria.append(f"Does not grow required crops: {', '.join(criteria['crop_types'])}")
    
    # Check other criteria
    if criteria.get("other") and len(criteria["other"]) > 0:
        reasons.append(f"Additional criteria to verify: {', '.join(criteria['other'])}")
    
    return {
        "scheme_id": scheme_id,
        "scheme_name": scheme["name"],
        "eligible": eligible,
        "reasons": reasons if eligible else failed_criteria,
        "next_steps": "Proceed with application" if eligible else "Review eligibility criteria",
        "criteria_checked": {
            "land_size": "min_land_acres" in criteria or "max_land_acres" in criteria,
            "income": "income_limit" in criteria and criteria["income_limit"] > 0,
            "crop_types": bool(criteria.get("crop_types"))
        }
    }


def get_application_steps(scheme_id: str) -> Dict:
    """
    Get step-by-step application guidance for a scheme.
    
    Args:
        scheme_id: Scheme identifier
    
    Returns:
        Dictionary with application steps and required documents
    
    Raises:
        ValueError: If scheme not found
    """
    # Input validation
    if not scheme_id or not isinstance(scheme_id, str):
        raise ValueError("Scheme ID must be a non-empty string")
    
    # Get scheme details
    scheme = get_scheme_details(scheme_id)
    
    return {
        "scheme_id": scheme_id,
        "scheme_name": scheme["name"],
        "application_process": scheme["application_process"],
        "documents_required": scheme["documents_required"],
        "website": scheme.get("website", "Not available"),
        "helpline": scheme.get("helpline", "Not available"),
        "estimated_time": "Varies by scheme (typically 2-4 weeks)",
        "tips": [
            "Keep all documents ready before starting application",
            "Make photocopies of all documents",
            "Note down application reference number",
            "Follow up regularly on application status"
        ]
    }
