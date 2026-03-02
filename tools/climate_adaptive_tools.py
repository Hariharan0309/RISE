"""
RISE Climate-Adaptive Recommendations Tools
Tools for climate data analysis and adaptive farming recommendations
"""

import boto3
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class ClimateAdaptiveTools:
    """Climate-adaptive recommendations tools for RISE farming assistant"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize climate-adaptive tools with AWS clients
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        
        # DynamoDB table for climate analysis storage
        self.climate_table = self.dynamodb.Table('RISE-ClimateAnalysis')
        
        # Model configuration
        self.model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
        
        logger.info(f"Climate-adaptive tools initialized in region {region}")
    
    def analyze_climate_data(self,
                            location: Dict[str, Any],
                            historical_weather: List[Dict[str, Any]],
                            current_season: str) -> Dict[str, Any]:
        """
        Analyze climate data and identify long-term trends
        
        Args:
            location: Location details (latitude, longitude, name)
            historical_weather: Historical weather data (past 30-90 days)
            current_season: Current farming season (Kharif/Rabi/Zaid)
        
        Returns:
            Dict with climate analysis results
        """
        try:
            # Calculate climate trends
            trends = self._calculate_climate_trends(historical_weather)
            
            # Identify climate risks
            risks = self._identify_climate_risks(trends, current_season)
            
            # Generate AI-powered analysis
            ai_analysis = self._generate_ai_climate_analysis(
                location, trends, risks, current_season
            )
            
            # Store analysis results
            analysis_id = self._store_climate_analysis(
                location, trends, risks, ai_analysis
            )
            
            return {
                'success': True,
                'analysis_id': analysis_id,
                'location': location,
                'trends': trends,
                'risks': risks,
                'ai_insights': ai_analysis,
                'season': current_season,
                'analyzed_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Climate analysis error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_resilient_crop_varieties(self,
                                    location: Dict[str, Any],
                                    climate_risks: List[str],
                                    soil_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Recommend resilient crop varieties based on climate projections
        
        Args:
            location: Location details
            climate_risks: Identified climate risks (drought, flood, heat stress, etc.)
            soil_type: Optional soil type information
        
        Returns:
            Dict with crop variety recommendations
        """
        try:
            # Build recommendation prompt
            prompt = self._build_crop_variety_prompt(location, climate_risks, soil_type)
            
            # Get AI recommendations
            response = self._invoke_bedrock(prompt)
            
            # Parse recommendations
            recommendations = self._parse_crop_recommendations(response)
            
            return {
                'success': True,
                'location': location,
                'climate_risks': climate_risks,
                'recommended_varieties': recommendations,
                'confidence_score': self._calculate_confidence_score(recommendations)
            }
        
        except Exception as e:
            logger.error(f"Crop variety recommendation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_water_efficient_techniques(self,
                                      location: Dict[str, Any],
                                      water_scarcity_level: str,
                                      crop_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Recommend water-efficient farming techniques
        
        Args:
            location: Location details
            water_scarcity_level: Level of water scarcity (low/medium/high/severe)
            crop_type: Optional current or planned crop type
        
        Returns:
            Dict with water-efficient technique recommendations
        """
        try:
            # Get technique recommendations
            techniques = self._get_water_saving_techniques(
                water_scarcity_level, crop_type
            )
            
            # Generate AI-powered implementation guidance
            implementation_guide = self._generate_implementation_guidance(
                location, techniques, crop_type
            )
            
            # Calculate cost-benefit analysis
            cost_benefit = self._calculate_cost_benefit(techniques)
            
            return {
                'success': True,
                'location': location,
                'water_scarcity_level': water_scarcity_level,
                'recommended_techniques': techniques,
                'implementation_guide': implementation_guide,
                'cost_benefit_analysis': cost_benefit
            }
        
        except Exception as e:
            logger.error(f"Water-efficient techniques error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_seasonal_advice(self,
                                location: Dict[str, Any],
                                season: str,
                                climate_trends: Dict[str, Any],
                                farmer_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate seasonal farming advice based on climate patterns
        
        Args:
            location: Location details
            season: Farming season (Kharif/Rabi/Zaid)
            climate_trends: Climate trend analysis
            farmer_profile: Optional farmer profile (crops, land size, etc.)
        
        Returns:
            Dict with seasonal advice
        """
        try:
            # Build seasonal advice prompt
            prompt = self._build_seasonal_advice_prompt(
                location, season, climate_trends, farmer_profile
            )
            
            # Get AI-generated advice
            response = self._invoke_bedrock(prompt)
            
            # Parse and structure advice
            advice = self._parse_seasonal_advice(response)
            
            return {
                'success': True,
                'location': location,
                'season': season,
                'advice': advice,
                'generated_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Seasonal advice generation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_climate_trends(self, historical_weather: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate climate trends from historical data"""
        if not historical_weather:
            return {
                'temperature_trend': 'stable',
                'rainfall_trend': 'stable',
                'extreme_events': []
            }
        
        # Calculate temperature trends
        temps = [w.get('temp_avg', 0) for w in historical_weather]
        temp_avg = sum(temps) / len(temps) if temps else 0
        temp_max = max(temps) if temps else 0
        temp_min = min(temps) if temps else 0
        
        # Calculate rainfall trends
        rainfall = [w.get('rainfall', 0) for w in historical_weather]
        rainfall_total = sum(rainfall)
        rainfall_avg = rainfall_total / len(rainfall) if rainfall else 0
        
        # Identify extreme events
        extreme_events = []
        for i, w in enumerate(historical_weather):
            if w.get('temp_max', 0) > 40:
                extreme_events.append({
                    'type': 'extreme_heat',
                    'date': w.get('date'),
                    'value': w.get('temp_max')
                })
            if w.get('rainfall', 0) > 50:
                extreme_events.append({
                    'type': 'heavy_rainfall',
                    'date': w.get('date'),
                    'value': w.get('rainfall')
                })
        
        # Determine trends
        temp_trend = 'increasing' if temp_avg > 30 else 'stable'
        rainfall_trend = 'decreasing' if rainfall_avg < 2 else 'stable'
        
        return {
            'temperature': {
                'average': round(temp_avg, 1),
                'max': round(temp_max, 1),
                'min': round(temp_min, 1),
                'trend': temp_trend
            },
            'rainfall': {
                'total': round(rainfall_total, 1),
                'average': round(rainfall_avg, 1),
                'trend': rainfall_trend
            },
            'extreme_events': extreme_events,
            'data_points': len(historical_weather)
        }
    
    def _identify_climate_risks(self, trends: Dict[str, Any], season: str) -> List[Dict[str, Any]]:
        """Identify climate risks based on trends"""
        risks = []
        
        # Temperature-based risks
        temp_avg = trends.get('temperature', {}).get('average', 0)
        temp_max = trends.get('temperature', {}).get('max', 0)
        
        if temp_avg > 35:
            risks.append({
                'type': 'heat_stress',
                'severity': 'high',
                'description': 'Prolonged high temperatures may cause heat stress in crops',
                'mitigation': 'Consider heat-tolerant varieties and adequate irrigation'
            })
        
        if temp_max >= 42:
            risks.append({
                'type': 'extreme_heat',
                'severity': 'critical',
                'description': 'Extreme heat events can severely damage crops',
                'mitigation': 'Implement shade nets and increase irrigation frequency'
            })
        
        # Rainfall-based risks
        rainfall_avg = trends.get('rainfall', {}).get('average', 0)
        rainfall_trend = trends.get('rainfall', {}).get('trend', 'stable')
        
        if rainfall_avg < 1 or rainfall_trend == 'decreasing':
            risks.append({
                'type': 'drought',
                'severity': 'high',
                'description': 'Low rainfall pattern indicates drought risk',
                'mitigation': 'Adopt water-efficient irrigation and drought-resistant crops'
            })
        
        # Extreme event risks
        extreme_events = trends.get('extreme_events', [])
        if len(extreme_events) > 5:
            risks.append({
                'type': 'climate_variability',
                'severity': 'medium',
                'description': 'High frequency of extreme weather events',
                'mitigation': 'Diversify crops and implement climate-resilient practices'
            })
        
        return risks
    
    def _generate_ai_climate_analysis(self,
                                     location: Dict[str, Any],
                                     trends: Dict[str, Any],
                                     risks: List[Dict[str, Any]],
                                     season: str) -> str:
        """Generate AI-powered climate analysis"""
        prompt = f"""Analyze the following climate data for a farming location in India:

Location: {location.get('name', 'Unknown')}
Season: {season}

Climate Trends:
- Temperature: {trends.get('temperature', {}).get('average', 0)}°C average, trend: {trends.get('temperature', {}).get('trend', 'stable')}
- Rainfall: {trends.get('rainfall', {}).get('average', 0)}mm average, trend: {trends.get('rainfall', {}).get('trend', 'stable')}
- Extreme events: {len(trends.get('extreme_events', []))} recorded

Identified Risks:
{json.dumps(risks, indent=2)}

Provide a concise climate analysis (3-4 sentences) focusing on:
1. Key climate patterns affecting farming
2. Most significant risks to address
3. Overall climate adaptation priority

Keep the response practical and farmer-friendly."""

        try:
            response = self._invoke_bedrock(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return "Climate analysis unavailable. Please consult local agricultural experts."
    
    def _build_crop_variety_prompt(self,
                                  location: Dict[str, Any],
                                  climate_risks: List[str],
                                  soil_type: Optional[str]) -> str:
        """Build prompt for crop variety recommendations"""
        return f"""Recommend resilient crop varieties for Indian farming:

Location: {location.get('name', 'Unknown')}
Climate Risks: {', '.join(climate_risks)}
Soil Type: {soil_type or 'Not specified'}

Provide 3-5 crop variety recommendations that are:
1. Resilient to the identified climate risks
2. Suitable for the soil type and location
3. Economically viable for smallholder farmers
4. Available in India

For each variety, provide:
- Crop name and variety
- Key resilience features
- Expected yield
- Market demand
- Confidence score (0-100)

Format as JSON array."""
    
    def _get_water_saving_techniques(self,
                                    water_scarcity_level: str,
                                    crop_type: Optional[str]) -> List[Dict[str, Any]]:
        """Get water-saving technique recommendations"""
        techniques = []
        
        # Drip irrigation
        if water_scarcity_level in ['medium', 'high', 'severe']:
            techniques.append({
                'name': 'Drip Irrigation',
                'description': 'Delivers water directly to plant roots, reducing water waste by 30-50%',
                'water_savings': '30-50%',
                'initial_cost': 'Medium (₹25,000-50,000 per acre)',
                'maintenance': 'Low',
                'suitability': 'All crops, especially vegetables and fruits',
                'priority': 'high'
            })
        
        # Mulching
        techniques.append({
            'name': 'Mulching',
            'description': 'Covers soil to reduce evaporation and maintain moisture',
            'water_savings': '20-30%',
            'initial_cost': 'Low (₹2,000-5,000 per acre)',
            'maintenance': 'Low',
            'suitability': 'All crops',
            'priority': 'high'
        })
        
        # Rainwater harvesting
        if water_scarcity_level in ['high', 'severe']:
            techniques.append({
                'name': 'Rainwater Harvesting',
                'description': 'Collects and stores rainwater for irrigation during dry periods',
                'water_savings': '40-60%',
                'initial_cost': 'High (₹50,000-1,50,000)',
                'maintenance': 'Medium',
                'suitability': 'All crops',
                'priority': 'medium'
            })
        
        # Sprinkler irrigation
        techniques.append({
            'name': 'Sprinkler Irrigation',
            'description': 'Sprays water over crops, more efficient than flood irrigation',
            'water_savings': '20-40%',
            'initial_cost': 'Medium (₹30,000-60,000 per acre)',
            'maintenance': 'Medium',
            'suitability': 'Field crops, vegetables',
            'priority': 'medium'
        })
        
        # Conservation tillage
        techniques.append({
            'name': 'Conservation Tillage',
            'description': 'Minimal soil disturbance to retain moisture',
            'water_savings': '15-25%',
            'initial_cost': 'Low (₹5,000-10,000)',
            'maintenance': 'Low',
            'suitability': 'All crops',
            'priority': 'medium'
        })
        
        return techniques
    
    def _generate_implementation_guidance(self,
                                         location: Dict[str, Any],
                                         techniques: List[Dict[str, Any]],
                                         crop_type: Optional[str]) -> str:
        """Generate implementation guidance using AI"""
        prompt = f"""Provide practical implementation guidance for water-efficient farming techniques:

Location: {location.get('name', 'Unknown')}
Crop Type: {crop_type or 'General farming'}

Recommended Techniques:
{json.dumps([t['name'] for t in techniques], indent=2)}

Provide step-by-step implementation guidance (5-7 steps) that is:
1. Practical for smallholder farmers
2. Cost-effective
3. Easy to understand
4. Specific to Indian farming context

Keep the response concise and actionable."""

        try:
            response = self._invoke_bedrock(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Implementation guidance error: {e}")
            return "Consult local agricultural extension officers for implementation guidance."
    
    def _calculate_cost_benefit(self, techniques: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate cost-benefit analysis for techniques"""
        total_initial_cost = 0
        total_water_savings = 0
        
        for technique in techniques:
            # Extract cost range (simplified)
            cost_str = technique.get('initial_cost', '')
            if 'Low' in cost_str:
                total_initial_cost += 5000
            elif 'Medium' in cost_str:
                total_initial_cost += 40000
            elif 'High' in cost_str:
                total_initial_cost += 100000
            
            # Extract water savings percentage
            savings_str = technique.get('water_savings', '0%')
            savings_pct = int(savings_str.split('-')[0].replace('%', ''))
            total_water_savings += savings_pct
        
        avg_water_savings = total_water_savings / len(techniques) if techniques else 0
        
        # Estimate annual savings (simplified)
        annual_water_cost = 15000  # Average per acre
        annual_savings = annual_water_cost * (avg_water_savings / 100)
        payback_period = total_initial_cost / annual_savings if annual_savings > 0 else 0
        
        return {
            'total_initial_investment': f"₹{total_initial_cost:,}",
            'average_water_savings': f"{avg_water_savings:.0f}%",
            'estimated_annual_savings': f"₹{annual_savings:,.0f}",
            'payback_period_years': round(payback_period, 1),
            'roi_5_years': f"{((annual_savings * 5 - total_initial_cost) / total_initial_cost * 100):.0f}%"
        }
    
    def _build_seasonal_advice_prompt(self,
                                     location: Dict[str, Any],
                                     season: str,
                                     climate_trends: Dict[str, Any],
                                     farmer_profile: Optional[Dict[str, Any]]) -> str:
        """Build prompt for seasonal advice"""
        return f"""Generate seasonal farming advice for Indian farmers:

Location: {location.get('name', 'Unknown')}
Season: {season}
Climate Trends: {json.dumps(climate_trends, indent=2)}
Farmer Profile: {json.dumps(farmer_profile, indent=2) if farmer_profile else 'Not provided'}

Provide comprehensive seasonal advice covering:
1. Crop selection for this season
2. Planting and sowing timing
3. Irrigation management
4. Pest and disease prevention
5. Weather-specific precautions
6. Expected challenges and solutions

Keep advice practical, specific to the season, and suitable for smallholder farmers.
Format as structured sections."""
    
    def _parse_seasonal_advice(self, response: str) -> Dict[str, Any]:
        """Parse seasonal advice from AI response"""
        # Simple parsing - in production, use more sophisticated parsing
        return {
            'full_advice': response,
            'key_recommendations': self._extract_key_points(response),
            'priority_actions': self._extract_priority_actions(response)
        }
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from advice text"""
        # Simple extraction - look for numbered or bulleted points
        lines = text.split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove numbering/bullets
                clean_line = line.lstrip('0123456789.-•) ').strip()
                if clean_line:
                    key_points.append(clean_line)
        
        return key_points[:10]  # Limit to top 10
    
    def _extract_priority_actions(self, text: str) -> List[str]:
        """Extract priority actions from advice text"""
        # Look for action-oriented phrases
        action_keywords = ['should', 'must', 'need to', 'important to', 'ensure', 'implement']
        lines = text.split('.')
        priority_actions = []
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in action_keywords):
                priority_actions.append(line)
        
        return priority_actions[:5]  # Limit to top 5
    
    def _parse_crop_recommendations(self, response: str) -> List[Dict[str, Any]]:
        """Parse crop recommendations from AI response"""
        try:
            # Try to parse as JSON
            recommendations = json.loads(response)
            if isinstance(recommendations, list):
                return recommendations
        except json.JSONDecodeError:
            pass
        
        # Fallback: return structured placeholder
        return [{
            'crop_name': 'Consult local agricultural experts',
            'variety': 'N/A',
            'resilience_features': ['AI parsing error'],
            'expected_yield': 'N/A',
            'market_demand': 'N/A',
            'confidence_score': 0
        }]
    
    def _calculate_confidence_score(self, recommendations: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score for recommendations"""
        if not recommendations:
            return 0.0
        
        scores = [r.get('confidence_score', 50) for r in recommendations]
        return sum(scores) / len(scores)
    
    def _invoke_bedrock(self, prompt: str) -> str:
        """Invoke Amazon Bedrock for AI generation"""
        try:
            body = json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 2000,
                'messages': [{
                    'role': 'user',
                    'content': prompt
                }],
                'temperature': 0.7
            })
            
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
        
        except Exception as e:
            logger.error(f"Bedrock invocation error: {e}")
            raise
    
    def _store_climate_analysis(self,
                                location: Dict[str, Any],
                                trends: Dict[str, Any],
                                risks: List[Dict[str, Any]],
                                ai_analysis: str) -> str:
        """Store climate analysis in DynamoDB"""
        try:
            analysis_id = f"climate_{location.get('name', 'unknown')}_{int(datetime.now().timestamp())}"
            
            self.climate_table.put_item(
                Item={
                    'analysis_id': analysis_id,
                    'location': json.dumps(location),
                    'trends': json.dumps(trends),
                    'risks': json.dumps(risks),
                    'ai_analysis': ai_analysis,
                    'created_at': datetime.now().isoformat(),
                    'ttl': int((datetime.now() + timedelta(days=90)).timestamp())
                }
            )
            
            return analysis_id
        
        except Exception as e:
            logger.error(f"Storage error: {e}")
            return f"temp_{int(datetime.now().timestamp())}"


# Tool functions for agent integration

def create_climate_adaptive_tools(region: str = "us-east-1") -> ClimateAdaptiveTools:
    """
    Factory function to create climate-adaptive tools instance
    
    Args:
        region: AWS region
    
    Returns:
        ClimateAdaptiveTools instance
    """
    return ClimateAdaptiveTools(region=region)
