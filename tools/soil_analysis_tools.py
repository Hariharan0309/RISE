"""
RISE Soil Analysis Tools
Tools for analyzing soil conditions and providing crop recommendations using Amazon Bedrock
"""

import boto3
import logging
import base64
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from PIL import Image
import io

logger = logging.getLogger(__name__)


class SoilAnalysisTools:
    """Soil analysis tools using Amazon Bedrock multimodal"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize soil analysis tools
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # DynamoDB table for farm data
        self.farm_data_table = self.dynamodb.Table('RISE-FarmData')
        
        # Model configuration
        self.model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
        
        # Soil types
        self.soil_types = ['clay', 'loam', 'sandy', 'silt', 'peat', 'chalky']
        
        # Fertility levels
        self.fertility_levels = ['low', 'medium', 'high']
        
        logger.info(f"Soil analysis tools initialized in region {region}")
    
    def analyze_soil_from_image(self,
                                image_data: bytes,
                                user_id: str,
                                farm_id: str,
                                location: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Analyze soil from image using Bedrock multimodal
        
        Args:
            image_data: Image bytes
            user_id: User ID
            farm_id: Farm ID
            location: Location information
        
        Returns:
            Dict with soil analysis results
        """
        try:
            # Validate image
            validation = self._validate_image(image_data)
            
            if not validation['valid']:
                return {
                    'success': False,
                    'error': 'invalid_image',
                    'validation': validation
                }
            
            # Compress image if needed
            compressed_image = self._compress_image(image_data)
            
            # Encode image to base64
            image_base64 = base64.b64encode(compressed_image).decode('utf-8')
            
            # Build prompt
            prompt = self._build_soil_image_prompt(location or {})
            
            # Call Bedrock with multimodal input
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 2500,
                    'messages': [
                        {
                            'role': 'user',
                            'content': [
                                {
                                    'type': 'image',
                                    'source': {
                                        'type': 'base64',
                                        'media_type': 'image/jpeg',
                                        'data': image_base64
                                    }
                                },
                                {
                                    'type': 'text',
                                    'text': prompt
                                }
                            ]
                        }
                    ],
                    'temperature': 0.3
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            analysis_text = response_body['content'][0]['text']
            
            # Parse structured analysis
            analysis = self._parse_soil_analysis(analysis_text)
            
            # Generate analysis ID
            analysis_id = f"soil_{uuid.uuid4().hex[:12]}"
            
            # Store image in S3
            s3_key = f"images/soil-samples/{user_id}/{analysis_id}.jpg"
            self.s3_client.put_object(
                Bucket='rise-application-data',
                Key=s3_key,
                Body=compressed_image,
                ContentType='image/jpeg',
                Metadata={
                    'user_id': user_id,
                    'farm_id': farm_id,
                    'analysis_id': analysis_id,
                    'timestamp': str(int(datetime.now().timestamp()))
                }
            )
            
            # Store analysis in DynamoDB
            self._store_soil_analysis(
                analysis_id=analysis_id,
                farm_id=farm_id,
                user_id=user_id,
                s3_key=s3_key,
                analysis=analysis,
                location=location or {}
            )
            
            return {
                'success': True,
                'analysis_id': analysis_id,
                's3_key': s3_key,
                **analysis
            }
        
        except Exception as e:
            logger.error(f"Soil image analysis error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_soil_from_test_data(self,
                                    test_data: Dict[str, Any],
                                    user_id: str,
                                    farm_id: str,
                                    location: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Analyze soil from manual test data
        
        Args:
            test_data: Soil test data (pH, NPK, etc.)
            user_id: User ID
            farm_id: Farm ID
            location: Location information
        
        Returns:
            Dict with soil analysis results
        """
        try:
            # Build prompt with test data
            prompt = self._build_test_data_prompt(test_data, location or {})
            
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
            analysis_text = response_body['content'][0]['text']
            
            # Parse structured analysis
            analysis = self._parse_soil_analysis(analysis_text)
            
            # Add test data to analysis
            analysis['test_data_provided'] = test_data
            
            # Generate analysis ID
            analysis_id = f"soil_{uuid.uuid4().hex[:12]}"
            
            # Store analysis in DynamoDB
            self._store_soil_analysis(
                analysis_id=analysis_id,
                farm_id=farm_id,
                user_id=user_id,
                s3_key=None,
                analysis=analysis,
                location=location or {}
            )
            
            return {
                'success': True,
                'analysis_id': analysis_id,
                **analysis
            }
        
        except Exception as e:
            logger.error(f"Soil test data analysis error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_crop_recommendations(self,
                                soil_type: str,
                                fertility_level: str,
                                location: Dict[str, str],
                                climate_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get crop recommendations based on soil conditions
        
        Args:
            soil_type: Type of soil
            fertility_level: Fertility level
            location: Location information
            climate_data: Optional climate data
        
        Returns:
            Dict with crop recommendations
        """
        try:
            # Build prompt for crop recommendations
            prompt = f"""Based on the following soil and location information, recommend suitable crops:

Soil Type: {soil_type}
Fertility Level: {fertility_level}
Location: {location.get('state', 'Unknown')}, {location.get('district', 'Unknown')}
"""
            
            if climate_data:
                prompt += f"\nClimate Data: {json.dumps(climate_data, indent=2)}\n"
            
            prompt += """
Provide recommendations in the following format:

1. HIGHLY SUITABLE CROPS:
   For each crop:
   - Crop Name
   - Expected Yield (per acre)
   - Growing Season
   - Market Demand (high/medium/low)
   - Estimated Profit Margin

2. MODERATELY SUITABLE CROPS:
   (Same format as above)
   - Note any amendments needed

3. NOT RECOMMENDED CROPS:
   - List crops and reasons why

4. SOIL PREPARATION RECOMMENDATIONS:
   - Specific steps for each recommended crop

5. MARKET CONSIDERATIONS:
   - Current market trends
   - Price forecasts
   - Demand analysis
"""
            
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
            recommendations_text = response_body['content'][0]['text']
            
            # Parse crop recommendations
            recommendations = self._parse_crop_recommendations(recommendations_text)
            
            return {
                'success': True,
                **recommendations
            }
        
        except Exception as e:
            logger.error(f"Crop recommendations error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_deficiency_report(self,
                                  deficiencies: List[str],
                                  soil_type: str,
                                  location: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate detailed deficiency report with amendment recommendations
        
        Args:
            deficiencies: List of identified deficiencies
            soil_type: Type of soil
            location: Location information
        
        Returns:
            Dict with deficiency report
        """
        try:
            # Build prompt
            prompt = f"""Generate a detailed soil deficiency report and amendment plan:

Soil Type: {soil_type}
Location: {location.get('state', 'Unknown')}, {location.get('district', 'Unknown')}
Identified Deficiencies:
{chr(10).join(f'- {d}' for d in deficiencies)}

Provide a comprehensive report in the following format:

1. DEFICIENCY ANALYSIS:
   For each deficiency:
   - Deficiency Name
   - Severity Level (low/medium/high/critical)
   - Impact on Crop Production
   - Visual Symptoms
   - Root Causes

2. ORGANIC AMENDMENT RECOMMENDATIONS:
   For each deficiency:
   - Organic Material (compost, manure, etc.)
   - Quantity per Acre (in kg or tons)
   - Application Method
   - Application Timing
   - Expected Results Timeline
   - Estimated Cost

3. CHEMICAL AMENDMENT RECOMMENDATIONS:
   For each deficiency:
   - Fertilizer Type (with NPK ratio)
   - Quantity per Acre (in kg)
   - Application Method
   - Application Timing
   - Safety Precautions
   - Estimated Cost

4. COMBINED TREATMENT PLAN:
   - Integrated approach using both organic and chemical
   - Step-by-step timeline
   - Total estimated cost
   - Expected improvement timeline

5. MONITORING PLAN:
   - Parameters to monitor
   - Monitoring frequency
   - Success indicators
   - When to retest soil

6. PREVENTIVE MEASURES:
   - Long-term soil health strategies
   - Crop rotation recommendations
   - Cover crop suggestions
   - Sustainable practices

Provide specific quantities and costs in Indian Rupees where possible.
"""
            
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
            report_text = response_body['content'][0]['text']
            
            return {
                'success': True,
                'report': report_text,
                'deficiencies': deficiencies,
                'soil_type': soil_type,
                'location': location
            }
        
        except Exception as e:
            logger.error(f"Deficiency report generation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_image(self, image_data: bytes) -> Dict[str, Any]:
        """Validate image data"""
        try:
            img = Image.open(io.BytesIO(image_data))
            width, height = img.size
            
            issues = []
            
            if width < 300 or height < 300:
                issues.append('low_resolution')
            
            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'dimensions': {'width': width, 'height': height}
            }
        
        except Exception as e:
            logger.error(f"Image validation error: {e}")
            return {
                'valid': False,
                'issues': ['invalid_image']
            }
    
    def _compress_image(self, image_data: bytes, max_size_kb: int = 500) -> bytes:
        """Compress image to reduce size"""
        try:
            img = Image.open(io.BytesIO(image_data))
            
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            quality = 85
            output = io.BytesIO()
            
            while quality > 20:
                output.seek(0)
                output.truncate()
                img.save(output, format='JPEG', quality=quality, optimize=True)
                
                if len(output.getvalue()) / 1024 <= max_size_kb:
                    break
                
                quality -= 10
            
            return output.getvalue()
        
        except Exception as e:
            logger.error(f"Image compression error: {e}")
            return image_data
    
    def _build_soil_image_prompt(self, location: Dict[str, str]) -> str:
        """Build prompt for soil image analysis"""
        
        prompt = """You are an expert soil scientist. Analyze this soil sample image comprehensively.

"""
        
        if location:
            prompt += f"Location: {location.get('state', 'Unknown')}, {location.get('district', 'Unknown')}\n"
        
        prompt += """
Provide analysis in this format:

1. SOIL TYPE: [clay/loam/sandy/silt/peat/chalky]
2. FERTILITY LEVEL: [low/medium/high]
3. ESTIMATED pH: [value or range]
4. NPK LEVELS:
   - Nitrogen: [low/medium/high]
   - Phosphorus: [low/medium/high]
   - Potassium: [low/medium/high]
5. ORGANIC MATTER: [percentage if estimable]
6. DEFICIENCIES: [list all identified]
7. SUITABLE CROPS: [list top 5-7 crops]
8. AMENDMENTS: [organic and chemical recommendations with quantities]
9. IMPROVEMENT PLAN: [short and long-term actions]

Be specific with quantities and provide actionable recommendations.
"""
        
        return prompt
    
    def _build_test_data_prompt(self, test_data: Dict[str, Any], location: Dict[str, str]) -> str:
        """Build prompt for test data analysis"""
        
        prompt = f"""Analyze this soil test data and provide comprehensive recommendations:

Location: {location.get('state', 'Unknown')}, {location.get('district', 'Unknown')}

TEST DATA:
{json.dumps(test_data, indent=2)}

Provide analysis in this format:

1. SOIL TYPE: [based on data]
2. FERTILITY ASSESSMENT: [detailed]
3. NPK ANALYSIS: [detailed interpretation]
4. pH ANALYSIS: [impact on crops]
5. DEFICIENCIES: [all identified with severity]
6. AMENDMENTS: [organic and chemical with quantities per acre]
7. SUITABLE CROPS: [top recommendations with yields]
8. IMPROVEMENT PLAN: [timeline with actions]
9. COST ANALYSIS: [estimated costs in INR]

Be specific and actionable.
"""
        
        return prompt
    
    def _parse_soil_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse soil analysis from AI response"""
        
        soil_type = 'unknown'
        fertility_level = 'medium'
        ph_level = None
        npk_levels = {}
        organic_matter = None
        deficiencies = []
        suitable_crops = []
        
        lines = analysis_text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            if 'soil type:' in line_lower or 'primary type:' in line_lower:
                soil_type_str = line.split(':', 1)[1].strip().lower()
                for st in self.soil_types:
                    if st in soil_type_str:
                        soil_type = st
                        break
            
            if 'fertility level:' in line_lower or 'fertility assessment:' in line_lower:
                fert_str = line.split(':', 1)[1].strip().lower()
                for fl in self.fertility_levels:
                    if fl in fert_str:
                        fertility_level = fl
                        break
            
            if 'ph' in line_lower and ':' in line:
                try:
                    import re
                    ph_str = line.split(':', 1)[1].strip()
                    ph_match = re.search(r'(\d+\.?\d*)', ph_str)
                    if ph_match:
                        ph_level = float(ph_match.group(1))
                except:
                    pass
            
            if 'nitrogen' in line_lower and ':' in line:
                npk_levels['nitrogen'] = self._extract_level(line)
            if 'phosphorus' in line_lower and ':' in line:
                npk_levels['phosphorus'] = self._extract_level(line)
            if 'potassium' in line_lower and ':' in line:
                npk_levels['potassium'] = self._extract_level(line)
            
            if 'organic matter' in line_lower and ':' in line:
                try:
                    import re
                    om_str = line.split(':', 1)[1].strip()
                    om_match = re.search(r'(\d+\.?\d*)', om_str)
                    if om_match:
                        organic_matter = float(om_match.group(1))
                except:
                    pass
            
            if 'deficiencies:' in line_lower or 'deficiencies identified' in line_lower:
                # Check if deficiencies are on the same line
                if ':' in line:
                    deficiency_text = line.split(':', 1)[1].strip()
                    if deficiency_text and len(deficiency_text) > 3:
                        # Split by comma if multiple deficiencies on same line
                        for def_item in deficiency_text.split(','):
                            def_item = def_item.strip()
                            if def_item and len(def_item) > 3:
                                deficiencies.append(def_item)
                
                # Also check next lines for list format
                for j in range(i+1, min(i+10, len(lines))):
                    if lines[j].strip().startswith('-'):
                        deficiency = lines[j].strip()[1:].strip()
                        if deficiency and len(deficiency) > 3:
                            deficiencies.append(deficiency)
            
            if 'suitable crops:' in line_lower or 'highly suitable:' in line_lower:
                crops_str = line.split(':', 1)[1].strip()
                crops = [c.strip() for c in crops_str.split(',') if c.strip()]
                suitable_crops.extend(crops)
        
        recommendations = self._extract_recommendations(analysis_text)
        
        return {
            'soil_type': soil_type,
            'fertility_level': fertility_level,
            'ph_level': ph_level,
            'npk_levels': npk_levels,
            'organic_matter': organic_matter,
            'deficiencies': deficiencies,
            'suitable_crops': suitable_crops,
            'recommendations': recommendations,
            'full_analysis': analysis_text
        }
    
    def _extract_level(self, line: str) -> str:
        """Extract nutrient level from line"""
        line_lower = line.lower()
        
        if 'low' in line_lower:
            return 'low'
        elif 'high' in line_lower:
            return 'high'
        elif 'medium' in line_lower or 'moderate' in line_lower:
            return 'medium'
        else:
            return 'unknown'
    
    def _extract_recommendations(self, analysis_text: str) -> Dict[str, List[str]]:
        """Extract recommendations from analysis"""
        
        recommendations = {
            'organic_amendments': [],
            'chemical_amendments': [],
            'water_management': [],
            'soil_improvement': []
        }
        
        if 'compost' in analysis_text.lower():
            recommendations['organic_amendments'].append('Compost application')
        
        if 'manure' in analysis_text.lower():
            recommendations['organic_amendments'].append('Organic manure')
        
        if 'fertilizer' in analysis_text.lower() or 'npk' in analysis_text.lower():
            recommendations['chemical_amendments'].append('Chemical fertilizer - see full analysis')
        
        return recommendations
    
    def _parse_crop_recommendations(self, recommendations_text: str) -> Dict[str, Any]:
        """Parse crop recommendations from AI response"""
        
        highly_suitable = []
        moderately_suitable = []
        not_recommended = []
        
        lines = recommendations_text.split('\n')
        current_section = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if 'highly suitable' in line_lower:
                current_section = 'highly'
            elif 'moderately suitable' in line_lower:
                current_section = 'moderately'
            elif 'not recommended' in line_lower:
                current_section = 'not_recommended'
            
            if line.strip().startswith('-') and current_section:
                crop = line.strip()[1:].strip()
                if crop:
                    if current_section == 'highly':
                        highly_suitable.append(crop)
                    elif current_section == 'moderately':
                        moderately_suitable.append(crop)
                    elif current_section == 'not_recommended':
                        not_recommended.append(crop)
        
        return {
            'highly_suitable_crops': highly_suitable,
            'moderately_suitable_crops': moderately_suitable,
            'not_recommended_crops': not_recommended,
            'full_recommendations': recommendations_text
        }
    
    def _store_soil_analysis(self,
                            analysis_id: str,
                            farm_id: str,
                            user_id: str,
                            s3_key: Optional[str],
                            analysis: Dict[str, Any],
                            location: Dict[str, str]) -> None:
        """Store soil analysis in DynamoDB"""
        try:
            item = {
                'farm_id': farm_id,
                'timestamp': int(datetime.now().timestamp()),
                'analysis_id': analysis_id,
                'user_id': user_id,
                'data_type': 'soil_analysis',
                'soil_analysis': analysis,
                'location': location,
                'image_s3_key': s3_key
            }
            
            self.farm_data_table.put_item(Item=item)
            logger.info(f"Soil analysis stored: {analysis_id}")
        
        except Exception as e:
            logger.error(f"Error storing soil analysis: {e}")


# Tool functions for agent integration

def create_soil_tools(region: str = "us-east-1") -> SoilAnalysisTools:
    """
    Factory function to create soil analysis tools instance
    
    Args:
        region: AWS region
    
    Returns:
        SoilAnalysisTools instance
    """
    return SoilAnalysisTools(region=region)


def analyze_soil_image(image_data: bytes,
                      user_id: str,
                      farm_id: str,
                      location: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Tool function for analyzing soil from image
    
    Args:
        image_data: Image bytes
        user_id: User ID
        farm_id: Farm ID
        location: Location information
    
    Returns:
        Soil analysis results
    """
    tools = create_soil_tools()
    return tools.analyze_soil_from_image(image_data, user_id, farm_id, location)


def analyze_soil_test_data(test_data: Dict[str, Any],
                          user_id: str,
                          farm_id: str,
                          location: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Tool function for analyzing soil from test data
    
    Args:
        test_data: Soil test data
        user_id: User ID
        farm_id: Farm ID
        location: Location information
    
    Returns:
        Soil analysis results
    """
    tools = create_soil_tools()
    return tools.analyze_soil_from_test_data(test_data, user_id, farm_id, location)
