"""
Manager Agent for MissionAI Farmer Agent.

This agent serves as the central orchestrator that receives all user requests,
analyzes intent, routes to appropriate specialist agents, maintains conversation
context, and coordinates multi-agent workflows.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from pathlib import Path

from data_models import UserProfile, Location, Farm

logger = logging.getLogger(__name__)


# Onboarding roadmap templates by season
ONBOARDING_ROADMAPS = {
    "monsoon": {
        "season": "Monsoon (June-September)",
        "steps": [
            {
                "step": 1,
                "title": "Soil Preparation",
                "description": "Prepare your soil before monsoon planting",
                "tasks": [
                    "Test soil pH and nutrients",
                    "Add organic matter or compost",
                    "Ensure proper drainage",
                    "Level the field"
                ],
                "agents": ["soil_analysis"]
            },
            {
                "step": 2,
                "title": "Crop Selection",
                "description": "Choose suitable crops for monsoon season",
                "tasks": [
                    "Consider soil type and rainfall",
                    "Select disease-resistant varieties",
                    "Plan crop rotation",
                    "Calculate seed requirements"
                ],
                "agents": ["soil_analysis", "finance_calculator"]
            },
            {
                "step": 3,
                "title": "Planting",
                "description": "Plant at the right time with proper spacing",
                "tasks": [
                    "Wait for adequate soil moisture",
                    "Follow recommended spacing",
                    "Use quality seeds",
                    "Apply starter fertilizer"
                ],
                "agents": ["weather_advisor"]
            },
            {
                "step": 4,
                "title": "Crop Management",
                "description": "Monitor and care for your crops",
                "tasks": [
                    "Regular field inspection",
                    "Pest and disease monitoring",
                    "Timely weeding",
                    "Proper irrigation management"
                ],
                "agents": ["disease_diagnosis", "weather_advisor"]
            },
            {
                "step": 5,
                "title": "Harvest Planning",
                "description": "Prepare for harvest and marketing",
                "tasks": [
                    "Monitor crop maturity",
                    "Check market prices",
                    "Arrange harvest labor",
                    "Plan storage or immediate sale"
                ],
                "agents": ["market_price", "finance_calculator"]
            }
        ]
    },
    "winter": {
        "season": "Winter (October-February)",
        "steps": [
            {
                "step": 1,
                "title": "Post-Monsoon Soil Assessment",
                "description": "Assess soil condition after monsoon",
                "tasks": [
                    "Check soil moisture levels",
                    "Test nutrient status",
                    "Repair any erosion damage",
                    "Plan irrigation needs"
                ],
                "agents": ["soil_analysis"]
            },
            {
                "step": 2,
                "title": "Winter Crop Selection",
                "description": "Choose crops suitable for winter season",
                "tasks": [
                    "Select cold-tolerant varieties",
                    "Consider market demand",
                    "Plan for irrigation availability",
                    "Calculate input costs"
                ],
                "agents": ["soil_analysis", "market_price", "finance_calculator"]
            },
            {
                "step": 3,
                "title": "Planting and Care",
                "description": "Plant and manage winter crops",
                "tasks": [
                    "Plant at optimal time",
                    "Protect from frost if needed",
                    "Manage irrigation carefully",
                    "Monitor for pests"
                ],
                "agents": ["weather_advisor", "disease_diagnosis"]
            },
            {
                "step": 4,
                "title": "Harvest and Marketing",
                "description": "Harvest and sell your produce",
                "tasks": [
                    "Harvest at right maturity",
                    "Grade and sort produce",
                    "Find best market prices",
                    "Arrange transportation"
                ],
                "agents": ["market_price", "finance_calculator"]
            }
        ]
    },
    "summer": {
        "season": "Summer (March-May)",
        "steps": [
            {
                "step": 1,
                "title": "Soil Conservation",
                "description": "Protect soil during hot season",
                "tasks": [
                    "Apply mulch to retain moisture",
                    "Consider cover crops",
                    "Repair bunds and terraces",
                    "Plan water conservation"
                ],
                "agents": ["soil_analysis"]
            },
            {
                "step": 2,
                "title": "Summer Crop Planning",
                "description": "Select drought-tolerant crops",
                "tasks": [
                    "Choose water-efficient crops",
                    "Ensure irrigation availability",
                    "Consider short-duration varieties",
                    "Plan for heat stress management"
                ],
                "agents": ["soil_analysis", "weather_advisor", "finance_calculator"]
            },
            {
                "step": 3,
                "title": "Water Management",
                "description": "Efficient irrigation practices",
                "tasks": [
                    "Use drip or sprinkler irrigation",
                    "Irrigate during cooler hours",
                    "Monitor soil moisture",
                    "Prevent water wastage"
                ],
                "agents": ["weather_advisor"]
            },
            {
                "step": 4,
                "title": "Harvest and Storage",
                "description": "Harvest and store properly",
                "tasks": [
                    "Harvest early morning",
                    "Proper drying and storage",
                    "Check market prices",
                    "Plan for next season"
                ],
                "agents": ["market_price", "finance_calculator"]
            }
        ]
    }
}


# In-memory storage for user contexts (would use database in production)
USER_CONTEXTS = {}

# In-memory storage for conversation history
CONVERSATION_HISTORY = {}

# Storage directory for persistent data
STORAGE_DIR = Path("data/user_storage")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def detect_language(text: str) -> str:
    """
    Detect the language of input text.
    
    Args:
        text: Input text to analyze
        
    Returns:
        str: Detected language ('kannada', 'english', 'hindi')
    """
    # Simple keyword-based detection (would use proper NLP in production)
    # Kannada detection
    kannada_chars = set('ಅಆಇಈಉಊಋಎಏಐಒಓಔಕಖಗಘಙಚಛಜಝಞಟಠಡಢಣತಥದಧನಪಫಬಭಮಯರಲವಶಷಸಹಳೞ')
    # Hindi detection
    hindi_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
    
    text_chars = set(text)
    
    if text_chars & kannada_chars:
        return 'kannada'
    elif text_chars & hindi_chars:
        return 'hindi'
    else:
        return 'english'


def get_user_context(user_id: str) -> Dict[str, Any]:
    """
    Retrieve user profile and conversation history.
    Automatically restores from persistent storage if not in memory.
    
    Args:
        user_id: User identifier
        
    Returns:
        dict: User context including profile and history
    """
    # If not in memory, try to restore from disk
    if user_id not in USER_CONTEXTS:
        restore_session(user_id)
    
    # If still not in memory, create default context
    if user_id not in USER_CONTEXTS:
        USER_CONTEXTS[user_id] = {
            "user_id": user_id,
            "profile": None,
            "language_preference": "english",
            "onboarding_complete": False,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat()
        }
        CONVERSATION_HISTORY[user_id] = []
    
    # Update last active
    USER_CONTEXTS[user_id]["last_active"] = datetime.now().isoformat()
    
    # Get conversation history (last 10 interactions)
    history = CONVERSATION_HISTORY.get(user_id, [])[-10:]
    
    return {
        "user_context": USER_CONTEXTS[user_id],
        "conversation_history": history
    }


def save_user_context(user_id: str, context: Dict[str, Any]) -> bool:
    """
    Persist user profile and preferences to memory and disk.
    
    Args:
        user_id: User identifier
        context: User context to save
        
    Returns:
        bool: True if successful
    """
    try:
        # Update user context in memory
        if user_id not in USER_CONTEXTS:
            USER_CONTEXTS[user_id] = {}
        
        USER_CONTEXTS[user_id].update(context)
        USER_CONTEXTS[user_id]["last_active"] = datetime.now().isoformat()
        
        # Persist to disk
        save_user_profile_to_disk(user_id, USER_CONTEXTS[user_id])
        
        logger.info(f"User context saved for user: {user_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving user context: {str(e)}")
        return False


def load_user_profile_from_disk(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Load user profile from persistent storage.
    
    Args:
        user_id: User identifier
        
    Returns:
        dict: User profile or None if not found
    """
    profile_path = STORAGE_DIR / f"{user_id}_profile.json"
    
    if not profile_path.exists():
        return None
    
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        logger.info(f"Loaded user profile from disk: {user_id}")
        return profile_data
    except Exception as e:
        logger.error(f"Error loading user profile from disk: {str(e)}")
        return None


def save_user_profile_to_disk(user_id: str, profile: Dict[str, Any]) -> bool:
    """
    Save user profile to persistent storage.
    
    Args:
        user_id: User identifier
        profile: User profile data
        
    Returns:
        bool: True if successful
    """
    profile_path = STORAGE_DIR / f"{user_id}_profile.json"
    
    try:
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved user profile to disk: {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving user profile to disk: {str(e)}")
        return False


def load_conversation_history_from_disk(user_id: str) -> List[Dict[str, Any]]:
    """
    Load conversation history from persistent storage.
    
    Args:
        user_id: User identifier
        
    Returns:
        list: Conversation history or empty list
    """
    history_path = STORAGE_DIR / f"{user_id}_history.json"
    
    if not history_path.exists():
        return []
    
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
        logger.info(f"Loaded conversation history from disk: {user_id}")
        return history_data
    except Exception as e:
        logger.error(f"Error loading conversation history from disk: {str(e)}")
        return []


def save_conversation_history_to_disk(user_id: str, history: List[Dict[str, Any]]) -> bool:
    """
    Save conversation history to persistent storage.
    
    Args:
        user_id: User identifier
        history: Conversation history
        
    Returns:
        bool: True if successful
    """
    history_path = STORAGE_DIR / f"{user_id}_history.json"
    
    try:
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved conversation history to disk: {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving conversation history to disk: {str(e)}")
        return False


def restore_session(user_id: str) -> Dict[str, Any]:
    """
    Restore user session from persistent storage.
    
    Args:
        user_id: User identifier
        
    Returns:
        dict: Restored session data
    """
    # Load profile from disk
    profile = load_user_profile_from_disk(user_id)
    
    # Load conversation history from disk
    history = load_conversation_history_from_disk(user_id)
    
    # Restore to in-memory storage
    if profile:
        USER_CONTEXTS[user_id] = profile
    
    if history:
        CONVERSATION_HISTORY[user_id] = history
    
    logger.info(f"Session restored for user: {user_id}")
    
    return {
        "profile_restored": profile is not None,
        "history_restored": len(history) > 0,
        "history_turns": len(history)
    }


def persist_session(user_id: str) -> bool:
    """
    Persist current session to disk.
    
    Args:
        user_id: User identifier
        
    Returns:
        bool: True if successful
    """
    profile_saved = False
    history_saved = False
    
    # Save profile if exists
    if user_id in USER_CONTEXTS:
        profile_saved = save_user_profile_to_disk(user_id, USER_CONTEXTS[user_id])
    
    # Save conversation history if exists
    if user_id in CONVERSATION_HISTORY:
        history_saved = save_conversation_history_to_disk(user_id, CONVERSATION_HISTORY[user_id])
    
    logger.info(f"Session persisted for user: {user_id} (profile: {profile_saved}, history: {history_saved})")
    
    return profile_saved or history_saved


def delete_user_data(user_id: str) -> bool:
    """
    Delete all user data (memory and persistent storage).
    
    Args:
        user_id: User identifier
        
    Returns:
        bool: True if successful
    """
    try:
        # Remove from in-memory storage
        if user_id in USER_CONTEXTS:
            del USER_CONTEXTS[user_id]
        
        if user_id in CONVERSATION_HISTORY:
            del CONVERSATION_HISTORY[user_id]
        
        # Remove from disk
        profile_path = STORAGE_DIR / f"{user_id}_profile.json"
        history_path = STORAGE_DIR / f"{user_id}_history.json"
        
        if profile_path.exists():
            profile_path.unlink()
        
        if history_path.exists():
            history_path.unlink()
        
        logger.info(f"All data deleted for user: {user_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error deleting user data: {str(e)}")
        return False


def save_conversation_turn(user_id: str, user_message: str, agent_response: str, agent_name: str):
    """
    Save a conversation turn to history and persist to disk.
    
    Args:
        user_id: User identifier
        user_message: User's message
        agent_response: Agent's response
        agent_name: Name of the agent that responded
    """
    if user_id not in CONVERSATION_HISTORY:
        CONVERSATION_HISTORY[user_id] = []
    
    turn = {
        "timestamp": datetime.now().isoformat(),
        "user_message": user_message,
        "agent_response": agent_response,
        "agent_name": agent_name
    }
    
    CONVERSATION_HISTORY[user_id].append(turn)
    
    # Keep only last 20 turns
    if len(CONVERSATION_HISTORY[user_id]) > 20:
        CONVERSATION_HISTORY[user_id] = CONVERSATION_HISTORY[user_id][-20:]
    
    # Persist to disk
    save_conversation_history_to_disk(user_id, CONVERSATION_HISTORY[user_id])


def route_to_agent(intent: str, context: Dict[str, Any]) -> str:
    """
    Determine which specialist agent should handle the request.
    
    Args:
        intent: Analyzed user intent
        context: User context and conversation history
        
    Returns:
        str: Target agent name
    """
    intent_lower = intent.lower()
    
    # Disease diagnosis keywords
    disease_keywords = [
        'disease', 'pest', 'spots', 'wilting', 'yellowing', 'infected',
        'fungus', 'insect', 'damage', 'leaves', 'dying', 'sick', 'problem with crop',
        'crop health', 'plant disease', 'bug', 'worm', 'caterpillar'
    ]
    
    # Soil analysis keywords
    soil_keywords = [
        'soil', 'fertility', 'nutrients', 'ph', 'soil type', 'soil health',
        'soil test', 'which crop', 'crop recommendation', 'what to plant',
        'soil improvement', 'compost', 'manure'
    ]
    
    # Weather keywords
    weather_keywords = [
        'weather', 'rain', 'forecast', 'temperature', 'humidity', 'wind',
        'when to spray', 'when to plant', 'when to harvest', 'timing',
        'monsoon', 'drought', 'storm', 'climate'
    ]
    
    # Market keywords
    market_keywords = [
        'price', 'market', 'sell', 'buy', 'listing', 'buyer', 'seller',
        'mandi', 'rate', 'cost of', 'selling price', 'purchase', 'marketplace',
        'expiry', 'quality grade'
    ]
    
    # Scheme keywords
    scheme_keywords = [
        'scheme', 'subsidy', 'government', 'loan', 'insurance', 'pm-kisan',
        'eligibility', 'benefit', 'application', 'yojana', 'support',
        'financial aid', 'grant'
    ]
    
    # Finance keywords
    finance_keywords = [
        'profit', 'loss', 'calculate', 'cost', 'expense', 'income', 'roi',
        'return', 'investment', 'budget', 'financial', 'money', 'earnings',
        'compare crops', 'which crop profitable'
    ]
    
    # Community keywords
    community_keywords = [
        'community', 'forum', 'other farmers', 'local farmers', 'experience',
        'advice from farmers', 'what others say', 'peer', 'neighbor',
        'share experience', 'ask farmers'
    ]
    
    # Count keyword matches for each agent
    scores = {
        'disease_diagnosis': sum(1 for kw in disease_keywords if kw in intent_lower),
        'soil_analysis': sum(1 for kw in soil_keywords if kw in intent_lower),
        'weather_advisor': sum(1 for kw in weather_keywords if kw in intent_lower),
        'market_price': sum(1 for kw in market_keywords if kw in intent_lower),
        'schemes_navigator': sum(1 for kw in scheme_keywords if kw in intent_lower),
        'finance_calculator': sum(1 for kw in finance_keywords if kw in intent_lower),
        'community_advisor': sum(1 for kw in community_keywords if kw in intent_lower)
    }
    
    # Get agent with highest score
    max_score = max(scores.values())
    
    if max_score == 0:
        # No clear match, return manager for clarification
        return 'manager'
    
    # Check for ambiguity (multiple agents with same high score)
    top_agents = [agent for agent, score in scores.items() if score == max_score]
    
    if len(top_agents) > 1:
        # Ambiguous intent
        return 'ambiguous'
    
    return top_agents[0]


class ManagerAgent:
    """
    Central orchestrator agent for the MissionAI system.
    
    This agent receives all user requests, analyzes intent, routes to
    appropriate specialist agents, maintains conversation context,
    and coordinates multi-agent workflows.
    """
    
    def __init__(self, specialist_agents: Optional[Dict[str, Any]] = None):
        """
        Initialize the Manager Agent.
        
        Args:
            specialist_agents: Optional dict of specialist agent instances
        """
        self.name = "Manager Agent"
        self.description = "Central orchestrator for intent analysis and agent routing"
        self.tools = [
            detect_language,
            get_user_context,
            save_user_context,
            route_to_agent
        ]
        
        # Initialize specialist agents
        if specialist_agents:
            self.specialist_agents = specialist_agents
        else:
            # Default agent names (would be actual agent instances in production)
            self.specialist_agents = {
                'disease_diagnosis': None,
                'soil_analysis': None,
                'weather_advisor': None,
                'market_price': None,
                'schemes_navigator': None,
                'finance_calculator': None,
                'community_advisor': None
            }
        
        logger.info(f"{self.name} initialized with {len(self.specialist_agents)} specialist agents")
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the Manager Agent.
        
        Returns:
            str: System prompt defining agent's role and expertise
        """
        return """You are the Manager Agent for MissionAI, a voice-first AI assistant for rural Indian farmers.

Your role is to:
1. Understand farmer requests in Kannada, English, or Hindi
2. Analyze intent and determine which specialist agent can best help
3. Route requests to the appropriate specialist agent
4. Maintain conversation context across interactions
5. Coordinate multi-agent workflows when needed
6. Handle ambiguous requests by asking clarifying questions
7. Provide a seamless, conversational experience

Available Specialist Agents:
- Disease Diagnosis Agent: Crop disease identification from images, treatment recommendations
- Soil Analysis Agent: Soil classification, fertility assessment, crop recommendations
- Weather Advisor Agent: Weather forecasts, farming activity timing, proactive alerts
- Market Price Agent: Real-time market prices, produce listings, expiry tracking
- Schemes Navigator Agent: Government schemes, eligibility checking, application guidance
- Finance Calculator Agent: Profit/loss calculations, cost estimation, crop comparisons
- Community Advisor Agent: Local farmer forum, community knowledge, peer support

Intent Analysis Guidelines:
1. Look for keywords that indicate which specialist is needed
2. Consider the context from previous conversation turns
3. If multiple agents could help, ask clarifying questions
4. If no specialist matches, provide general guidance or suggest alternatives

Routing Rules:
- Disease/pest/crop health issues → Disease Diagnosis Agent
- Soil/fertility/crop recommendations → Soil Analysis Agent
- Weather/timing/forecasts → Weather Advisor Agent
- Prices/market/buying/selling → Market Price Agent
- Government schemes/subsidies/loans → Schemes Navigator Agent
- Costs/profits/financial planning → Finance Calculator Agent
- Community questions/local knowledge → Community Advisor Agent

When handling ambiguous requests:
1. Identify the 2-3 most likely interpretations
2. Ask: "Are you asking about [Option A] or [Option B]?"
3. Provide clear, simple choices
4. Wait for clarification before routing

Context Management:
1. Remember user's language preference
2. Track user's farm details (location, crops, size)
3. Reference previous interactions when relevant
4. Maintain conversation flow across agent handoffs

Language Handling:
1. Detect input language automatically
2. Respond in the same language as input
3. Store language preference for future interactions
4. Support code-mixing (e.g., English + Kannada)

Error Handling:
1. If a specialist agent fails, apologize and offer alternatives
2. If request is unclear, ask for more details
3. If outside system capabilities, acknowledge limitations honestly
4. Always maintain a helpful, supportive tone

Conversation Style:
- Warm and friendly, like a knowledgeable neighbor
- Use simple language appropriate for rural farmers
- Be patient and encouraging
- Avoid technical jargon unless necessary
- Provide actionable, practical advice
- Show empathy for farming challenges

Examples of Good Routing:
- "My tomato plants have brown spots" → Disease Diagnosis Agent
- "What should I plant in my clay soil?" → Soil Analysis Agent
- "When should I spray pesticide?" → Weather Advisor Agent
- "What is the price of rice today?" → Market Price Agent
- "Am I eligible for PM-KISAN?" → Schemes Navigator Agent
- "How much profit will I make from cotton?" → Finance Calculator Agent
- "What do other farmers say about this fertilizer?" → Community Advisor Agent

Examples of Ambiguity Handling:
- "Tell me about cotton" → Ask: "Are you asking about cotton prices, cotton diseases, or cotton profitability?"
- "I need help with my farm" → Ask: "What specific help do you need? Crop health, weather advice, market prices, or something else?"
- "What should I do now?" → Ask: "Can you tell me more about what you're working on? Are you planting, treating a disease, or planning to sell?"

Remember:
- You are the farmer's trusted guide through the AI system
- Your goal is to connect them with the right specialist quickly
- Maintain context so farmers don't repeat themselves
- Be proactive in offering relevant information
- Always prioritize the farmer's success and wellbeing
"""
    
    def process(
        self,
        user_message: str,
        user_id: str,
        language: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user request and route to appropriate agent.
        
        Args:
            user_message: User's message or query
            user_id: User identifier
            language: Optional language override
            image_url: Optional image URL for multimodal requests
            
        Returns:
            dict: Routing decision and context
        """
        logger.info(f"Processing request from user: {user_id}")
        
        try:
            # Detect language if not provided
            if not language:
                language = detect_language(user_message)
            
            # Get user context
            context = get_user_context(user_id)
            
            # Update language preference
            if language:
                context["user_context"]["language_preference"] = language
                save_user_context(user_id, {"language_preference": language})
            
            # Analyze intent and route
            target_agent = route_to_agent(user_message, context)
            
            # Handle ambiguous routing
            if target_agent == 'ambiguous':
                return {
                    "success": True,
                    "action": "clarify",
                    "message": "I can help you with multiple things. Could you please clarify what you need?",
                    "language": language,
                    "user_id": user_id
                }
            
            # Handle no clear routing
            if target_agent == 'manager':
                return {
                    "success": True,
                    "action": "general_response",
                    "message": "I'm here to help! I can assist with crop diseases, soil analysis, weather advice, market prices, government schemes, financial planning, and community knowledge. What would you like to know?",
                    "language": language,
                    "user_id": user_id
                }
            
            # Route to specialist agent
            specialist = self.specialist_agents.get(target_agent)
            
            if specialist is None:
                # Agent not initialized, return routing info
                return {
                    "success": True,
                    "action": "route",
                    "target_agent": target_agent,
                    "language": language,
                    "user_id": user_id,
                    "context": context,
                    "image_url": image_url,
                    "message": f"Routing to {target_agent.replace('_', ' ').title()} Agent"
                }
            
            # Perform handoff to specialist
            handoff_result = self.handoff_to_specialist(
                target_agent=target_agent,
                user_message=user_message,
                context=context,
                image_url=image_url
            )
            
            if not handoff_result.get("success"):
                # Handle handoff error
                return self.handle_handoff_error(
                    target_agent=target_agent,
                    error=handoff_result.get("error", "Unknown error"),
                    user_id=user_id,
                    language=language
                )
            
            # Save conversation turn
            save_conversation_turn(
                user_id=user_id,
                user_message=user_message,
                agent_response=str(handoff_result),
                agent_name=self.name
            )
            
            return handoff_result
        
        except Exception as e:
            logger.error(f"Error processing manager request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred while processing your request. Please try again.",
                "language": language or "english",
                "user_id": user_id
            }
    
    def get_tools(self):
        """Get list of available tools for this agent."""
        return self.tools
    
    def get_personalized_recommendations(
        self,
        user_id: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Generate personalized recommendations based on user profile and history.
        
        Args:
            user_id: User identifier
            query: User query
            
        Returns:
            dict: Personalized recommendations
        """
        context = get_user_context(user_id)
        user_context = context.get("user_context", {})
        profile = user_context.get("profile")
        history = context.get("conversation_history", [])
        
        recommendations = {
            "user_id": user_id,
            "query": query,
            "personalized": False,
            "recommendations": []
        }
        
        # If no profile, return generic recommendations
        if not profile:
            recommendations["recommendations"].append(
                "Complete your profile to get personalized recommendations"
            )
            return recommendations
        
        recommendations["personalized"] = True
        
        # Add recommendations based on profile
        if "location" in profile:
            location = profile["location"]
            recommendations["recommendations"].append(
                f"Based on your location in {location.get('district', 'your area')}, "
                f"I can provide hyper-local advice"
            )
        
        if "crops" in profile:
            crops = profile["crops"]
            recommendations["recommendations"].append(
                f"I see you grow {', '.join(crops)}. I can help with specific advice for these crops"
            )
        
        # Add recommendations based on history
        if len(history) > 0:
            recent_topics = set()
            for turn in history[-5:]:
                agent_name = turn.get("agent_name", "")
                if "Disease" in agent_name:
                    recent_topics.add("crop health")
                elif "Market" in agent_name:
                    recent_topics.add("market prices")
                elif "Weather" in agent_name:
                    recent_topics.add("weather")
            
            if recent_topics:
                recommendations["recommendations"].append(
                    f"Based on your recent questions about {', '.join(recent_topics)}, "
                    f"I can provide follow-up advice"
                )
        
        return recommendations
    
    def clear_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Delete all user data for privacy compliance.
        
        Args:
            user_id: User identifier
            
        Returns:
            dict: Deletion confirmation
        """
        success = delete_user_data(user_id)
        
        return {
            "success": success,
            "user_id": user_id,
            "message": "All your data has been deleted" if success else "Error deleting data"
        }
    
    def save_session(self, user_id: str) -> Dict[str, Any]:
        """
        Manually save current session to persistent storage.
        
        Args:
            user_id: User identifier
            
        Returns:
            dict: Save confirmation
        """
        success = persist_session(user_id)
        
        return {
            "success": success,
            "user_id": user_id,
            "message": "Session saved successfully" if success else "Error saving session"
        }
    
    def restore_user_session(self, user_id: str) -> Dict[str, Any]:
        """
        Manually restore user session from persistent storage.
        
        Args:
            user_id: User identifier
            
        Returns:
            dict: Restoration status
        """
        result = restore_session(user_id)
        
        return {
            "success": result["profile_restored"] or result["history_restored"],
            "user_id": user_id,
            "profile_restored": result["profile_restored"],
            "history_restored": result["history_restored"],
            "history_turns": result["history_turns"],
            "message": "Session restored successfully" if result["profile_restored"] or result["history_restored"] else "No saved session found"
        }
    
    def is_new_farmer(self, user_id: str) -> bool:
        """
        Determine if a farmer is new to the system.
        
        Args:
            user_id: User identifier
            
        Returns:
            bool: True if new farmer
        """
        context = get_user_context(user_id)
        user_context = context.get("user_context", {})
        
        # New farmer if onboarding not complete and no profile
        return (
            not user_context.get("onboarding_complete", False) and
            user_context.get("profile") is None
        )
    
    def get_current_season(self) -> str:
        """
        Determine current farming season based on month.
        
        Returns:
            str: Season name ('monsoon', 'winter', 'summer')
        """
        current_month = datetime.now().month
        
        # Monsoon: June-September (6-9)
        if 6 <= current_month <= 9:
            return "monsoon"
        # Winter: October-February (10-12, 1-2)
        elif current_month >= 10 or current_month <= 2:
            return "winter"
        # Summer: March-May (3-5)
        else:
            return "summer"
    
    def get_onboarding_roadmap(
        self,
        user_id: str,
        season: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get personalized onboarding roadmap for a new farmer.
        
        Args:
            user_id: User identifier
            season: Optional season override (defaults to current season)
            
        Returns:
            dict: Onboarding roadmap with steps
        """
        if season is None:
            season = self.get_current_season()
        
        roadmap = ONBOARDING_ROADMAPS.get(season, ONBOARDING_ROADMAPS["monsoon"])
        
        context = get_user_context(user_id)
        user_context = context.get("user_context", {})
        profile = user_context.get("profile", {})
        
        # Customize roadmap based on profile if available
        customized_roadmap = {
            "user_id": user_id,
            "season": roadmap["season"],
            "steps": roadmap["steps"].copy(),
            "current_step": user_context.get("onboarding_step", 1),
            "total_steps": len(roadmap["steps"]),
            "personalized": False
        }
        
        # Add personalization if profile exists
        if profile:
            customized_roadmap["personalized"] = True
            if "location" in profile:
                customized_roadmap["location"] = profile["location"]
            if "crops" in profile:
                customized_roadmap["preferred_crops"] = profile["crops"]
        
        return customized_roadmap
    
    def update_onboarding_progress(
        self,
        user_id: str,
        step: int,
        completed: bool = True
    ) -> Dict[str, Any]:
        """
        Update farmer's onboarding progress.
        
        Args:
            user_id: User identifier
            step: Step number completed
            completed: Whether step is completed
            
        Returns:
            dict: Updated progress status
        """
        context = get_user_context(user_id)
        user_context = context.get("user_context", {})
        
        # Update onboarding step
        current_step = user_context.get("onboarding_step", 1)
        
        if completed and step >= current_step:
            new_step = step + 1
            user_context["onboarding_step"] = new_step
            
            # Get total steps for current season
            season = self.get_current_season()
            roadmap = ONBOARDING_ROADMAPS.get(season, ONBOARDING_ROADMAPS["monsoon"])
            total_steps = len(roadmap["steps"])
            
            # Mark onboarding complete if all steps done
            if new_step > total_steps:
                user_context["onboarding_complete"] = True
                save_user_context(user_id, user_context)
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "onboarding_complete": True,
                    "message": "Congratulations! You've completed the onboarding roadmap."
                }
            
            save_user_context(user_id, user_context)
            
            return {
                "success": True,
                "user_id": user_id,
                "current_step": new_step,
                "total_steps": total_steps,
                "onboarding_complete": False,
                "message": f"Step {step} completed! Moving to step {new_step}."
            }
        
        return {
            "success": False,
            "user_id": user_id,
            "message": "Step not updated"
        }
    
    def start_onboarding(self, user_id: str) -> Dict[str, Any]:
        """
        Start onboarding process for a new farmer.
        
        Args:
            user_id: User identifier
            
        Returns:
            dict: Onboarding start confirmation with first steps
        """
        # Initialize onboarding
        context = get_user_context(user_id)
        user_context = context.get("user_context", {})
        
        user_context["onboarding_step"] = 1
        user_context["onboarding_complete"] = False
        user_context["onboarding_started_at"] = datetime.now().isoformat()
        
        save_user_context(user_id, user_context)
        
        # Get roadmap
        roadmap = self.get_onboarding_roadmap(user_id)
        
        # Get first step
        first_step = roadmap["steps"][0] if roadmap["steps"] else None
        
        return {
            "success": True,
            "user_id": user_id,
            "message": f"Welcome! Let's get you started with farming for {roadmap['season']}.",
            "season": roadmap["season"],
            "total_steps": roadmap["total_steps"],
            "first_step": first_step,
            "roadmap": roadmap
        }
    
    def get_onboarding_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get current onboarding status for a farmer.
        
        Args:
            user_id: User identifier
            
        Returns:
            dict: Onboarding status
        """
        context = get_user_context(user_id)
        user_context = context.get("user_context", {})
        
        is_complete = user_context.get("onboarding_complete", False)
        current_step = user_context.get("onboarding_step", 1)
        
        if is_complete:
            return {
                "user_id": user_id,
                "onboarding_complete": True,
                "message": "Onboarding completed"
            }
        
        # Get current roadmap
        roadmap = self.get_onboarding_roadmap(user_id)
        
        # Get current step details
        current_step_details = None
        if 0 < current_step <= len(roadmap["steps"]):
            current_step_details = roadmap["steps"][current_step - 1]
        
        return {
            "user_id": user_id,
            "onboarding_complete": False,
            "current_step": current_step,
            "total_steps": roadmap["total_steps"],
            "season": roadmap["season"],
            "current_step_details": current_step_details,
            "progress_percentage": (current_step - 1) / roadmap["total_steps"] * 100
        }
    
    def handoff_to_specialist(
        self,
        target_agent: str,
        user_message: str,
        context: Dict[str, Any],
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Hand off request to a specialist agent with context.
        
        Args:
            target_agent: Target specialist agent key
            user_message: User's message
            context: User context to pass to specialist
            image_url: Optional image URL for multimodal requests
            
        Returns:
            dict: Specialist agent response
        """
        try:
            specialist = self.specialist_agents.get(target_agent)
            
            if not specialist:
                return {
                    "success": False,
                    "error": f"Specialist agent '{target_agent}' not found",
                    "message": "I'm having trouble connecting to the right specialist. Please try again."
                }
            
            # Extract relevant context for the specialist
            user_context = context.get("user_context", {})
            language = user_context.get("language_preference", "english")
            
            # Prepare handoff context
            handoff_context = {
                "user_id": user_context.get("user_id"),
                "language": language,
                "user_profile": user_context.get("profile"),
                "conversation_history": context.get("conversation_history", [])[-3:],  # Last 3 turns
                "image_url": image_url
            }
            
            logger.info(f"Handing off to {target_agent} with context")
            
            # Call specialist agent's process method
            # In production, this would invoke the actual agent
            # For now, we return the handoff information
            
            return {
                "success": True,
                "action": "handoff_complete",
                "target_agent": target_agent,
                "specialist": specialist,
                "handoff_context": handoff_context,
                "user_message": user_message
            }
        
        except Exception as e:
            logger.error(f"Error during handoff to {target_agent}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred while connecting to the specialist. Please try again."
            }
    
    def handle_multi_agent_workflow(
        self,
        workflow_steps: List[Dict[str, Any]],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Coordinate a multi-agent workflow with multiple handoffs.
        
        Args:
            workflow_steps: List of workflow steps with agent and parameters
            user_id: User identifier
            
        Returns:
            dict: Workflow execution results
        """
        try:
            results = []
            context = get_user_context(user_id)
            
            for step in workflow_steps:
                target_agent = step.get("agent")
                message = step.get("message")
                image_url = step.get("image_url")
                
                # Execute handoff
                result = self.handoff_to_specialist(
                    target_agent=target_agent,
                    user_message=message,
                    context=context,
                    image_url=image_url
                )
                
                if not result.get("success"):
                    # Workflow failed at this step
                    return {
                        "success": False,
                        "failed_at_step": len(results),
                        "error": result.get("error"),
                        "partial_results": results
                    }
                
                results.append(result)
                
                # Update context with result for next step
                save_conversation_turn(
                    user_id=user_id,
                    user_message=message,
                    agent_response=str(result),
                    agent_name=target_agent
                )
                
                # Refresh context
                context = get_user_context(user_id)
            
            return {
                "success": True,
                "workflow_complete": True,
                "steps_executed": len(results),
                "results": results
            }
        
        except Exception as e:
            logger.error(f"Error in multi-agent workflow: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred during the workflow execution."
            }
    
    def handle_handoff_error(
        self,
        target_agent: str,
        error: str,
        user_id: str,
        language: str = "english"
    ) -> Dict[str, Any]:
        """
        Handle errors during agent handoff gracefully.
        
        Args:
            target_agent: Agent that failed
            error: Error message
            user_id: User identifier
            language: User's language preference
            
        Returns:
            dict: Error handling response with alternatives
        """
        logger.error(f"Handoff error to {target_agent}: {error}")
        
        # Determine alternative agents or actions
        alternatives = []
        
        if target_agent == 'disease_diagnosis':
            alternatives = [
                "Try uploading a clearer image",
                "Describe the symptoms in detail",
                "Check the community forum for similar issues"
            ]
        elif target_agent == 'weather_advisor':
            alternatives = [
                "Try again in a few moments",
                "Check local weather sources",
                "Ask the community about current conditions"
            ]
        elif target_agent == 'market_price':
            alternatives = [
                "Try again shortly",
                "Check local mandi prices",
                "Ask other farmers about recent prices"
            ]
        else:
            alternatives = [
                "Try rephrasing your question",
                "Try again in a few moments",
                "Ask the community for advice"
            ]
        
        # Prepare error response
        error_messages = {
            "english": f"I'm having trouble connecting to the {target_agent.replace('_', ' ')} specialist right now. Here are some alternatives:",
            "kannada": f"{target_agent.replace('_', ' ')} ವಿಶೇಷಜ್ಞರೊಂದಿಗೆ ಸಂಪರ್ಕ ಸಾಧಿಸಲು ನನಗೆ ತೊಂದರೆಯಾಗುತ್ತಿದೆ. ಇಲ್ಲಿ ಕೆಲವು ಪರ್ಯಾಯಗಳಿವೆ:",
            "hindi": f"मुझे अभी {target_agent.replace('_', ' ')} विशेषज्ञ से जुड़ने में परेशानी हो रही है। यहां कुछ विकल्प हैं:"
        }
        
        return {
            "success": False,
            "action": "error_handled",
            "error": error,
            "message": error_messages.get(language, error_messages["english"]),
            "alternatives": alternatives,
            "user_id": user_id,
            "language": language
        }
