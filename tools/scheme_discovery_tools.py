"""
RISE Scheme Discovery Tools
Tools for analyzing farmer profiles, checking eligibility, and recommending schemes
"""

import boto3
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class SchemeDiscoveryTools:
    """Scheme discovery and eligibility tools for RISE farming assistant"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize scheme discovery tools with AWS clients
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        
        # DynamoDB tables
        self.schemes_table = self.dynamodb.Table('RISE-GovernmentSchemes')
        self.user_profiles_table = self.dynamodb.Table('RISE-UserProfiles')
        
        # Eligibility criteria mappings
        self.farmer_categories = {
            'marginal': {'max_land': 1.0},
            'small': {'max_land': 2.0},
            'medium': {'max_land': 10.0},
            'large': {'min_land': 10.0}
        }
        
        logger.info(f"Scheme discovery tools initialized in region {region}")
    
    def analyze_farmer_profile(self, farmer_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze farmer profile using Amazon Bedrock to identify applicable schemes
        
        Args:
            farmer_profile: Farmer information including location, land size, crops, etc.
        
        Returns:
            Dict with profile analysis and scheme categories
        """
        try:
            # Extract key profile attributes
            land_size = farmer_profile.get('farm_details', {}).get('land_size', 0)
            state = farmer_profile.get('location', {}).get('state', 'central').lower()
            crops = farmer_profile.get('farm_details', {}).get('crops', [])
            annual_income = farmer_profile.get('annual_income', 0)
            
            # Determine farmer category
            farmer_category = self._determine_farmer_category(land_size)
            
            # Build analysis prompt for AI
            analysis_prompt = f"""Analyze this farmer profile and identify applicable government scheme categories:

Farmer Profile:
- Location: {state}
- Land Size: {land_size} acres
- Farmer Category: {farmer_category}
- Crops: {', '.join(crops) if crops else 'Not specified'}
- Annual Income: ₹{annual_income}

Available Scheme Categories:
1. crop_insurance - Insurance schemes for crop protection
2. subsidies - Direct financial subsidies and support
3. loans - Agricultural loans and credit facilities
4. equipment - Equipment purchase subsidies
5. irrigation - Irrigation infrastructure support
6. organic_farming - Organic farming promotion schemes
7. training - Training and skill development programs
8. market_access - Market linkage and access programs
9. soil_health - Soil health management schemes
10. seeds - Seed distribution and quality programs

Based on this profile, identify:
1. Top 3 most relevant scheme categories
2. Specific needs this farmer might have
3. Priority areas for government support
4. Estimated total benefit potential

Format as JSON with keys: relevant_categories, farmer_needs, priority_areas, estimated_benefits"""

            # Use Amazon Bedrock for analysis
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 1000,
                    'messages': [{
                        'role': 'user',
                        'content': analysis_prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            ai_response = response_body['content'][0]['text']
            
            # Parse AI response
            analysis = self._parse_json_response(ai_response)
            
            # Add computed attributes
            analysis['farmer_category'] = farmer_category
            analysis['profile_completeness'] = self._calculate_profile_completeness(farmer_profile)
            
            return {
                'success': True,
                'analysis': analysis,
                'profile_summary': {
                    'farmer_category': farmer_category,
                    'land_size': land_size,
                    'state': state,
                    'crops_count': len(crops)
                }
            }
        
        except Exception as e:
            logger.error(f"Profile analysis error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_eligibility(self, farmer_profile: Dict[str, Any], scheme_id: str) -> Dict[str, Any]:
        """
        Check if farmer is eligible for a specific scheme
        
        Args:
            farmer_profile: Farmer information
            scheme_id: Scheme identifier
        
        Returns:
            Dict with eligibility determination and required documents
        """
        try:
            # Get scheme details
            scheme_response = self.schemes_table.get_item(Key={'scheme_id': scheme_id})
            
            if 'Item' not in scheme_response:
                return {
                    'success': False,
                    'error': f'Scheme not found: {scheme_id}'
                }
            
            scheme = self._convert_decimals(scheme_response['Item'])
            
            # Extract farmer attributes
            land_size = farmer_profile.get('farm_details', {}).get('land_size', 0)
            state = farmer_profile.get('location', {}).get('state', '').lower()
            farmer_category = self._determine_farmer_category(land_size)
            has_land_ownership = farmer_profile.get('farm_details', {}).get('land_ownership', False)
            
            # Check eligibility criteria
            eligibility_criteria = scheme.get('eligibility_criteria', {})
            eligible = True
            reasons = []
            missing_requirements = []
            
            # Check state eligibility
            scheme_state = scheme.get('state', 'central').lower()
            if scheme_state != 'central' and scheme_state != state:
                eligible = False
                reasons.append(f"Scheme is only for {scheme_state.title()} state")
            
            # Check land ownership requirement
            required_ownership = eligibility_criteria.get('land_ownership', 'any')
            if required_ownership == 'required' and not has_land_ownership:
                eligible = False
                reasons.append("Land ownership is required")
                missing_requirements.append("Land ownership documents")
            
            # Check land size requirement
            required_land_size = eligibility_criteria.get('land_size', 'any')
            if required_land_size != 'any':
                if not self._check_land_size_eligibility(land_size, required_land_size):
                    eligible = False
                    reasons.append(f"Land size requirement not met: {required_land_size}")
            
            # Check farmer type requirement
            required_farmer_type = eligibility_criteria.get('farmer_type', 'all')
            if required_farmer_type != 'all' and required_farmer_type != farmer_category:
                eligible = False
                reasons.append(f"Scheme is only for {required_farmer_type} farmers")
            
            # Generate required documents list
            required_documents = self._generate_required_documents(scheme, farmer_profile)
            
            # Calculate confidence score
            confidence_score = self._calculate_eligibility_confidence(
                farmer_profile, scheme, eligible
            )
            
            return {
                'success': True,
                'scheme_id': scheme_id,
                'scheme_name': scheme['scheme_name'],
                'eligible': eligible,
                'confidence_score': confidence_score,
                'reasons': reasons if not eligible else ["All eligibility criteria met"],
                'required_documents': required_documents,
                'missing_requirements': missing_requirements,
                'next_steps': self._generate_next_steps(eligible, scheme)
            }
        
        except Exception as e:
            logger.error(f"Eligibility check error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def recommend_schemes(self, farmer_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend schemes based on farmer profile with prioritization
        
        Args:
            farmer_profile: Farmer information
        
        Returns:
            Dict with recommended schemes prioritized by benefit and deadline
        """
        try:
            # Analyze profile first
            analysis_result = self.analyze_farmer_profile(farmer_profile)
            
            if not analysis_result['success']:
                return analysis_result
            
            analysis = analysis_result['analysis']
            relevant_categories = analysis.get('relevant_categories', [])
            
            # Get schemes from relevant categories
            state = farmer_profile.get('location', {}).get('state', '').lower()
            all_schemes = []
            
            # Search central schemes
            central_schemes = self._search_schemes_by_categories(relevant_categories, 'central')
            all_schemes.extend(central_schemes)
            
            # Search state schemes
            if state and state != 'central':
                state_schemes = self._search_schemes_by_categories(relevant_categories, state)
                all_schemes.extend(state_schemes)
            
            # Check eligibility for each scheme
            eligible_schemes = []
            for scheme in all_schemes:
                eligibility = self.check_eligibility(farmer_profile, scheme['scheme_id'])
                
                if eligibility['success'] and eligibility['eligible']:
                    # Calculate benefit amount
                    benefit_calc = self.calculate_benefit_amount(farmer_profile, scheme['scheme_id'])
                    
                    scheme_with_details = {
                        **scheme,
                        'eligibility_confidence': eligibility['confidence_score'],
                        'required_documents': eligibility['required_documents'],
                        'estimated_benefit': benefit_calc.get('estimated_benefit', 0),
                        'next_steps': eligibility['next_steps']
                    }
                    eligible_schemes.append(scheme_with_details)
            
            # Prioritize schemes
            prioritized = self.prioritize_schemes(eligible_schemes)
            
            return {
                'success': True,
                'count': len(prioritized['schemes']),
                'schemes': prioritized['schemes'],
                'total_potential_benefit': prioritized['total_benefit'],
                'profile_analysis': analysis,
                'recommendation_summary': {
                    'high_priority': len([s for s in prioritized['schemes'] if s.get('priority_score', 0) >= 80]),
                    'medium_priority': len([s for s in prioritized['schemes'] if 50 <= s.get('priority_score', 0) < 80]),
                    'low_priority': len([s for s in prioritized['schemes'] if s.get('priority_score', 0) < 50])
                }
            }
        
        except Exception as e:
            logger.error(f"Scheme recommendation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_benefit_amount(self, farmer_profile: Dict[str, Any], scheme_id: str) -> Dict[str, Any]:
        """
        Calculate estimated benefit amount based on farmer profile
        
        Args:
            farmer_profile: Farmer information
            scheme_id: Scheme identifier
        
        Returns:
            Dict with benefit calculation details
        """
        try:
            # Get scheme details
            scheme_response = self.schemes_table.get_item(Key={'scheme_id': scheme_id})
            
            if 'Item' not in scheme_response:
                return {
                    'success': False,
                    'error': f'Scheme not found: {scheme_id}'
                }
            
            scheme = self._convert_decimals(scheme_response['Item'])
            
            # Base benefit amount
            base_benefit = float(scheme.get('benefit_amount', 0))
            
            # Calculate multipliers based on profile
            land_size = farmer_profile.get('farm_details', {}).get('land_size', 0)
            farmer_category = self._determine_farmer_category(land_size)
            
            # Apply category-specific calculations
            category = scheme.get('category', '')
            estimated_benefit = base_benefit
            
            if category == 'subsidies':
                # Direct subsidy - usually fixed or per acre
                if 'per_acre' in scheme.get('description', '').lower():
                    estimated_benefit = base_benefit * land_size
            
            elif category == 'crop_insurance':
                # Insurance - based on crop value
                estimated_benefit = base_benefit  # Max coverage
            
            elif category == 'loans':
                # Loan amount - based on land size and crop type
                estimated_benefit = min(base_benefit, land_size * 50000)  # ₹50k per acre
            
            elif category == 'equipment':
                # Equipment subsidy - percentage of cost
                estimated_benefit = base_benefit  # Max subsidy amount
            
            elif category == 'irrigation':
                # Irrigation subsidy - based on land size
                estimated_benefit = min(base_benefit, land_size * 30000)  # ₹30k per acre
            
            # Calculate annual vs one-time benefit
            is_recurring = 'annual' in scheme.get('description', '').lower()
            
            # Calculate 5-year total benefit
            total_5year_benefit = estimated_benefit * 5 if is_recurring else estimated_benefit
            
            return {
                'success': True,
                'scheme_id': scheme_id,
                'scheme_name': scheme['scheme_name'],
                'base_benefit': base_benefit,
                'estimated_benefit': estimated_benefit,
                'is_recurring': is_recurring,
                'total_5year_benefit': total_5year_benefit,
                'calculation_factors': {
                    'land_size': land_size,
                    'farmer_category': farmer_category,
                    'scheme_category': category
                }
            }
        
        except Exception as e:
            logger.error(f"Benefit calculation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def prioritize_schemes(self, schemes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prioritize schemes by deadline and benefit amount
        
        Args:
            schemes: List of schemes to prioritize
        
        Returns:
            Dict with prioritized schemes
        """
        try:
            current_time = int(datetime.now().timestamp())
            prioritized_schemes = []
            
            for scheme in schemes:
                # Calculate priority score (0-100)
                priority_score = 0
                
                # Benefit amount factor (0-40 points)
                benefit = float(scheme.get('estimated_benefit', scheme.get('benefit_amount', 0)))
                if benefit > 0:
                    # Normalize benefit to 0-40 scale (max at ₹500k)
                    benefit_score = min(40, (benefit / 500000) * 40)
                    priority_score += benefit_score
                
                # Deadline urgency factor (0-30 points)
                deadline = scheme.get('application_deadline', 0)
                if deadline and deadline > current_time:
                    days_remaining = (deadline - current_time) / 86400
                    if days_remaining <= 30:
                        urgency_score = 30  # Very urgent
                    elif days_remaining <= 90:
                        urgency_score = 20  # Urgent
                    elif days_remaining <= 180:
                        urgency_score = 10  # Moderate
                    else:
                        urgency_score = 5  # Low urgency
                    priority_score += urgency_score
                else:
                    priority_score += 15  # No deadline (ongoing scheme)
                
                # Eligibility confidence factor (0-20 points)
                confidence = scheme.get('eligibility_confidence', 0.8)
                priority_score += confidence * 20
                
                # Document availability factor (0-10 points)
                required_docs = len(scheme.get('required_documents', []))
                if required_docs <= 3:
                    doc_score = 10
                elif required_docs <= 5:
                    doc_score = 7
                else:
                    doc_score = 4
                priority_score += doc_score
                
                # Add priority information to scheme
                scheme['priority_score'] = round(priority_score, 2)
                scheme['priority_level'] = self._get_priority_level(priority_score)
                scheme['days_to_deadline'] = self._calculate_days_to_deadline(deadline)
                
                prioritized_schemes.append(scheme)
            
            # Sort by priority score (descending)
            prioritized_schemes.sort(key=lambda x: x['priority_score'], reverse=True)
            
            # Calculate total potential benefit
            total_benefit = sum(float(s.get('estimated_benefit', s.get('benefit_amount', 0))) 
                              for s in prioritized_schemes)
            
            return {
                'success': True,
                'schemes': prioritized_schemes,
                'total_benefit': total_benefit,
                'prioritization_summary': {
                    'total_schemes': len(prioritized_schemes),
                    'high_priority': len([s for s in prioritized_schemes if s['priority_score'] >= 80]),
                    'urgent_deadlines': len([s for s in prioritized_schemes if s.get('days_to_deadline') is not None and s.get('days_to_deadline') <= 30])
                }
            }
        
        except Exception as e:
            logger.error(f"Scheme prioritization error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    # Helper methods
    
    def _determine_farmer_category(self, land_size: float) -> str:
        """Determine farmer category based on land size"""
        if land_size <= 1.0:
            return 'marginal'
        elif land_size <= 2.0:
            return 'small'
        elif land_size <= 10.0:
            return 'medium'
        else:
            return 'large'
    
    def _calculate_profile_completeness(self, profile: Dict[str, Any]) -> float:
        """Calculate profile completeness score (0-1)"""
        required_fields = [
            'location.state',
            'farm_details.land_size',
            'farm_details.crops',
            'annual_income'
        ]
        
        completed = 0
        for field in required_fields:
            keys = field.split('.')
            value = profile
            for key in keys:
                value = value.get(key, {})
            if value:
                completed += 1
        
        return completed / len(required_fields)
    
    def _check_land_size_eligibility(self, land_size: float, requirement: str) -> bool:
        """Check if land size meets requirement"""
        try:
            if 'below' in requirement.lower() or 'under' in requirement.lower():
                # Extract number
                import re
                numbers = re.findall(r'\d+\.?\d*', requirement)
                if numbers:
                    max_size = float(numbers[0])
                    return land_size <= max_size
            elif 'above' in requirement.lower() or 'over' in requirement.lower():
                import re
                numbers = re.findall(r'\d+\.?\d*', requirement)
                if numbers:
                    min_size = float(numbers[0])
                    return land_size >= min_size
            return True
        except:
            return True
    
    def _generate_required_documents(self, scheme: Dict[str, Any], 
                                    farmer_profile: Dict[str, Any]) -> List[str]:
        """Generate list of required documents for scheme application"""
        base_documents = scheme.get('required_documents', [])
        
        # Add profile-specific documents
        additional_docs = []
        
        # Check if income proof needed
        if scheme.get('category') in ['loans', 'subsidies']:
            if 'Income Certificate' not in base_documents:
                additional_docs.append('Income Certificate')
        
        # Check if caste certificate needed for certain schemes
        if 'SC/ST' in scheme.get('description', ''):
            if 'Caste Certificate' not in base_documents:
                additional_docs.append('Caste Certificate')
        
        return base_documents + additional_docs
    
    def _calculate_eligibility_confidence(self, farmer_profile: Dict[str, Any],
                                         scheme: Dict[str, Any], eligible: bool) -> float:
        """Calculate confidence score for eligibility determination"""
        if not eligible:
            return 0.0
        
        # Base confidence
        confidence = 0.8
        
        # Increase confidence if profile is complete
        completeness = self._calculate_profile_completeness(farmer_profile)
        confidence += (completeness - 0.5) * 0.2
        
        # Decrease confidence if scheme has complex criteria
        criteria_count = len(scheme.get('eligibility_criteria', {}))
        if criteria_count > 5:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _generate_next_steps(self, eligible: bool, scheme: Dict[str, Any]) -> List[str]:
        """Generate next steps for scheme application"""
        if not eligible:
            return [
                "Review eligibility criteria",
                "Contact local agriculture office for guidance",
                "Explore alternative schemes"
            ]
        
        steps = [
            f"Gather required documents: {', '.join(scheme.get('required_documents', [])[:3])}",
            f"Visit official website: {scheme.get('official_website', 'Contact local office')}",
            f"Application process: {scheme.get('application_process', 'Contact local agriculture office')}"
        ]
        
        # Add deadline reminder if applicable
        deadline = scheme.get('application_deadline', 0)
        if deadline:
            days_remaining = self._calculate_days_to_deadline(deadline)
            if days_remaining and days_remaining <= 30:
                steps.insert(0, f"⚠️ URGENT: Apply within {days_remaining} days")
        
        return steps
    
    def _search_schemes_by_categories(self, categories: List[str], state: str) -> List[Dict[str, Any]]:
        """Search schemes by categories and state"""
        schemes = []
        
        for category in categories:
            try:
                response = self.schemes_table.query(
                    IndexName='CategorySchemeIndex',
                    KeyConditionExpression='category = :cat',
                    FilterExpression='#state = :state AND active_status = :status',
                    ExpressionAttributeNames={'#state': 'state'},
                    ExpressionAttributeValues={
                        ':cat': category.lower(),
                        ':state': state.lower(),
                        ':status': 'active'
                    }
                )
                schemes.extend(response.get('Items', []))
            except Exception as e:
                logger.warning(f"Error searching category {category}: {e}")
        
        return self._convert_decimals(schemes)
    
    def _get_priority_level(self, score: float) -> str:
        """Get priority level from score"""
        if score >= 80:
            return 'high'
        elif score >= 50:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_days_to_deadline(self, deadline: int) -> Optional[int]:
        """Calculate days remaining to deadline"""
        if not deadline:
            return None
        
        current_time = int(datetime.now().timestamp())
        if deadline <= current_time:
            return 0
        
        return int((deadline - current_time) / 86400)
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from AI response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    'relevant_categories': ['subsidies', 'crop_insurance', 'loans'],
                    'farmer_needs': ['Financial support', 'Risk protection'],
                    'priority_areas': ['Income support', 'Crop protection'],
                    'estimated_benefits': 'Moderate to high'
                }
        except:
            return {
                'relevant_categories': ['subsidies'],
                'farmer_needs': ['Financial support'],
                'priority_areas': ['Income support'],
                'estimated_benefits': 'Moderate'
            }
    
    def _convert_decimals(self, obj):
        """Convert Decimal objects to float for JSON serialization"""
        if isinstance(obj, list):
            return [self._convert_decimals(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._convert_decimals(value) for key, value in obj.items()}
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj


# Tool functions for agent integration

def create_scheme_discovery_tools(region: str = "us-east-1") -> SchemeDiscoveryTools:
    """
    Factory function to create scheme discovery tools instance
    
    Args:
        region: AWS region
    
    Returns:
        SchemeDiscoveryTools instance
    """
    return SchemeDiscoveryTools(region=region)


def recommend_schemes_tool(farmer_profile: Dict[str, Any]) -> str:
    """
    Tool for recommending schemes to farmers
    
    Args:
        farmer_profile: Farmer information
    
    Returns:
        Formatted scheme recommendations
    """
    tools = create_scheme_discovery_tools()
    result = tools.recommend_schemes(farmer_profile)
    
    if result['success']:
        output = f"Found {result['count']} applicable schemes for this farmer:\n\n"
        
        for i, scheme in enumerate(result['schemes'][:5], 1):
            output += f"{i}. {scheme['scheme_name']}\n"
            output += f"   Priority: {scheme['priority_level'].upper()} ({scheme['priority_score']:.1f}/100)\n"
            output += f"   Estimated Benefit: ₹{scheme.get('estimated_benefit', 0):,.0f}\n"
            output += f"   Category: {scheme['category'].replace('_', ' ').title()}\n"
            
            if scheme.get('days_to_deadline'):
                output += f"   ⏰ Deadline: {scheme['days_to_deadline']} days remaining\n"
            
            output += f"   Documents: {', '.join(scheme['required_documents'][:3])}\n\n"
        
        output += f"\nTotal Potential Benefit: ₹{result['total_potential_benefit']:,.0f}\n"
        
        return output
    else:
        return f"Error: {result.get('error', 'Failed to recommend schemes')}"


def check_eligibility_tool(farmer_profile: Dict[str, Any], scheme_id: str) -> str:
    """
    Tool for checking scheme eligibility
    
    Args:
        farmer_profile: Farmer information
        scheme_id: Scheme identifier
    
    Returns:
        Formatted eligibility result
    """
    tools = create_scheme_discovery_tools()
    result = tools.check_eligibility(farmer_profile, scheme_id)
    
    if result['success']:
        output = f"Eligibility Check: {result['scheme_name']}\n\n"
        output += f"Status: {'✅ ELIGIBLE' if result['eligible'] else '❌ NOT ELIGIBLE'}\n"
        output += f"Confidence: {result['confidence_score']*100:.0f}%\n\n"
        
        output += "Reasons:\n"
        for reason in result['reasons']:
            output += f"  • {reason}\n"
        
        if result['eligible']:
            output += f"\nRequired Documents:\n"
            for doc in result['required_documents']:
                output += f"  • {doc}\n"
            
            output += f"\nNext Steps:\n"
            for step in result['next_steps']:
                output += f"  {step}\n"
        
        return output
    else:
        return f"Error: {result.get('error', 'Failed to check eligibility')}"
