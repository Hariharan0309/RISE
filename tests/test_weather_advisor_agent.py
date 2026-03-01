"""
Unit tests for Weather Advisor Agent.

Tests the Weather Advisor Agent's ability to provide weather forecasts,
activity timing recommendations, and proactive advice.
"""

import pytest
from agents.weather_advisor_agent import WeatherAdvisorAgent


class TestWeatherAdvisorAgent:
    """Test suite for Weather Advisor Agent."""
    
    @pytest.fixture
    def agent(self):
        """Create a Weather Advisor Agent instance."""
        return WeatherAdvisorAgent()
    
    @pytest.fixture
    def sample_location(self):
        """Sample location for testing."""
        return {
            "district": "Bangalore Rural",
            "state": "Karnataka"
        }
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "Weather Advisor Agent"
        assert agent.description == "Specialized in weather forecasting and farming activity timing"
        assert len(agent.tools) == 4
    
    def test_get_system_prompt(self, agent):
        """Test system prompt is comprehensive."""
        prompt = agent.get_system_prompt()
        assert "agricultural meteorologist" in prompt.lower()
        assert "weather" in prompt.lower()
        assert "timing" in prompt.lower()
        assert len(prompt) > 200
    
    def test_get_forecast(self, agent, sample_location):
        """Test getting weather forecast."""
        result = agent.get_forecast(sample_location, days=7)
        
        assert result["success"] is True
        assert result["query_type"] == "forecast"
        assert "current_weather" in result
        assert "forecast" in result
        assert "alerts" in result
        assert len(result["forecast"]) == 7
        
        # Check current weather structure
        current = result["current_weather"]
        assert "temperature" in current
        assert "humidity" in current
        assert "rainfall" in current
        assert "wind_speed" in current
        assert "conditions" in current
    
    def test_get_activity_timing_spraying(self, agent, sample_location):
        """Test getting activity timing for spraying."""
        result = agent.get_activity_timing(
            sample_location,
            activity="spraying",
            crop="tomato"
        )
        
        assert result["success"] is True
        assert result["query_type"] == "activity_timing"
        assert "activity_analysis" in result
        
        analysis = result["activity_analysis"]
        assert analysis["activity"] == "spraying"
        assert analysis["crop"] == "tomato"
        assert "optimal_days" in analysis
        assert "recommendations" in analysis
    
    def test_get_activity_timing_harvesting(self, agent, sample_location):
        """Test getting activity timing for harvesting."""
        result = agent.get_activity_timing(
            sample_location,
            activity="harvesting",
            crop="rice"
        )
        
        assert result["success"] is True
        assert "activity_analysis" in result
        
        analysis = result["activity_analysis"]
        assert analysis["activity"] == "harvesting"
        assert "optimal_days" in analysis
    
    def test_get_proactive_advice(self, agent, sample_location):
        """Test getting proactive advice for crop and growth stage."""
        result = agent.get_proactive_advice(
            sample_location,
            crop="tomato",
            growth_stage="flowering"
        )
        
        assert result["success"] is True
        assert result["query_type"] == "proactive_advice"
        assert "proactive_advice" in result
        
        advice = result["proactive_advice"]
        assert advice["crop"] == "tomato"
        assert advice["growth_stage"] == "flowering"
        assert "advice" in advice
        assert "priority" in advice
        assert len(advice["advice"]) > 0
    
    def test_adverse_weather_alerts(self, agent, sample_location):
        """Test that adverse weather conditions generate alerts."""
        result = agent.get_forecast(sample_location, days=7)
        
        assert result["success"] is True
        assert "alerts" in result
        # Alerts may or may not be present depending on weather conditions
        # Just verify the structure
        if result["alerts"]:
            alert = result["alerts"][0]
            assert "date" in alert
            assert "type" in alert
            assert "severity" in alert
            assert "message" in alert
            assert "precautions" in alert
    
    def test_invalid_location(self, agent):
        """Test handling of invalid location."""
        result = agent.get_forecast({}, days=7)
        
        assert result["success"] is False
        assert "error" in result
    
    def test_invalid_activity(self, agent, sample_location):
        """Test handling of invalid activity."""
        result = agent.get_activity_timing(
            sample_location,
            activity="invalid_activity"
        )
        
        assert result["success"] is False
        assert "error" in result
    
    def test_invalid_growth_stage(self, agent, sample_location):
        """Test handling of invalid growth stage."""
        result = agent.get_proactive_advice(
            sample_location,
            crop="tomato",
            growth_stage="invalid_stage"
        )
        
        assert result["success"] is False
        assert "error" in result
    
    def test_forecast_days_range(self, agent, sample_location):
        """Test forecast with different day ranges."""
        # Test 1 day
        result = agent.get_forecast(sample_location, days=1)
        assert result["success"] is True
        assert len(result["forecast"]) == 1
        
        # Test 14 days
        result = agent.get_forecast(sample_location, days=14)
        assert result["success"] is True
        assert len(result["forecast"]) == 14
    
    def test_crop_specific_advice(self, agent, sample_location):
        """Test that crop-specific advice is provided."""
        result = agent.get_activity_timing(
            sample_location,
            activity="irrigation",
            crop="rice"
        )
        
        assert result["success"] is True
        analysis = result["activity_analysis"]
        
        # Should have crop-specific advice if crop is provided
        if analysis.get("crop_specific_advice"):
            assert len(analysis["crop_specific_advice"]) > 0
    
    def test_specific_timing_advice(self, agent, sample_location):
        """Test that specific timing advice is provided (e.g., 'spray tomorrow morning')."""
        result = agent.get_activity_timing(
            sample_location,
            activity="spraying"
        )
        
        assert result["success"] is True
        analysis = result["activity_analysis"]
        
        # Check that recommendations include timing information
        recommendations = analysis["recommendations"]
        assert len(recommendations) > 0
        
        # At least one recommendation should mention timing
        has_timing = any(
            "morning" in rec.lower() or 
            "evening" in rec.lower() or 
            "afternoon" in rec.lower() or
            "time" in rec.lower()
            for rec in recommendations
        )
        assert has_timing or "no optimal conditions" in recommendations[0].lower()
    
    def test_weather_crop_integration(self, agent, sample_location):
        """Test that weather advice integrates with crop requirements."""
        result = agent.get_proactive_advice(
            sample_location,
            crop="tomato",
            growth_stage="seedling"
        )
        
        assert result["success"] is True
        advice_data = result["proactive_advice"]
        
        # Should have advice that considers both weather and crop stage
        assert "advice" in advice_data
        assert len(advice_data["advice"]) > 0
        
        # Should have weather summary
        assert "weather_summary" in advice_data
    
    def test_multiple_activities(self, agent, sample_location):
        """Test different farming activities."""
        activities = ["planting", "spraying", "harvesting", "irrigation", "fertilizing"]
        
        for activity in activities:
            result = agent.get_activity_timing(sample_location, activity=activity)
            assert result["success"] is True
            assert result["activity_analysis"]["activity"] == activity
    
    def test_multiple_growth_stages(self, agent, sample_location):
        """Test different growth stages."""
        stages = ["seedling", "vegetative", "flowering", "fruiting", "maturity"]
        
        for stage in stages:
            result = agent.get_proactive_advice(
                sample_location,
                crop="tomato",
                growth_stage=stage
            )
            assert result["success"] is True
            assert result["proactive_advice"]["growth_stage"] == stage
    
    def test_spray_tomorrow_morning_advice(self, agent, sample_location):
        """
        Test specific timing advice like 'spray tomorrow morning'.
        
        This test validates Requirement 4.4: hyper-local advice with specific timing.
        The agent should provide actionable timing recommendations with reasoning.
        """
        result = agent.get_activity_timing(
            sample_location,
            activity="spraying",
            crop="tomato"
        )
        
        assert result["success"] is True
        assert result["query_type"] == "activity_timing"
        assert "activity_analysis" in result
        
        analysis = result["activity_analysis"]
        assert analysis["activity"] == "spraying"
        
        # Verify optimal days are provided
        assert "optimal_days" in analysis
        optimal_days = analysis["optimal_days"]
        
        # Verify recommendations include specific timing
        assert "recommendations" in analysis
        recommendations = analysis["recommendations"]
        assert len(recommendations) > 0
        
        # If optimal conditions exist, verify timing specificity
        if optimal_days:
            first_optimal = optimal_days[0]
            
            # Should have date, timing, and reason
            assert "date" in first_optimal
            assert "timing" in first_optimal
            assert "reason" in first_optimal
            
            # Timing should be specific (mention time of day)
            timing = first_optimal["timing"].lower()
            assert any(
                time_word in timing 
                for time_word in ["morning", "evening", "afternoon", "am", "pm"]
            ), f"Timing should specify time of day, got: {first_optimal['timing']}"
            
            # Reason should explain why this timing is optimal
            reason = first_optimal["reason"]
            assert len(reason) > 10, "Reason should be descriptive"
            
            # First recommendation should mention the best time
            first_rec = recommendations[0].lower()
            assert "best time" in first_rec or "optimal" in first_rec
            
            # Should include date reference
            assert any(
                date_word in first_rec 
                for date_word in ["tomorrow", "today", first_optimal["date"]]
            )
        else:
            # If no optimal conditions, should explain why
            assert any(
                "no optimal" in rec.lower() or "wait" in rec.lower()
                for rec in recommendations
            )
