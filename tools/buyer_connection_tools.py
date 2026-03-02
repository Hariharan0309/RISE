"""
RISE Direct Buyer Connection Tools
Tools for connecting farmers with verified buyers, crop listing, matching, and transaction facilitation
"""

import boto3
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class BuyerConnectionTools:
    """Direct buyer connection tools for RISE farming assistant"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize buyer connection tools with AWS clients
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        
        # DynamoDB tables
        self.buyers_table = self.dynamodb.Table('RISE-Buyers')
        self.listings_table = self.dynamodb.Table('RISE-CropListings')
        self.transactions_table = self.dynamodb.Table('RISE-Transactions')
        
        logger.info(f"Buyer connection tools initialized in region {region}")
    
    def register_buyer(self,
                      buyer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register and verify a new buyer
        
        Args:
            buyer_data: Buyer registration information
        
        Returns:
            Dict with registration result
        """
        try:
            buyer_id = f"buyer_{uuid.uuid4().hex[:8]}"
            
            buyer_item = {
                'buyer_id': buyer_id,
                'business_name': buyer_data['business_name'],
                'contact_person': buyer_data['contact_person'],
                'phone_number': buyer_data['phone_number'],
                'email': buyer_data.get('email', ''),
                'business_type': buyer_data['business_type'],  # wholesaler, retailer, processor, exporter
                'location': {
                    'state': buyer_data['location']['state'],
                    'district': buyer_data['location']['district'],
                    'address': buyer_data['location'].get('address', ''),
                    'latitude': Decimal(str(buyer_data['location'].get('latitude', 0))),
                    'longitude': Decimal(str(buyer_data['location'].get('longitude', 0)))
                },
                'crop_interests': buyer_data.get('crop_interests', []),
                'quality_requirements': buyer_data.get('quality_requirements', {}),
                'payment_terms': buyer_data.get('payment_terms', 'negotiable'),
                'verification_status': 'pending',
                'verification_documents': buyer_data.get('verification_documents', []),
                'ratings': {'average': 0, 'count': 0, 'reviews': []},
                'created_timestamp': int(datetime.now().timestamp()),
                'active': True
            }
            
            # Store in DynamoDB
            self.buyers_table.put_item(Item=buyer_item)
            
            logger.info(f"Buyer registered: {buyer_id}")
            
            return {
                'success': True,
                'buyer_id': buyer_id,
                'verification_status': 'pending',
                'message': 'Buyer registration successful. Verification pending.'
            }
        
        except Exception as e:
            logger.error(f"Buyer registration error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_crop_listing(self,
                           farmer_id: str,
                           listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a crop listing for sale
        
        Args:
            farmer_id: Farmer's user ID
            listing_data: Crop listing information
        
        Returns:
            Dict with listing result
        """
        try:
            listing_id = f"listing_{uuid.uuid4().hex[:8]}"
            
            listing_item = {
                'listing_id': listing_id,
                'farmer_id': farmer_id,
                'crop_name': listing_data['crop_name'].lower().strip(),
                'quantity': Decimal(str(listing_data['quantity'])),
                'unit': listing_data.get('unit', 'quintal'),
                'quality_grade': listing_data.get('quality_grade', 'standard'),
                'expected_price': Decimal(str(listing_data.get('expected_price', 0))),
                'harvest_date': listing_data.get('harvest_date', datetime.now().isoformat()),
                'available_from': listing_data.get('available_from', datetime.now().isoformat()),
                'location': {
                    'state': listing_data['location']['state'],
                    'district': listing_data['location']['district'],
                    'latitude': Decimal(str(listing_data['location'].get('latitude', 0))),
                    'longitude': Decimal(str(listing_data['location'].get('longitude', 0)))
                },
                'description': listing_data.get('description', ''),
                'images': listing_data.get('images', []),
                'certifications': listing_data.get('certifications', []),
                'status': 'active',
                'matches': [],
                'created_timestamp': int(datetime.now().timestamp()),
                'updated_timestamp': int(datetime.now().timestamp())
            }
            
            # Store in DynamoDB
            self.listings_table.put_item(Item=listing_item)
            
            # Find potential buyer matches
            matches = self._find_buyer_matches(listing_item)
            
            if matches:
                # Update listing with matches
                listing_item['matches'] = matches
                self.listings_table.put_item(Item=listing_item)
            
            logger.info(f"Crop listing created: {listing_id}, matches: {len(matches)}")
            
            return {
                'success': True,
                'listing_id': listing_id,
                'status': 'active',
                'potential_matches': len(matches),
                'matches': matches[:5]  # Return top 5 matches
            }
        
        except Exception as e:
            logger.error(f"Crop listing error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _find_buyer_matches(self, listing: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find matching buyers for a crop listing using AI-powered algorithm
        
        Args:
            listing: Crop listing data
        
        Returns:
            List of matched buyers with scores
        """
        try:
            # Query buyers interested in this crop
            # In production, use GSI for efficient querying
            response = self.buyers_table.scan(
                FilterExpression='active = :active AND verification_status = :verified',
                ExpressionAttributeValues={
                    ':active': True,
                    ':verified': 'verified'
                }
            )
            
            buyers = response.get('Items', [])
            matches = []
            
            for buyer in buyers:
                # Check if buyer is interested in this crop
                if listing['crop_name'] not in [c.lower() for c in buyer.get('crop_interests', [])]:
                    continue
                
                # Calculate match score
                score = self._calculate_match_score(listing, buyer)
                
                if score > 0.5:  # Minimum match threshold
                    matches.append({
                        'buyer_id': buyer['buyer_id'],
                        'business_name': buyer['business_name'],
                        'business_type': buyer['business_type'],
                        'location': buyer['location'],
                        'match_score': round(score, 2),
                        'distance_km': self._calculate_distance(
                            listing['location'],
                            buyer['location']
                        ),
                        'ratings': buyer['ratings'],
                        'payment_terms': buyer.get('payment_terms', 'negotiable')
                    })
            
            # Sort by match score and distance
            matches.sort(key=lambda x: (x['match_score'], -x['distance_km']), reverse=True)
            
            return matches
        
        except Exception as e:
            logger.error(f"Buyer matching error: {e}")
            return []
    
    def _calculate_match_score(self,
                               listing: Dict[str, Any],
                               buyer: Dict[str, Any]) -> float:
        """
        Calculate match score between listing and buyer
        
        Args:
            listing: Crop listing
            buyer: Buyer profile
        
        Returns:
            Match score (0-1)
        """
        score = 0.0
        
        # Crop interest match (30%)
        if listing['crop_name'] in [c.lower() for c in buyer.get('crop_interests', [])]:
            score += 0.3
        
        # Location proximity (25%)
        distance = self._calculate_distance(listing['location'], buyer['location'])
        if distance <= 50:
            score += 0.25
        elif distance <= 100:
            score += 0.15
        elif distance <= 200:
            score += 0.05
        
        # Quality requirements match (20%)
        quality_reqs = buyer.get('quality_requirements', {})
        crop_quality_req = quality_reqs.get(listing['crop_name'], {})
        
        if not crop_quality_req or listing.get('quality_grade', 'standard') >= crop_quality_req.get('min_grade', 'standard'):
            score += 0.20
        
        # Buyer rating (15%)
        buyer_rating = buyer.get('ratings', {}).get('average', 0)
        score += (buyer_rating / 5.0) * 0.15
        
        # Business type preference (10%)
        preferred_types = ['processor', 'exporter', 'wholesaler', 'retailer']
        if buyer.get('business_type') in preferred_types:
            type_score = (4 - preferred_types.index(buyer['business_type'])) / 4
            score += type_score * 0.10
        
        return min(score, 1.0)
    
    def _calculate_distance(self,
                           loc1: Dict[str, Any],
                           loc2: Dict[str, Any]) -> float:
        """
        Calculate distance between two locations in kilometers
        
        Args:
            loc1: First location with latitude/longitude
            loc2: Second location with latitude/longitude
        
        Returns:
            Distance in kilometers
        """
        from math import radians, sin, cos, sqrt, atan2
        
        lat1 = radians(float(loc1.get('latitude', 0)))
        lon1 = radians(float(loc1.get('longitude', 0)))
        lat2 = radians(float(loc2.get('latitude', 0)))
        lon2 = radians(float(loc2.get('longitude', 0)))
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        # Earth radius in kilometers
        radius = 6371
        
        return radius * c
    
    def get_quality_standards(self, crop_name: str) -> Dict[str, Any]:
        """
        Get quality standards and benchmarks for a crop
        
        Args:
            crop_name: Name of the crop
        
        Returns:
            Dict with quality standards
        """
        try:
            crop_name = crop_name.lower().strip()
            
            # Quality standards database
            standards = {
                'wheat': {
                    'grades': ['premium', 'grade_a', 'grade_b', 'standard'],
                    'parameters': {
                        'moisture_content': {'max': 12, 'unit': '%'},
                        'foreign_matter': {'max': 2, 'unit': '%'},
                        'damaged_grains': {'max': 3, 'unit': '%'},
                        'shriveled_grains': {'max': 6, 'unit': '%'}
                    },
                    'premium_criteria': {
                        'moisture_content': {'max': 10},
                        'foreign_matter': {'max': 1},
                        'damaged_grains': {'max': 1}
                    }
                },
                'rice': {
                    'grades': ['premium', 'grade_a', 'grade_b', 'standard'],
                    'parameters': {
                        'moisture_content': {'max': 14, 'unit': '%'},
                        'broken_grains': {'max': 5, 'unit': '%'},
                        'foreign_matter': {'max': 1, 'unit': '%'},
                        'chalky_grains': {'max': 6, 'unit': '%'}
                    },
                    'premium_criteria': {
                        'moisture_content': {'max': 12},
                        'broken_grains': {'max': 2},
                        'foreign_matter': {'max': 0.5}
                    }
                },
                'tomato': {
                    'grades': ['premium', 'grade_a', 'grade_b', 'standard'],
                    'parameters': {
                        'size': {'min': 50, 'unit': 'mm'},
                        'color': {'requirement': 'uniform_red'},
                        'firmness': {'requirement': 'firm'},
                        'defects': {'max': 5, 'unit': '%'}
                    },
                    'premium_criteria': {
                        'size': {'min': 60},
                        'defects': {'max': 2}
                    }
                }
            }
            
            standard = standards.get(crop_name, {
                'grades': ['premium', 'grade_a', 'standard'],
                'parameters': {
                    'moisture_content': {'max': 14, 'unit': '%'},
                    'foreign_matter': {'max': 2, 'unit': '%'},
                    'damaged_produce': {'max': 5, 'unit': '%'}
                },
                'premium_criteria': {
                    'moisture_content': {'max': 12},
                    'foreign_matter': {'max': 1}
                }
            })
            
            return {
                'success': True,
                'crop_name': crop_name,
                'standards': standard
            }
        
        except Exception as e:
            logger.error(f"Quality standards error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_price_benchmarks(self,
                            crop_name: str,
                            location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get price benchmarks for negotiation
        
        Args:
            crop_name: Name of the crop
            location: Location information
        
        Returns:
            Dict with price benchmarks
        """
        try:
            # Import market price tools for integration
            import sys
            import os
            sys.path.insert(0, os.path.dirname(__file__))
            from market_price_tools import MarketPriceTools
            
            market_tools = MarketPriceTools(region=self.region)
            
            # Get current market prices
            prices = market_tools.get_current_prices(
                crop_name,
                float(location.get('latitude', 0)),
                float(location.get('longitude', 0)),
                radius_km=100
            )
            
            if not prices['success']:
                return prices
            
            stats = prices['statistics']
            
            # Calculate fair price range
            fair_price_range = {
                'min': round(stats['avg_price'] * 0.95, 2),
                'max': round(stats['avg_price'] * 1.05, 2),
                'recommended': round(stats['avg_price'], 2)
            }
            
            return {
                'success': True,
                'crop_name': crop_name,
                'market_average': stats['avg_price'],
                'market_range': {
                    'min': stats['min_price'],
                    'max': stats['max_price']
                },
                'fair_price_range': fair_price_range,
                'currency': 'INR',
                'unit': 'quintal',
                'last_updated': prices['timestamp']
            }
        
        except Exception as e:
            logger.error(f"Price benchmarks error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def initiate_transaction(self,
                            listing_id: str,
                            buyer_id: str,
                            negotiation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate a transaction between farmer and buyer
        
        Args:
            listing_id: Crop listing ID
            buyer_id: Buyer ID
            negotiation_data: Negotiation details
        
        Returns:
            Dict with transaction result
        """
        try:
            transaction_id = f"txn_{uuid.uuid4().hex[:8]}"
            
            # Get listing details
            listing_response = self.listings_table.get_item(Key={'listing_id': listing_id})
            if 'Item' not in listing_response:
                return {
                    'success': False,
                    'error': 'Listing not found'
                }
            
            listing = listing_response['Item']
            
            transaction_item = {
                'transaction_id': transaction_id,
                'listing_id': listing_id,
                'farmer_id': listing['farmer_id'],
                'buyer_id': buyer_id,
                'crop_name': listing['crop_name'],
                'quantity': negotiation_data.get('quantity', listing['quantity']),
                'agreed_price': Decimal(str(negotiation_data['agreed_price'])),
                'unit': listing['unit'],
                'quality_grade': listing['quality_grade'],
                'payment_terms': negotiation_data.get('payment_terms', 'on_delivery'),
                'delivery_date': negotiation_data.get('delivery_date', ''),
                'delivery_location': negotiation_data.get('delivery_location', {}),
                'payment_status': 'pending',
                'delivery_status': 'pending',
                'status': 'confirmed',
                'created_timestamp': int(datetime.now().timestamp()),
                'updated_timestamp': int(datetime.now().timestamp())
            }
            
            # Store transaction
            self.transactions_table.put_item(Item=transaction_item)
            
            # Update listing status
            listing['status'] = 'sold'
            listing['updated_timestamp'] = int(datetime.now().timestamp())
            self.listings_table.put_item(Item=listing)
            
            logger.info(f"Transaction initiated: {transaction_id}")
            
            return {
                'success': True,
                'transaction_id': transaction_id,
                'status': 'confirmed',
                'payment_status': 'pending',
                'next_steps': [
                    'Complete payment processing',
                    'Arrange logistics and delivery',
                    'Quality inspection on delivery'
                ]
            }
        
        except Exception as e:
            logger.error(f"Transaction initiation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


# Tool functions for agent integration

def create_buyer_connection_tools(region: str = "us-east-1") -> BuyerConnectionTools:
    """
    Factory function to create buyer connection tools instance
    
    Args:
        region: AWS region
    
    Returns:
        BuyerConnectionTools instance
    """
    return BuyerConnectionTools(region=region)


def register_buyer_tool(buyer_data: Dict[str, Any]) -> str:
    """
    Tool for registering a new buyer
    
    Args:
        buyer_data: Buyer registration information
    
    Returns:
        Registration result message
    """
    tools = create_buyer_connection_tools()
    result = tools.register_buyer(buyer_data)
    
    if result['success']:
        return f"""Buyer Registration Successful!

Buyer ID: {result['buyer_id']}
Status: {result['verification_status']}

{result['message']}
"""
    else:
        return f"Error: {result.get('error', 'Failed to register buyer')}"


def create_crop_listing_tool(farmer_id: str, listing_data: Dict[str, Any]) -> str:
    """
    Tool for creating a crop listing
    
    Args:
        farmer_id: Farmer's user ID
        listing_data: Crop listing information
    
    Returns:
        Listing result message
    """
    tools = create_buyer_connection_tools()
    result = tools.create_crop_listing(farmer_id, listing_data)
    
    if result['success']:
        output = f"""Crop Listing Created Successfully!

Listing ID: {result['listing_id']}
Status: {result['status']}
Potential Buyers Found: {result['potential_matches']}

Top Matches:
"""
        for match in result['matches']:
            output += f"• {match['business_name']} ({match['business_type']}) - Match Score: {match['match_score']}, Distance: {match['distance_km']:.1f}km\n"
        
        return output
    else:
        return f"Error: {result.get('error', 'Failed to create listing')}"


def get_quality_standards_tool(crop_name: str) -> str:
    """
    Tool for getting quality standards
    
    Args:
        crop_name: Name of the crop
    
    Returns:
        Quality standards information
    """
    tools = create_buyer_connection_tools()
    result = tools.get_quality_standards(crop_name)
    
    if result['success']:
        standards = result['standards']
        output = f"""Quality Standards for {result['crop_name'].title()}:

Available Grades: {', '.join(standards['grades'])}

Quality Parameters:
"""
        for param, values in standards['parameters'].items():
            output += f"• {param.replace('_', ' ').title()}: "
            if 'max' in values:
                output += f"Max {values['max']}{values.get('unit', '')}\n"
            elif 'min' in values:
                output += f"Min {values['min']}{values.get('unit', '')}\n"
            elif 'requirement' in values:
                output += f"{values['requirement']}\n"
        
        return output
    else:
        return f"Error: {result.get('error', 'Failed to fetch quality standards')}"


def get_price_benchmarks_tool(crop_name: str, location: Dict[str, Any]) -> str:
    """
    Tool for getting price benchmarks
    
    Args:
        crop_name: Name of the crop
        location: Location information
    
    Returns:
        Price benchmarks information
    """
    tools = create_buyer_connection_tools()
    result = tools.get_price_benchmarks(crop_name, location)
    
    if result['success']:
        output = f"""Price Benchmarks for {result['crop_name'].title()}:

Market Average: ₹{result['market_average']:.2f}/{result['unit']}
Market Range: ₹{result['market_range']['min']} - ₹{result['market_range']['max']}

Fair Price Range for Negotiation:
• Minimum: ₹{result['fair_price_range']['min']}/{result['unit']}
• Recommended: ₹{result['fair_price_range']['recommended']}/{result['unit']}
• Maximum: ₹{result['fair_price_range']['max']}/{result['unit']}

Last Updated: {result['last_updated']}
"""
        return output
    else:
        return f"Error: {result.get('error', 'Failed to fetch price benchmarks')}"
