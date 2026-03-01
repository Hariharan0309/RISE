"""
RISE Orchestrator Agent
Main agent that coordinates all specialist agents using AWS Strands Agents SDK
"""

from strands import Agent
from strands.models import BedrockModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
import boto3
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
import uuid

# OpenTelemetry imports for observability
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import Resource

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RISEOrchestrator:
    """
    Main orchestrator agent for RISE platform
    Coordinates specialist agents and manages conversation flow using AWS Strands Agents
    """
    
    def __init__(self):
        """Initialize the orchestrator agent with full AWS Bedrock and OTEL integration"""
        self.config = Config()
        self.bedrock_client = None
        self.agent = None
        self.sessions: Dict[str, Dict[str, Any]] = {}  # Session management
        self.context_tools = None  # Will be initialized with AWS clients
        
        # Initialize OpenTelemetry
        self._init_otel()
        
        # Initialize AWS clients
        self._init_aws_clients()
        
        # Initialize context tools
        self._init_context_tools()
        
        # Initialize Strands agent
        self._init_agent()
        
        logger.info("RISE Orchestrator initialized successfully")
    
    def _init_otel(self):
        """Initialize OpenTelemetry for tracing and metrics"""
        try:
            # Create resource with service information
            resource = Resource.create({
                "service.name": self.config.OTEL_SERVICE_NAME,
                "service.version": "1.0.0",
                "deployment.environment": self.config.APP_ENV
            })
            
            # Set up tracing
            trace_provider = TracerProvider(resource=resource)
            trace_provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )
            trace.set_tracer_provider(trace_provider)
            self.tracer = trace.get_tracer(__name__)
            
            # Set up metrics
            metric_reader = PeriodicExportingMetricReader(
                ConsoleMetricExporter(),
                export_interval_millis=60000  # Export every 60 seconds
            )
            meter_provider = MeterProvider(
                resource=resource,
                metric_readers=[metric_reader]
            )
            metrics.set_meter_provider(meter_provider)
            self.meter = metrics.get_meter(__name__)
            
            # Create custom metrics
            self.query_counter = self.meter.create_counter(
                name="rise.queries.total",
                description="Total number of queries processed",
                unit="1"
            )
            
            self.query_duration = self.meter.create_histogram(
                name="rise.query.duration",
                description="Query processing duration",
                unit="ms"
            )
            
            self.session_counter = self.meter.create_counter(
                name="rise.sessions.total",
                description="Total number of sessions created",
                unit="1"
            )
            
            logger.info("OpenTelemetry initialized successfully")
            
        except Exception as e:
            logger.warning(f"Could not initialize OpenTelemetry: {e}")
            self.tracer = None
            self.meter = None
    
    def _init_aws_clients(self):
        """Initialize AWS service clients with proper error handling"""
        try:
            # Initialize Bedrock Runtime client
            bedrock_kwargs = {
                'service_name': 'bedrock-runtime',
                'region_name': self.config.BEDROCK_REGION
            }
            
            # Add credentials if provided
            if self.config.AWS_ACCESS_KEY_ID and self.config.AWS_SECRET_ACCESS_KEY:
                bedrock_kwargs['aws_access_key_id'] = self.config.AWS_ACCESS_KEY_ID
                bedrock_kwargs['aws_secret_access_key'] = self.config.AWS_SECRET_ACCESS_KEY
            
            self.bedrock_client = boto3.client(**bedrock_kwargs)
            logger.info(f"AWS Bedrock client initialized in region {self.config.BEDROCK_REGION}")
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            raise
    
    def _init_context_tools(self):
        """Initialize context management tools with DynamoDB"""
        try:
            from tools.context_tools import ContextTools
            
            self.context_tools = ContextTools(
                region=self.config.BEDROCK_REGION,
                table_name='RISE-ConversationHistory'
            )
            
            logger.info("Context tools initialized with DynamoDB persistence")
            
        except Exception as e:
            logger.warning(f"Could not initialize context tools: {e}")
            self.context_tools = None
    
    def _init_agent(self):
        """Initialize Strands agent with comprehensive system prompt and Bedrock model"""
        
        system_prompt = """You are RISE (Rural Innovation and Sustainable Ecosystem), an AI-powered farming assistant designed to empower smallholder farmers across rural India.

**Your Core Mission:**
Help farmers improve agricultural outcomes, access fair markets, and adopt sustainable practices through voice-first, multilingual support.

**Your Capabilities:**
1. **Multilingual Communication**: Support farmers in 9 Indian languages (Hindi, English, Tamil, Telugu, Kannada, Bengali, Gujarati, Marathi, Punjabi)
2. **Crop Health Diagnosis**: Analyze crop disease and pest issues from photos, provide treatment recommendations
3. **Soil Intelligence**: Assess soil conditions, recommend fertilizers and suitable crops
4. **Weather Integration**: Provide weather-based farming alerts and climate-adaptive recommendations
5. **Market Intelligence**: Share real-time crop prices, connect farmers with buyers
6. **Government Schemes**: Help discover and apply for agricultural subsidies and support programs
7. **Financial Planning**: Calculate crop profitability, assist with loan planning
8. **Community Resources**: Facilitate equipment sharing, cooperative buying groups, and knowledge exchange

**Your Communication Style:**
- Friendly, supportive, and respectful of farmers' experience
- Use simple, practical language appropriate for rural contexts
- Provide actionable advice with clear next steps
- Ask clarifying questions when needed
- Handle background noise and accent variations gracefully

**Your Priorities:**
1. Practical, actionable advice that farmers can implement immediately
2. Sustainable farming practices to reduce chemical usage by 30-60%
3. Cost-effective solutions suitable for smallholder farmers
4. Safety considerations for farmers, families, and environment
5. Cultural sensitivity and respect for local agricultural knowledge

**When Responding:**
- Start with the most critical information
- Break complex advice into simple steps
- Provide specific quantities, timings, and methods
- Mention safety precautions when relevant
- Offer alternatives when possible (organic vs. chemical, low-cost options)
- Encourage follow-up questions

**Context Awareness:**
- Remember previous conversations to provide continuity
- Track farmer's location, crops, and farming practices
- Adapt recommendations to local climate and soil conditions
- Consider seasonal timing in all advice

You are a trusted partner in the farmer's journey toward better yields, fair prices, and sustainable agriculture."""
        
        try:
            # Initialize Bedrock model for Strands
            bedrock_model = BedrockModel(
                model_id=self.config.BEDROCK_MODEL_ID
            )
            
            # Initialize Strands Agent with Bedrock model
            self.agent = Agent(
                name="RISE-Orchestrator",
                description="Main farming assistant orchestrator for rural Indian farmers",
                system_prompt=system_prompt,
                model=bedrock_model,
                # Tools will be added in subsequent phases
                tools=[]
            )
            
            logger.info(f"Strands agent initialized with model {self.config.BEDROCK_MODEL_ID}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Strands agent: {e}")
            raise
    
    def create_session(self, user_id: str, language: str = "en", metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new conversation session for a user
        
        Args:
            user_id: Unique identifier for the user
            language: Preferred language code
            metadata: Additional session metadata (location, crops, etc.)
        
        Returns:
            session_id: Unique session identifier
        """
        with self.tracer.start_as_current_span("create_session") as span:
            session_id = str(uuid.uuid4())
            
            self.sessions[session_id] = {
                "session_id": session_id,
                "user_id": user_id,
                "language": language,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "conversation_history": [],
                "context": metadata or {},
                "message_count": 0
            }
            
            # Record metrics
            if self.session_counter:
                self.session_counter.add(1, {"language": language})
            
            span.set_attribute("session_id", session_id)
            span.set_attribute("user_id", user_id)
            span.set_attribute("language", language)
            
            logger.info(f"Created session {session_id} for user {user_id}")
            
            return session_id
    
    def load_session_from_history(self, session_id: str, user_id: str) -> Optional[str]:
        """
        Load or create a session, restoring conversation history from DynamoDB
        
        Args:
            session_id: Session identifier (can be new or existing)
            user_id: User identifier
        
        Returns:
            session_id if successful, None otherwise
        """
        try:
            # Check if session exists in memory
            if session_id in self.sessions:
                logger.debug(f"Session {session_id} already loaded in memory")
                return session_id
            
            # Try to load from DynamoDB
            if self.context_tools:
                messages = self.context_tools.get_conversation_history(session_id, limit=50)
                
                if messages:
                    # Restore session from history
                    first_message = messages[0]
                    
                    self.sessions[session_id] = {
                        "session_id": session_id,
                        "user_id": user_id,
                        "language": first_message.get('metadata', {}).get('language', 'en'),
                        "created_at": first_message.get('created_at', datetime.utcnow().isoformat()),
                        "last_activity": datetime.utcnow().isoformat(),
                        "conversation_history": [
                            {
                                "role": msg['role'],
                                "content": msg['content'],
                                "timestamp": msg.get('created_at', '')
                            }
                            for msg in messages
                        ],
                        "context": {},
                        "message_count": len(messages)
                    }
                    
                    logger.info(f"Restored session {session_id} with {len(messages)} messages from DynamoDB")
                    return session_id
            
            # If no history found, create new session
            logger.info(f"No history found for session {session_id}, creating new session")
            return self.create_session(user_id)
            
        except Exception as e:
            logger.error(f"Error loading session from history: {e}")
            return None
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session information
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session data or None if not found
        """
        return self.sessions.get(session_id)
    
    def update_session_context(self, session_id: str, context_updates: Dict[str, Any]) -> bool:
        """
        Update session context with new information
        
        Args:
            session_id: Session identifier
            context_updates: Dictionary of context updates
        
        Returns:
            Success status
        """
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found")
            return False
        
        session["context"].update(context_updates)
        session["last_activity"] = datetime.utcnow().isoformat()
        
        logger.debug(f"Updated context for session {session_id}")
        return True
    
    def process_query(self, 
                     session_id: str, 
                     query: str, 
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user query using the Strands agent with full error handling and DynamoDB persistence
        
        Args:
            session_id: Session identifier
            query: User's question or request
            context: Additional context for this query
        
        Returns:
            Response dictionary with text, metadata, and status
        """
        start_time = datetime.utcnow()
        
        with self.tracer.start_as_current_span("process_query") as span:
            try:
                # Validate session
                session = self.sessions.get(session_id)
                if not session:
                    logger.error(f"Session {session_id} not found")
                    return {
                        "success": False,
                        "error": "Session not found. Please create a new session.",
                        "response": None
                    }
                
                # Update session activity
                session["last_activity"] = datetime.utcnow().isoformat()
                session["message_count"] += 1
                
                # Add query to in-memory conversation history
                session["conversation_history"].append({
                    "role": "user",
                    "content": query,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Persist to DynamoDB if context tools available
                if self.context_tools:
                    self.context_tools.save_conversation_message(
                        session_id=session_id,
                        user_id=session["user_id"],
                        role='user',
                        content=query,
                        metadata=context
                    )
                
                # Retrieve conversation context from DynamoDB
                conversation_context = ""
                if self.context_tools:
                    conversation_context = self.context_tools.get_context_window(
                        session_id=session_id,
                        window_size=5
                    )
                
                # Prepare context for agent
                agent_context = {
                    "user_language": session["language"],
                    "conversation_history": session["conversation_history"][-5:],  # Last 5 messages
                    "user_context": session["context"],
                    "persistent_context": conversation_context
                }
                
                if context:
                    agent_context.update(context)
                
                # Set span attributes
                span.set_attribute("session_id", session_id)
                span.set_attribute("query_length", len(query))
                span.set_attribute("language", session["language"])
                span.set_attribute("message_count", session["message_count"])
                
                # Process with Strands agent
                logger.info(f"Processing query for session {session_id}: {query[:100]}...")
                
                # Enhance query with context for better responses
                enhanced_query = query
                if conversation_context and conversation_context != "No previous conversation context.":
                    enhanced_query = f"{conversation_context}\n\nCurrent question: {query}"
                
                # Run the agent using invoke_async (Strands uses async by default)
                import asyncio
                
                # Create event loop if needed
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Invoke agent
                agent_response = loop.run_until_complete(
                    self.agent.invoke_async(enhanced_query)
                )
                
                # Extract response text from agent response
                if hasattr(agent_response, 'content'):
                    response_text = agent_response.content
                elif isinstance(agent_response, str):
                    response_text = agent_response
                else:
                    response_text = str(agent_response)
                
                # Add response to in-memory conversation history
                session["conversation_history"].append({
                    "role": "assistant",
                    "content": response_text,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Persist response to DynamoDB
                if self.context_tools:
                    self.context_tools.save_conversation_message(
                        session_id=session_id,
                        user_id=session["user_id"],
                        role='assistant',
                        content=response_text,
                        metadata={'duration_ms': (datetime.utcnow() - start_time).total_seconds() * 1000}
                    )
                
                # Check if conversation is getting long and needs summarization
                if session["message_count"] > 20 and session["message_count"] % 10 == 0:
                    if self.context_tools:
                        logger.info(f"Triggering conversation summarization for session {session_id}")
                        self.context_tools.summarize_conversation(session_id)
                
                # Calculate duration
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Record metrics
                if self.query_counter:
                    self.query_counter.add(1, {
                        "language": session["language"],
                        "status": "success"
                    })
                
                if self.query_duration:
                    self.query_duration.record(duration_ms, {
                        "language": session["language"]
                    })
                
                span.set_attribute("response_length", len(response_text))
                span.set_attribute("duration_ms", duration_ms)
                
                logger.info(f"Query processed successfully in {duration_ms:.2f}ms")
                
                return {
                    "success": True,
                    "response": response_text,
                    "session_id": session_id,
                    "language": session["language"],
                    "duration_ms": duration_ms,
                    "message_count": session["message_count"],
                    "context_persisted": self.context_tools is not None
                }
                
            except Exception as e:
                logger.error(f"Error processing query: {e}", exc_info=True)
                
                # Record error metric
                if self.query_counter:
                    self.query_counter.add(1, {
                        "language": session.get("language", "unknown") if session else "unknown",
                        "status": "error"
                    })
                
                span.set_attribute("error", True)
                span.set_attribute("error_message", str(e))
                
                return {
                    "success": False,
                    "error": f"An error occurred: {str(e)}",
                    "response": "I apologize, but I encountered an error processing your request. Please try again or rephrase your question.",
                    "session_id": session_id
                }
    
    def process_voice_query(self, 
                           session_id: str,
                           audio_data: bytes, 
                           language: Optional[str] = None) -> Dict[str, Any]:
        """
        Process voice input and return response with voice output
        
        Args:
            session_id: Session identifier
            audio_data: Audio bytes from user
            language: Detected or preferred language (optional, will auto-detect)
        
        Returns:
            Dict with text response, audio response, and transcription
        """
        with self.tracer.start_as_current_span("process_voice_query") as span:
            session = self.sessions.get(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            span.set_attribute("session_id", session_id)
            span.set_attribute("audio_size_bytes", len(audio_data))
            
            try:
                # Import voice tools
                from tools.voice_tools import VoiceProcessingTools
                
                # Create voice tools instance
                voice_tools = VoiceProcessingTools(region=self.config.BEDROCK_REGION)
                
                # Process voice query (transcribe + detect language)
                transcription_result = voice_tools.process_voice_query(
                    audio_data=audio_data,
                    user_language=language or session["language"]
                )
                
                if not transcription_result['success']:
                    return {
                        "success": False,
                        "error": transcription_result.get('error', 'Transcription failed')
                    }
                
                transcribed_text = transcription_result['text']
                detected_language = transcription_result['language_code']
                
                # Update session language if different
                if detected_language != session["language"]:
                    session["language"] = detected_language
                
                # Process the transcribed text query
                text_response = self.process_query(
                    session_id=session_id,
                    query=transcribed_text,
                    context={"input_type": "voice"}
                )
                
                if not text_response['success']:
                    return text_response
                
                # Generate voice response
                voice_response = voice_tools.generate_voice_response(
                    text=text_response['response'],
                    language_code=detected_language
                )
                
                return {
                    "success": True,
                    "transcribed_text": transcribed_text,
                    "detected_language": detected_language,
                    "language_name": transcription_result['language_name'],
                    "text_response": text_response['response'],
                    "audio_response": voice_response.get('audio_data') if voice_response['success'] else None,
                    "audio_format": voice_response.get('audio_format', 'mp3'),
                    "session_id": session_id,
                    "duration_ms": text_response.get('duration_ms', 0)
                }
                
            except Exception as e:
                logger.error(f"Voice query processing error: {e}", exc_info=True)
                span.set_attribute("error", True)
                span.set_attribute("error_message", str(e))
                
                return {
                    "success": False,
                    "error": f"Voice processing error: {str(e)}"
                }
    
    def translate_response(self,
                          text: str,
                          target_language: str,
                          source_language: str = 'en',
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Translate response text to target language with agricultural context
        
        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (default: English)
            context: Optional context for cultural adaptation
        
        Returns:
            Dict with translated text and metadata
        """
        with self.tracer.start_as_current_span("translate_response") as span:
            try:
                # Import translation tools
                from tools.translation_tools import TranslationTools
                
                # Create translation tools instance
                translation_tools = TranslationTools(
                    region=self.config.BEDROCK_REGION,
                    enable_caching=True
                )
                
                span.set_attribute("source_language", source_language)
                span.set_attribute("target_language", target_language)
                span.set_attribute("text_length", len(text))
                
                # Use context-aware translation if context provided
                if context:
                    result = translation_tools.translate_with_context(
                        text=text,
                        target_language=target_language,
                        context=context,
                        source_language=source_language
                    )
                else:
                    # Use fallback translation for reliability
                    result = translation_tools.translate_with_fallback(
                        text=text,
                        target_language=target_language,
                        source_language=source_language,
                        fallback_language='hi'
                    )
                
                span.set_attribute("translation_success", result['success'])
                if result.get('from_cache'):
                    span.set_attribute("from_cache", True)
                
                return result
                
            except Exception as e:
                logger.error(f"Translation error: {e}", exc_info=True)
                span.set_attribute("error", True)
                span.set_attribute("error_message", str(e))
                
                return {
                    "success": False,
                    "error": f"Translation error: {str(e)}",
                    "translated_text": text  # Return original text on error
                }
    
    def process_multilingual_query(self,
                                   session_id: str,
                                   query: str,
                                   query_language: str,
                                   response_language: Optional[str] = None,
                                   context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process query in one language and return response in another language
        
        Args:
            session_id: Session identifier
            query: User's query
            query_language: Language of the query
            response_language: Desired response language (defaults to query language)
            context: Additional context for processing
        
        Returns:
            Dict with response in target language
        """
        with self.tracer.start_as_current_span("process_multilingual_query") as span:
            try:
                session = self.sessions.get(session_id)
                if not session:
                    return {
                        "success": False,
                        "error": "Session not found"
                    }
                
                # Default response language to query language
                if not response_language:
                    response_language = query_language
                
                span.set_attribute("session_id", session_id)
                span.set_attribute("query_language", query_language)
                span.set_attribute("response_language", response_language)
                
                # If query is not in English, translate to English for processing
                if query_language != 'en':
                    translation_result = self.translate_response(
                        text=query,
                        target_language='en',
                        source_language=query_language,
                        context=context
                    )
                    
                    if not translation_result['success']:
                        return {
                            "success": False,
                            "error": "Failed to translate query"
                        }
                    
                    english_query = translation_result['translated_text']
                else:
                    english_query = query
                
                # Process query in English
                response = self.process_query(
                    session_id=session_id,
                    query=english_query,
                    context=context
                )
                
                if not response['success']:
                    return response
                
                # If response language is not English, translate response
                if response_language != 'en':
                    translation_result = self.translate_response(
                        text=response['response'],
                        target_language=response_language,
                        source_language='en',
                        context=context
                    )
                    
                    if translation_result['success']:
                        response['response'] = translation_result['translated_text']
                        response['translated'] = True
                        response['translation_from_cache'] = translation_result.get('from_cache', False)
                
                response['query_language'] = query_language
                response['response_language'] = response_language
                
                return response
                
            except Exception as e:
                logger.error(f"Multilingual query processing error: {e}", exc_info=True)
                span.set_attribute("error", True)
                span.set_attribute("error_message", str(e))
                
                return {
                    "success": False,
                    "error": f"Multilingual processing error: {str(e)}"
                }
    
    def analyze_image(self, 
                     session_id: str,
                     image_data: bytes, 
                     analysis_type: str,
                     additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze crop/soil images using Amazon Bedrock multimodal capabilities
        (Placeholder for Phase 3 implementation)
        
        Args:
            session_id: Session identifier
            image_data: Image bytes
            analysis_type: Type of analysis (disease, pest, soil)
            additional_context: Additional context (crop type, symptoms, etc.)
        
        Returns:
            Analysis results with diagnosis and recommendations
        """
        with self.tracer.start_as_current_span("analyze_image") as span:
            session = self.sessions.get(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            span.set_attribute("session_id", session_id)
            span.set_attribute("analysis_type", analysis_type)
            span.set_attribute("image_size_bytes", len(image_data))
            
            # TODO: Implement image analysis with Bedrock multimodal
            # This will be completed in Phase 3
            logger.info(f"Image analysis requested for session {session_id}, type: {analysis_type} (not yet implemented)")
            
            return {
                "success": False,
                "analysis_type": analysis_type,
                "result": "Image analysis will be implemented in Phase 3",
                "confidence": 0.0,
                "recommendations": []
            }
    
    def cleanup_session(self, session_id: str) -> bool:
        """
        Clean up and remove a session from memory
        (DynamoDB data persists with TTL-based cleanup)
        
        Args:
            session_id: Session identifier
        
        Returns:
            Success status
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned up session {session_id} from memory")
            return True
        return False
    
    def cleanup_expired_sessions(self, timeout_hours: int = 24) -> int:
        """
        Clean up sessions that have been inactive for longer than timeout
        
        Args:
            timeout_hours: Hours of inactivity before cleanup (default: 24)
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            current_time = datetime.utcnow()
            timeout_delta = timedelta(hours=timeout_hours)
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                last_activity = datetime.fromisoformat(session["last_activity"])
                if current_time - last_activity > timeout_delta:
                    expired_sessions.append(session_id)
            
            # Remove expired sessions
            for session_id in expired_sessions:
                del self.sessions[session_id]
                logger.info(f"Cleaned up expired session {session_id}")
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
            return len(expired_sessions)
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
            return 0
    
    def check_session_timeout(self, session_id: str, timeout_hours: int = 24) -> bool:
        """
        Check if a session has timed out
        
        Args:
            session_id: Session identifier
            timeout_hours: Hours of inactivity before timeout (default: 24)
        
        Returns:
            True if session has timed out, False otherwise
        """
        session = self.sessions.get(session_id)
        if not session:
            return True  # Session doesn't exist, consider it timed out
        
        try:
            last_activity = datetime.fromisoformat(session["last_activity"])
            current_time = datetime.utcnow()
            timeout_delta = timedelta(hours=timeout_hours)
            
            return (current_time - last_activity) > timeout_delta
            
        except Exception as e:
            logger.error(f"Error checking session timeout: {e}")
            return False
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions)
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session statistics or None
        """
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session_id,
            "user_id": session["user_id"],
            "language": session["language"],
            "created_at": session["created_at"],
            "last_activity": session["last_activity"],
            "message_count": session["message_count"],
            "conversation_length": len(session["conversation_history"])
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive orchestrator status
        
        Returns:
            Status dictionary with all component states
        """
        return {
            "orchestrator": {
                "status": "operational",
                "agent_initialized": self.agent is not None,
                "aws_configured": self.bedrock_client is not None,
                "otel_enabled": self.tracer is not None
            },
            "configuration": {
                "model_id": self.config.BEDROCK_MODEL_ID,
                "region": self.config.BEDROCK_REGION,
                "environment": self.config.APP_ENV,
                "supported_languages": list(self.config.SUPPORTED_LANGUAGES.keys())
            },
            "sessions": {
                "active_count": self.get_active_sessions_count(),
                "total_created": len(self.sessions)
            },
            "capabilities": {
                "voice_processing": True,   # Phase 2 - Implemented
                "translation": True,        # Phase 2 - Implemented
                "multilingual": True,       # Phase 2 - Implemented
                "context_management": True, # Phase 2 - Implemented
                "context_persistence": self.context_tools is not None,  # DynamoDB persistence
                "conversation_summarization": self.context_tools is not None,
                "session_timeout": True,    # Automatic cleanup
                "image_analysis": False,    # Phase 3
                "error_handling": True,
                "observability": self.tracer is not None
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all components
        
        Returns:
            Health status dictionary
        """
        health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        # Check agent
        health["checks"]["agent"] = {
            "status": "healthy" if self.agent else "unhealthy",
            "message": "Agent initialized" if self.agent else "Agent not initialized"
        }
        
        # Check AWS Bedrock
        try:
            # Simple check - if client exists and we can create it, it's healthy
            health["checks"]["bedrock"] = {
                "status": "healthy" if self.bedrock_client else "unhealthy",
                "message": "Bedrock client initialized" if self.bedrock_client else "Bedrock client not initialized"
            }
        except Exception as e:
            health["checks"]["bedrock"] = {
                "status": "unhealthy",
                "message": f"Bedrock error: {str(e)}"
            }
            health["status"] = "degraded"
        
        # Check OTEL
        health["checks"]["observability"] = {
            "status": "healthy" if self.tracer else "degraded",
            "message": "OTEL enabled" if self.tracer else "OTEL not enabled"
        }
        
        return health

# Global orchestrator instance
_orchestrator: Optional[RISEOrchestrator] = None

def get_orchestrator() -> RISEOrchestrator:
    """
    Get or create the global orchestrator instance (Singleton pattern)
    
    Returns:
        RISEOrchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = RISEOrchestrator()
    return _orchestrator

def reset_orchestrator():
    """Reset the global orchestrator instance (useful for testing)"""
    global _orchestrator
    _orchestrator = None

# Convenience functions for common operations

def create_farming_session(user_id: str, language: str = "hi", location: Optional[str] = None, crops: Optional[List[str]] = None) -> str:
    """
    Create a new farming session with common metadata
    
    Args:
        user_id: User identifier
        language: Preferred language (default: Hindi)
        location: Farmer's location
        crops: List of crops being grown
    
    Returns:
        session_id
    """
    orchestrator = get_orchestrator()
    metadata = {}
    
    if location:
        metadata["location"] = location
    if crops:
        metadata["crops"] = crops
    
    return orchestrator.create_session(user_id, language, metadata)

def ask_farming_question(session_id: str, question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Ask a farming question and get a response
    
    Args:
        session_id: Session identifier
        question: Farmer's question
        context: Additional context
    
    Returns:
        Response dictionary
    """
    orchestrator = get_orchestrator()
    return orchestrator.process_query(session_id, question, context)

def get_orchestrator_health() -> Dict[str, Any]:
    """
    Get health status of the orchestrator
    
    Returns:
        Health status dictionary
    """
    try:
        orchestrator = get_orchestrator()
        return orchestrator.health_check()
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    # Test the orchestrator
    print("=" * 60)
    print("RISE Orchestrator Agent - Test Mode")
    print("=" * 60)
    
    try:
        # Initialize orchestrator
        print("\n1. Initializing orchestrator...")
        orchestrator = get_orchestrator()
        print("✓ Orchestrator initialized successfully")
        
        # Check status
        print("\n2. Checking status...")
        status = orchestrator.get_status()
        print(f"✓ Status: {status['orchestrator']['status']}")
        print(f"  - Agent initialized: {status['orchestrator']['agent_initialized']}")
        print(f"  - AWS configured: {status['orchestrator']['aws_configured']}")
        print(f"  - Model: {status['configuration']['model_id']}")
        print(f"  - Region: {status['configuration']['region']}")
        print(f"  - Supported languages: {len(status['configuration']['supported_languages'])}")
        
        # Health check
        print("\n3. Running health check...")
        health = orchestrator.health_check()
        print(f"✓ Health: {health['status']}")
        for check_name, check_result in health['checks'].items():
            print(f"  - {check_name}: {check_result['status']} - {check_result['message']}")
        
        # Create test session
        print("\n4. Creating test session...")
        session_id = orchestrator.create_session(
            user_id="test_farmer_001",
            language="hi",
            metadata={
                "location": "Uttar Pradesh",
                "crops": ["wheat", "rice"]
            }
        )
        print(f"✓ Session created: {session_id}")
        
        # Get session stats
        print("\n5. Getting session stats...")
        stats = orchestrator.get_session_stats(session_id)
        print(f"✓ Session stats:")
        print(f"  - User ID: {stats['user_id']}")
        print(f"  - Language: {stats['language']}")
        print(f"  - Messages: {stats['message_count']}")
        
        # Test query (will work if AWS credentials are configured)
        print("\n6. Testing query processing...")
        try:
            response = orchestrator.process_query(
                session_id=session_id,
                query="What are the best practices for wheat cultivation?",
                context={"crop": "wheat", "season": "rabi"}
            )
            
            if response['success']:
                print(f"✓ Query processed successfully")
                print(f"  - Response length: {len(response['response'])} characters")
                print(f"  - Duration: {response['duration_ms']:.2f}ms")
                print(f"  - Message count: {response['message_count']}")
            else:
                print(f"⚠ Query processing returned error: {response.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"⚠ Query processing failed (expected if AWS not configured): {e}")
        
        # Cleanup
        print("\n7. Cleaning up session...")
        orchestrator.cleanup_session(session_id)
        print("✓ Session cleaned up")
        
        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
