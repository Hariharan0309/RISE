"""
RISE Weather Data Tools
Tools for fetching and caching weather data with location-based retrieval.
Uses Open-Meteo free API (no API key required): https://open-meteo.com/
"""

import boto3
import logging
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
import requests
import os

logger = logging.getLogger(__name__)

# Open-Meteo uses WMO weather codes; map to short descriptions
_WMO_WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def _weather_code_to_description(code: int) -> str:
    """Convert Open-Meteo WMO weather code to description."""
    return _WMO_WEATHER_CODES.get(int(code), "Unknown")


class WeatherTools:
    """Weather data tools for RISE farming assistant with caching (Open-Meteo free API)."""
    
    def __init__(self, region: str = "us-east-1", api_key: Optional[str] = None):
        """
        Initialize weather tools with AWS clients.
        
        Args:
            region: AWS region for services (DynamoDB cache).
            api_key: Unused (kept for backward compatibility). Open-Meteo requires no key.
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        
        # DynamoDB table for weather forecast storage
        self.weather_table = self.dynamodb.Table('RISE-WeatherForecast')
        
        # Open-Meteo API (free, no API key)
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.api_key = api_key  # kept for backward compatibility; unused
        
        # Cache TTL: 6 hours
        self.cache_ttl = timedelta(hours=6)
        
        logger.info(f"Weather tools initialized in region {region} (Open-Meteo)")
    
    def get_current_weather(self,
                           latitude: float,
                           longitude: float,
                           location_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current weather for a location (Open-Meteo free API).
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            location_name: Optional location name for display
        
        Returns:
            Dict with current weather data
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(latitude, longitude, 'current')
            cached_data = self._get_from_cache(cache_key)
            
            if cached_data:
                logger.info(f"Cache hit for current weather at ({latitude}, {longitude})")
                return {
                    'success': True,
                    'from_cache': True,
                    **cached_data
                }
            
            # Open-Meteo: no API key required
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'current': 'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation',
                'timezone': 'auto',
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            cur = data.get('current', {})
            temp = cur.get('temperature_2m', 0)
            weather_data = {
                'location': {
                    'name': location_name or 'Unknown',
                    'latitude': latitude,
                    'longitude': longitude,
                    'country': 'IN'
                },
                'current': {
                    'temperature': temp,
                    'feels_like': temp,  # Open-Meteo doesn't provide; use same as temp
                    'temp_min': temp,
                    'temp_max': temp,
                    'pressure': 1013,
                    'humidity': cur.get('relative_humidity_2m', 0),
                    'weather': _weather_code_to_description(cur.get('weather_code', 0)),
                    'weather_description': _weather_code_to_description(cur.get('weather_code', 0)),
                    'weather_icon': str(cur.get('weather_code', 0)),
                    'wind_speed': cur.get('wind_speed_10m', 0),
                    'wind_direction': 0,
                    'clouds': 0,
                    'visibility': 10000,
                    'rain_1h': cur.get('precipitation', 0),
                    'rain_3h': 0
                },
                'sun': {'sunrise': '', 'sunset': ''},
                'timestamp': cur.get('time', datetime.now(timezone.utc).isoformat()),
                'timezone_offset': 19800
            }
            
            self._save_to_cache(cache_key, weather_data)
            return {'success': True, 'from_cache': False, **weather_data}
        
        except Exception as e:
            logger.error(f"Weather API error: {e}", exc_info=True)
            return {'success': False, 'error': f"Failed to fetch weather data: {str(e)}"}
    
    def get_forecast(self,
                    latitude: float,
                    longitude: float,
                    days: int = 5,
                    location_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get weather forecast for a location (Open-Meteo free API, up to 16 days).
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            days: Number of days for forecast
            location_name: Optional location name for display
        
        Returns:
            Dict with forecast data
        """
        try:
            cache_key = self._get_cache_key(latitude, longitude, f'forecast_{days}')
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                logger.info(f"Cache hit for forecast at ({latitude}, {longitude})")
                return {'success': True, 'from_cache': True, **cached_data}
            
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code',
                'timezone': 'auto',
                'forecast_days': min(days, 16),
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            daily = data.get('daily', {})
            times = daily.get('time', [])
            max_t = daily.get('temperature_2m_max', [])
            min_t = daily.get('temperature_2m_min', [])
            precip = daily.get('precipitation_sum', [])
            codes = daily.get('weather_code', [])
            
            daily_summary = []
            for i in range(len(times)):
                daily_summary.append({
                    'date': times[i],
                    'temp_min': min_t[i] if i < len(min_t) else 0,
                    'temp_max': max_t[i] if i < len(max_t) else 0,
                    'rain_total': precip[i] if i < len(precip) else 0,
                    'weather': _weather_code_to_description(codes[i] if i < len(codes) else 0),
                })
            
            forecast_data = {
                'location': {
                    'name': location_name or 'Unknown',
                    'latitude': latitude,
                    'longitude': longitude,
                    'country': 'IN'
                },
                'forecast': [],
                'daily_summary': daily_summary,
                'forecast_days': len(daily_summary),
                'total_forecasts': len(daily_summary),
            }
            self._save_to_cache(cache_key, forecast_data)
            return {'success': True, 'from_cache': False, **forecast_data}
        
        except Exception as e:
            logger.error(f"Forecast API error: {e}", exc_info=True)
            return {'success': False, 'error': f"Failed to fetch forecast data: {str(e)}"}
    
    def get_farming_weather_insights(self,
                                    latitude: float,
                                    longitude: float,
                                    location_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get weather insights relevant for farming activities
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            location_name: Optional location name
        
        Returns:
            Dict with farming-specific weather insights
        """
        try:
            # Get current weather and forecast
            current = self.get_current_weather(latitude, longitude, location_name)
            forecast = self.get_forecast(latitude, longitude, 5, location_name)
            
            if not current['success'] or not forecast['success']:
                return {
                    'success': False,
                    'error': 'Failed to fetch weather data for insights'
                }
            
            # Analyze weather for farming activities
            insights = {
                'location': current['location'],
                'current_conditions': current['current'],
                'farming_recommendations': self._generate_farming_recommendations(
                    current['current'],
                    forecast['daily_summary']
                ),
                'irrigation_advice': self._generate_irrigation_advice(
                    current['current'],
                    forecast['daily_summary']
                ),
                'adverse_weather_alerts': self._check_adverse_weather(
                    forecast['daily_summary']
                ),
                'optimal_activities': self._suggest_optimal_activities(
                    current['current'],
                    forecast['daily_summary']
                ),
                'next_48_hours': forecast['daily_summary'][:2] if len(forecast['daily_summary']) >= 2 else forecast['daily_summary']
            }
            
            return {
                'success': True,
                **insights
            }
        
        except Exception as e:
            logger.error(f"Farming insights error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_farming_recommendations(self,
                                         current: Dict[str, Any],
                                         forecast: List[Dict[str, Any]]) -> List[str]:
        """Generate farming recommendations based on weather"""
        recommendations = []
        
        # Temperature-based recommendations
        temp = current['temperature']
        if temp > 35:
            recommendations.append("High temperature alert: Avoid spraying pesticides during peak heat hours (11 AM - 3 PM)")
            recommendations.append("Ensure adequate irrigation to prevent heat stress in crops")
        elif temp < 10:
            recommendations.append("Low temperature alert: Protect sensitive crops from cold stress")
            recommendations.append("Consider covering young plants during night")
        
        # Humidity-based recommendations
        humidity = current['humidity']
        if humidity > 80:
            recommendations.append("High humidity: Increased risk of fungal diseases. Monitor crops closely")
            recommendations.append("Avoid irrigation if soil moisture is adequate")
        elif humidity < 30:
            recommendations.append("Low humidity: Increase irrigation frequency to prevent water stress")
        
        # Wind-based recommendations
        wind_speed = current['wind_speed']
        if wind_speed > 20:
            recommendations.append("High wind alert: Postpone spraying operations")
            recommendations.append("Secure lightweight structures and protect young plants")
        
        # Rain-based recommendations
        if current['rain_1h'] > 0 or current['rain_3h'] > 0:
            recommendations.append("Recent rainfall: Delay irrigation and fertilizer application")
            recommendations.append("Good time for transplanting if soil moisture is optimal")
        
        # Check forecast for rain
        rain_expected = any(day['rain_total'] > 2 for day in forecast[:3])
        if rain_expected:
            recommendations.append("Rain expected in next 3 days: Plan field activities accordingly")
            recommendations.append("Postpone fertilizer application until after rain")
        
        return recommendations
    
    def _generate_irrigation_advice(self,
                                   current: Dict[str, Any],
                                   forecast: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate irrigation advice based on weather"""
        
        # Calculate irrigation need score (0-10)
        score = 5  # Base score
        
        # Adjust based on temperature
        temp = current['temperature']
        if temp > 35:
            score += 2
        elif temp > 30:
            score += 1
        elif temp < 20:
            score -= 1
        
        # Adjust based on humidity
        humidity = current['humidity']
        if humidity < 40:
            score += 2
        elif humidity < 60:
            score += 1
        elif humidity > 80:
            score -= 2
        
        # Adjust based on recent rain
        if current['rain_1h'] > 0 or current['rain_3h'] > 0:
            score -= 3
        
        # Adjust based on forecast
        rain_next_2_days = sum(day['rain_total'] for day in forecast[:2])
        if rain_next_2_days > 10:
            score -= 2
        elif rain_next_2_days > 5:
            score -= 1
        
        # Clamp score
        score = max(0, min(10, score))
        
        # Generate advice
        if score >= 8:
            priority = "High"
            advice = "Irrigation strongly recommended today. Soil moisture likely low."
            timing = "Early morning (6-8 AM) or evening (5-7 PM)"
        elif score >= 6:
            priority = "Medium"
            advice = "Irrigation recommended if soil appears dry. Check soil moisture."
            timing = "Early morning or evening preferred"
        elif score >= 4:
            priority = "Low"
            advice = "Irrigation may not be necessary. Monitor soil moisture."
            timing = "Only if soil is visibly dry"
        else:
            priority = "Not Needed"
            advice = "Irrigation not recommended. Adequate moisture expected."
            timing = "Wait for soil to dry"
        
        return {
            'priority': priority,
            'score': score,
            'advice': advice,
            'optimal_timing': timing,
            'expected_rain_48h': rain_next_2_days
        }
    
    def _check_adverse_weather(self, forecast: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for adverse weather conditions"""
        alerts = []
        
        for i, day in enumerate(forecast[:5]):
            day_alerts = []
            
            # High temperature alert
            if day['temp_max'] > 40:
                day_alerts.append({
                    'type': 'extreme_heat',
                    'severity': 'high',
                    'message': f"Extreme heat expected: {day['temp_max']}°C"
                })
            
            # Low temperature alert
            if day['temp_min'] < 5:
                day_alerts.append({
                    'type': 'cold_wave',
                    'severity': 'high',
                    'message': f"Cold wave alert: {day['temp_min']}°C"
                })
            
            # Heavy rain alert
            if day['rain_total'] > 50:
                day_alerts.append({
                    'type': 'heavy_rain',
                    'severity': 'high',
                    'message': f"Heavy rainfall expected: {day['rain_total']}mm"
                })
            elif day['rain_total'] > 25:
                day_alerts.append({
                    'type': 'moderate_rain',
                    'severity': 'medium',
                    'message': f"Moderate rainfall expected: {day['rain_total']}mm"
                })
            
            if day_alerts:
                alerts.append({
                    'date': day['date'],
                    'day_number': i + 1,
                    'alerts': day_alerts
                })
        
        return alerts
    
    def _suggest_optimal_activities(self,
                                   current: Dict[str, Any],
                                   forecast: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Suggest optimal farming activities based on weather"""
        
        activities = {
            'recommended_today': [],
            'avoid_today': [],
            'plan_for_tomorrow': []
        }
        
        # Today's recommendations
        temp = current['temperature']
        humidity = current['humidity']
        wind = current['wind_speed']
        rain = current['rain_1h'] + current['rain_3h']
        
        if rain == 0 and wind < 10 and 20 <= temp <= 30:
            activities['recommended_today'].append("Spraying pesticides/fungicides")
            activities['recommended_today'].append("Fertilizer application")
        
        if rain == 0 and temp < 30:
            activities['recommended_today'].append("Field preparation and plowing")
            activities['recommended_today'].append("Weeding operations")
        
        if rain > 0 or humidity > 70:
            activities['recommended_today'].append("Transplanting seedlings")
        
        if wind > 15 or rain > 0:
            activities['avoid_today'].append("Spraying operations")
        
        if temp > 35:
            activities['avoid_today'].append("Heavy manual labor during midday")
        
        # Tomorrow's planning
        if len(forecast) > 0:
            tomorrow = forecast[0]
            if tomorrow['rain_total'] < 5 and tomorrow['temp_max'] < 35:
                activities['plan_for_tomorrow'].append("Good day for field activities")
            if tomorrow['rain_total'] > 10:
                activities['plan_for_tomorrow'].append("Expect rain - plan indoor activities")
        
        return activities
    
    def get_ai_weather_recommendations(self,
                                      latitude: float,
                                      longitude: float,
                                      location_name: Optional[str] = None,
                                      user_crops: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get AI-powered recommendations: optimal crops and farming processes suited to current
        and forecast weather for the user's location.
        """
        try:
            # Fetch current weather and forecast
            current_result = self.get_current_weather(latitude, longitude, location_name)
            forecast_result = self.get_forecast(latitude, longitude, 5)
            if not current_result.get('success'):
                return {'success': False, 'error': current_result.get('error', 'Failed to fetch weather')}
            if not forecast_result.get('success'):
                return {'success': False, 'error': forecast_result.get('error', 'Failed to fetch forecast')}
            
            current = current_result['current']
            loc_name = current_result.get('location', {}).get('name', location_name or 'this location')
            daily = forecast_result.get('daily_summary', [])[:5]
            weather_summary = (
                f"Current: {current['temperature']}°C, {current['weather_description']}, "
                f"Humidity {current['humidity']}%, Wind {current['wind_speed']} m/s, Rain (1h) {current['rain_1h']}mm. "
                f"Next 5 days: " + "; ".join(
                    f"{d['date']} {d['temp_min']}-{d['temp_max']}°C, {d['rain_total']}mm rain"
                    for d in daily
                )
            )
            crops_context = ""
            if user_crops:
                crops_context = f" The farmer currently grows or is interested in: {', '.join(user_crops)}."
            
            from config import Config
            prompt = f"""You are an agricultural advisor for Indian farmers. Based on the following weather data for {loc_name}, provide brief, actionable advice in plain language (2-4 short paragraphs).

Weather data:
{weather_summary}
{crops_context}

Provide:
1. **Optimal crops** – Which crops or varieties are best suited to plant or focus on in the current and upcoming weather (consider season and region).
2. **Optimal farming processes** – What to do now: e.g. irrigation, spraying, planting, harvesting, pest management, or what to avoid.
3. **Short-term tips** – Any specific actions for the next 3-5 days.

Keep the tone helpful and practical. Write in clear English. Do not use bullet points if you prefer flowing paragraphs."""

            body = {
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 800,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.3,
            }
            response = self.bedrock.invoke_model(
                modelId=Config.BEDROCK_MODEL_ID,
                body=json.dumps(body),
            )
            response_body = json.loads(response['body'].read())
            analysis_text = response_body['content'][0]['text'].strip()
            
            return {
                'success': True,
                'location': {'name': loc_name, 'latitude': latitude, 'longitude': longitude},
                'analysis': analysis_text,
                'weather_summary': weather_summary,
            }
        except Exception as e:
            logger.error(f"AI weather recommendations error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _get_cache_key(self, latitude: float, longitude: float, data_type: str) -> str:
        """Generate cache key for weather data"""
        # Round coordinates to 2 decimal places for cache efficiency
        lat_rounded = round(latitude, 2)
        lon_rounded = round(longitude, 2)
        content = f"{lat_rounded}:{lon_rounded}:{data_type}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve weather data from DynamoDB cache"""
        try:
            response = self.weather_table.get_item(Key={'cache_key': cache_key})
            
            if 'Item' in response:
                item = response['Item']
                expires_at = datetime.fromisoformat(item['expires_at'])
                
                if datetime.now() < expires_at:
                    logger.debug(f"Cache hit for key {cache_key}")
                    return json.loads(item['weather_data'])
                else:
                    # Delete expired cache entry
                    self.weather_table.delete_item(Key={'cache_key': cache_key})
                    logger.debug(f"Cache expired for key {cache_key}")
            
            return None
        
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
            return None
    
    def _save_to_cache(self, cache_key: str, weather_data: Dict[str, Any]):
        """Save weather data to DynamoDB cache"""
        try:
            expires_at = datetime.now() + self.cache_ttl
            ttl = int((expires_at + timedelta(days=1)).timestamp())  # DynamoDB TTL
            
            self.weather_table.put_item(
                Item={
                    'cache_key': cache_key,
                    'weather_data': json.dumps(weather_data),
                    'cached_at': datetime.now().isoformat(),
                    'expires_at': expires_at.isoformat(),
                    'ttl': ttl
                }
            )
            logger.debug(f"Cached weather data for key {cache_key}")
        
        except Exception as e:
            logger.warning(f"Cache save error: {e}")
    
    def clear_cache(self):
        """Clear all cached weather data"""
        try:
            # Scan and delete all items
            response = self.weather_table.scan()
            
            with self.weather_table.batch_writer() as batch:
                for item in response.get('Items', []):
                    batch.delete_item(Key={'cache_key': item['cache_key']})
            
            logger.info("Weather cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")


# Tool functions for agent integration (Strands @tool for orchestrator)
try:
    from strands import tool
except ImportError:
    def tool(fn):
        return fn  # no-op if Strands not installed

def create_weather_tools(region: str = "us-east-1", api_key: Optional[str] = None) -> WeatherTools:
    """
    Factory function to create weather tools instance (Open-Meteo, no API key required).
    
    Args:
        region: AWS region (for DynamoDB cache)
        api_key: Unused; kept for backward compatibility
    
    Returns:
        WeatherTools instance
    """
    return WeatherTools(region=region, api_key=api_key)


@tool
def get_current_weather_tool(latitude: float, longitude: float, location_name: Optional[str] = None) -> str:
    """
    Get current weather for a location. Use when the user asks about today's weather, temperature, rain, or conditions.
    Requires latitude and longitude (e.g. from user's farm or district).
    """
    tools = create_weather_tools()
    result = tools.get_current_weather(latitude, longitude, location_name)
    
    if result['success']:
        current = result['current']
        return f"""Current Weather at {result['location']['name']}:
Temperature: {current['temperature']}°C (feels like {current['feels_like']}°C)
Conditions: {current['weather_description']}
Humidity: {current['humidity']}%
Wind: {current['wind_speed']} m/s
Rain: {current['rain_1h']}mm (last hour)
"""
    else:
        return f"Error: {result.get('error', 'Failed to fetch weather')}"


@tool
def get_forecast_tool(latitude: float, longitude: float, days: int = 5) -> str:
    """
    Get weather forecast for the next few days. Use when the user asks about upcoming weather, rain, or planning farming by forecast.
    """
    tools = create_weather_tools()
    result = tools.get_forecast(latitude, longitude, days)
    
    if result['success']:
        summary = "Weather Forecast:\n"
        for day in result['daily_summary']:
            summary += f"\n{day['date']}: {day['temp_min']}-{day['temp_max']}°C, "
            summary += f"{day['weather']}, Rain: {day['rain_total']}mm"
        return summary
    else:
        return f"Error: {result.get('error', 'Failed to fetch forecast')}"


@tool
def get_farming_insights_tool(latitude: float, longitude: float) -> str:
    """
    Get farming-specific weather insights and recommendations (irrigation, planting, spraying). Use when the user asks for farming advice based on weather.
    """
    tools = create_weather_tools()
    result = tools.get_farming_weather_insights(latitude, longitude)
    
    if result['success']:
        insights = f"Farming Weather Insights for {result['location']['name']}:\n\n"
        
        insights += "Recommendations:\n"
        for rec in result['farming_recommendations'][:5]:
            insights += f"• {rec}\n"
        
        insights += f"\nIrrigation: {result['irrigation_advice']['priority']} priority\n"
        insights += f"{result['irrigation_advice']['advice']}\n"
        
        if result['adverse_weather_alerts']:
            insights += "\nWeather Alerts:\n"
            for alert in result['adverse_weather_alerts']:
                insights += f"• {alert['date']}: {len(alert['alerts'])} alert(s)\n"
        
        return insights
    else:
        return f"Error: {result.get('error', 'Failed to fetch insights')}"


@tool
def get_weather_ai_recommendations_tool(latitude: float, longitude: float,
                                        location_name: Optional[str] = None,
                                        user_crops: Optional[str] = None) -> str:
    """
    Get AI recommendations for optimal crops and farming processes based on current and forecast weather at this location. Use when the user asks what to grow, what to do now, or best crops/activities for the weather. user_crops: optional comma-separated list of crops they grow or are interested in.
    """
    tools = create_weather_tools()
    crops_list = [c.strip() for c in (user_crops or "").split(",") if c.strip()] or None
    result = tools.get_ai_weather_recommendations(latitude, longitude, location_name, crops_list)
    if result.get('success'):
        return result.get('analysis', '') or "No analysis generated."
    return f"Error: {result.get('error', 'Failed to get AI recommendations')}"
