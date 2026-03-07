"""
RISE Government Scheme Tools
Tools for managing, searching, and analyzing government agricultural schemes
"""

import boto3
import logging
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
import os
from decimal import Decimal
import uuid

logger = logging.getLogger(__name__)


class GovernmentSchemeTools:
    """Government scheme management tools for RISE farming assistant"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize government scheme tools with AWS clients
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        
        # DynamoDB table for government schemes
        self.schemes_table = self.dynamodb.Table('RISE-GovernmentSchemes')
        
        # API endpoints for government scheme data
        # Note: In production, integrate with actual government APIs
        # Examples: data.gov.in, pmkisan.gov.in, state agricultural portals
        self.api_endpoints = {
            'pmkisan': os.getenv('PMKISAN_API_URL', ''),
            'pmfby': os.getenv('PMFBY_API_URL', ''),
            'data_gov': os.getenv('DATA_GOV_IN_API_URL', 'https://api.data.gov.in/resource/'),
            'state_portals': {}  # State-specific portals
        }
        
        # Scheme categories
        self.scheme_categories = [
            'crop_insurance',
            'subsidies',
            'loans',
            'equipment',
            'irrigation',
            'organic_farming',
            'training',
            'market_access',
            'soil_health',
            'seeds'
        ]
        
        logger.info(f"Government scheme tools initialized in region {region}")
    
    def ingest_scheme_data(self, scheme_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest government scheme data into the database
        
        Args:
            scheme_data: Scheme information to ingest
        
        Returns:
            Dict with ingestion result
        """
        try:
            # Generate scheme ID if not provided
            if 'scheme_id' not in scheme_data:
                scheme_data['scheme_id'] = f"SCH_{uuid.uuid4().hex[:12].upper()}"
            
            # Validate required fields
            required_fields = ['scheme_name', 'scheme_type', 'state', 'category']
            for field in required_fields:
                if field not in scheme_data:
                    return {
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }
            
            # Normalize and enrich data
            enriched_scheme = self._enrich_scheme_data(scheme_data)
            
            # Store in DynamoDB
            self.schemes_table.put_item(Item=enriched_scheme)
            
            logger.info(f"Ingested scheme: {enriched_scheme['scheme_id']} - {enriched_scheme['scheme_name']}")
            
            return {
                'success': True,
                'scheme_id': enriched_scheme['scheme_id'],
                'scheme_name': enriched_scheme['scheme_name'],
                'message': 'Scheme data ingested successfully'
            }
        
        except Exception as e:
            logger.error(f"Scheme ingestion error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_schemes(self,
                      state: Optional[str] = None,
                      category: Optional[str] = None,
                      scheme_type: Optional[str] = None,
                      active_only: bool = True) -> Dict[str, Any]:
        """
        Search for government schemes based on criteria
        
        Args:
            state: State name (None for central schemes)
            category: Scheme category
            scheme_type: Type of scheme (central/state)
            active_only: Only return active schemes
        
        Returns:
            Dict with matching schemes
        """
        try:
            schemes = []
            
            # Query based on provided criteria
            if state and scheme_type:
                # Query by state and scheme type
                response = self.schemes_table.query(
                    IndexName='StateSchemeIndex',
                    KeyConditionExpression='#state = :state AND scheme_type = :type',
                    ExpressionAttributeNames={'#state': 'state'},
                    ExpressionAttributeValues={
                        ':state': state.lower(),
                        ':type': scheme_type.lower()
                    }
                )
                schemes = response.get('Items', [])
            
            elif category:
                # Query by category
                response = self.schemes_table.query(
                    IndexName='CategorySchemeIndex',
                    KeyConditionExpression='category = :cat',
                    ExpressionAttributeValues={
                        ':cat': category.lower()
                    },
                    ScanIndexForward=False  # Sort by benefit amount descending
                )
                schemes = response.get('Items', [])
            
            else:
                # Scan all schemes (use with caution in production)
                response = self.schemes_table.scan()
                schemes = response.get('Items', [])
            
            # Filter by active status
            if active_only:
                schemes = [s for s in schemes if s.get('active_status') == 'active']
            
            # Convert Decimal to float for JSON serialization
            schemes = self._convert_decimals(schemes)
            
            return {
                'success': True,
                'count': len(schemes),
                'schemes': schemes
            }
        
        except Exception as e:
            logger.error(f"Scheme search error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_scheme_details(self, scheme_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific scheme
        
        Args:
            scheme_id: Unique scheme identifier
        
        Returns:
            Dict with scheme details
        """
        try:
            response = self.schemes_table.get_item(Key={'scheme_id': scheme_id})
            
            if 'Item' not in response:
                return {
                    'success': False,
                    'error': f'Scheme not found: {scheme_id}'
                }
            
            scheme = self._convert_decimals(response['Item'])
            
            return {
                'success': True,
                'scheme': scheme
            }
        
        except Exception as e:
            logger.error(f"Get scheme details error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_scheme_status(self, scheme_id: str, status: str) -> Dict[str, Any]:
        """
        Update the active status of a scheme
        
        Args:
            scheme_id: Unique scheme identifier
            status: New status (active/inactive/expired)
        
        Returns:
            Dict with update result
        """
        try:
            valid_statuses = ['active', 'inactive', 'expired']
            if status not in valid_statuses:
                return {
                    'success': False,
                    'error': f'Invalid status. Must be one of: {valid_statuses}'
                }
            
            self.schemes_table.update_item(
                Key={'scheme_id': scheme_id},
                UpdateExpression='SET active_status = :status, last_updated = :updated',
                ExpressionAttributeValues={
                    ':status': status,
                    ':updated': int(datetime.now().timestamp())
                }
            )
            
            logger.info(f"Updated scheme {scheme_id} status to {status}")
            
            return {
                'success': True,
                'scheme_id': scheme_id,
                'new_status': status
            }
        
        except Exception as e:
            logger.error(f"Update scheme status error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def scrape_government_schemes(self, source: str = 'all') -> Dict[str, Any]:
        """
        Scrape government scheme data from various sources
        
        Args:
            source: Data source to scrape (all/pmkisan/pmfby/state)
        
        Returns:
            Dict with scraping results
        """
        try:
            ingested_count = 0
            errors = []
            
            # Mock data for demonstration
            # In production, implement actual web scraping or API integration
            mock_schemes = self._get_mock_schemes()
            
            for scheme_data in mock_schemes:
                result = self.ingest_scheme_data(scheme_data)
                if result['success']:
                    ingested_count += 1
                else:
                    errors.append({
                        'scheme': scheme_data.get('scheme_name', 'Unknown'),
                        'error': result['error']
                    })
            
            return {
                'success': True,
                'source': source,
                'ingested_count': ingested_count,
                'errors': errors,
                'message': f'Successfully ingested {ingested_count} schemes'
            }
        
        except Exception as e:
            logger.error(f"Scheme scraping error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def categorize_scheme(self, scheme_description: str) -> Dict[str, Any]:
        """
        Use AI to categorize a scheme based on its description
        
        Args:
            scheme_description: Description of the scheme
        
        Returns:
            Dict with categorization results
        """
        try:
            prompt = f"""Analyze this government agricultural scheme and categorize it:

Scheme Description: {scheme_description}

Available Categories:
- crop_insurance: Insurance schemes for crop protection
- subsidies: Direct financial subsidies and support
- loans: Agricultural loans and credit facilities
- equipment: Equipment purchase subsidies
- irrigation: Irrigation infrastructure support
- organic_farming: Organic farming promotion schemes
- training: Training and skill development programs
- market_access: Market linkage and access programs
- soil_health: Soil health management schemes
- seeds: Seed distribution and quality programs

Provide:
1. Primary category (one of the above)
2. Secondary categories (if applicable)
3. Target beneficiaries (small farmers, marginal farmers, all farmers, etc.)
4. Key benefits summary
5. Suggested tags for searchability

Format as JSON."""

            # Use Amazon Bedrock for categorization
            from config import Config
            response = self.bedrock.invoke_model(
                modelId=Config.BEDROCK_MODEL_ID,
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 500,
                    'messages': [{
                        'role': 'user',
                        'content': prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            ai_response = response_body['content'][0]['text']
            
            # Parse AI response
            categorization = self._parse_categorization_response(ai_response)
            
            return {
                'success': True,
                'categorization': categorization
            }
        
        except Exception as e:
            logger.error(f"Scheme categorization error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def monitor_scheme_updates(self) -> Dict[str, Any]:
        """
        Monitor for updates to existing schemes
        
        Returns:
            Dict with monitoring results
        """
        try:
            # Get all active schemes
            response = self.schemes_table.query(
                IndexName='DeadlineSchemeIndex',
                KeyConditionExpression='active_status = :status',
                ExpressionAttributeValues={
                    ':status': 'active'
                }
            )
            
            schemes = response.get('Items', [])
            updates_found = []
            expired_schemes = []
            
            current_time = int(datetime.now().timestamp())
            
            for scheme in schemes:
                # Check if scheme has expired
                deadline = scheme.get('application_deadline', 0)
                if deadline and deadline < current_time:
                    expired_schemes.append(scheme['scheme_id'])
                    self.update_scheme_status(scheme['scheme_id'], 'expired')
                
                # In production, check external sources for updates
                # For now, just log monitoring activity
            
            return {
                'success': True,
                'total_schemes_monitored': len(schemes),
                'expired_schemes': len(expired_schemes),
                'updates_found': len(updates_found),
                'message': f'Monitored {len(schemes)} schemes, marked {len(expired_schemes)} as expired'
            }
        
        except Exception as e:
            logger.error(f"Scheme monitoring error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _enrich_scheme_data(self, scheme_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich scheme data with additional fields"""
        
        enriched = scheme_data.copy()
        
        # Add timestamps
        current_time = int(datetime.now().timestamp())
        enriched['created_at'] = enriched.get('created_at', current_time)
        enriched['last_updated'] = current_time
        
        # Normalize fields
        enriched['state'] = enriched.get('state', 'central').lower()
        enriched['category'] = enriched.get('category', 'subsidies').lower()
        enriched['scheme_type'] = enriched.get('scheme_type', 'central').lower()
        enriched['active_status'] = enriched.get('active_status', 'active')
        
        # Convert benefit amount to Decimal
        if 'benefit_amount' in enriched:
            enriched['benefit_amount'] = Decimal(str(enriched['benefit_amount']))
        else:
            enriched['benefit_amount'] = Decimal('0')
        
        # Convert deadline to timestamp
        if 'application_deadline' in enriched and isinstance(enriched['application_deadline'], str):
            try:
                deadline_dt = datetime.fromisoformat(enriched['application_deadline'])
                enriched['application_deadline'] = int(deadline_dt.timestamp())
            except:
                enriched['application_deadline'] = 0
        
        # Add search tags
        if 'tags' not in enriched:
            enriched['tags'] = self._generate_tags(enriched)
        
        return enriched
    
    def _generate_tags(self, scheme_data: Dict[str, Any]) -> List[str]:
        """Generate search tags for a scheme"""
        tags = []
        
        # Add category tags
        if 'category' in scheme_data:
            tags.append(scheme_data['category'])
        
        # Add state tags
        if 'state' in scheme_data:
            tags.append(scheme_data['state'])
        
        # Add scheme type tags
        if 'scheme_type' in scheme_data:
            tags.append(scheme_data['scheme_type'])
        
        # Add eligibility tags
        if 'eligibility_criteria' in scheme_data:
            eligibility = scheme_data['eligibility_criteria']
            if isinstance(eligibility, dict):
                land_size = eligibility.get('land_size')
                if land_size:
                    # Try to extract numeric value from land_size
                    try:
                        if isinstance(land_size, (int, float)):
                            tags.append('small_farmer' if land_size <= 2 else 'large_farmer')
                        elif isinstance(land_size, str):
                            # Try to parse numeric value from string
                            import re
                            numbers = re.findall(r'\d+\.?\d*', land_size)
                            if numbers:
                                size = float(numbers[0])
                                tags.append('small_farmer' if size <= 2 else 'large_farmer')
                    except (ValueError, TypeError):
                        pass  # Skip if can't parse land size
        
        return list(set(tags))  # Remove duplicates
    
    def _get_mock_schemes(self) -> List[Dict[str, Any]]:
        """Get mock scheme data for demonstration"""
        
        return [
            {
                'scheme_name': 'PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)',
                'scheme_type': 'central',
                'state': 'central',
                'category': 'subsidies',
                'description': 'Direct income support of ₹6000 per year to all farmer families',
                'benefit_amount': 6000,
                'eligibility_criteria': {
                    'land_ownership': 'required',
                    'land_size': 'any',
                    'farmer_type': 'all'
                },
                'application_process': 'Online through PM-KISAN portal or CSC',
                'required_documents': ['Aadhaar', 'Bank Account', 'Land Records'],
                'application_deadline': int((datetime.now() + timedelta(days=365)).timestamp()),
                'official_website': 'https://pmkisan.gov.in',
                'active_status': 'active'
            },
            {
                'scheme_name': 'PMFBY (Pradhan Mantri Fasal Bima Yojana)',
                'scheme_type': 'central',
                'state': 'central',
                'category': 'crop_insurance',
                'description': 'Comprehensive crop insurance scheme covering all stages of crop cycle',
                'benefit_amount': 200000,
                'eligibility_criteria': {
                    'land_ownership': 'owner_or_tenant',
                    'land_size': 'any',
                    'farmer_type': 'all'
                },
                'application_process': 'Through banks, CSCs, or insurance companies',
                'required_documents': ['Aadhaar', 'Bank Account', 'Land Records', 'Sowing Certificate'],
                'application_deadline': int((datetime.now() + timedelta(days=180)).timestamp()),
                'official_website': 'https://pmfby.gov.in',
                'active_status': 'active'
            },
            {
                'scheme_name': 'Kisan Credit Card (KCC)',
                'scheme_type': 'central',
                'state': 'central',
                'category': 'loans',
                'description': 'Credit facility for farmers to meet agricultural expenses',
                'benefit_amount': 300000,
                'eligibility_criteria': {
                    'land_ownership': 'required',
                    'land_size': 'any',
                    'farmer_type': 'all'
                },
                'application_process': 'Through banks and cooperative societies',
                'required_documents': ['Aadhaar', 'Land Records', 'Income Proof'],
                'application_deadline': 0,  # No deadline, ongoing
                'official_website': 'https://www.nabard.org/kcc.aspx',
                'active_status': 'active'
            },
            {
                'scheme_name': 'Soil Health Card Scheme',
                'scheme_type': 'central',
                'state': 'central',
                'category': 'soil_health',
                'description': 'Free soil testing and health cards for farmers',
                'benefit_amount': 0,
                'eligibility_criteria': {
                    'land_ownership': 'required',
                    'land_size': 'any',
                    'farmer_type': 'all'
                },
                'application_process': 'Through state agriculture departments',
                'required_documents': ['Aadhaar', 'Land Records'],
                'application_deadline': 0,
                'official_website': 'https://soilhealth.dac.gov.in',
                'active_status': 'active'
            },
            {
                'scheme_name': 'Paramparagat Krishi Vikas Yojana (PKVY)',
                'scheme_type': 'central',
                'state': 'central',
                'category': 'organic_farming',
                'description': 'Support for organic farming through cluster approach',
                'benefit_amount': 50000,
                'eligibility_criteria': {
                    'land_ownership': 'required',
                    'land_size': 'any',
                    'farmer_type': 'organic_farmers'
                },
                'application_process': 'Through state agriculture departments',
                'required_documents': ['Aadhaar', 'Land Records', 'Group Formation Certificate'],
                'application_deadline': int((datetime.now() + timedelta(days=90)).timestamp()),
                'official_website': 'https://pgsindia-ncof.gov.in',
                'active_status': 'active'
            }
        ]
    
    def _parse_categorization_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI categorization response"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback to basic parsing
                return {
                    'primary_category': 'subsidies',
                    'secondary_categories': [],
                    'target_beneficiaries': ['all_farmers'],
                    'key_benefits': ai_response[:200],
                    'tags': []
                }
        except:
            return {
                'primary_category': 'subsidies',
                'secondary_categories': [],
                'target_beneficiaries': ['all_farmers'],
                'key_benefits': 'Unable to parse categorization',
                'tags': []
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

def create_government_scheme_tools(region: str = "us-east-1") -> GovernmentSchemeTools:
    """
    Factory function to create government scheme tools instance
    
    Args:
        region: AWS region
    
    Returns:
        GovernmentSchemeTools instance
    """
    return GovernmentSchemeTools(region=region)


def search_schemes_tool(state: Optional[str] = None, category: Optional[str] = None) -> str:
    """
    Tool for searching government schemes
    
    Args:
        state: State name (None for central schemes)
        category: Scheme category
    
    Returns:
        Formatted scheme search results
    """
    tools = create_government_scheme_tools()
    result = tools.search_schemes(state=state, category=category)
    
    if result['success']:
        output = f"Found {result['count']} government schemes:\n\n"
        
        for scheme in result['schemes'][:5]:  # Show top 5
            output += f"• {scheme['scheme_name']}\n"
            output += f"  Type: {scheme['scheme_type'].title()}\n"
            output += f"  Category: {scheme['category'].replace('_', ' ').title()}\n"
            output += f"  Benefit: ₹{scheme.get('benefit_amount', 0):,.0f}\n"
            output += f"  Status: {scheme['active_status'].title()}\n\n"
        
        if result['count'] > 5:
            output += f"... and {result['count'] - 5} more schemes\n"
        
        return output
    else:
        return f"Error: {result.get('error', 'Failed to search schemes')}"


def get_scheme_details_tool(scheme_id: str) -> str:
    """
    Tool for getting detailed scheme information
    
    Args:
        scheme_id: Unique scheme identifier
    
    Returns:
        Formatted scheme details
    """
    tools = create_government_scheme_tools()
    result = tools.get_scheme_details(scheme_id)
    
    if result['success']:
        scheme = result['scheme']
        output = f"""Scheme Details:

Name: {scheme['scheme_name']}
Type: {scheme['scheme_type'].title()}
Category: {scheme['category'].replace('_', ' ').title()}
Status: {scheme['active_status'].title()}

Description:
{scheme.get('description', 'No description available')}

Benefit Amount: ₹{scheme.get('benefit_amount', 0):,.0f}

Eligibility:
"""
        eligibility = scheme.get('eligibility_criteria', {})
        for key, value in eligibility.items():
            output += f"  • {key.replace('_', ' ').title()}: {value}\n"
        
        output += f"\nRequired Documents:\n"
        for doc in scheme.get('required_documents', []):
            output += f"  • {doc}\n"
        
        output += f"\nApplication Process:\n{scheme.get('application_process', 'Contact local agriculture office')}\n"
        
        if scheme.get('official_website'):
            output += f"\nOfficial Website: {scheme['official_website']}\n"
        
        return output
    else:
        return f"Error: {result.get('error', 'Failed to get scheme details')}"


def ingest_scheme_tool(scheme_data: Dict[str, Any]) -> str:
    """
    Tool for ingesting new scheme data
    
    Args:
        scheme_data: Scheme information to ingest
    
    Returns:
        Ingestion result message
    """
    tools = create_government_scheme_tools()
    result = tools.ingest_scheme_data(scheme_data)
    
    if result['success']:
        return f"Successfully ingested scheme: {result['scheme_name']} (ID: {result['scheme_id']})"
    else:
        return f"Error: {result.get('error', 'Failed to ingest scheme')}"
