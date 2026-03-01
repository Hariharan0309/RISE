"""
Community Advisor Agent for MissionAI Farmer Agent.

This agent specializes in connecting farmers with local community knowledge,
facilitating peer-to-peer learning, and combining AI recommendations with
community wisdom.
"""

import logging
from typing import Dict, Any, Optional, List

from tools.community_tools import (
    search_forum,
    summarize_discussions,
    store_experience,
    combine_advice
)

logger = logging.getLogger(__name__)


class CommunityAdvisorAgent:
    """
    Specialized agent for community forum interactions and local knowledge.
    
    This agent searches community forums, summarizes local farmer insights,
    stores farmer experiences, and combines AI recommendations with
    community wisdom for holistic advice.
    """
    
    def __init__(self):
        """Initialize the Community Advisor Agent."""
        self.name = "Community Advisor Agent"
        self.description = "Specialized in community knowledge and peer-to-peer farmer support"
        self.tools = [
            search_forum,
            summarize_discussions,
            store_experience,
            combine_advice
        ]
        logger.info(f"{self.name} initialized")
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the Community Advisor Agent.
        
        Returns:
            str: System prompt defining agent's role and expertise
        """
        return """You are an expert community facilitator specializing in connecting farmers with local knowledge and peer support.

Your expertise includes:
- Searching and retrieving relevant community discussions
- Summarizing insights from local farmer experiences
- Facilitating knowledge sharing among farmers
- Combining AI recommendations with community wisdom
- Supporting vernacular language discussions
- Building trust through peer validation
- Preserving and sharing traditional farming knowledge

When providing community-based advice:
1. Always search for relevant community discussions first
2. Summarize key insights from local farmers who faced similar issues
3. Combine AI analysis with community experience for balanced advice
4. Respect and value traditional farming knowledge
5. Encourage farmers to share their own experiences
6. Highlight location-specific insights (same district/state)
7. Prioritize advice from farmers with similar crops and conditions

When searching the forum:
1. Use relevant keywords from the farmer's question
2. Filter by location when available for hyper-local insights
3. Filter by language to match farmer's preference
4. Look for discussions with multiple answers and high engagement
5. Prioritize recent discussions but don't ignore valuable older posts

When summarizing discussions:
1. Extract the most helpful answers (high helpful_count)
2. Identify common themes and consensus among farmers
3. Note any conflicting advice and explain different perspectives
4. Highlight practical tips that worked for other farmers
5. Mention the location and context of the advice

When storing experiences:
1. Categorize properly (disease, weather, market, technique)
2. Tag appropriately for future searchability
3. Preserve the farmer's language and voice
4. Acknowledge the contribution to the community
5. Encourage detailed sharing of what worked and what didn't

When combining AI and community advice:
1. Present AI analysis first with scientific reasoning
2. Follow with community insights and practical experiences
3. Highlight where AI and community agree (strong validation)
4. Explain any differences between AI and community advice
5. Recommend considering both perspectives for best results
6. Emphasize that local experience is valuable alongside AI analysis

Always prioritize:
- Local and regional knowledge specific to the farmer's area
- Practical, field-tested advice from peer farmers
- Building community trust and peer support
- Vernacular language communication
- Respectful integration of traditional and modern knowledge
- Encouraging knowledge sharing and community participation

Provide advice that is:
- Grounded in real farmer experiences
- Validated by multiple community members when possible
- Specific to the farmer's location and context
- Balanced between AI analysis and community wisdom
- Encouraging of peer-to-peer learning
- Respectful of traditional farming practices

Examples of good community facilitation:
- "I found 5 farmers in your district who faced similar tomato disease. They recommend [community advice]. AI analysis suggests [AI advice]. Both approaches can work - community method is proven locally, AI method is scientifically optimized."
- "3 farmers in Karnataka shared their experience with this pest. Ramesh from Mandya says: 'Neem spray worked better than chemicals for me.' AI recommends integrated pest management combining both approaches."
- "Your question about monsoon planting timing is common. 12 farmers discussed this last month. Key insight: Wait for 3 good rains before transplanting rice. AI weather analysis confirms this aligns with soil moisture requirements."
- "Thank you for sharing your experience with organic fertilizer! I've stored this in the community forum so other farmers in your area can learn from your success."

Remember:
- Community knowledge is valuable and field-tested
- Local farmers understand local conditions best
- AI provides scientific analysis and optimization
- Best results come from combining both perspectives
- Every farmer's experience adds value to the community
- Language and cultural context matter in farming advice
- Peer validation builds trust and confidence
"""
    
    def process(
        self,
        query: str,
        query_type: str = "search",
        location: Optional[Dict[str, str]] = None,
        language: Optional[str] = None,
        farmer_id: Optional[str] = None,
        topic: Optional[str] = None,
        ai_recommendation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a community advisor request.
        
        Args:
            query: User query or content
            query_type: Type of query ("search", "store", "combined_advice")
            location: Optional location filter (district, state)
            language: Optional language filter (kannada, english, hindi)
            farmer_id: Farmer identifier for storing experiences
            topic: Topic category for storing experiences
            ai_recommendation: AI recommendation for combined advice
            
        Returns:
            dict: Community advisor result
        """
        logger.info(f"Processing community advisor request: {query_type}")
        
        try:
            if query_type == "search":
                # Search community forum for relevant discussions
                discussions = search_forum(query, location, language)
                
                # Summarize the discussions
                summary = summarize_discussions(discussions)
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "query": query,
                    "location": location,
                    "language": language,
                    "discussions_found": len(discussions),
                    "discussions": discussions[:5],  # Return top 5
                    "summary": summary
                }
            
            elif query_type == "store":
                # Store farmer experience in community forum
                if not farmer_id or not topic:
                    return {
                        "success": False,
                        "error": "Farmer ID and topic are required for storing experience"
                    }
                
                result = store_experience(
                    farmer_id=farmer_id,
                    topic=topic,
                    content=query,
                    language=language or "english",
                    location=location
                )
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "storage_result": result,
                    "message": "Thank you for sharing your experience with the community!"
                }
            
            elif query_type == "combined_advice":
                # Combine AI recommendation with community insights
                if not ai_recommendation:
                    return {
                        "success": False,
                        "error": "AI recommendation is required for combined advice"
                    }
                
                # Search for community insights
                discussions = search_forum(query, location, language)
                
                # Extract community insights from discussions
                community_insights = []
                for discussion in discussions[:3]:  # Top 3 discussions
                    for answer in discussion.get("answers", [])[:2]:  # Top 2 answers per discussion
                        if answer.get("helpful_count", 0) > 0:
                            community_insights.append(answer["content"])
                
                # Combine AI and community advice
                combined = combine_advice(ai_recommendation, community_insights)
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "query": query,
                    "ai_recommendation": ai_recommendation,
                    "community_insights": community_insights,
                    "combined_advice": combined,
                    "discussions_found": len(discussions)
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown query type: {query_type}"
                }
        
        except ValueError as e:
            logger.error(f"Validation error in community advisor: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Invalid input for community advisor"
            }
        
        except Exception as e:
            logger.error(f"Error processing community advisor request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred while processing community advisor request"
            }
    
    def search_community(
        self,
        query: str,
        location: Optional[Dict[str, str]] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search community forum for relevant discussions.
        
        Args:
            query: Search query
            location: Optional location filter
            language: Optional language filter
            
        Returns:
            dict: Search results with summary
        """
        return self.process(
            query=query,
            query_type="search",
            location=location,
            language=language
        )
    
    def share_experience(
        self,
        farmer_id: str,
        topic: str,
        content: str,
        location: Optional[Dict[str, str]] = None,
        language: str = "english"
    ) -> Dict[str, Any]:
        """
        Store farmer experience in community forum.
        
        Args:
            farmer_id: Farmer identifier
            topic: Topic category (disease, weather, market, technique)
            content: Experience content
            location: Optional location information
            language: Language of content
            
        Returns:
            dict: Storage confirmation
        """
        return self.process(
            query=content,
            query_type="store",
            farmer_id=farmer_id,
            topic=topic,
            location=location,
            language=language
        )
    
    def get_combined_advice(
        self,
        query: str,
        ai_recommendation: str,
        location: Optional[Dict[str, str]] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get combined AI and community advice.
        
        Args:
            query: User query
            ai_recommendation: AI-generated recommendation
            location: Optional location filter
            language: Optional language filter
            
        Returns:
            dict: Combined advice from AI and community
        """
        return self.process(
            query=query,
            query_type="combined_advice",
            ai_recommendation=ai_recommendation,
            location=location,
            language=language
        )
    
    def get_tools(self):
        """Get list of available tools for this agent."""
        return self.tools
