"""
RISE Resource Alert System Tools
Tools for monitoring unused equipment and sending proactive alerts
"""

import boto3
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class ResourceAlertTools:
    """Resource alert tools for unused equipment monitoring"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize resource alert tools with AWS clients
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.eventbridge = boto3.client('events', region_name=region)
        
        # DynamoDB tables
        self.resource_table = self.dynamodb.Table('RISE-ResourceSharing')
        self.booking_table = self.dynamodb.Table('RISE-ResourceBookings')
        self.user_table = self.dynamodb.Table('RISE-UserProfiles')
        
        logger.info(f"Resource alert tools initialized in region {region}")
    
    def find_unused_resources(self, days_threshold: int = 30) -> Dict[str, Any]:
        """
        Find equipment that hasn't been used or booked in specified days
        
        Args:
            days_threshold: Number of days of inactivity to trigger alert
        
        Returns:
            Dict with unused resources list
        """
        try:
            current_time = int(datetime.now().timestamp())
            threshold_time = current_time - (days_threshold * 24 * 60 * 60)
            
            # Scan all resources
            response = self.resource_table.scan()
            resources = response.get('Items', [])
            
            unused_resources = []
            
            for resource in resources:
                # Check last used timestamp
                last_used = resource.get('last_used_timestamp', 0)
                created = resource.get('created_timestamp', current_time)
                
                # Skip if resource is newly created (less than threshold days old)
                if created > threshold_time:
                    continue
                
                # Check if unused for threshold period
                if last_used < threshold_time:
                    # Get recent bookings to verify
                    recent_bookings = self._get_recent_bookings(
                        resource['resource_id'],
                        days_threshold
                    )
                    
                    if len(recent_bookings) == 0:
                        unused_resources.append({
                            'resource_id': resource['resource_id'],
                            'owner_user_id': resource['owner_user_id'],
                            'equipment_name': resource['equipment_details']['name'],
                            'equipment_type': resource['resource_type'],
                            'daily_rate': float(resource['equipment_details'].get('daily_rate', 0)),
                            'last_used_timestamp': last_used,
                            'days_unused': (current_time - max(last_used, created)) // (24 * 60 * 60),
                            'location': resource['location']
                        })
            
            logger.info(f"Found {len(unused_resources)} unused resources")
            
            return {
                'success': True,
                'count': len(unused_resources),
                'unused_resources': unused_resources,
                'days_threshold': days_threshold
            }
        
        except Exception as e:
            logger.error(f"Find unused resources error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_recent_bookings(self, resource_id: str, days: int) -> List[Dict]:
        """Get recent bookings for a resource"""
        try:
            threshold_time = int((datetime.now() - timedelta(days=days)).timestamp())
            
            response = self.booking_table.scan(
                FilterExpression='resource_id = :rid AND created_timestamp > :threshold',
                ExpressionAttributeValues={
                    ':rid': resource_id,
                    ':threshold': threshold_time
                }
            )
            
            return response.get('Items', [])
        
        except Exception as e:
            logger.warning(f"Get recent bookings error: {e}")
            return []
    
    def calculate_potential_income(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate potential income from unused equipment
        
        Args:
            resource: Resource information
        
        Returns:
            Dict with income estimates
        """
        try:
            daily_rate = resource.get('daily_rate', 0)
            equipment_type = resource.get('equipment_type', '')
            
            # Utilization rates by equipment type (based on market data)
            utilization_rates = {
                'tractor': 0.6,      # 60% utilization
                'harvester': 0.5,    # 50% utilization
                'pump': 0.4,         # 40% utilization
                'drone': 0.3,        # 30% utilization
                'default': 0.5       # 50% default
            }
            
            utilization_rate = utilization_rates.get(equipment_type, utilization_rates['default'])
            
            # Calculate estimates
            days_per_month = 30
            monthly_income = daily_rate * days_per_month * utilization_rate
            yearly_income = monthly_income * 12
            
            # Calculate opportunity cost (income lost due to non-sharing)
            days_unused = resource.get('days_unused', 30)
            opportunity_cost = daily_rate * days_unused * utilization_rate
            
            return {
                'success': True,
                'daily_rate': daily_rate,
                'utilization_rate': utilization_rate,
                'estimated_monthly_income': round(monthly_income, 2),
                'estimated_yearly_income': round(yearly_income, 2),
                'opportunity_cost': round(opportunity_cost, 2),
                'days_unused': days_unused
            }
        
        except Exception as e:
            logger.error(f"Calculate potential income error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_unused_resource_alert(self,
                                   resource: Dict[str, Any],
                                   user_language: str = 'hi') -> Dict[str, Any]:
        """
        Send alert to equipment owner about unused resource
        
        Args:
            resource: Resource information
            user_language: User's preferred language
        
        Returns:
            Dict with alert result
        """
        try:
            # Calculate potential income
            income_data = self.calculate_potential_income(resource)
            
            if not income_data['success']:
                return income_data
            
            # Get user details
            user_response = self.user_table.get_item(
                Key={'user_id': resource['owner_user_id']}
            )
            
            if 'Item' not in user_response:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            user = user_response['Item']
            user_language = user.get('preferences', {}).get('language', 'hi')
            
            # Generate alert message in user's language
            alert_message = self._generate_alert_message(
                resource,
                income_data,
                user_language
            )
            
            # Send alert (will be implemented with voice tools integration)
            alert_result = {
                'success': True,
                'resource_id': resource['resource_id'],
                'owner_user_id': resource['owner_user_id'],
                'alert_message': alert_message,
                'potential_monthly_income': income_data['estimated_monthly_income'],
                'opportunity_cost': income_data['opportunity_cost'],
                'days_unused': resource['days_unused'],
                'alert_timestamp': int(datetime.now().timestamp())
            }
            
            logger.info(f"Alert sent for resource: {resource['resource_id']}")
            
            return alert_result
        
        except Exception as e:
            logger.error(f"Send unused resource alert error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_alert_message(self,
                               resource: Dict[str, Any],
                               income_data: Dict[str, Any],
                               language: str) -> str:
        """Generate alert message in specified language"""
        
        equipment_name = resource['equipment_name']
        days_unused = resource['days_unused']
        monthly_income = income_data['estimated_monthly_income']
        opportunity_cost = income_data['opportunity_cost']
        
        # Message templates by language
        messages = {
            'hi': f"""🚜 उपकरण साझाकरण अवसर!

आपका {equipment_name} पिछले {days_unused} दिनों से उपयोग नहीं हुआ है।

💰 संभावित आय:
• मासिक आय: ₹{monthly_income:.0f}
• खोई हुई आय: ₹{opportunity_cost:.0f}

क्या आप इसे साझा करना चाहेंगे और अतिरिक्त आय अर्जित करना चाहेंगे?

अभी सूचीबद्ध करें और अपने समुदाय की मदद करें!""",
            
            'en': f"""🚜 Equipment Sharing Opportunity!

Your {equipment_name} has been unused for the past {days_unused} days.

💰 Potential Income:
• Monthly income: ₹{monthly_income:.0f}
• Lost income: ₹{opportunity_cost:.0f}

Would you like to share it and earn additional income?

List it now and help your community!""",
            
            'ta': f"""🚜 உபகரண பகிர்வு வாய்ப்பு!

உங்கள் {equipment_name} கடந்த {days_unused} நாட்களாக பயன்படுத்தப்படவில்லை.

💰 சாத்தியமான வருமானம்:
• மாதாந்திர வருமானம்: ₹{monthly_income:.0f}
• இழந்த வருமானம்: ₹{opportunity_cost:.0f}

இதை பகிர்ந்து கூடுதல் வருமானம் ஈட்ட விரும்புகிறீர்களா?

இப்போதே பட்டியலிட்டு உங்கள் சமூகத்திற்கு உதவுங்கள்!""",
            
            'te': f"""🚜 పరికరాల భాగస్వామ్య అవకాశం!

మీ {equipment_name} గత {days_unused} రోజులుగా ఉపయోగించబడలేదు.

💰 సంభావ్య ఆదాయం:
• నెలవారీ ఆదాయం: ₹{monthly_income:.0f}
• కోల్పోయిన ఆదాయం: ₹{opportunity_cost:.0f}

దీన్ని భాగస్వామ్యం చేసి అదనపు ఆదాయం పొందాలనుకుంటున్నారా?

ఇప్పుడే జాబితా చేసి మీ సమాజానికి సహాయం చేయండి!""",
            
            'kn': f"""🚜 ಉಪಕರಣ ಹಂಚಿಕೆ ಅವಕಾಶ!

ನಿಮ್ಮ {equipment_name} ಕಳೆದ {days_unused} ದಿನಗಳಿಂದ ಬಳಸಲಾಗಿಲ್ಲ.

💰 ಸಂಭಾವ್ಯ ಆದಾಯ:
• ಮಾಸಿಕ ಆದಾಯ: ₹{monthly_income:.0f}
• ಕಳೆದುಹೋದ ಆದಾಯ: ₹{opportunity_cost:.0f}

ಇದನ್ನು ಹಂಚಿಕೊಂಡು ಹೆಚ್ಚುವರಿ ಆದಾಯ ಗಳಿಸಲು ಬಯಸುವಿರಾ?

ಈಗಲೇ ಪಟ್ಟಿ ಮಾಡಿ ಮತ್ತು ನಿಮ್ಮ ಸಮುದಾಯಕ್ಕೆ ಸಹಾಯ ಮಾಡಿ!""",
            
            'bn': f"""🚜 সরঞ্জাম ভাগাভাগির সুযোগ!

আপনার {equipment_name} গত {days_unused} দিন ধরে ব্যবহার হয়নি।

💰 সম্ভাব্য আয়:
• মাসিক আয়: ₹{monthly_income:.0f}
• হারানো আয়: ₹{opportunity_cost:.0f}

আপনি কি এটি ভাগ করে অতিরিক্ত আয় করতে চান?

এখনই তালিকাভুক্ত করুন এবং আপনার সম্প্রদায়কে সাহায্য করুন!""",
            
            'gu': f"""🚜 સાધન વહેંચણીની તક!

તમારું {equipment_name} છેલ્લા {days_unused} દિવસથી ઉપયોગમાં નથી.

💰 સંભવિત આવક:
• માસિક આવક: ₹{monthly_income:.0f}
• ગુમાવેલી આવક: ₹{opportunity_cost:.0f}

શું તમે તેને શેર કરીને વધારાની આવક મેળવવા માંગો છો?

હમણાં જ સૂચિબદ્ધ કરો અને તમારા સમુદાયને મદદ કરો!""",
            
            'mr': f"""🚜 उपकरणे सामायिक करण्याची संधी!

तुमचे {equipment_name} गेल्या {days_unused} दिवसांपासून वापरले गेले नाही.

💰 संभाव्य उत्पन्न:
• मासिक उत्पन्न: ₹{monthly_income:.0f}
• गमावलेले उत्पन्न: ₹{opportunity_cost:.0f}

तुम्हाला ते सामायिक करून अतिरिक्त उत्पन्न मिळवायचे आहे का?

आता सूचीबद्ध करा आणि तुमच्या समुदायाला मदत करा!""",
            
            'pa': f"""🚜 ਸਾਜ਼ੋ-ਸਾਮਾਨ ਸਾਂਝਾ ਕਰਨ ਦਾ ਮੌਕਾ!

ਤੁਹਾਡਾ {equipment_name} ਪਿਛਲੇ {days_unused} ਦਿਨਾਂ ਤੋਂ ਵਰਤਿਆ ਨਹੀਂ ਗਿਆ।

💰 ਸੰਭਾਵਿਤ ਆਮਦਨ:
• ਮਹੀਨਾਵਾਰ ਆਮਦਨ: ₹{monthly_income:.0f}
• ਗੁਆਚੀ ਆਮਦਨ: ₹{opportunity_cost:.0f}

ਕੀ ਤੁਸੀਂ ਇਸਨੂੰ ਸਾਂਝਾ ਕਰਕੇ ਵਾਧੂ ਆਮਦਨ ਕਮਾਉਣਾ ਚਾਹੁੰਦੇ ਹੋ?

ਹੁਣੇ ਸੂਚੀਬੱਧ ਕਰੋ ਅਤੇ ਆਪਣੇ ਭਾਈਚਾਰੇ ਦੀ ਮਦਦ ਕਰੋ!"""
        }
        
        return messages.get(language, messages['en'])
    
    def send_batch_alerts(self, days_threshold: int = 30) -> Dict[str, Any]:
        """
        Send alerts for all unused resources
        
        Args:
            days_threshold: Days of inactivity threshold
        
        Returns:
            Dict with batch alert results
        """
        try:
            # Find unused resources
            unused_result = self.find_unused_resources(days_threshold)
            
            if not unused_result['success']:
                return unused_result
            
            unused_resources = unused_result['unused_resources']
            alerts_sent = []
            alerts_failed = []
            
            for resource in unused_resources:
                alert_result = self.send_unused_resource_alert(resource)
                
                if alert_result['success']:
                    alerts_sent.append(alert_result)
                else:
                    alerts_failed.append({
                        'resource_id': resource['resource_id'],
                        'error': alert_result.get('error', 'Unknown error')
                    })
            
            logger.info(f"Batch alerts: {len(alerts_sent)} sent, {len(alerts_failed)} failed")
            
            return {
                'success': True,
                'total_unused': len(unused_resources),
                'alerts_sent': len(alerts_sent),
                'alerts_failed': len(alerts_failed),
                'alerts': alerts_sent,
                'failures': alerts_failed
            }
        
        except Exception as e:
            logger.error(f"Batch alerts error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_alert_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's alert preferences
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with alert preferences
        """
        try:
            response = self.user_table.get_item(Key={'user_id': user_id})
            
            if 'Item' not in response:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            user = response['Item']
            preferences = user.get('preferences', {})
            alert_prefs = preferences.get('alert_preferences', {
                'unused_equipment_alerts': True,
                'alert_frequency': 'weekly',  # daily, weekly, monthly
                'alert_threshold_days': 30,
                'alert_channels': ['voice', 'sms'],  # voice, sms, push
                'quiet_hours': {
                    'enabled': True,
                    'start': '22:00',
                    'end': '07:00'
                }
            })
            
            return {
                'success': True,
                'user_id': user_id,
                'alert_preferences': alert_prefs
            }
        
        except Exception as e:
            logger.error(f"Get alert preferences error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_alert_preferences(self,
                                 user_id: str,
                                 preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user's alert preferences
        
        Args:
            user_id: User ID
            preferences: New alert preferences
        
        Returns:
            Dict with update result
        """
        try:
            response = self.user_table.get_item(Key={'user_id': user_id})
            
            if 'Item' not in response:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            user = response['Item']
            user_prefs = user.get('preferences', {})
            
            # Update alert preferences
            current_alert_prefs = user_prefs.get('alert_preferences', {})
            current_alert_prefs.update(preferences)
            user_prefs['alert_preferences'] = current_alert_prefs
            
            user['preferences'] = user_prefs
            
            # Save to DynamoDB
            self.user_table.put_item(Item=user)
            
            logger.info(f"Alert preferences updated for user: {user_id}")
            
            return {
                'success': True,
                'user_id': user_id,
                'alert_preferences': current_alert_prefs,
                'message': 'Alert preferences updated successfully'
            }
        
        except Exception as e:
            logger.error(f"Update alert preferences error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


# Factory function for tool creation

def create_resource_alert_tools(region: str = "us-east-1") -> ResourceAlertTools:
    """
    Factory function to create resource alert tools instance
    
    Args:
        region: AWS region
    
    Returns:
        ResourceAlertTools instance
    """
    return ResourceAlertTools(region=region)
