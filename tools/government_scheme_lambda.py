"""
RISE Government Scheme Lambda Function
AWS Lambda handler for government scheme operations
"""

import json
import logging
import os
from typing import Dict, Any
from government_scheme_tools import GovernmentSchemeTools

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize government scheme tools
scheme_tools = GovernmentSchemeTools(
    region=os.environ.get('AWS_REGION', 'us-east-1')
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for government scheme requests
    
    Event structure:
    {
        "action": "search" | "get_details" | "ingest" | "update_status" | "scrape" | "monitor",
        "state": str (optional, for search),
        "category": str (optional, for search),
        "scheme_type": str (optional, for search),
        "scheme_id": str (for get_details, update_status),
        "status": str (for update_status),
        "scheme_data": dict (for ingest),
        "source": str (optional, for scrape)
    }
    
    Returns:
        API Gateway response with scheme data
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'search')
        
        logger.info(f"Government scheme request: action={action}")
        
        # Route to appropriate handler
        if action == 'search':
            result = handle_search(body)
        elif action == 'get_details':
            result = handle_get_details(body)
        elif action == 'ingest':
            result = handle_ingest(body)
        elif action == 'update_status':
            result = handle_update_status(body)
        elif action == 'scrape':
            result = handle_scrape(body)
        elif action == 'monitor':
            result = handle_monitor(body)
        else:
            return error_response(400, f'Invalid action: {action}')
        
        # Return response
        status_code = 200 if result.get('success') else 500
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result, default=str)
        }
    
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return error_response(400, f'Invalid input: {str(e)}')
    
    except Exception as e:
        logger.error(f"Lambda error: {e}", exc_info=True)
        return error_response(500, 'Internal server error')


def handle_search(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle scheme search request"""
    try:
        state = body.get('state')
        category = body.get('category')
        scheme_type = body.get('scheme_type')
        active_only = body.get('active_only', True)
        
        result = scheme_tools.search_schemes(
            state=state,
            category=category,
            scheme_type=scheme_type,
            active_only=active_only
        )
        
        logger.info(f"Scheme search completed: found {result.get('count', 0)} schemes")
        return result
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_get_details(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get scheme details request"""
    try:
        scheme_id = body.get('scheme_id')
        
        if not scheme_id:
            return {
                'success': False,
                'error': 'scheme_id is required'
            }
        
        result = scheme_tools.get_scheme_details(scheme_id)
        logger.info(f"Scheme details retrieved: {scheme_id}")
        return result
    
    except Exception as e:
        logger.error(f"Get details error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_ingest(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle scheme data ingestion request"""
    try:
        scheme_data = body.get('scheme_data')
        
        if not scheme_data:
            return {
                'success': False,
                'error': 'scheme_data is required'
            }
        
        result = scheme_tools.ingest_scheme_data(scheme_data)
        logger.info(f"Scheme ingestion completed: {result.get('scheme_id', 'unknown')}")
        return result
    
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_update_status(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle scheme status update request"""
    try:
        scheme_id = body.get('scheme_id')
        status = body.get('status')
        
        if not scheme_id or not status:
            return {
                'success': False,
                'error': 'scheme_id and status are required'
            }
        
        result = scheme_tools.update_scheme_status(scheme_id, status)
        logger.info(f"Scheme status updated: {scheme_id} -> {status}")
        return result
    
    except Exception as e:
        logger.error(f"Update status error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_scrape(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle scheme data scraping request"""
    try:
        source = body.get('source', 'all')
        
        result = scheme_tools.scrape_government_schemes(source)
        logger.info(f"Scheme scraping completed: {result.get('ingested_count', 0)} schemes ingested")
        return result
    
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_monitor(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle scheme monitoring request"""
    try:
        result = scheme_tools.monitor_scheme_updates()
        logger.info(f"Scheme monitoring completed: {result.get('total_schemes_monitored', 0)} schemes checked")
        return result
    
    except Exception as e:
        logger.error(f"Monitoring error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Generate error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'success': False,
            'error': message
        })
    }


# For local testing
if __name__ == '__main__':
    # Test event for search
    test_event = {
        'action': 'search',
        'category': 'subsidies',
        'active_only': True
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test event for scraping
    test_event2 = {
        'action': 'scrape',
        'source': 'all'
    }
    
    result2 = lambda_handler(test_event2, None)
    print("\n" + "="*50 + "\n")
    print(json.dumps(json.loads(result2['body']), indent=2))
    
    # Test event for monitoring
    test_event3 = {
        'action': 'monitor'
    }
    
    result3 = lambda_handler(test_event3, None)
    print("\n" + "="*50 + "\n")
    print(json.dumps(json.loads(result3['body']), indent=2))
