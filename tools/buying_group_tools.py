"""
RISE Cooperative Buying Groups Tools
Tools for forming buying groups, matching farmers, and negotiating bulk pricing
"""

import boto3
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class BuyingGroupTools:
    """Cooperative buying groups tools for RISE farming assistant"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize buying group tools with AWS clients
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        
        # DynamoDB tables
        self.groups_table = self.dynamodb.Table('RISE-BuyingGroups')
        self.user_profiles_table = self.dynamodb.Table('RISE-UserProfiles')
        
        logger.info(f"Buying group tools initialized in region {region}")
    
    def create_buying_group(self,
                           organizer_id: str,
                           group_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new cooperative buying group
        
        Args:
            organizer_id: Group organizer's user ID
            group_data: Group details including products, location, etc.
        
        Returns:
            Dict with group creation result
        """
        try:
            group_id = f"grp_{uuid.uuid4().hex[:8]}"
            
            group_item = {
                'group_id': group_id,
                'group_name': group_data['group_name'],
                'organizer_user_id': organizer_id,
                'members': [organizer_id],
                'target_products': group_data['target_products'],  # List of products to buy
                'location_area': f"{group_data['location']['district']}_{group_data['location']['state']}",
                'location': {
                    'state': group_data['location']['state'],
                    'district': group_data['location']['district'],
                    'radius_km': group_data['location'].get('radius_km', 25)
                },
                'group_status': 'forming',  # forming, active, negotiating, completed, closed
                'total_quantity_needed': {},  # Will be calculated from member requirements
                'bulk_pricing_achieved': {},  # Product -> discount percentage
                'vendor_details': {},
                'delivery_schedule': {},
                'payment_status': {},  # Member -> payment status
                'member_requirements': {},  # Member -> product requirements
                'created_timestamp': int(datetime.now().timestamp()),
                'updated_timestamp': int(datetime.now().timestamp()),
                'target_discount_min': Decimal('15'),  # Minimum 15% discount target
                'target_discount_max': Decimal('30'),  # Maximum 30% discount target
                'max_members': group_data.get('max_members', 50),
                'min_members': group_data.get('min_members', 5),
                'deadline': group_data.get('deadline', (datetime.now() + timedelta(days=14)).isoformat())
            }
            
            # Store in DynamoDB
            self.groups_table.put_item(Item=group_item)
            
            logger.info(f"Buying group created: {group_id}")
            
            return {
                'success': True,
                'group_id': group_id,
                'group_name': group_data['group_name'],
                'status': 'forming',
                'message': f'Buying group "{group_data["group_name"]}" created successfully',
                'target_discount': '15-30%',
                'deadline': group_item['deadline']
            }
        
        except Exception as e:
            logger.error(f"Group creation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def find_matching_groups(self,
                            user_id: str,
                            requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find buying groups matching farmer's requirements
        
        Args:
            user_id: Farmer's user ID
            requirements: Product requirements and location
        
        Returns:
            Dict with matching groups
        """
        try:
            # Get user profile for location
            user_response = self.user_profiles_table.get_item(Key={'user_id': user_id})
            if 'Item' not in user_response:
                return {
                    'success': False,
                    'error': 'User profile not found'
                }
            
            user = user_response['Item']
            user_location = user.get('location', {})
            
            # Query groups by location
            location_key = f"{requirements.get('district', user_location.get('district'))}_{requirements.get('state', user_location.get('state'))}"
            
            response = self.groups_table.scan(
                FilterExpression='group_status IN (:forming, :active)',
                ExpressionAttributeValues={
                    ':forming': 'forming',
                    ':active': 'active'
                }
            )
            
            groups = response.get('Items', [])
            matching_groups = []
            
            required_products = set(requirements.get('products', []))
            
            for group in groups:
                # Check location match
                if group['location_area'] != location_key:
                    # Check if within radius
                    group_location = group['location']
                    if not self._is_within_radius(user_location, group_location):
                        continue
                
                # Check product match
                group_products = set(group['target_products'])
                matching_products = required_products.intersection(group_products)
                
                if not matching_products:
                    continue
                
                # Calculate match score
                match_score = len(matching_products) / len(required_products) * 100
                
                # Check if group has space
                current_members = len(group.get('members', []))
                max_members = group.get('max_members', 50)
                
                if current_members >= max_members:
                    continue
                
                matching_groups.append({
                    'group_id': group['group_id'],
                    'group_name': group['group_name'],
                    'organizer_user_id': group['organizer_user_id'],
                    'target_products': group['target_products'],
                    'matching_products': list(matching_products),
                    'match_score': round(match_score, 1),
                    'location': group['location'],
                    'current_members': current_members,
                    'max_members': max_members,
                    'status': group['group_status'],
                    'deadline': group.get('deadline', ''),
                    'estimated_discount': f"{float(group.get('target_discount_min', 15))}-{float(group.get('target_discount_max', 30))}%"
                })
            
            # Sort by match score
            matching_groups.sort(key=lambda x: x['match_score'], reverse=True)
            
            logger.info(f"Found {len(matching_groups)} matching groups for user {user_id}")
            
            return {
                'success': True,
                'count': len(matching_groups),
                'groups': matching_groups,
                'user_location': user_location
            }
        
        except Exception as e:
            logger.error(f"Group matching error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def join_buying_group(self,
                         user_id: str,
                         group_id: str,
                         member_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Join an existing buying group
        
        Args:
            user_id: Farmer's user ID
            group_id: Group ID to join
            member_requirements: Member's product requirements
        
        Returns:
            Dict with join result
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
            
            # Check if group is accepting members
            if group['group_status'] not in ['forming', 'active']:
                return {
                    'success': False,
                    'error': f'Group is not accepting new members (status: {group["group_status"]})'
                }
            
            # Check if already a member
            members = group.get('members', [])
            if user_id in members:
                return {
                    'success': False,
                    'error': 'Already a member of this group'
                }
            
            # Check if group is full
            if len(members) >= group.get('max_members', 50):
                return {
                    'success': False,
                    'error': 'Group is full'
                }
            
            # Add member
            members.append(user_id)
            
            # Update member requirements
            member_reqs = group.get('member_requirements', {})
            member_reqs[user_id] = member_requirements
            
            # Recalculate total quantities
            total_quantities = self._calculate_total_quantities(member_reqs)
            
            # Update group
            group['members'] = members
            group['member_requirements'] = member_reqs
            group['total_quantity_needed'] = total_quantities
            group['updated_timestamp'] = int(datetime.now().timestamp())
            
            # Check if minimum members reached
            if len(members) >= group.get('min_members', 5) and group['group_status'] == 'forming':
                group['group_status'] = 'active'
            
            self.groups_table.put_item(Item=group)
            
            # Calculate potential savings
            potential_savings = self._calculate_potential_savings(member_requirements, total_quantities)
            
            logger.info(f"User {user_id} joined group {group_id}")
            
            return {
                'success': True,
                'group_id': group_id,
                'group_name': group['group_name'],
                'status': group['group_status'],
                'total_members': len(members),
                'total_quantities': {k: float(v) for k, v in total_quantities.items()},
                'potential_savings': potential_savings,
                'message': f'Successfully joined "{group["group_name"]}"'
            }
        
        except Exception as e:
            logger.error(f"Join group error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_bulk_pricing(self,
                              group_id: str,
                              vendor_quotes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate bulk pricing discounts for group orders
        
        Args:
            group_id: Group ID
            vendor_quotes: Optional vendor quotes (if available)
        
        Returns:
            Dict with pricing calculations
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
            total_quantities = group.get('total_quantity_needed', {})
            
            if not total_quantities:
                return {
                    'success': False,
                    'error': 'No quantities specified yet'
                }
            
            # Calculate discount tiers based on quantity
            pricing_breakdown = {}
            
            for product, quantity in total_quantities.items():
                quantity_float = float(quantity)
                
                # Discount tiers (example logic)
                if quantity_float >= 1000:
                    discount_pct = 30
                elif quantity_float >= 500:
                    discount_pct = 25
                elif quantity_float >= 250:
                    discount_pct = 20
                elif quantity_float >= 100:
                    discount_pct = 15
                else:
                    discount_pct = 10
                
                # Use vendor quotes if available
                if vendor_quotes and product in vendor_quotes:
                    market_price = vendor_quotes[product]['market_price']
                    bulk_price = vendor_quotes[product]['bulk_price']
                    actual_discount = ((market_price - bulk_price) / market_price) * 100
                else:
                    # Estimate market price (in production, fetch from market data)
                    market_price = 1000  # Example: ₹1000 per unit
                    bulk_price = market_price * (1 - discount_pct / 100)
                    actual_discount = discount_pct
                
                total_cost = bulk_price * quantity_float
                savings = (market_price - bulk_price) * quantity_float
                
                pricing_breakdown[product] = {
                    'quantity': quantity_float,
                    'market_price_per_unit': market_price,
                    'bulk_price_per_unit': round(bulk_price, 2),
                    'discount_percentage': round(actual_discount, 1),
                    'total_cost': round(total_cost, 2),
                    'total_savings': round(savings, 2)
                }
            
            # Calculate per-member costs
            member_costs = self._calculate_member_costs(group, pricing_breakdown)
            
            # Update group with pricing
            group['bulk_pricing_achieved'] = {
                product: Decimal(str(data['discount_percentage']))
                for product, data in pricing_breakdown.items()
            }
            group['updated_timestamp'] = int(datetime.now().timestamp())
            self.groups_table.put_item(Item=group)
            
            logger.info(f"Bulk pricing calculated for group {group_id}")
            
            return {
                'success': True,
                'group_id': group_id,
                'pricing_breakdown': pricing_breakdown,
                'member_costs': member_costs,
                'total_members': len(group.get('members', [])),
                'average_discount': round(
                    sum(data['discount_percentage'] for data in pricing_breakdown.values()) / len(pricing_breakdown),
                    1
                )
            }
        
        except Exception as e:
            logger.error(f"Bulk pricing calculation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def negotiate_with_vendors(self,
                              group_id: str,
                              vendor_list: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Use AI to negotiate with suppliers for bulk pricing
        
        Args:
            group_id: Group ID
            vendor_list: Optional list of vendor names/contacts
        
        Returns:
            Dict with negotiation results
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
            total_quantities = group.get('total_quantity_needed', {})
            
            # Prepare negotiation prompt
            negotiation_prompt = f"""
You are a procurement specialist helping a cooperative buying group of {len(group.get('members', []))} farmers negotiate bulk pricing.

Group Details:
- Products needed: {', '.join(total_quantities.keys())}
- Quantities: {json.dumps({k: float(v) for k, v in total_quantities.items()}, indent=2)}
- Location: {group['location']['district']}, {group['location']['state']}
- Target discount: 15-30%

Generate a professional negotiation message to send to agricultural input suppliers. Include:
1. Introduction of the buying group
2. Specific quantities needed
3. Request for bulk pricing quotes
4. Delivery requirements
5. Payment terms proposal

Keep it concise and professional in Hindi and English.
"""
            
            # Call Bedrock for AI-generated negotiation message
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 1000,
                    'messages': [{
                        'role': 'user',
                        'content': negotiation_prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            negotiation_message = response_body['content'][0]['text']
            
            # Store vendor details
            vendor_details = {
                'negotiation_message': negotiation_message,
                'vendors_contacted': vendor_list or [],
                'negotiation_timestamp': int(datetime.now().timestamp()),
                'status': 'pending_response'
            }
            
            group['vendor_details'] = vendor_details
            group['group_status'] = 'negotiating'
            group['updated_timestamp'] = int(datetime.now().timestamp())
            self.groups_table.put_item(Item=group)
            
            logger.info(f"Vendor negotiation initiated for group {group_id}")
            
            return {
                'success': True,
                'group_id': group_id,
                'negotiation_message': negotiation_message,
                'vendors_contacted': len(vendor_list) if vendor_list else 0,
                'status': 'negotiating',
                'next_steps': [
                    'Send negotiation message to vendors',
                    'Wait for vendor quotes',
                    'Compare quotes and select best offer',
                    'Finalize order with selected vendor'
                ]
            }
        
        except Exception as e:
            logger.error(f"Vendor negotiation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_group_details(self, group_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a buying group
        
        Args:
            group_id: Group ID
        
        Returns:
            Dict with group details
        """
        try:
            response = self.groups_table.get_item(Key={'group_id': group_id})
            
            if 'Item' not in response:
                return {
                    'success': False,
                    'error': 'Group not found'
                }
            
            group = response['Item']
            
            return {
                'success': True,
                'group_id': group_id,
                'group_name': group['group_name'],
                'organizer_user_id': group['organizer_user_id'],
                'members': group.get('members', []),
                'member_count': len(group.get('members', [])),
                'target_products': group['target_products'],
                'location': group['location'],
                'status': group['group_status'],
                'total_quantities': {k: float(v) for k, v in group.get('total_quantity_needed', {}).items()},
                'bulk_pricing': {k: float(v) for k, v in group.get('bulk_pricing_achieved', {}).items()},
                'vendor_details': group.get('vendor_details', {}),
                'deadline': group.get('deadline', ''),
                'created_timestamp': group['created_timestamp'],
                'min_members': group.get('min_members', 5),
                'max_members': group.get('max_members', 50)
            }
        
        except Exception as e:
            logger.error(f"Get group details error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_groups(self, user_id: str) -> Dict[str, Any]:
        """
        Get all buying groups a user is part of
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with user's groups
        """
        try:
            # Scan for groups where user is a member
            response = self.groups_table.scan()
            groups = response.get('Items', [])
            
            user_groups = []
            for group in groups:
                if user_id in group.get('members', []):
                    user_groups.append({
                        'group_id': group['group_id'],
                        'group_name': group['group_name'],
                        'status': group['group_status'],
                        'member_count': len(group.get('members', [])),
                        'target_products': group['target_products'],
                        'is_organizer': group['organizer_user_id'] == user_id,
                        'deadline': group.get('deadline', '')
                    })
            
            logger.info(f"Found {len(user_groups)} groups for user {user_id}")
            
            return {
                'success': True,
                'count': len(user_groups),
                'groups': user_groups
            }
        
        except Exception as e:
            logger.error(f"Get user groups error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_total_quantities(self, member_requirements: Dict[str, Any]) -> Dict[str, Decimal]:
        """Calculate total quantities needed from all members"""
        totals = {}
        
        for member_id, requirements in member_requirements.items():
            for product, quantity in requirements.items():
                if product not in totals:
                    totals[product] = Decimal('0')
                totals[product] += Decimal(str(quantity))
        
        return totals
    
    def _calculate_potential_savings(self,
                                    member_requirements: Dict[str, Any],
                                    total_quantities: Dict[str, Decimal]) -> Dict[str, float]:
        """Calculate potential savings for a member"""
        savings = {}
        
        for product, quantity in member_requirements.items():
            if product in total_quantities:
                total_qty = float(total_quantities[product])
                member_qty = float(quantity)
                
                # Estimate discount based on total quantity
                if total_qty >= 1000:
                    discount_pct = 30
                elif total_qty >= 500:
                    discount_pct = 25
                elif total_qty >= 250:
                    discount_pct = 20
                elif total_qty >= 100:
                    discount_pct = 15
                else:
                    discount_pct = 10
                
                # Estimate savings (assuming ₹1000 per unit market price)
                market_price = 1000
                savings_amount = market_price * member_qty * (discount_pct / 100)
                
                savings[product] = round(savings_amount, 2)
        
        return savings
    
    def _calculate_member_costs(self,
                               group: Dict[str, Any],
                               pricing_breakdown: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate costs for each member"""
        member_costs = {}
        member_requirements = group.get('member_requirements', {})
        
        for member_id, requirements in member_requirements.items():
            member_total = 0
            member_breakdown = {}
            
            for product, quantity in requirements.items():
                if product in pricing_breakdown:
                    price_per_unit = pricing_breakdown[product]['bulk_price_per_unit']
                    cost = price_per_unit * float(quantity)
                    member_total += cost
                    
                    member_breakdown[product] = {
                        'quantity': float(quantity),
                        'price_per_unit': price_per_unit,
                        'total_cost': round(cost, 2)
                    }
            
            member_costs[member_id] = {
                'breakdown': member_breakdown,
                'total_cost': round(member_total, 2)
            }
        
        return member_costs
    
    def _is_within_radius(self,
                         location1: Dict[str, Any],
                         location2: Dict[str, Any]) -> bool:
        """Check if two locations are within specified radius"""
        # Simple check: same district and state
        return (location1.get('district') == location2.get('district') and
                location1.get('state') == location2.get('state'))


# Tool functions for agent integration

def create_buying_group_tools(region: str = "us-east-1") -> BuyingGroupTools:
    """
    Factory function to create buying group tools instance
    
    Args:
        region: AWS region
    
    Returns:
        BuyingGroupTools instance
    """
    return BuyingGroupTools(region=region)
