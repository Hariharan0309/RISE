"""
RISE Translation Tools
Tools for multilingual translation with agricultural terminology support using AWS Translate
"""

import boto3
import logging
from typing import Dict, Any, Optional, List
import json
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class TranslationTools:
    """Translation tools for RISE farming assistant with caching and agricultural terminology"""
    
    def __init__(self, region: str = "us-east-1", enable_caching: bool = True):
        """
        Initialize translation tools with AWS clients
        
        Args:
            region: AWS region for services
            enable_caching: Enable translation caching for performance
        """
        self.region = region
        self.translate_client = boto3.client('translate', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        
        # Language code mapping for AWS Translate
        self.language_codes = {
            'en': {'translate': 'en', 'name': 'English'},
            'hi': {'translate': 'hi', 'name': 'Hindi'},
            'ta': {'translate': 'ta', 'name': 'Tamil'},
            'te': {'translate': 'te', 'name': 'Telugu'},
            'kn': {'translate': 'kn', 'name': 'Kannada'},
            'bn': {'translate': 'bn', 'name': 'Bengali'},
            'gu': {'translate': 'gu', 'name': 'Gujarati'},
            'mr': {'translate': 'mr', 'name': 'Marathi'},
            'pa': {'translate': 'pa', 'name': 'Punjabi'}
        }
        
        # Agricultural terminology for custom translation
        self.agricultural_terms = {
            'en': {
                'fertilizer': 'fertilizer',
                'pesticide': 'pesticide',
                'crop': 'crop',
                'soil': 'soil',
                'irrigation': 'irrigation',
                'harvest': 'harvest',
                'yield': 'yield',
                'seed': 'seed',
                'tractor': 'tractor',
                'subsidy': 'subsidy'
            },
            'hi': {
                'fertilizer': 'उर्वरक',
                'pesticide': 'कीटनाशक',
                'crop': 'फसल',
                'soil': 'मिट्टी',
                'irrigation': 'सिंचाई',
                'harvest': 'कटाई',
                'yield': 'उपज',
                'seed': 'बीज',
                'tractor': 'ट्रैक्टर',
                'subsidy': 'सब्सिडी'
            }
        }
        
        # Translation cache (in-memory for now, can be Redis in production)
        self.enable_caching = enable_caching
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(hours=24)  # Cache for 24 hours
        
        # Custom terminology name for AWS Translate
        self.terminology_name = "rise-agricultural-terms"
        
        logger.info(f"Translation tools initialized in region {region} with caching: {enable_caching}")
    
    def _get_cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate cache key for translation"""
        content = f"{text}:{source_lang}:{target_lang}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """Retrieve translation from cache if available and not expired"""
        if not self.enable_caching:
            return None
        
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            if datetime.now() < cached_item['expires_at']:
                logger.debug(f"Cache hit for key {cache_key}")
                return cached_item['translation']
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
                logger.debug(f"Cache expired for key {cache_key}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, translation: str):
        """Save translation to cache"""
        if not self.enable_caching:
            return
        
        self.cache[cache_key] = {
            'translation': translation,
            'cached_at': datetime.now(),
            'expires_at': datetime.now() + self.cache_ttl
        }
        logger.debug(f"Cached translation for key {cache_key}")
    
    def translate_text(self,
                      text: str,
                      target_language: str,
                      source_language: str = 'auto',
                      use_terminology: bool = True,
                      preserve_formatting: bool = True) -> Dict[str, Any]:
        """
        Translate text to target language using AWS Translate
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'hi', 'ta')
            source_language: Source language code or 'auto' for auto-detection
            use_terminology: Use custom agricultural terminology
            preserve_formatting: Preserve text formatting (newlines, etc.)
        
        Returns:
            Dict with translated text and metadata
        """
        try:
            # Validate target language
            if target_language not in self.language_codes:
                return {
                    'success': False,
                    'error': f'Unsupported target language: {target_language}'
                }
            
            # Check cache first
            if source_language != 'auto':
                cache_key = self._get_cache_key(text, source_language, target_language)
                cached_translation = self._get_from_cache(cache_key)
                if cached_translation:
                    return {
                        'success': True,
                        'translated_text': cached_translation,
                        'source_language': source_language,
                        'target_language': target_language,
                        'from_cache': True
                    }
            
            # Prepare translation parameters
            translate_params = {
                'Text': text,
                'TargetLanguageCode': self.language_codes[target_language]['translate']
            }
            
            # Set source language
            if source_language == 'auto':
                translate_params['SourceLanguageCode'] = 'auto'
            elif source_language in self.language_codes:
                translate_params['SourceLanguageCode'] = self.language_codes[source_language]['translate']
            else:
                return {
                    'success': False,
                    'error': f'Unsupported source language: {source_language}'
                }
            
            # Add custom terminology if available and requested
            if use_terminology:
                try:
                    # Check if terminology exists
                    self.translate_client.get_terminology(Name=self.terminology_name)
                    translate_params['TerminologyNames'] = [self.terminology_name]
                except self.translate_client.exceptions.ResourceNotFoundException:
                    logger.warning(f"Custom terminology '{self.terminology_name}' not found, proceeding without it")
            
            # Perform translation
            response = self.translate_client.translate_text(**translate_params)
            
            translated_text = response['TranslatedText']
            detected_source_lang = response.get('SourceLanguageCode', source_language)
            
            # Map back to our language codes
            source_lang_code = self._map_aws_lang_to_code(detected_source_lang)
            
            # Cache the result
            if source_language != 'auto':
                cache_key = self._get_cache_key(text, source_lang_code, target_language)
                self._save_to_cache(cache_key, translated_text)
            
            return {
                'success': True,
                'translated_text': translated_text,
                'source_language': source_lang_code,
                'target_language': target_language,
                'source_language_name': self.language_codes.get(source_lang_code, {}).get('name', 'Unknown'),
                'target_language_name': self.language_codes[target_language]['name'],
                'from_cache': False,
                'terminology_used': use_terminology and 'TerminologyNames' in translate_params
            }
        
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _map_aws_lang_to_code(self, aws_lang: str) -> str:
        """Map AWS Translate language code to our language code"""
        for code, langs in self.language_codes.items():
            if langs['translate'] == aws_lang:
                return code
        return 'en'  # Default to English
    
    def translate_with_fallback(self,
                               text: str,
                               target_language: str,
                               source_language: str = 'auto',
                               fallback_language: str = 'hi') -> Dict[str, Any]:
        """
        Translate text with fallback to Hindi if translation fails
        
        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code or 'auto'
            fallback_language: Fallback language (default: Hindi)
        
        Returns:
            Dict with translated text and metadata
        """
        # Try primary translation
        result = self.translate_text(text, target_language, source_language)
        
        if result['success']:
            return result
        
        # If failed and target is not fallback language, try fallback
        if target_language != fallback_language:
            logger.warning(f"Translation to {target_language} failed, falling back to {fallback_language}")
            fallback_result = self.translate_text(text, fallback_language, source_language)
            
            if fallback_result['success']:
                fallback_result['fallback_used'] = True
                fallback_result['original_target'] = target_language
                return fallback_result
        
        # If all fails, return original text
        return {
            'success': False,
            'translated_text': text,
            'source_language': source_language,
            'target_language': target_language,
            'error': 'Translation failed, returning original text',
            'fallback_used': False
        }
    
    def translate_with_context(self,
                              text: str,
                              target_language: str,
                              context: Optional[Dict[str, Any]] = None,
                              source_language: str = 'auto') -> Dict[str, Any]:
        """
        Context-aware translation with cultural adaptation
        
        Args:
            text: Text to translate
            target_language: Target language code
            context: Context information (crop type, region, farming practice)
            source_language: Source language code or 'auto'
        
        Returns:
            Dict with translated text and metadata
        """
        # Perform base translation
        result = self.translate_text(text, target_language, source_language)
        
        if not result['success']:
            return result
        
        # Apply cultural adaptations based on context
        if context:
            translated_text = result['translated_text']
            
            # Example: Adapt measurements based on region
            if context.get('region') and context.get('adapt_measurements'):
                # This is a placeholder for cultural adaptation logic
                # In production, this would include region-specific adaptations
                logger.debug(f"Applied cultural adaptation for region: {context.get('region')}")
            
            # Example: Adapt crop names to local varieties
            if context.get('crop_type'):
                # This is a placeholder for crop name adaptation
                logger.debug(f"Applied crop adaptation for: {context.get('crop_type')}")
            
            result['context_adapted'] = True
            result['context_used'] = context
        
        return result
    
    def batch_translate(self,
                       texts: List[str],
                       target_language: str,
                       source_language: str = 'auto') -> Dict[str, Any]:
        """
        Translate multiple texts in batch
        
        Args:
            texts: List of texts to translate
            target_language: Target language code
            source_language: Source language code or 'auto'
        
        Returns:
            Dict with list of translations and metadata
        """
        try:
            translations = []
            errors = []
            
            for i, text in enumerate(texts):
                result = self.translate_text(text, target_language, source_language)
                
                if result['success']:
                    translations.append({
                        'index': i,
                        'original': text,
                        'translated': result['translated_text'],
                        'from_cache': result.get('from_cache', False)
                    })
                else:
                    errors.append({
                        'index': i,
                        'original': text,
                        'error': result.get('error', 'Unknown error')
                    })
            
            return {
                'success': len(errors) == 0,
                'translations': translations,
                'errors': errors,
                'total_count': len(texts),
                'success_count': len(translations),
                'error_count': len(errors),
                'target_language': target_language
            }
        
        except Exception as e:
            logger.error(f"Batch translation error: {e}")
            return {
                'success': False,
                'error': str(e),
                'translations': [],
                'errors': []
            }
    
    def create_custom_terminology(self,
                                 terminology_data: Dict[str, Dict[str, str]],
                                 s3_bucket: str = 'rise-application-data') -> Dict[str, Any]:
        """
        Create or update custom terminology for agricultural terms
        
        Args:
            terminology_data: Dictionary mapping source terms to target translations
                             Format: {'en': {'term1': 'term1'}, 'hi': {'term1': 'अनुवाद1'}}
            s3_bucket: S3 bucket for terminology file storage
        
        Returns:
            Dict with creation status
        """
        try:
            # Prepare terminology file in CSV format
            # Format: en,hi,ta,te,...
            #         term1,अनुवाद1,மொழிபெயர்ப்பு1,...
            
            languages = list(terminology_data.keys())
            terms = list(terminology_data[languages[0]].keys())
            
            # Build CSV content
            csv_lines = [','.join(languages)]  # Header
            
            for term in terms:
                row = []
                for lang in languages:
                    translation = terminology_data[lang].get(term, term)
                    row.append(translation)
                csv_lines.append(','.join(row))
            
            csv_content = '\n'.join(csv_lines)
            
            # Upload to S3
            s3_key = f"terminology/{self.terminology_name}.csv"
            self.s3_client.put_object(
                Bucket=s3_bucket,
                Key=s3_key,
                Body=csv_content.encode('utf-8'),
                ContentType='text/csv'
            )
            
            terminology_s3_uri = f"s3://{s3_bucket}/{s3_key}"
            
            # Import terminology to AWS Translate
            try:
                # Try to delete existing terminology first
                self.translate_client.delete_terminology(Name=self.terminology_name)
                logger.info(f"Deleted existing terminology: {self.terminology_name}")
            except self.translate_client.exceptions.ResourceNotFoundException:
                pass
            
            # Import new terminology
            response = self.translate_client.import_terminology(
                Name=self.terminology_name,
                MergeStrategy='OVERWRITE',
                TerminologyData={
                    'File': csv_content.encode('utf-8'),
                    'Format': 'CSV'
                }
            )
            
            return {
                'success': True,
                'terminology_name': self.terminology_name,
                'term_count': response['TerminologyProperties']['TermCount'],
                'source_language': response['TerminologyProperties']['SourceLanguageCode'],
                'target_languages': response['TerminologyProperties']['TargetLanguageCodes'],
                's3_uri': terminology_s3_uri
            }
        
        except Exception as e:
            logger.error(f"Custom terminology creation error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_language_preference(self, user_id: str) -> str:
        """
        Get user's language preference (placeholder for DynamoDB integration)
        
        Args:
            user_id: User identifier
        
        Returns:
            Language code
        """
        # TODO: Integrate with DynamoDB UserProfiles table
        # For now, return default
        return 'hi'  # Default to Hindi
    
    def set_language_preference(self, user_id: str, language_code: str) -> Dict[str, Any]:
        """
        Set user's language preference (placeholder for DynamoDB integration)
        
        Args:
            user_id: User identifier
            language_code: Preferred language code
        
        Returns:
            Dict with success status
        """
        # TODO: Integrate with DynamoDB UserProfiles table
        if language_code not in self.language_codes:
            return {
                'success': False,
                'error': f'Unsupported language: {language_code}'
            }
        
        # Placeholder - would save to DynamoDB
        logger.info(f"Language preference for user {user_id} set to {language_code}")
        
        return {
            'success': True,
            'user_id': user_id,
            'language_code': language_code,
            'language_name': self.language_codes[language_code]['name']
        }
    
    def clear_cache(self):
        """Clear translation cache"""
        self.cache.clear()
        logger.info("Translation cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache)
        expired_entries = sum(1 for item in self.cache.values() if datetime.now() >= item['expires_at'])
        
        return {
            'enabled': self.enable_caching,
            'total_entries': total_entries,
            'active_entries': total_entries - expired_entries,
            'expired_entries': expired_entries,
            'ttl_hours': self.cache_ttl.total_seconds() / 3600
        }


# Strands @tool decorator functions for agent integration

def create_translation_tools(region: str = "us-east-1", enable_caching: bool = True) -> TranslationTools:
    """
    Factory function to create translation tools instance
    
    Args:
        region: AWS region
        enable_caching: Enable translation caching
    
    Returns:
        TranslationTools instance
    """
    return TranslationTools(region=region, enable_caching=enable_caching)


# Tool functions for Strands agent integration

def translate_tool(text: str, target_language: str, source_language: str = 'auto') -> str:
    """
    Tool for translating text to target language
    
    Args:
        text: Text to translate
        target_language: Target language code (hi, ta, te, etc.)
        source_language: Source language code or 'auto'
    
    Returns:
        Translated text or error message
    """
    tools = create_translation_tools()
    result = tools.translate_text(text, target_language, source_language)
    
    if result['success']:
        return result['translated_text']
    else:
        return f"Error: {result.get('error', 'Translation failed')}"


def translate_with_fallback_tool(text: str, target_language: str, source_language: str = 'auto') -> str:
    """
    Tool for translating text with Hindi fallback
    
    Args:
        text: Text to translate
        target_language: Target language code
        source_language: Source language code or 'auto'
    
    Returns:
        Translated text or error message
    """
    tools = create_translation_tools()
    result = tools.translate_with_fallback(text, target_language, source_language)
    
    if result['success']:
        fallback_note = " (Hindi fallback used)" if result.get('fallback_used') else ""
        return result['translated_text'] + fallback_note
    else:
        return f"Error: {result.get('error', 'Translation failed')}"


def context_aware_translate_tool(text: str, 
                                 target_language: str, 
                                 crop_type: Optional[str] = None,
                                 region: Optional[str] = None) -> str:
    """
    Tool for context-aware translation with cultural adaptation
    
    Args:
        text: Text to translate
        target_language: Target language code
        crop_type: Type of crop for context
        region: Region for cultural adaptation
    
    Returns:
        Translated text with cultural adaptations
    """
    tools = create_translation_tools()
    
    context = {}
    if crop_type:
        context['crop_type'] = crop_type
    if region:
        context['region'] = region
        context['adapt_measurements'] = True
    
    result = tools.translate_with_context(text, target_language, context)
    
    if result['success']:
        return result['translated_text']
    else:
        return f"Error: {result.get('error', 'Translation failed')}"


def batch_translate_tool(texts: List[str], target_language: str) -> str:
    """
    Tool for batch translation of multiple texts
    
    Args:
        texts: List of texts to translate
        target_language: Target language code
    
    Returns:
        JSON string with translations
    """
    tools = create_translation_tools()
    result = tools.batch_translate(texts, target_language)
    
    if result['success']:
        return json.dumps({
            'translations': [t['translated'] for t in result['translations']],
            'count': result['success_count']
        })
    else:
        return f"Error: {result.get('error', 'Batch translation failed')}"
