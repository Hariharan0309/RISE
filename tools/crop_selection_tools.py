"""
RISE Crop Selection Tools
Tools for recommending suitable crops based on soil, climate, and market demand
"""

import boto3
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from calendar import month_name

logger = logging.getLogger(__name__)


class CropSelectionTools:
    """Crop selection and recommendation tools using Amazon Bedrock"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize crop selection tools
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # DynamoDB table for farm data
        self.farm_data_table = self.dynamodb.Table('RISE-FarmData')
        
        # Model configuration
        self.model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
        
        # Seasons
        self.seasons = ['kharif', 'rabi', 'zaid', 'perennial']
        
        logger.info(f"Crop selection tools initialized in region {region}")
    
    def recommend_crops(self,
                       soil_analysis: Dict[str, Any],
                       location: Dict[str, str],
                       farm_size_acres: float,
                       climate_data: Optional[Dict[str, Any]] = None,
                       market_preferences: Optional[Dict[str, Any]] = None,
                       farmer_experience: Optional[str] = None) -> Dict[str, Any]:
        """
        Recommend suitable crops based on soil, climate, and market demand
        
        Args:
            soil_analysis: Soil analysis results from soil_analysis_tools
            location: Location information (state, district)
            farm_size_acres: Farm size in acres
            climate_data: Optional climate/weather data
            market_preferences: Optional market demand preferences
            farmer_experience: Optional farmer experience level
        
        Returns:
            Dict with crop recommendations
        """
        try:
            # Build prompt for crop recommendations
            prompt = self._build_crop_recommendation_prompt(
                soil_analysis, location, farm_size_acres,
                climate_data, market_preferences, farmer_experience
            )
            
            # Call Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 4000,
                    'messages': [
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    'temperature': 0.3
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            recommendations_text = response_body['content'][0]['text']
            
            # Parse crop recommendations
            recommendations = self._parse_crop_recommendations(recommendations_text)
            
            # Generate recommendation ID
            recommendation_id = f"crop_rec_{uuid.uuid4().hex[:12]}"
            
            # Store recommendations
            self._store_crop_recommendations(
                recommendation_id=recommendation_id,
                soil_analysis=soil_analysis,
                location=location,
                recommendations=recommendations
            )
            
            return {
                'success': True,
                'recommendation_id': recommendation_id,
                **recommendations,
                'full_recommendations': recommendations_text
            }
        
        except Exception as e:
            logger.error(f"Crop recommendation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def calculate_crop_profitability(self,
                                    crop_name: str,
                                    farm_size_acres: float,
                                    location: Dict[str, str],
                                    soil_type: str,
                                    input_costs: Optional[Dict[str, float]] = None,
                                    market_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate crop profitability with cost-benefit analysis
        
        Args:
            crop_name: Name of the crop
            farm_size_acres: Farm size in acres
            location: Location information
            soil_type: Soil type
            input_costs: Optional custom input costs
            market_price: Optional current market price per quintal
        
        Returns:
            Dict with profitability analysis
        """
        try:
            # Use mock market data if not provided
            if not market_price:
                market_price = self._get_mock_market_price(crop_name, location)
            
            # Build prompt for profitability calculation
            prompt = self._build_profitability_prompt(
                crop_name, farm_size_acres, location, soil_type,
                input_costs, market_price
            )
            
            # Call Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 3000,
                    'messages': [
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    'temperature': 0.3
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            profitability_text = response_body['content'][0]['text']
            
            # Parse profitability data
            profitability = self._parse_profitability(profitability_text)
            
            return {
                'success': True,
                'crop_name': crop_name,
                'farm_size_acres': farm_size_acres,
                'market_price_per_quintal': market_price,
                **profitability,
                'full_analysis': profitability_text
            }
        
        except Exception as e:
            logger.error(f"Profitability calculation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def generate_seasonal_calendar(self,
                                   location: Dict[str, str],
                                   soil_type: str,
                                   farm_size_acres: float,
                                   selected_crops: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate seasonal crop calendar for planning
        
        Args:
            location: Location information
            soil_type: Soil type
            farm_size_acres: Farm size in acres
            selected_crops: Optional list of crops to include
        
        Returns:
            Dict with seasonal calendar
        """
        try:
            # Build prompt for seasonal calendar
            prompt = self._build_seasonal_calendar_prompt(
                location, soil_type, farm_size_acres, selected_crops
            )
            
            # Call Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 3500,
                    'messages': [
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    'temperature': 0.3
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            calendar_text = response_body['content'][0]['text']
            
            # Parse calendar data
            calendar = self._parse_seasonal_calendar(calendar_text)
            
            return {
                'success': True,
                'location': location,
                'soil_type': soil_type,
                **calendar,
                'full_calendar': calendar_text
            }
        
        except Exception as e:
            logger.error(f"Seasonal calendar generation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def compare_crop_options(self,
                            crop_list: List[str],
                            soil_analysis: Dict[str, Any],
                            location: Dict[str, str],
                            farm_size_acres: float,
                            comparison_criteria: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compare multiple crop options side by side
        
        Args:
            crop_list: List of crops to compare
            soil_analysis: Soil analysis results
            location: Location information
            farm_size_acres: Farm size in acres
            comparison_criteria: Optional criteria (profitability, water_needs, labor, etc.)
        
        Returns:
            Dict with crop comparison
        """
        try:
            # Default comparison criteria
            if not comparison_criteria:
                comparison_criteria = [
                    'profitability', 'water_requirements', 'labor_needs',
                    'market_demand', 'risk_level', 'soil_suitability'
                ]
            
            # Build prompt for crop comparison
            prompt = self._build_crop_comparison_prompt(
                crop_list, soil_analysis, location, farm_size_acres, comparison_criteria
            )
            
            # Call Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 3500,
                    'messages': [
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    'temperature': 0.3
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            comparison_text = response_body['content'][0]['text']
            
            # Parse comparison data
            comparison = self._parse_crop_comparison(comparison_text)
            
            return {
                'success': True,
                'crops_compared': crop_list,
                'comparison_criteria': comparison_criteria,
                **comparison,
                'full_comparison': comparison_text
            }
        
        except Exception as e:
            logger.error(f"Crop comparison error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _build_crop_recommendation_prompt(self,
                                         soil_analysis: Dict[str, Any],
                                         location: Dict[str, str],
                                         farm_size_acres: float,
                                         climate_data: Optional[Dict[str, Any]],
                                         market_preferences: Optional[Dict[str, Any]],
                                         farmer_experience: Optional[str]) -> str:
        """Build prompt for crop recommendations"""
        
        prompt = f"""You are an expert agricultural advisor specializing in crop selection.
Recommend suitable crops based on the following comprehensive analysis:

LOCATION: {location.get('district', 'Unknown')}, {location.get('state', 'Unknown')}
FARM SIZE: {farm_size_acres} acres

SOIL ANALYSIS:
- Soil Type: {soil_analysis.get('soil_type', 'unknown')}
- Fertility Level: {soil_analysis.get('fertility_level', 'unknown')}
- pH Level: {soil_analysis.get('ph_level', 'not tested')}
- NPK Levels:
  * Nitrogen: {soil_analysis.get('npk_levels', {}).get('nitrogen', 'unknown')}
  * Phosphorus: {soil_analysis.get('npk_levels', {}).get('phosphorus', 'unknown')}
  * Potassium: {soil_analysis.get('npk_levels', {}).get('potassium', 'unknown')}
- Organic Matter: {soil_analysis.get('organic_matter', 'not tested')}%
- Deficiencies: {', '.join(soil_analysis.get('deficiencies', ['None']))}
"""
        
        if climate_data:
            prompt += f"\nCLIMATE DATA:\n{json.dumps(climate_data, indent=2)}\n"
        else:
            prompt += "\nCLIMATE DATA: Using typical patterns for the region\n"
        
        if market_preferences:
            prompt += f"\nMARKET PREFERENCES:\n{json.dumps(market_preferences, indent=2)}\n"
        
        if farmer_experience:
            prompt += f"\nFARMER EXPERIENCE: {farmer_experience}\n"
        
        prompt += """
Provide comprehensive crop recommendations in the following format:

1. HIGHLY RECOMMENDED CROPS (Top 3-5):
   For each crop:
   - Crop Name: [local and scientific name]
   - Suitability Score: [1-10]
   - Season: [Kharif/Rabi/Zaid/Perennial]
   - Expected Yield: [quintals per acre]
   - Growing Duration: [days]
   - Water Requirements: [low/medium/high]
   - Labor Requirements: [low/medium/high]
   - Market Demand: [high/medium/low]
   - Current Market Price: [₹ per quintal - estimate]
   - Estimated Revenue: [₹ per acre]
   - Input Costs: [₹ per acre]
   - Net Profit: [₹ per acre]
   - Profit Margin: [%]
   - Risk Level: [low/medium/high]
   - Key Advantages: [list 3-4 points]
   - Challenges: [list 2-3 points]
   - Reasoning: [why this crop is suitable]

2. MODERATELY SUITABLE CROPS (3-4 options):
   (Same format as above)
   - Additional Requirements: [what needs to be done]

3. NOT RECOMMENDED CROPS:
   - Crop names with brief reasons why not suitable

4. CROP ROTATION SUGGESTIONS:
   - Recommended rotation sequence
   - Benefits of rotation
   - Timeline for rotation

5. INTERCROPPING OPPORTUNITIES:
   - Compatible crop combinations
   - Benefits and expected yields
   - Management considerations

6. RISK ASSESSMENT:
   For each recommended crop:
   - Weather risks
   - Pest/disease risks
   - Market risks
   - Mitigation strategies

7. RESOURCE REQUIREMENTS SUMMARY:
   - Total water needs
   - Labor calendar
   - Equipment needed
   - Storage requirements

8. MARKET INTELLIGENCE:
   - Current market trends
   - Price forecasts (next 6 months)
   - Demand patterns
   - Best selling locations
   - Direct buyer opportunities

9. FINANCIAL PLANNING:
   - Total investment needed
   - Cash flow timeline
   - Break-even analysis
   - ROI expectations

Prioritize crops that match the soil conditions, have good market demand, and are suitable for the farmer's experience level.
Provide specific, actionable recommendations with realistic financial projections.
"""
        
        return prompt

    def _build_profitability_prompt(self,
                                   crop_name: str,
                                   farm_size_acres: float,
                                   location: Dict[str, str],
                                   soil_type: str,
                                   input_costs: Optional[Dict[str, float]],
                                   market_price: float) -> str:
        """Build prompt for profitability calculation"""
        
        prompt = f"""You are an expert agricultural economist. Calculate detailed profitability for:

CROP: {crop_name}
FARM SIZE: {farm_size_acres} acres
LOCATION: {location.get('district', 'Unknown')}, {location.get('state', 'Unknown')}
SOIL TYPE: {soil_type}
CURRENT MARKET PRICE: ₹{market_price} per quintal
"""
        
        if input_costs:
            prompt += f"\nPROVIDED INPUT COSTS:\n{json.dumps(input_costs, indent=2)}\n"
        
        prompt += """
Provide comprehensive profitability analysis in the following format:

1. INPUT COSTS (Per Acre):
   - Seeds/Seedlings: [₹]
   - Fertilizers (NPK): [₹]
   - Organic Manure: [₹]
   - Pesticides/Fungicides: [₹]
   - Irrigation: [₹]
   - Labor (planting, maintenance, harvesting): [₹]
   - Equipment/Machinery rental: [₹]
   - Transportation: [₹]
   - Miscellaneous: [₹]
   - TOTAL INPUT COST PER ACRE: [₹]

2. EXPECTED YIELD:
   - Average Yield: [quintals per acre]
   - Optimistic Yield: [quintals per acre]
   - Conservative Yield: [quintals per acre]

3. REVENUE CALCULATION (Per Acre):
   - Average Scenario: [yield × price = ₹]
   - Optimistic Scenario: [yield × price = ₹]
   - Conservative Scenario: [yield × price = ₹]

4. PROFIT CALCULATION (Per Acre):
   - Average Net Profit: [revenue - costs = ₹]
   - Optimistic Net Profit: [₹]
   - Conservative Net Profit: [₹]
   - Profit Margin: [%]

5. TOTAL FARM PROFITABILITY ({farm_size_acres} acres):
   - Total Investment: [₹]
   - Total Revenue (average): [₹]
   - Total Net Profit (average): [₹]
   - ROI: [%]

6. BREAK-EVEN ANALYSIS:
   - Break-even Yield: [quintals per acre]
   - Break-even Price: [₹ per quintal]
   - Safety Margin: [%]

7. RISK FACTORS:
   - Weather risks: [impact on yield/profit]
   - Market price volatility: [potential range]
   - Pest/disease risks: [potential losses]
   - Overall risk rating: [low/medium/high]

8. CASH FLOW TIMELINE:
   - Month 1-2: [expenses]
   - Month 3-4: [expenses]
   - Month 5-6: [expenses]
   - Harvest month: [revenue]
   - Net cash flow: [timeline]

9. COMPARISON WITH ALTERNATIVES:
   - How this crop compares to other options
   - Relative profitability ranking

10. RECOMMENDATIONS:
    - Is this crop financially viable?
    - Suggestions for maximizing profit
    - Cost reduction opportunities
    - Market timing strategies

Provide realistic, region-specific estimates based on current agricultural economics.
"""
        
        return prompt

    def _build_seasonal_calendar_prompt(self,
                                       location: Dict[str, str],
                                       soil_type: str,
                                       farm_size_acres: float,
                                       selected_crops: Optional[List[str]]) -> str:
        """Build prompt for seasonal calendar"""
        
        prompt = f"""You are an expert agricultural planner. Create a comprehensive seasonal crop calendar for:

LOCATION: {location.get('district', 'Unknown')}, {location.get('state', 'Unknown')}
SOIL TYPE: {soil_type}
FARM SIZE: {farm_size_acres} acres
"""
        
        if selected_crops:
            prompt += f"\nSELECTED CROPS: {', '.join(selected_crops)}\n"
        else:
            prompt += "\nCreate calendar for most suitable crops for this region\n"
        
        prompt += """
Provide a detailed seasonal crop calendar in the following format:

1. KHARIF SEASON (Monsoon - June to October):
   For each recommended crop:
   - Crop Name
   - Planting Window: [specific dates/months]
   - Key Activities Timeline:
     * Land preparation: [dates]
     * Sowing/Planting: [dates]
     * First fertilizer application: [dates]
     * Irrigation schedule: [frequency and dates]
     * Pest management: [critical periods]
     * Second fertilizer application: [dates]
     * Harvesting: [dates]
   - Expected Yield: [quintals per acre]
   - Market Timing: [best time to sell]

2. RABI SEASON (Winter - November to March):
   (Same format as Kharif)

3. ZAID SEASON (Summer - March to June):
   (Same format as Kharif)

4. PERENNIAL CROPS:
   - Crop options
   - Planting season
   - Maintenance calendar
   - Harvesting cycles

5. CROP ROTATION PLAN:
   - Year 1: [Kharif crop] → [Rabi crop] → [Zaid crop]
   - Year 2: [rotation sequence]
   - Year 3: [rotation sequence]
   - Benefits of this rotation

6. MONTHLY ACTIVITY CALENDAR:
   For each month (January to December):
   - Primary activities
   - Crops in field
   - Expected labor requirements
   - Critical tasks
   - Weather considerations

7. RESOURCE PLANNING:
   - Peak labor months
   - Irrigation requirements by month
   - Equipment needs by season
   - Input procurement timeline

8. FINANCIAL CALENDAR:
   - Investment periods
   - Expected revenue months
   - Cash flow planning
   - Loan repayment timing

9. MARKET CALENDAR:
   - Best selling months for each crop
   - Price trends by season
   - Storage vs immediate sale decisions

10. RISK MANAGEMENT CALENDAR:
    - Weather risk periods
    - Pest/disease monitoring schedule
    - Insurance coverage periods
    - Contingency planning

Provide specific dates and actionable timelines based on regional agricultural patterns.
Consider local festivals, weather patterns, and market dynamics.
"""
        
        return prompt

    def _build_crop_comparison_prompt(self,
                                     crop_list: List[str],
                                     soil_analysis: Dict[str, Any],
                                     location: Dict[str, str],
                                     farm_size_acres: float,
                                     comparison_criteria: List[str]) -> str:
        """Build prompt for crop comparison"""
        
        prompt = f"""You are an expert agricultural consultant. Compare the following crops side by side:

CROPS TO COMPARE: {', '.join(crop_list)}
LOCATION: {location.get('district', 'Unknown')}, {location.get('state', 'Unknown')}
FARM SIZE: {farm_size_acres} acres
SOIL TYPE: {soil_analysis.get('soil_type', 'unknown')}

COMPARISON CRITERIA: {', '.join(comparison_criteria)}

Provide detailed comparison in the following format:

1. COMPARISON TABLE:
   Create a side-by-side comparison table with these columns:
   - Criteria
   - {' | '.join(crop_list)}

   Include rows for:
   - Soil Suitability (1-10)
   - Water Requirements (liters/acre/season)
   - Growing Duration (days)
   - Labor Requirements (person-days/acre)
   - Input Costs (₹/acre)
   - Expected Yield (quintals/acre)
   - Market Price (₹/quintal)
   - Revenue (₹/acre)
   - Net Profit (₹/acre)
   - Profit Margin (%)
   - Market Demand (high/medium/low)
   - Risk Level (low/medium/high)
   - Technical Difficulty (easy/medium/hard)

2. DETAILED ANALYSIS FOR EACH CROP:
   For each crop:
   - Strengths: [list 4-5 key advantages]
   - Weaknesses: [list 3-4 limitations]
   - Best suited for: [farmer profile/conditions]
   - Not recommended if: [conditions to avoid]

3. PROFITABILITY RANKING:
   Rank crops by:
   - Net profit per acre
   - ROI percentage
   - Risk-adjusted returns

4. RESOURCE REQUIREMENTS COMPARISON:
   - Water: [rank from lowest to highest]
   - Labor: [rank from lowest to highest]
   - Capital: [rank from lowest to highest]
   - Technical expertise: [rank from easiest to hardest]

5. MARKET ANALYSIS:
   For each crop:
   - Current demand trend
   - Price stability
   - Competition level
   - Market accessibility

6. RISK COMPARISON:
   For each crop:
   - Weather sensitivity
   - Pest/disease vulnerability
   - Market volatility
   - Overall risk score

7. SEASONAL CONSIDERATIONS:
   - Best season for each crop
   - Crop rotation compatibility
   - Intercropping possibilities

8. FINAL RECOMMENDATION:
   - Top choice: [crop name and why]
   - Second choice: [crop name and why]
   - Third choice: [crop name and why]
   - Overall recommendation based on:
     * Profitability
     * Risk level
     * Resource availability
     * Farmer experience
     * Market conditions

9. DECISION MATRIX:
   Provide a scoring matrix (1-10) for each crop across:
   - Profitability
   - Sustainability
   - Risk level (inverse)
   - Market demand
   - Ease of cultivation
   - TOTAL SCORE

10. ACTIONABLE INSIGHTS:
    - Which crop to choose if priority is maximum profit
    - Which crop to choose if priority is low risk
    - Which crop to choose if water is limited
    - Which crop to choose if labor is limited
    - Which crop for beginner farmers
    - Which crop for experienced farmers

Provide objective, data-driven comparison with clear recommendations.
"""
        
        return prompt

    def _parse_crop_recommendations(self, recommendations_text: str) -> Dict[str, Any]:
        """Parse crop recommendations from AI response"""
        
        highly_recommended = []
        moderately_suitable = []
        not_recommended = []
        
        lines = recommendations_text.split('\n')
        current_section = None
        current_crop = {}
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Section detection
            if 'highly recommended' in line_lower:
                current_section = 'highly'
            elif 'moderately suitable' in line_lower:
                current_section = 'moderately'
            elif 'not recommended' in line_lower:
                current_section = 'not_recommended'
            
            # Crop name detection
            if 'crop name:' in line_lower:
                if current_crop and current_section:
                    if current_section == 'highly':
                        highly_recommended.append(current_crop)
                    elif current_section == 'moderately':
                        moderately_suitable.append(current_crop)
                
                current_crop = {'name': line.split(':', 1)[1].strip()}
            
            # Extract other fields
            if current_crop:
                if 'expected yield:' in line_lower:
                    current_crop['expected_yield'] = line.split(':', 1)[1].strip()
                elif 'market demand:' in line_lower:
                    current_crop['market_demand'] = line.split(':', 1)[1].strip()
                elif 'net profit:' in line_lower:
                    current_crop['net_profit'] = line.split(':', 1)[1].strip()
                elif 'risk level:' in line_lower:
                    current_crop['risk_level'] = line.split(':', 1)[1].strip()
        
        # Add last crop
        if current_crop and current_section:
            if current_section == 'highly':
                highly_recommended.append(current_crop)
            elif current_section == 'moderately':
                moderately_suitable.append(current_crop)
        
        return {
            'highly_recommended_crops': highly_recommended,
            'moderately_suitable_crops': moderately_suitable,
            'not_recommended_crops': not_recommended
        }
    
    def _parse_profitability(self, profitability_text: str) -> Dict[str, Any]:
        """Parse profitability data from AI response"""
        
        profitability = {
            'input_costs_per_acre': 0,
            'expected_yield_per_acre': 0,
            'revenue_per_acre': 0,
            'net_profit_per_acre': 0,
            'profit_margin': 0,
            'roi': 0,
            'risk_rating': 'medium'
        }
        
        lines = profitability_text.split('\n')
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if 'total input cost per acre:' in line_lower:
                try:
                    import re
                    cost_match = re.search(r'₹?\s*(\d+(?:,\d+)*)', line)
                    if cost_match:
                        profitability['input_costs_per_acre'] = float(cost_match.group(1).replace(',', ''))
                except:
                    pass
            
            if 'average yield:' in line_lower and 'per acre' in line_lower:
                try:
                    import re
                    yield_match = re.search(r'(\d+(?:\.\d+)?)', line)
                    if yield_match:
                        profitability['expected_yield_per_acre'] = float(yield_match.group(1))
                except:
                    pass
            
            if 'average net profit:' in line_lower:
                try:
                    import re
                    profit_match = re.search(r'₹?\s*(\d+(?:,\d+)*)', line)
                    if profit_match:
                        profitability['net_profit_per_acre'] = float(profit_match.group(1).replace(',', ''))
                except:
                    pass
            
            if 'roi:' in line_lower or 'return on investment:' in line_lower:
                try:
                    import re
                    roi_match = re.search(r'(\d+(?:\.\d+)?)\s*%', line)
                    if roi_match:
                        profitability['roi'] = float(roi_match.group(1))
                except:
                    pass
        
        return profitability

    def _parse_seasonal_calendar(self, calendar_text: str) -> Dict[str, Any]:
        """Parse seasonal calendar from AI response"""
        
        calendar = {
            'kharif_crops': [],
            'rabi_crops': [],
            'zaid_crops': [],
            'perennial_crops': [],
            'monthly_activities': {}
        }
        
        lines = calendar_text.split('\n')
        current_season = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if 'kharif season' in line_lower:
                current_season = 'kharif'
            elif 'rabi season' in line_lower:
                current_season = 'rabi'
            elif 'zaid season' in line_lower:
                current_season = 'zaid'
            elif 'perennial' in line_lower:
                current_season = 'perennial'
            
            if 'crop name:' in line_lower and current_season:
                crop_name = line.split(':', 1)[1].strip()
                if current_season == 'kharif':
                    calendar['kharif_crops'].append(crop_name)
                elif current_season == 'rabi':
                    calendar['rabi_crops'].append(crop_name)
                elif current_season == 'zaid':
                    calendar['zaid_crops'].append(crop_name)
                elif current_season == 'perennial':
                    calendar['perennial_crops'].append(crop_name)
        
        return calendar
    
    def _parse_crop_comparison(self, comparison_text: str) -> Dict[str, Any]:
        """Parse crop comparison from AI response"""
        
        comparison = {
            'comparison_table': {},
            'rankings': {},
            'recommendation': ''
        }
        
        lines = comparison_text.split('\n')
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if 'top choice:' in line_lower or 'final recommendation:' in line_lower:
                comparison['recommendation'] = line.split(':', 1)[1].strip()
        
        return comparison
    
    def _get_mock_market_price(self, crop_name: str, location: Dict[str, str]) -> float:
        """Get mock market price for crop (placeholder for real market data)"""
        
        # Mock prices per quintal in INR
        mock_prices = {
            'wheat': 2200,
            'rice': 2000,
            'paddy': 2000,
            'maize': 1800,
            'corn': 1800,
            'cotton': 6000,
            'sugarcane': 350,
            'soybean': 4000,
            'groundnut': 5500,
            'peanut': 5500,
            'potato': 1200,
            'tomato': 1500,
            'onion': 1000,
            'chickpea': 5000,
            'chana': 5000,
            'pigeon pea': 6000,
            'tur': 6000,
            'mustard': 5500,
            'sunflower': 6000
        }
        
        crop_lower = crop_name.lower()
        
        for key, price in mock_prices.items():
            if key in crop_lower:
                return price
        
        # Default price if crop not found
        return 2500

    def _store_crop_recommendations(self,
                                   recommendation_id: str,
                                   soil_analysis: Dict[str, Any],
                                   location: Dict[str, str],
                                   recommendations: Dict[str, Any]) -> None:
        """Store crop recommendations in DynamoDB"""
        try:
            item = {
                'farm_id': f"farm_{uuid.uuid4().hex[:8]}",
                'timestamp': int(datetime.now().timestamp()),
                'recommendation_id': recommendation_id,
                'data_type': 'crop_recommendations',
                'soil_analysis': soil_analysis,
                'location': location,
                'recommendations': recommendations,
                'created_at': datetime.now().isoformat()
            }
            
            self.farm_data_table.put_item(Item=item)
            logger.info(f"Crop recommendations stored: {recommendation_id}")
        
        except Exception as e:
            logger.error(f"Error storing crop recommendations: {e}")


# Tool functions for agent integration

def create_crop_selection_tools(region: str = "us-east-1") -> CropSelectionTools:
    """
    Factory function to create crop selection tools instance
    
    Args:
        region: AWS region
    
    Returns:
        CropSelectionTools instance
    """
    return CropSelectionTools(region=region)


def recommend_crops(soil_analysis: Dict[str, Any],
                   location: Dict[str, str],
                   farm_size_acres: float,
                   climate_data: Optional[Dict[str, Any]] = None,
                   market_preferences: Optional[Dict[str, Any]] = None,
                   farmer_experience: Optional[str] = None) -> Dict[str, Any]:
    """
    Tool function for crop recommendations
    
    Args:
        soil_analysis: Soil analysis results
        location: Location information
        farm_size_acres: Farm size in acres
        climate_data: Optional climate data
        market_preferences: Optional market preferences
        farmer_experience: Optional farmer experience level
    
    Returns:
        Crop recommendations
    """
    tools = create_crop_selection_tools()
    return tools.recommend_crops(
        soil_analysis, location, farm_size_acres,
        climate_data, market_preferences, farmer_experience
    )


def calculate_crop_profitability(crop_name: str,
                                farm_size_acres: float,
                                location: Dict[str, str],
                                soil_type: str,
                                input_costs: Optional[Dict[str, float]] = None,
                                market_price: Optional[float] = None) -> Dict[str, Any]:
    """
    Tool function for crop profitability calculation
    
    Args:
        crop_name: Name of the crop
        farm_size_acres: Farm size in acres
        location: Location information
        soil_type: Soil type
        input_costs: Optional custom input costs
        market_price: Optional current market price
    
    Returns:
        Profitability analysis
    """
    tools = create_crop_selection_tools()
    return tools.calculate_crop_profitability(
        crop_name, farm_size_acres, location, soil_type,
        input_costs, market_price
    )


def generate_seasonal_calendar(location: Dict[str, str],
                              soil_type: str,
                              farm_size_acres: float,
                              selected_crops: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Tool function for seasonal calendar generation
    
    Args:
        location: Location information
        soil_type: Soil type
        farm_size_acres: Farm size in acres
        selected_crops: Optional list of crops
    
    Returns:
        Seasonal calendar
    """
    tools = create_crop_selection_tools()
    return tools.generate_seasonal_calendar(
        location, soil_type, farm_size_acres, selected_crops
    )
