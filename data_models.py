"""
Data models for MissionAI Farmer Agent system.

This module defines all data classes used throughout the system with
JSON serialization/deserialization capabilities.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime
import json


@dataclass
class Location:
    """Geographic location information."""
    state: str
    district: str
    village: str
    coordinates: Dict[str, float]  # {"lat": float, "lon": float}
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Location':
        return cls(**data)


@dataclass
class Farm:
    """Farm details."""
    size_acres: float
    soil_type: str
    current_crops: List[str]
    irrigation: str  # "rainfed", "drip", "flood"
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Farm':
        return cls(**data)


@dataclass
class UserProfile:
    """User profile for farmer."""
    user_id: str
    name: str
    phone: str
    location: Location
    farm: Farm
    language_preference: str  # "kannada", "english", "hindi"
    onboarding_complete: bool
    created_at: str
    last_active: str
    
    def to_dict(self) -> dict:
        data = asdict(self)
        return data
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserProfile':
        location = Location.from_dict(data['location'])
        farm = Farm.from_dict(data['farm'])
        return cls(
            user_id=data['user_id'],
            name=data['name'],
            phone=data['phone'],
            location=location,
            farm=farm,
            language_preference=data['language_preference'],
            onboarding_complete=data['onboarding_complete'],
            created_at=data['created_at'],
            last_active=data['last_active']
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'UserProfile':
        return cls.from_dict(json.loads(json_str))


@dataclass
class Treatment:
    """Treatment option for disease."""
    name: str
    application: str
    timing: str
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Treatment':
        return cls(**data)


@dataclass
class DiseaseDiagnosisResult:
    """Result of crop disease diagnosis."""
    diagnosis_id: str
    crop_type: str
    image_url: str
    disease_name: str
    confidence: float  # 0.0 to 1.0
    severity: str  # "low", "medium", "high"
    symptoms: List[str]
    causes: List[str]
    treatments: Dict[str, List[Dict]]  # {"organic": [...], "chemical": [...]}
    prevention: List[str]
    estimated_yield_impact: str
    timestamp: str
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DiseaseDiagnosisResult':
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DiseaseDiagnosisResult':
        return cls.from_dict(json.loads(json_str))


@dataclass
class CropRecommendation:
    """Crop recommendation with suitability info."""
    crop: str
    suitability: str
    expected_yield: str
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CropRecommendation':
        return cls(**data)


@dataclass
class Nutrients:
    """Soil nutrient levels."""
    nitrogen: str  # "deficient", "adequate", "excess"
    phosphorus: str
    potassium: str
    organic_matter: str
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Nutrients':
        return cls(**data)


@dataclass
class SoilAnalysisResult:
    """Result of soil analysis."""
    analysis_id: str
    soil_type: str  # "clay", "loam", "sandy", "silt", "laterite"
    fertility: str  # "low", "medium", "high"
    ph_level: float
    nutrients: Nutrients
    recommended_crops: List[CropRecommendation]
    improvement_tips: List[str]
    timestamp: str
    
    def to_dict(self) -> dict:
        data = asdict(self)
        return data
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SoilAnalysisResult':
        nutrients = Nutrients.from_dict(data['nutrients'])
        crops = [CropRecommendation.from_dict(c) for c in data['recommended_crops']]
        return cls(
            analysis_id=data['analysis_id'],
            soil_type=data['soil_type'],
            fertility=data['fertility'],
            ph_level=data['ph_level'],
            nutrients=nutrients,
            recommended_crops=crops,
            improvement_tips=data['improvement_tips'],
            timestamp=data['timestamp']
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SoilAnalysisResult':
        return cls.from_dict(json.loads(json_str))


@dataclass
class CurrentWeather:
    """Current weather conditions."""
    temperature: float
    humidity: float
    rainfall: float
    wind_speed: float
    conditions: str
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CurrentWeather':
        return cls(**data)


@dataclass
class FarmingAdvice:
    """Farming activity advice based on weather."""
    activity: str
    optimal_timing: str
    reasoning: str
    precautions: List[str]
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FarmingAdvice':
        return cls(**data)


@dataclass
class WeatherAdvisory:
    """Weather advisory for farming."""
    advisory_id: str
    location: Dict
    current_weather: CurrentWeather
    forecast: List[Dict]  # 7-day forecast
    farming_advice: FarmingAdvice
    alerts: List[Dict]  # {"type": str, "severity": str, "message": str}
    timestamp: str
    
    def to_dict(self) -> dict:
        data = asdict(self)
        return data
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WeatherAdvisory':
        current = CurrentWeather.from_dict(data['current_weather'])
        advice = FarmingAdvice.from_dict(data['farming_advice'])
        return cls(
            advisory_id=data['advisory_id'],
            location=data['location'],
            current_weather=current,
            forecast=data['forecast'],
            farming_advice=advice,
            alerts=data['alerts'],
            timestamp=data['timestamp']
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WeatherAdvisory':
        return cls.from_dict(json.loads(json_str))


@dataclass
class MarketListing:
    """Market listing for produce or inputs."""
    listing_id: str
    type: str  # "sell", "buy"
    product: str
    category: str  # "produce", "seeds", "fertilizer", "pesticide"
    quantity: float
    unit: str
    quality: str  # "grade_a", "grade_b", "organic"
    price_per_unit: float
    location: Dict
    expiry_date: str
    is_sustainable: bool
    seller_id: str
    created_at: str
    status: str  # "active", "sold", "expired"
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MarketListing':
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MarketListing':
        return cls.from_dict(json.loads(json_str))


@dataclass
class EligibilityCriteria:
    """Eligibility criteria for government scheme."""
    min_land_acres: float
    max_land_acres: float
    income_limit: float
    crop_types: List[str]
    other: List[str]
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EligibilityCriteria':
        return cls(**data)


@dataclass
class GovernmentScheme:
    """Government scheme information."""
    scheme_id: str
    name: str
    name_vernacular: Dict[str, str]  # {"kannada": str, "hindi": str}
    level: str  # "central", "state"
    state: str
    category: str  # "subsidy", "insurance", "loan", "training"
    description: str
    benefits: List[str]
    eligibility_criteria: EligibilityCriteria
    application_process: List[str]
    documents_required: List[str]
    website: str
    helpline: str
    
    def to_dict(self) -> dict:
        data = asdict(self)
        return data
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GovernmentScheme':
        criteria = EligibilityCriteria.from_dict(data['eligibility_criteria'])
        return cls(
            scheme_id=data['scheme_id'],
            name=data['name'],
            name_vernacular=data['name_vernacular'],
            level=data['level'],
            state=data['state'],
            category=data['category'],
            description=data['description'],
            benefits=data['benefits'],
            eligibility_criteria=criteria,
            application_process=data['application_process'],
            documents_required=data['documents_required'],
            website=data['website'],
            helpline=data['helpline']
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'GovernmentScheme':
        return cls.from_dict(json.loads(json_str))


@dataclass
class Costs:
    """Cost breakdown for farming."""
    seeds: float
    fertilizers: float
    pesticides: float
    labor: float
    water: float
    equipment: float
    other: float
    total: float
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Costs':
        return cls(**data)


@dataclass
class Revenue:
    """Revenue calculation."""
    expected_yield_kg: float
    price_per_kg: float
    total: float
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Revenue':
        return cls(**data)


@dataclass
class FinancialCalculation:
    """Financial calculation for crop profitability."""
    calculation_id: str
    crop: str
    area_acres: float
    costs: Costs
    revenue: Revenue
    profit_loss: float
    roi_percentage: float
    break_even_price: float
    timestamp: str
    
    def to_dict(self) -> dict:
        data = asdict(self)
        return data
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FinancialCalculation':
        costs = Costs.from_dict(data['costs'])
        revenue = Revenue.from_dict(data['revenue'])
        return cls(
            calculation_id=data['calculation_id'],
            crop=data['crop'],
            area_acres=data['area_acres'],
            costs=costs,
            revenue=revenue,
            profit_loss=data['profit_loss'],
            roi_percentage=data['roi_percentage'],
            break_even_price=data['break_even_price'],
            timestamp=data['timestamp']
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'FinancialCalculation':
        return cls.from_dict(json.loads(json_str))


@dataclass
class Answer:
    """Answer to a community post."""
    farmer_id: str
    content: str
    helpful_count: int
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Answer':
        return cls(**data)


@dataclass
class CommunityPost:
    """Community forum post."""
    post_id: str
    farmer_id: str
    location: Dict
    language: str
    topic: str  # "disease", "weather", "market", "technique"
    question: str
    answers: List[Answer]
    tags: List[str]
    created_at: str
    view_count: int
    
    def to_dict(self) -> dict:
        data = asdict(self)
        return data
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CommunityPost':
        answers = [Answer.from_dict(a) for a in data['answers']]
        return cls(
            post_id=data['post_id'],
            farmer_id=data['farmer_id'],
            location=data['location'],
            language=data['language'],
            topic=data['topic'],
            question=data['question'],
            answers=answers,
            tags=data['tags'],
            created_at=data['created_at'],
            view_count=data['view_count']
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'CommunityPost':
        return cls.from_dict(json.loads(json_str))
