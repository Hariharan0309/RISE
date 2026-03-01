"""
Schemes Navigator Agent for MissionAI Farmer Agent.

This agent specializes in government scheme awareness, eligibility checking,
and application guidance for central and state-level agricultural schemes.
"""

import logging
from typing import Dict, Any, Optional, List

from tools.scheme_tools import (
    list_schemes,
    get_scheme_details,
    check_eligibility,
    get_application_steps
)

logger = logging.getLogger(__name__)


class SchemesNavigatorAgent:
    """
    Specialized agent for government scheme navigation and eligibility checking.
    
    This agent provides scheme discovery, detailed information, eligibility
    determination, and application guidance for farmers.
    """
    
    def __init__(self):
        """Initialize the Schemes Navigator Agent."""
        self.name = "Schemes Navigator Agent"
        self.description = "Specialized in government schemes and eligibility checking"
        self.tools = [
            list_schemes,
            get_scheme_details,
            check_eligibility,
            get_application_steps
        ]
        logger.info(f"{self.name} initialized")
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the Schemes Navigator Agent.
        
        Returns:
            str: System prompt defining agent's role and expertise
        """
        return """You are an expert government schemes advisor specializing in agricultural schemes and farmer welfare programs.

Your expertise includes:
- Central and state-level agricultural schemes
- Eligibility criteria and requirements
- Application processes and documentation
- Subsidy programs (PM-KISAN, PMFBY, etc.)
- Insurance schemes for crops and farmers
- Loan facilities (KCC, NABARD schemes)
- Training and capacity building programs
- Organic farming support schemes
- Irrigation and mechanization subsidies

When helping farmers with schemes:
1. Always explain schemes in simple, clear language
2. Check eligibility carefully based on farmer profile
3. Provide complete information (benefits, criteria, process)
4. Guide through application steps systematically
5. Mention required documents upfront
6. Provide helpline numbers and websites
7. Prioritize schemes most relevant to farmer's situation
8. Explain both central and state schemes available

For scheme discovery:
1. Filter by category (subsidy, insurance, loan, training)
2. Consider farmer's state for state-specific schemes
3. Present schemes with clear descriptions
4. Highlight key benefits and eligibility

For eligibility checking:
1. Ask for necessary farmer information (land size, crops, income)
2. Check all criteria systematically
3. Explain why farmer is eligible or not eligible
4. Suggest alternative schemes if not eligible
5. Be transparent about requirements

For application guidance:
1. Break down process into clear steps
2. List all required documents
3. Provide website and helpline information
4. Give realistic timelines
5. Offer tips for successful application
6. Mention common mistakes to avoid

Always prioritize:
- Farmer's best interests and maximum benefits
- Schemes that improve income and reduce risk
- Sustainable and organic farming schemes
- Easy-to-access schemes with simple processes
- Schemes with high success rates

Provide advice that is:
- Accurate and up-to-date
- Easy to understand for farmers with limited literacy
- Action-oriented with clear next steps
- Supportive and encouraging
- Culturally sensitive and respectful

Examples of good advice:
- "You are eligible for PM-KISAN which gives ₹6000 per year. You just need Aadhaar and land documents"
- "Based on your 3 acres of land, you qualify for Krishi Bhagya scheme with 80% subsidy on drip irrigation"
- "Since you grow organic crops, PKVY scheme can give you ₹50,000 per hectare for 3 years"
- "Your income is above the limit for this scheme, but you can apply for KCC loan at low interest"

Remember:
- Many farmers are not aware of schemes they qualify for
- Application processes can be intimidating - provide reassurance
- Documentation is often a barrier - explain clearly what's needed
- Follow-up and persistence are important - encourage farmers
- Local agriculture officers can help - mention this resource
"""
    
    def process(
        self,
        query_type: str,
        category: Optional[str] = None,
        state: Optional[str] = None,
        scheme_id: Optional[str] = None,
        farmer_profile: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a government scheme query.
        
        Args:
            query_type: Type of query ("list", "details", "eligibility", "application")
            category: Optional category filter (subsidy, insurance, loan, training)
            state: Optional state filter
            scheme_id: Scheme identifier for details/eligibility/application queries
            farmer_profile: Farmer profile for eligibility checking
            
        Returns:
            dict: Scheme information result
        """
        logger.info(f"Processing scheme query: {query_type}")
        
        try:
            if query_type == "list":
                # List schemes with optional filters
                schemes = list_schemes(category=category, state=state)
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "category": category,
                    "state": state,
                    "total_schemes": len(schemes),
                    "schemes": schemes,
                    "message": f"Found {len(schemes)} schemes"
                }
            
            elif query_type == "details":
                # Get detailed scheme information
                if not scheme_id:
                    return {
                        "success": False,
                        "error": "Scheme ID is required for details query"
                    }
                
                details = get_scheme_details(scheme_id)
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "scheme": details,
                    "message": f"Retrieved details for {details['name']}"
                }
            
            elif query_type == "eligibility":
                # Check farmer eligibility for a scheme
                if not scheme_id:
                    return {
                        "success": False,
                        "error": "Scheme ID is required for eligibility check"
                    }
                
                if not farmer_profile:
                    return {
                        "success": False,
                        "error": "Farmer profile is required for eligibility check"
                    }
                
                eligibility_result = check_eligibility(scheme_id, farmer_profile)
                
                # Add recommendations based on eligibility
                if eligibility_result["eligible"]:
                    eligibility_result["recommendation"] = (
                        f"You are eligible for {eligibility_result['scheme_name']}! "
                        "Proceed with the application process."
                    )
                else:
                    eligibility_result["recommendation"] = (
                        f"You are not currently eligible for {eligibility_result['scheme_name']}. "
                        "Let me help you find other schemes you may qualify for."
                    )
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "eligibility": eligibility_result,
                    "message": "Eligibility check completed"
                }
            
            elif query_type == "application":
                # Get application steps and guidance
                if not scheme_id:
                    return {
                        "success": False,
                        "error": "Scheme ID is required for application guidance"
                    }
                
                application_info = get_application_steps(scheme_id)
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "application": application_info,
                    "message": f"Application guidance for {application_info['scheme_name']}"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown query type: {query_type}"
                }
        
        except ValueError as e:
            logger.error(f"Validation error in scheme query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Invalid input for scheme query"
            }
        
        except Exception as e:
            logger.error(f"Error processing scheme query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred while processing scheme query"
            }
    
    def list_available_schemes(
        self,
        category: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List available government schemes with optional filters.
        
        Args:
            category: Optional category filter (subsidy, insurance, loan, training)
            state: Optional state filter
            
        Returns:
            dict: List of schemes
        """
        return self.process(
            query_type="list",
            category=category,
            state=state
        )
    
    def get_scheme_information(self, scheme_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific scheme.
        
        Args:
            scheme_id: Scheme identifier
            
        Returns:
            dict: Detailed scheme information
        """
        return self.process(
            query_type="details",
            scheme_id=scheme_id
        )
    
    def check_farmer_eligibility(
        self,
        scheme_id: str,
        farmer_profile: Dict
    ) -> Dict[str, Any]:
        """
        Check if a farmer is eligible for a scheme.
        
        Args:
            scheme_id: Scheme identifier
            farmer_profile: Farmer profile with land, income, crops, etc.
            
        Returns:
            dict: Eligibility result with reasoning
        """
        return self.process(
            query_type="eligibility",
            scheme_id=scheme_id,
            farmer_profile=farmer_profile
        )
    
    def get_application_guidance(self, scheme_id: str) -> Dict[str, Any]:
        """
        Get step-by-step application guidance for a scheme.
        
        Args:
            scheme_id: Scheme identifier
            
        Returns:
            dict: Application steps and requirements
        """
        return self.process(
            query_type="application",
            scheme_id=scheme_id
        )
    
    def find_schemes_for_farmer(self, farmer_profile: Dict) -> Dict[str, Any]:
        """
        Find all schemes a farmer may be eligible for.
        
        Args:
            farmer_profile: Farmer profile with land, income, crops, etc.
            
        Returns:
            dict: List of potentially eligible schemes
        """
        logger.info("Finding schemes for farmer profile")
        
        try:
            # Get farmer's state if available
            state = None
            if "location" in farmer_profile and "state" in farmer_profile["location"]:
                state = farmer_profile["location"]["state"]
            
            # Get all schemes (central + state-specific)
            all_schemes = list_schemes(state=state)
            
            # Check eligibility for each scheme
            eligible_schemes = []
            potentially_eligible = []
            
            for scheme in all_schemes:
                try:
                    eligibility = check_eligibility(
                        scheme["scheme_id"],
                        farmer_profile
                    )
                    
                    if eligibility["eligible"]:
                        eligible_schemes.append({
                            "scheme": scheme,
                            "eligibility": eligibility
                        })
                    else:
                        # Check if close to eligible (failed only 1 criterion)
                        if len(eligibility["reasons"]) <= 1:
                            potentially_eligible.append({
                                "scheme": scheme,
                                "eligibility": eligibility
                            })
                
                except Exception as e:
                    logger.warning(f"Error checking eligibility for {scheme['scheme_id']}: {str(e)}")
                    continue
            
            return {
                "success": True,
                "farmer_state": state,
                "total_schemes_checked": len(all_schemes),
                "eligible_schemes": eligible_schemes,
                "potentially_eligible": potentially_eligible,
                "message": f"Found {len(eligible_schemes)} schemes you are eligible for"
            }
        
        except Exception as e:
            logger.error(f"Error finding schemes for farmer: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred while finding schemes"
            }
    
    def get_tools(self):
        """Get list of available tools for this agent."""
        return self.tools
