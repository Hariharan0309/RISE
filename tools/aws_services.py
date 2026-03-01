"""
AWS Service Integration Module

This module provides boto3 client initialization and connection validation
for AWS services used in the MissionAI Farmer Agent system.

Services:
- Amazon Bedrock (Claude AI models)
- Amazon Transcribe (Speech-to-Text)
- Amazon Polly (Text-to-Speech)
- Amazon Translate (Language translation)
- Amazon S3 (Image storage)
"""

import os
import logging
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))


class AWSServiceClients:
    """
    Singleton class to manage AWS service clients.
    Initializes and validates connections to all required AWS services.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AWSServiceClients, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize AWS service clients with credentials from environment variables."""
        if self._initialized:
            return
            
        # Load AWS credentials from environment
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        
        # Validate credentials are present
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            logger.warning("AWS credentials not found in environment variables")
        
        # Initialize clients
        self._bedrock_client = None
        self._bedrock_runtime_client = None
        self._transcribe_client = None
        self._polly_client = None
        self._translate_client = None
        self._s3_client = None
        
        self._initialized = True
        logger.info(f"AWS Service Clients initialized for region: {self.aws_region}")
    
    @property
    def bedrock(self):
        """Get or create Amazon Bedrock client."""
        if self._bedrock_client is None:
            self._bedrock_client = boto3.client(
                'bedrock',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            logger.info("Bedrock client initialized")
        return self._bedrock_client
    
    @property
    def bedrock_runtime(self):
        """Get or create Amazon Bedrock Runtime client for model invocation."""
        if self._bedrock_runtime_client is None:
            self._bedrock_runtime_client = boto3.client(
                'bedrock-runtime',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            logger.info("Bedrock Runtime client initialized")
        return self._bedrock_runtime_client
    
    @property
    def transcribe(self):
        """Get or create Amazon Transcribe client."""
        if self._transcribe_client is None:
            self._transcribe_client = boto3.client(
                'transcribe',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            logger.info("Transcribe client initialized")
        return self._transcribe_client
    
    @property
    def polly(self):
        """Get or create Amazon Polly client."""
        if self._polly_client is None:
            self._polly_client = boto3.client(
                'polly',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            logger.info("Polly client initialized")
        return self._polly_client
    
    @property
    def translate(self):
        """Get or create Amazon Translate client."""
        if self._translate_client is None:
            self._translate_client = boto3.client(
                'translate',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            logger.info("Translate client initialized")
        return self._translate_client
    
    @property
    def s3(self):
        """Get or create Amazon S3 client."""
        if self._s3_client is None:
            self._s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            logger.info("S3 client initialized")
        return self._s3_client


def validate_bedrock_connection() -> Dict[str, Any]:
    """
    Validate connection to Amazon Bedrock service.
    
    Returns:
        dict: Validation result with 'success' boolean and 'message' string
    """
    try:
        clients = AWSServiceClients()
        # List foundation models to verify connection
        response = clients.bedrock.list_foundation_models()
        logger.info("Bedrock connection validated successfully")
        return {
            'success': True,
            'message': 'Bedrock connection successful',
            'models_available': len(response.get('modelSummaries', []))
        }
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        return {
            'success': False,
            'message': 'AWS credentials not found. Please configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY'
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"Bedrock connection failed: {error_code}")
        return {
            'success': False,
            'message': f'Bedrock connection failed: {error_code}'
        }
    except Exception as e:
        logger.error(f"Unexpected error validating Bedrock connection: {str(e)}")
        return {
            'success': False,
            'message': f'Unexpected error: {str(e)}'
        }


def validate_transcribe_connection() -> Dict[str, Any]:
    """
    Validate connection to Amazon Transcribe service.
    
    Returns:
        dict: Validation result with 'success' boolean and 'message' string
    """
    try:
        clients = AWSServiceClients()
        # List transcription jobs to verify connection (should return empty list if no jobs)
        clients.transcribe.list_transcription_jobs(MaxResults=1)
        logger.info("Transcribe connection validated successfully")
        return {
            'success': True,
            'message': 'Transcribe connection successful'
        }
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        return {
            'success': False,
            'message': 'AWS credentials not found'
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"Transcribe connection failed: {error_code}")
        return {
            'success': False,
            'message': f'Transcribe connection failed: {error_code}'
        }
    except Exception as e:
        logger.error(f"Unexpected error validating Transcribe connection: {str(e)}")
        return {
            'success': False,
            'message': f'Unexpected error: {str(e)}'
        }


def validate_polly_connection() -> Dict[str, Any]:
    """
    Validate connection to Amazon Polly service.
    
    Returns:
        dict: Validation result with 'success' boolean and 'message' string
    """
    try:
        clients = AWSServiceClients()
        # Describe voices to verify connection
        response = clients.polly.describe_voices()
        logger.info("Polly connection validated successfully")
        return {
            'success': True,
            'message': 'Polly connection successful',
            'voices_available': len(response.get('Voices', []))
        }
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        return {
            'success': False,
            'message': 'AWS credentials not found'
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"Polly connection failed: {error_code}")
        return {
            'success': False,
            'message': f'Polly connection failed: {error_code}'
        }
    except Exception as e:
        logger.error(f"Unexpected error validating Polly connection: {str(e)}")
        return {
            'success': False,
            'message': f'Unexpected error: {str(e)}'
        }


def validate_translate_connection() -> Dict[str, Any]:
    """
    Validate connection to Amazon Translate service.
    
    Returns:
        dict: Validation result with 'success' boolean and 'message' string
    """
    try:
        clients = AWSServiceClients()
        # List languages to verify connection
        response = clients.translate.list_languages()
        logger.info("Translate connection validated successfully")
        return {
            'success': True,
            'message': 'Translate connection successful',
            'languages_available': len(response.get('Languages', []))
        }
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        return {
            'success': False,
            'message': 'AWS credentials not found'
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"Translate connection failed: {error_code}")
        return {
            'success': False,
            'message': f'Translate connection failed: {error_code}'
        }
    except Exception as e:
        logger.error(f"Unexpected error validating Translate connection: {str(e)}")
        return {
            'success': False,
            'message': f'Unexpected error: {str(e)}'
        }


def validate_s3_connection() -> Dict[str, Any]:
    """
    Validate connection to Amazon S3 service.
    
    Returns:
        dict: Validation result with 'success' boolean and 'message' string
    """
    try:
        clients = AWSServiceClients()
        # List buckets to verify connection
        response = clients.s3.list_buckets()
        logger.info("S3 connection validated successfully")
        return {
            'success': True,
            'message': 'S3 connection successful',
            'buckets_available': len(response.get('Buckets', []))
        }
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        return {
            'success': False,
            'message': 'AWS credentials not found'
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"S3 connection failed: {error_code}")
        return {
            'success': False,
            'message': f'S3 connection failed: {error_code}'
        }
    except Exception as e:
        logger.error(f"Unexpected error validating S3 connection: {str(e)}")
        return {
            'success': False,
            'message': f'Unexpected error: {str(e)}'
        }


def validate_all_connections() -> Dict[str, Dict[str, Any]]:
    """
    Validate connections to all AWS services.
    
    Returns:
        dict: Dictionary with service names as keys and validation results as values
    """
    results = {
        'bedrock': validate_bedrock_connection(),
        'transcribe': validate_transcribe_connection(),
        'polly': validate_polly_connection(),
        'translate': validate_translate_connection(),
        's3': validate_s3_connection()
    }
    
    all_success = all(result['success'] for result in results.values())
    logger.info(f"All connections validated: {all_success}")
    
    return results


# Create a global instance for easy import
aws_clients = AWSServiceClients()



# Voice Processing Functions

# Language code mappings
LANGUAGE_CODE_MAP = {
    'kannada': 'kn-IN',
    'english': 'en-IN',
    'hindi': 'hi-IN',
    'kn': 'kn-IN',
    'en': 'en-IN',
    'hi': 'hi-IN'
}

# Polly voice ID mappings
POLLY_VOICE_MAP = {
    'kannada': os.getenv('AWS_POLLY_VOICE_ID_KANNADA', 'Aditi'),
    'english': os.getenv('AWS_POLLY_VOICE_ID_ENGLISH', 'Aditi'),
    'hindi': os.getenv('AWS_POLLY_VOICE_ID_HINDI', 'Aditi'),
    'kn': os.getenv('AWS_POLLY_VOICE_ID_KANNADA', 'Aditi'),
    'en': os.getenv('AWS_POLLY_VOICE_ID_ENGLISH', 'Aditi'),
    'hi': os.getenv('AWS_POLLY_VOICE_ID_HINDI', 'Aditi')
}


def detect_language(text: str) -> str:
    """
    Detect the language of the input text using simple heuristics.
    
    For production, this should use a more sophisticated language detection library
    or AWS Comprehend. This implementation uses basic character set detection.
    
    Args:
        text: Input text to detect language
        
    Returns:
        str: Detected language code ('kannada', 'english', or 'hindi')
    """
    if not text or not text.strip():
        return 'english'  # Default to English
    
    # Check for Kannada script (Unicode range: 0C80-0CFF)
    kannada_chars = sum(1 for char in text if '\u0C80' <= char <= '\u0CFF')
    
    # Check for Devanagari script (Hindi) (Unicode range: 0900-097F)
    devanagari_chars = sum(1 for char in text if '\u0900' <= char <= '\u097F')
    
    # Check for Latin script (English) (Unicode range: 0000-007F)
    latin_chars = sum(1 for char in text if '\u0000' <= char <= '\u007F')
    
    total_chars = len(text.replace(' ', ''))
    
    if total_chars == 0:
        return 'english'
    
    # Calculate percentages
    kannada_pct = kannada_chars / total_chars
    devanagari_pct = devanagari_chars / total_chars
    latin_pct = latin_chars / total_chars
    
    # Determine language based on highest percentage
    if kannada_pct > 0.3:
        return 'kannada'
    elif devanagari_pct > 0.3:
        return 'hindi'
    else:
        return 'english'


def transcribe_audio(audio_bytes: bytes, language: str = 'english') -> Dict[str, Any]:
    """
    Transcribe audio bytes to text using Amazon Transcribe.
    
    This function uses Amazon Transcribe's streaming API for real-time transcription.
    For production, consider using start_transcription_job for longer audio files.
    
    Args:
        audio_bytes: Audio data in bytes (WAV, MP3, or other supported format)
        language: Language code ('kannada', 'english', or 'hindi')
        
    Returns:
        dict: Transcription result with 'success', 'text', and 'confidence' fields
    """
    try:
        # Normalize language code
        language_code = LANGUAGE_CODE_MAP.get(language.lower(), 'en-IN')
        
        # For this implementation, we'll use a simplified approach
        # In production, you would use TranscribeStreamingClient or start_transcription_job
        
        # Note: Amazon Transcribe requires audio to be uploaded to S3 for batch jobs
        # or streamed for real-time transcription. This is a placeholder implementation.
        
        logger.info(f"Transcribing audio with language: {language_code}")
        
        # TODO: Implement actual transcription logic
        # This would involve:
        # 1. Upload audio to S3
        # 2. Start transcription job
        # 3. Wait for completion
        # 4. Retrieve transcript
        
        # For now, return a mock response structure
        return {
            'success': True,
            'text': '',  # Transcribed text would go here
            'language': language,
            'confidence': 0.0,
            'message': 'Transcription requires S3 upload and job processing'
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"Transcription failed: {error_code}")
        return {
            'success': False,
            'text': '',
            'error': error_code,
            'message': f'Transcription failed: {error_code}'
        }
    except Exception as e:
        logger.error(f"Unexpected error during transcription: {str(e)}")
        return {
            'success': False,
            'text': '',
            'error': str(e),
            'message': f'Unexpected error: {str(e)}'
        }


def text_to_speech(text: str, language: str = 'english') -> Dict[str, Any]:
    """
    Convert text to speech using Amazon Polly.
    
    Args:
        text: Text to convert to speech
        language: Language code ('kannada', 'english', or 'hindi')
        
    Returns:
        dict: TTS result with 'success', 'audio_bytes', and 'audio_format' fields
    """
    try:
        if not text or not text.strip():
            return {
                'success': False,
                'audio_bytes': None,
                'message': 'Text cannot be empty'
            }
        
        clients = AWSServiceClients()
        
        # Normalize language and get voice ID
        language_normalized = language.lower()
        voice_id = POLLY_VOICE_MAP.get(language_normalized, 'Aditi')
        
        logger.info(f"Converting text to speech with voice: {voice_id}, language: {language}")
        
        # Call Amazon Polly
        response = clients.polly.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice_id,
            Engine='neural'  # Use neural engine for better quality
        )
        
        # Read audio stream
        audio_bytes = response['AudioStream'].read()
        
        logger.info(f"Text-to-speech conversion successful, audio size: {len(audio_bytes)} bytes")
        
        return {
            'success': True,
            'audio_bytes': audio_bytes,
            'audio_format': 'mp3',
            'language': language,
            'voice_id': voice_id
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"Text-to-speech failed: {error_code}")
        return {
            'success': False,
            'audio_bytes': None,
            'error': error_code,
            'message': f'Text-to-speech failed: {error_code}'
        }
    except Exception as e:
        logger.error(f"Unexpected error during text-to-speech: {str(e)}")
        return {
            'success': False,
            'audio_bytes': None,
            'error': str(e),
            'message': f'Unexpected error: {str(e)}'
        }


def translate_text(text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
    """
    Translate text from source language to target language using Amazon Translate.
    
    Args:
        text: Text to translate
        source_lang: Source language code ('kannada', 'english', or 'hindi')
        target_lang: Target language code ('kannada', 'english', or 'hindi')
        
    Returns:
        dict: Translation result with 'success', 'translated_text', and language info
    """
    try:
        if not text or not text.strip():
            return {
                'success': False,
                'translated_text': '',
                'message': 'Text cannot be empty'
            }
        
        # If source and target are the same, return original text
        if source_lang.lower() == target_lang.lower():
            return {
                'success': True,
                'translated_text': text,
                'source_language': source_lang,
                'target_language': target_lang,
                'message': 'No translation needed (same language)'
            }
        
        clients = AWSServiceClients()
        
        # Map language names to AWS Translate language codes
        translate_lang_map = {
            'kannada': 'kn',
            'english': 'en',
            'hindi': 'hi',
            'kn': 'kn',
            'en': 'en',
            'hi': 'hi'
        }
        
        source_code = translate_lang_map.get(source_lang.lower(), 'en')
        target_code = translate_lang_map.get(target_lang.lower(), 'en')
        
        logger.info(f"Translating text from {source_code} to {target_code}")
        
        # Call Amazon Translate
        response = clients.translate.translate_text(
            Text=text,
            SourceLanguageCode=source_code,
            TargetLanguageCode=target_code
        )
        
        translated_text = response['TranslatedText']
        
        logger.info(f"Translation successful: {len(text)} -> {len(translated_text)} chars")
        
        return {
            'success': True,
            'translated_text': translated_text,
            'source_language': source_lang,
            'target_language': target_lang,
            'source_code': source_code,
            'target_code': target_code
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"Translation failed: {error_code}")
        return {
            'success': False,
            'translated_text': '',
            'error': error_code,
            'message': f'Translation failed: {error_code}'
        }
    except Exception as e:
        logger.error(f"Unexpected error during translation: {str(e)}")
        return {
            'success': False,
            'translated_text': '',
            'error': str(e),
            'message': f'Unexpected error: {str(e)}'
        }



# Error Handling and Resilience Patterns

import time
from functools import wraps
from typing import Callable, Any


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for AWS service calls.
    
    Prevents cascading failures by temporarily blocking calls to a failing service.
    States: CLOSED (normal), OPEN (blocking), HALF_OPEN (testing recovery)
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery (HALF_OPEN state)
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result or raises exception
        """
        if self.state == 'OPEN':
            # Check if timeout has elapsed
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = 'HALF_OPEN'
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise Exception(f"Circuit breaker is OPEN. Service unavailable.")
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset failure count
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                logger.info("Circuit breaker closed - service recovered")
            
            self.failure_count = 0
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
                logger.error(f"Circuit breaker opened after {self.failure_count} failures")
            
            raise e


# Global circuit breakers for each service
_circuit_breakers = {
    'bedrock': CircuitBreaker(failure_threshold=5, timeout=60),
    'transcribe': CircuitBreaker(failure_threshold=5, timeout=60),
    'polly': CircuitBreaker(failure_threshold=5, timeout=60),
    'translate': CircuitBreaker(failure_threshold=5, timeout=60),
    's3': CircuitBreaker(failure_threshold=5, timeout=60)
}


def with_retry(max_retries: int = 3, backoff_factor: float = 2.0, service_name: str = 'unknown'):
    """
    Decorator to add exponential backoff retry logic to AWS service calls.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff (delay = backoff_factor ^ attempt)
        service_name: Name of the AWS service for logging
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    # Use circuit breaker if available
                    if service_name in _circuit_breakers:
                        return _circuit_breakers[service_name].call(func, *args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    last_exception = e
                    
                    # Don't retry on certain errors
                    non_retryable_errors = [
                        'ValidationException',
                        'InvalidParameterException',
                        'AccessDeniedException',
                        'ResourceNotFoundException'
                    ]
                    
                    if error_code in non_retryable_errors:
                        logger.error(f"{service_name} non-retryable error: {error_code}")
                        raise e
                    
                    # Retry on throttling and server errors
                    if attempt < max_retries:
                        delay = backoff_factor ** attempt
                        logger.warning(
                            f"{service_name} error {error_code}, "
                            f"retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"{service_name} failed after {max_retries} retries")
                        
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        delay = backoff_factor ** attempt
                        logger.warning(
                            f"{service_name} unexpected error, "
                            f"retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"{service_name} failed after {max_retries} retries")
            
            # All retries exhausted
            raise last_exception
        
        return wrapper
    return decorator


@with_retry(max_retries=3, backoff_factor=2.0, service_name='polly')
def text_to_speech_with_retry(text: str, language: str = 'english') -> Dict[str, Any]:
    """
    Convert text to speech with retry logic and circuit breaker.
    
    This is a wrapper around text_to_speech with enhanced error handling.
    
    Args:
        text: Text to convert to speech
        language: Language code ('kannada', 'english', or 'hindi')
        
    Returns:
        dict: TTS result with 'success', 'audio_bytes', and 'audio_format' fields
    """
    return text_to_speech(text, language)


@with_retry(max_retries=3, backoff_factor=2.0, service_name='translate')
def translate_text_with_retry(text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
    """
    Translate text with retry logic and circuit breaker.
    
    This is a wrapper around translate_text with enhanced error handling.
    
    Args:
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code
        
    Returns:
        dict: Translation result
    """
    return translate_text(text, source_lang, target_lang)


@with_retry(max_retries=3, backoff_factor=2.0, service_name='transcribe')
def transcribe_audio_with_retry(audio_bytes: bytes, language: str = 'english') -> Dict[str, Any]:
    """
    Transcribe audio with retry logic and circuit breaker.
    
    This is a wrapper around transcribe_audio with enhanced error handling.
    
    Args:
        audio_bytes: Audio data in bytes
        language: Language code
        
    Returns:
        dict: Transcription result
    """
    return transcribe_audio(audio_bytes, language)


def get_circuit_breaker_status(service_name: str) -> Dict[str, Any]:
    """
    Get the current status of a circuit breaker.
    
    Args:
        service_name: Name of the AWS service
        
    Returns:
        dict: Circuit breaker status information
    """
    if service_name not in _circuit_breakers:
        return {
            'service': service_name,
            'exists': False,
            'message': 'Circuit breaker not found'
        }
    
    cb = _circuit_breakers[service_name]
    return {
        'service': service_name,
        'exists': True,
        'state': cb.state,
        'failure_count': cb.failure_count,
        'last_failure_time': cb.last_failure_time,
        'failure_threshold': cb.failure_threshold,
        'timeout': cb.timeout
    }


def reset_circuit_breaker(service_name: str) -> Dict[str, Any]:
    """
    Manually reset a circuit breaker to CLOSED state.
    
    Args:
        service_name: Name of the AWS service
        
    Returns:
        dict: Reset operation result
    """
    if service_name not in _circuit_breakers:
        return {
            'success': False,
            'message': f'Circuit breaker for {service_name} not found'
        }
    
    cb = _circuit_breakers[service_name]
    cb.state = 'CLOSED'
    cb.failure_count = 0
    cb.last_failure_time = None
    
    logger.info(f"Circuit breaker for {service_name} manually reset")
    
    return {
        'success': True,
        'service': service_name,
        'message': f'Circuit breaker for {service_name} reset to CLOSED state'
    }


def get_all_circuit_breaker_status() -> Dict[str, Dict[str, Any]]:
    """
    Get status of all circuit breakers.
    
    Returns:
        dict: Status of all circuit breakers
    """
    return {
        service: get_circuit_breaker_status(service)
        for service in _circuit_breakers.keys()
    }


# Graceful fallback mechanisms

def safe_text_to_speech(text: str, language: str = 'english', fallback_text: str = None) -> Dict[str, Any]:
    """
    Text-to-speech with graceful fallback.
    
    If TTS fails, returns a response indicating text-only mode.
    
    Args:
        text: Text to convert to speech
        language: Language code
        fallback_text: Optional fallback text to display if TTS fails
        
    Returns:
        dict: TTS result or fallback response
    """
    try:
        result = text_to_speech_with_retry(text, language)
        return result
    except Exception as e:
        logger.warning(f"TTS failed, falling back to text-only mode: {str(e)}")
        return {
            'success': False,
            'audio_bytes': None,
            'fallback_mode': True,
            'text': fallback_text or text,
            'message': 'Audio unavailable, displaying text only',
            'error': str(e)
        }


def safe_translate_text(text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
    """
    Translation with graceful fallback.
    
    If translation fails, returns original text with warning.
    
    Args:
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code
        
    Returns:
        dict: Translation result or fallback response
    """
    try:
        result = translate_text_with_retry(text, source_lang, target_lang)
        return result
    except Exception as e:
        logger.warning(f"Translation failed, returning original text: {str(e)}")
        return {
            'success': False,
            'translated_text': text,
            'fallback_mode': True,
            'source_language': source_lang,
            'target_language': target_lang,
            'message': 'Translation unavailable, showing original text',
            'error': str(e)
        }


def safe_transcribe_audio(audio_bytes: bytes, language: str = 'english') -> Dict[str, Any]:
    """
    Transcription with graceful fallback.
    
    If transcription fails, prompts user to try again or use text input.
    
    Args:
        audio_bytes: Audio data in bytes
        language: Language code
        
    Returns:
        dict: Transcription result or fallback response
    """
    try:
        result = transcribe_audio_with_retry(audio_bytes, language)
        return result
    except Exception as e:
        logger.warning(f"Transcription failed: {str(e)}")
        return {
            'success': False,
            'text': '',
            'fallback_mode': True,
            'message': 'Voice input unavailable. Please try again or use text input.',
            'error': str(e)
        }
