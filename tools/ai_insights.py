"""
RISE Shared AI Insights
Single place to call Bedrock for short, helpful AI-generated insights across features.
"""

import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def get_ai_insight(prompt: str, max_tokens: int = 650, temperature: float = 0.3) -> Dict[str, Any]:
    """
    Call Bedrock to generate a short, helpful text response. Use for AI insights
    across Market Prices, Loan, Schemes, Equipment, Buyer, Buying Groups, etc.
    
    Returns:
        {'success': True, 'text': str} or {'success': False, 'error': str}
    """
    try:
        import boto3
        from config import Config
        client = boto3.client('bedrock-runtime', region_name=getattr(Config, 'BEDROCK_REGION', 'us-east-1'))
        model_id = Config.BEDROCK_MODEL_ID
        body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': max_tokens,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': temperature,
        }
        response = client.invoke_model(modelId=model_id, body=json.dumps(body))
        response_body = json.loads(response['body'].read())
        text = response_body['content'][0]['text'].strip()
        return {'success': True, 'text': text}
    except Exception as e:
        logger.error(f"AI insight error: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}
