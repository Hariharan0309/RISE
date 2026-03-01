"""
Weather advisor tools for MissionAI Farmer Agent.

This module provides tools for weather forecasting, farming condition analysis,
and proactive weather-based advice.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random


# Mock weather data generator (would use real API in production)
def generate_mock_weather(location: Dict[str, str], days: int) -> List[Dict]:
    """Generate mock weather forecast data."""
    forecast = []
    base_temp = 28.0
    
    for i in range(days):
        date = datetime.now() + timedelta(days=i)
        
        # Add some variation
        temp_variation = random.uniform(-5, 5)
        humidity_variation = random.uniform(-10, 10)
        
        forecast.append({
            "date": date.strftime("%Y-%m-%d"),
            "temperature": round(base_temp + temp_variation, 1),
            "humidity": round(65 + humidity_variation, 1),
            "rainfall": round(random.uniform(0, 50), 1),
            "wind_speed": round(random.uniform(5, 25), 1),
            "conditions": random.choice(["sunny", "partly_cloudy", "cloudy", "rainy"])
        })
    
    return forecast


def get_weather_forecast(
    location: Dict[str, str],
    days: int = 7
) -> Dict:
    """
    Get weather forecast for a location.
    
    Args:
        location: Location dict with district and state
        days: Number of days to forecast (1-14)
    
    Returns:
        Dictionary with current weather and forecast
    
    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    if not location or not isinstance(location, dict):
        raise ValueError("Location must be a dictionary")
    if "district" not in location or "state" not in location:
        raise ValueError("Location must contain 'district' and 'state' fields")
    if days < 1 or days > 14:
        raise ValueError("Days must be between 1 and 14")
    
    # Generate forecast (mock data)
    forecast = generate_mock_weather(location, days)
    
    # Current weather is first day
    current = forecast[0]
    
    return {
        "location": location,
        "current_weather": {
            "temperature": current["temperature"],
            "humidity": current["humidity"],
            "rainfall": current["rainfall"],
            "wind_speed": current["wind_speed"],
            "conditions": current["conditions"]
        },
        "forecast": forecast,
        "forecast_days": days,
        "last_updated": datetime.now().isoformat()
    }


def analyze_farming_conditions(
    weather: Dict,
    activity: str,
    crop: Optional[str] = None
) -> Dict:
    """
    Analyze weather conditions for farming activities.
    
    Args:
        weather: Weather data from get_weather_forecast
        activity: Farming activity (planting, spraying, harvesting, irrigation)
        crop: Optional crop type for crop-specific advice
    
    Returns:
        Dictionary with activity timing recommendations
    
    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    if not weather or not isinstance(weather, dict):
        raise ValueError("Weather must be a dictionary")
    if "current_weather" not in weather or "forecast" not in weather:
        raise ValueError("Weather must contain 'current_weather' and 'forecast' fields")
    if not activity or not isinstance(activity, str):
        raise ValueError("Activity must be a non-empty string")
    
    valid_activities = ["planting", "spraying", "harvesting", "irrigation", "fertilizing"]
    if activity.lower() not in valid_activities:
        raise ValueError(f"Activity must be one of: {', '.join(valid_activities)}")
    
    activity_lower = activity.lower()
    forecast = weather["forecast"]
    
    # Analyze conditions for activity
    recommendations = []
    optimal_days = []
    
    for day_data in forecast[:7]:  # Analyze next 7 days
        date = day_data["date"]
        temp = day_data["temperature"]
        humidity = day_data["humidity"]
        rainfall = day_data["rainfall"]
        wind = day_data["wind_speed"]
        conditions = day_data["conditions"]
        
        # Activity-specific analysis
        if activity_lower == "spraying":
            # Good for spraying: low wind, no rain, moderate temp
            if wind < 15 and rainfall < 2 and 20 <= temp <= 35:
                optimal_days.append({
                    "date": date,
                    "timing": "early morning (6-9 AM) or evening (4-6 PM)",
                    "reason": "Low wind and no rain expected"
                })
        
        elif activity_lower == "planting":
            # Good for planting: adequate moisture, moderate temp
            if rainfall > 5 or humidity > 70:
                optimal_days.append({
                    "date": date,
                    "timing": "morning (8-11 AM)",
                    "reason": "Good soil moisture conditions"
                })
        
        elif activity_lower == "harvesting":
            # Good for harvesting: dry conditions, low humidity
            if rainfall < 1 and humidity < 70 and conditions in ["sunny", "partly_cloudy"]:
                optimal_days.append({
                    "date": date,
                    "timing": "late morning to afternoon (10 AM - 4 PM)",
                    "reason": "Dry conditions ideal for harvesting"
                })
        
        elif activity_lower == "irrigation":
            # Need irrigation: low rainfall, high temp
            if rainfall < 2 and temp > 30:
                optimal_days.append({
                    "date": date,
                    "timing": "early morning (5-8 AM) or evening (5-7 PM)",
                    "reason": "Low rainfall and high temperature"
                })
        
        elif activity_lower == "fertilizing":
            # Good for fertilizing: before rain, moderate conditions
            if 2 < rainfall < 20 and temp < 35:
                optimal_days.append({
                    "date": date,
                    "timing": "before rainfall",
                    "reason": "Rain will help nutrients penetrate soil"
                })
    
    # Generate recommendations
    if optimal_days:
        best_day = optimal_days[0]
        recommendations.append(f"Best time: {best_day['date']} {best_day['timing']}")
        recommendations.append(f"Reason: {best_day['reason']}")
    else:
        recommendations.append(f"No optimal conditions in next 7 days for {activity}")
        recommendations.append("Monitor weather and wait for better conditions")
    
    # Crop-specific advice
    crop_advice = []
    if crop:
        crop_lower = crop.lower()
        if crop_lower in ["tomato", "potato", "chilli"]:
            crop_advice.append(f"{crop} is sensitive to excessive moisture")
        elif crop_lower in ["rice", "sugarcane"]:
            crop_advice.append(f"{crop} requires consistent water supply")
    
    return {
        "activity": activity,
        "crop": crop,
        "optimal_days": optimal_days,
        "recommendations": recommendations,
        "crop_specific_advice": crop_advice,
        "analyzed_period": f"Next {len(forecast)} days"
    }


def check_adverse_conditions(forecast: List[Dict]) -> List[Dict]:
    """
    Check for adverse weather conditions in forecast.
    
    Args:
        forecast: List of forecast day dictionaries
    
    Returns:
        List of alerts for adverse conditions
    
    Raises:
        ValueError: If forecast is invalid
    """
    # Input validation
    if not forecast or not isinstance(forecast, list):
        raise ValueError("Forecast must be a non-empty list")
    
    alerts = []
    
    for day_data in forecast:
        date = day_data["date"]
        temp = day_data["temperature"]
        rainfall = day_data["rainfall"]
        wind = day_data["wind_speed"]
        
        # Check for extreme conditions
        if temp > 40:
            alerts.append({
                "date": date,
                "type": "heat_wave",
                "severity": "high",
                "message": f"Extreme heat expected ({temp}°C). Increase irrigation and provide shade.",
                "precautions": [
                    "Increase irrigation frequency",
                    "Mulch soil to retain moisture",
                    "Avoid working during peak heat hours"
                ]
            })
        
        if temp < 10:
            alerts.append({
                "date": date,
                "type": "cold_wave",
                "severity": "medium",
                "message": f"Cold conditions expected ({temp}°C). Protect sensitive crops.",
                "precautions": [
                    "Cover sensitive plants",
                    "Delay planting of warm-season crops",
                    "Protect young seedlings"
                ]
            })
        
        if rainfall > 50:
            alerts.append({
                "date": date,
                "type": "heavy_rain",
                "severity": "high",
                "message": f"Heavy rainfall expected ({rainfall}mm). Risk of waterlogging.",
                "precautions": [
                    "Ensure proper drainage",
                    "Postpone spraying activities",
                    "Protect harvested produce",
                    "Check for pest outbreaks after rain"
                ]
            })
        
        if wind > 40:
            alerts.append({
                "date": date,
                "type": "strong_wind",
                "severity": "medium",
                "message": f"Strong winds expected ({wind} km/h). Risk of crop damage.",
                "precautions": [
                    "Stake tall plants",
                    "Avoid spraying",
                    "Secure farm structures",
                    "Harvest ripe produce"
                ]
            })
    
    return alerts


def generate_proactive_advice(
    weather: Dict,
    crop: str,
    growth_stage: str
) -> Dict:
    """
    Generate proactive farming advice based on weather and crop stage.
    
    Args:
        weather: Weather data from get_weather_forecast
        crop: Crop type
        growth_stage: Current growth stage (seedling, vegetative, flowering, fruiting, maturity)
    
    Returns:
        Dictionary with proactive advice
    
    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    if not weather or not isinstance(weather, dict):
        raise ValueError("Weather must be a dictionary")
    if not crop or not isinstance(crop, str):
        raise ValueError("Crop must be a non-empty string")
    if not growth_stage or not isinstance(growth_stage, str):
        raise ValueError("Growth stage must be a non-empty string")
    
    valid_stages = ["seedling", "vegetative", "flowering", "fruiting", "maturity"]
    if growth_stage.lower() not in valid_stages:
        raise ValueError(f"Growth stage must be one of: {', '.join(valid_stages)}")
    
    current = weather["current_weather"]
    forecast = weather["forecast"]
    
    advice = []
    priority = "medium"
    
    # Stage-specific advice
    stage_lower = growth_stage.lower()
    
    if stage_lower == "seedling":
        advice.append("Seedling stage requires consistent moisture")
        if current["rainfall"] < 5:
            advice.append("Irrigate daily in morning hours")
            priority = "high"
    
    elif stage_lower == "flowering":
        advice.append("Flowering stage is critical for yield")
        if current["temperature"] > 35:
            advice.append("High temperature may affect pollination. Consider light irrigation.")
            priority = "high"
        if current["rainfall"] > 20:
            advice.append("Heavy rain may damage flowers. Ensure drainage.")
            priority = "high"
    
    elif stage_lower == "fruiting":
        advice.append("Fruiting stage requires balanced water and nutrients")
        if current["humidity"] > 80:
            advice.append("High humidity increases disease risk. Monitor for fungal infections.")
            priority = "medium"
    
    elif stage_lower == "maturity":
        advice.append("Crop is nearing harvest")
        if current["rainfall"] < 2 and current["conditions"] in ["sunny", "partly_cloudy"]:
            advice.append("Good conditions for harvesting in next 2-3 days")
            priority = "high"
    
    # Weather-based advice
    upcoming_rain = sum(1 for d in forecast[:3] if d["rainfall"] > 10)
    if upcoming_rain >= 2:
        advice.append("Heavy rain expected in next 3 days. Complete urgent field work now.")
        priority = "high"
    
    return {
        "crop": crop,
        "growth_stage": growth_stage,
        "advice": advice,
        "priority": priority,
        "weather_summary": f"Current: {current['conditions']}, Temp: {current['temperature']}°C",
        "generated_at": datetime.now().isoformat()
    }
