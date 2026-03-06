"""
RISE Optimized Lambda Function Example
Demonstrates network optimization techniques for rural connectivity
"""

import json
import boto3
import os
from typing import Dict, Any
import sys

# Add infrastructure to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from network_optimization import NetworkOptimizer
from image_optimizer import ImageProcessor, S3ImageOptimizer
from batch_request_handler import BatchRequestHandler


# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Initialize optimizers
network_optimizer = NetworkOptimizer()
image_optimizer = S3ImageOptimizer(s3_client=s3_client)
batch_handler = BatchRequestHandler()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler with network optimization
    
    Args:
        event: Lambda event
        context: Lambda context
    
    Returns:
        Optimized Lambda response
    """
    
    # Get request path and method
    path = event.get('path', '')
    method = event.get('httpMethod', 'GET')
    
    # Get network type from headers (sent by client)
    headers = event.get('headers', {})
    network_type = headers.get('X-Network-Type', '3g')
    
    # Route to appropriate handler
    if path == '/api/v1/optimize/image':
        return handle_image_optimization(event, network_type)
    elif path == '/api/v1/batch':
        return handle_batch_request(event, network_type)
    elif path == '/api/v1/data/weather':
        return handle_weather_request(event, network_type)
    else:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Not found'})
        }


def handle_image_optimization(event: Dict[str, Any], network_type: str) -> Dict[str, Any]:
    """
    Handle image optimization request
    
    Args:
        event: Lambda event
        network_type: Detected network type
    
    Returns:
        Optimized response with image URLs
    """
    try:
        body = json.loads(event.get('body', '{}'))
        image_s3_key = body.get('image_key')
        
        if not image_s3_key:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'image_key required'})
            }
        
        # Get image from S3
        bucket_name = os.environ.get('S3_BUCKET_NAME')
        response = s3_client.get_object(Bucket=bucket_name, Key=image_s3_key)
        image_data = response['Body'].read()
        
        # Optimize and upload versions
        result = image_optimizer.optimize_and_upload(
            image_data=image_data,
            s3_key=image_s3_key,
            network_type=network_type
        )
        
        # Get adaptive config
        config = network_optimizer.get_adaptive_config(network_type)
        
        # Return optimized response
        response_data = {
            'success': True,
            'network_type': network_type,
            'adaptive_config': config,
            'image_versions': result['versions'],
            'placeholder': result['placeholder']
        }
        
        # Compress response if needed
        if config['enable_compression']:
            return network_optimizer.create_compressed_lambda_response(
                response_data,
                compression_level=config['compression_level']
            )
        else:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(response_data)
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handle_batch_request(event: Dict[str, Any], network_type: str) -> Dict[str, Any]:
    """
    Handle batched API requests
    
    Args:
        event: Lambda event
        network_type: Detected network type
    
    Returns:
        Batched response
    """
    try:
        body = json.loads(event.get('body', '{}'))
        batch_request = body
        
        # Define handler map for different endpoints
        handler_map = {
            'weather': get_weather_data,
            'market_prices': get_market_prices,
            'schemes': get_government_schemes,
            'forum_posts': get_forum_posts
        }
        
        # Process batch
        batch_response = batch_handler.process_batch(batch_request, handler_map)
        
        # Get adaptive config
        config = network_optimizer.get_adaptive_config(network_type)
        
        # Compress response if needed
        if config['enable_compression']:
            return network_optimizer.create_compressed_lambda_response(
                batch_response,
                compression_level=config['compression_level']
            )
        else:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(batch_response)
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handle_weather_request(event: Dict[str, Any], network_type: str) -> Dict[str, Any]:
    """
    Handle weather data request with optimization
    
    Args:
        event: Lambda event
        network_type: Detected network type
    
    Returns:
        Optimized weather response
    """
    try:
        params = event.get('queryStringParameters', {})
        location = params.get('location')
        
        if not location:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'location required'})
            }
        
        # Get weather data
        weather_data = get_weather_data(location=location)
        
        # Get adaptive config
        config = network_optimizer.get_adaptive_config(network_type)
        
        # Reduce data for slow networks
        if network_type in ['2g', 'slow-2g']:
            # Return only essential data
            weather_data = {
                'location': weather_data.get('location'),
                'temperature': weather_data.get('temperature'),
                'condition': weather_data.get('condition'),
                'rainfall_probability': weather_data.get('rainfall_probability')
            }
        
        # Compress response if needed
        if config['enable_compression']:
            return network_optimizer.create_compressed_lambda_response(
                weather_data,
                compression_level=config['compression_level']
            )
        else:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Cache-Control': 'public, max-age=3600'
                },
                'body': json.dumps(weather_data)
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


# Mock handler functions (replace with actual implementations)

def get_weather_data(location: str) -> Dict[str, Any]:
    """Get weather data for location"""
    return {
        'location': location,
        'temperature': 28,
        'condition': 'Partly Cloudy',
        'humidity': 65,
        'wind_speed': 12,
        'rainfall_probability': 30,
        'forecast': [
            {'day': 'Today', 'temp': 28, 'condition': 'Partly Cloudy'},
            {'day': 'Tomorrow', 'temp': 30, 'condition': 'Sunny'},
            {'day': 'Day 3', 'temp': 27, 'condition': 'Rainy'}
        ]
    }


def get_market_prices(crop: str, location: str) -> Dict[str, Any]:
    """Get market prices for crop"""
    return {
        'crop': crop,
        'location': location,
        'current_price': 2500,
        'unit': 'per quintal',
        'trend': 'up',
        'change_percent': 5.2
    }


def get_government_schemes(user_id: str) -> Dict[str, Any]:
    """Get applicable government schemes"""
    return {
        'user_id': user_id,
        'schemes': [
            {
                'name': 'PM-KISAN',
                'eligible': True,
                'benefit': '₹6000/year'
            },
            {
                'name': 'Soil Health Card',
                'eligible': True,
                'benefit': 'Free soil testing'
            }
        ]
    }


def get_forum_posts(limit: int = 10) -> Dict[str, Any]:
    """Get recent forum posts"""
    return {
        'posts': [
            {
                'id': 'post1',
                'title': 'Best practices for wheat cultivation',
                'author': 'Farmer123',
                'replies': 5
            },
            {
                'id': 'post2',
                'title': 'Dealing with pest infestation',
                'author': 'Farmer456',
                'replies': 8
            }
        ],
        'total': 2
    }


# Export handler
__all__ = ['lambda_handler']
