"""
RISE Voice Processing Tools
Tools for speech-to-text, text-to-speech, and language detection using AWS services
"""

import boto3
import logging
from typing import Dict, Any, Optional, List
import base64
import json
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class VoiceProcessingTools:
    """Voice processing tools for RISE farming assistant"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize voice processing tools with AWS clients
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.transcribe_client = boto3.client('transcribe', region_name=region)
        self.polly_client = boto3.client('polly', region_name=region)
        self.comprehend_client = boto3.client('comprehend', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        
        # Language code mapping for AWS services
        self.language_codes = {
            'en': {'transcribe': 'en-IN', 'polly': 'en-IN', 'name': 'English'},
            'hi': {'transcribe': 'hi-IN', 'polly': 'hi-IN', 'name': 'Hindi'},
            'ta': {'transcribe': 'ta-IN', 'polly': 'ta-IN', 'name': 'Tamil'},
            'te': {'transcribe': 'te-IN', 'polly': 'te-IN', 'name': 'Telugu'},
            'kn': {'transcribe': 'kn-IN', 'polly': 'kn-IN', 'name': 'Kannada'},
            'bn': {'transcribe': 'bn-IN', 'polly': 'bn-IN', 'name': 'Bengali'},
            'gu': {'transcribe': 'gu-IN', 'polly': 'gu-IN', 'name': 'Gujarati'},
            'mr': {'transcribe': 'mr-IN', 'polly': 'mr-IN', 'name': 'Marathi'},
            'pa': {'transcribe': 'pa-IN', 'polly': 'pa-IN', 'name': 'Punjabi'}
        }
        
        # Polly voice mapping for Indic languages
        self.polly_voices = {
            'en-IN': 'Aditi',  # Female Indian English voice
            'hi-IN': 'Aditi',  # Supports Hindi
            'ta-IN': 'Aditi',  # Supports Tamil
            'te-IN': 'Aditi',  # Supports Telugu
            'kn-IN': 'Aditi',  # Supports Kannada
            'bn-IN': 'Aditi',  # Supports Bengali
            'gu-IN': 'Aditi',  # Supports Gujarati
            'mr-IN': 'Aditi',  # Supports Marathi
            'pa-IN': 'Aditi'   # Supports Punjabi
        }
        
        logger.info(f"Voice processing tools initialized in region {region}")
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect language from text using Amazon Comprehend
        
        Args:
            text: Text to analyze for language detection
        
        Returns:
            Dict with detected language code and confidence
        """
        try:
            response = self.comprehend_client.detect_dominant_language(Text=text)
            
            if response['Languages']:
                dominant_lang = response['Languages'][0]
                lang_code = dominant_lang['LanguageCode']
                confidence = dominant_lang['Score']
                
                # Map to our supported language codes
                supported_lang = self._map_to_supported_language(lang_code)
                
                return {
                    'success': True,
                    'language_code': supported_lang,
                    'language_name': self.language_codes.get(supported_lang, {}).get('name', 'Unknown'),
                    'confidence': confidence,
                    'original_code': lang_code
                }
            else:
                return {
                    'success': False,
                    'error': 'No language detected',
                    'language_code': 'en'  # Default to English
                }
        
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return {
                'success': False,
                'error': str(e),
                'language_code': 'en'  # Default to English on error
            }
    
    def _map_to_supported_language(self, lang_code: str) -> str:
        """Map detected language code to supported language"""
        # Extract base language code (e.g., 'hi' from 'hi-IN')
        base_code = lang_code.split('-')[0].lower()
        
        # Check if it's in our supported languages
        if base_code in self.language_codes:
            return base_code
        
        # Default to English if not supported
        return 'en'
    
    def transcribe_audio(self, 
                        audio_data: bytes, 
                        language_code: Optional[str] = None,
                        s3_bucket: str = 'rise-application-data',
                        enable_noise_reduction: bool = True) -> Dict[str, Any]:
        """
        Transcribe audio to text using Amazon Transcribe
        
        Args:
            audio_data: Audio file bytes (WAV, MP3, FLAC, etc.)
            language_code: Language code (e.g., 'hi', 'en'). If None, will auto-detect
            s3_bucket: S3 bucket for temporary audio storage
            enable_noise_reduction: Enable noise reduction for rural environments
        
        Returns:
            Dict with transcription text and metadata
        """
        try:
            # Generate unique job name
            job_name = f"transcribe_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
            
            # Upload audio to S3
            s3_key = f"audio/voice-queries/{job_name}.wav"
            self.s3_client.put_object(
                Bucket=s3_bucket,
                Key=s3_key,
                Body=audio_data,
                ContentType='audio/wav'
            )
            
            audio_uri = f"s3://{s3_bucket}/{s3_key}"
            
            # Determine language for transcription
            if language_code and language_code in self.language_codes:
                transcribe_lang = self.language_codes[language_code]['transcribe']
                identify_language = False
            else:
                # Auto-detect language from supported Indic languages
                transcribe_lang = None
                identify_language = True
            
            # Start transcription job
            transcribe_params = {
                'TranscriptionJobName': job_name,
                'Media': {'MediaFileUri': audio_uri},
                'MediaFormat': 'wav',
                'OutputBucketName': s3_bucket
            }
            
            if identify_language:
                # Enable automatic language identification
                transcribe_params['IdentifyLanguage'] = True
                transcribe_params['LanguageOptions'] = [
                    self.language_codes[code]['transcribe'] 
                    for code in self.language_codes.keys()
                ]
            else:
                transcribe_params['LanguageCode'] = transcribe_lang
            
            # Enable noise reduction settings for rural environments
            if enable_noise_reduction:
                transcribe_params['Settings'] = {
                    'ShowSpeakerLabels': False,
                    'MaxSpeakerLabels': 1,
                    'ChannelIdentification': False
                }
            
            self.transcribe_client.start_transcription_job(**transcribe_params)
            
            # Wait for job completion (with timeout)
            import time
            max_wait = 60  # 60 seconds timeout
            wait_time = 0
            
            while wait_time < max_wait:
                status = self.transcribe_client.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                
                job_status = status['TranscriptionJob']['TranscriptionJobStatus']
                
                if job_status == 'COMPLETED':
                    # Get transcription result
                    transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
                    
                    # Download transcript from S3
                    import requests
                    transcript_response = requests.get(transcript_uri)
                    transcript_data = transcript_response.json()
                    
                    # Extract text
                    transcription_text = transcript_data['results']['transcripts'][0]['transcript']
                    
                    # Get detected language if auto-detect was used
                    detected_lang = None
                    if identify_language and 'language_identification' in transcript_data['results']:
                        lang_results = transcript_data['results']['language_identification']
                        if lang_results:
                            detected_lang = lang_results[0]['code']
                    
                    # Cleanup S3 files
                    self._cleanup_transcription_files(s3_bucket, s3_key, job_name)
                    
                    return {
                        'success': True,
                        'text': transcription_text,
                        'language_code': self._map_transcribe_lang_to_code(detected_lang or transcribe_lang),
                        'confidence': transcript_data['results']['items'][0].get('alternatives', [{}])[0].get('confidence', 1.0) if transcript_data['results']['items'] else 1.0,
                        'job_name': job_name
                    }
                
                elif job_status == 'FAILED':
                    failure_reason = status['TranscriptionJob'].get('FailureReason', 'Unknown error')
                    logger.error(f"Transcription job failed: {failure_reason}")
                    
                    # Cleanup
                    self._cleanup_transcription_files(s3_bucket, s3_key, job_name)
                    
                    return {
                        'success': False,
                        'error': f"Transcription failed: {failure_reason}"
                    }
                
                # Wait before checking again
                time.sleep(2)
                wait_time += 2
            
            # Timeout
            logger.error(f"Transcription job timed out: {job_name}")
            return {
                'success': False,
                'error': 'Transcription timed out. Please try again with a shorter audio clip.'
            }
        
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _map_transcribe_lang_to_code(self, transcribe_lang: str) -> str:
        """Map Transcribe language code to our language code"""
        for code, langs in self.language_codes.items():
            if langs['transcribe'] == transcribe_lang:
                return code
        return 'en'
    
    def _cleanup_transcription_files(self, bucket: str, audio_key: str, job_name: str):
        """Clean up temporary S3 files"""
        try:
            # Delete audio file
            self.s3_client.delete_object(Bucket=bucket, Key=audio_key)
            
            # Delete transcription output
            transcript_key = f"{job_name}.json"
            self.s3_client.delete_object(Bucket=bucket, Key=transcript_key)
            
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")
    
    def synthesize_speech(self, 
                         text: str, 
                         language_code: str = 'en',
                         voice_id: Optional[str] = None,
                         output_format: str = 'mp3') -> Dict[str, Any]:
        """
        Convert text to speech using Amazon Polly
        
        Args:
            text: Text to convert to speech
            language_code: Language code (e.g., 'hi', 'en')
            voice_id: Specific Polly voice ID (optional, will auto-select based on language)
            output_format: Audio format ('mp3', 'ogg_vorbis', 'pcm')
        
        Returns:
            Dict with audio data and metadata
        """
        try:
            # Get language-specific settings
            if language_code not in self.language_codes:
                language_code = 'en'  # Default to English
            
            polly_lang = self.language_codes[language_code]['polly']
            
            # Select voice
            if not voice_id:
                voice_id = self.polly_voices.get(polly_lang, 'Aditi')
            
            # Synthesize speech
            response = self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat=output_format,
                VoiceId=voice_id,
                LanguageCode=polly_lang,
                Engine='neural'  # Use neural engine for better quality
            )
            
            # Read audio stream
            audio_data = response['AudioStream'].read()
            
            # Encode to base64 for transmission
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            return {
                'success': True,
                'audio_data': audio_base64,
                'audio_format': output_format,
                'language_code': language_code,
                'voice_id': voice_id,
                'text_length': len(text)
            }
        
        except Exception as e:
            logger.error(f"Speech synthesis error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_voice_query(self, 
                           audio_data: bytes,
                           user_language: Optional[str] = None,
                           s3_bucket: str = 'rise-application-data') -> Dict[str, Any]:
        """
        Complete voice query processing: transcribe, detect language, return text
        
        Args:
            audio_data: Audio file bytes
            user_language: User's preferred language (optional)
            s3_bucket: S3 bucket for audio storage
        
        Returns:
            Dict with transcribed text and detected language
        """
        try:
            # Transcribe audio
            transcription = self.transcribe_audio(
                audio_data=audio_data,
                language_code=user_language,
                s3_bucket=s3_bucket,
                enable_noise_reduction=True
            )
            
            if not transcription['success']:
                return transcription
            
            text = transcription['text']
            detected_lang = transcription['language_code']
            
            # If no user language was provided, detect from text
            if not user_language:
                lang_detection = self.detect_language(text)
                if lang_detection['success']:
                    detected_lang = lang_detection['language_code']
            
            return {
                'success': True,
                'text': text,
                'language_code': detected_lang,
                'language_name': self.language_codes.get(detected_lang, {}).get('name', 'Unknown'),
                'confidence': transcription.get('confidence', 1.0)
            }
        
        except Exception as e:
            logger.error(f"Voice query processing error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_voice_response(self,
                               text: str,
                               language_code: str = 'en') -> Dict[str, Any]:
        """
        Generate voice response for text
        
        Args:
            text: Response text to convert to speech
            language_code: Language code for speech synthesis
        
        Returns:
            Dict with audio data
        """
        return self.synthesize_speech(
            text=text,
            language_code=language_code,
            output_format='mp3'
        )


# Strands @tool decorator functions for agent integration

def create_voice_tools(region: str = "us-east-1") -> VoiceProcessingTools:
    """
    Factory function to create voice processing tools instance
    
    Args:
        region: AWS region
    
    Returns:
        VoiceProcessingTools instance
    """
    return VoiceProcessingTools(region=region)


# Tool functions for Strands agent integration

def transcribe_audio_tool(audio_data: bytes, language_code: Optional[str] = None) -> str:
    """
    Tool for transcribing audio to text
    
    Args:
        audio_data: Audio file bytes
        language_code: Optional language code
    
    Returns:
        Transcribed text
    """
    tools = create_voice_tools()
    result = tools.transcribe_audio(audio_data, language_code)
    
    if result['success']:
        return result['text']
    else:
        return f"Error: {result.get('error', 'Transcription failed')}"


def synthesize_speech_tool(text: str, language_code: str = 'en') -> str:
    """
    Tool for converting text to speech
    
    Args:
        text: Text to convert
        language_code: Language code
    
    Returns:
        Base64 encoded audio data
    """
    tools = create_voice_tools()
    result = tools.synthesize_speech(text, language_code)
    
    if result['success']:
        return result['audio_data']
    else:
        return f"Error: {result.get('error', 'Speech synthesis failed')}"


def detect_language_tool(text: str) -> str:
    """
    Tool for detecting language from text
    
    Args:
        text: Text to analyze
    
    Returns:
        Detected language code
    """
    tools = create_voice_tools()
    result = tools.detect_language(text)
    
    if result['success']:
        return f"{result['language_name']} ({result['language_code']}) - Confidence: {result['confidence']:.2f}"
    else:
        return f"Error: {result.get('error', 'Language detection failed')}"
