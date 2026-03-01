"""
Unit tests for data models serialization and deserialization.

Tests JSON round-trip for each model and validation logic.
Requirements: 13.1, 13.3
"""

import pytest
import json
from datetime import datetime
from data_models import (
    UserProfile, Location, Farm,
    DiseaseDiagnosisResult, Treatment,
    SoilAnalysisResult, CropRecommendation, Nutrients,
    WeatherAdvisory, CurrentWeather, FarmingAdvice,
    MarketListing,
    GovernmentScheme, EligibilityCriteria,
    FinancialCalculation, Costs, Revenue,
    CommunityPost, Answer
)


class TestUserProfile:
    """Test UserProfile serialization and deserialization."""
    
    def test_user_profile_to_dict(self):
        """Test UserProfile converts to dict correctly."""
        location = Location(
            state="Karnataka",
            district="Mysore",
            village="Hunsur",
            coordinates={"lat": 12.3, "lon": 76.2}
        )
        farm = Farm(
            size_acres=5.0,
            soil_type="loam",
            current_crops=["rice", "sugarcane"],
            irrigation="drip"
        )
        profile = UserProfile(
            user_id="user123",
            name="Ravi Kumar",
            phone="+919876543210",
            location=location,
            farm=farm,
            language_preference="kannada",
            onboarding_complete=True,
            created_at="2024-01-01T00:00:00Z",
            last_active="2024-01-15T10:30:00Z"
        )
        
        data = profile.to_dict()
        assert data['user_id'] == "user123"
        assert data['name'] == "Ravi Kumar"
        assert data['location']['state'] == "Karnataka"
        assert data['farm']['size_acres'] == 5.0
    
    def test_user_profile_json_round_trip(self):
        """Test UserProfile JSON serialization round-trip."""
        location = Location(
            state="Karnataka",
            district="Mysore",
            village="Hunsur",
            coordinates={"lat": 12.3, "lon": 76.2}
        )
        farm = Farm(
            size_acres=5.0,
            soil_type="loam",
            current_crops=["rice", "sugarcane"],
            irrigation="drip"
        )
        original = UserProfile(
            user_id="user123",
            name="Ravi Kumar",
            phone="+919876543210",
            location=location,
            farm=farm,
            language_preference="kannada",
            onboarding_complete=True,
            created_at="2024-01-01T00:00:00Z",
            last_active="2024-01-15T10:30:00Z"
        )
        
        json_str = original.to_json()
        restored = UserProfile.from_json(json_str)
        
        assert restored.user_id == original.user_id
        assert restored.name == original.name
        assert restored.location.state == original.location.state
        assert restored.farm.size_acres == original.farm.size_acres
        assert restored.language_preference == original.language_preference


class TestDiseaseDiagnosisResult:
    """Test DiseaseDiagnosisResult serialization."""
    
    def test_diagnosis_result_to_dict(self):
        """Test DiseaseDiagnosisResult converts to dict correctly."""
        result = DiseaseDiagnosisResult(
            diagnosis_id="diag123",
            crop_type="tomato",
            image_url="s3://bucket/image.jpg",
            disease_name="Late Blight",
            confidence=0.92,
            severity="high",
            symptoms=["brown spots", "wilting"],
            causes=["fungal infection"],
            treatments={
                "organic": [{"name": "neem oil", "application": "spray", "timing": "morning"}],
                "chemical": [{"name": "fungicide", "application": "spray", "timing": "evening"}]
            },
            prevention=["crop rotation", "proper spacing"],
            estimated_yield_impact="30-40% loss if untreated",
            timestamp="2024-01-15T10:00:00Z"
        )
        
        data = result.to_dict()
        assert data['diagnosis_id'] == "diag123"
        assert data['disease_name'] == "Late Blight"
        assert data['confidence'] == 0.92
        assert len(data['symptoms']) == 2
    
    def test_diagnosis_result_json_round_trip(self):
        """Test DiseaseDiagnosisResult JSON round-trip."""
        original = DiseaseDiagnosisResult(
            diagnosis_id="diag123",
            crop_type="tomato",
            image_url="s3://bucket/image.jpg",
            disease_name="Late Blight",
            confidence=0.92,
            severity="high",
            symptoms=["brown spots", "wilting"],
            causes=["fungal infection"],
            treatments={
                "organic": [{"name": "neem oil", "application": "spray", "timing": "morning"}],
                "chemical": [{"name": "fungicide", "application": "spray", "timing": "evening"}]
            },
            prevention=["crop rotation", "proper spacing"],
            estimated_yield_impact="30-40% loss if untreated",
            timestamp="2024-01-15T10:00:00Z"
        )
        
        json_str = original.to_json()
        restored = DiseaseDiagnosisResult.from_json(json_str)
        
        assert restored.diagnosis_id == original.diagnosis_id
        assert restored.disease_name == original.disease_name
        assert restored.confidence == original.confidence
        assert restored.severity == original.severity


class TestSoilAnalysisResult:
    """Test SoilAnalysisResult serialization."""
    
    def test_soil_analysis_to_dict(self):
        """Test SoilAnalysisResult converts to dict correctly."""
        nutrients = Nutrients(
            nitrogen="adequate",
            phosphorus="deficient",
            potassium="adequate",
            organic_matter="adequate"
        )
        crops = [
            CropRecommendation(crop="rice", suitability="high", expected_yield="4 tons/acre"),
            CropRecommendation(crop="wheat", suitability="medium", expected_yield="2.5 tons/acre")
        ]
        result = SoilAnalysisResult(
            analysis_id="soil123",
            soil_type="loam",
            fertility="medium",
            ph_level=6.5,
            nutrients=nutrients,
            recommended_crops=crops,
            improvement_tips=["add phosphorus fertilizer", "maintain organic matter"],
            timestamp="2024-01-15T10:00:00Z"
        )
        
        data = result.to_dict()
        assert data['soil_type'] == "loam"
        assert data['ph_level'] == 6.5
        assert len(data['recommended_crops']) == 2
    
    def test_soil_analysis_json_round_trip(self):
        """Test SoilAnalysisResult JSON round-trip."""
        nutrients = Nutrients(
            nitrogen="adequate",
            phosphorus="deficient",
            potassium="adequate",
            organic_matter="adequate"
        )
        crops = [
            CropRecommendation(crop="rice", suitability="high", expected_yield="4 tons/acre")
        ]
        original = SoilAnalysisResult(
            analysis_id="soil123",
            soil_type="loam",
            fertility="medium",
            ph_level=6.5,
            nutrients=nutrients,
            recommended_crops=crops,
            improvement_tips=["add phosphorus fertilizer"],
            timestamp="2024-01-15T10:00:00Z"
        )
        
        json_str = original.to_json()
        restored = SoilAnalysisResult.from_json(json_str)
        
        assert restored.analysis_id == original.analysis_id
        assert restored.soil_type == original.soil_type
        assert restored.nutrients.nitrogen == original.nutrients.nitrogen


class TestWeatherAdvisory:
    """Test WeatherAdvisory serialization."""
    
    def test_weather_advisory_to_dict(self):
        """Test WeatherAdvisory converts to dict correctly."""
        current = CurrentWeather(
            temperature=28.5,
            humidity=65.0,
            rainfall=0.0,
            wind_speed=12.0,
            conditions="partly cloudy"
        )
        advice = FarmingAdvice(
            activity="spraying",
            optimal_timing="tomorrow morning 6-9 AM",
            reasoning="low wind, no rain predicted",
            precautions=["wear protective gear", "avoid afternoon heat"]
        )
        advisory = WeatherAdvisory(
            advisory_id="weather123",
            location={"state": "Karnataka", "district": "Mysore"},
            current_weather=current,
            forecast=[{"day": "tomorrow", "temp": 30, "rain": 0}],
            farming_advice=advice,
            alerts=[],
            timestamp="2024-01-15T10:00:00Z"
        )
        
        data = advisory.to_dict()
        assert data['advisory_id'] == "weather123"
        assert data['current_weather']['temperature'] == 28.5
    
    def test_weather_advisory_json_round_trip(self):
        """Test WeatherAdvisory JSON round-trip."""
        current = CurrentWeather(
            temperature=28.5,
            humidity=65.0,
            rainfall=0.0,
            wind_speed=12.0,
            conditions="partly cloudy"
        )
        advice = FarmingAdvice(
            activity="spraying",
            optimal_timing="tomorrow morning 6-9 AM",
            reasoning="low wind, no rain predicted",
            precautions=["wear protective gear"]
        )
        original = WeatherAdvisory(
            advisory_id="weather123",
            location={"state": "Karnataka", "district": "Mysore"},
            current_weather=current,
            forecast=[{"day": "tomorrow", "temp": 30, "rain": 0}],
            farming_advice=advice,
            alerts=[],
            timestamp="2024-01-15T10:00:00Z"
        )
        
        json_str = original.to_json()
        restored = WeatherAdvisory.from_json(json_str)
        
        assert restored.advisory_id == original.advisory_id
        assert restored.current_weather.temperature == original.current_weather.temperature


class TestMarketListing:
    """Test MarketListing serialization."""
    
    def test_market_listing_to_dict(self):
        """Test MarketListing converts to dict correctly."""
        listing = MarketListing(
            listing_id="listing123",
            type="sell",
            product="tomatoes",
            category="produce",
            quantity=100.0,
            unit="kg",
            quality="grade_a",
            price_per_unit=30.0,
            location={"state": "Karnataka", "district": "Mysore"},
            expiry_date="2024-01-20",
            is_sustainable=True,
            seller_id="user123",
            created_at="2024-01-15T10:00:00Z",
            status="active"
        )
        
        data = listing.to_dict()
        assert data['listing_id'] == "listing123"
        assert data['quantity'] == 100.0
        assert data['is_sustainable'] is True
    
    def test_market_listing_json_round_trip(self):
        """Test MarketListing JSON round-trip."""
        original = MarketListing(
            listing_id="listing123",
            type="sell",
            product="tomatoes",
            category="produce",
            quantity=100.0,
            unit="kg",
            quality="grade_a",
            price_per_unit=30.0,
            location={"state": "Karnataka", "district": "Mysore"},
            expiry_date="2024-01-20",
            is_sustainable=True,
            seller_id="user123",
            created_at="2024-01-15T10:00:00Z",
            status="active"
        )
        
        json_str = original.to_json()
        restored = MarketListing.from_json(json_str)
        
        assert restored.listing_id == original.listing_id
        assert restored.quantity == original.quantity
        assert restored.is_sustainable == original.is_sustainable


class TestGovernmentScheme:
    """Test GovernmentScheme serialization."""
    
    def test_government_scheme_to_dict(self):
        """Test GovernmentScheme converts to dict correctly."""
        criteria = EligibilityCriteria(
            min_land_acres=0.0,
            max_land_acres=10.0,
            income_limit=200000.0,
            crop_types=["all"],
            other=["must be registered farmer"]
        )
        scheme = GovernmentScheme(
            scheme_id="scheme123",
            name="PM-KISAN",
            name_vernacular={"kannada": "ಪಿಎಂ-ಕಿಸಾನ್", "hindi": "पीएम-किसान"},
            level="central",
            state="all",
            category="subsidy",
            description="Direct income support",
            benefits=["Rs 6000 per year"],
            eligibility_criteria=criteria,
            application_process=["Register online", "Submit documents"],
            documents_required=["Aadhaar", "Land records"],
            website="https://pmkisan.gov.in",
            helpline="1800-123-4567"
        )
        
        data = scheme.to_dict()
        assert data['scheme_id'] == "scheme123"
        assert data['name'] == "PM-KISAN"
    
    def test_government_scheme_json_round_trip(self):
        """Test GovernmentScheme JSON round-trip."""
        criteria = EligibilityCriteria(
            min_land_acres=0.0,
            max_land_acres=10.0,
            income_limit=200000.0,
            crop_types=["all"],
            other=["must be registered farmer"]
        )
        original = GovernmentScheme(
            scheme_id="scheme123",
            name="PM-KISAN",
            name_vernacular={"kannada": "ಪಿಎಂ-ಕಿಸಾನ್", "hindi": "पीएम-किसान"},
            level="central",
            state="all",
            category="subsidy",
            description="Direct income support",
            benefits=["Rs 6000 per year"],
            eligibility_criteria=criteria,
            application_process=["Register online"],
            documents_required=["Aadhaar"],
            website="https://pmkisan.gov.in",
            helpline="1800-123-4567"
        )
        
        json_str = original.to_json()
        restored = GovernmentScheme.from_json(json_str)
        
        assert restored.scheme_id == original.scheme_id
        assert restored.name == original.name


class TestFinancialCalculation:
    """Test FinancialCalculation serialization."""
    
    def test_financial_calculation_to_dict(self):
        """Test FinancialCalculation converts to dict correctly."""
        costs = Costs(
            seeds=5000.0,
            fertilizers=8000.0,
            pesticides=3000.0,
            labor=15000.0,
            water=2000.0,
            equipment=5000.0,
            other=2000.0,
            total=40000.0
        )
        revenue = Revenue(
            expected_yield_kg=2000.0,
            price_per_kg=30.0,
            total=60000.0
        )
        calc = FinancialCalculation(
            calculation_id="calc123",
            crop="tomato",
            area_acres=2.0,
            costs=costs,
            revenue=revenue,
            profit_loss=20000.0,
            roi_percentage=50.0,
            break_even_price=20.0,
            timestamp="2024-01-15T10:00:00Z"
        )
        
        data = calc.to_dict()
        assert data['calculation_id'] == "calc123"
        assert data['profit_loss'] == 20000.0
    
    def test_financial_calculation_json_round_trip(self):
        """Test FinancialCalculation JSON round-trip."""
        costs = Costs(
            seeds=5000.0,
            fertilizers=8000.0,
            pesticides=3000.0,
            labor=15000.0,
            water=2000.0,
            equipment=5000.0,
            other=2000.0,
            total=40000.0
        )
        revenue = Revenue(
            expected_yield_kg=2000.0,
            price_per_kg=30.0,
            total=60000.0
        )
        original = FinancialCalculation(
            calculation_id="calc123",
            crop="tomato",
            area_acres=2.0,
            costs=costs,
            revenue=revenue,
            profit_loss=20000.0,
            roi_percentage=50.0,
            break_even_price=20.0,
            timestamp="2024-01-15T10:00:00Z"
        )
        
        json_str = original.to_json()
        restored = FinancialCalculation.from_json(json_str)
        
        assert restored.calculation_id == original.calculation_id
        assert restored.profit_loss == original.profit_loss


class TestCommunityPost:
    """Test CommunityPost serialization."""
    
    def test_community_post_to_dict(self):
        """Test CommunityPost converts to dict correctly."""
        answers = [
            Answer(farmer_id="user456", content="Try neem oil spray", helpful_count=5),
            Answer(farmer_id="user789", content="Check soil pH", helpful_count=3)
        ]
        post = CommunityPost(
            post_id="post123",
            farmer_id="user123",
            location={"state": "Karnataka", "district": "Mysore"},
            language="kannada",
            topic="disease",
            question="How to treat tomato blight?",
            answers=answers,
            tags=["tomato", "disease", "blight"],
            created_at="2024-01-15T10:00:00Z",
            view_count=25
        )
        
        data = post.to_dict()
        assert data['post_id'] == "post123"
        assert len(data['answers']) == 2
    
    def test_community_post_json_round_trip(self):
        """Test CommunityPost JSON round-trip."""
        answers = [
            Answer(farmer_id="user456", content="Try neem oil spray", helpful_count=5)
        ]
        original = CommunityPost(
            post_id="post123",
            farmer_id="user123",
            location={"state": "Karnataka", "district": "Mysore"},
            language="kannada",
            topic="disease",
            question="How to treat tomato blight?",
            answers=answers,
            tags=["tomato", "disease"],
            created_at="2024-01-15T10:00:00Z",
            view_count=25
        )
        
        json_str = original.to_json()
        restored = CommunityPost.from_json(json_str)
        
        assert restored.post_id == original.post_id
        assert len(restored.answers) == len(original.answers)
        assert restored.answers[0].farmer_id == original.answers[0].farmer_id
