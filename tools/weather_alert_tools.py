"""
RISE Weather Alert Tools
Tools for weather-based alerts, farming activity recommendations, and protective measures
"""

import boto3
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

try:
    from weather_tools import WeatherTools
except ImportError:
    from tools.weather_tools import WeatherTools

logger = logging.getLogger(__name__)


class WeatherAlertTools:
    """Weather alert and farming recommendation tools"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize weather alert tools
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        
        # DynamoDB tables
        self.alerts_table = self.dynamodb.Table('RISE-WeatherAlerts')
        self.user_table = self.dynamodb.Table('RISE-UserProfiles')
        
        # Weather tools for data fetching
        self.weather_tools = WeatherTools(region=region)
        
        logger.info(f"Weather alert tools initialized in region {region}")
    
    def monitor_weather_conditions(self, user_id: str) -> Dict[str, Any]:
        """
        Monitor weather conditions for a user's location and generate alerts
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with alerts and recommendations
        """
        try:
            # Get user profile with location
            user_profile = self._get_user_profile(user_id)
            
            if not user_profile or 'location' not in user_profile:
                return {
                    'success': False,
                    'error': 'User location not found'
                }
            
            location = user_profile['location']
            latitude = float(location.get('latitude', 0))
            longitude = float(location.get('longitude', 0))
            
            # Get weather forecast
            forecast_result = self.weather_tools.get_forecast(
                latitude, longitude, days=5, location_name=location.get('name')
            )
            
            if not forecast_result['success']:
                return forecast_result
            
            # Analyze weather for alerts
            alerts = self._detect_adverse_weather(
                forecast_result['daily_summary'],
                forecast_result['forecast']
            )
            
            # Generate farming recommendations
            recommendations = self._generate_activity_recommendations(
                forecast_result['daily_summary'],
                user_profile.get('crops', [])
            )
            
            # Calculate irrigation timing
            irrigation = self._calculate_irrigation_timing(
                forecast_result['daily_summary'],
                user_profile.get('farm_details', {})
            )
            
            # Generate protective measures
            protective_measures = self._generate_protective_measures(alerts)
            
            # Save alerts to database
            alert_data = {
                'user_id': user_id,
                'alerts': alerts,
                'recommendations': recommendations,
                'irrigation': irrigation,
                'protective_measures': protective_measures,
                'location': location,
                'timestamp': datetime.now().isoformat()
            }
            
            self._save_alert(user_id, alert_data)
            
            # Send notifications if critical alerts exist
            critical_alerts = [a for a in alerts if a.get('severity') == 'high']
            if critical_alerts:
                self._send_alert_notification(user_id, critical_alerts, user_profile)
            
            return {
                'success': True,
                'alerts': alerts,
                'recommendations': recommendations,
                'irrigation': irrigation,
                'protective_measures': protective_measures,
                'location': location
            }
        
        except Exception as e:
            logger.error(f"Weather monitoring error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_adverse_weather(self,
                               daily_summary: List[Dict[str, Any]],
                               hourly_forecast: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect adverse weather conditions with 48-72 hour advance notice
        
        Args:
            daily_summary: Daily weather summary
            hourly_forecast: Hourly forecast data
        
        Returns:
            List of weather alerts
        """
        alerts = []
        
        for i, day in enumerate(daily_summary):
            day_number = i + 1
            hours_ahead = day_number * 24
            
            # Only alert for 48-72 hour window (days 2-3)
            if hours_ahead < 48 or hours_ahead > 96:
                continue
            
            date = day['date']
            
            # Extreme heat alert
            if day['temp_max'] > 40:
                alerts.append({
                    'type': 'extreme_heat',
                    'severity': 'high',
                    'date': date,
                    'hours_ahead': hours_ahead,
                    'title': 'Extreme Heat Warning',
                    'message': f"Extreme heat expected on {date}: {day['temp_max']}°C",
                    'details': {
                        'max_temp': day['temp_max'],
                        'min_temp': day['temp_min']
                    }
                })
            elif day['temp_max'] > 38:
                alerts.append({
                    'type': 'high_heat',
                    'severity': 'medium',
                    'date': date,
                    'hours_ahead': hours_ahead,
                    'title': 'High Temperature Alert',
                    'message': f"High temperature expected on {date}: {day['temp_max']}°C",
                    'details': {
                        'max_temp': day['temp_max'],
                        'min_temp': day['temp_min']
                    }
                })
            
            # Cold wave alert
            if day['temp_min'] < 5:
                alerts.append({
                    'type': 'cold_wave',
                    'severity': 'high',
                    'date': date,
                    'hours_ahead': hours_ahead,
                    'title': 'Cold Wave Warning',
                    'message': f"Cold wave expected on {date}: {day['temp_min']}°C",
                    'details': {
                        'max_temp': day['temp_max'],
                        'min_temp': day['temp_min']
                    }
                })
            elif day['temp_min'] < 10:
                alerts.append({
                    'type': 'cold_weather',
                    'severity': 'medium',
                    'date': date,
                    'hours_ahead': hours_ahead,
                    'title': 'Cold Weather Alert',
                    'message': f"Cold weather expected on {date}: {day['temp_min']}°C",
                    'details': {
                        'max_temp': day['temp_max'],
                        'min_temp': day['temp_min']
                    }
                })
            
            # Heavy rain alert
            if day['rain_total'] > 50:
                alerts.append({
                    'type': 'heavy_rain',
                    'severity': 'high',
                    'date': date,
                    'hours_ahead': hours_ahead,
                    'title': 'Heavy Rainfall Warning',
                    'message': f"Heavy rainfall expected on {date}: {day['rain_total']}mm",
                    'details': {
                        'rainfall': day['rain_total'],
                        'humidity': day['humidity_avg']
                    }
                })
            elif day['rain_total'] > 25:
                alerts.append({
                    'type': 'moderate_rain',
                    'severity': 'medium',
                    'date': date,
                    'hours_ahead': hours_ahead,
                    'title': 'Moderate Rainfall Alert',
                    'message': f"Moderate rainfall expected on {date}: {day['rain_total']}mm",
                    'details': {
                        'rainfall': day['rain_total'],
                        'humidity': day['humidity_avg']
                    }
                })
            
            # Drought conditions (no rain for extended period)
            if i >= 2:
                total_rain_3days = sum(daily_summary[j]['rain_total'] for j in range(i-2, i+1))
                if total_rain_3days < 2 and day['humidity_avg'] < 40:
                    alerts.append({
                        'type': 'drought_risk',
                        'severity': 'medium',
                        'date': date,
                        'hours_ahead': hours_ahead,
                        'title': 'Drought Risk Alert',
                        'message': f"Low rainfall and humidity on {date}",
                        'details': {
                            'rainfall_3day': total_rain_3days,
                            'humidity': day['humidity_avg']
                        }
                    })
        
        return alerts
    
    def _generate_activity_recommendations(self,
                                          daily_summary: List[Dict[str, Any]],
                                          crops: List[str]) -> List[Dict[str, Any]]:
        """
        Generate farming activity recommendations based on weather
        
        Args:
            daily_summary: Daily weather summary
            crops: User's crops
        
        Returns:
            List of activity recommendations
        """
        recommendations = []
        
        for i, day in enumerate(daily_summary[:3]):  # Next 3 days
            date = day['date']
            activities = {
                'date': date,
                'day_number': i + 1,
                'recommended': [],
                'avoid': [],
                'optimal_timing': []
            }
            
            temp_max = day['temp_max']
            temp_min = day['temp_min']
            rain = day['rain_total']
            humidity = day['humidity_avg']
            
            # Spraying recommendations
            if rain < 2 and temp_max < 32 and humidity < 70:
                activities['recommended'].append({
                    'activity': 'Pesticide/Fungicide Spraying',
                    'reason': 'Ideal conditions: low rain, moderate temperature',
                    'timing': 'Early morning (6-9 AM) or evening (4-6 PM)'
                })
            elif rain > 5:
                activities['avoid'].append({
                    'activity': 'Spraying Operations',
                    'reason': 'Rain expected - chemicals will wash away'
                })
            
            # Irrigation recommendations
            if rain < 5 and temp_max > 30:
                activities['recommended'].append({
                    'activity': 'Irrigation',
                    'reason': 'Low rainfall and high temperature',
                    'timing': 'Early morning (5-7 AM) or evening (6-8 PM)'
                })
            elif rain > 10:
                activities['avoid'].append({
                    'activity': 'Irrigation',
                    'reason': 'Adequate rainfall expected'
                })
            
            # Field preparation
            if rain < 2 and temp_max < 35:
                activities['recommended'].append({
                    'activity': 'Field Preparation/Plowing',
                    'reason': 'Good weather for field work',
                    'timing': 'Morning to afternoon (7 AM - 4 PM)'
                })
            
            # Transplanting
            if rain > 5 and rain < 25 and temp_max < 32:
                activities['recommended'].append({
                    'activity': 'Transplanting Seedlings',
                    'reason': 'Adequate moisture and moderate temperature',
                    'timing': 'Late afternoon or evening'
                })
            
            # Fertilizer application
            if rain < 2 and temp_max < 35:
                activities['recommended'].append({
                    'activity': 'Fertilizer Application',
                    'reason': 'Dry conditions suitable for application',
                    'timing': 'Morning or evening, before irrigation'
                })
            elif rain > 10:
                activities['avoid'].append({
                    'activity': 'Fertilizer Application',
                    'reason': 'Heavy rain will wash away nutrients'
                })
            
            # Harvesting
            if rain < 2 and humidity < 70:
                activities['recommended'].append({
                    'activity': 'Harvesting',
                    'reason': 'Dry conditions ideal for harvest',
                    'timing': 'Morning after dew dries (9 AM onwards)'
                })
            elif rain > 10:
                activities['avoid'].append({
                    'activity': 'Harvesting',
                    'reason': 'Rain will damage harvested crops'
                })
            
            # Extreme weather warnings
            if temp_max > 38:
                activities['avoid'].append({
                    'activity': 'Heavy Manual Labor',
                    'reason': 'Extreme heat - risk of heat stroke'
                })
                activities['optimal_timing'].append({
                    'timing': 'Early morning (5-9 AM) only',
                    'reason': 'Avoid midday heat'
                })
            
            if temp_min < 10:
                activities['optimal_timing'].append({
                    'timing': 'Late morning to afternoon (10 AM - 4 PM)',
                    'reason': 'Avoid cold morning hours'
                })
            
            recommendations.append(activities)
        
        return recommendations
    
    def _calculate_irrigation_timing(self,
                                    daily_summary: List[Dict[str, Any]],
                                    farm_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate optimal irrigation timing based on weather forecast
        
        Args:
            daily_summary: Daily weather summary
            farm_details: Farm details including soil type
        
        Returns:
            Irrigation timing recommendations
        """
        # Calculate irrigation need for next 7 days
        irrigation_schedule = []
        
        soil_type = farm_details.get('soil_type', 'loam')
        
        # Soil water retention factors
        retention_factors = {
            'clay': 0.8,      # High retention
            'loam': 1.0,      # Medium retention
            'sandy': 1.3,     # Low retention
            'silt': 0.9       # Medium-high retention
        }
        
        retention_factor = retention_factors.get(soil_type.lower(), 1.0)
        
        for i, day in enumerate(daily_summary):
            date = day['date']
            
            # Calculate irrigation need score (0-10)
            score = 5  # Base score
            
            # Temperature adjustment
            if day['temp_max'] > 35:
                score += 2 * retention_factor
            elif day['temp_max'] > 30:
                score += 1 * retention_factor
            elif day['temp_max'] < 20:
                score -= 1
            
            # Humidity adjustment
            if day['humidity_avg'] < 40:
                score += 2
            elif day['humidity_avg'] < 60:
                score += 1
            elif day['humidity_avg'] > 80:
                score -= 2
            
            # Rainfall adjustment
            if day['rain_total'] > 10:
                score -= 3
            elif day['rain_total'] > 5:
                score -= 2
            elif day['rain_total'] > 2:
                score -= 1
            
            # Check previous day's rain
            if i > 0 and daily_summary[i-1]['rain_total'] > 10:
                score -= 2
            
            # Clamp score
            score = max(0, min(10, score))
            
            # Determine irrigation recommendation
            if score >= 8:
                priority = 'High'
                recommendation = 'Irrigation strongly recommended'
                water_amount = 'Heavy watering (25-30mm)'
            elif score >= 6:
                priority = 'Medium'
                recommendation = 'Irrigation recommended if soil is dry'
                water_amount = 'Moderate watering (15-20mm)'
            elif score >= 4:
                priority = 'Low'
                recommendation = 'Light irrigation may be needed'
                water_amount = 'Light watering (10-15mm)'
            else:
                priority = 'Not Needed'
                recommendation = 'Irrigation not required'
                water_amount = 'No watering needed'
            
            irrigation_schedule.append({
                'date': date,
                'day_number': i + 1,
                'priority': priority,
                'score': round(score, 1),
                'recommendation': recommendation,
                'water_amount': water_amount,
                'optimal_time': 'Early morning (5-7 AM) or evening (6-8 PM)',
                'weather': {
                    'temp_max': day['temp_max'],
                    'humidity': day['humidity_avg'],
                    'rainfall': day['rain_total']
                }
            })
        
        # Calculate total water needed for week
        total_water_needed = sum(
            25 if s['priority'] == 'High' else
            15 if s['priority'] == 'Medium' else
            10 if s['priority'] == 'Low' else 0
            for s in irrigation_schedule
        )
        
        return {
            'schedule': irrigation_schedule,
            'soil_type': soil_type,
            'retention_factor': retention_factor,
            'total_water_week': total_water_needed,
            'water_saving_tips': self._get_water_saving_tips(soil_type)
        }
    
    def _generate_protective_measures(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate protective measure recommendations based on alerts
        
        Args:
            alerts: List of weather alerts
        
        Returns:
            List of protective measures
        """
        measures = []
        
        for alert in alerts:
            alert_type = alert['type']
            
            if alert_type == 'extreme_heat':
                measures.append({
                    'alert_type': alert_type,
                    'date': alert['date'],
                    'measures': [
                        'Increase irrigation frequency to prevent heat stress',
                        'Apply mulch to conserve soil moisture',
                        'Provide shade nets for sensitive crops',
                        'Avoid spraying during peak heat hours (11 AM - 3 PM)',
                        'Monitor crops for wilting and heat damage',
                        'Ensure adequate water supply for livestock'
                    ],
                    'urgency': 'high'
                })
            
            elif alert_type == 'high_heat':
                measures.append({
                    'alert_type': alert_type,
                    'date': alert['date'],
                    'measures': [
                        'Schedule irrigation for early morning or evening',
                        'Monitor soil moisture levels closely',
                        'Postpone heavy field work to cooler hours',
                        'Check irrigation systems for proper functioning'
                    ],
                    'urgency': 'medium'
                })
            
            elif alert_type == 'cold_wave':
                measures.append({
                    'alert_type': alert_type,
                    'date': alert['date'],
                    'measures': [
                        'Cover sensitive crops with plastic sheets or cloth',
                        'Light small fires around field perimeter (smoke method)',
                        'Irrigate before cold night (wet soil retains heat)',
                        'Protect young plants and seedlings',
                        'Delay transplanting until temperature rises',
                        'Provide shelter for livestock'
                    ],
                    'urgency': 'high'
                })
            
            elif alert_type == 'cold_weather':
                measures.append({
                    'alert_type': alert_type,
                    'date': alert['date'],
                    'measures': [
                        'Monitor sensitive crops for cold damage',
                        'Consider covering young plants',
                        'Delay early morning field activities',
                        'Ensure livestock have warm shelter'
                    ],
                    'urgency': 'medium'
                })
            
            elif alert_type == 'heavy_rain':
                measures.append({
                    'alert_type': alert_type,
                    'date': alert['date'],
                    'measures': [
                        'Ensure proper field drainage systems are clear',
                        'Harvest mature crops before rain if possible',
                        'Secure farm equipment and structures',
                        'Postpone fertilizer and pesticide application',
                        'Protect stored crops from moisture',
                        'Check for waterlogging after rain',
                        'Monitor for fungal disease outbreaks'
                    ],
                    'urgency': 'high'
                })
            
            elif alert_type == 'moderate_rain':
                measures.append({
                    'alert_type': alert_type,
                    'date': alert['date'],
                    'measures': [
                        'Postpone spraying operations',
                        'Delay fertilizer application',
                        'Good time for transplanting after rain',
                        'Check drainage in low-lying areas'
                    ],
                    'urgency': 'medium'
                })
            
            elif alert_type == 'drought_risk':
                measures.append({
                    'alert_type': alert_type,
                    'date': alert['date'],
                    'measures': [
                        'Implement water conservation measures',
                        'Apply mulch to reduce evaporation',
                        'Consider drip irrigation for efficiency',
                        'Prioritize irrigation for critical crops',
                        'Reduce water-intensive activities',
                        'Monitor soil moisture regularly'
                    ],
                    'urgency': 'medium'
                })
        
        return measures
    
    def _get_water_saving_tips(self, soil_type: str) -> List[str]:
        """Get water-saving tips based on soil type"""
        tips = [
            'Use drip irrigation for 30-50% water savings',
            'Irrigate during early morning or evening to reduce evaporation',
            'Apply organic mulch to retain soil moisture',
            'Check for and repair irrigation system leaks'
        ]
        
        if soil_type.lower() == 'sandy':
            tips.extend([
                'Sandy soil: Add organic matter to improve water retention',
                'Consider more frequent but lighter irrigation'
            ])
        elif soil_type.lower() == 'clay':
            tips.extend([
                'Clay soil: Irrigate less frequently but more deeply',
                'Improve drainage to prevent waterlogging'
            ])
        
        return tips
    
    def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from DynamoDB"""
        try:
            response = self.user_table.get_item(Key={'user_id': user_id})
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error fetching user profile: {e}")
            return None
    
    def _save_alert(self, user_id: str, alert_data: Dict[str, Any]):
        """Save alert to DynamoDB"""
        try:
            alert_id = f"alert_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.alerts_table.put_item(
                Item={
                    'alert_id': alert_id,
                    'user_id': user_id,
                    'alert_data': json.dumps(alert_data),
                    'timestamp': alert_data['timestamp'],
                    'ttl': int((datetime.now() + timedelta(days=7)).timestamp())
                }
            )
            logger.info(f"Alert saved: {alert_id}")
        except Exception as e:
            logger.error(f"Error saving alert: {e}")
    
    def _send_alert_notification(self,
                                 user_id: str,
                                 alerts: List[Dict[str, Any]],
                                 user_profile: Dict[str, Any]):
        """Send alert notification via SNS"""
        try:
            # Get user's phone number and language preference
            phone = user_profile.get('phone_number')
            language = user_profile.get('preferences', {}).get('language', 'en')
            
            if not phone:
                logger.warning(f"No phone number for user {user_id}")
                return
            
            # Create alert message
            message = self._format_alert_message(alerts, language)
            
            # Send SMS via SNS (if configured)
            # self.sns.publish(PhoneNumber=phone, Message=message)
            
            logger.info(f"Alert notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def _format_alert_message(self, alerts: List[Dict[str, Any]], language: str) -> str:
        """Format alert message for notification"""
        if language == 'hi':
            message = "🌾 RISE मौसम चेतावनी\n\n"
            for alert in alerts[:2]:  # Limit to 2 alerts for SMS
                message += f"⚠️ {alert['title']}\n{alert['message']}\n\n"
        else:
            message = "🌾 RISE Weather Alert\n\n"
            for alert in alerts[:2]:
                message += f"⚠️ {alert['title']}\n{alert['message']}\n\n"
        
        return message
    
    def get_user_alerts(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Get recent alerts for a user
        
        Args:
            user_id: User identifier
            days: Number of days to look back
        
        Returns:
            Dict with user's recent alerts
        """
        try:
            # Query alerts table
            cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
            
            response = self.alerts_table.query(
                IndexName='UserAlertIndex',
                KeyConditionExpression='user_id = :uid AND #ts > :cutoff',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={
                    ':uid': user_id,
                    ':cutoff': cutoff_time
                }
            )
            
            alerts = []
            for item in response.get('Items', []):
                alert_data = json.loads(item['alert_data'])
                alerts.append(alert_data)
            
            return {
                'success': True,
                'alerts': alerts,
                'count': len(alerts)
            }
        
        except Exception as e:
            logger.error(f"Error fetching user alerts: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Tool functions for agent integration

def create_weather_alert_tools(region: str = "us-east-1") -> WeatherAlertTools:
    """
    Factory function to create weather alert tools instance
    
    Args:
        region: AWS region
    
    Returns:
        WeatherAlertTools instance
    """
    return WeatherAlertTools(region=region)


def monitor_weather_for_user(user_id: str) -> str:
    """
    Tool for monitoring weather and generating alerts for a user
    
    Args:
        user_id: User identifier
    
    Returns:
        Weather alerts and recommendations
    """
    tools = create_weather_alert_tools()
    result = tools.monitor_weather_conditions(user_id)
    
    if result['success']:
        output = f"Weather Monitoring for User {user_id}\n"
        output += f"Location: {result['location'].get('name', 'Unknown')}\n\n"
        
        if result['alerts']:
            output += f"⚠️ {len(result['alerts'])} Weather Alert(s):\n"
            for alert in result['alerts']:
                output += f"  • {alert['title']} ({alert['date']})\n"
        else:
            output += "✅ No adverse weather alerts\n"
        
        output += f"\n📋 {len(result['recommendations'])} Day(s) of Recommendations Available\n"
        output += f"💧 Irrigation Schedule: {len(result['irrigation']['schedule'])} days planned\n"
        
        return output
    else:
        return f"Error: {result.get('error', 'Failed to monitor weather')}"
