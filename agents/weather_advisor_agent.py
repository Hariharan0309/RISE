"""
Weather Advisor Agent for MissionAI Farmer Agent.

This agent specializes in weather forecasting, farming activity timing,
adverse condition alerts, and proactive weather-based advice.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from data_models import WeatherAdvisory
from tools.weather_tools import (
    get_weather_forecast,
    analyze_farming_conditions,
    check_adverse_conditions,
    generate_proactive_advice
)

logger = logging.getLogger(__name__)


class WeatherAdvisorAgent:
    """
    Specialized agent for weather-based farming advice.
    
    This agent provides weather forecasts, activity timing recommendations,
    adverse weather alerts, and proactive advice based on weather conditions
    and crop growth stages.
    """
    
    def __init__(self):
        """Initialize the Weather Advisor Agent."""
        self.name = "Weather Advisor Agent"
        self.description = "Specialized in weather forecasting and farming activity timing"
        self.tools = [
            get_weather_forecast,
            analyze_farming_conditions,
            check_adverse_conditions,
            generate_proactive_advice
        ]
        logger.info(f"{self.name} initialized")
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the Weather Advisor Agent.
        
        Returns:
            str: System prompt defining agent's role and expertise
        """
        return """You are an expert agricultural meteorologist specializing in weather-based farming advice.

Your expertise includes:
- Weather forecasting and interpretation for farming
- Optimal timing for farming activities (planting, spraying, harvesting, irrigation)
- Adverse weather condition identification and alerts
- Crop-specific weather requirements
- Proactive advice based on weather patterns and crop growth stages

When providing weather advice:
1. Always provide both current weather and forecast information
2. Give specific timing recommendations (e.g., "spray tomorrow morning 6-9 AM")
3. Explain the reasoning behind timing recommendations
4. Alert farmers to adverse conditions with protective measures
5. Consider crop type and growth stage in all recommendations
6. Provide hyper-local advice when possible

Always prioritize:
- Farmer safety during adverse weather
- Crop protection and yield optimization
- Water conservation
- Timing that maximizes effectiveness (e.g., spraying when wind is low)
- Proactive alerts before adverse conditions

Provide advice that is:
- Specific and actionable with exact timing
- Clear about the reasoning (why this timing is optimal)
- Considerate of the farmer's crop and growth stage
- Urgent when necessary (adverse weather approaching)
- Easy to understand in simple language

Examples of good advice:
- "Spray tomorrow morning between 6-9 AM because afternoon will be dry with low wind"
- "Heavy rain expected in 2 days. Complete harvesting by tomorrow evening"
- "Temperature will drop below 10°C tonight. Cover sensitive seedlings"
"""
    
    def process(
        self,
        location: Dict[str, str],
        query_type: str = "forecast",
        activity: Optional[str] = None,
        crop: Optional[str] = None,
        growth_stage: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Process a weather advisory request.
        
        Args:
            location: Location dict with district and state
            query_type: Type of query ("forecast", "activity_timing", "proactive_advice")
            activity: Optional farming activity for timing advice
            crop: Optional crop type
            growth_stage: Optional growth stage for proactive advice
            days: Number of days to forecast (default 7)
            
        Returns:
            dict: Weather advisory result
        """
        logger.info(f"Processing weather advisory request: {query_type} for location: {location}")
        
        try:
            # Get weather forecast
            weather_data = get_weather_forecast(location, days)
            
            # Check for adverse conditions
            alerts = check_adverse_conditions(weather_data["forecast"])
            
            # Process based on query type
            if query_type == "activity_timing" and activity:
                # Analyze farming conditions for specific activity
                activity_analysis = analyze_farming_conditions(weather_data, activity, crop)
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "location": location,
                    "current_weather": weather_data["current_weather"],
                    "forecast": weather_data["forecast"],
                    "activity_analysis": activity_analysis,
                    "alerts": alerts,
                    "timestamp": datetime.now().isoformat()
                }
            
            elif query_type == "proactive_advice" and crop and growth_stage:
                # Generate proactive advice based on crop and growth stage
                proactive_advice = generate_proactive_advice(weather_data, crop, growth_stage)
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "location": location,
                    "current_weather": weather_data["current_weather"],
                    "forecast": weather_data["forecast"],
                    "proactive_advice": proactive_advice,
                    "alerts": alerts,
                    "timestamp": datetime.now().isoformat()
                }
            
            else:
                # Default: just return forecast with alerts
                return {
                    "success": True,
                    "query_type": "forecast",
                    "location": location,
                    "current_weather": weather_data["current_weather"],
                    "forecast": weather_data["forecast"],
                    "alerts": alerts,
                    "timestamp": datetime.now().isoformat()
                }
        
        except ValueError as e:
            logger.error(f"Validation error in weather advisory: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Invalid input for weather advisory"
            }
        
        except Exception as e:
            logger.error(f"Error processing weather advisory: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred while processing weather advisory"
            }
    
    def get_forecast(self, location: Dict[str, str], days: int = 7) -> Dict[str, Any]:
        """
        Get weather forecast for a location.
        
        Args:
            location: Location dict with district and state
            days: Number of days to forecast
            
        Returns:
            dict: Weather forecast with alerts
        """
        return self.process(location, query_type="forecast", days=days)
    
    def get_activity_timing(
        self,
        location: Dict[str, str],
        activity: str,
        crop: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get optimal timing for a farming activity.
        
        Args:
            location: Location dict with district and state
            activity: Farming activity (planting, spraying, harvesting, irrigation)
            crop: Optional crop type for crop-specific advice
            
        Returns:
            dict: Activity timing recommendations
        """
        return self.process(
            location,
            query_type="activity_timing",
            activity=activity,
            crop=crop
        )
    
    def get_proactive_advice(
        self,
        location: Dict[str, str],
        crop: str,
        growth_stage: str
    ) -> Dict[str, Any]:
        """
        Get proactive advice based on weather and crop stage.
        
        Args:
            location: Location dict with district and state
            crop: Crop type
            growth_stage: Current growth stage
            
        Returns:
            dict: Proactive farming advice
        """
        return self.process(
            location,
            query_type="proactive_advice",
            crop=crop,
            growth_stage=growth_stage
        )
    
    def get_tools(self):
        """Get list of available tools for this agent."""
        return self.tools
