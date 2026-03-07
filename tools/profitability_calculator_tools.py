"""
RISE Crop Profitability Calculator Tools
Comprehensive tools for crop profitability analysis with cost estimation, yield prediction, and risk assessment
"""

import boto3
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class ProfitabilityCalculatorTools:
    """Crop profitability calculator with comprehensive cost and yield analysis"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize profitability calculator tools
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # DynamoDB table for profitability data
        self.profitability_table = self.dynamodb.Table('RISE-ProfitabilityData')
        
        # Import market price and weather tools for integration
        try:
            from market_price_tools import MarketPriceTools
            from weather_tools import WeatherTools
            self.market_tools = MarketPriceTools(region=region)
            self.weather_tools = WeatherTools(region=region)
        except ImportError:
            logger.warning("Market price or weather tools not available")
            self.market_tools = None
            self.weather_tools = None
        
        logger.info(f"Profitability calculator initialized in region {region}")

    def calculate_comprehensive_profitability(self,
                                             crop_name: str,
                                             farm_size_acres: float,
                                             location: Dict[str, Any],
                                             soil_type: str = 'loamy',
                                             season: Optional[str] = None,
                                             custom_input_costs: Optional[Dict[str, float]] = None,
                                             historical_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive profitability analysis for a crop
        
        Args:
            crop_name: Name of the crop
            farm_size_acres: Farm size in acres
            location: Location dict with state, district, latitude, longitude
            soil_type: Soil type (loamy, clay, sandy, etc.)
            season: Growing season (kharif, rabi, zaid)
            custom_input_costs: Optional custom input costs
            historical_data: Optional historical yield data
        
        Returns:
            Dict with comprehensive profitability analysis
        """
        try:
            crop_name = crop_name.lower().strip()
            
            # Get real-time market prices
            market_price = self._get_market_price(crop_name, location)
            
            # Estimate input costs
            cost_breakdown = self.estimate_input_costs(
                crop_name, farm_size_acres, location, soil_type, season
            )
            
            if not cost_breakdown['success']:
                return cost_breakdown
            
            # Override with custom costs if provided
            if custom_input_costs:
                cost_breakdown['costs_per_acre'].update(custom_input_costs)
                cost_breakdown['total_cost_per_acre'] = sum(cost_breakdown['costs_per_acre'].values())

            
            # Predict yield
            yield_prediction = self.predict_crop_yield(
                crop_name, location, soil_type, season, historical_data
            )
            
            if not yield_prediction['success']:
                return yield_prediction
            
            # Calculate profitability scenarios
            scenarios = self._calculate_profit_scenarios(
                cost_breakdown,
                yield_prediction,
                market_price,
                farm_size_acres
            )
            
            # Assess risk factors
            risk_assessment = self._assess_risk_factors(
                crop_name, location, season, yield_prediction
            )
            
            # Generate profit/loss projections
            projections = self._generate_projections(
                scenarios, risk_assessment, market_price
            )
            
            # Store analysis
            analysis_id = f"prof_{uuid.uuid4().hex[:12]}"
            self._store_profitability_analysis(analysis_id, {
                'crop_name': crop_name,
                'location': location,
                'scenarios': scenarios,
                'risk_assessment': risk_assessment
            })
            
            return {
                'success': True,
                'analysis_id': analysis_id,
                'crop_name': crop_name,
                'farm_size_acres': farm_size_acres,
                'location': location,
                'market_price_per_quintal': market_price,
                'cost_breakdown': cost_breakdown,
                'yield_prediction': yield_prediction,
                'profitability_scenarios': scenarios,
                'risk_assessment': risk_assessment,
                'projections': projections,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Profitability calculation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def estimate_input_costs(self,
                            crop_name: str,
                            farm_size_acres: float,
                            location: Dict[str, Any],
                            soil_type: str = 'loamy',
                            season: Optional[str] = None) -> Dict[str, Any]:
        """
        Estimate comprehensive input costs for crop cultivation
        
        Args:
            crop_name: Name of the crop
            farm_size_acres: Farm size in acres
            location: Location information
            soil_type: Soil type
            season: Growing season
        
        Returns:
            Dict with detailed cost breakdown
        """
        try:
            crop_name = crop_name.lower().strip()
            
            # Get crop-specific cost data
            crop_costs = self._get_crop_cost_database()
            
            if crop_name not in crop_costs:
                # Use average costs for unknown crops
                crop_name = 'default'
            
            costs = crop_costs[crop_name]
            
            # Calculate costs per acre
            costs_per_acre = {
                'seeds': costs['seeds_per_acre'],
                'fertilizers_npk': costs['fertilizers_npk'],
                'organic_manure': costs['organic_manure'],
                'pesticides': costs['pesticides'],
                'fungicides': costs['fungicides'],
                'irrigation': costs['irrigation'],
                'labor_planting': costs['labor_planting'],
                'labor_maintenance': costs['labor_maintenance'],
                'labor_harvesting': costs['labor_harvesting'],
                'equipment_rental': costs['equipment_rental'],
                'transportation': costs['transportation'],
                'storage': costs['storage'],
                'miscellaneous': costs['miscellaneous']
            }
            
            # Adjust for soil type
            soil_adjustment = self._get_soil_cost_adjustment(soil_type)
            for key in ['fertilizers_npk', 'organic_manure']:
                costs_per_acre[key] *= soil_adjustment
            
            # Adjust for location (state-based cost variations)
            location_adjustment = self._get_location_cost_adjustment(location.get('state', 'Unknown'))
            for key in costs_per_acre:
                costs_per_acre[key] *= location_adjustment
            
            # Calculate totals
            total_cost_per_acre = sum(costs_per_acre.values())
            total_farm_cost = total_cost_per_acre * farm_size_acres
            
            # Calculate labor breakdown
            total_labor_cost = (costs_per_acre['labor_planting'] + 
                              costs_per_acre['labor_maintenance'] + 
                              costs_per_acre['labor_harvesting'])
            
            return {
                'success': True,
                'crop_name': crop_name,
                'farm_size_acres': farm_size_acres,
                'costs_per_acre': costs_per_acre,
                'total_cost_per_acre': round(total_cost_per_acre, 2),
                'total_farm_cost': round(total_farm_cost, 2),
                'cost_categories': {
                    'inputs': round(costs_per_acre['seeds'] + costs_per_acre['fertilizers_npk'] + 
                                  costs_per_acre['organic_manure'] + costs_per_acre['pesticides'] + 
                                  costs_per_acre['fungicides'], 2),
                    'labor': round(total_labor_cost, 2),
                    'operations': round(costs_per_acre['irrigation'] + costs_per_acre['equipment_rental'] + 
                                      costs_per_acre['transportation'] + costs_per_acre['storage'], 2),
                    'miscellaneous': round(costs_per_acre['miscellaneous'], 2)
                },
                'currency': 'INR',
                'season': season or 'not specified'
            }
        
        except Exception as e:
            logger.error(f"Cost estimation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def predict_crop_yield(self,
                          crop_name: str,
                          location: Dict[str, Any],
                          soil_type: str = 'loamy',
                          season: Optional[str] = None,
                          historical_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Predict crop yield based on historical data and environmental factors
        
        Args:
            crop_name: Name of the crop
            location: Location information
            soil_type: Soil type
            season: Growing season
            historical_data: Optional historical yield data
        
        Returns:
            Dict with yield predictions
        """
        try:
            crop_name = crop_name.lower().strip()
            
            # Get base yield data
            yield_database = self._get_crop_yield_database()
            
            if crop_name not in yield_database:
                crop_name = 'default'
            
            base_yield = yield_database[crop_name]
            
            # Calculate yield adjustments
            soil_factor = self._get_soil_yield_factor(soil_type)
            location_factor = self._get_location_yield_factor(location.get('state', 'Unknown'))
            season_factor = self._get_season_yield_factor(crop_name, season)
            
            # Get weather impact if available
            weather_factor = 1.0
            if self.weather_tools and 'latitude' in location and 'longitude' in location:
                weather_factor = self._calculate_weather_impact(
                    location['latitude'], location['longitude']
                )
            
            # Calculate yield scenarios
            average_yield = base_yield * soil_factor * location_factor * season_factor * weather_factor
            optimistic_yield = average_yield * 1.25  # 25% above average
            conservative_yield = average_yield * 0.75  # 25% below average
            
            # Use historical data if provided
            if historical_data and 'past_yields' in historical_data:
                past_yields = historical_data['past_yields']
                if past_yields:
                    historical_avg = sum(past_yields) / len(past_yields)
                    # Blend historical with predicted (70% historical, 30% predicted)
                    average_yield = (historical_avg * 0.7) + (average_yield * 0.3)
                    optimistic_yield = average_yield * 1.2
                    conservative_yield = average_yield * 0.8
            
            return {
                'success': True,
                'crop_name': crop_name,
                'yield_per_acre_quintals': {
                    'average': round(average_yield, 2),
                    'optimistic': round(optimistic_yield, 2),
                    'conservative': round(conservative_yield, 2)
                },
                'factors_applied': {
                    'soil_factor': round(soil_factor, 2),
                    'location_factor': round(location_factor, 2),
                    'season_factor': round(season_factor, 2),
                    'weather_factor': round(weather_factor, 2)
                },
                'confidence': 'medium' if not historical_data else 'high',
                'unit': 'quintals per acre'
            }
        
        except Exception as e:
            logger.error(f"Yield prediction error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def compare_crop_profitability(self,
                                  crop_list: List[str],
                                  farm_size_acres: float,
                                  location: Dict[str, Any],
                                  soil_type: str = 'loamy',
                                  season: Optional[str] = None) -> Dict[str, Any]:
        """
        Compare profitability across multiple crops
        
        Args:
            crop_list: List of crop names to compare
            farm_size_acres: Farm size in acres
            location: Location information
            soil_type: Soil type
            season: Growing season
        
        Returns:
            Dict with comparative profitability analysis
        """
        try:
            comparisons = []
            
            for crop_name in crop_list:
                result = self.calculate_comprehensive_profitability(
                    crop_name=crop_name,
                    farm_size_acres=farm_size_acres,
                    location=location,
                    soil_type=soil_type,
                    season=season
                )
                
                if result['success']:
                    comparisons.append({
                        'crop_name': crop_name,
                        'total_cost': result['cost_breakdown']['total_farm_cost'],
                        'average_yield': result['yield_prediction']['yield_per_acre_quintals']['average'],
                        'market_price': result['market_price_per_quintal'],
                        'average_revenue': result['profitability_scenarios']['average']['total_revenue'],
                        'average_profit': result['profitability_scenarios']['average']['net_profit'],
                        'roi': result['profitability_scenarios']['average']['roi_percent'],
                        'risk_score': result['risk_assessment']['overall_risk_score']
                    })
            
            if not comparisons:
                return {
                    'success': False,
                    'error': 'No valid crop profitability data available'
                }
            
            # Sort by average profit (descending)
            comparisons.sort(key=lambda x: x['average_profit'], reverse=True)
            
            # Generate rankings
            rankings = {
                'by_profit': [c['crop_name'] for c in sorted(comparisons, key=lambda x: x['average_profit'], reverse=True)],
                'by_roi': [c['crop_name'] for c in sorted(comparisons, key=lambda x: x['roi'], reverse=True)],
                'by_low_risk': [c['crop_name'] for c in sorted(comparisons, key=lambda x: x['risk_score'])]
            }
            
            return {
                'success': True,
                'crops_compared': crop_list,
                'farm_size_acres': farm_size_acres,
                'location': location,
                'comparisons': comparisons,
                'rankings': rankings,
                'best_overall': comparisons[0]['crop_name'],
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Crop comparison error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _calculate_profit_scenarios(self,
                                   cost_breakdown: Dict[str, Any],
                                   yield_prediction: Dict[str, Any],
                                   market_price: float,
                                   farm_size_acres: float) -> Dict[str, Any]:
        """Calculate profit scenarios (average, optimistic, conservative)"""
        
        total_cost = cost_breakdown['total_farm_cost']
        yields = yield_prediction['yield_per_acre_quintals']
        
        scenarios = {}
        
        for scenario_name, yield_per_acre in yields.items():
            total_yield = yield_per_acre * farm_size_acres
            revenue = total_yield * market_price
            profit = revenue - total_cost
            roi = (profit / total_cost * 100) if total_cost > 0 else 0
            profit_margin = (profit / revenue * 100) if revenue > 0 else 0
            
            scenarios[scenario_name] = {
                'yield_per_acre': round(yield_per_acre, 2),
                'total_yield_quintals': round(total_yield, 2),
                'price_per_quintal': market_price,
                'total_revenue': round(revenue, 2),
                'total_cost': round(total_cost, 2),
                'net_profit': round(profit, 2),
                'profit_per_acre': round(profit / farm_size_acres, 2),
                'roi_percent': round(roi, 2),
                'profit_margin_percent': round(profit_margin, 2)
            }
        
        return scenarios
    
    def _assess_risk_factors(self,
                           crop_name: str,
                           location: Dict[str, Any],
                           season: Optional[str],
                           yield_prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk factors affecting profitability"""
        
        risk_factors = []
        risk_scores = {}
        
        # Weather risk
        weather_risk = self._assess_weather_risk(location, season)
        risk_factors.append({
            'factor': 'weather',
            'risk_level': weather_risk['level'],
            'description': weather_risk['description'],
            'mitigation': weather_risk['mitigation']
        })
        risk_scores['weather'] = weather_risk['score']
        
        # Pest and disease risk
        pest_risk = self._assess_pest_disease_risk(crop_name, season)
        risk_factors.append({
            'factor': 'pest_disease',
            'risk_level': pest_risk['level'],
            'description': pest_risk['description'],
            'mitigation': pest_risk['mitigation']
        })
        risk_scores['pest_disease'] = pest_risk['score']
        
        # Market volatility risk
        market_risk = self._assess_market_risk(crop_name)
        risk_factors.append({
            'factor': 'market_volatility',
            'risk_level': market_risk['level'],
            'description': market_risk['description'],
            'mitigation': market_risk['mitigation']
        })
        risk_scores['market'] = market_risk['score']
        
        # Yield variability risk
        yield_range = (yield_prediction['yield_per_acre_quintals']['optimistic'] - 
                      yield_prediction['yield_per_acre_quintals']['conservative'])
        yield_avg = yield_prediction['yield_per_acre_quintals']['average']
        yield_variability = (yield_range / yield_avg * 100) if yield_avg > 0 else 50
        
        if yield_variability > 40:
            yield_risk_level = 'high'
            yield_risk_score = 7
        elif yield_variability > 25:
            yield_risk_level = 'medium'
            yield_risk_score = 5
        else:
            yield_risk_level = 'low'
            yield_risk_score = 3
        
        risk_factors.append({
            'factor': 'yield_variability',
            'risk_level': yield_risk_level,
            'description': f'Yield variability of {round(yield_variability, 1)}%',
            'mitigation': 'Use improved seeds and follow best practices'
        })
        risk_scores['yield'] = yield_risk_score
        
        # Calculate overall risk score (1-10)
        overall_risk_score = sum(risk_scores.values()) / len(risk_scores)
        
        if overall_risk_score >= 7:
            overall_risk_level = 'high'
        elif overall_risk_score >= 5:
            overall_risk_level = 'medium'
        else:
            overall_risk_level = 'low'
        
        return {
            'risk_factors': risk_factors,
            'risk_scores': risk_scores,
            'overall_risk_score': round(overall_risk_score, 2),
            'overall_risk_level': overall_risk_level,
            'recommendation': self._get_risk_recommendation(overall_risk_level)
        }

    def _generate_projections(self,
                            scenarios: Dict[str, Any],
                            risk_assessment: Dict[str, Any],
                            market_price: float) -> Dict[str, Any]:
        """Generate profit/loss projections with risk adjustments"""
        
        # Base projections from scenarios
        projections = {
            'best_case': {
                'scenario': 'optimistic',
                'net_profit': scenarios['optimistic']['net_profit'],
                'probability': 0.25,
                'conditions': 'Favorable weather, good market prices, optimal yield'
            },
            'expected_case': {
                'scenario': 'average',
                'net_profit': scenarios['average']['net_profit'],
                'probability': 0.50,
                'conditions': 'Normal weather, stable market prices, average yield'
            },
            'worst_case': {
                'scenario': 'conservative',
                'net_profit': scenarios['conservative']['net_profit'],
                'probability': 0.25,
                'conditions': 'Adverse weather, low market prices, below-average yield'
            }
        }
        
        # Adjust probabilities based on risk
        risk_level = risk_assessment['overall_risk_level']
        if risk_level == 'high':
            projections['best_case']['probability'] = 0.15
            projections['expected_case']['probability'] = 0.45
            projections['worst_case']['probability'] = 0.40
        elif risk_level == 'low':
            projections['best_case']['probability'] = 0.35
            projections['expected_case']['probability'] = 0.55
            projections['worst_case']['probability'] = 0.10
        
        # Calculate expected value
        expected_profit = (
            projections['best_case']['net_profit'] * projections['best_case']['probability'] +
            projections['expected_case']['net_profit'] * projections['expected_case']['probability'] +
            projections['worst_case']['net_profit'] * projections['worst_case']['probability']
        )
        
        # Price sensitivity analysis
        price_scenarios = {
            'price_increase_10_percent': {
                'price': market_price * 1.1,
                'profit_change': scenarios['average']['total_yield_quintals'] * market_price * 0.1
            },
            'price_decrease_10_percent': {
                'price': market_price * 0.9,
                'profit_change': scenarios['average']['total_yield_quintals'] * market_price * -0.1
            }
        }
        
        return {
            'projections': projections,
            'expected_profit': round(expected_profit, 2),
            'price_sensitivity': price_scenarios,
            'break_even_price': round(scenarios['average']['total_cost'] / 
                                     scenarios['average']['total_yield_quintals'], 2),
            'break_even_yield': round(scenarios['average']['total_cost'] / market_price, 2)
        }

    def _get_market_price(self, crop_name: str, location: Dict[str, Any]) -> float:
        """Get current market price for crop"""
        
        # Try to get real-time market price
        if self.market_tools and 'latitude' in location and 'longitude' in location:
            try:
                price_data = self.market_tools.get_current_prices(
                    crop_name,
                    location['latitude'],
                    location['longitude'],
                    radius_km=50
                )
                
                if price_data.get('success'):
                    return price_data['statistics']['avg_price']
            except Exception as e:
                logger.warning(f"Failed to get real-time price: {e}")
        
        # Fallback to mock prices
        return self._get_mock_market_price(crop_name)
    
    def _get_mock_market_price(self, crop_name: str) -> float:
        """Get mock market price (fallback)"""
        
        mock_prices = {
            'wheat': 2200, 'rice': 2000, 'paddy': 2000, 'maize': 1800,
            'corn': 1800, 'cotton': 6000, 'sugarcane': 350, 'soybean': 4000,
            'groundnut': 5500, 'peanut': 5500, 'potato': 1200, 'tomato': 1500,
            'onion': 1000, 'chickpea': 5000, 'chana': 5000, 'pigeon pea': 6000,
            'tur': 6000, 'mustard': 5500, 'sunflower': 6000, 'bajra': 2000,
            'jowar': 2800, 'barley': 1800, 'gram': 5000, 'lentil': 5500,
            'default': 2500
        }
        
        for key, price in mock_prices.items():
            if key in crop_name.lower():
                return price
        
        return mock_prices['default']
    
    def _calculate_weather_impact(self, latitude: float, longitude: float) -> float:
        """Calculate weather impact factor on yield"""
        
        try:
            weather_data = self.weather_tools.get_farming_weather_insights(latitude, longitude)
            
            if not weather_data.get('success'):
                return 1.0
            
            # Analyze weather conditions
            current = weather_data['current_conditions']
            irrigation = weather_data['irrigation_advice']
            
            impact_factor = 1.0
            
            # Temperature impact
            temp = current['temperature']
            if temp > 40 or temp < 5:
                impact_factor *= 0.85  # Extreme temperature reduces yield
            elif 20 <= temp <= 30:
                impact_factor *= 1.05  # Optimal temperature
            
            # Humidity impact
            humidity = current['humidity']
            if humidity > 85:
                impact_factor *= 0.95  # High humidity risk
            elif 60 <= humidity <= 75:
                impact_factor *= 1.02  # Good humidity
            
            # Irrigation need impact
            if irrigation['priority'] == 'High':
                impact_factor *= 0.95  # Water stress
            
            return max(0.7, min(1.15, impact_factor))
        
        except Exception as e:
            logger.warning(f"Weather impact calculation failed: {e}")
            return 1.0

    def _get_crop_cost_database(self) -> Dict[str, Dict[str, float]]:
        """Get crop-specific cost database (per acre in INR)"""
        
        return {
            'wheat': {
                'seeds_per_acre': 1200, 'fertilizers_npk': 3500, 'organic_manure': 1500,
                'pesticides': 800, 'fungicides': 500, 'irrigation': 2000,
                'labor_planting': 1500, 'labor_maintenance': 2500, 'labor_harvesting': 2000,
                'equipment_rental': 1500, 'transportation': 800, 'storage': 500,
                'miscellaneous': 700
            },
            'rice': {
                'seeds_per_acre': 1000, 'fertilizers_npk': 4000, 'organic_manure': 1800,
                'pesticides': 1000, 'fungicides': 600, 'irrigation': 3500,
                'labor_planting': 2000, 'labor_maintenance': 3000, 'labor_harvesting': 2500,
                'equipment_rental': 1800, 'transportation': 900, 'storage': 600,
                'miscellaneous': 800
            },
            'paddy': {
                'seeds_per_acre': 1000, 'fertilizers_npk': 4000, 'organic_manure': 1800,
                'pesticides': 1000, 'fungicides': 600, 'irrigation': 3500,
                'labor_planting': 2000, 'labor_maintenance': 3000, 'labor_harvesting': 2500,
                'equipment_rental': 1800, 'transportation': 900, 'storage': 600,
                'miscellaneous': 800
            },
            'maize': {
                'seeds_per_acre': 1500, 'fertilizers_npk': 3000, 'organic_manure': 1200,
                'pesticides': 900, 'fungicides': 400, 'irrigation': 2500,
                'labor_planting': 1200, 'labor_maintenance': 2000, 'labor_harvesting': 1800,
                'equipment_rental': 1200, 'transportation': 700, 'storage': 400,
                'miscellaneous': 600
            },
            'cotton': {
                'seeds_per_acre': 2000, 'fertilizers_npk': 4500, 'organic_manure': 2000,
                'pesticides': 2500, 'fungicides': 1000, 'irrigation': 3000,
                'labor_planting': 1800, 'labor_maintenance': 3500, 'labor_harvesting': 3000,
                'equipment_rental': 2000, 'transportation': 1200, 'storage': 800,
                'miscellaneous': 1000
            },
            'sugarcane': {
                'seeds_per_acre': 8000, 'fertilizers_npk': 6000, 'organic_manure': 3000,
                'pesticides': 1500, 'fungicides': 800, 'irrigation': 5000,
                'labor_planting': 3000, 'labor_maintenance': 4000, 'labor_harvesting': 5000,
                'equipment_rental': 3000, 'transportation': 2000, 'storage': 500,
                'miscellaneous': 1500
            },
            'potato': {
                'seeds_per_acre': 6000, 'fertilizers_npk': 4000, 'organic_manure': 2000,
                'pesticides': 1200, 'fungicides': 800, 'irrigation': 2500,
                'labor_planting': 2500, 'labor_maintenance': 2000, 'labor_harvesting': 2500,
                'equipment_rental': 1500, 'transportation': 1500, 'storage': 1000,
                'miscellaneous': 1000
            },
            'tomato': {
                'seeds_per_acre': 3000, 'fertilizers_npk': 3500, 'organic_manure': 2000,
                'pesticides': 1500, 'fungicides': 1000, 'irrigation': 3000,
                'labor_planting': 2000, 'labor_maintenance': 3000, 'labor_harvesting': 2500,
                'equipment_rental': 1000, 'transportation': 1200, 'storage': 800,
                'miscellaneous': 1000
            },
            'onion': {
                'seeds_per_acre': 2500, 'fertilizers_npk': 3000, 'organic_manure': 1500,
                'pesticides': 1000, 'fungicides': 600, 'irrigation': 2500,
                'labor_planting': 2000, 'labor_maintenance': 2500, 'labor_harvesting': 2000,
                'equipment_rental': 1000, 'transportation': 1000, 'storage': 1200,
                'miscellaneous': 800
            },
            'default': {
                'seeds_per_acre': 2000, 'fertilizers_npk': 3500, 'organic_manure': 1500,
                'pesticides': 1000, 'fungicides': 600, 'irrigation': 2500,
                'labor_planting': 1500, 'labor_maintenance': 2500, 'labor_harvesting': 2000,
                'equipment_rental': 1500, 'transportation': 1000, 'storage': 600,
                'miscellaneous': 800
            }
        }

    def _get_crop_yield_database(self) -> Dict[str, float]:
        """Get crop-specific average yield database (quintals per acre)"""
        
        return {
            'wheat': 18.0, 'rice': 20.0, 'paddy': 20.0, 'maize': 22.0,
            'corn': 22.0, 'cotton': 8.0, 'sugarcane': 300.0, 'soybean': 10.0,
            'groundnut': 12.0, 'peanut': 12.0, 'potato': 80.0, 'tomato': 100.0,
            'onion': 60.0, 'chickpea': 8.0, 'chana': 8.0, 'pigeon pea': 7.0,
            'tur': 7.0, 'mustard': 8.0, 'sunflower': 10.0, 'bajra': 12.0,
            'jowar': 10.0, 'barley': 15.0, 'gram': 8.0, 'lentil': 6.0,
            'default': 15.0
        }
    
    def _get_soil_cost_adjustment(self, soil_type: str) -> float:
        """Get cost adjustment factor based on soil type"""
        
        adjustments = {
            'loamy': 1.0,
            'clay': 1.1,  # Needs more amendments
            'sandy': 1.15,  # Needs more fertilizer
            'silt': 1.05,
            'black': 0.95,  # Naturally fertile
            'red': 1.1,
            'alluvial': 0.95,
            'laterite': 1.2
        }
        
        return adjustments.get(soil_type.lower(), 1.0)
    
    def _get_soil_yield_factor(self, soil_type: str) -> float:
        """Get yield factor based on soil type"""
        
        factors = {
            'loamy': 1.0,
            'clay': 0.95,
            'sandy': 0.85,
            'silt': 0.95,
            'black': 1.1,  # Excellent for cotton
            'red': 0.9,
            'alluvial': 1.15,  # Very fertile
            'laterite': 0.8
        }
        
        return factors.get(soil_type.lower(), 1.0)
    
    def _get_location_cost_adjustment(self, state: str) -> float:
        """Get cost adjustment based on state (labor and input costs vary)"""
        
        adjustments = {
            'punjab': 1.15, 'haryana': 1.12, 'delhi': 1.20,
            'uttar pradesh': 1.0, 'bihar': 0.85, 'west bengal': 0.95,
            'maharashtra': 1.05, 'karnataka': 1.0, 'tamil nadu': 1.05,
            'andhra pradesh': 0.95, 'telangana': 0.95, 'kerala': 1.10,
            'gujarat': 1.05, 'rajasthan': 0.95, 'madhya pradesh': 0.90,
            'chhattisgarh': 0.85, 'odisha': 0.85, 'jharkhand': 0.85
        }
        
        return adjustments.get(state.lower(), 1.0)
    
    def _get_location_yield_factor(self, state: str) -> float:
        """Get yield factor based on state (agricultural productivity varies)"""
        
        factors = {
            'punjab': 1.25, 'haryana': 1.20, 'uttar pradesh': 1.05,
            'bihar': 0.85, 'west bengal': 1.0, 'maharashtra': 1.0,
            'karnataka': 1.05, 'tamil nadu': 1.10, 'andhra pradesh': 1.05,
            'telangana': 1.0, 'kerala': 0.95, 'gujarat': 1.10,
            'rajasthan': 0.85, 'madhya pradesh': 0.95, 'chhattisgarh': 0.90,
            'odisha': 0.90, 'jharkhand': 0.85
        }
        
        return factors.get(state.lower(), 1.0)
    
    def _get_season_yield_factor(self, crop_name: str, season: Optional[str]) -> float:
        """Get yield factor based on season suitability"""
        
        if not season:
            return 1.0
        
        season = season.lower()
        
        # Crop-season suitability
        optimal_seasons = {
            'wheat': ['rabi'], 'rice': ['kharif'], 'paddy': ['kharif'],
            'maize': ['kharif', 'rabi'], 'cotton': ['kharif'],
            'sugarcane': ['perennial'], 'potato': ['rabi'], 'tomato': ['rabi', 'zaid'],
            'onion': ['rabi', 'kharif'], 'mustard': ['rabi']
        }
        
        if crop_name in optimal_seasons:
            if season in optimal_seasons[crop_name]:
                return 1.1  # Optimal season
            else:
                return 0.85  # Sub-optimal season
        
        return 1.0

    def _assess_weather_risk(self, location: Dict[str, Any], season: Optional[str]) -> Dict[str, Any]:
        """Assess weather-related risks"""
        
        # Default risk assessment
        risk_score = 5
        risk_level = 'medium'
        description = 'Moderate weather risk based on seasonal patterns'
        mitigation = 'Monitor weather forecasts and follow advisories'
        
        # Try to get real weather data
        if self.weather_tools and 'latitude' in location and 'longitude' in location:
            try:
                weather_data = self.weather_tools.get_farming_weather_insights(
                    location['latitude'], location['longitude']
                )
                
                if weather_data.get('success'):
                    alerts = weather_data.get('adverse_weather_alerts', [])
                    
                    if len(alerts) >= 3:
                        risk_score = 8
                        risk_level = 'high'
                        description = f'{len(alerts)} adverse weather alerts in next 5 days'
                        mitigation = 'Consider delaying planting or take protective measures'
                    elif len(alerts) >= 1:
                        risk_score = 6
                        risk_level = 'medium'
                        description = f'{len(alerts)} weather alert(s) expected'
                        mitigation = 'Prepare for adverse weather conditions'
                    else:
                        risk_score = 3
                        risk_level = 'low'
                        description = 'Favorable weather conditions expected'
                        mitigation = 'Continue normal operations'
            except Exception as e:
                logger.warning(f"Weather risk assessment failed: {e}")
        
        return {
            'score': risk_score,
            'level': risk_level,
            'description': description,
            'mitigation': mitigation
        }
    
    def _assess_pest_disease_risk(self, crop_name: str, season: Optional[str]) -> Dict[str, Any]:
        """Assess pest and disease risks"""
        
        # Crop-specific pest/disease risk database
        high_risk_crops = ['cotton', 'tomato', 'potato', 'rice', 'paddy']
        medium_risk_crops = ['wheat', 'maize', 'onion', 'sugarcane']
        
        if crop_name in high_risk_crops:
            return {
                'score': 7,
                'level': 'high',
                'description': f'{crop_name.title()} is susceptible to pests and diseases',
                'mitigation': 'Regular monitoring, integrated pest management, timely spraying'
            }
        elif crop_name in medium_risk_crops:
            return {
                'score': 5,
                'level': 'medium',
                'description': f'{crop_name.title()} has moderate pest/disease risk',
                'mitigation': 'Periodic monitoring and preventive measures'
            }
        else:
            return {
                'score': 3,
                'level': 'low',
                'description': f'{crop_name.title()} has relatively low pest/disease risk',
                'mitigation': 'Basic preventive measures sufficient'
            }
    
    def _assess_market_risk(self, crop_name: str) -> Dict[str, Any]:
        """Assess market price volatility risk"""
        
        # Market volatility database
        high_volatility_crops = ['tomato', 'onion', 'potato', 'cotton']
        low_volatility_crops = ['wheat', 'rice', 'paddy', 'sugarcane']
        
        if crop_name in high_volatility_crops:
            return {
                'score': 7,
                'level': 'high',
                'description': f'{crop_name.title()} prices are highly volatile',
                'mitigation': 'Consider contract farming, storage options, or price hedging'
            }
        elif crop_name in low_volatility_crops:
            return {
                'score': 3,
                'level': 'low',
                'description': f'{crop_name.title()} has stable government-supported prices',
                'mitigation': 'Sell at MSP or through government procurement'
            }
        else:
            return {
                'score': 5,
                'level': 'medium',
                'description': f'{crop_name.title()} has moderate price fluctuations',
                'mitigation': 'Monitor market trends and time sales appropriately'
            }
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on overall risk level"""
        
        recommendations = {
            'low': 'Good opportunity with manageable risks. Proceed with confidence.',
            'medium': 'Moderate risk level. Implement risk mitigation strategies and monitor closely.',
            'high': 'High risk detected. Consider alternatives or ensure adequate risk management measures.'
        }
        
        return recommendations.get(risk_level, 'Assess risks carefully before proceeding.')
    
    def _store_profitability_analysis(self, analysis_id: str, data: Dict[str, Any]):
        """Store profitability analysis in DynamoDB"""
        try:
            timestamp = int(datetime.now().timestamp())
            
            self.profitability_table.put_item(
                Item={
                    'analysis_id': analysis_id,
                    'timestamp': timestamp,
                    'crop_name': data['crop_name'],
                    'location': json.dumps(data['location']),
                    'scenarios': json.dumps(data['scenarios'], default=str),
                    'risk_assessment': json.dumps(data['risk_assessment']),
                    'created_at': datetime.now().isoformat(),
                    'ttl': timestamp + (90 * 24 * 3600)  # 90 days retention
                }
            )
            logger.info(f"Profitability analysis stored: {analysis_id}")
        except Exception as e:
            logger.error(f"Failed to store profitability analysis: {e}")


# Tool functions for agent integration (Strands @tool for orchestrator)
try:
    from strands import tool
except ImportError:
    def tool(fn):
        return fn  # no-op if Strands not installed


def create_profitability_calculator_tools(region: str = "us-east-1") -> ProfitabilityCalculatorTools:
    """Factory function to create profitability calculator tools instance"""
    return ProfitabilityCalculatorTools(region=region)


@tool
def calculate_profitability_tool(crop_name: str, farm_size_acres: float,
                                location: Dict[str, Any], soil_type: str = 'loamy') -> str:
    """
    Calculate crop profitability (costs, yield, revenue, ROI) for a crop and farm size. Use when the user asks about profit, ROI, or whether to grow a crop. Location can be e.g. {'state': 'Punjab'}.
    """
    tools = create_profitability_calculator_tools()
    result = tools.calculate_comprehensive_profitability(
        crop_name, farm_size_acres, location, soil_type
    )
    
    if result['success']:
        avg = result['profitability_scenarios']['average']
        return f"""Profitability Analysis for {result['crop_name'].title()}:

Total Investment: ₹{result['cost_breakdown']['total_farm_cost']:,.2f}
Expected Yield: {avg['total_yield_quintals']} quintals
Expected Revenue: ₹{avg['total_revenue']:,.2f}
Net Profit: ₹{avg['net_profit']:,.2f}
ROI: {avg['roi_percent']}%
Risk Level: {result['risk_assessment']['overall_risk_level'].upper()}
"""
    else:
        return f"Error: {result.get('error', 'Failed to calculate profitability')}"
