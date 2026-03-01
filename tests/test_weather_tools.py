"""
Property-based tests for weather advisor tools.

Tests Properties 4 and 5 from the design document.
"""

import pytest
from hypothesis import given, strategies as st, assume
from tools.weather_tools import (
    get_weather_forecast,
    analyze_farming_conditions,
    check_adverse_conditions,
    generate_proactive_advice
)


# Helper strategies
@st.composite
def location_strategy(draw):
    """Generate valid location dictionaries."""
    districts = ["Bangalore", "Mysore", "Mandya", "Hassan", "Tumkur"]
    states = ["Karnataka", "Tamil Nadu", "Andhra Pradesh"]
    return {
        "district": draw(st.sampled_from(districts)),
        "state": draw(st.sampled_from(states))
    }


# Feature: missionai-farmer-agent, Property 4: Weather Forecast Completeness
@given(
    location=location_strategy(),
    days=st.integers(min_value=1, max_value=14)
)
@pytest.mark.property_test
def test_weather_forecast_completeness(location, days):
    """
    **Validates: Requirements 4.1**
    
    Property 4: Weather Forecast Completeness
    For any weather information request with valid location,
    the Weather_Advisor_Agent SHALL return both current weather
    conditions and a 7-day forecast.
    """
    result = get_weather_forecast(location, days)
    
    # Verify current weather is present
    assert "current_weather" in result, "Result must include current weather"
    current = result["current_weather"]
    
    # Verify all required current weather fields
    required_fields = ["temperature", "humidity", "rainfall", "wind_speed", "conditions"]
    for field in required_fields:
        assert field in current, f"Current weather must include {field}"
        assert current[field] is not None, f"{field} must not be None"
    
    # Verify forecast is present
    assert "forecast" in result, "Result must include forecast"
    forecast = result["forecast"]
    
    assert isinstance(forecast, list), "Forecast must be a list"
    assert len(forecast) == days, f"Forecast must contain {days} days"
    
    # Verify each forecast day has required fields
    for day in forecast:
        for field in required_fields:
            assert field in day, f"Each forecast day must include {field}"


# Feature: missionai-farmer-agent, Property 5: Weather-Crop Integration
@given(
    location=location_strategy(),
    activity=st.sampled_from(["planting", "spraying", "harvesting", "irrigation", "fertilizing"]),
    crop=st.sampled_from(["tomato", "rice", "wheat", "cotton", "potato"])
)
@pytest.mark.property_test
def test_weather_crop_integration(location, activity, crop):
    """
    **Validates: Requirements 4.5**
    
    Property 5: Weather-Crop Integration
    For any farming activity advice request, when weather data and
    crop type are available, the Weather_Advisor_Agent SHALL provide
    recommendations that consider both weather conditions and
    crop-specific requirements.
    """
    # Get weather data
    weather = get_weather_forecast(location, 7)
    
    # Analyze farming conditions with crop
    result = analyze_farming_conditions(weather, activity, crop)
    
    # Verify result includes both weather and crop considerations
    assert "activity" in result
    assert result["activity"] == activity
    
    assert "crop" in result
    assert result["crop"] == crop
    
    assert "recommendations" in result
    assert isinstance(result["recommendations"], list)
    assert len(result["recommendations"]) > 0, "Must provide at least one recommendation"
    
    # Verify crop-specific advice is present when crop is provided
    assert "crop_specific_advice" in result
    assert isinstance(result["crop_specific_advice"], list)


# Additional unit tests
def test_get_weather_forecast_invalid_location():
    """Test weather forecast with invalid location."""
    with pytest.raises(ValueError) as exc_info:
        get_weather_forecast({"district": "Bangalore"}, 7)  # Missing state
    assert "location" in str(exc_info.value).lower()


def test_get_weather_forecast_invalid_days():
    """Test weather forecast with invalid days."""
    location = {"district": "Bangalore", "state": "Karnataka"}
    
    with pytest.raises(ValueError) as exc_info:
        get_weather_forecast(location, 0)
    assert "days" in str(exc_info.value).lower()
    
    with pytest.raises(ValueError) as exc_info:
        get_weather_forecast(location, 20)
    assert "days" in str(exc_info.value).lower()


def test_analyze_farming_conditions_invalid_activity():
    """Test farming conditions with invalid activity."""
    location = {"district": "Bangalore", "state": "Karnataka"}
    weather = get_weather_forecast(location, 7)
    
    with pytest.raises(ValueError) as exc_info:
        analyze_farming_conditions(weather, "invalid_activity")
    assert "activity" in str(exc_info.value).lower()


def test_analyze_farming_conditions_spraying():
    """Test specific advice for spraying activity."""
    location = {"district": "Bangalore", "state": "Karnataka"}
    weather = get_weather_forecast(location, 7)
    
    result = analyze_farming_conditions(weather, "spraying", "tomato")
    
    assert result["activity"] == "spraying"
    assert "recommendations" in result
    assert "optimal_days" in result


def test_check_adverse_conditions_empty_forecast():
    """Test adverse conditions check with empty forecast."""
    with pytest.raises(ValueError) as exc_info:
        check_adverse_conditions([])
    assert "forecast" in str(exc_info.value).lower()


def test_check_adverse_conditions_extreme_heat():
    """Test adverse conditions detection for extreme heat."""
    forecast = [
        {
            "date": "2024-03-01",
            "temperature": 45.0,
            "humidity": 30.0,
            "rainfall": 0.0,
            "wind_speed": 10.0,
            "conditions": "sunny"
        }
    ]
    
    alerts = check_adverse_conditions(forecast)
    
    # Should detect heat wave
    assert len(alerts) > 0
    heat_alerts = [a for a in alerts if a["type"] == "heat_wave"]
    assert len(heat_alerts) > 0
    assert heat_alerts[0]["severity"] == "high"


def test_check_adverse_conditions_heavy_rain():
    """Test adverse conditions detection for heavy rain."""
    forecast = [
        {
            "date": "2024-03-01",
            "temperature": 28.0,
            "humidity": 90.0,
            "rainfall": 80.0,
            "wind_speed": 15.0,
            "conditions": "rainy"
        }
    ]
    
    alerts = check_adverse_conditions(forecast)
    
    # Should detect heavy rain
    assert len(alerts) > 0
    rain_alerts = [a for a in alerts if a["type"] == "heavy_rain"]
    assert len(rain_alerts) > 0
    assert "precautions" in rain_alerts[0]


def test_check_adverse_conditions_strong_wind():
    """Test adverse conditions detection for strong wind."""
    forecast = [
        {
            "date": "2024-03-01",
            "temperature": 30.0,
            "humidity": 60.0,
            "rainfall": 0.0,
            "wind_speed": 50.0,
            "conditions": "windy"
        }
    ]
    
    alerts = check_adverse_conditions(forecast)
    
    # Should detect strong wind
    assert len(alerts) > 0
    wind_alerts = [a for a in alerts if a["type"] == "strong_wind"]
    assert len(wind_alerts) > 0


def test_generate_proactive_advice_invalid_stage():
    """Test proactive advice with invalid growth stage."""
    location = {"district": "Bangalore", "state": "Karnataka"}
    weather = get_weather_forecast(location, 7)
    
    with pytest.raises(ValueError) as exc_info:
        generate_proactive_advice(weather, "tomato", "invalid_stage")
    assert "growth stage" in str(exc_info.value).lower()


def test_generate_proactive_advice_seedling():
    """Test proactive advice for seedling stage."""
    location = {"district": "Bangalore", "state": "Karnataka"}
    weather = get_weather_forecast(location, 7)
    
    result = generate_proactive_advice(weather, "tomato", "seedling")
    
    assert result["crop"] == "tomato"
    assert result["growth_stage"] == "seedling"
    assert "advice" in result
    assert isinstance(result["advice"], list)
    assert len(result["advice"]) > 0
    assert "priority" in result
    assert result["priority"] in ["low", "medium", "high"]


def test_generate_proactive_advice_flowering():
    """Test proactive advice for flowering stage."""
    location = {"district": "Bangalore", "state": "Karnataka"}
    weather = get_weather_forecast(location, 7)
    
    result = generate_proactive_advice(weather, "rice", "flowering")
    
    assert result["growth_stage"] == "flowering"
    assert "advice" in result
    # Flowering stage should have specific advice
    advice_text = " ".join(result["advice"]).lower()
    assert "flowering" in advice_text or "critical" in advice_text


def test_generate_proactive_advice_maturity():
    """Test proactive advice for maturity stage."""
    location = {"district": "Bangalore", "state": "Karnataka"}
    weather = get_weather_forecast(location, 7)
    
    result = generate_proactive_advice(weather, "wheat", "maturity")
    
    assert result["growth_stage"] == "maturity"
    assert "advice" in result
    # Maturity stage should mention harvest
    advice_text = " ".join(result["advice"]).lower()
    assert "harvest" in advice_text or "maturity" in advice_text


def test_analyze_farming_conditions_all_activities():
    """Test that all valid activities can be analyzed."""
    location = {"district": "Bangalore", "state": "Karnataka"}
    weather = get_weather_forecast(location, 7)
    
    activities = ["planting", "spraying", "harvesting", "irrigation", "fertilizing"]
    
    for activity in activities:
        result = analyze_farming_conditions(weather, activity)
        assert result["activity"] == activity
        assert "recommendations" in result
        assert "optimal_days" in result


def test_weather_forecast_location_preserved():
    """Test that location is preserved in weather forecast result."""
    location = {"district": "Mysore", "state": "Karnataka"}
    result = get_weather_forecast(location, 5)
    
    assert result["location"] == location
    assert result["forecast_days"] == 5
