"""
Soil Analysis Agent for MissionAI Farmer Agent.

This agent specializes in soil classification, fertility assessment,
and crop recommendations based on soil conditions.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from data_models import SoilAnalysisResult

logger = logging.getLogger(__name__)


# Soil type database with characteristics
SOIL_TYPES_DATABASE = {
    "clay": {
        "name": "Clay Soil",
        "characteristics": [
            "Heavy and sticky when wet",
            "Forms hard clumps when dry",
            "Poor drainage",
            "High nutrient retention"
        ],
        "ph_range": (6.0, 7.5),
        "water_retention": "high",
        "drainage": "poor"
    },
    "loam": {
        "name": "Loam Soil",
        "characteristics": [
            "Balanced mixture of sand, silt, and clay",
            "Good drainage and water retention",
            "Easy to work with",
            "Ideal for most crops"
        ],
        "ph_range": (6.0, 7.0),
        "water_retention": "medium",
        "drainage": "good"
    },
    "sandy": {
        "name": "Sandy Soil",
        "characteristics": [
            "Gritty texture",
            "Drains quickly",
            "Low nutrient retention",
            "Warms up quickly in spring"
        ],
        "ph_range": (5.5, 7.0),
        "water_retention": "low",
        "drainage": "excellent"
    },
    "silt": {
        "name": "Silt Soil",
        "characteristics": [
            "Smooth and silky texture",
            "Good water retention",
            "Moderate drainage",
            "Fertile when well-managed"
        ],
        "ph_range": (6.0, 7.5),
        "water_retention": "high",
        "drainage": "moderate"
    },
    "laterite": {
        "name": "Laterite Soil",
        "characteristics": [
            "Red or reddish-brown color",
            "High iron and aluminum content",
            "Low fertility",
            "Common in tropical regions"
        ],
        "ph_range": (5.0, 6.5),
        "water_retention": "low",
        "drainage": "good"
    }
}


# Crop suitability database
CROP_SUITABILITY = {
    "clay": {
        "highly_suitable": ["rice", "wheat", "sugarcane", "cotton"],
        "moderately_suitable": ["soybean", "sunflower"],
        "not_suitable": ["groundnut", "potato"]
    },
    "loam": {
        "highly_suitable": ["tomato", "potato", "onion", "wheat", "rice", "cotton", "vegetables"],
        "moderately_suitable": ["all crops"],
        "not_suitable": []
    },
    "sandy": {
        "highly_suitable": ["groundnut", "watermelon", "millet", "carrot"],
        "moderately_suitable": ["potato", "tomato"],
        "not_suitable": ["rice", "sugarcane"]
    },
    "silt": {
        "highly_suitable": ["wheat", "soybean", "vegetables"],
        "moderately_suitable": ["rice", "cotton"],
        "not_suitable": []
    },
    "laterite": {
        "highly_suitable": ["cashew", "coffee", "tea", "rubber"],
        "moderately_suitable": ["millet", "groundnut"],
        "not_suitable": ["rice", "wheat"]
    }
}


def classify_soil(image_url: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Classify soil type from image or description.
    
    Args:
        image_url: Optional URL or path to soil image
        description: Optional text description of soil
        
    Returns:
        dict: Soil classification result
    """
    try:
        # In production, this would use image analysis or NLP
        # For now, we'll simulate classification
        
        # Mock classification (would use actual vision/NLP in production)
        detected_soil_type = "loam"  # Default to loam
        confidence = 0.82
        
        if description:
            description_lower = description.lower()
            if "clay" in description_lower or "sticky" in description_lower:
                detected_soil_type = "clay"
                confidence = 0.85
            elif "sandy" in description_lower or "gritty" in description_lower:
                detected_soil_type = "sandy"
                confidence = 0.88
            elif "red" in description_lower or "laterite" in description_lower:
                detected_soil_type = "laterite"
                confidence = 0.80
            elif "silt" in description_lower or "smooth" in description_lower:
                detected_soil_type = "silt"
                confidence = 0.83
        
        soil_info = SOIL_TYPES_DATABASE.get(detected_soil_type, SOIL_TYPES_DATABASE["loam"])
        
        return {
            "success": True,
            "soil_type": detected_soil_type,
            "soil_name": soil_info["name"],
            "confidence": confidence,
            "characteristics": soil_info["characteristics"],
            "ph_range": soil_info["ph_range"],
            "water_retention": soil_info["water_retention"],
            "drainage": soil_info["drainage"]
        }
        
    except Exception as e:
        logger.error(f"Error classifying soil: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Unable to classify soil type"
        }


def assess_fertility(soil_type: str, indicators: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Assess soil fertility based on soil type and indicators.
    
    Args:
        soil_type: Type of soil (clay, loam, sandy, silt, laterite)
        indicators: Optional dict with pH, organic matter, etc.
        
    Returns:
        dict: Fertility assessment
    """
    try:
        soil_type_lower = soil_type.lower()
        
        # Default fertility levels by soil type
        fertility_defaults = {
            "clay": "medium",
            "loam": "high",
            "sandy": "low",
            "silt": "medium",
            "laterite": "low"
        }
        
        fertility = fertility_defaults.get(soil_type_lower, "medium")
        
        # Mock nutrient assessment (would use actual soil test data in production)
        nutrients = {
            "nitrogen": "adequate",
            "phosphorus": "adequate",
            "potassium": "adequate",
            "organic_matter": "medium"
        }
        
        # Adjust based on indicators if provided
        if indicators:
            if "ph" in indicators:
                ph = indicators["ph"]
                if ph < 5.5:
                    nutrients["nitrogen"] = "deficient"
                    fertility = "low"
                elif ph > 8.0:
                    nutrients["phosphorus"] = "deficient"
                    fertility = "low"
            
            if "organic_matter" in indicators:
                om = indicators["organic_matter"]
                if om < 2.0:
                    nutrients["organic_matter"] = "low"
                    fertility = "low" if fertility != "high" else "medium"
        
        # Estimate pH based on soil type if not provided
        soil_info = SOIL_TYPES_DATABASE.get(soil_type_lower, {})
        ph_range = soil_info.get("ph_range", (6.0, 7.0))
        estimated_ph = (ph_range[0] + ph_range[1]) / 2
        
        return {
            "success": True,
            "soil_type": soil_type,
            "fertility": fertility,
            "ph_level": indicators.get("ph", estimated_ph) if indicators else estimated_ph,
            "nutrients": nutrients,
            "assessment": f"Soil fertility is {fertility}",
            "recommendations": _get_fertility_recommendations(fertility, nutrients)
        }
        
    except Exception as e:
        logger.error(f"Error assessing fertility: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Unable to assess soil fertility"
        }


def _get_fertility_recommendations(fertility: str, nutrients: Dict[str, str]) -> List[str]:
    """Get recommendations based on fertility assessment."""
    recommendations = []
    
    if fertility == "low":
        recommendations.append("Add organic compost to improve soil fertility")
        recommendations.append("Consider green manure crops")
    
    if nutrients.get("nitrogen") == "deficient":
        recommendations.append("Apply nitrogen-rich fertilizers or organic manure")
    
    if nutrients.get("phosphorus") == "deficient":
        recommendations.append("Add phosphate fertilizers or bone meal")
    
    if nutrients.get("potassium") == "deficient":
        recommendations.append("Apply potash or wood ash")
    
    if nutrients.get("organic_matter") == "low":
        recommendations.append("Increase organic matter through compost and mulching")
    
    if not recommendations:
        recommendations.append("Maintain current soil management practices")
    
    return recommendations


def recommend_crops(soil_type: str, season: str, location: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """
    Recommend suitable crops based on soil type, season, and location.
    
    Args:
        soil_type: Type of soil
        season: Growing season (kharif, rabi, summer)
        location: Optional location dict with state and district
        
    Returns:
        list: List of recommended crops with suitability and expected yield
    """
    try:
        soil_type_lower = soil_type.lower()
        season_lower = season.lower()
        
        if soil_type_lower not in CROP_SUITABILITY:
            return []
        
        suitability = CROP_SUITABILITY[soil_type_lower]
        recommendations = []
        
        # Expected yields (kg per acre) - mock data
        yield_estimates = {
            "rice": {"kharif": 2500, "rabi": 2000, "summer": 1800},
            "wheat": {"kharif": 1500, "rabi": 2000, "summer": 1200},
            "tomato": {"kharif": 8000, "rabi": 9000, "summer": 7000},
            "potato": {"kharif": 7000, "rabi": 8000, "summer": 6500},
            "onion": {"kharif": 6000, "rabi": 7000, "summer": 5500},
            "cotton": {"kharif": 800, "rabi": 700, "summer": 600},
            "sugarcane": {"kharif": 35000, "rabi": 32000, "summer": 30000},
            "groundnut": {"kharif": 1200, "rabi": 1400, "summer": 1100},
            "soybean": {"kharif": 1000, "rabi": 900, "summer": 800},
            "vegetables": {"kharif": 5000, "rabi": 6000, "summer": 4500}
        }
        
        # Add highly suitable crops
        for crop in suitability["highly_suitable"]:
            yield_data = yield_estimates.get(crop, {"kharif": 1000, "rabi": 1000, "summer": 1000})
            expected_yield = yield_data.get(season_lower, 1000)
            
            recommendations.append({
                "crop": crop,
                "suitability": "highly_suitable",
                "expected_yield": f"{expected_yield} kg/acre",
                "season": season,
                "care_requirements": _get_care_requirements(crop, soil_type_lower)
            })
        
        # Add moderately suitable crops
        for crop in suitability["moderately_suitable"]:
            if crop == "all crops":
                continue
            
            yield_data = yield_estimates.get(crop, {"kharif": 800, "rabi": 800, "summer": 800})
            expected_yield = yield_data.get(season_lower, 800)
            
            recommendations.append({
                "crop": crop,
                "suitability": "moderately_suitable",
                "expected_yield": f"{expected_yield} kg/acre",
                "season": season,
                "care_requirements": _get_care_requirements(crop, soil_type_lower)
            })
        
        # Sort by suitability
        recommendations.sort(key=lambda x: 0 if x["suitability"] == "highly_suitable" else 1)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error recommending crops: {str(e)}")
        return []


def _get_care_requirements(crop: str, soil_type: str) -> List[str]:
    """Get care requirements for a crop based on soil type."""
    requirements = []
    
    if soil_type == "clay":
        requirements.append("Ensure proper drainage to prevent waterlogging")
        requirements.append("Avoid overwatering")
    elif soil_type == "sandy":
        requirements.append("Frequent irrigation required")
        requirements.append("Regular fertilization needed")
    elif soil_type == "laterite":
        requirements.append("Add organic matter regularly")
        requirements.append("Monitor pH levels")
    
    # Crop-specific requirements
    if crop in ["rice", "sugarcane"]:
        requirements.append("Requires consistent water supply")
    elif crop in ["groundnut", "potato"]:
        requirements.append("Avoid excessive moisture")
    
    return requirements


def get_soil_improvement_tips(soil_type: str, deficiencies: Optional[List[str]] = None) -> List[str]:
    """
    Get soil improvement tips based on soil type and deficiencies.
    
    Args:
        soil_type: Type of soil
        deficiencies: Optional list of nutrient deficiencies
        
    Returns:
        list: List of improvement tips
    """
    try:
        soil_type_lower = soil_type.lower()
        tips = []
        
        # General tips by soil type
        if soil_type_lower == "clay":
            tips.extend([
                "Add organic matter (compost, manure) to improve drainage",
                "Use gypsum to break up clay particles",
                "Avoid working soil when wet",
                "Create raised beds for better drainage"
            ])
        elif soil_type_lower == "sandy":
            tips.extend([
                "Add organic compost to improve water retention",
                "Use mulch to reduce water evaporation",
                "Apply fertilizers in smaller, frequent doses",
                "Consider cover crops to add organic matter"
            ])
        elif soil_type_lower == "laterite":
            tips.extend([
                "Add lime to increase pH if too acidic",
                "Incorporate organic matter regularly",
                "Use green manure crops",
                "Apply balanced NPK fertilizers"
            ])
        elif soil_type_lower == "silt":
            tips.extend([
                "Add organic matter to improve structure",
                "Avoid compaction by minimizing tillage",
                "Use cover crops to prevent erosion",
                "Maintain good drainage"
            ])
        elif soil_type_lower == "loam":
            tips.extend([
                "Maintain organic matter levels",
                "Practice crop rotation",
                "Use balanced fertilization",
                "Prevent soil compaction"
            ])
        
        # Add tips for specific deficiencies
        if deficiencies:
            for deficiency in deficiencies:
                if "nitrogen" in deficiency.lower():
                    tips.append("Apply nitrogen-rich fertilizers or legume cover crops")
                elif "phosphorus" in deficiency.lower():
                    tips.append("Add rock phosphate or bone meal")
                elif "potassium" in deficiency.lower():
                    tips.append("Apply potash or wood ash")
                elif "organic" in deficiency.lower():
                    tips.append("Increase compost and organic matter additions")
        
        return tips
        
    except Exception as e:
        logger.error(f"Error getting improvement tips: {str(e)}")
        return ["Consult with local agricultural extension officer"]


class SoilAnalysisAgent:
    """
    Specialized agent for soil analysis and crop recommendations.
    
    This agent analyzes soil conditions, assesses fertility, and recommends
    suitable crops based on soil type, season, and location.
    """
    
    def __init__(self):
        """Initialize the Soil Analysis Agent."""
        self.name = "Soil Analysis Agent"
        self.description = "Specialized in soil classification and crop recommendations"
        self.tools = [
            classify_soil,
            assess_fertility,
            recommend_crops,
            get_soil_improvement_tips
        ]
        logger.info(f"{self.name} initialized")
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the Soil Analysis Agent.
        
        Returns:
            str: System prompt defining agent's role and expertise
        """
        return """You are an expert soil scientist and agronomist specializing in soil analysis and crop recommendations.

Your expertise includes:
- Soil type classification (clay, loam, sandy, silt, laterite)
- Soil fertility assessment
- Nutrient deficiency identification
- Crop suitability analysis
- Soil improvement recommendations

When analyzing soil:
1. Classify the soil type based on texture, color, and characteristics
2. Assess fertility levels and nutrient status
3. Recommend suitable crops for the soil type and season
4. Provide expected yield estimates
5. Suggest soil improvement measures if needed

Always prioritize:
- Sustainable soil management practices
- Long-term soil health over short-term gains
- Organic amendments when possible
- Crop rotation and diversity
- Water conservation

Provide recommendations that are:
- Specific to the farmer's soil type and location
- Practical and cost-effective
- Based on seasonal considerations
- Easy to understand and implement"""
    
    def process(self, image_url: Optional[str] = None, description: Optional[str] = None, 
                season: str = "kharif", location: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Process a soil analysis request.
        
        Args:
            image_url: Optional URL or path to soil image
            description: Optional text description of soil
            season: Growing season
            location: Optional location information
            
        Returns:
            dict: Complete soil analysis result
        """
        logger.info(f"Processing soil analysis request for season: {season}")
        
        # Classify soil
        classification = classify_soil(image_url, description)
        
        if not classification.get("success"):
            return classification
        
        soil_type = classification["soil_type"]
        
        # Assess fertility
        fertility = assess_fertility(soil_type)
        
        # Recommend crops
        crops = recommend_crops(soil_type, season, location)
        
        # Get improvement tips
        deficiencies = [k for k, v in fertility.get("nutrients", {}).items() if v == "deficient"]
        improvement_tips = get_soil_improvement_tips(soil_type, deficiencies)
        
        # Create complete result
        result = SoilAnalysisResult(
            analysis_id=str(uuid.uuid4()),
            soil_type=classification["soil_name"],
            fertility=fertility.get("fertility", "medium"),
            ph_level=fertility.get("ph_level", 6.5),
            nutrients=fertility.get("nutrients", {}),
            recommended_crops=crops,
            improvement_tips=improvement_tips,
            timestamp=datetime.now().isoformat()
        )
        
        return {
            "success": True,
            **result.to_dict()
        }
    
    def get_tools(self):
        """Get list of available tools for this agent."""
        return self.tools
