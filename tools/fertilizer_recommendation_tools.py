"""
RISE Fertilizer Recommendation Tools
Tools for calculating NPK requirements and providing precision fertilizer recommendations
"""

import boto3
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FertilizerRecommendationTools:
    """Fertilizer recommendation tools using Amazon Bedrock and weather integration"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize fertilizer recommendation tools
        
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
        
        # Crop growth stages
        self.growth_stages = ['seedling', 'vegetative', 'flowering', 'fruiting', 'maturity']
        
        logger.info(f"Fertilizer recommendation tools initialized in region {region}")

    def calculate_npk_requirements(self,
                                   soil_analysis: Dict[str, Any],
                                   target_crop: str,
                                   farm_size_acres: float,
                                   location: Dict[str, str]) -> Dict[str, Any]:
        """
        Calculate precise NPK requirements based on soil analysis and target crop
        
        Args:
            soil_analysis: Soil analysis results from soil_analysis_tools
            target_crop: Target crop name
            farm_size_acres: Farm size in acres
            location: Location information
        
        Returns:
            Dict with NPK calculations and recommendations
        """
        try:
            # Build prompt for NPK calculation
            prompt = self._build_npk_calculation_prompt(
                soil_analysis, target_crop, farm_size_acres, location
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
            calculation_text = response_body['content'][0]['text']
            
            # Parse NPK calculations
            npk_data = self._parse_npk_calculations(calculation_text)
            
            return {
                'success': True,
                'target_crop': target_crop,
                'farm_size_acres': farm_size_acres,
                **npk_data,
                'full_calculation': calculation_text
            }
        
        except Exception as e:
            logger.error(f"NPK calculation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def get_precision_recommendations(self,
                                     npk_requirements: Dict[str, Any],
                                     soil_analysis: Dict[str, Any],
                                     target_crop: str,
                                     growth_stage: str,
                                     weather_forecast: Optional[Dict[str, Any]] = None,
                                     budget_constraint: Optional[float] = None) -> Dict[str, Any]:
        """
        Get precision fertilizer recommendations with timing and application methods
        
        Args:
            npk_requirements: NPK requirements from calculate_npk_requirements
            soil_analysis: Soil analysis results
            target_crop: Target crop name
            growth_stage: Current growth stage
            weather_forecast: Optional weather forecast data
            budget_constraint: Optional budget limit in INR
        
        Returns:
            Dict with precision recommendations
        """
        try:
            # Build prompt for precision recommendations
            prompt = self._build_precision_recommendation_prompt(
                npk_requirements, soil_analysis, target_crop, 
                growth_stage, weather_forecast, budget_constraint
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
            recommendations_text = response_body['content'][0]['text']
            
            # Parse recommendations
            recommendations = self._parse_precision_recommendations(recommendations_text)
            
            return {
                'success': True,
                'target_crop': target_crop,
                'growth_stage': growth_stage,
                **recommendations,
                'full_recommendations': recommendations_text
            }
        
        except Exception as e:
            logger.error(f"Precision recommendations error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def get_application_timing(self,
                              target_crop: str,
                              growth_stage: str,
                              weather_forecast: Dict[str, Any],
                              location: Dict[str, str]) -> Dict[str, Any]:
        """
        Calculate optimal fertilizer application timing based on weather and growth stage
        
        Args:
            target_crop: Target crop name
            growth_stage: Current growth stage
            weather_forecast: Weather forecast data (7-14 days)
            location: Location information
        
        Returns:
            Dict with optimal timing recommendations
        """
        try:
            # Build prompt for timing recommendations
            prompt = self._build_timing_prompt(
                target_crop, growth_stage, weather_forecast, location
            )
            
            # Call Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 2000,
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
            timing_text = response_body['content'][0]['text']
            
            # Parse timing recommendations
            timing_data = self._parse_timing_recommendations(timing_text)
            
            return {
                'success': True,
                'target_crop': target_crop,
                'growth_stage': growth_stage,
                **timing_data,
                'full_timing_analysis': timing_text
            }
        
        except Exception as e:
            logger.error(f"Application timing error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def track_crop_growth_stage(self,
                               user_id: str,
                               farm_id: str,
                               crop_name: str,
                               planting_date: str,
                               current_observations: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Track and determine current crop growth stage
        
        Args:
            user_id: User ID
            farm_id: Farm ID
            crop_name: Crop name
            planting_date: Planting date (ISO format)
            current_observations: Optional current observations
        
        Returns:
            Dict with growth stage information
        """
        try:
            # Calculate days since planting
            planting_dt = datetime.fromisoformat(planting_date)
            days_since_planting = (datetime.now() - planting_dt).days
            
            # Build prompt for growth stage determination
            prompt = self._build_growth_stage_prompt(
                crop_name, days_since_planting, current_observations
            )
            
            # Call Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 1500,
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
            stage_text = response_body['content'][0]['text']
            
            # Parse growth stage
            stage_data = self._parse_growth_stage(stage_text)
            
            # Store growth stage tracking
            tracking_id = f"growth_{uuid.uuid4().hex[:12]}"
            self._store_growth_tracking(
                tracking_id, user_id, farm_id, crop_name,
                planting_date, days_since_planting, stage_data
            )
            
            return {
                'success': True,
                'tracking_id': tracking_id,
                'crop_name': crop_name,
                'days_since_planting': days_since_planting,
                **stage_data
            }
        
        except Exception as e:
            logger.error(f"Growth stage tracking error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def generate_amendment_suggestions(self,
                                      npk_requirements: Dict[str, Any],
                                      soil_deficiencies: List[str],
                                      farm_size_acres: float,
                                      prioritize_organic: bool = True,
                                      budget_constraint: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate organic and chemical amendment suggestions with quantities
        
        Args:
            npk_requirements: NPK requirements
            soil_deficiencies: List of soil deficiencies
            farm_size_acres: Farm size in acres
            prioritize_organic: Whether to prioritize organic options
            budget_constraint: Optional budget limit in INR
        
        Returns:
            Dict with amendment suggestions
        """
        try:
            # Build prompt for amendment suggestions
            prompt = self._build_amendment_prompt(
                npk_requirements, soil_deficiencies, farm_size_acres,
                prioritize_organic, budget_constraint
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
            amendments_text = response_body['content'][0]['text']
            
            # Parse amendments
            amendments = self._parse_amendments(amendments_text)
            
            return {
                'success': True,
                'farm_size_acres': farm_size_acres,
                'prioritize_organic': prioritize_organic,
                **amendments,
                'full_amendments': amendments_text
            }
        
        except Exception as e:
            logger.error(f"Amendment suggestions error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def prioritize_cost_effective_solutions(self,
                                           organic_options: List[Dict[str, Any]],
                                           chemical_options: List[Dict[str, Any]],
                                           budget: float,
                                           farm_size_acres: float) -> Dict[str, Any]:
        """
        Prioritize cost-effective fertilizer solutions
        
        Args:
            organic_options: List of organic fertilizer options
            chemical_options: List of chemical fertilizer options
            budget: Available budget in INR
            farm_size_acres: Farm size in acres
        
        Returns:
            Dict with prioritized cost-effective solutions
        """
        try:
            # Build prompt for cost optimization
            prompt = self._build_cost_optimization_prompt(
                organic_options, chemical_options, budget, farm_size_acres
            )
            
            # Call Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 2500,
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
            optimization_text = response_body['content'][0]['text']
            
            # Parse cost-effective solutions
            solutions = self._parse_cost_solutions(optimization_text)
            
            return {
                'success': True,
                'budget': budget,
                'farm_size_acres': farm_size_acres,
                **solutions,
                'full_analysis': optimization_text
            }
        
        except Exception as e:
            logger.error(f"Cost optimization error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _build_npk_calculation_prompt(self,
                                     soil_analysis: Dict[str, Any],
                                     target_crop: str,
                                     farm_size_acres: float,
                                     location: Dict[str, str]) -> str:
        """Build prompt for NPK calculation"""
        
        prompt = f"""You are an expert agricultural scientist specializing in soil fertility and crop nutrition.
Calculate precise NPK (Nitrogen, Phosphorus, Potassium) requirements for the following scenario:

TARGET CROP: {target_crop}
FARM SIZE: {farm_size_acres} acres
LOCATION: {location.get('district', 'Unknown')}, {location.get('state', 'Unknown')}

CURRENT SOIL ANALYSIS:
- Soil Type: {soil_analysis.get('soil_type', 'unknown')}
- Fertility Level: {soil_analysis.get('fertility_level', 'unknown')}
- pH Level: {soil_analysis.get('ph_level', 'not tested')}
- Current NPK Levels:
  * Nitrogen (N): {soil_analysis.get('npk_levels', {}).get('nitrogen', 'unknown')}
  * Phosphorus (P): {soil_analysis.get('npk_levels', {}).get('phosphorus', 'unknown')}
  * Potassium (K): {soil_analysis.get('npk_levels', {}).get('potassium', 'unknown')}
- Organic Matter: {soil_analysis.get('organic_matter', 'not tested')}%
- Deficiencies: {', '.join(soil_analysis.get('deficiencies', ['None identified']))}

Provide calculations in the following format:

1. CROP NPK REQUIREMENTS:
   - Total Nitrogen (N) needed: [kg per acre]
   - Total Phosphorus (P2O5) needed: [kg per acre]
   - Total Potassium (K2O) needed: [kg per acre]
   - Rationale: [explain based on crop needs]

2. SOIL CONTRIBUTION:
   - Available N from soil: [kg per acre]
   - Available P from soil: [kg per acre]
   - Available K from soil: [kg per acre]

3. NET REQUIREMENTS (Crop needs - Soil contribution):
   - Additional N needed: [kg per acre]
   - Additional P needed: [kg per acre]
   - Additional K needed: [kg per acre]

4. TOTAL FARM REQUIREMENTS ({farm_size_acres} acres):
   - Total N: [kg]
   - Total P2O5: [kg]
   - Total K2O: [kg]

5. SPLIT APPLICATION SCHEDULE:
   - Basal dose (at planting): [NPK quantities]
   - First top-dressing (timing): [NPK quantities]
   - Second top-dressing (timing): [NPK quantities]
   - Additional applications if needed

6. MICRONUTRIENTS:
   - Zinc (Zn): [if needed, quantity]
   - Iron (Fe): [if needed, quantity]
   - Other micronutrients: [list with quantities]

Provide specific, actionable quantities based on scientific crop nutrition principles.
"""
        
        return prompt

    def _build_precision_recommendation_prompt(self,
                                              npk_requirements: Dict[str, Any],
                                              soil_analysis: Dict[str, Any],
                                              target_crop: str,
                                              growth_stage: str,
                                              weather_forecast: Optional[Dict[str, Any]],
                                              budget_constraint: Optional[float]) -> str:
        """Build prompt for precision recommendations"""
        
        prompt = f"""You are an expert in precision agriculture and fertilizer management.
Provide detailed fertilizer recommendations for:

CROP: {target_crop}
GROWTH STAGE: {growth_stage}
SOIL TYPE: {soil_analysis.get('soil_type', 'unknown')}

NPK REQUIREMENTS:
{json.dumps(npk_requirements, indent=2)}
"""
        
        if weather_forecast:
            prompt += f"\nWEATHER FORECAST (Next 7-14 days):\n{json.dumps(weather_forecast, indent=2)}\n"
        
        if budget_constraint:
            prompt += f"\nBUDGET CONSTRAINT: ₹{budget_constraint}\n"
        
        prompt += """
Provide recommendations in the following format:

1. ORGANIC FERTILIZER OPTIONS:
   For each option:
   - Name: [e.g., Farmyard Manure, Compost, Vermicompost]
   - NPK Content: [typical NPK ratio]
   - Quantity per acre: [tons or kg]
   - Total quantity needed: [for entire farm]
   - Application method: [broadcasting, banding, etc.]
   - Cost per acre: [₹]
   - Total cost: [₹]
   - Benefits: [list key benefits]
   - Availability: [easy/moderate/difficult to source]

2. CHEMICAL FERTILIZER OPTIONS:
   For each option:
   - Fertilizer name: [e.g., Urea, DAP, MOP, NPK 10:26:26]
   - NPK ratio: [N:P:K]
   - Quantity per acre: [kg]
   - Total quantity needed: [kg]
   - Application method: [broadcasting, fertigation, etc.]
   - Cost per acre: [₹]
   - Total cost: [₹]
   - Timing: [specific application timing]
   - Safety precautions: [list]

3. COMBINED APPROACH (Organic + Chemical):
   - Integrated fertilization plan
   - Quantities of each type
   - Application sequence
   - Total cost
   - Expected benefits

4. APPLICATION TIMING:
   - Optimal application dates
   - Weather considerations
   - Soil moisture requirements
   - Time of day recommendations

5. APPLICATION METHODS:
   - Broadcasting: [when and how]
   - Band placement: [when and how]
   - Foliar spray: [if applicable]
   - Fertigation: [if applicable]
   - Incorporation depth: [cm]

6. COST-BENEFIT ANALYSIS:
   - Expected yield increase: [%]
   - Return on investment: [₹]
   - Payback period: [months]

Prioritize cost-effective, sustainable solutions that match the farmer's budget and resources.
"""
        
        return prompt

    def _build_timing_prompt(self,
                            target_crop: str,
                            growth_stage: str,
                            weather_forecast: Dict[str, Any],
                            location: Dict[str, str]) -> str:
        """Build prompt for timing recommendations"""
        
        prompt = f"""You are an expert in agricultural timing and weather-based fertilizer management.
Determine optimal fertilizer application timing for:

CROP: {target_crop}
GROWTH STAGE: {growth_stage}
LOCATION: {location.get('district', 'Unknown')}, {location.get('state', 'Unknown')}

WEATHER FORECAST:
{json.dumps(weather_forecast, indent=2)}

Provide timing recommendations in the following format:

1. OPTIMAL APPLICATION WINDOW:
   - Best dates: [specific date range]
   - Rationale: [why these dates]
   - Weather conditions needed: [temperature, rainfall, etc.]

2. WEATHER CONSIDERATIONS:
   - Rainfall timing: [avoid/prefer certain conditions]
   - Temperature requirements: [optimal range]
   - Wind conditions: [impact on application]
   - Soil moisture: [required level]

3. TIME OF DAY:
   - Best time: [morning/evening/specific hours]
   - Reason: [explain why]
   - Conditions to avoid: [list]

4. CROP GROWTH STAGE ALIGNMENT:
   - Current stage needs: [what crop needs now]
   - Next stage preparation: [upcoming needs]
   - Critical timing windows: [don't miss these]

5. RISK ASSESSMENT:
   - Weather risks: [rain, heat, etc.]
   - Application risks: [leaching, volatilization]
   - Mitigation strategies: [how to reduce risks]

6. ALTERNATIVE DATES:
   - If primary window missed: [backup dates]
   - Adjustments needed: [changes to quantities/methods]

7. POST-APPLICATION CARE:
   - Irrigation needs: [if any]
   - Monitoring requirements: [what to watch]
   - Expected response time: [when to see results]

Be specific with dates and provide clear reasoning based on weather patterns and crop physiology.
"""
        
        return prompt

    def _build_growth_stage_prompt(self,
                                  crop_name: str,
                                  days_since_planting: int,
                                  current_observations: Optional[Dict[str, Any]]) -> str:
        """Build prompt for growth stage determination"""
        
        prompt = f"""You are an expert crop physiologist. Determine the current growth stage for:

CROP: {crop_name}
DAYS SINCE PLANTING: {days_since_planting}
"""
        
        if current_observations:
            prompt += f"\nCURRENT OBSERVATIONS:\n{json.dumps(current_observations, indent=2)}\n"
        
        prompt += """
Provide growth stage analysis in the following format:

1. CURRENT GROWTH STAGE:
   - Stage name: [seedling/vegetative/flowering/fruiting/maturity]
   - Sub-stage: [if applicable, e.g., early vegetative, late flowering]
   - Confidence: [high/medium/low]

2. STAGE CHARACTERISTICS:
   - Typical duration: [days]
   - Key visual indicators: [what to look for]
   - Physiological changes: [what's happening in the plant]

3. NUTRITIONAL NEEDS AT THIS STAGE:
   - Primary nutrient: [N/P/K priority]
   - Secondary nutrients: [if needed]
   - Micronutrients: [if needed]
   - Rationale: [why these nutrients now]

4. NEXT STAGE PREDICTION:
   - Expected transition date: [approximate date]
   - Signs to watch for: [indicators of stage change]
   - Preparation needed: [what to do before next stage]

5. FERTILIZER TIMING:
   - Current application needs: [immediate/wait]
   - Optimal timing: [specific recommendations]
   - Quantity adjustments: [based on stage]

6. MONITORING RECOMMENDATIONS:
   - What to observe: [specific indicators]
   - Frequency: [how often to check]
   - Red flags: [warning signs]

Be specific and provide actionable guidance based on crop development patterns.
"""
        
        return prompt

    def _build_amendment_prompt(self,
                               npk_requirements: Dict[str, Any],
                               soil_deficiencies: List[str],
                               farm_size_acres: float,
                               prioritize_organic: bool,
                               budget_constraint: Optional[float]) -> str:
        """Build prompt for amendment suggestions"""
        
        prompt = f"""You are an expert in soil amendments and organic farming practices.
Generate comprehensive amendment suggestions for:

FARM SIZE: {farm_size_acres} acres
PRIORITIZE ORGANIC: {'Yes' if prioritize_organic else 'No'}
"""
        
        if budget_constraint:
            prompt += f"BUDGET LIMIT: ₹{budget_constraint}\n"
        
        prompt += f"""
NPK REQUIREMENTS:
{json.dumps(npk_requirements, indent=2)}

SOIL DEFICIENCIES:
{', '.join(soil_deficiencies) if soil_deficiencies else 'None identified'}

Provide amendment suggestions in the following format:

1. ORGANIC AMENDMENTS:
   For each amendment:
   - Name: [e.g., Farmyard Manure, Compost, Vermicompost, Green Manure]
   - NPK content: [typical ratio]
   - Quantity per acre: [tons or kg]
   - Total quantity for farm: [tons or kg]
   - Application method: [detailed instructions]
   - Application timing: [when to apply]
   - Cost per acre: [₹]
   - Total cost: [₹]
   - Benefits: [list all benefits]
   - Sourcing: [where to get it]
   - Preparation time: [if making at home]

2. CHEMICAL AMENDMENTS:
   For each fertilizer:
   - Product name: [specific fertilizer]
   - NPK ratio: [N:P:K]
   - Quantity per acre: [kg]
   - Total quantity for farm: [kg]
   - Application method: [broadcasting, banding, etc.]
   - Application timing: [specific dates/stages]
   - Cost per acre: [₹]
   - Total cost: [₹]
   - Safety precautions: [handling, storage, application]
   - Brand recommendations: [if any]

3. MICRONUTRIENT AMENDMENTS:
   For each deficiency:
   - Nutrient: [Zn, Fe, Mn, etc.]
   - Product: [specific product name]
   - Quantity: [kg per acre]
   - Application method: [soil/foliar]
   - Cost: [₹]

4. INTEGRATED APPROACH:
   - Combination plan: [organic + chemical]
   - Application sequence: [step by step]
   - Total cost: [₹]
   - Expected results: [timeline and outcomes]
   - Sustainability benefits: [long-term advantages]

5. COST COMPARISON:
   - Organic-only approach: [total cost]
   - Chemical-only approach: [total cost]
   - Integrated approach: [total cost]
   - Recommended approach: [which one and why]

6. LONG-TERM SOIL HEALTH:
   - Organic matter building: [strategies]
   - Soil structure improvement: [methods]
   - Microbial activity: [how to enhance]
   - Sustainability practices: [recommendations]

Prioritize {'organic and sustainable' if prioritize_organic else 'cost-effective'} solutions.
Provide specific quantities, costs, and actionable instructions.
"""
        
        return prompt

    def _build_cost_optimization_prompt(self,
                                       organic_options: List[Dict[str, Any]],
                                       chemical_options: List[Dict[str, Any]],
                                       budget: float,
                                       farm_size_acres: float) -> str:
        """Build prompt for cost optimization"""
        
        prompt = f"""You are an expert in agricultural economics and cost optimization.
Analyze and prioritize cost-effective fertilizer solutions for:

FARM SIZE: {farm_size_acres} acres
AVAILABLE BUDGET: ₹{budget}

ORGANIC OPTIONS:
{json.dumps(organic_options, indent=2)}

CHEMICAL OPTIONS:
{json.dumps(chemical_options, indent=2)}

Provide cost optimization analysis in the following format:

1. BUDGET ANALYSIS:
   - Total budget: [₹]
   - Cost per acre available: [₹]
   - Budget adequacy: [sufficient/tight/insufficient]

2. COST-EFFECTIVE SOLUTIONS (Ranked):
   For each solution (top 5):
   - Rank: [1-5]
   - Solution type: [organic/chemical/integrated]
   - Components: [list fertilizers]
   - Total cost: [₹]
   - Cost per acre: [₹]
   - NPK delivered: [quantities]
   - Cost per kg NPK: [₹]
   - Expected yield increase: [%]
   - ROI: [return on investment]
   - Payback period: [months]
   - Why recommended: [key reasons]

3. BUDGET-CONSTRAINED RECOMMENDATIONS:
   - Best option within budget: [specific recommendation]
   - Quantities: [detailed breakdown]
   - Application plan: [how to apply]
   - Expected results: [realistic outcomes]
   - Trade-offs: [what's compromised]

4. PHASED APPROACH (if budget insufficient):
   - Phase 1 (immediate): [critical applications]
   - Phase 2 (next month): [secondary applications]
   - Phase 3 (later): [optional applications]
   - Prioritization rationale: [why this sequence]

5. COST-SAVING STRATEGIES:
   - Bulk purchasing: [potential savings]
   - Cooperative buying: [group purchase benefits]
   - Timing optimization: [off-season discounts]
   - DIY options: [making compost, etc.]
   - Government subsidies: [available schemes]

6. VALUE-FOR-MONEY ANALYSIS:
   - Best organic option: [name and why]
   - Best chemical option: [name and why]
   - Best integrated option: [combination and why]
   - Overall recommendation: [final suggestion]

7. RISK ASSESSMENT:
   - Low-cost risks: [potential issues]
   - High-cost risks: [over-investment concerns]
   - Balanced approach: [recommended risk level]

Prioritize solutions that maximize crop nutrition while staying within budget.
Consider both immediate costs and long-term soil health benefits.
"""
        
        return prompt

    def _parse_npk_calculations(self, calculation_text: str) -> Dict[str, Any]:
        """Parse NPK calculations from AI response"""
        
        npk_data = {
            'nitrogen_per_acre': 0,
            'phosphorus_per_acre': 0,
            'potassium_per_acre': 0,
            'total_nitrogen': 0,
            'total_phosphorus': 0,
            'total_potassium': 0,
            'split_schedule': [],
            'micronutrients': []
        }
        
        lines = calculation_text.split('\n')
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Extract per-acre requirements
            if 'additional n needed' in line_lower or 'nitrogen needed' in line_lower:
                try:
                    import re
                    match = re.search(r'(\d+\.?\d*)\s*kg', line)
                    if match:
                        npk_data['nitrogen_per_acre'] = float(match.group(1))
                except:
                    pass
            
            if 'additional p needed' in line_lower or 'phosphorus needed' in line_lower:
                try:
                    import re
                    match = re.search(r'(\d+\.?\d*)\s*kg', line)
                    if match:
                        npk_data['phosphorus_per_acre'] = float(match.group(1))
                except:
                    pass
            
            if 'additional k needed' in line_lower or 'potassium needed' in line_lower:
                try:
                    import re
                    match = re.search(r'(\d+\.?\d*)\s*kg', line)
                    if match:
                        npk_data['potassium_per_acre'] = float(match.group(1))
                except:
                    pass
            
            # Extract total requirements
            if 'total n:' in line_lower:
                try:
                    import re
                    match = re.search(r'(\d+\.?\d*)\s*kg', line)
                    if match:
                        npk_data['total_nitrogen'] = float(match.group(1))
                except:
                    pass
            
            if 'total p' in line_lower and ':' in line:
                try:
                    import re
                    match = re.search(r'(\d+\.?\d*)\s*kg', line)
                    if match:
                        npk_data['total_phosphorus'] = float(match.group(1))
                except:
                    pass
            
            if 'total k' in line_lower and ':' in line:
                try:
                    import re
                    match = re.search(r'(\d+\.?\d*)\s*kg', line)
                    if match:
                        npk_data['total_potassium'] = float(match.group(1))
                except:
                    pass
        
        return npk_data

    def _parse_precision_recommendations(self, recommendations_text: str) -> Dict[str, Any]:
        """Parse precision recommendations from AI response"""
        
        recommendations = {
            'organic_options': [],
            'chemical_options': [],
            'combined_approach': '',
            'application_timing': '',
            'application_methods': '',
            'cost_benefit': ''
        }
        
        # Extract sections
        if 'ORGANIC FERTILIZER OPTIONS' in recommendations_text:
            start = recommendations_text.find('ORGANIC FERTILIZER OPTIONS')
            end = recommendations_text.find('2. CHEMICAL FERTILIZER OPTIONS', start)
            if end == -1:
                end = len(recommendations_text)
            recommendations['organic_options'] = recommendations_text[start:end].strip()
        
        if 'CHEMICAL FERTILIZER OPTIONS' in recommendations_text:
            start = recommendations_text.find('CHEMICAL FERTILIZER OPTIONS')
            end = recommendations_text.find('3. COMBINED APPROACH', start)
            if end == -1:
                end = len(recommendations_text)
            recommendations['chemical_options'] = recommendations_text[start:end].strip()
        
        if 'COMBINED APPROACH' in recommendations_text:
            start = recommendations_text.find('COMBINED APPROACH')
            end = recommendations_text.find('4. APPLICATION TIMING', start)
            if end == -1:
                end = len(recommendations_text)
            recommendations['combined_approach'] = recommendations_text[start:end].strip()
        
        return recommendations
    
    def _parse_timing_recommendations(self, timing_text: str) -> Dict[str, Any]:
        """Parse timing recommendations from AI response"""
        
        timing_data = {
            'optimal_window': '',
            'weather_considerations': '',
            'time_of_day': '',
            'risk_assessment': '',
            'alternative_dates': ''
        }
        
        # Extract key sections
        lines = timing_text.split('\n')
        current_section = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if 'optimal application window' in line_lower:
                current_section = 'optimal_window'
            elif 'weather considerations' in line_lower:
                current_section = 'weather_considerations'
            elif 'time of day' in line_lower:
                current_section = 'time_of_day'
            elif 'risk assessment' in line_lower:
                current_section = 'risk_assessment'
            elif 'alternative dates' in line_lower:
                current_section = 'alternative_dates'
        
        return timing_data

    def _parse_growth_stage(self, stage_text: str) -> Dict[str, Any]:
        """Parse growth stage from AI response"""
        
        stage_data = {
            'current_stage': 'unknown',
            'sub_stage': '',
            'confidence': 'medium',
            'nutritional_needs': {},
            'next_stage_prediction': '',
            'monitoring_recommendations': ''
        }
        
        lines = stage_text.split('\n')
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if 'stage name:' in line_lower:
                stage_str = line.split(':', 1)[1].strip().lower()
                for stage in self.growth_stages:
                    if stage in stage_str:
                        stage_data['current_stage'] = stage
                        break
            
            if 'sub-stage:' in line_lower:
                stage_data['sub_stage'] = line.split(':', 1)[1].strip()
            
            if 'confidence:' in line_lower:
                conf_str = line.split(':', 1)[1].strip().lower()
                if 'high' in conf_str:
                    stage_data['confidence'] = 'high'
                elif 'low' in conf_str:
                    stage_data['confidence'] = 'low'
                else:
                    stage_data['confidence'] = 'medium'
        
        return stage_data
    
    def _parse_amendments(self, amendments_text: str) -> Dict[str, Any]:
        """Parse amendments from AI response"""
        
        amendments = {
            'organic_amendments': [],
            'chemical_amendments': [],
            'micronutrient_amendments': [],
            'integrated_approach': '',
            'cost_comparison': {},
            'long_term_benefits': ''
        }
        
        # Extract sections
        if 'ORGANIC AMENDMENTS' in amendments_text:
            start = amendments_text.find('ORGANIC AMENDMENTS')
            end = amendments_text.find('2. CHEMICAL AMENDMENTS', start)
            if end == -1:
                end = len(amendments_text)
            amendments['organic_amendments'] = amendments_text[start:end].strip()
        
        if 'CHEMICAL AMENDMENTS' in amendments_text:
            start = amendments_text.find('CHEMICAL AMENDMENTS')
            end = amendments_text.find('3. MICRONUTRIENT AMENDMENTS', start)
            if end == -1:
                end = len(amendments_text)
            amendments['chemical_amendments'] = amendments_text[start:end].strip()
        
        return amendments
    
    def _parse_cost_solutions(self, optimization_text: str) -> Dict[str, Any]:
        """Parse cost-effective solutions from AI response"""
        
        solutions = {
            'budget_analysis': '',
            'ranked_solutions': [],
            'recommended_solution': '',
            'cost_saving_strategies': [],
            'value_analysis': ''
        }
        
        # Extract budget analysis
        if 'BUDGET ANALYSIS' in optimization_text:
            start = optimization_text.find('BUDGET ANALYSIS')
            end = optimization_text.find('2. COST-EFFECTIVE SOLUTIONS', start)
            if end == -1:
                end = len(optimization_text)
            solutions['budget_analysis'] = optimization_text[start:end].strip()
        
        return solutions

    def _store_growth_tracking(self,
                              tracking_id: str,
                              user_id: str,
                              farm_id: str,
                              crop_name: str,
                              planting_date: str,
                              days_since_planting: int,
                              stage_data: Dict[str, Any]) -> None:
        """Store growth tracking in DynamoDB"""
        try:
            item = {
                'farm_id': farm_id,
                'timestamp': int(datetime.now().timestamp()),
                'tracking_id': tracking_id,
                'user_id': user_id,
                'data_type': 'growth_tracking',
                'crop_name': crop_name,
                'planting_date': planting_date,
                'days_since_planting': days_since_planting,
                'growth_stage_data': stage_data
            }
            
            self.farm_data_table.put_item(Item=item)
            logger.info(f"Growth tracking stored: {tracking_id}")
        
        except Exception as e:
            logger.error(f"Error storing growth tracking: {e}")


# Tool functions for agent integration

def create_fertilizer_tools(region: str = "us-east-1") -> FertilizerRecommendationTools:
    """
    Factory function to create fertilizer recommendation tools instance
    
    Args:
        region: AWS region
    
    Returns:
        FertilizerRecommendationTools instance
    """
    return FertilizerRecommendationTools(region=region)


def calculate_npk(soil_analysis: Dict[str, Any],
                 target_crop: str,
                 farm_size_acres: float,
                 location: Dict[str, str]) -> Dict[str, Any]:
    """
    Tool function for calculating NPK requirements
    
    Args:
        soil_analysis: Soil analysis results
        target_crop: Target crop name
        farm_size_acres: Farm size in acres
        location: Location information
    
    Returns:
        NPK calculation results
    """
    tools = create_fertilizer_tools()
    return tools.calculate_npk_requirements(soil_analysis, target_crop, farm_size_acres, location)


def get_fertilizer_recommendations(npk_requirements: Dict[str, Any],
                                  soil_analysis: Dict[str, Any],
                                  target_crop: str,
                                  growth_stage: str,
                                  weather_forecast: Optional[Dict[str, Any]] = None,
                                  budget_constraint: Optional[float] = None) -> Dict[str, Any]:
    """
    Tool function for getting precision fertilizer recommendations
    
    Args:
        npk_requirements: NPK requirements
        soil_analysis: Soil analysis results
        target_crop: Target crop name
        growth_stage: Current growth stage
        weather_forecast: Optional weather forecast
        budget_constraint: Optional budget limit
    
    Returns:
        Precision recommendations
    """
    tools = create_fertilizer_tools()
    return tools.get_precision_recommendations(
        npk_requirements, soil_analysis, target_crop,
        growth_stage, weather_forecast, budget_constraint
    )
