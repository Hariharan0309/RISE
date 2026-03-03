"""
RISE Local Economy Tracking Tools
Tools for tracking economic impact, cost savings, and community metrics
"""

import boto3
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

logger = logging.getLogger(__name__)


class LocalEconomyTools:
    """Local economy tracking tools for RISE farming assistant"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize local economy tools with AWS clients
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # DynamoDB tables
        self.resource_table = self.dynamodb.Table('RISE-ResourceSharing')
        self.booking_table = self.dynamodb.Table('RISE-ResourceBookings')
        self.groups_table = self.dynamodb.Table('RISE-BuyingGroups')
        self.user_profiles_table = self.dynamodb.Table('RISE-UserProfiles')
        
        logger.info(f"Local economy tools initialized in region {region}")
    
    def calculate_economic_impact(self,
                                 location: Dict[str, Any],
                                 time_period: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive economic impact metrics for a location
        
        Args:
            location: Location details (state, district)
            time_period: Optional time period for analysis
        
        Returns:
            Dict with economic impact metrics
        """
        try:
            # Default to last 30 days if no time period specified
            if not time_period:
                end_time = datetime.now()
                start_time = end_time - timedelta(days=30)
                time_period = {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            
            # Calculate all metrics
            equipment_utilization = self._calculate_equipment_utilization(location, time_period)
            cost_savings = self._calculate_cost_savings(location, time_period)
            additional_income = self._calculate_additional_income(location, time_period)
            cooperative_savings = self._calculate_cooperative_savings(location, time_period)
            transaction_count = self._count_transactions(location, time_period)
            engagement_score = self._calculate_engagement_score(location, time_period)
            sustainability_metrics = self._calculate_sustainability_metrics(location, time_period)
            
            # Calculate total economic benefit
            total_benefit = cost_savings['total'] + additional_income['total'] + cooperative_savings['total']
            
            logger.info(f"Economic impact calculated for {location['district']}, {location['state']}")
            
            return {
                'success': True,
                'location': location,
                'time_period': time_period,
                'metrics': {
                    'equipment_utilization_rate': equipment_utilization,
                    'cost_savings': cost_savings,
                    'additional_income': additional_income,
                    'cooperative_buying_savings': cooperative_savings,
                    'transaction_count': transaction_count,
                    'community_engagement_score': engagement_score,
                    'sustainability_metrics': sustainability_metrics,
                    'total_economic_benefit': round(total_benefit, 2)
                },
                'summary': {
                    'total_farmers_benefited': transaction_count['unique_farmers'],
                    'total_transactions': transaction_count['total'],
                    'average_savings_per_farmer': round(total_benefit / max(transaction_count['unique_farmers'], 1), 2),
                    'engagement_level': self._get_engagement_level(engagement_score)
                }
            }
        
        except Exception as e:
            logger.error(f"Economic impact calculation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def track_cost_savings(self,
                          user_id: str,
                          time_period: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Track cost savings for a specific farmer
        
        Args:
            user_id: Farmer's user ID
            time_period: Optional time period for analysis
        
        Returns:
            Dict with cost savings breakdown
        """
        try:
            # Default to last 30 days
            if not time_period:
                end_time = datetime.now()
                start_time = end_time - timedelta(days=30)
                time_period = {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            
            start_timestamp = int(datetime.fromisoformat(time_period['start']).timestamp())
            end_timestamp = int(datetime.fromisoformat(time_period['end']).timestamp())
            
            # Calculate savings from equipment rentals (vs buying)
            rental_savings = self._calculate_rental_savings(user_id, start_timestamp, end_timestamp)
            
            # Calculate savings from cooperative buying
            buying_savings = self._calculate_user_buying_savings(user_id, start_timestamp, end_timestamp)
            
            # Total savings
            total_savings = rental_savings['total'] + buying_savings['total']
            
            logger.info(f"Cost savings tracked for user {user_id}: ₹{total_savings}")
            
            return {
                'success': True,
                'user_id': user_id,
                'time_period': time_period,
                'savings_breakdown': {
                    'equipment_rental_savings': rental_savings,
                    'cooperative_buying_savings': buying_savings,
                    'total_savings': round(total_savings, 2)
                },
                'comparison': {
                    'vs_equipment_purchase': rental_savings['vs_purchase'],
                    'vs_retail_prices': buying_savings['vs_retail']
                }
            }
        
        except Exception as e:
            logger.error(f"Cost savings tracking error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def track_additional_income(self,
                               user_id: str,
                               time_period: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Track additional income generated from resource sharing
        
        Args:
            user_id: Farmer's user ID
            time_period: Optional time period for analysis
        
        Returns:
            Dict with income breakdown
        """
        try:
            # Default to last 30 days
            if not time_period:
                end_time = datetime.now()
                start_time = end_time - timedelta(days=30)
                time_period = {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            
            start_timestamp = int(datetime.fromisoformat(time_period['start']).timestamp())
            end_timestamp = int(datetime.fromisoformat(time_period['end']).timestamp())
            
            # Get all bookings where user is the owner
            response = self.booking_table.scan(
                FilterExpression='owner_user_id = :uid AND created_timestamp BETWEEN :start AND :end',
                ExpressionAttributeValues={
                    ':uid': user_id,
                    ':start': start_timestamp,
                    ':end': end_timestamp
                }
            )
            
            bookings = response.get('Items', [])
            
            # Calculate income by equipment type
            income_by_type = defaultdict(lambda: {'count': 0, 'total': 0})
            total_income = 0
            
            for booking in bookings:
                if booking.get('payment_status') == 'completed':
                    amount = float(booking.get('total_cost', 0))
                    total_income += amount
                    
                    # Get resource type
                    resource_id = booking['resource_id']
                    resource_response = self.resource_table.get_item(Key={'resource_id': resource_id})
                    if 'Item' in resource_response:
                        resource_type = resource_response['Item']['resource_type']
                        income_by_type[resource_type]['count'] += 1
                        income_by_type[resource_type]['total'] += amount
            
            # Calculate projections
            days_in_period = (datetime.fromisoformat(time_period['end']) - 
                            datetime.fromisoformat(time_period['start'])).days
            monthly_projection = (total_income / max(days_in_period, 1)) * 30
            annual_projection = monthly_projection * 12
            
            logger.info(f"Additional income tracked for user {user_id}: ₹{total_income}")
            
            return {
                'success': True,
                'user_id': user_id,
                'time_period': time_period,
                'income_breakdown': {
                    'by_equipment_type': {k: {'count': v['count'], 'total': round(v['total'], 2)} 
                                         for k, v in income_by_type.items()},
                    'total_income': round(total_income, 2),
                    'total_bookings': len(bookings),
                    'completed_bookings': sum(1 for b in bookings if b.get('payment_status') == 'completed')
                },
                'projections': {
                    'monthly': round(monthly_projection, 2),
                    'annual': round(annual_projection, 2)
                }
            }
        
        except Exception as e:
            logger.error(f"Additional income tracking error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_resource_utilization(self,
                                      location: Dict[str, Any],
                                      time_period: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Calculate resource utilization rates for a location
        
        Args:
            location: Location details
            time_period: Optional time period for analysis
        
        Returns:
            Dict with utilization metrics
        """
        try:
            utilization_data = self._calculate_equipment_utilization(location, time_period)
            
            return {
                'success': True,
                'location': location,
                'time_period': time_period,
                'utilization_metrics': utilization_data
            }
        
        except Exception as e:
            logger.error(f"Resource utilization calculation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_sustainability_metrics(self,
                                       location: Dict[str, Any],
                                       time_period: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Generate sustainability metrics for resource sharing
        
        Args:
            location: Location details
            time_period: Optional time period for analysis
        
        Returns:
            Dict with sustainability metrics
        """
        try:
            metrics = self._calculate_sustainability_metrics(location, time_period)
            
            return {
                'success': True,
                'location': location,
                'time_period': time_period,
                'sustainability_metrics': metrics
            }
        
        except Exception as e:
            logger.error(f"Sustainability metrics generation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_community_network_data(self,
                                   location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get community network visualization data
        
        Args:
            location: Location details
        
        Returns:
            Dict with network data for visualization
        """
        try:
            # Get all users in location
            response = self.user_profiles_table.scan()
            users = response.get('Items', [])
            
            local_users = [u for u in users 
                          if u.get('location', {}).get('district') == location.get('district') and
                             u.get('location', {}).get('state') == location.get('state')]
            
            # Build network connections
            connections = []
            
            # Equipment sharing connections
            booking_response = self.booking_table.scan()
            bookings = booking_response.get('Items', [])
            
            for booking in bookings:
                owner_id = booking.get('owner_user_id')
                renter_id = booking.get('renter_user_id')
                
                if owner_id and renter_id:
                    connections.append({
                        'source': owner_id,
                        'target': renter_id,
                        'type': 'equipment_sharing',
                        'value': float(booking.get('total_cost', 0))
                    })
            
            # Buying group connections
            groups_response = self.groups_table.scan()
            groups = groups_response.get('Items', [])
            
            for group in groups:
                members = group.get('members', [])
                organizer = group.get('organizer_user_id')
                
                # Connect organizer to all members
                for member in members:
                    if member != organizer:
                        connections.append({
                            'source': organizer,
                            'target': member,
                            'type': 'buying_group',
                            'group_id': group['group_id']
                        })
            
            # Calculate network statistics
            unique_participants = set()
            for conn in connections:
                unique_participants.add(conn['source'])
                unique_participants.add(conn['target'])
            
            logger.info(f"Community network data generated for {location['district']}, {location['state']}")
            
            return {
                'success': True,
                'location': location,
                'network': {
                    'nodes': [{'id': user['user_id'], 'name': user.get('name', 'Unknown')} 
                             for user in local_users],
                    'connections': connections
                },
                'statistics': {
                    'total_users': len(local_users),
                    'active_participants': len(unique_participants),
                    'total_connections': len(connections),
                    'equipment_sharing_connections': sum(1 for c in connections if c['type'] == 'equipment_sharing'),
                    'buying_group_connections': sum(1 for c in connections if c['type'] == 'buying_group')
                }
            }
        
        except Exception as e:
            logger.error(f"Community network data error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    # Helper methods
    
    def _calculate_equipment_utilization(self,
                                        location: Dict[str, Any],
                                        time_period: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Calculate equipment utilization rates"""
        # Get all resources in location
        response = self.resource_table.scan()
        resources = response.get('Items', [])
        
        local_resources = [r for r in resources 
                          if r.get('location', {}).get('district') == location.get('district') and
                             r.get('location', {}).get('state') == location.get('state')]
        
        if not local_resources:
            return {
                'overall_rate': 0,
                'by_type': {},
                'total_equipment': 0
            }
        
        # Calculate utilization by type
        utilization_by_type = defaultdict(lambda: {'total': 0, 'utilized': 0})
        
        for resource in local_resources:
            resource_type = resource['resource_type']
            utilization_by_type[resource_type]['total'] += 1
            
            # Check if resource has recent bookings
            if resource.get('last_used_timestamp', 0) > 0:
                utilization_by_type[resource_type]['utilized'] += 1
        
        # Calculate rates
        overall_utilized = sum(v['utilized'] for v in utilization_by_type.values())
        overall_total = len(local_resources)
        overall_rate = (overall_utilized / overall_total * 100) if overall_total > 0 else 0
        
        by_type = {
            k: {
                'rate': round((v['utilized'] / v['total'] * 100) if v['total'] > 0 else 0, 1),
                'total': v['total'],
                'utilized': v['utilized']
            }
            for k, v in utilization_by_type.items()
        }
        
        return {
            'overall_rate': round(overall_rate, 1),
            'by_type': by_type,
            'total_equipment': overall_total
        }
    
    def _calculate_cost_savings(self,
                               location: Dict[str, Any],
                               time_period: Dict[str, str]) -> Dict[str, Any]:
        """Calculate total cost savings in location"""
        start_timestamp = int(datetime.fromisoformat(time_period['start']).timestamp())
        end_timestamp = int(datetime.fromisoformat(time_period['end']).timestamp())
        
        # Get all bookings in time period
        response = self.booking_table.scan(
            FilterExpression='created_timestamp BETWEEN :start AND :end',
            ExpressionAttributeValues={
                ':start': start_timestamp,
                ':end': end_timestamp
            }
        )
        
        bookings = response.get('Items', [])
        total_savings = 0
        
        # Estimate savings (rental cost vs purchase cost)
        for booking in bookings:
            rental_cost = float(booking.get('total_cost', 0))
            # Assume equipment purchase would cost 50x the rental
            purchase_cost = rental_cost * 50
            savings = purchase_cost - rental_cost
            total_savings += savings
        
        return {
            'total': round(total_savings, 2),
            'from_equipment_sharing': round(total_savings, 2),
            'transaction_count': len(bookings)
        }
    
    def _calculate_additional_income(self,
                                    location: Dict[str, Any],
                                    time_period: Dict[str, str]) -> Dict[str, Any]:
        """Calculate total additional income generated"""
        start_timestamp = int(datetime.fromisoformat(time_period['start']).timestamp())
        end_timestamp = int(datetime.fromisoformat(time_period['end']).timestamp())
        
        response = self.booking_table.scan(
            FilterExpression='created_timestamp BETWEEN :start AND :end AND payment_status = :status',
            ExpressionAttributeValues={
                ':start': start_timestamp,
                ':end': end_timestamp,
                ':status': 'completed'
            }
        )
        
        bookings = response.get('Items', [])
        total_income = sum(float(b.get('total_cost', 0)) for b in bookings)
        
        return {
            'total': round(total_income, 2),
            'from_equipment_sharing': round(total_income, 2),
            'transaction_count': len(bookings)
        }
    
    def _calculate_cooperative_savings(self,
                                      location: Dict[str, Any],
                                      time_period: Dict[str, str]) -> Dict[str, Any]:
        """Calculate savings from cooperative buying"""
        # Get all groups in location
        location_key = f"{location.get('district')}_{location.get('state')}"
        
        response = self.groups_table.scan(
            FilterExpression='location_area = :loc',
            ExpressionAttributeValues={
                ':loc': location_key
            }
        )
        
        groups = response.get('Items', [])
        total_savings = 0
        
        for group in groups:
            # Calculate savings based on bulk pricing achieved
            bulk_pricing = group.get('bulk_pricing_achieved', {})
            total_quantities = group.get('total_quantity_needed', {})
            
            for product, discount_pct in bulk_pricing.items():
                if product in total_quantities:
                    quantity = float(total_quantities[product])
                    # Assume ₹1000 per unit market price
                    market_price = 1000
                    savings = market_price * quantity * (float(discount_pct) / 100)
                    total_savings += savings
        
        return {
            'total': round(total_savings, 2),
            'from_bulk_buying': round(total_savings, 2),
            'group_count': len(groups)
        }
    
    def _count_transactions(self,
                           location: Dict[str, Any],
                           time_period: Dict[str, str]) -> Dict[str, Any]:
        """Count resource sharing transactions"""
        start_timestamp = int(datetime.fromisoformat(time_period['start']).timestamp())
        end_timestamp = int(datetime.fromisoformat(time_period['end']).timestamp())
        
        response = self.booking_table.scan(
            FilterExpression='created_timestamp BETWEEN :start AND :end',
            ExpressionAttributeValues={
                ':start': start_timestamp,
                ':end': end_timestamp
            }
        )
        
        bookings = response.get('Items', [])
        
        # Count unique farmers
        unique_farmers = set()
        for booking in bookings:
            unique_farmers.add(booking.get('owner_user_id'))
            unique_farmers.add(booking.get('renter_user_id'))
        
        return {
            'total': len(bookings),
            'unique_farmers': len(unique_farmers),
            'equipment_sharing': len(bookings)
        }
    
    def _calculate_engagement_score(self,
                                   location: Dict[str, Any],
                                   time_period: Dict[str, str]) -> float:
        """Calculate community engagement score (0-100)"""
        # Get metrics
        transaction_count = self._count_transactions(location, time_period)
        utilization = self._calculate_equipment_utilization(location, time_period)
        
        # Calculate score based on multiple factors
        transaction_score = min(transaction_count['total'] / 10 * 30, 30)  # Max 30 points
        utilization_score = utilization['overall_rate'] * 0.4  # Max 40 points
        participation_score = min(transaction_count['unique_farmers'] / 20 * 30, 30)  # Max 30 points
        
        total_score = transaction_score + utilization_score + participation_score
        
        return round(total_score, 1)
    
    def _calculate_sustainability_metrics(self,
                                         location: Dict[str, Any],
                                         time_period: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Calculate sustainability metrics"""
        # Get equipment sharing data
        utilization = self._calculate_equipment_utilization(location, time_period)
        
        # Estimate environmental impact
        total_equipment = utilization['total_equipment']
        utilization_rate = utilization['overall_rate']
        
        # Estimate equipment that didn't need to be purchased
        equipment_saved = int(total_equipment * (utilization_rate / 100))
        
        # Estimate CO2 savings (manufacturing + transport)
        co2_per_equipment = 5000  # kg CO2 per equipment
        co2_saved = equipment_saved * co2_per_equipment
        
        # Estimate resource efficiency
        resource_efficiency = utilization_rate  # Higher utilization = better efficiency
        
        return {
            'equipment_purchases_avoided': equipment_saved,
            'estimated_co2_savings_kg': co2_saved,
            'resource_efficiency_score': round(resource_efficiency, 1),
            'shared_equipment_count': total_equipment,
            'sustainability_level': self._get_sustainability_level(resource_efficiency)
        }
    
    def _calculate_rental_savings(self,
                                 user_id: str,
                                 start_timestamp: int,
                                 end_timestamp: int) -> Dict[str, Any]:
        """Calculate savings from renting vs buying equipment"""
        response = self.booking_table.scan(
            FilterExpression='renter_user_id = :uid AND created_timestamp BETWEEN :start AND :end',
            ExpressionAttributeValues={
                ':uid': user_id,
                ':start': start_timestamp,
                ':end': end_timestamp
            }
        )
        
        bookings = response.get('Items', [])
        total_rental_cost = sum(float(b.get('total_cost', 0)) for b in bookings)
        
        # Estimate purchase cost (50x rental cost)
        estimated_purchase_cost = total_rental_cost * 50
        savings = estimated_purchase_cost - total_rental_cost
        
        return {
            'total': round(savings, 2),
            'rental_cost': round(total_rental_cost, 2),
            'vs_purchase': round(estimated_purchase_cost, 2),
            'booking_count': len(bookings)
        }
    
    def _calculate_user_buying_savings(self,
                                      user_id: str,
                                      start_timestamp: int,
                                      end_timestamp: int) -> Dict[str, Any]:
        """Calculate savings from cooperative buying"""
        # Get user's buying groups
        response = self.groups_table.scan()
        groups = response.get('Items', [])
        
        user_groups = [g for g in groups if user_id in g.get('members', [])]
        
        total_savings = 0
        
        for group in user_groups:
            member_requirements = group.get('member_requirements', {}).get(user_id, {})
            bulk_pricing = group.get('bulk_pricing_achieved', {})
            
            for product, quantity in member_requirements.items():
                if product in bulk_pricing:
                    discount_pct = float(bulk_pricing[product])
                    # Assume ₹1000 per unit market price
                    market_price = 1000
                    savings = market_price * float(quantity) * (discount_pct / 100)
                    total_savings += savings
        
        # Estimate retail cost
        retail_cost = total_savings / 0.2 if total_savings > 0 else 0  # Assuming 20% average discount
        
        return {
            'total': round(total_savings, 2),
            'vs_retail': round(retail_cost, 2),
            'group_count': len(user_groups)
        }
    
    def _get_engagement_level(self, score: float) -> str:
        """Get engagement level description"""
        if score >= 80:
            return 'Excellent'
        elif score >= 60:
            return 'Good'
        elif score >= 40:
            return 'Moderate'
        elif score >= 20:
            return 'Low'
        else:
            return 'Very Low'
    
    def _get_sustainability_level(self, score: float) -> str:
        """Get sustainability level description"""
        if score >= 80:
            return 'Highly Sustainable'
        elif score >= 60:
            return 'Sustainable'
        elif score >= 40:
            return 'Moderately Sustainable'
        else:
            return 'Needs Improvement'


# Tool functions for agent integration

def create_local_economy_tools(region: str = "us-east-1") -> LocalEconomyTools:
    """
    Factory function to create local economy tools instance
    
    Args:
        region: AWS region
    
    Returns:
        LocalEconomyTools instance
    """
    return LocalEconomyTools(region=region)
