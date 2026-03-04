"""
RISE AI-Powered Supplier Negotiation Tools
Tools for negotiating with suppliers, managing bulk pricing requests, quality verification, and delivery coordination
"""

import boto3
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class SupplierNegotiationTools:
    """AI-powered supplier negotiation tools for RISE farming assistant"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize supplier negotiation tools with AWS clients
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        
        # DynamoDB tables
        self.suppliers_table = self.dynamodb.Table('RISE-Suppliers')
        self.negotiations_table = self.dynamodb.Table('RISE-Negotiations')
        self.quotes_table = self.dynamodb.Table('RISE-SupplierQuotes')
        
        logger.info(f"Supplier negotiation tools initialized in region {region}")
    
    def register_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new supplier in the database
        
        Args:
            supplier_data: Supplier registration information
        
        Returns:
            Dict with registration result
        """
        try:
            supplier_id = f"sup_{uuid.uuid4().hex[:8]}"
            
            supplier_item = {
                'supplier_id': supplier_id,
                'business_name': supplier_data['business_name'],
                'contact_person': supplier_data['contact_person'],
                'phone_number': supplier_data['phone_number'],
                'email': supplier_data.get('email', ''),
                'supplier_type': supplier_data['supplier_type'],  # seeds, fertilizers, pesticides, equipment
                'location': {
                    'state': supplier_data['location']['state'],
                    'district': supplier_data['location']['district'],
                    'address': supplier_data['location'].get('address', ''),
                    'latitude': Decimal(str(supplier_data['location'].get('latitude', 0))),
                    'longitude': Decimal(str(supplier_data['location'].get('longitude', 0)))
                },
                'products_offered': supplier_data.get('products_offered', []),
                'certifications': supplier_data.get('certifications', []),
                'quality_standards': supplier_data.get('quality_standards', {}),
                'delivery_areas': supplier_data.get('delivery_areas', []),
                'payment_terms': supplier_data.get('payment_terms', []),
                'minimum_order_quantity': supplier_data.get('minimum_order_quantity', {}),
                'bulk_discount_tiers': supplier_data.get('bulk_discount_tiers', {}),
                'ratings': {'average': Decimal('0'), 'count': 0, 'reviews': []},
                'verification_status': 'pending',
                'verification_documents': supplier_data.get('verification_documents', []),
                'created_timestamp': int(datetime.now().timestamp()),
                'updated_timestamp': int(datetime.now().timestamp()),
                'active': True
            }
            
            # Store in DynamoDB
            self.suppliers_table.put_item(Item=supplier_item)
            
            logger.info(f"Supplier registered: {supplier_id}")
            
            return {
                'success': True,
                'supplier_id': supplier_id,
                'verification_status': 'pending',
                'message': f'Supplier "{supplier_data["business_name"]}" registered successfully'
            }
        
        except Exception as e:
            logger.error(f"Supplier registration error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def find_suppliers(self,
                      product_requirements: Dict[str, Any],
                      location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find suppliers matching product requirements and location
        
        Args:
            product_requirements: Products and quantities needed
            location: Buyer location information
        
        Returns:
            Dict with matching suppliers
        """
        try:
            # Query suppliers by product type
            response = self.suppliers_table.scan(
                FilterExpression='active = :active AND verification_status = :verified',
                ExpressionAttributeValues={
                    ':active': True,
                    ':verified': 'verified'
                }
            )
            
            suppliers = response.get('Items', [])
            matching_suppliers = []
            
            required_products = set(product_requirements.keys())
            
            for supplier in suppliers:
                # Check product match
                supplier_products = set(supplier.get('products_offered', []))
                matching_products = required_products.intersection(supplier_products)
                
                if not matching_products:
                    continue
                
                # Check delivery area
                if not self._can_deliver_to(supplier, location):
                    continue
                
                # Check minimum order quantities
                meets_moq = self._meets_minimum_order(supplier, product_requirements)
                
                # Calculate match score
                match_score = self._calculate_supplier_match_score(
                    supplier, product_requirements, location
                )
                
                matching_suppliers.append({
                    'supplier_id': supplier['supplier_id'],
                    'business_name': supplier['business_name'],
                    'supplier_type': supplier['supplier_type'],
                    'contact_person': supplier['contact_person'],
                    'phone_number': supplier['phone_number'],
                    'email': supplier.get('email', ''),
                    'location': supplier['location'],
                    'matching_products': list(matching_products),
                    'match_score': round(match_score, 2),
                    'meets_moq': meets_moq,
                    'certifications': supplier.get('certifications', []),
                    'ratings': {
                        'average': float(supplier['ratings'].get('average', 0)),
                        'count': supplier['ratings'].get('count', 0)
                    },
                    'payment_terms': supplier.get('payment_terms', []),
                    'bulk_discount_available': bool(supplier.get('bulk_discount_tiers'))
                })
            
            # Sort by match score
            matching_suppliers.sort(key=lambda x: x['match_score'], reverse=True)
            
            logger.info(f"Found {len(matching_suppliers)} matching suppliers")
            
            return {
                'success': True,
                'count': len(matching_suppliers),
                'suppliers': matching_suppliers
            }
        
        except Exception as e:
            logger.error(f"Supplier search error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_bulk_pricing_request(self,
                                     buyer_id: str,
                                     product_requirements: Dict[str, Any],
                                     supplier_ids: List[str],
                                     delivery_location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI-powered bulk pricing request to send to suppliers
        
        Args:
            buyer_id: Buyer/group ID
            product_requirements: Products and quantities needed
            supplier_ids: List of supplier IDs to contact
            delivery_location: Delivery location details
        
        Returns:
            Dict with generated request and negotiation ID
        """
        try:
            negotiation_id = f"neg_{uuid.uuid4().hex[:8]}"
            
            # Prepare negotiation prompt for AI
            negotiation_prompt = f"""
You are a professional procurement specialist helping farmers negotiate bulk pricing for agricultural inputs.

Buyer Requirements:
- Products needed: {json.dumps(product_requirements, indent=2)}
- Delivery location: {delivery_location['district']}, {delivery_location['state']}
- Target discount: 15-30% from retail prices

Generate a professional bulk pricing request message that includes:
1. Professional introduction
2. Specific product requirements with quantities
3. Request for bulk pricing quotes with discount tiers
4. Quality assurance and certification requirements
5. Delivery requirements to rural locations
6. Payment terms proposal (suitable for farmers)
7. Timeline for quote submission

Keep it concise, professional, and persuasive. Write in both Hindi and English for better reach.
"""
            
            # Call Bedrock for AI-generated request
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 1500,
                    'messages': [{
                        'role': 'user',
                        'content': negotiation_prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            request_message = response_body['content'][0]['text']
            
            # Store negotiation record
            negotiation_item = {
                'negotiation_id': negotiation_id,
                'buyer_id': buyer_id,
                'product_requirements': product_requirements,
                'supplier_ids': supplier_ids,
                'delivery_location': delivery_location,
                'request_message': request_message,
                'status': 'pending_quotes',
                'quotes_received': [],
                'created_timestamp': int(datetime.now().timestamp()),
                'updated_timestamp': int(datetime.now().timestamp()),
                'deadline': (datetime.now() + timedelta(days=7)).isoformat()
            }
            
            self.negotiations_table.put_item(Item=negotiation_item)
            
            logger.info(f"Bulk pricing request generated: {negotiation_id}")
            
            return {
                'success': True,
                'negotiation_id': negotiation_id,
                'request_message': request_message,
                'suppliers_contacted': len(supplier_ids),
                'status': 'pending_quotes',
                'deadline': negotiation_item['deadline'],
                'next_steps': [
                    'Send request to selected suppliers',
                    'Wait for supplier quotes (7 days)',
                    'Compare quotes and verify quality',
                    'Select best supplier and finalize order'
                ]
            }
        
        except Exception as e:
            logger.error(f"Bulk pricing request generation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def submit_supplier_quote(self,
                             negotiation_id: str,
                             supplier_id: str,
                             quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a supplier quote for a negotiation
        
        Args:
            negotiation_id: Negotiation ID
            supplier_id: Supplier ID
            quote_data: Quote details including pricing, terms, etc.
        
        Returns:
            Dict with submission result
        """
        try:
            quote_id = f"quote_{uuid.uuid4().hex[:8]}"
            
            # Get negotiation details
            neg_response = self.negotiations_table.get_item(Key={'negotiation_id': negotiation_id})
            if 'Item' not in neg_response:
                return {
                    'success': False,
                    'error': 'Negotiation not found'
                }
            
            negotiation = neg_response['Item']
            
            # Store quote
            quote_item = {
                'quote_id': quote_id,
                'negotiation_id': negotiation_id,
                'supplier_id': supplier_id,
                'product_pricing': quote_data['product_pricing'],  # Product -> price per unit
                'discount_percentage': Decimal(str(quote_data.get('discount_percentage', 0))),
                'total_amount': Decimal(str(quote_data['total_amount'])),
                'payment_terms': quote_data.get('payment_terms', 'on_delivery'),
                'delivery_timeline': quote_data.get('delivery_timeline', ''),
                'quality_certifications': quote_data.get('quality_certifications', []),
                'warranty_terms': quote_data.get('warranty_terms', ''),
                'additional_notes': quote_data.get('additional_notes', ''),
                'valid_until': quote_data.get('valid_until', (datetime.now() + timedelta(days=30)).isoformat()),
                'status': 'submitted',
                'created_timestamp': int(datetime.now().timestamp())
            }
            
            self.quotes_table.put_item(Item=quote_item)
            
            # Update negotiation with quote
            quotes_received = negotiation.get('quotes_received', [])
            quotes_received.append(quote_id)
            
            negotiation['quotes_received'] = quotes_received
            negotiation['updated_timestamp'] = int(datetime.now().timestamp())
            
            if len(quotes_received) >= len(negotiation['supplier_ids']):
                negotiation['status'] = 'quotes_complete'
            
            self.negotiations_table.put_item(Item=negotiation)
            
            logger.info(f"Quote submitted: {quote_id} for negotiation {negotiation_id}")
            
            return {
                'success': True,
                'quote_id': quote_id,
                'negotiation_id': negotiation_id,
                'status': 'submitted',
                'quotes_received': len(quotes_received),
                'total_suppliers': len(negotiation['supplier_ids'])
            }
        
        except Exception as e:
            logger.error(f"Quote submission error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def compare_quotes(self, negotiation_id: str) -> Dict[str, Any]:
        """
        Compare all quotes received for a negotiation using AI analysis
        
        Args:
            negotiation_id: Negotiation ID
        
        Returns:
            Dict with quote comparison and recommendation
        """
        try:
            # Get negotiation details
            neg_response = self.negotiations_table.get_item(Key={'negotiation_id': negotiation_id})
            if 'Item' not in neg_response:
                return {
                    'success': False,
                    'error': 'Negotiation not found'
                }
            
            negotiation = neg_response['Item']
            quote_ids = negotiation.get('quotes_received', [])
            
            if not quote_ids:
                return {
                    'success': False,
                    'error': 'No quotes received yet'
                }
            
            # Fetch all quotes
            quotes = []
            for quote_id in quote_ids:
                quote_response = self.quotes_table.get_item(Key={'quote_id': quote_id})
                if 'Item' in quote_response:
                    quote = quote_response['Item']
                    
                    # Get supplier details
                    supplier_response = self.suppliers_table.get_item(
                        Key={'supplier_id': quote['supplier_id']}
                    )
                    supplier = supplier_response.get('Item', {})
                    
                    quotes.append({
                        'quote_id': quote_id,
                        'supplier_id': quote['supplier_id'],
                        'supplier_name': supplier.get('business_name', 'Unknown'),
                        'total_amount': float(quote['total_amount']),
                        'discount_percentage': float(quote.get('discount_percentage', 0)),
                        'payment_terms': quote.get('payment_terms', ''),
                        'delivery_timeline': quote.get('delivery_timeline', ''),
                        'quality_certifications': quote.get('quality_certifications', []),
                        'supplier_rating': float(supplier.get('ratings', {}).get('average', 0)),
                        'product_pricing': {k: float(v) for k, v in quote['product_pricing'].items()}
                    })
            
            # Use AI to analyze and recommend
            comparison_prompt = f"""
You are a procurement analyst helping farmers select the best supplier quote.

Quotes Received:
{json.dumps(quotes, indent=2)}

Analyze these quotes considering:
1. Total cost and discount percentage (weight: 40%)
2. Quality certifications and standards (weight: 25%)
3. Delivery timeline and reliability (weight: 20%)
4. Payment terms favorable to farmers (weight: 10%)
5. Supplier ratings and reputation (weight: 5%)

Provide:
1. Ranking of quotes from best to worst
2. Detailed comparison highlighting pros and cons
3. Clear recommendation with reasoning
4. Risk assessment for each option

Format your response as a structured analysis.
"""
            
            # Call Bedrock for AI analysis
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 2000,
                    'messages': [{
                        'role': 'user',
                        'content': comparison_prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            ai_analysis = response_body['content'][0]['text']
            
            # Calculate simple ranking
            ranked_quotes = sorted(quotes, key=lambda q: (
                -q['discount_percentage'] * 0.4 +
                -q['total_amount'] / 10000 * 0.3 +
                q['supplier_rating'] * 0.2 +
                len(q['quality_certifications']) * 0.1
            ), reverse=True)
            
            logger.info(f"Quotes compared for negotiation {negotiation_id}")
            
            return {
                'success': True,
                'negotiation_id': negotiation_id,
                'quotes_count': len(quotes),
                'quotes': quotes,
                'ranked_quotes': ranked_quotes,
                'ai_analysis': ai_analysis,
                'recommended_quote': ranked_quotes[0] if ranked_quotes else None,
                'best_price': min(q['total_amount'] for q in quotes),
                'best_discount': max(q['discount_percentage'] for q in quotes),
                'average_price': sum(q['total_amount'] for q in quotes) / len(quotes)
            }
        
        except Exception as e:
            logger.error(f"Quote comparison error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_quality_assurance(self,
                                supplier_id: str,
                                product_name: str) -> Dict[str, Any]:
        """
        Verify supplier's quality assurance and certifications
        
        Args:
            supplier_id: Supplier ID
            product_name: Product to verify
        
        Returns:
            Dict with quality verification results
        """
        try:
            # Get supplier details
            supplier_response = self.suppliers_table.get_item(Key={'supplier_id': supplier_id})
            if 'Item' not in supplier_response:
                return {
                    'success': False,
                    'error': 'Supplier not found'
                }
            
            supplier = supplier_response['Item']
            
            # Check certifications
            certifications = supplier.get('certifications', [])
            quality_standards = supplier.get('quality_standards', {})
            
            # Verify against industry standards
            verification_result = {
                'supplier_id': supplier_id,
                'supplier_name': supplier['business_name'],
                'product_name': product_name,
                'certifications': certifications,
                'quality_standards': quality_standards,
                'verification_status': supplier.get('verification_status', 'pending'),
                'verification_checks': []
            }
            
            # Check for required certifications
            required_certs = self._get_required_certifications(product_name)
            for cert in required_certs:
                has_cert = any(cert.lower() in c.lower() for c in certifications)
                verification_result['verification_checks'].append({
                    'certification': cert,
                    'required': True,
                    'verified': has_cert,
                    'status': 'pass' if has_cert else 'fail'
                })
            
            # Overall verification status
            all_passed = all(check['status'] == 'pass' for check in verification_result['verification_checks'])
            verification_result['overall_status'] = 'verified' if all_passed else 'needs_review'
            verification_result['compliance_score'] = round(
                sum(1 for check in verification_result['verification_checks'] if check['status'] == 'pass') /
                len(verification_result['verification_checks']) * 100, 1
            ) if verification_result['verification_checks'] else 0
            
            logger.info(f"Quality verification completed for supplier {supplier_id}")
            
            return {
                'success': True,
                **verification_result
            }
        
        except Exception as e:
            logger.error(f"Quality verification error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def coordinate_delivery(self,
                          negotiation_id: str,
                          selected_quote_id: str,
                          delivery_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordinate delivery logistics for selected quote
        
        Args:
            negotiation_id: Negotiation ID
            selected_quote_id: Selected quote ID
            delivery_details: Delivery coordination details
        
        Returns:
            Dict with delivery coordination result
        """
        try:
            delivery_id = f"del_{uuid.uuid4().hex[:8]}"
            
            # Get quote and negotiation details
            quote_response = self.quotes_table.get_item(Key={'quote_id': selected_quote_id})
            if 'Item' not in quote_response:
                return {
                    'success': False,
                    'error': 'Quote not found'
                }
            
            quote = quote_response['Item']
            
            neg_response = self.negotiations_table.get_item(Key={'negotiation_id': negotiation_id})
            negotiation = neg_response.get('Item', {})
            
            # Create delivery coordination record
            delivery_record = {
                'delivery_id': delivery_id,
                'negotiation_id': negotiation_id,
                'quote_id': selected_quote_id,
                'supplier_id': quote['supplier_id'],
                'buyer_id': negotiation.get('buyer_id', ''),
                'delivery_location': negotiation.get('delivery_location', {}),
                'delivery_date': delivery_details.get('delivery_date', ''),
                'delivery_time_slot': delivery_details.get('delivery_time_slot', ''),
                'delivery_contact': delivery_details.get('delivery_contact', {}),
                'special_instructions': delivery_details.get('special_instructions', ''),
                'delivery_status': 'scheduled',
                'tracking_number': f"TRK{uuid.uuid4().hex[:12].upper()}",
                'created_timestamp': int(datetime.now().timestamp()),
                'updated_timestamp': int(datetime.now().timestamp())
            }
            
            # Store delivery record (would use a separate table in production)
            # For now, update negotiation with delivery info
            negotiation['selected_quote_id'] = selected_quote_id
            negotiation['delivery_id'] = delivery_id
            negotiation['delivery_details'] = delivery_record
            negotiation['status'] = 'delivery_scheduled'
            negotiation['updated_timestamp'] = int(datetime.now().timestamp())
            
            self.negotiations_table.put_item(Item=negotiation)
            
            logger.info(f"Delivery coordinated: {delivery_id}")
            
            return {
                'success': True,
                'delivery_id': delivery_id,
                'tracking_number': delivery_record['tracking_number'],
                'delivery_date': delivery_record['delivery_date'],
                'delivery_status': 'scheduled',
                'estimated_delivery': delivery_details.get('delivery_date', ''),
                'contact_info': delivery_details.get('delivery_contact', {}),
                'next_steps': [
                    'Supplier will prepare order',
                    'Delivery will be dispatched on scheduled date',
                    'Track delivery using tracking number',
                    'Inspect quality upon delivery',
                    'Complete payment as per terms'
                ]
            }
        
        except Exception as e:
            logger.error(f"Delivery coordination error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def manage_payment(self,
                      negotiation_id: str,
                      payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage payment collection and distribution
        
        Args:
            negotiation_id: Negotiation ID
            payment_data: Payment details
        
        Returns:
            Dict with payment management result
        """
        try:
            payment_id = f"pay_{uuid.uuid4().hex[:8]}"
            
            # Get negotiation details
            neg_response = self.negotiations_table.get_item(Key={'negotiation_id': negotiation_id})
            if 'Item' not in neg_response:
                return {
                    'success': False,
                    'error': 'Negotiation not found'
                }
            
            negotiation = neg_response['Item']
            selected_quote_id = negotiation.get('selected_quote_id')
            
            if not selected_quote_id:
                return {
                    'success': False,
                    'error': 'No quote selected yet'
                }
            
            # Get quote details
            quote_response = self.quotes_table.get_item(Key={'quote_id': selected_quote_id})
            quote = quote_response.get('Item', {})
            
            total_amount = float(quote.get('total_amount', 0))
            
            # Create payment record
            payment_record = {
                'payment_id': payment_id,
                'negotiation_id': negotiation_id,
                'quote_id': selected_quote_id,
                'supplier_id': quote.get('supplier_id', ''),
                'buyer_id': negotiation.get('buyer_id', ''),
                'total_amount': Decimal(str(total_amount)),
                'payment_method': payment_data.get('payment_method', 'bank_transfer'),
                'payment_terms': quote.get('payment_terms', 'on_delivery'),
                'payment_status': 'pending',
                'payment_schedule': payment_data.get('payment_schedule', []),
                'transaction_reference': payment_data.get('transaction_reference', ''),
                'created_timestamp': int(datetime.now().timestamp()),
                'updated_timestamp': int(datetime.now().timestamp())
            }
            
            # Calculate payment distribution if it's a group purchase
            if 'member_contributions' in payment_data:
                payment_record['member_contributions'] = payment_data['member_contributions']
                payment_record['collection_status'] = {
                    member: 'pending' for member in payment_data['member_contributions'].keys()
                }
            
            # Update negotiation with payment info
            negotiation['payment_id'] = payment_id
            negotiation['payment_details'] = payment_record
            negotiation['status'] = 'payment_pending'
            negotiation['updated_timestamp'] = int(datetime.now().timestamp())
            
            self.negotiations_table.put_item(Item=negotiation)
            
            logger.info(f"Payment managed: {payment_id}")
            
            return {
                'success': True,
                'payment_id': payment_id,
                'total_amount': total_amount,
                'payment_status': 'pending',
                'payment_method': payment_record['payment_method'],
                'payment_terms': payment_record['payment_terms'],
                'member_count': len(payment_data.get('member_contributions', {})),
                'next_steps': [
                    'Collect payments from all members',
                    'Verify payment receipt',
                    'Transfer payment to supplier',
                    'Confirm delivery schedule'
                ]
            }
        
        except Exception as e:
            logger.error(f"Payment management error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_negotiation_status(self, negotiation_id: str) -> Dict[str, Any]:
        """
        Get detailed status of a negotiation
        
        Args:
            negotiation_id: Negotiation ID
        
        Returns:
            Dict with negotiation status
        """
        try:
            response = self.negotiations_table.get_item(Key={'negotiation_id': negotiation_id})
            
            if 'Item' not in response:
                return {
                    'success': False,
                    'error': 'Negotiation not found'
                }
            
            negotiation = response['Item']
            
            return {
                'success': True,
                'negotiation_id': negotiation_id,
                'buyer_id': negotiation.get('buyer_id', ''),
                'status': negotiation.get('status', ''),
                'product_requirements': negotiation.get('product_requirements', {}),
                'suppliers_contacted': len(negotiation.get('supplier_ids', [])),
                'quotes_received': len(negotiation.get('quotes_received', [])),
                'selected_quote_id': negotiation.get('selected_quote_id', ''),
                'delivery_id': negotiation.get('delivery_id', ''),
                'payment_id': negotiation.get('payment_id', ''),
                'created_timestamp': negotiation.get('created_timestamp', 0),
                'deadline': negotiation.get('deadline', '')
            }
        
        except Exception as e:
            logger.error(f"Get negotiation status error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _can_deliver_to(self, supplier: Dict[str, Any], location: Dict[str, Any]) -> bool:
        """Check if supplier can deliver to location"""
        delivery_areas = supplier.get('delivery_areas', [])
        
        if not delivery_areas:
            # If no specific areas defined, assume they deliver to their state
            return supplier['location']['state'] == location.get('state')
        
        # Check if location matches any delivery area
        location_key = f"{location.get('district')}_{location.get('state')}"
        return any(location_key in area for area in delivery_areas)
    
    def _meets_minimum_order(self,
                            supplier: Dict[str, Any],
                            requirements: Dict[str, Any]) -> bool:
        """Check if order meets minimum order quantities"""
        moq = supplier.get('minimum_order_quantity', {})
        
        if not moq:
            return True
        
        for product, quantity in requirements.items():
            if product in moq:
                if float(quantity) < float(moq[product]):
                    return False
        
        return True
    
    def _calculate_supplier_match_score(self,
                                       supplier: Dict[str, Any],
                                       requirements: Dict[str, Any],
                                       location: Dict[str, Any]) -> float:
        """Calculate match score for supplier"""
        score = 0.0
        
        # Product match (40%)
        supplier_products = set(supplier.get('products_offered', []))
        required_products = set(requirements.keys())
        match_ratio = len(supplier_products.intersection(required_products)) / len(required_products)
        score += match_ratio * 0.4
        
        # Location proximity (20%)
        if supplier['location']['state'] == location.get('state'):
            score += 0.2
            if supplier['location']['district'] == location.get('district'):
                score += 0.1
        
        # Supplier rating (20%)
        rating = float(supplier.get('ratings', {}).get('average', 0))
        score += (rating / 5.0) * 0.2
        
        # Certifications (10%)
        cert_count = len(supplier.get('certifications', []))
        score += min(cert_count / 5, 1.0) * 0.1
        
        # Bulk discount availability (10%)
        if supplier.get('bulk_discount_tiers'):
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_required_certifications(self, product_name: str) -> List[str]:
        """Get required certifications for a product"""
        cert_requirements = {
            'seeds': ['Seed Certification', 'Quality Assurance', 'Phytosanitary Certificate'],
            'fertilizer': ['FCO License', 'Quality Certification', 'ISO 9001'],
            'pesticide': ['CIB Registration', 'Quality Certification', 'Safety Standards'],
            'equipment': ['Quality Certification', 'Warranty', 'Safety Standards']
        }
        
        # Match product to category
        product_lower = product_name.lower()
        for category, certs in cert_requirements.items():
            if category in product_lower:
                return certs
        
        return ['Quality Certification', 'Business License']


# Tool functions for agent integration

def create_supplier_negotiation_tools(region: str = "us-east-1") -> SupplierNegotiationTools:
    """
    Factory function to create supplier negotiation tools instance
    
    Args:
        region: AWS region
    
    Returns:
        SupplierNegotiationTools instance
    """
    return SupplierNegotiationTools(region=region)
