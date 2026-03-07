"""
RISE Market Price Tracking Tools
Tools for fetching, aggregating, and analyzing market prices with location-based retrieval
"""

import boto3
import logging
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
import os
from decimal import Decimal

logger = logging.getLogger(__name__)


class MarketPriceTools:
    """Market price tracking tools for RISE farming assistant"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize market price tools with AWS clients
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # DynamoDB table for market price storage
        self.price_table = self.dynamodb.Table('RISE-MarketPrices')
        
        # API endpoints for market data
        # Note: In production, integrate with actual government APIs
        # Examples: data.gov.in, agmarknet.gov.in
        self.api_endpoints = {
            'agmarknet': os.getenv('AGMARKNET_API_URL', 'https://api.data.gov.in/resource/'),
            'backup': os.getenv('MARKET_DATA_BACKUP_URL', '')
        }
        
        # Cache TTL: 6 hours for market prices
        self.cache_ttl = timedelta(hours=6)
        
        # Search radius in kilometers
        self.default_radius_km = 50
        
        logger.info(f"Market price tools initialized in region {region}")
    
    def get_current_prices(self,
                          crop_name: str,
                          latitude: float,
                          longitude: float,
                          radius_km: int = 50) -> Dict[str, Any]:
        """
        Get current market prices for a crop within specified radius
        
        Args:
            crop_name: Name of the crop
            latitude: Location latitude
            longitude: Location longitude
            radius_km: Search radius in kilometers (default 50km)
        
        Returns:
            Dict with current market prices from multiple markets
        """
        try:
            # Normalize crop name
            crop_name = crop_name.lower().strip()
            
            # Check cache first
            cache_key = self._get_cache_key(crop_name, latitude, longitude, radius_km)
            cached_data = self._get_from_cache(cache_key)
            
            if cached_data:
                logger.info(f"Cache hit for {crop_name} prices at ({latitude}, {longitude})")
                return {
                    'success': True,
                    'from_cache': True,
                    **cached_data
                }
            
            # Fetch from market data sources
            market_prices = self._fetch_market_prices(crop_name, latitude, longitude, radius_km)
            
            if not market_prices:
                return {
                    'success': False,
                    'error': f'No market data found for {crop_name} within {radius_km}km'
                }
            
            # Calculate statistics
            prices = [m['price'] for m in market_prices]
            price_data = {
                'crop_name': crop_name,
                'location': {
                    'latitude': latitude,
                    'longitude': longitude,
                    'radius_km': radius_km
                },
                'markets': market_prices,
                'statistics': {
                    'min_price': min(prices),
                    'max_price': max(prices),
                    'avg_price': sum(prices) / len(prices),
                    'market_count': len(market_prices)
                },
                'timestamp': datetime.now().isoformat(),
                'currency': 'INR',
                'unit': 'quintal'  # Standard unit for agricultural commodities
            }
            
            # Cache the result
            self._save_to_cache(cache_key, price_data)
            
            return {
                'success': True,
                'from_cache': False,
                **price_data
            }
        
        except Exception as e:
            logger.error(f"Market price fetch error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_price_history(self,
                         crop_name: str,
                         market_id: str,
                         days: int = 30) -> Dict[str, Any]:
        """
        Get historical price data for a crop at a specific market
        
        Args:
            crop_name: Name of the crop
            market_id: Market identifier
            days: Number of days of history (default 30)
        
        Returns:
            Dict with historical price data
        """
        try:
            crop_name = crop_name.lower().strip()
            
            # Query DynamoDB for historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            history = self._query_price_history(crop_name, market_id, start_date, end_date)
            
            if not history:
                return {
                    'success': False,
                    'error': f'No historical data found for {crop_name} at market {market_id}'
                }
            
            # Calculate trends
            prices = [h['price'] for h in history]
            trend_data = self._calculate_price_trends(prices)
            
            return {
                'success': True,
                'crop_name': crop_name,
                'market_id': market_id,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'history': history,
                'trends': trend_data,
                'currency': 'INR',
                'unit': 'quintal'
            }
        
        except Exception as e:
            logger.error(f"Price history error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def predict_price_trends(self,
                            crop_name: str,
                            market_id: str,
                            forecast_days: int = 7) -> Dict[str, Any]:
        """
        Predict future price trends using basic ML
        
        Args:
            crop_name: Name of the crop
            market_id: Market identifier
            forecast_days: Number of days to forecast
        
        Returns:
            Dict with price predictions
        """
        try:
            # Get 30-day historical data
            history_result = self.get_price_history(crop_name, market_id, 30)
            
            if not history_result['success']:
                return history_result
            
            history = history_result['history']
            
            # Simple moving average prediction
            predictions = self._simple_price_prediction(history, forecast_days)
            
            return {
                'success': True,
                'crop_name': crop_name,
                'market_id': market_id,
                'forecast_days': forecast_days,
                'predictions': predictions,
                'confidence': 'medium',  # Basic ML has medium confidence
                'method': 'moving_average',
                'currency': 'INR',
                'unit': 'quintal'
            }
        
        except Exception as e:
            logger.error(f"Price prediction error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_optimal_selling_time(self,
                                crop_name: str,
                                latitude: float,
                                longitude: float,
                                harvest_date: Optional[str] = None,
                                storage_capacity: bool = True) -> Dict[str, Any]:
        """
        Calculate optimal selling time based on price trends and crop perishability
        
        Args:
            crop_name: Name of the crop
            latitude: Location latitude
            longitude: Location longitude
            harvest_date: Expected harvest date (ISO format)
            storage_capacity: Whether farmer has storage capacity
        
        Returns:
            Dict with optimal selling recommendations
        """
        try:
            crop_name = crop_name.lower().strip()
            
            # Get current prices
            current_prices = self.get_current_prices(crop_name, latitude, longitude)
            
            if not current_prices['success']:
                return current_prices
            
            # Get best market
            best_market = max(current_prices['markets'], key=lambda m: m['price'])
            
            # Get price predictions
            predictions = self.predict_price_trends(crop_name, best_market['market_id'], 14)
            
            # Determine crop perishability
            perishability = self._get_crop_perishability(crop_name)
            
            # Calculate optimal selling time
            recommendation = self._calculate_optimal_selling_time(
                current_prices,
                predictions if predictions['success'] else None,
                perishability,
                storage_capacity,
                harvest_date
            )
            
            return {
                'success': True,
                'crop_name': crop_name,
                'current_best_price': best_market['price'],
                'best_market': best_market,
                'recommendation': recommendation,
                'perishability': perishability,
                'storage_available': storage_capacity
            }
        
        except Exception as e:
            logger.error(f"Optimal selling time error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _fetch_market_prices(self,
                            crop_name: str,
                            latitude: float,
                            longitude: float,
                            radius_km: int) -> List[Dict[str, Any]]:
        """Fetch market prices from data sources"""
        
        # Mock data for demonstration
        # In production, integrate with actual APIs like:
        # - AgMarkNet (https://agmarknet.gov.in/)
        # - data.gov.in agricultural datasets
        # - State agricultural marketing boards
        
        mock_markets = [
            {
                'market_id': 'MKT001',
                'market_name': 'Delhi Azadpur Mandi',
                'location': {
                    'latitude': 28.7041,
                    'longitude': 77.1025,
                    'district': 'Delhi',
                    'state': 'Delhi'
                },
                'distance_km': 15.2,
                'price': 2500,
                'arrival_quantity': 150,
                'last_updated': datetime.now().isoformat()
            },
            {
                'market_id': 'MKT002',
                'market_name': 'Ghaziabad Mandi',
                'location': {
                    'latitude': 28.6692,
                    'longitude': 77.4538,
                    'district': 'Ghaziabad',
                    'state': 'Uttar Pradesh'
                },
                'distance_km': 25.8,
                'price': 2450,
                'arrival_quantity': 120,
                'last_updated': datetime.now().isoformat()
            },
            {
                'market_id': 'MKT003',
                'market_name': 'Noida Sector 1 Mandi',
                'location': {
                    'latitude': 28.5355,
                    'longitude': 77.3910,
                    'district': 'Gautam Buddha Nagar',
                    'state': 'Uttar Pradesh'
                },
                'distance_km': 32.5,
                'price': 2480,
                'arrival_quantity': 90,
                'last_updated': datetime.now().isoformat()
            }
        ]
        
        # Filter by radius
        nearby_markets = [m for m in mock_markets if m['distance_km'] <= radius_km]
        
        # Store in DynamoDB for history
        for market in nearby_markets:
            self._store_price_record(crop_name, market)
        
        return nearby_markets
    
    def _query_price_history(self,
                            crop_name: str,
                            market_id: str,
                            start_date: datetime,
                            end_date: datetime) -> List[Dict[str, Any]]:
        """Query historical price data from DynamoDB"""
        
        try:
            # Query with composite key
            response = self.price_table.query(
                KeyConditionExpression='crop_market_id = :cm AND #ts BETWEEN :start AND :end',
                ExpressionAttributeNames={
                    '#ts': 'timestamp'
                },
                ExpressionAttributeValues={
                    ':cm': f"{crop_name}#{market_id}",
                    ':start': int(start_date.timestamp()),
                    ':end': int(end_date.timestamp())
                }
            )
            
            history = []
            for item in response.get('Items', []):
                history.append({
                    'date': datetime.fromtimestamp(int(item['timestamp'])).isoformat(),
                    'price': float(item['price']),
                    'arrival_quantity': int(item.get('arrival_quantity', 0))
                })
            
            # Sort by date
            history.sort(key=lambda x: x['date'])
            
            return history
        
        except Exception as e:
            logger.warning(f"History query error: {e}")
            # Return mock data for demonstration
            return self._generate_mock_history(start_date, end_date)
    
    def _generate_mock_history(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate mock historical data for demonstration"""
        history = []
        current_date = start_date
        base_price = 2400
        
        while current_date <= end_date:
            # Add some random variation
            import random
            variation = random.uniform(-100, 150)
            price = base_price + variation
            
            history.append({
                'date': current_date.isoformat(),
                'price': round(price, 2),
                'arrival_quantity': random.randint(80, 200)
            })
            
            current_date += timedelta(days=1)
            base_price = price  # Trend continuation
        
        return history
    
    def _calculate_price_trends(self, prices: List[float]) -> Dict[str, Any]:
        """Calculate price trend statistics"""
        
        if len(prices) < 2:
            return {
                'trend': 'insufficient_data',
                'change_percent': 0,
                'volatility': 0
            }
        
        # Calculate trend
        first_price = prices[0]
        last_price = prices[-1]
        change_percent = ((last_price - first_price) / first_price) * 100
        
        # Calculate volatility (standard deviation)
        avg_price = sum(prices) / len(prices)
        variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
        volatility = variance ** 0.5
        
        # Determine trend direction
        if change_percent > 5:
            trend = 'increasing'
        elif change_percent < -5:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change_percent': round(change_percent, 2),
            'volatility': round(volatility, 2),
            'avg_price': round(avg_price, 2),
            'price_range': {
                'min': min(prices),
                'max': max(prices)
            }
        }
    
    def _simple_price_prediction(self,
                                 history: List[Dict[str, Any]],
                                 forecast_days: int) -> List[Dict[str, Any]]:
        """Simple moving average price prediction"""
        
        if len(history) < 7:
            return []
        
        # Use 7-day moving average
        window_size = 7
        prices = [h['price'] for h in history]
        
        predictions = []
        last_date = datetime.fromisoformat(history[-1]['date'])
        
        # Calculate moving average
        recent_avg = sum(prices[-window_size:]) / window_size
        
        # Calculate trend
        older_avg = sum(prices[-window_size*2:-window_size]) / window_size if len(prices) >= window_size*2 else recent_avg
        trend = recent_avg - older_avg
        
        # Generate predictions
        predicted_price = recent_avg
        for i in range(1, forecast_days + 1):
            predicted_price += trend * 0.5  # Dampen trend
            forecast_date = last_date + timedelta(days=i)
            
            predictions.append({
                'date': forecast_date.isoformat(),
                'predicted_price': round(predicted_price, 2),
                'confidence_range': {
                    'low': round(predicted_price * 0.95, 2),
                    'high': round(predicted_price * 1.05, 2)
                }
            })
        
        return predictions
    
    def _get_crop_perishability(self, crop_name: str) -> Dict[str, Any]:
        """Get crop perishability information"""
        
        # Crop perishability database
        perishability_db = {
            'tomato': {'category': 'highly_perishable', 'shelf_life_days': 7, 'storage_cost_per_day': 5},
            'potato': {'category': 'moderately_perishable', 'shelf_life_days': 90, 'storage_cost_per_day': 2},
            'onion': {'category': 'moderately_perishable', 'shelf_life_days': 120, 'storage_cost_per_day': 2},
            'wheat': {'category': 'non_perishable', 'shelf_life_days': 365, 'storage_cost_per_day': 1},
            'rice': {'category': 'non_perishable', 'shelf_life_days': 365, 'storage_cost_per_day': 1},
            'sugarcane': {'category': 'highly_perishable', 'shelf_life_days': 14, 'storage_cost_per_day': 3},
            'banana': {'category': 'highly_perishable', 'shelf_life_days': 5, 'storage_cost_per_day': 4},
            'mango': {'category': 'highly_perishable', 'shelf_life_days': 10, 'storage_cost_per_day': 4}
        }
        
        return perishability_db.get(crop_name, {
            'category': 'moderately_perishable',
            'shelf_life_days': 30,
            'storage_cost_per_day': 3
        })
    
    def _calculate_optimal_selling_time(self,
                                       current_prices: Dict[str, Any],
                                       predictions: Optional[Dict[str, Any]],
                                       perishability: Dict[str, Any],
                                       storage_capacity: bool,
                                       harvest_date: Optional[str]) -> Dict[str, Any]:
        """Calculate optimal selling time recommendation"""
        
        current_avg = current_prices['statistics']['avg_price']
        
        # Default recommendation
        recommendation = {
            'timing': 'immediate',
            'reason': 'Sell immediately after harvest',
            'expected_price': current_avg,
            'confidence': 'medium'
        }
        
        # If highly perishable, recommend immediate sale
        if perishability['category'] == 'highly_perishable':
            recommendation['timing'] = 'immediate'
            recommendation['reason'] = f"Crop is highly perishable (shelf life: {perishability['shelf_life_days']} days). Sell immediately to avoid losses."
            return recommendation
        
        # If no storage, recommend immediate sale
        if not storage_capacity:
            recommendation['timing'] = 'immediate'
            recommendation['reason'] = "No storage capacity available. Sell immediately after harvest."
            return recommendation
        
        # If predictions available, analyze
        if predictions and predictions.get('success'):
            pred_list = predictions['predictions']
            if pred_list:
                # Find best predicted price
                best_pred = max(pred_list, key=lambda p: p['predicted_price'])
                best_price = best_pred['predicted_price']
                best_days = (datetime.fromisoformat(best_pred['date']) - datetime.now()).days
                
                # Calculate storage cost
                storage_cost = perishability['storage_cost_per_day'] * best_days
                net_gain = best_price - current_avg - storage_cost
                
                if net_gain > current_avg * 0.05:  # 5% gain threshold
                    recommendation['timing'] = f'wait_{best_days}_days'
                    recommendation['reason'] = f"Price expected to increase by ₹{round(best_price - current_avg, 2)}/quintal in {best_days} days. Net gain after storage costs: ₹{round(net_gain, 2)}/quintal."
                    recommendation['expected_price'] = best_price
                    recommendation['storage_cost'] = storage_cost
                    recommendation['net_gain'] = net_gain
                    recommendation['confidence'] = 'medium'
                else:
                    recommendation['reason'] = "Price increase not significant enough to cover storage costs. Sell now."
        
        return recommendation
    
    def _store_price_record(self, crop_name: str, market_data: Dict[str, Any]):
        """Store price record in DynamoDB"""
        try:
            timestamp = int(datetime.now().timestamp())
            
            self.price_table.put_item(
                Item={
                    'crop_market_id': f"{crop_name}#{market_data['market_id']}",
                    'timestamp': timestamp,
                    'crop_name': crop_name,
                    'market_id': market_data['market_id'],
                    'market_name': market_data['market_name'],
                    'price': Decimal(str(market_data['price'])),
                    'arrival_quantity': market_data.get('arrival_quantity', 0),
                    'location': json.dumps(market_data['location']),
                    'ttl': timestamp + (90 * 24 * 3600)  # 90 days retention
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store price record: {e}")
    
    def _get_cache_key(self, crop_name: str, latitude: float, longitude: float, radius: int) -> str:
        """Generate cache key for market prices"""
        lat_rounded = round(latitude, 2)
        lon_rounded = round(longitude, 2)
        content = f"{crop_name}:{lat_rounded}:{lon_rounded}:{radius}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve market prices from cache"""
        try:
            response = self.price_table.get_item(Key={'cache_key': cache_key})
            
            if 'Item' in response:
                item = response['Item']
                expires_at = datetime.fromisoformat(item['expires_at'])
                
                if datetime.now() < expires_at:
                    logger.debug(f"Cache hit for key {cache_key}")
                    return json.loads(item['price_data'])
                else:
                    self.price_table.delete_item(Key={'cache_key': cache_key})
                    logger.debug(f"Cache expired for key {cache_key}")
            
            return None
        
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
            return None
    
    def _save_to_cache(self, cache_key: str, price_data: Dict[str, Any]):
        """Save market prices to cache"""
        try:
            expires_at = datetime.now() + self.cache_ttl
            ttl = int((expires_at + timedelta(days=1)).timestamp())
            
            self.price_table.put_item(
                Item={
                    'cache_key': cache_key,
                    'price_data': json.dumps(price_data, default=str),
                    'cached_at': datetime.now().isoformat(),
                    'expires_at': expires_at.isoformat(),
                    'ttl': ttl
                }
            )
            logger.debug(f"Cached market prices for key {cache_key}")
        
        except Exception as e:
            logger.warning(f"Cache save error: {e}")


# Tool functions for agent integration (Strands @tool for orchestrator)
try:
    from strands import tool
except ImportError:
    def tool(fn):
        return fn  # no-op if Strands not installed

def create_market_price_tools(region: str = "us-east-1") -> MarketPriceTools:
    """
    Factory function to create market price tools instance
    
    Args:
        region: AWS region
    
    Returns:
        MarketPriceTools instance
    """
    return MarketPriceTools(region=region)


@tool
def get_current_prices_tool(crop_name: str, latitude: float, longitude: float, radius_km: int = 50) -> str:
    """
    Get current market prices for a crop near a location. Use when the user asks about crop prices, mandi rates, or selling price.
    """
    tools = create_market_price_tools()
    result = tools.get_current_prices(crop_name, latitude, longitude, radius_km)
    
    if result['success']:
        stats = result['statistics']
        output = f"""Current Market Prices for {result['crop_name'].title()}:

Price Range: ₹{stats['min_price']} - ₹{stats['max_price']} per quintal
Average Price: ₹{stats['avg_price']:.2f} per quintal
Markets Found: {stats['market_count']} within {result['location']['radius_km']}km

Top Markets:
"""
        for market in result['markets'][:3]:
            output += f"• {market['market_name']}: ₹{market['price']}/quintal ({market['distance_km']}km away)\n"
        
        return output
    else:
        return f"Error: {result.get('error', 'Failed to fetch market prices')}"


@tool
def get_price_history_tool(crop_name: str, market_id: str, days: int = 30) -> str:
    """
    Get price history and trends for a crop at a market. Use when the user asks about price trends, past rates, or market_id.
    """
    tools = create_market_price_tools()
    result = tools.get_price_history(crop_name, market_id, days)
    
    if result['success']:
        trends = result['trends']
        output = f"""Price History for {result['crop_name'].title()} at {result['market_id']}:

Period: {days} days
Trend: {trends['trend'].upper()}
Price Change: {trends['change_percent']}%
Average Price: ₹{trends['avg_price']:.2f}/quintal
Price Range: ₹{trends['price_range']['min']} - ₹{trends['price_range']['max']}
Volatility: {trends['volatility']:.2f}
"""
        return output
    else:
        return f"Error: {result.get('error', 'Failed to fetch price history')}"


@tool
def get_optimal_selling_time_tool(crop_name: str, latitude: float, longitude: float, storage_capacity: bool = True) -> str:
    """
    Get recommendation for when to sell a crop (optimal selling time). Use when the user asks when to sell, best time to sell, or storage vs sell now.
    """
    tools = create_market_price_tools()
    result = tools.get_optimal_selling_time(crop_name, latitude, longitude, None, storage_capacity)
    
    if result['success']:
        rec = result['recommendation']
        output = f"""Optimal Selling Time for {result['crop_name'].title()}:

Current Best Price: ₹{result['current_best_price']}/quintal
Best Market: {result['best_market']['market_name']}

Recommendation: {rec['timing'].upper()}
Reason: {rec['reason']}
Expected Price: ₹{rec['expected_price']:.2f}/quintal
"""
        if 'net_gain' in rec:
            output += f"Potential Net Gain: ₹{rec['net_gain']:.2f}/quintal\n"
        
        return output
    else:
        return f"Error: {result.get('error', 'Failed to calculate optimal selling time')}"
