"""
RISE Orchestrator Agent
Main agent that coordinates all specialist agents
"""

from strands import Agent
from config import Config
import boto3
from typing import Optional

class RISEOrchestrator:
    """
    Main orchestrator agent for RISE platform
    Coordinates specialist agents and manages conversation flow
    """
    
    def __init__(self):
        """Initialize the orchestrator agent"""
        self.config = Config()
        self.bedrock_client = None
        self.agent = None
        
        # Initialize AWS clients
        self._init_aws_clients()
        
        # Initialize Strands agent
        self._init_agent()
    
    def _init_aws_clients(self):
        """Initialize AWS service clients"""
        try:
            self.bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=self.config.BEDROCK_REGION,
                aws_access_key_id=self.config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.config.AWS_SECRET_ACCESS_KEY
            )
        except Exception as e:
            print(f"Warning: Could not initialize AWS clients: {e}")
    
    def _init_agent(self):
        """Initialize Strands agent with system prompt"""
        
        system_prompt = """You are RISE (Rural Innovation and Sustainable Ecosystem), 
        an AI-powered farming assistant designed to help smallholder farmers in India.
        
        Your capabilities include:
        - Providing agricultural advice in multiple Indian languages
        - Diagnosing crop diseases and pest issues from images
        - Analyzing soil conditions and recommending fertilizers
        - Offering weather-based farming recommendations
        - Providing market price information and connecting farmers with buyers
        - Helping farmers discover and apply for government schemes
        - Assisting with financial planning and profitability calculations
        - Facilitating community resource sharing and cooperative buying
        
        You communicate in a friendly, supportive manner and always prioritize:
        1. Practical, actionable advice
        2. Sustainable farming practices
        3. Cost-effective solutions
        4. Safety and environmental considerations
        
        When you don't have enough information, ask clarifying questions.
        Always be respectful of the farmer's experience and local knowledge.
        """
        
        try:
            # Initialize Strands Agent
            # Note: Full implementation will be completed in subsequent phases
            self.agent = Agent(
                name="RISE-Orchestrator",
                description="Main farming assistant orchestrator",
                system_prompt=system_prompt,
                # Model configuration will be added when AWS is configured
            )
        except Exception as e:
            print(f"Warning: Could not initialize Strands agent: {e}")
            self.agent = None
    
    def process_query(self, query: str, language: str = "en") -> str:
        """
        Process a user query and return a response
        
        Args:
            query: User's question or request
            language: Language code (en, hi, ta, etc.)
        
        Returns:
            Response string
        """
        if not self.agent:
            return "Agent not initialized. Please configure AWS credentials."
        
        # TODO: Implement full query processing with Strands agent
        # This will be completed in Phase 2-3
        
        return f"Query received: {query} (Language: {language})"
    
    def process_voice_query(self, audio_data: bytes, language: str = "en") -> dict:
        """
        Process voice input and return response
        
        Args:
            audio_data: Audio bytes from user
            language: Detected or preferred language
        
        Returns:
            Dict with text response and audio response
        """
        # TODO: Implement voice processing with Amazon Transcribe
        # This will be completed in Phase 2
        
        return {
            "text": "Voice processing not yet implemented",
            "audio": None
        }
    
    def analyze_image(self, image_data: bytes, analysis_type: str) -> dict:
        """
        Analyze crop/soil images using Amazon Bedrock
        
        Args:
            image_data: Image bytes
            analysis_type: Type of analysis (disease, pest, soil)
        
        Returns:
            Analysis results
        """
        # TODO: Implement image analysis with Bedrock multimodal
        # This will be completed in Phase 3
        
        return {
            "analysis_type": analysis_type,
            "result": "Image analysis not yet implemented"
        }
    
    def get_status(self) -> dict:
        """Get orchestrator status"""
        return {
            "agent_initialized": self.agent is not None,
            "aws_configured": self.bedrock_client is not None,
            "model_id": self.config.BEDROCK_MODEL_ID,
            "region": self.config.AWS_REGION
        }

# Global orchestrator instance
_orchestrator: Optional[RISEOrchestrator] = None

def get_orchestrator() -> RISEOrchestrator:
    """Get or create the global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = RISEOrchestrator()
    return _orchestrator
