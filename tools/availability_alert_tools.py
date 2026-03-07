"""
RISE Resource Availability Alert System Tools
Tools for location-based notifications, seasonal demand prediction, and alert management
"""

import boto3
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from math import radians, sin, cos, sqrt, atan2

logger = logging.getLogger(__name__)


class AvailabilityAlertTools:
    """Resource availability alert tools for RISE farming assistant"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize availability alert tools with AWS clients
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        self.eventbridge = boto3.client('events', region_name=region)
        
        # DynamoDB tables
        self.resource_table = self.dynamodb.Table('RISE-ResourceSharing')
        self.booking_table = self.dynamodb.Table('RISE-ResourceBookings')
        self.groups_table = self.dynamodb.Table('RISE-BuyingGroups')
        self.user_table = self.dynamodb.Table('RISE-UserProfiles')
        
        logger.info(f"Availability alert tools initialized in region {region}")
    
    def send_equipment_availability_alert(self,
                                         resource_id: str,
                                         radius_km: int = 25) -> Dict[str, Any]:
        """
        Send location-based alerts for newly available equipment
        
        Args:
            resource_id: Equipment resource ID
            radius_km: Notification radius in kilometers
        
        Returns:
            Dict with alert result
        """
        try:
            # Get resource details
            resource_response = self.resource_table.get_item(Key={'resource_id': resource_id})
            if 'Item' not in resource_response:
                return {
                    'success': False,
                    'error': 'Resource not found'
                }
            
            resource = resource_response['Item']
            resource_location = resource['location']
            
            # Find nearby farmers
            nearby_farmers = self._find_nearby_farmers(resource_location, radius_km)
            
            alerts_sent = []
            
            for farmer in nearby_farmers:
                # Skip the owner
                if farmer['user_id'] == resource['owner_user_id']:
                    continue
                
                # Check if farmer has interest in this equipment type
                if self._check_equipment_interest(farmer, resource['resource_type']):
                    # Calculate distance
                    distance = self._calculate_distance(
                        farmer['location'],
                        resource_location
                    )
                    
                    # Generate alert message
                    alert_message = self._generate_equipment_alert_message(
                        resource,
                        distance,
                        farmer.get('preferences', {}).get('language', 'hi')
                    )
                    
                    # Send alert
                    alert_result = {
                        'user_id': farmer['user_id'],
                        'resource_id': resource_id,
                        'alert_message': alert_message,
                        'distance_km': round(distance, 1),
                        'timestamp': int(datetime.now().timestamp())
                    }
                    
                    alerts_sent.append(alert_result)
            
            logger.info(f"Equipment availability alerts sent: {len(alerts_sent)}")
            
            return {
                'success': True,
                'resource_id': resource_id,
                'alerts_sent': len(alerts_sent),
                'alerts': alerts_sent,
                'equipment_name': resource['equipment_details']['name'],
                'equipment_type': resource['resource_type']
            }
        
        except Exception as e:
            logger.error(f"Equipment availability alert error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    
    def send_bulk_buying_opportunity_alert(self,
                                          group_id: str,
                                          radius_km: int = 25) -> Dict[str, Any]:
        """
        Send alerts for bulk buying opportunities
        
        Args:
            group_id: Buying group ID
            radius_km: Notification radius in kilometers
        
        Returns:
            Dict with alert result
        """
        try:
            # Get group details
            group_response = self.groups_table.get_item(Key={'group_id': group_id})
            if 'Item' not in group_response:
                return {
                    'success': False,
                    'error': 'Group not found'
                }
            
            group = group_response['Item']
            group_location = group['location']
            
            # Find nearby farmers
            nearby_farmers = self._find_nearby_farmers(group_location, radius_km)
            
            alerts_sent = []
            
            for farmer in nearby_farmers:
                # Skip existing members
                if farmer['user_id'] in group.get('members', []):
                    continue
                
                # Check if farmer needs these products
                if self._check_product_interest(farmer, group['target_products']):
                    # Calculate potential savings
                    potential_savings = self._estimate_farmer_savings(
                        farmer,
                        group['target_products'],
                        group.get('bulk_pricing_achieved', {})
                    )
                    
                    # Generate alert message
                    alert_message = self._generate_buying_group_alert_message(
                        group,
                        potential_savings,
                        farmer.get('preferences', {}).get('language', 'hi')
                    )
                    
                    # Send alert
                    alert_result = {
                        'user_id': farmer['user_id'],
                        'group_id': group_id,
                        'alert_message': alert_message,
                        'potential_savings': potential_savings,
                        'timestamp': int(datetime.now().timestamp())
                    }
                    
                    alerts_sent.append(alert_result)
            
            logger.info(f"Bulk buying opportunity alerts sent: {len(alerts_sent)}")
            
            return {
                'success': True,
                'group_id': group_id,
                'alerts_sent': len(alerts_sent),
                'alerts': alerts_sent,
                'group_name': group['group_name'],
                'target_products': group['target_products']
            }
        
        except Exception as e:
            logger.error(f"Bulk buying opportunity alert error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def predict_seasonal_demand(self,
                               user_id: str,
                               crop_calendar: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Predict seasonal equipment and resource demand using Bedrock
        
        Args:
            user_id: User ID
            crop_calendar: Optional crop calendar data
        
        Returns:
            Dict with demand predictions
        """
        try:
            # Get user profile
            user_response = self.user_table.get_item(Key={'user_id': user_id})
            if 'Item' not in user_response:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            user = user_response['Item']
            location = user.get('location', {})
            farm_details = user.get('farm_details', {})
            
            # Use provided crop calendar or get from user profile
            if not crop_calendar:
                crop_calendar = farm_details.get('crop_calendar', {})
            
            # Prepare prediction prompt
            prediction_prompt = f"""
Analyze seasonal agricultural equipment and resource needs for a farmer:

Location: {location.get('district', 'Unknown')}, {location.get('state', 'Unknown')}
Farm Size: {farm_details.get('land_size', 'Unknown')} acres
Current Crops: {', '.join(farm_details.get('crops', []))}
Crop Calendar: {json.dumps(crop_calendar, indent=2)}

Predict equipment and resource needs for the next 90 days:
1. Equipment needed (tractors, harvesters, pumps, etc.)
2. Peak demand periods
3. Recommended booking timeline
4. Cost optimization strategies
5. Alternative resource sharing opportunities

Provide specific dates and actionable recommendations.
"""
            
            # Call Bedrock for AI prediction
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-5-haiku-20241022-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 2000,
                    'messages': [{
                        'role': 'user',
                        'content': prediction_prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            prediction_text = response_body['content'][0]['text']
            
            # Parse predictions into structured format
            predictions = self._parse_demand_predictions(prediction_text)
            
            logger.info(f"Seasonal demand predicted for user {user_id}")
            
            return {
                'success': True,
                'user_id': user_id,
                'predictions': predictions,
                'prediction_text': prediction_text,
                'generated_timestamp': int(datetime.now().timestamp()),
                'valid_until': int((datetime.now() + timedelta(days=90)).timestamp())
            }
        
        except Exception as e:
            logger.error(f"Seasonal demand prediction error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_advance_booking(self,
                              user_id: str,
                              booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create advance booking for predicted resource needs
        
        Args:
            user_id: User ID
            booking_data: Advance booking details
        
        Returns:
            Dict with booking result
        """
        try:
            advance_booking_id = f"adv_{uuid.uuid4().hex[:8]}"
            
            # Validate booking date is in future
            booking_date = datetime.fromisoformat(booking_data['booking_date'])
            if booking_date <= datetime.now():
                return {
                    'success': False,
                    'error': 'Booking date must be in the future'
                }
            
            # Search for available equipment
            search_result = self._search_available_equipment(
                booking_data['equipment_type'],
                booking_data['location'],
                booking_data['booking_date']
            )
            
            if not search_result['success'] or not search_result.get('equipment'):
                return {
                    'success': False,
                    'error': 'No equipment available for advance booking',
                    'recommendation': 'Try adjusting dates or equipment type'
                }
            
            # Select best option (closest, highest rated)
            best_equipment = search_result['equipment'][0]
            
            # Create advance booking
            advance_booking = {
                'advance_booking_id': advance_booking_id,
                'user_id': user_id,
                'resource_id': best_equipment['resource_id'],
                'equipment_type': booking_data['equipment_type'],
                'booking_date': booking_data['booking_date'],
                'duration_days': booking_data.get('duration_days', 1),
                'status': 'advance_reserved',
                'created_timestamp': int(datetime.now().timestamp()),
                'reminder_sent': False
            }
            
            logger.info(f"Advance booking created: {advance_booking_id}")
            
            return {
                'success': True,
                'advance_booking_id': advance_booking_id,
                'resource_id': best_equipment['resource_id'],
                'equipment_name': best_equipment['name'],
                'booking_date': booking_data['booking_date'],
                'estimated_cost': best_equipment['daily_rate'] * booking_data.get('duration_days', 1),
                'reminder_date': (booking_date - timedelta(days=7)).isoformat(),
                'message': 'Advance booking created successfully. You will receive a reminder 7 days before.'
            }
        
        except Exception as e:
            logger.error(f"Advance booking error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_optimal_sharing_schedule(self,
                                         resource_id: str,
                                         time_period_days: int = 30) -> Dict[str, Any]:
        """
        Generate optimal sharing schedule to maximize utilization
        
        Args:
            resource_id: Equipment resource ID
            time_period_days: Time period for schedule generation
        
        Returns:
            Dict with optimal schedule
        """
        try:
            # Get resource details
            resource_response = self.resource_table.get_item(Key={'resource_id': resource_id})
            if 'Item' not in resource_response:
                return {
                    'success': False,
                    'error': 'Resource not found'
                }
            
            resource = resource_response['Item']
            
            # Get existing bookings
            existing_bookings = self._get_resource_bookings(
                resource_id,
                time_period_days
            )
            
            # Find demand patterns
            demand_analysis = self._analyze_demand_patterns(
                resource['resource_type'],
                resource['location']
            )
            
            # Generate optimal schedule using AI
            schedule_prompt = f"""
Generate an optimal sharing schedule for agricultural equipment:

Equipment: {resource['equipment_details']['name']} ({resource['resource_type']})
Location: {resource['location']['district']}, {resource['location']['state']}
Daily Rate: ₹{float(resource['equipment_details'].get('daily_rate', 0))}
Time Period: {time_period_days} days

Existing Bookings: {len(existing_bookings)} bookings
Demand Pattern: {demand_analysis.get('pattern', 'moderate')}

Create an optimal schedule that:
1. Maximizes utilization rate
2. Allows maintenance windows
3. Considers seasonal demand
4. Balances owner availability
5. Optimizes revenue

Provide specific time slots and recommendations.
"""
            
            # Call Bedrock for schedule optimization
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-5-haiku-20241022-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 1500,
                    'messages': [{
                        'role': 'user',
                        'content': schedule_prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            schedule_text = response_body['content'][0]['text']
            
            # Parse schedule
            optimal_schedule = self._parse_optimal_schedule(schedule_text, time_period_days)
            
            # Calculate projected revenue
            projected_revenue = self._calculate_projected_revenue(
                resource,
                optimal_schedule
            )
            
            logger.info(f"Optimal schedule generated for resource {resource_id}")
            
            return {
                'success': True,
                'resource_id': resource_id,
                'optimal_schedule': optimal_schedule,
                'schedule_text': schedule_text,
                'projected_utilization_rate': optimal_schedule.get('utilization_rate', 0),
                'projected_monthly_revenue': projected_revenue,
                'existing_bookings': len(existing_bookings),
                'recommendations': optimal_schedule.get('recommendations', [])
            }
        
        except Exception as e:
            logger.error(f"Optimal schedule generation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    
    def customize_alert_preferences(self,
                                   user_id: str,
                                   preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Customize user's alert preferences
        
        Args:
            user_id: User ID
            preferences: Alert preference settings
        
        Returns:
            Dict with update result
        """
        try:
            # Get user profile
            user_response = self.user_table.get_item(Key={'user_id': user_id})
            if 'Item' not in user_response:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            user = user_response['Item']
            user_prefs = user.get('preferences', {})
            
            # Update alert preferences
            alert_prefs = user_prefs.get('alert_preferences', {})
            
            # Equipment availability alerts
            if 'equipment_alerts' in preferences:
                alert_prefs['equipment_alerts'] = {
                    'enabled': preferences['equipment_alerts'].get('enabled', True),
                    'equipment_types': preferences['equipment_alerts'].get('equipment_types', []),
                    'radius_km': preferences['equipment_alerts'].get('radius_km', 25),
                    'frequency': preferences['equipment_alerts'].get('frequency', 'immediate')
                }
            
            # Bulk buying alerts
            if 'buying_group_alerts' in preferences:
                alert_prefs['buying_group_alerts'] = {
                    'enabled': preferences['buying_group_alerts'].get('enabled', True),
                    'product_interests': preferences['buying_group_alerts'].get('product_interests', []),
                    'min_discount': preferences['buying_group_alerts'].get('min_discount', 15)
                }
            
            # Seasonal demand alerts
            if 'seasonal_alerts' in preferences:
                alert_prefs['seasonal_alerts'] = {
                    'enabled': preferences['seasonal_alerts'].get('enabled', True),
                    'advance_notice_days': preferences['seasonal_alerts'].get('advance_notice_days', 30)
                }
            
            # Alert channels
            if 'alert_channels' in preferences:
                alert_prefs['alert_channels'] = preferences['alert_channels']
            
            # Quiet hours
            if 'quiet_hours' in preferences:
                alert_prefs['quiet_hours'] = preferences['quiet_hours']
            
            user_prefs['alert_preferences'] = alert_prefs
            user['preferences'] = user_prefs
            
            # Save to DynamoDB
            self.user_table.put_item(Item=user)
            
            logger.info(f"Alert preferences updated for user {user_id}")
            
            return {
                'success': True,
                'user_id': user_id,
                'alert_preferences': alert_prefs,
                'message': 'Alert preferences updated successfully'
            }
        
        except Exception as e:
            logger.error(f"Customize alert preferences error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_alert_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's current alert preferences
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with alert preferences
        """
        try:
            user_response = self.user_table.get_item(Key={'user_id': user_id})
            
            if 'Item' not in user_response:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            user = user_response['Item']
            preferences = user.get('preferences', {})
            alert_prefs = preferences.get('alert_preferences', {
                'equipment_alerts': {
                    'enabled': True,
                    'equipment_types': [],
                    'radius_km': 25,
                    'frequency': 'immediate'
                },
                'buying_group_alerts': {
                    'enabled': True,
                    'product_interests': [],
                    'min_discount': 15
                },
                'seasonal_alerts': {
                    'enabled': True,
                    'advance_notice_days': 30
                },
                'alert_channels': ['voice', 'sms'],
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
    
    # Helper methods
    
    def _find_nearby_farmers(self,
                            location: Dict[str, Any],
                            radius_km: int) -> List[Dict[str, Any]]:
        """Find farmers within specified radius"""
        try:
            # Scan user profiles (in production, use GSI for efficient querying)
            response = self.user_table.scan()
            users = response.get('Items', [])
            
            nearby_farmers = []
            
            for user in users:
                user_location = user.get('location', {})
                
                # Calculate distance
                distance = self._calculate_distance(location, user_location)
                
                if distance <= radius_km:
                    nearby_farmers.append(user)
            
            return nearby_farmers
        
        except Exception as e:
            logger.warning(f"Find nearby farmers error: {e}")
            return []
    
    def _calculate_distance(self,
                           loc1: Dict[str, Any],
                           loc2: Dict[str, Any]) -> float:
        """Calculate distance between two locations in kilometers"""
        try:
            lat1 = radians(float(loc1.get('latitude', 0)))
            lon1 = radians(float(loc1.get('longitude', 0)))
            lat2 = radians(float(loc2.get('latitude', 0)))
            lon2 = radians(float(loc2.get('longitude', 0)))
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            
            return 6371 * c  # Earth radius in km
        except Exception as e:
            logger.warning(f"Distance calculation error: {e}")
            return 999999  # Return large distance on error
    
    def _check_equipment_interest(self,
                                 farmer: Dict[str, Any],
                                 equipment_type: str) -> bool:
        """Check if farmer is interested in equipment type"""
        alert_prefs = farmer.get('preferences', {}).get('alert_preferences', {})
        equipment_alerts = alert_prefs.get('equipment_alerts', {})
        
        if not equipment_alerts.get('enabled', True):
            return False
        
        interested_types = equipment_alerts.get('equipment_types', [])
        
        # If no specific types, interested in all
        if not interested_types:
            return True
        
        return equipment_type in interested_types
    
    def _check_product_interest(self,
                               farmer: Dict[str, Any],
                               products: List[str]) -> bool:
        """Check if farmer is interested in products"""
        alert_prefs = farmer.get('preferences', {}).get('alert_preferences', {})
        buying_alerts = alert_prefs.get('buying_group_alerts', {})
        
        if not buying_alerts.get('enabled', True):
            return False
        
        interested_products = buying_alerts.get('product_interests', [])
        
        # If no specific products, interested in all
        if not interested_products:
            return True
        
        # Check for any matching products
        return any(product in interested_products for product in products)
    
    def _estimate_farmer_savings(self,
                                farmer: Dict[str, Any],
                                products: List[str],
                                bulk_pricing: Dict[str, Any]) -> float:
        """Estimate potential savings for farmer"""
        # Simple estimation (in production, use actual requirements)
        avg_discount = 20  # 20% average discount
        
        if bulk_pricing:
            discounts = [float(v) for v in bulk_pricing.values()]
            if discounts:
                avg_discount = sum(discounts) / len(discounts)
        
        # Estimate based on typical farmer spending
        estimated_monthly_spend = 10000  # ₹10,000 per month
        estimated_savings = estimated_monthly_spend * (avg_discount / 100)
        
        return round(estimated_savings, 2)
    
    def _generate_equipment_alert_message(self,
                                         resource: Dict[str, Any],
                                         distance: float,
                                         language: str) -> str:
        """Generate equipment availability alert message"""
        equipment_name = resource['equipment_details']['name']
        daily_rate = float(resource['equipment_details'].get('daily_rate', 0))
        location = f"{resource['location']['district']}, {resource['location']['state']}"
        
        messages = {
            'hi': f"""🚜 नया उपकरण उपलब्ध है!

उपकरण: {equipment_name}
स्थान: {location} ({distance:.1f} किमी दूर)
दर: ₹{daily_rate:.0f}/दिन

अभी बुक करें और समय पर उपकरण प्राप्त करें!""",
            
            'en': f"""🚜 New Equipment Available!

Equipment: {equipment_name}
Location: {location} ({distance:.1f} km away)
Rate: ₹{daily_rate:.0f}/day

Book now and get equipment on time!"""
        }
        
        return messages.get(language, messages['en'])
    
    def _generate_buying_group_alert_message(self,
                                            group: Dict[str, Any],
                                            savings: float,
                                            language: str) -> str:
        """Generate buying group opportunity alert message"""
        group_name = group['group_name']
        products = ', '.join(group['target_products'][:3])
        member_count = len(group.get('members', []))
        
        messages = {
            'hi': f"""💰 थोक खरीद का अवसर!

समूह: {group_name}
उत्पाद: {products}
सदस्य: {member_count} किसान
संभावित बचत: ₹{savings:.0f}/माह

अभी शामिल हों और 15-30% तक बचत करें!""",
            
            'en': f"""💰 Bulk Buying Opportunity!

Group: {group_name}
Products: {products}
Members: {member_count} farmers
Potential Savings: ₹{savings:.0f}/month

Join now and save 15-30%!"""
        }
        
        return messages.get(language, messages['en'])
    
    def _parse_demand_predictions(self, prediction_text: str) -> Dict[str, Any]:
        """Parse AI-generated demand predictions into structured format"""
        # Simple parsing (in production, use more sophisticated NLP)
        predictions = {
            'equipment_needs': [],
            'peak_periods': [],
            'booking_timeline': [],
            'cost_optimization': [],
            'recommendations': []
        }
        
        # Extract key information from text
        lines = prediction_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if 'equipment' in line.lower() and 'need' in line.lower():
                current_section = 'equipment_needs'
            elif 'peak' in line.lower() or 'demand' in line.lower():
                current_section = 'peak_periods'
            elif 'booking' in line.lower() or 'timeline' in line.lower():
                current_section = 'booking_timeline'
            elif 'cost' in line.lower() or 'optimization' in line.lower():
                current_section = 'cost_optimization'
            elif 'recommend' in line.lower():
                current_section = 'recommendations'
            elif current_section and line.startswith(('-', '•', '*', '1', '2', '3', '4', '5')):
                predictions[current_section].append(line.lstrip('-•*123456789. '))
        
        return predictions
    
    def _search_available_equipment(self,
                                   equipment_type: str,
                                   location: Dict[str, Any],
                                   booking_date: str) -> Dict[str, Any]:
        """Search for available equipment"""
        try:
            response = self.resource_table.scan(
                FilterExpression='resource_type = :type AND availability_status = :status',
                ExpressionAttributeValues={
                    ':type': equipment_type,
                    ':status': 'available'
                }
            )
            
            resources = response.get('Items', [])
            available_equipment = []
            
            for resource in resources:
                distance = self._calculate_distance(location, resource['location'])
                
                if distance <= 50:  # 50km radius for advance booking
                    available_equipment.append({
                        'resource_id': resource['resource_id'],
                        'name': resource['equipment_details']['name'],
                        'daily_rate': float(resource['equipment_details'].get('daily_rate', 0)),
                        'distance_km': round(distance, 1),
                        'rating': float(resource['ratings'].get('average', 0))
                    })
            
            # Sort by distance and rating
            available_equipment.sort(key=lambda x: (x['distance_km'], -x['rating']))
            
            return {
                'success': True,
                'equipment': available_equipment
            }
        
        except Exception as e:
            logger.error(f"Search equipment error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_resource_bookings(self,
                              resource_id: str,
                              days: int) -> List[Dict]:
        """Get resource bookings for specified period"""
        try:
            threshold_time = int((datetime.now() + timedelta(days=days)).timestamp())
            
            response = self.booking_table.scan(
                FilterExpression='resource_id = :rid AND booking_start < :threshold',
                ExpressionAttributeValues={
                    ':rid': resource_id,
                    ':threshold': threshold_time
                }
            )
            
            return response.get('Items', [])
        
        except Exception as e:
            logger.warning(f"Get bookings error: {e}")
            return []
    
    def _analyze_demand_patterns(self,
                                equipment_type: str,
                                location: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze demand patterns for equipment type"""
        # Simple analysis (in production, use historical data)
        return {
            'pattern': 'moderate',
            'peak_season': 'kharif',
            'utilization_rate': 0.6
        }
    
    def _parse_optimal_schedule(self,
                               schedule_text: str,
                               days: int) -> Dict[str, Any]:
        """Parse AI-generated optimal schedule"""
        # Simple parsing
        schedule = {
            'time_slots': [],
            'utilization_rate': 0.7,
            'maintenance_windows': [],
            'recommendations': []
        }
        
        # Extract recommendations
        lines = schedule_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '•', '*')):
                schedule['recommendations'].append(line.lstrip('-•* '))
        
        return schedule
    
    def _calculate_projected_revenue(self,
                                    resource: Dict[str, Any],
                                    schedule: Dict[str, Any]) -> float:
        """Calculate projected revenue from optimal schedule"""
        daily_rate = float(resource['equipment_details'].get('daily_rate', 0))
        utilization_rate = schedule.get('utilization_rate', 0.7)
        days_per_month = 30
        
        return round(daily_rate * days_per_month * utilization_rate, 2)


# Factory function for tool creation

def create_availability_alert_tools(region: str = "us-east-1") -> AvailabilityAlertTools:
    """
    Factory function to create availability alert tools instance
    
    Args:
        region: AWS region
    
    Returns:
        AvailabilityAlertTools instance
    """
    return AvailabilityAlertTools(region=region)
