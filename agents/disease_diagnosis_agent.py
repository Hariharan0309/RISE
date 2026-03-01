"""
Disease Diagnosis Agent for MissionAI Farmer Agent.

This agent specializes in analyzing crop images for disease identification,
providing treatment recommendations, and assessing image quality.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from data_models import DiseaseDiagnosisResult
from tools.aws_services import aws_clients

logger = logging.getLogger(__name__)


# Mock disease database (would be comprehensive in production)
DISEASE_DATABASE = {
    "late_blight": {
        "name": "Late Blight",
        "crops": ["tomato", "potato"],
        "symptoms": [
            "Dark brown spots on leaves",
            "White fungal growth on leaf undersides",
            "Rapid spreading during humid conditions",
            "Fruit rot with brown lesions"
        ],
        "causes": [
            "Phytophthora infestans fungus",
            "High humidity and moderate temperatures",
            "Poor air circulation"
        ],
        "treatments": {
            "organic": [
                {"name": "Copper-based fungicide", "application": "Spray every 7-10 days", "timing": "Early morning"},
                {"name": "Neem oil solution", "application": "Spray weekly", "timing": "Evening"},
                {"name": "Remove infected plants", "application": "Immediately upon detection", "timing": "Anytime"}
            ],
            "chemical": [
                {"name": "Mancozeb", "application": "2g per liter, spray every 7 days", "timing": "Morning"},
                {"name": "Chlorothalonil", "application": "As per label instructions", "timing": "Morning"}
            ]
        },
        "prevention": [
            "Use disease-resistant varieties",
            "Ensure proper spacing for air circulation",
            "Avoid overhead irrigation",
            "Remove plant debris regularly"
        ]
    },
    "powdery_mildew": {
        "name": "Powdery Mildew",
        "crops": ["tomato", "cucumber", "pumpkin", "chilli"],
        "symptoms": [
            "White powdery coating on leaves",
            "Yellowing of affected leaves",
            "Stunted growth",
            "Reduced yield"
        ],
        "causes": [
            "Fungal infection",
            "High humidity with moderate temperatures",
            "Poor air circulation"
        ],
        "treatments": {
            "organic": [
                {"name": "Baking soda spray", "application": "1 tbsp per liter, spray weekly", "timing": "Morning"},
                {"name": "Milk solution", "application": "1:9 milk to water ratio", "timing": "Morning"},
                {"name": "Sulfur dust", "application": "Apply as per instructions", "timing": "Morning"}
            ],
            "chemical": [
                {"name": "Sulfur-based fungicide", "application": "As per label", "timing": "Morning"},
                {"name": "Myclobutanil", "application": "As per label", "timing": "Morning"}
            ]
        },
        "prevention": [
            "Improve air circulation",
            "Avoid overhead watering",
            "Remove infected leaves promptly",
            "Use resistant varieties"
        ]
    },
    "bacterial_wilt": {
        "name": "Bacterial Wilt",
        "crops": ["tomato", "potato", "chilli"],
        "symptoms": [
            "Sudden wilting of plants",
            "No recovery after watering",
            "Brown discoloration in stem",
            "Bacterial ooze from cut stems"
        ],
        "causes": [
            "Ralstonia solanacearum bacteria",
            "Soil-borne pathogen",
            "Spread through contaminated water and tools"
        ],
        "treatments": {
            "organic": [
                {"name": "Remove infected plants", "application": "Immediately, burn or bury", "timing": "Anytime"},
                {"name": "Soil solarization", "application": "Cover soil with plastic for 4-6 weeks", "timing": "Summer"},
                {"name": "Crop rotation", "application": "Avoid susceptible crops for 3-4 years", "timing": "Next season"}
            ],
            "chemical": [
                {"name": "Streptomycin sulfate", "application": "Soil drench as per label", "timing": "Early stage"},
                {"name": "Copper oxychloride", "application": "Preventive spray", "timing": "Before infection"}
            ]
        },
        "prevention": [
            "Use disease-free seeds and seedlings",
            "Practice crop rotation",
            "Sanitize tools and equipment",
            "Improve soil drainage"
        ]
    }
}


def check_image_quality(image_url: str) -> Dict[str, Any]:
    """
    Check if image quality is sufficient for disease diagnosis.
    
    Args:
        image_url: URL or path to the image
        
    Returns:
        dict: Quality assessment with 'sufficient', 'issues', and 'recommendations'
    """
    # In production, this would use actual image analysis
    # For now, we'll return a basic structure
    
    # Mock quality check (would use PIL/OpenCV in production)
    quality_score = 0.85  # Mock score
    
    issues = []
    recommendations = []
    
    if quality_score < 0.6:
        issues.append("Image is too blurry")
        recommendations.append("Take photo in good lighting")
        recommendations.append("Hold camera steady")
    
    if quality_score < 0.7:
        issues.append("Low resolution")
        recommendations.append("Move closer to the affected area")
    
    sufficient = quality_score >= 0.7
    
    return {
        "sufficient": sufficient,
        "quality_score": quality_score,
        "issues": issues,
        "recommendations": recommendations if not sufficient else ["Image quality is good"]
    }


def get_treatment_options(disease: str, severity: str) -> Dict[str, Any]:
    """
    Get treatment options for a specific disease.
    
    Args:
        disease: Disease name (key from DISEASE_DATABASE)
        severity: Severity level ('low', 'medium', 'high')
        
    Returns:
        dict: Treatment options with organic and chemical treatments
    """
    disease_key = disease.lower().replace(" ", "_")
    
    if disease_key not in DISEASE_DATABASE:
        return {
            "disease": disease,
            "severity": severity,
            "treatments": {
                "organic": [],
                "chemical": []
            },
            "message": "Disease not found in database"
        }
    
    disease_info = DISEASE_DATABASE[disease_key]
    
    # Adjust recommendations based on severity
    treatments = disease_info["treatments"].copy()
    
    if severity == "high":
        recommendation = "Immediate action required. Consider chemical treatment for faster control."
    elif severity == "medium":
        recommendation = "Act within 24-48 hours. Organic treatments may be effective if applied promptly."
    else:
        recommendation = "Early stage detected. Organic treatments should be sufficient."
    
    return {
        "disease": disease_info["name"],
        "severity": severity,
        "treatments": treatments,
        "recommendation": recommendation,
        "prevention": disease_info["prevention"]
    }


def analyze_crop_image(image_url: str, crop_type: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze crop image for disease diagnosis using Bedrock Claude vision.
    
    Args:
        image_url: URL or S3 path to the crop image
        crop_type: Optional crop type for context
        description: Optional farmer's description of the problem
        
    Returns:
        dict: Diagnosis result with disease name, severity, and recommendations
    """
    try:
        # Check image quality first
        quality_check = check_image_quality(image_url)
        
        if not quality_check["sufficient"]:
            return {
                "success": False,
                "diagnosis_id": str(uuid.uuid4()),
                "message": "Image quality insufficient for diagnosis",
                "quality_issues": quality_check["issues"],
                "recommendations": quality_check["recommendations"]
            }
        
        # In production, this would call Bedrock Claude vision API
        # For now, we'll simulate the analysis with mock data
        
        # Mock disease detection (would use actual vision API)
        # This is a simplified simulation
        detected_disease = "late_blight"  # Mock detection
        confidence = 0.87
        severity = "medium"
        
        disease_info = DISEASE_DATABASE.get(detected_disease, {})
        
        if not disease_info:
            return {
                "success": False,
                "diagnosis_id": str(uuid.uuid4()),
                "message": "Unable to identify disease from image"
            }
        
        # Get treatment options
        treatment_info = get_treatment_options(disease_info["name"], severity)
        
        # Create diagnosis result
        result = DiseaseDiagnosisResult(
            diagnosis_id=str(uuid.uuid4()),
            crop_type=crop_type or "unknown",
            image_url=image_url,
            disease_name=disease_info["name"],
            confidence=confidence,
            severity=severity,
            symptoms=disease_info["symptoms"],
            causes=disease_info["causes"],
            treatments=treatment_info["treatments"],
            prevention=disease_info["prevention"],
            estimated_yield_impact=f"{severity.capitalize()} impact - 20-40% yield loss if untreated",
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Disease diagnosis completed: {disease_info['name']} with {confidence:.2%} confidence")
        
        return {
            "success": True,
            **result.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Error during disease diagnosis: {str(e)}")
        return {
            "success": False,
            "diagnosis_id": str(uuid.uuid4()),
            "error": str(e),
            "message": "An error occurred during diagnosis. Please try again."
        }


class DiseaseDiagnosisAgent:
    """
    Specialized agent for crop disease diagnosis using multimodal vision analysis.
    
    This agent uses Amazon Bedrock Claude vision capabilities to analyze crop images,
    identify diseases, and provide treatment recommendations.
    """
    
    def __init__(self):
        """Initialize the Disease Diagnosis Agent."""
        self.name = "Disease Diagnosis Agent"
        self.description = "Specialized in crop disease identification and treatment recommendations"
        self.tools = [
            analyze_crop_image,
            get_treatment_options,
            check_image_quality
        ]
        logger.info(f"{self.name} initialized")
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the Disease Diagnosis Agent.
        
        Returns:
            str: System prompt defining agent's role and expertise
        """
        return """You are an expert agricultural pathologist specializing in crop disease diagnosis.

Your expertise includes:
- Identifying crop diseases from visual symptoms
- Analyzing images of diseased plants
- Recommending appropriate treatments (organic and chemical)
- Assessing disease severity and potential yield impact
- Providing preventive measures

When analyzing crop diseases:
1. First check if the image quality is sufficient for diagnosis
2. Identify the disease based on visible symptoms
3. Assess the severity (low, medium, high)
4. Provide both organic and chemical treatment options
5. Explain the urgency and expected outcomes
6. Suggest preventive measures for future crops

Always prioritize:
- Farmer safety when recommending treatments
- Cost-effective solutions
- Sustainable and organic options when possible
- Clear, actionable advice in simple language
- Urgency appropriate to disease severity

If the image is unclear or disease cannot be identified with confidence, ask for:
- A clearer image in better lighting
- Close-up of affected areas
- Description of when symptoms started
- Information about recent weather or farming practices"""
    
    def process(self, image_url: str, crop_type: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a disease diagnosis request.
        
        Args:
            image_url: URL or path to crop image
            crop_type: Optional crop type
            description: Optional farmer's description
            
        Returns:
            dict: Diagnosis result
        """
        logger.info(f"Processing disease diagnosis request for crop: {crop_type or 'unknown'}")
        
        result = analyze_crop_image(image_url, crop_type, description)
        
        return result
    
    def get_tools(self):
        """Get list of available tools for this agent."""
        return self.tools
