"""
RISE Equipment Sharing Marketplace Tools
Tools for equipment listing, search, booking, and resource sharing management
"""

import boto3
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class EquipmentSharingTools:
    """Equipment sharing marketplace tools for RISE farming assistant"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize equipment sharing tools with AWS clients
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        
        # DynamoDB tables
        self.resource_table = self.dynamodb.Table('RISE-ResourceSharing')
        self.booking_table = self.dynamodb.Table('RISE-ResourceBookings')
        
        logger.info(f"Equipment sharing tools initialized in region {region}")
    
    def list_equipment(self,
                      owner_id: str,
                      equipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        List equipment for sharing
        
        Args:
            owner_id: Equipment owner's user ID
            equipment_data: Equipment details
        
        Returns:
            Dict with listing result
        """
        try:
            resource_id = f"res_{uuid.uuid4().hex[:8]}"
            
            resource_item = {
                'resource_id': resource_id,
                'availability_date': equipment_data.get('available_from', datetime.now().isoformat()),
                'owner_user_id': owner_id,
                'resource_type': equipment_data['type'],  # tractor, pump, drone, harvester
                'equipment_details': {
                    'name': equipment_data['name'],
                    'model': equipment_data.get('model', ''),
                    'condition': equipment_data.get('condition', 'good'),
                    'hourly_rate': Decimal(str(equipment_data.get('hourly_rate', 0))),
                    'daily_rate': Decimal(str(equipment_data.get('daily_rate', 0))),
                    'specifications': equipment_data.get('specifications', {}),
                    'year': equipment_data.get('year', ''),
                    'capacity': equipment_data.get('capacity', '')
                },
                'location': {
                    'state': equipment_data['location']['state'],
                    'district': equipment_data['location']['district'],
                    'address': equipment_data['location'].get('address', ''),
                    'latitude': Decimal(str(equipment_data['location'].get('latitude', 0))),
                    'longitude': Decimal(str(equipment_data['location'].get('longitude', 0)))
                },
                'availability_status': 'available',
                'availability_calendar': equipment_data.get('availability_calendar', {}),
                'booking_history': [],
                'ratings': {'average': 0, 'count': 0, 'reviews': []},
                'photos': equipment_data.get('photos', []),
                'insurance_details': equipment_data.get('insurance_details', {}),
                'pickup_instructions': equipment_data.get('pickup_instructions', ''),
                'created_timestamp': int(datetime.now().timestamp()),
                'updated_timestamp': int(datetime.now().timestamp()),
                'last_used_timestamp': 0
            }
            
            # Store in DynamoDB
            self.resource_table.put_item(Item=resource_item)
            
            # Calculate potential income
            potential_income = self._calculate_potential_income(resource_item)
            
            logger.info(f"Equipment listed: {resource_id}")
            
            return {
                'success': True,
                'resource_id': resource_id,
                'status': 'listed_successfully',
                'estimated_monthly_income': potential_income,
                'message': f'Equipment listed successfully. Potential monthly income: ₹{potential_income}'
            }
        
        except Exception as e:
            logger.error(f"Equipment listing error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_equipment(self,
                        location: Dict[str, Any],
                        equipment_type: Optional[str] = None,
                        date_range: Optional[Dict[str, str]] = None,
                        radius_km: int = 25) -> Dict[str, Any]:
        """
        Search for available equipment within radius
        
        Args:
            location: Search location with latitude/longitude
            equipment_type: Type of equipment (optional)
            date_range: Availability date range (optional)
            radius_km: Search radius in kilometers (default 25km)
        
        Returns:
            Dict with search results
        """
        try:
            # Query all resources (in production, use GSI for efficient querying)
            response = self.resource_table.scan(
                FilterExpression='availability_status = :status',
                ExpressionAttributeValues={
                    ':status': 'available'
                }
            )
            
            resources = response.get('Items', [])
            available_equipment = []
            
            for resource in resources:
                # Filter by equipment type if specified
                if equipment_type and resource['resource_type'] != equipment_type:
                    continue
                
                # Calculate distance
                distance = self._calculate_distance(location, resource['location'])
                
                # Filter by radius
                if distance > radius_km:
                    continue
                
                # Check availability for date range if specified
                if date_range:
                    if not self._check_availability(resource['resource_id'], date_range):
                        continue
                
                # Add to results
                equipment_info = {
                    'resource_id': resource['resource_id'],
                    'owner_user_id': resource['owner_user_id'],
                    'type': resource['resource_type'],
                    'name': resource['equipment_details']['name'],
                    'model': resource['equipment_details'].get('model', ''),
                    'condition': resource['equipment_details'].get('condition', 'good'),
                    'hourly_rate': float(resource['equipment_details'].get('hourly_rate', 0)),
                    'daily_rate': float(resource['equipment_details'].get('daily_rate', 0)),
                    'specifications': resource['equipment_details'].get('specifications', {}),
                    'location': {
                        'state': resource['location']['state'],
                        'district': resource['location']['district'],
                        'address': resource['location'].get('address', '')
                    },
                    'distance_km': round(distance, 1),
                    'estimated_transport_cost': round(distance * 2, 2),  # ₹2 per km
                    'ratings': resource['ratings'],
                    'photos': resource.get('photos', []),
                    'availability_status': resource['availability_status']
                }
                
                available_equipment.append(equipment_info)
            
            # Sort by distance and rating
            available_equipment.sort(key=lambda x: (x['distance_km'], -x['ratings']['average']))
            
            logger.info(f"Equipment search: found {len(available_equipment)} results")
            
            return {
                'success': True,
                'count': len(available_equipment),
                'equipment': available_equipment,
                'search_params': {
                    'location': location,
                    'equipment_type': equipment_type,
                    'radius_km': radius_km
                }
            }
        
        except Exception as e:
            logger.error(f"Equipment search error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def book_equipment(self,
                      renter_id: str,
                      resource_id: str,
                      booking_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Book equipment for specified period
        
        Args:
            renter_id: Renter's user ID
            resource_id: Equipment resource ID
            booking_details: Booking information
        
        Returns:
            Dict with booking result
        """
        try:
            booking_id = f"book_{uuid.uuid4().hex[:8]}"
            
            # Get resource details
            resource_response = self.resource_table.get_item(Key={'resource_id': resource_id})
            if 'Item' not in resource_response:
                return {
                    'success': False,
                    'error': 'Equipment not found'
                }
            
            resource = resource_response['Item']
            
            # Verify availability
            start_time = booking_details['start_time']
            end_time = booking_details['end_time']
            
            if not self._verify_availability(resource_id, start_time, end_time):
                return {
                    'success': False,
                    'error': 'Equipment not available for requested time'
                }
            
            # Calculate total cost
            total_cost = self._calculate_booking_cost(resource, booking_details)
            insurance_premium = round(total_cost * 0.05, 2)
            
            booking_item = {
                'booking_id': booking_id,
                'resource_id': resource_id,
                'renter_user_id': renter_id,
                'owner_user_id': resource['owner_user_id'],
                'booking_start': start_time,
                'booking_end': end_time,
                'total_cost': Decimal(str(total_cost)),
                'payment_status': 'pending',
                'usage_tracking': {
                    'start_reading': 0,
                    'end_reading': 0,
                    'hours_used': 0
                },
                'insurance_details': {
                    'coverage_amount': Decimal(str(total_cost * 2)),
                    'premium': Decimal(str(insurance_premium)),
                    'policy_number': f"INS_{booking_id}",
                    'verified': True
                },
                'rating_given': {},
                'status': 'confirmed',
                'delivery_status': 'pending',
                'created_timestamp': int(datetime.now().timestamp()),
                'updated_timestamp': int(datetime.now().timestamp())
            }
            
            # Store booking
            self.booking_table.put_item(Item=booking_item)
            
            # Update resource availability
            self._update_resource_availability(resource_id, booking_details)
            
            # Generate pickup instructions
            pickup_instructions = self._generate_pickup_instructions(resource)
            
            logger.info(f"Equipment booked: {booking_id}")
            
            return {
                'success': True,
                'booking_id': booking_id,
                'status': 'confirmed',
                'total_cost': total_cost,
                'insurance_premium': insurance_premium,
                'payment_status': 'pending',
                'pickup_instructions': pickup_instructions,
                'next_steps': [
                    'Complete payment processing',
                    'Verify insurance coverage',
                    'Coordinate pickup with owner',
                    'Inspect equipment before use'
                ]
            }
        
        except Exception as e:
            logger.error(f"Equipment booking error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_equipment_details(self, resource_id: str) -> Dict[str, Any]:
        """
        Get detailed information about equipment
        
        Args:
            resource_id: Equipment resource ID
        
        Returns:
            Dict with equipment details
        """
        try:
            response = self.resource_table.get_item(Key={'resource_id': resource_id})
            
            if 'Item' not in response:
                return {
                    'success': False,
                    'error': 'Equipment not found'
                }
            
            resource = response['Item']
            
            # Get booking history
            booking_response = self.booking_table.scan(
                FilterExpression='resource_id = :rid',
                ExpressionAttributeValues={':rid': resource_id}
            )
            
            bookings = booking_response.get('Items', [])
            
            return {
                'success': True,
                'resource_id': resource_id,
                'equipment': {
                    'type': resource['resource_type'],
                    'name': resource['equipment_details']['name'],
                    'model': resource['equipment_details'].get('model', ''),
                    'condition': resource['equipment_details'].get('condition', 'good'),
                    'specifications': resource['equipment_details'].get('specifications', {}),
                    'year': resource['equipment_details'].get('year', ''),
                    'capacity': resource['equipment_details'].get('capacity', '')
                },
                'pricing': {
                    'hourly_rate': float(resource['equipment_details'].get('hourly_rate', 0)),
                    'daily_rate': float(resource['equipment_details'].get('daily_rate', 0))
                },
                'location': resource['location'],
                'availability_status': resource['availability_status'],
                'availability_calendar': resource.get('availability_calendar', {}),
                'ratings': resource['ratings'],
                'photos': resource.get('photos', []),
                'insurance_details': resource.get('insurance_details', {}),
                'pickup_instructions': resource.get('pickup_instructions', ''),
                'total_bookings': len(bookings),
                'owner_user_id': resource['owner_user_id']
            }
        
        except Exception as e:
            logger.error(f"Get equipment details error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def rate_equipment(self,
                      booking_id: str,
                      rating_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rate equipment after use
        
        Args:
            booking_id: Booking ID
            rating_data: Rating and review information
        
        Returns:
            Dict with rating result
        """
        try:
            # Get booking details
            booking_response = self.booking_table.get_item(Key={'booking_id': booking_id})
            if 'Item' not in booking_response:
                return {
                    'success': False,
                    'error': 'Booking not found'
                }
            
            booking = booking_response['Item']
            resource_id = booking['resource_id']
            
            # Update booking with rating
            booking['rating_given'] = {
                'equipment_rating': rating_data['equipment_rating'],
                'owner_rating': rating_data.get('owner_rating', 0),
                'review': rating_data.get('review', ''),
                'timestamp': int(datetime.now().timestamp())
            }
            self.booking_table.put_item(Item=booking)
            
            # Update resource ratings
            resource_response = self.resource_table.get_item(Key={'resource_id': resource_id})
            resource = resource_response['Item']
            
            ratings = resource['ratings']
            current_avg = float(ratings.get('average', 0))
            current_count = ratings.get('count', 0)
            
            # Calculate new average
            new_count = current_count + 1
            new_avg = ((current_avg * current_count) + rating_data['equipment_rating']) / new_count
            
            ratings['average'] = Decimal(str(round(new_avg, 2)))
            ratings['count'] = new_count
            ratings['reviews'].append({
                'booking_id': booking_id,
                'rating': rating_data['equipment_rating'],
                'review': rating_data.get('review', ''),
                'timestamp': int(datetime.now().timestamp())
            })
            
            resource['ratings'] = ratings
            self.resource_table.put_item(Item=resource)
            
            logger.info(f"Equipment rated: {resource_id}, new average: {new_avg:.2f}")
            
            return {
                'success': True,
                'message': 'Rating submitted successfully',
                'new_average_rating': round(new_avg, 2),
                'total_ratings': new_count
            }
        
        except Exception as e:
            logger.error(f"Rating error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_unused_equipment_alerts(self, days_threshold: int = 30) -> Dict[str, Any]:
        """
        Send alerts for unused equipment
        
        Args:
            days_threshold: Days of inactivity threshold
        
        Returns:
            Dict with alert results
        """
        try:
            current_time = int(datetime.now().timestamp())
            threshold_time = current_time - (days_threshold * 24 * 60 * 60)
            
            # Find unused equipment
            response = self.resource_table.scan()
            resources = response.get('Items', [])
            
            alerts_sent = 0
            
            for resource in resources:
                last_used = resource.get('last_used_timestamp', 0)
                
                if last_used < threshold_time:
                    # Calculate potential income
                    potential_income = self._calculate_potential_income(resource)
                    
                    # Send alert (in production, use SNS)
                    alert_message = f"""
आपका {resource['equipment_details']['name']} पिछले {days_threshold} दिनों से उपयोग नहीं हुआ है।

संभावित मासिक आय: ₹{potential_income}

क्या आप इसे साझा करना चाहेंगे?
"""
                    
                    logger.info(f"Alert sent for resource: {resource['resource_id']}")
                    alerts_sent += 1
            
            return {
                'success': True,
                'alerts_sent': alerts_sent,
                'message': f'Sent {alerts_sent} unused equipment alerts'
            }
        
        except Exception as e:
            logger.error(f"Unused equipment alerts error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_distance(self,
                           loc1: Dict[str, Any],
                           loc2: Dict[str, Any]) -> float:
        """Calculate distance between two locations in kilometers"""
        from math import radians, sin, cos, sqrt, atan2
        
        lat1 = radians(float(loc1.get('latitude', 0)))
        lon1 = radians(float(loc1.get('longitude', 0)))
        lat2 = radians(float(loc2.get('latitude', 0)))
        lon2 = radians(float(loc2.get('longitude', 0)))
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return 6371 * c  # Earth radius in km
    
    def _check_availability(self,
                           resource_id: str,
                           date_range: Dict[str, str]) -> bool:
        """Check if equipment is available for date range"""
        # Query bookings for this resource
        response = self.booking_table.scan(
            FilterExpression='resource_id = :rid AND #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':rid': resource_id,
                ':status': 'confirmed'
            }
        )
        
        bookings = response.get('Items', [])
        
        start = datetime.fromisoformat(date_range['start'])
        end = datetime.fromisoformat(date_range['end'])
        
        for booking in bookings:
            booking_start = datetime.fromisoformat(booking['booking_start'])
            booking_end = datetime.fromisoformat(booking['booking_end'])
            
            # Check for overlap
            if not (end <= booking_start or start >= booking_end):
                return False
        
        return True
    
    def _verify_availability(self,
                            resource_id: str,
                            start_time: str,
                            end_time: str) -> bool:
        """Verify equipment availability for booking"""
        return self._check_availability(resource_id, {'start': start_time, 'end': end_time})
    
    def _calculate_booking_cost(self,
                               resource: Dict[str, Any],
                               booking_details: Dict[str, Any]) -> float:
        """Calculate total booking cost"""
        start = datetime.fromisoformat(booking_details['start_time'])
        end = datetime.fromisoformat(booking_details['end_time'])
        
        duration_hours = (end - start).total_seconds() / 3600
        duration_days = duration_hours / 24
        
        hourly_rate = float(resource['equipment_details'].get('hourly_rate', 0))
        daily_rate = float(resource['equipment_details'].get('daily_rate', 0))
        
        # Use daily rate if booking is for full days
        if duration_days >= 1 and duration_hours % 24 == 0:
            return daily_rate * duration_days
        else:
            return hourly_rate * duration_hours
    
    def _calculate_potential_income(self, resource: Dict[str, Any]) -> float:
        """Calculate potential monthly income from equipment"""
        daily_rate = float(resource['equipment_details'].get('daily_rate', 0))
        
        # Assume 50% utilization rate
        utilization_rate = 0.5
        days_per_month = 30
        
        return daily_rate * days_per_month * utilization_rate
    
    def _update_resource_availability(self,
                                     resource_id: str,
                                     booking_details: Dict[str, Any]) -> None:
        """Update resource availability after booking"""
        # In production, update availability calendar
        pass
    
    def _generate_pickup_instructions(self, resource: Dict[str, Any]) -> str:
        """Generate pickup instructions for equipment"""
        location = resource['location']
        equipment = resource['equipment_details']
        
        instructions = f"""
Equipment Pickup Instructions:

Equipment: {equipment['name']} ({equipment.get('model', 'N/A')})
Location: {location.get('address', '')}, {location['district']}, {location['state']}

Pickup Details:
1. Contact owner before pickup
2. Inspect equipment condition
3. Verify insurance coverage
4. Take photos before use
5. Follow safety guidelines

{resource.get('pickup_instructions', '')}
"""
        return instructions.strip()


# Tool functions for agent integration

def create_equipment_sharing_tools(region: str = "us-east-1") -> EquipmentSharingTools:
    """
    Factory function to create equipment sharing tools instance
    
    Args:
        region: AWS region
    
    Returns:
        EquipmentSharingTools instance
    """
    return EquipmentSharingTools(region=region)

    def process_payment(self,
                       booking_id: str,
                       payment_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process payment for equipment booking
        
        Args:
            booking_id: Booking ID
            payment_details: Payment information
        
        Returns:
            Dict with payment result
        """
        try:
            # Get booking details
            booking_response = self.booking_table.get_item(Key={'booking_id': booking_id})
            if 'Item' not in booking_response:
                return {
                    'success': False,
                    'error': 'Booking not found'
                }
            
            booking = booking_response['Item']
            
            # Verify payment amount
            expected_amount = float(booking.get('final_amount', booking.get('total_cost', 0)))
            provided_amount = payment_details.get('amount', 0)
            
            if abs(provided_amount - expected_amount) > 0.01:
                return {
                    'success': False,
                    'error': f'Payment amount mismatch. Expected: ₹{expected_amount:.2f}, Provided: ₹{provided_amount:.2f}'
                }
            
            # Generate transaction ID
            transaction_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"
            
            # Update booking with payment details
            booking['payment_status'] = 'completed'
            booking['payment_details'] = {
                'transaction_id': transaction_id,
                'payment_method': payment_details.get('payment_method', 'upi'),
                'payment_timestamp': int(datetime.now().timestamp()),
                'amount_paid': Decimal(str(provided_amount)),
                'payment_reference': payment_details.get('reference', '')
            }
            booking['status'] = 'paid'
            booking['updated_timestamp'] = int(datetime.now().timestamp())
            
            self.booking_table.put_item(Item=booking)
            
            logger.info(f"Payment processed for booking: {booking_id}, transaction: {transaction_id}")
            
            return {
                'success': True,
                'transaction_id': transaction_id,
                'booking_id': booking_id,
                'amount_paid': provided_amount,
                'payment_status': 'completed',
                'payment_method': payment_details.get('payment_method', 'upi'),
                'message': 'Payment processed successfully'
            }
        
        except Exception as e:
            logger.error(f"Payment processing error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_usage_tracking(self,
                             booking_id: str,
                             usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update equipment usage tracking
        
        Args:
            booking_id: Booking ID
            usage_data: Usage tracking information
        
        Returns:
            Dict with update result
        """
        try:
            # Get booking details
            booking_response = self.booking_table.get_item(Key={'booking_id': booking_id})
            if 'Item' not in booking_response:
                return {
                    'success': False,
                    'error': 'Booking not found'
                }
            
            booking = booking_response['Item']
            
            # Update usage tracking
            usage_tracking = booking.get('usage_tracking', {})
            
            if 'start_reading' in usage_data:
                usage_tracking['start_reading'] = usage_data['start_reading']
                usage_tracking['actual_start_time'] = usage_data.get('actual_start_time', datetime.now().isoformat())
            
            if 'end_reading' in usage_data:
                usage_tracking['end_reading'] = usage_data['end_reading']
                usage_tracking['actual_end_time'] = usage_data.get('actual_end_time', datetime.now().isoformat())
                
                # Calculate hours used
                if usage_tracking.get('start_reading') and usage_tracking.get('end_reading'):
                    hours_used = usage_tracking['end_reading'] - usage_tracking['start_reading']
                    usage_tracking['hours_used'] = hours_used
            
            booking['usage_tracking'] = usage_tracking
            booking['updated_timestamp'] = int(datetime.now().timestamp())
            
            # Update delivery status
            if 'start_reading' in usage_data and not booking.get('delivery_status') == 'completed':
                booking['delivery_status'] = 'in_use'
            
            if 'end_reading' in usage_data:
                booking['delivery_status'] = 'completed'
                booking['status'] = 'completed'
            
            self.booking_table.put_item(Item=booking)
            
            logger.info(f"Usage tracking updated for booking: {booking_id}")
            
            return {
                'success': True,
                'booking_id': booking_id,
                'usage_tracking': usage_tracking,
                'message': 'Usage tracking updated successfully'
            }
        
        except Exception as e:
            logger.error(f"Usage tracking update error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_booking_details(self, booking_id: str) -> Dict[str, Any]:
        """
        Get detailed booking information
        
        Args:
            booking_id: Booking ID
        
        Returns:
            Dict with booking details
        """
        try:
            booking_response = self.booking_table.get_item(Key={'booking_id': booking_id})
            
            if 'Item' not in booking_response:
                return {
                    'success': False,
                    'error': 'Booking not found'
                }
            
            booking = booking_response['Item']
            
            # Get resource details
            resource_response = self.resource_table.get_item(Key={'resource_id': booking['resource_id']})
            resource = resource_response.get('Item', {})
            
            return {
                'success': True,
                'booking_id': booking_id,
                'booking': {
                    'resource_id': booking['resource_id'],
                    'renter_user_id': booking['renter_user_id'],
                    'owner_user_id': booking['owner_user_id'],
                    'booking_start': booking['booking_start'],
                    'booking_end': booking['booking_end'],
                    'total_cost': float(booking.get('total_cost', 0)),
                    'insurance_premium': float(booking.get('insurance_premium', 0)),
                    'transport_cost': float(booking.get('transport_cost', 0)),
                    'final_amount': float(booking.get('final_amount', booking.get('total_cost', 0))),
                    'payment_status': booking['payment_status'],
                    'payment_details': booking.get('payment_details', {}),
                    'usage_tracking': booking.get('usage_tracking', {}),
                    'insurance_details': booking.get('insurance_details', {}),
                    'status': booking['status'],
                    'delivery_status': booking.get('delivery_status', 'pending'),
                    'created_timestamp': booking['created_timestamp'],
                    'updated_timestamp': booking.get('updated_timestamp', booking['created_timestamp'])
                },
                'equipment': {
                    'name': resource.get('equipment_details', {}).get('name', 'Unknown'),
                    'type': resource.get('resource_type', 'Unknown'),
                    'model': resource.get('equipment_details', {}).get('model', ''),
                    'location': resource.get('location', {})
                }
            }
        
        except Exception as e:
            logger.error(f"Get booking details error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_bookings(self,
                         user_id: str,
                         booking_type: str = 'renter') -> Dict[str, Any]:
        """
        Get all bookings for a user (as renter or owner)
        
        Args:
            user_id: User ID
            booking_type: 'renter' or 'owner'
        
        Returns:
            Dict with user bookings
        """
        try:
            # Query bookings
            if booking_type == 'renter':
                filter_expression = 'renter_user_id = :uid'
            else:
                filter_expression = 'owner_user_id = :uid'
            
            response = self.booking_table.scan(
                FilterExpression=filter_expression,
                ExpressionAttributeValues={':uid': user_id}
            )
            
            bookings = response.get('Items', [])
            
            # Sort by created timestamp (newest first)
            bookings.sort(key=lambda x: x.get('created_timestamp', 0), reverse=True)
            
            # Format bookings
            formatted_bookings = []
            for booking in bookings:
                # Get resource details
                resource_response = self.resource_table.get_item(Key={'resource_id': booking['resource_id']})
                resource = resource_response.get('Item', {})
                
                formatted_bookings.append({
                    'booking_id': booking['booking_id'],
                    'resource_id': booking['resource_id'],
                    'equipment_name': resource.get('equipment_details', {}).get('name', 'Unknown'),
                    'equipment_type': resource.get('resource_type', 'Unknown'),
                    'booking_start': booking['booking_start'],
                    'booking_end': booking['booking_end'],
                    'total_cost': float(booking.get('total_cost', 0)),
                    'final_amount': float(booking.get('final_amount', booking.get('total_cost', 0))),
                    'payment_status': booking['payment_status'],
                    'status': booking['status'],
                    'delivery_status': booking.get('delivery_status', 'pending'),
                    'created_timestamp': booking['created_timestamp']
                })
            
            logger.info(f"Retrieved {len(formatted_bookings)} bookings for user: {user_id}")
            
            return {
                'success': True,
                'count': len(formatted_bookings),
                'bookings': formatted_bookings,
                'user_id': user_id,
                'booking_type': booking_type
            }
        
        except Exception as e:
            logger.error(f"Get user bookings error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_booking(self,
                      booking_id: str,
                      cancellation_reason: str = '') -> Dict[str, Any]:
        """
        Cancel an equipment booking
        
        Args:
            booking_id: Booking ID
            cancellation_reason: Reason for cancellation
        
        Returns:
            Dict with cancellation result
        """
        try:
            # Get booking details
            booking_response = self.booking_table.get_item(Key={'booking_id': booking_id})
            if 'Item' not in booking_response:
                return {
                    'success': False,
                    'error': 'Booking not found'
                }
            
            booking = booking_response['Item']
            
            # Check if booking can be cancelled
            if booking['status'] in ['completed', 'cancelled']:
                return {
                    'success': False,
                    'error': f'Cannot cancel booking with status: {booking["status"]}'
                }
            
            # Calculate refund amount
            refund_amount = 0
            if booking['payment_status'] == 'completed':
                # Full refund if cancelled 24 hours before start
                booking_start = datetime.fromisoformat(booking['booking_start'])
                hours_until_start = (booking_start - datetime.now()).total_seconds() / 3600
                
                if hours_until_start >= 24:
                    refund_amount = float(booking.get('final_amount', booking.get('total_cost', 0)))
                elif hours_until_start >= 12:
                    refund_amount = float(booking.get('final_amount', booking.get('total_cost', 0))) * 0.5
                # No refund if less than 12 hours
            
            # Update booking status
            booking['status'] = 'cancelled'
            booking['cancellation_details'] = {
                'reason': cancellation_reason,
                'cancelled_timestamp': int(datetime.now().timestamp()),
                'refund_amount': Decimal(str(refund_amount))
            }
            booking['updated_timestamp'] = int(datetime.now().timestamp())
            
            self.booking_table.put_item(Item=booking)
            
            logger.info(f"Booking cancelled: {booking_id}, refund: ₹{refund_amount:.2f}")
            
            return {
                'success': True,
                'booking_id': booking_id,
                'status': 'cancelled',
                'refund_amount': refund_amount,
                'message': f'Booking cancelled successfully. Refund amount: ₹{refund_amount:.2f}'
            }
        
        except Exception as e:
            logger.error(f"Booking cancellation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
