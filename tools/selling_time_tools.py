"""
RISE Optimal Selling Time Calculator Tools
Advanced tools for calculating optimal selling time with perishability analysis,
storage cost calculations, and price alert system
"""

import boto3
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class SellingTimeTools:
    """Optimal selling time calculator for RISE farming assistant"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize selling time tools with AWS clients
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        
        # DynamoDB tables
        self.alerts_table = self.dynamodb.Table('RISE-PriceAlerts')
        self.storage_table = self.dynamodb.Table('RISE-StorageCosts')
        
        logger.info(f"Selling time tools initialized in region {region}")
    
    def analyze_perishability(self, crop_name: str) -> Dict[str, Any]:
        """
        Analyze crop perishability factors
        
        Args:
            crop_name: Name of the crop
        
        Returns:
            Dict with perishability analysis
        """
        try:
            crop_name = crop_name.lower().strip()
            
            # Comprehensive perishability database
            perishability_db = {
                # Highly perishable (1-14 days)
                'tomato': {
                    'category': 'highly_perishable',
                    'shelf_life_days': 7,
                    'quality_degradation_rate': 0.15,  # 15% per day
                    'optimal_storage_temp': '10-12°C',
                    'storage_requirements': 'Cold storage with humidity control',
                    'post_harvest_loss_rate': 0.25  # 25% typical loss
                },
                'leafy_greens': {
                    'category': 'highly_perishable',
                    'shelf_life_days': 5,
                    'quality_degradation_rate': 0.20,
                    'optimal_storage_temp': '0-2°C',
                    'storage_requirements': 'Refrigerated storage',
                    'post_harvest_loss_rate': 0.30
                },
                'banana': {
                    'category': 'highly_perishable',
                    'shelf_life_days': 5,
                    'quality_degradation_rate': 0.18,
                    'optimal_storage_temp': '13-15°C',
                    'storage_requirements': 'Ventilated cool storage',
                    'post_harvest_loss_rate': 0.20
                },
                'mango': {
                    'category': 'highly_perishable',
                    'shelf_life_days': 10,
                    'quality_degradation_rate': 0.12,
                    'optimal_storage_temp': '10-13°C',
                    'storage_requirements': 'Cold storage',
                    'post_harvest_loss_rate': 0.18
                },
                'sugarcane': {
                    'category': 'highly_perishable',
                    'shelf_life_days': 14,
                    'quality_degradation_rate': 0.08,
                    'optimal_storage_temp': 'Ambient',
                    'storage_requirements': 'Covered storage',
                    'post_harvest_loss_rate': 0.15
                },
                
                # Moderately perishable (15-120 days)
                'potato': {
                    'category': 'moderately_perishable',
                    'shelf_life_days': 90,
                    'quality_degradation_rate': 0.01,
                    'optimal_storage_temp': '3-5°C',
                    'storage_requirements': 'Cool, dark, ventilated storage',
                    'post_harvest_loss_rate': 0.10
                },
                'onion': {
                    'category': 'moderately_perishable',
                    'shelf_life_days': 120,
                    'quality_degradation_rate': 0.008,
                    'optimal_storage_temp': '0-1°C',
                    'storage_requirements': 'Dry, ventilated storage',
                    'post_harvest_loss_rate': 0.08
                },
                'carrot': {
                    'category': 'moderately_perishable',
                    'shelf_life_days': 60,
                    'quality_degradation_rate': 0.015,
                    'optimal_storage_temp': '0-2°C',
                    'storage_requirements': 'Cold storage with high humidity',
                    'post_harvest_loss_rate': 0.12
                },
                
                # Non-perishable (>120 days)
                'wheat': {
                    'category': 'non_perishable',
                    'shelf_life_days': 365,
                    'quality_degradation_rate': 0.001,
                    'optimal_storage_temp': 'Ambient',
                    'storage_requirements': 'Dry, pest-free warehouse',
                    'post_harvest_loss_rate': 0.05
                },
                'rice': {
                    'category': 'non_perishable',
                    'shelf_life_days': 365,
                    'quality_degradation_rate': 0.001,
                    'optimal_storage_temp': 'Ambient',
                    'storage_requirements': 'Dry, pest-free warehouse',
                    'post_harvest_loss_rate': 0.05
                },
                'pulses': {
                    'category': 'non_perishable',
                    'shelf_life_days': 365,
                    'quality_degradation_rate': 0.001,
                    'optimal_storage_temp': 'Ambient',
                    'storage_requirements': 'Dry storage',
                    'post_harvest_loss_rate': 0.04
                }
            }
            
            # Get perishability data or use default
            perish_data = perishability_db.get(crop_name, {
                'category': 'moderately_perishable',
                'shelf_life_days': 30,
                'quality_degradation_rate': 0.03,
                'optimal_storage_temp': 'Cool storage',
                'storage_requirements': 'Covered, ventilated storage',
                'post_harvest_loss_rate': 0.15
            })
            
            return {
                'success': True,
                'crop_name': crop_name,
                **perish_data,
                'recommendation': self._get_perishability_recommendation(perish_data)
            }
        
        except Exception as e:
            logger.error(f"Perishability analysis error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def calculate_storage_costs(self,
                               crop_name: str,
                               quantity_quintals: float,
                               storage_days: int,
                               storage_type: str = 'standard') -> Dict[str, Any]:
        """
        Calculate storage costs including facility fees and quality degradation
        
        Args:
            crop_name: Name of the crop
            quantity_quintals: Quantity in quintals
            storage_days: Number of days to store
            storage_type: Type of storage (standard, cold, warehouse)
        
        Returns:
            Dict with storage cost breakdown
        """
        try:
            crop_name = crop_name.lower().strip()
            
            # Storage cost rates (INR per quintal per day)
            storage_rates = {
                'standard': {
                    'highly_perishable': 5,
                    'moderately_perishable': 2,
                    'non_perishable': 1
                },
                'cold': {
                    'highly_perishable': 8,
                    'moderately_perishable': 6,
                    'non_perishable': 4
                },
                'warehouse': {
                    'highly_perishable': 3,
                    'moderately_perishable': 1.5,
                    'non_perishable': 0.8
                }
            }
            
            # Get perishability
            perish_result = self.analyze_perishability(crop_name)
            if not perish_result['success']:
                return perish_result
            
            category = perish_result['category']
            degradation_rate = perish_result['quality_degradation_rate']
            
            # Calculate costs
            daily_rate = storage_rates.get(storage_type, storage_rates['standard'])[category]
            facility_cost = daily_rate * quantity_quintals * storage_days
            
            # Calculate quality degradation loss
            quality_loss_percent = min(degradation_rate * storage_days * 100, 100)
            quality_loss_value = 0  # Will be calculated with price data
            
            # Additional costs
            handling_cost = quantity_quintals * 10  # ₹10 per quintal handling
            insurance_cost = quantity_quintals * storage_days * 0.5  # ₹0.5 per quintal per day
            
            total_cost = facility_cost + handling_cost + insurance_cost
            
            return {
                'success': True,
                'crop_name': crop_name,
                'quantity_quintals': quantity_quintals,
                'storage_days': storage_days,
                'storage_type': storage_type,
                'costs': {
                    'facility_cost': round(facility_cost, 2),
                    'handling_cost': round(handling_cost, 2),
                    'insurance_cost': round(insurance_cost, 2),
                    'total_cost': round(total_cost, 2),
                    'cost_per_quintal': round(total_cost / quantity_quintals, 2),
                    'cost_per_day': round(total_cost / storage_days, 2)
                },
                'quality_impact': {
                    'degradation_percent': round(quality_loss_percent, 2),
                    'remaining_quality': round(100 - quality_loss_percent, 2)
                },
                'currency': 'INR'
            }
        
        except Exception as e:
            logger.error(f"Storage cost calculation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def calculate_optimal_selling_time(self,
                                      crop_name: str,
                                      current_price: float,
                                      predicted_prices: List[Dict[str, Any]],
                                      quantity_quintals: float,
                                      storage_capacity: bool = True,
                                      storage_type: str = 'standard') -> Dict[str, Any]:
        """
        Calculate optimal selling time considering all factors
        
        Args:
            crop_name: Name of the crop
            current_price: Current market price per quintal
            predicted_prices: List of predicted prices with dates
            quantity_quintals: Quantity to sell
            storage_capacity: Whether storage is available
            storage_type: Type of storage available
        
        Returns:
            Dict with optimal selling recommendation
        """
        try:
            crop_name = crop_name.lower().strip()
            
            # Get perishability analysis
            perish_result = self.analyze_perishability(crop_name)
            if not perish_result['success']:
                return perish_result
            
            # If no storage or highly perishable, recommend immediate sale
            if not storage_capacity:
                return {
                    'success': True,
                    'recommendation': {
                        'timing': 'immediate',
                        'days_to_wait': 0,
                        'reason': 'No storage capacity available',
                        'expected_revenue': current_price * quantity_quintals,
                        'net_profit': current_price * quantity_quintals,
                        'confidence': 'high'
                    }
                }
            
            if perish_result['category'] == 'highly_perishable':
                return {
                    'success': True,
                    'recommendation': {
                        'timing': 'immediate',
                        'days_to_wait': 0,
                        'reason': f"Crop is highly perishable (shelf life: {perish_result['shelf_life_days']} days)",
                        'expected_revenue': current_price * quantity_quintals,
                        'net_profit': current_price * quantity_quintals,
                        'confidence': 'high'
                    }
                }
            
            # Analyze each time point
            scenarios = []
            
            # Scenario 0: Sell immediately
            scenarios.append({
                'days': 0,
                'price': current_price,
                'storage_cost': 0,
                'quality_loss': 0,
                'revenue': current_price * quantity_quintals,
                'net_profit': current_price * quantity_quintals
            })
            
            # Analyze future scenarios
            for pred in predicted_prices:
                days = (datetime.fromisoformat(pred['date']) - datetime.now()).days
                
                # Skip if beyond shelf life
                if days > perish_result['shelf_life_days']:
                    continue
                
                # Calculate storage costs
                storage_result = self.calculate_storage_costs(
                    crop_name,
                    quantity_quintals,
                    days,
                    storage_type
                )
                
                if not storage_result['success']:
                    continue
                
                # Calculate quality-adjusted price
                quality_factor = 1 - (perish_result['quality_degradation_rate'] * days)
                adjusted_price = pred['predicted_price'] * quality_factor
                
                # Calculate net profit
                revenue = adjusted_price * quantity_quintals
                costs = storage_result['costs']['total_cost']
                net_profit = revenue - costs
                
                scenarios.append({
                    'days': days,
                    'date': pred['date'],
                    'price': pred['predicted_price'],
                    'adjusted_price': round(adjusted_price, 2),
                    'storage_cost': costs,
                    'quality_loss': round((1 - quality_factor) * 100, 2),
                    'revenue': round(revenue, 2),
                    'net_profit': round(net_profit, 2)
                })
            
            # Find optimal scenario
            best_scenario = max(scenarios, key=lambda s: s['net_profit'])
            
            # Calculate improvement over immediate sale
            immediate_profit = scenarios[0]['net_profit']
            profit_improvement = best_scenario['net_profit'] - immediate_profit
            improvement_percent = (profit_improvement / immediate_profit) * 100
            
            # Determine recommendation
            if best_scenario['days'] == 0 or improvement_percent < 5:
                timing = 'immediate'
                reason = "Current price is optimal. No significant benefit from waiting."
            else:
                timing = f"wait_{best_scenario['days']}_days"
                reason = f"Waiting {best_scenario['days']} days will increase net profit by ₹{round(profit_improvement, 2)} ({improvement_percent:.1f}%)"
            
            return {
                'success': True,
                'crop_name': crop_name,
                'quantity_quintals': quantity_quintals,
                'recommendation': {
                    'timing': timing,
                    'days_to_wait': best_scenario['days'],
                    'optimal_date': best_scenario.get('date', datetime.now().isoformat()),
                    'reason': reason,
                    'expected_price': best_scenario.get('adjusted_price', best_scenario['price']),
                    'expected_revenue': best_scenario['revenue'],
                    'storage_cost': best_scenario['storage_cost'],
                    'net_profit': best_scenario['net_profit'],
                    'profit_improvement': round(profit_improvement, 2),
                    'improvement_percent': round(improvement_percent, 2),
                    'confidence': 'high' if improvement_percent > 10 else 'medium'
                },
                'scenarios': scenarios,
                'perishability': perish_result
            }
        
        except Exception as e:
            logger.error(f"Optimal selling time calculation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def create_price_alert(self,
                          user_id: str,
                          crop_name: str,
                          target_price: float,
                          market_id: str,
                          phone_number: Optional[str] = None,
                          email: Optional[str] = None) -> Dict[str, Any]:
        """
        Create price alert for target price
        
        Args:
            user_id: User identifier
            crop_name: Name of the crop
            target_price: Target price per quintal
            market_id: Market to monitor
            phone_number: Optional phone for SMS alerts
            email: Optional email for alerts
        
        Returns:
            Dict with alert creation status
        """
        try:
            crop_name = crop_name.lower().strip()
            
            alert_id = f"{user_id}#{crop_name}#{market_id}#{int(datetime.now().timestamp())}"
            
            # Store alert in DynamoDB
            self.alerts_table.put_item(
                Item={
                    'alert_id': alert_id,
                    'user_id': user_id,
                    'crop_name': crop_name,
                    'market_id': market_id,
                    'target_price': Decimal(str(target_price)),
                    'phone_number': phone_number or '',
                    'email': email or '',
                    'status': 'active',
                    'created_at': datetime.now().isoformat(),
                    'triggered': False,
                    'ttl': int((datetime.now() + timedelta(days=90)).timestamp())
                }
            )
            
            return {
                'success': True,
                'alert_id': alert_id,
                'crop_name': crop_name,
                'target_price': target_price,
                'market_id': market_id,
                'message': f"Price alert created. You will be notified when {crop_name} reaches ₹{target_price}/quintal at {market_id}"
            }
        
        except Exception as e:
            logger.error(f"Price alert creation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_price_alerts(self,
                          user_id: str,
                          current_prices: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if any price alerts should be triggered
        
        Args:
            user_id: User identifier
            current_prices: Current market prices data
        
        Returns:
            Dict with triggered alerts
        """
        try:
            # Query user's active alerts
            response = self.alerts_table.query(
                IndexName='user_id-status-index',
                KeyConditionExpression='user_id = :uid AND #status = :active',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':uid': user_id,
                    ':active': 'active'
                }
            )
            
            triggered_alerts = []
            
            for alert in response.get('Items', []):
                crop_name = alert['crop_name']
                market_id = alert['market_id']
                target_price = float(alert['target_price'])
                
                # Check if price matches
                for market in current_prices.get('markets', []):
                    if market['market_id'] == market_id and market['price'] >= target_price:
                        # Trigger alert
                        self._trigger_alert(alert, market['price'])
                        triggered_alerts.append({
                            'alert_id': alert['alert_id'],
                            'crop_name': crop_name,
                            'target_price': target_price,
                            'current_price': market['price'],
                            'market_id': market_id,
                            'market_name': market['market_name']
                        })
            
            return {
                'success': True,
                'triggered_count': len(triggered_alerts),
                'alerts': triggered_alerts
            }
        
        except Exception as e:
            logger.error(f"Price alert check error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_alerts(self, user_id: str) -> Dict[str, Any]:
        """
        Get all alerts for a user
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with user's alerts
        """
        try:
            response = self.alerts_table.query(
                IndexName='user_id-status-index',
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id}
            )
            
            alerts = []
            for item in response.get('Items', []):
                alerts.append({
                    'alert_id': item['alert_id'],
                    'crop_name': item['crop_name'],
                    'market_id': item['market_id'],
                    'target_price': float(item['target_price']),
                    'status': item['status'],
                    'created_at': item['created_at'],
                    'triggered': item.get('triggered', False)
                })
            
            return {
                'success': True,
                'alerts': alerts,
                'count': len(alerts)
            }
        
        except Exception as e:
            logger.error(f"Get alerts error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_alert(self, alert_id: str) -> Dict[str, Any]:
        """
        Delete a price alert
        
        Args:
            alert_id: Alert identifier
        
        Returns:
            Dict with deletion status
        """
        try:
            self.alerts_table.delete_item(Key={'alert_id': alert_id})
            
            return {
                'success': True,
                'message': 'Alert deleted successfully'
            }
        
        except Exception as e:
            logger.error(f"Alert deletion error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _trigger_alert(self, alert: Dict[str, Any], current_price: float):
        """Trigger price alert notification"""
        try:
            # Update alert status
            self.alerts_table.update_item(
                Key={'alert_id': alert['alert_id']},
                UpdateExpression='SET #status = :triggered, triggered = :true, triggered_at = :now, triggered_price = :price',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':triggered': 'triggered',
                    ':true': True,
                    ':now': datetime.now().isoformat(),
                    ':price': Decimal(str(current_price))
                }
            )
            
            # Send notification (SMS/Email via SNS)
            message = f"Price Alert: {alert['crop_name']} has reached ₹{current_price}/quintal at {alert['market_id']} (Target: ₹{float(alert['target_price'])})"
            
            if alert.get('phone_number'):
                self.sns.publish(
                    PhoneNumber=alert['phone_number'],
                    Message=message
                )
            
            logger.info(f"Alert triggered: {alert['alert_id']}")
        
        except Exception as e:
            logger.warning(f"Alert trigger error: {e}")
    
    def _get_perishability_recommendation(self, perish_data: Dict[str, Any]) -> str:
        """Generate perishability-based recommendation"""
        category = perish_data['category']
        shelf_life = perish_data['shelf_life_days']
        
        if category == 'highly_perishable':
            return f"Sell within {shelf_life} days. Consider immediate sale or cold storage."
        elif category == 'moderately_perishable':
            return f"Can be stored for up to {shelf_life} days. Monitor market prices for optimal timing."
        else:
            return f"Long shelf life ({shelf_life} days). Can wait for better prices."


# Tool functions for agent integration

def create_selling_time_tools(region: str = "us-east-1") -> SellingTimeTools:
    """
    Factory function to create selling time tools instance
    
    Args:
        region: AWS region
    
    Returns:
        SellingTimeTools instance
    """
    return SellingTimeTools(region=region)
