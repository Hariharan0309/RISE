"""
RISE Translation Tools Integration Example
Demonstrates how to use translation tools with the RISE farming assistant
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.translation_tools import (
    TranslationTools,
    translate_tool,
    translate_with_fallback_tool,
    context_aware_translate_tool,
    batch_translate_tool
)
import json


def example_basic_translation():
    """Example 1: Basic text translation"""
    print("=" * 60)
    print("Example 1: Basic Translation")
    print("=" * 60)
    
    tools = TranslationTools(region='us-east-1', enable_caching=True)
    
    # English to Hindi
    result = tools.translate_text(
        text="Your crop looks healthy and ready for harvest",
        target_language="hi",
        source_language="en"
    )
    
    if result['success']:
        print(f"Original (English): Your crop looks healthy and ready for harvest")
        print(f"Translated (Hindi): {result['translated_text']}")
        print(f"From cache: {result['from_cache']}")
    else:
        print(f"Error: {result['error']}")
    
    print()


def example_auto_language_detection():
    """Example 2: Automatic language detection"""
    print("=" * 60)
    print("Example 2: Auto Language Detection")
    print("=" * 60)
    
    tools = TranslationTools(region='us-east-1')
    
    # Auto-detect source language
    result = tools.translate_text(
        text="मेरी फसल में कीड़े लग गए हैं",
        target_language="en",
        source_language="auto"
    )
    
    if result['success']:
        print(f"Original: मेरी फसल में कीड़े लग गए हैं")
        print(f"Detected language: {result['source_language_name']}")
        print(f"Translated: {result['translated_text']}")
    
    print()


def example_fallback_translation():
    """Example 3: Translation with fallback"""
    print("=" * 60)
    print("Example 3: Translation with Fallback")
    print("=" * 60)
    
    tools = TranslationTools(region='us-east-1')
    
    # Try Tamil, fallback to Hindi if fails
    result = tools.translate_with_fallback(
        text="Apply organic fertilizer to improve soil health",
        target_language="ta",
        source_language="en",
        fallback_language="hi"
    )
    
    if result['success']:
        print(f"Original: Apply organic fertilizer to improve soil health")
        print(f"Target language: {result['target_language']}")
        print(f"Translated: {result['translated_text']}")
        if result.get('fallback_used'):
            print(f"Note: Fallback to {result['target_language']} was used")
    
    print()


def example_context_aware_translation():
    """Example 4: Context-aware translation"""
    print("=" * 60)
    print("Example 4: Context-Aware Translation")
    print("=" * 60)
    
    tools = TranslationTools(region='us-east-1')
    
    # Translation with agricultural context
    context = {
        'crop_type': 'rice',
        'region': 'punjab',
        'farming_practice': 'organic',
        'adapt_measurements': True
    }
    
    result = tools.translate_with_context(
        text="Plant rice seeds at 20cm spacing with proper irrigation",
        target_language="hi",
        context=context,
        source_language="en"
    )
    
    if result['success']:
        print(f"Original: Plant rice seeds at 20cm spacing with proper irrigation")
        print(f"Context: {context}")
        print(f"Translated: {result['translated_text']}")
        print(f"Context adapted: {result.get('context_adapted', False)}")
    
    print()


def example_batch_translation():
    """Example 5: Batch translation"""
    print("=" * 60)
    print("Example 5: Batch Translation")
    print("=" * 60)
    
    tools = TranslationTools(region='us-east-1')
    
    # Translate multiple farming tips
    farming_tips = [
        "Water your crops early in the morning",
        "Check soil moisture before irrigation",
        "Remove weeds regularly to prevent competition",
        "Apply fertilizer based on soil test results",
        "Monitor crops for pest and disease symptoms"
    ]
    
    result = tools.batch_translate(
        texts=farming_tips,
        target_language="hi",
        source_language="en"
    )
    
    if result['success']:
        print(f"Translated {result['success_count']} out of {result['total_count']} tips:")
        print()
        for translation in result['translations']:
            print(f"EN: {translation['original']}")
            print(f"HI: {translation['translated']}")
            print()
    
    print()


def example_multilingual_conversation():
    """Example 6: Multilingual conversation flow"""
    print("=" * 60)
    print("Example 6: Multilingual Conversation")
    print("=" * 60)
    
    tools = TranslationTools(region='us-east-1')
    
    # Simulate a conversation in multiple languages
    conversation = [
        {"speaker": "Farmer", "language": "hi", "text": "नमस्ते, मुझे अपनी फसल के बारे में सलाह चाहिए"},
        {"speaker": "Assistant", "language": "en", "text": "Hello! I'd be happy to help with your crop. What crop are you growing?"},
        {"speaker": "Farmer", "language": "hi", "text": "मैं गेहूं उगा रहा हूं"},
        {"speaker": "Assistant", "language": "en", "text": "Great! Wheat is an important crop. What specific advice do you need?"}
    ]
    
    print("Conversation with translations:")
    print()
    
    for message in conversation:
        print(f"{message['speaker']} ({message['language'].upper()}): {message['text']}")
        
        # Translate to opposite language
        target_lang = "en" if message['language'] == "hi" else "hi"
        result = tools.translate_text(
            text=message['text'],
            target_language=target_lang,
            source_language=message['language']
        )
        
        if result['success']:
            print(f"  → Translation ({target_lang.upper()}): {result['translated_text']}")
        print()
    
    print()


def example_agricultural_terminology():
    """Example 7: Agricultural terminology translation"""
    print("=" * 60)
    print("Example 7: Agricultural Terminology")
    print("=" * 60)
    
    tools = TranslationTools(region='us-east-1')
    
    # Agricultural terms that need accurate translation
    agricultural_texts = [
        "Apply NPK fertilizer at 120:60:40 kg/ha",
        "Use integrated pest management techniques",
        "Maintain soil pH between 6.0 and 7.5",
        "Practice crop rotation to improve soil health",
        "Implement drip irrigation for water efficiency"
    ]
    
    print("Translating agricultural advice to Hindi:")
    print()
    
    for text in agricultural_texts:
        result = tools.translate_text(
            text=text,
            target_language="hi",
            source_language="en",
            use_terminology=True
        )
        
        if result['success']:
            print(f"EN: {text}")
            print(f"HI: {result['translated_text']}")
            print(f"Terminology used: {result.get('terminology_used', False)}")
            print()
    
    print()


def example_caching_performance():
    """Example 8: Translation caching performance"""
    print("=" * 60)
    print("Example 8: Caching Performance")
    print("=" * 60)
    
    tools = TranslationTools(region='us-east-1', enable_caching=True)
    
    text = "Check your crop for signs of disease"
    
    # First translation (cache miss)
    print("First translation (cache miss):")
    result1 = tools.translate_text(text, "hi", "en")
    print(f"From cache: {result1.get('from_cache', False)}")
    
    # Second translation (cache hit)
    print("\nSecond translation (cache hit):")
    result2 = tools.translate_text(text, "hi", "en")
    print(f"From cache: {result2.get('from_cache', False)}")
    
    # Cache statistics
    stats = tools.get_cache_stats()
    print(f"\nCache statistics:")
    print(f"  Enabled: {stats['enabled']}")
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  Active entries: {stats['active_entries']}")
    print(f"  TTL: {stats['ttl_hours']} hours")
    
    print()


def example_strands_tool_functions():
    """Example 9: Using Strands tool functions"""
    print("=" * 60)
    print("Example 9: Strands Tool Functions")
    print("=" * 60)
    
    # Simple translation tool
    print("1. Simple translation:")
    result = translate_tool("Good morning, farmer", "hi", "en")
    print(f"   Result: {result}")
    
    # Translation with fallback
    print("\n2. Translation with fallback:")
    result = translate_with_fallback_tool("How is your harvest?", "ta", "en")
    print(f"   Result: {result}")
    
    # Context-aware translation
    print("\n3. Context-aware translation:")
    result = context_aware_translate_tool(
        text="Apply fertilizer in the morning",
        target_language="hi",
        crop_type="wheat",
        region="punjab"
    )
    print(f"   Result: {result}")
    
    # Batch translation
    print("\n4. Batch translation:")
    result = batch_translate_tool(
        texts=["Hello", "Thank you", "Goodbye"],
        target_language="hi"
    )
    result_data = json.loads(result)
    print(f"   Translations: {result_data['translations']}")
    print(f"   Count: {result_data['count']}")
    
    print()


def example_language_preference():
    """Example 10: Language preference management"""
    print("=" * 60)
    print("Example 10: Language Preference Management")
    print("=" * 60)
    
    tools = TranslationTools(region='us-east-1')
    
    user_id = "farmer_12345"
    
    # Get current preference
    current_lang = tools.get_language_preference(user_id)
    print(f"Current language preference: {current_lang}")
    
    # Set new preference
    result = tools.set_language_preference(user_id, "ta")
    if result['success']:
        print(f"Updated language preference to: {result['language_name']} ({result['language_code']})")
    
    # Try to set invalid language
    result = tools.set_language_preference(user_id, "fr")
    if not result['success']:
        print(f"Error setting invalid language: {result['error']}")
    
    print()


def example_error_handling():
    """Example 11: Error handling"""
    print("=" * 60)
    print("Example 11: Error Handling")
    print("=" * 60)
    
    tools = TranslationTools(region='us-east-1')
    
    # Try unsupported language
    print("1. Unsupported target language:")
    result = tools.translate_text("Hello", "fr", "en")
    if not result['success']:
        print(f"   Error: {result['error']}")
    
    # Try unsupported source language
    print("\n2. Unsupported source language:")
    result = tools.translate_text("Hello", "hi", "de")
    if not result['success']:
        print(f"   Error: {result['error']}")
    
    # Empty text
    print("\n3. Empty text handling:")
    result = tools.translate_text("", "hi", "en")
    print(f"   Success: {result['success']}")
    
    print()


def main():
    """Run all examples"""
    print("\n")
    print("*" * 60)
    print("RISE Translation Tools - Integration Examples")
    print("*" * 60)
    print("\n")
    
    examples = [
        ("Basic Translation", example_basic_translation),
        ("Auto Language Detection", example_auto_language_detection),
        ("Fallback Translation", example_fallback_translation),
        ("Context-Aware Translation", example_context_aware_translation),
        ("Batch Translation", example_batch_translation),
        ("Multilingual Conversation", example_multilingual_conversation),
        ("Agricultural Terminology", example_agricultural_terminology),
        ("Caching Performance", example_caching_performance),
        ("Strands Tool Functions", example_strands_tool_functions),
        ("Language Preference", example_language_preference),
        ("Error Handling", example_error_handling)
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        try:
            func()
        except Exception as e:
            print(f"Error in {name}: {e}")
            print()
    
    print("*" * 60)
    print("All examples completed!")
    print("*" * 60)


if __name__ == "__main__":
    # Note: These examples use mocked AWS services for demonstration
    # In production, ensure AWS credentials are configured
    print("\nNote: These examples demonstrate the API usage.")
    print("For actual translation, configure AWS credentials and services.\n")
    
    # Uncomment to run examples
    # main()
    
    print("Examples are ready to run. Uncomment main() to execute.")
