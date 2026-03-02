"""
RISE Weather Data Tools
Tools for fetching and caching weather data with location-based retrieval
"""

import boto3
import logging
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
import os

logger = logging.getLogger(__name__)


class WeatherTools:
    """Weather data tools for RISE farming assistant with caching"""
    
    def __init__(self, region: str = "us-east-1", api_key: Optional[str] = None):
        """
        Initialize weather tools with AWS clients
        
        Args:
            region: AWS region for services
            api_key: OpenWeatherMap API key (or from environment)
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # DynamoDB table for weather forecast storage
        self.weather_table = self.dynamodb.Table('RISE-WeatherForecast')
        
        # OpenWeatherMap API configuration
        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY', '')
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
        # Cache TTL: 6 hours
        self.cache_ttl = timedelta(hours=6)
        
        logger.info(f"Weather tools initialized in region {region}")
    
    def get_current_weather(self,
                           latitude: float,
                           longitude: float,
                           location_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current weather for a location
        
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
            
            # Fetch from API
            url = f"{self.base_url}/weather"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'units': 'metric',  # Celsius
                'lang': 'en'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse weather data
            weather_data = {
                'location': {
                    'name': location_name or data.get('name', 'Unknown'),
                    'latitude': latitude,
                    'longitude': longitude,
                    'country': data.get('sys', {}).get('country', 'IN')
                },
                'current': {
                    'temperature': data['main']['temp'],
                    'feels_like': data['main']['feels_like'],
                    'temp_min': data['main']['temp_min'],
                    'temp_max': data['main']['temp_max'],
                    'pressure': data['main']['pressure'],
                    'humidity': data['main']['humidity'],
                    'weather': data['weather'][0]['main'],
                    'weather_description': data['weather'][0]['description'],
                    'weather_icon': data['weather'][0]['icon'],
                    'wind_speed': data['wind']['speed'],
                    'wind_direction': data['wind'].get('deg', 0),
                    'clouds': data['clouds']['all'],
                    'visibility': data.get('visibility', 10000),
                    'rain_1h': data.get('rain', {}).get('1h', 0),
                    'rain_3h': data.get('rain', {}).get('3h', 0)
                },
                'sun': {
                    'sunrise': datetime.fromtimestamp(data['sys']['sunrise']).isoformat(),
                    'sunset': datetime.fromtimestamp(data['sys']['sunset']).isoformat()
                },
                'timestamp': datetime.fromtimestamp(data['dt']).isoformat(),
                'timezone_offset': data.get('timezone', 19800)  # Default to IST
            }
            
            # Cache the result
            self._save_to_cache(cache_key, weather_data)
            
            return {
                'success': True,
                'from_cache': False,
                **weather_data
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Weather API error: {e}")
            return {
                'success': False,
                'error': f"Failed to fetch weather data: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Weather processing error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_forecast(self,
                    latitude: float,
                    longitude: float,
                    days: int = 5,
                    location_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get weather forecast for a location
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            days: Number of days for forecast (max 5 for free tier)
            location_name: Optional location name for display
        
        Returns:
            Dict with forecast data
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(latitude, longitude, f'forecast_{days}')
            cached_data = self._get_from_cache(cache_key)
            
            if cached_data:
                logger.info(f"Cache hit for forecast at ({latitude}, {longitude})")
                return {
                    'success': True,
                    'from_cache': True,
                    **cached_data
                }
            
            # Fetch from API
            url = f"{self.base_url}/forecast"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'en',
                'cnt': days * 8  # 8 forecasts per day (3-hour intervals)
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse forecast data
            forecast_list = []
            daily_summary = {}
            
            for item in data['list']:
                forecast_time = datetime.fromtimestamp(item['dt'])
                date_key = forecast_time.date().isoformat()
                
                forecast_item = {
                    'datetime': forecast_time.isoformat(),
                    'temperature': item['main']['temp'],
                    'feels_like': item['main']['feels_like'],
                    'temp_min': item['main']['temp_min'],
                    'temp_max': item['main']['temp_max'],
                    'pressure': item['main']['pressure'],
                    'humidity': item['main']['humidity'],
                    'weather': item['weather'][0]['main'],
                    'weather_description': item['weather'][0]['description'],
                    'weather_icon': item['weather'][0]['icon'],
                    'wind_speed': item['wind']['speed'],
                    'wind_direction': item['wind'].get('deg', 0),
                    'clouds': item['clouds']['all'],
                    'pop': item.get('pop', 0) * 100,  # Probability of precipitation
                    'rain_3h': item.get('rain', {}).get('3h', 0),
                    'visibility': item.get('visibility', 10000)
                }
                
                forecast_list.append(forecast_item)
                
                # Build daily summary
                if date_key not in daily_summary:
                    daily_summary[date_key] = {
                        'date': date_key,
                        'temp_min': item['main']['temp_min'],
                        'temp_max': item['main']['temp_max'],
                        'humidity_avg': item['main']['humidity'],
                        'rain_total': item.get('rain', {}).get('3h', 0),
                        'weather_conditions': [item['weather'][0]['main']],
                        'count': 1
                    }
                else:
                    daily_summary[date_key]['temp_min'] = min(
                        daily_summary[date_key]['temp_min'],
                        item['main']['temp_min']
                    )
                    daily_summary[date_key]['temp_max'] = max(
                        daily_summary[date_key]['temp_max'],
                        item['main']['temp_max']
                    )
                    daily_summary[date_key]['humidity_avg'] += item['main']['humidity']
                    daily_summary[date_key]['rain_total'] += item.get('rain', {}).get('3h', 0)
                    daily_summary[date_key]['weather_conditions'].append(item['weather'][0]['main'])
                    daily_summary[date_key]['count'] += 1
            
            # Calculate averages for daily summary
            for date_key in daily_summary:
                count = daily_summary[date_key]['count']
                daily_summary[date_key]['humidity_avg'] = round(
                    daily_summary[date_key]['humidity_avg'] / count
                )
                # Get most common weather condition
                conditions = daily_summary[date_key]['weather_conditions']
                daily_summary[date_key]['weather'] = max(set(conditions), key=conditions.count)
                del daily_summary[date_key]['weather_conditions']
                del daily_summary[date_key]['count']
            
            forecast_data = {
                'location': {
                    'name': location_name or data['city']['name'],
                    'latitude': latitude,
                    'longitude': longitude,
                    'country': data['city']['country']
                },
                'forecast': forecast_list,
                'daily_summary': list(daily_summary.values()),
                'forecast_days': days,
                'total_forecasts': len(forecast_list)
            }
            
            # Cache the result
            self._save_to_cache(cache_key, forecast_data)
            
            return {
                'success': True,
                'from_cache': False,
                **forecast_data
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Forecast API error: {e}")
            return {
                'success': False,
                'error': f"Failed to fetch forecast data: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Forecast processing error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
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


# Tool functions for agent integration

def create_weather_tools(region: str = "us-east-1", api_key: Optional[str] = None) -> WeatherTools:
    """
    Factory function to create weather tools instance
    
    Args:
        region: AWS region
        api_key: OpenWeatherMap API key
    
    Returns:
        WeatherTools instance
    """
    return WeatherTools(region=region, api_key=api_key)


def get_current_weather_tool(latitude: float, longitude: float, location_name: Optional[str] = None) -> str:
    """
    Tool for getting current weather
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        location_name: Optional location name
    
    Returns:
        Current weather information
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


def get_forecast_tool(latitude: float, longitude: float, days: int = 5) -> str:
    """
    Tool for getting weather forecast
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        days: Number of days
    
    Returns:
        Weather forecast information
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


def get_farming_insights_tool(latitude: float, longitude: float) -> str:
    """
    Tool for getting farming-specific weather insights
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
    
    Returns:
        Farming weather insights
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
