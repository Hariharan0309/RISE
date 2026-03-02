"""
RISE Pest Identification Tools
Tools for analyzing crop images and identifying pests using Amazon Bedrock multimodal
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


class PestIdentificationTools:
    """Pest identification tools using Amazon Bedrock multimodal"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize pest identification tools
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # DynamoDB tables
        self.pest_diagnosis_table = self.dynamodb.Table('RISE-PestDiagnosisHistory')
        self.pest_knowledge_table = self.dynamodb.Table('RISE-PestKnowledgeBase')
        
        # Model configuration
        self.model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
        
        # Lifecycle stages
        self.lifecycle_stages = ['egg', 'larva', 'pupa', 'nymph', 'adult']
        
        # Severity levels
        self.severity_levels = ['low', 'medium', 'high', 'critical']
        
        logger.info(f"Pest identification tools initialized in region {region}")
    
    def compress_image(self, image_data: bytes, max_size_kb: int = 500) -> bytes:
        """
        Compress image to reduce size while maintaining quality
        
        Args:
            image_data: Original image bytes
            max_size_kb: Maximum size in KB
        
        Returns:
            Compressed image bytes
        """
        try:
            # Open image
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Calculate compression quality
            quality = 85
            output = io.BytesIO()
            
            # Iteratively compress until size is acceptable
            while quality > 20:
                output.seek(0)
                output.truncate()
                img.save(output, format='JPEG', quality=quality, optimize=True)
                
                size_kb = len(output.getvalue()) / 1024
                
                if size_kb <= max_size_kb:
                    break
                
                quality -= 10
            
            compressed_data = output.getvalue()
            
            logger.info(f"Image compressed from {len(image_data)/1024:.1f}KB to {len(compressed_data)/1024:.1f}KB")
            
            return compressed_data
        
        except Exception as e:
            logger.error(f"Image compression error: {e}")
            return image_data  # Return original if compression fails
    
    def validate_image_quality(self, image_data: bytes) -> Dict[str, Any]:
        """
        Validate image quality for pest identification
        
        Args:
            image_data: Image bytes
        
        Returns:
            Dict with validation results and guidance
        """
        try:
            img = Image.open(io.BytesIO(image_data))
            
            width, height = img.size
            file_size_kb = len(image_data) / 1024
            
            issues = []
            guidance = []
            
            # Check resolution
            if width < 300 or height < 300:
                issues.append('low_resolution')
                guidance.append('Take a higher resolution photo (at least 300x300 pixels)')
            
            # Check if image is too small
            if file_size_kb < 10:
                issues.append('file_too_small')
                guidance.append('Image file is very small, may indicate poor quality')
            
            # Check aspect ratio
            aspect_ratio = width / height
            if aspect_ratio > 3 or aspect_ratio < 0.33:
                issues.append('unusual_aspect_ratio')
                guidance.append('Try to capture the pest in a more balanced frame')
            
            is_valid = len(issues) == 0
            
            return {
                'valid': is_valid,
                'issues': issues,
                'guidance': guidance,
                'dimensions': {'width': width, 'height': height},
                'file_size_kb': file_size_kb
            }
        
        except Exception as e:
            logger.error(f"Image validation error: {e}")
            return {
                'valid': False,
                'issues': ['invalid_image'],
                'guidance': ['Unable to read image file. Please upload a valid image (JPEG, PNG)']
            }

    def analyze_pest_image(self, 
                          image_data: bytes,
                          user_id: str,
                          crop_type: Optional[str] = None,
                          additional_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze crop image for pest identification using Bedrock multimodal
        
        Args:
            image_data: Image bytes
            user_id: User ID for tracking
            crop_type: Type of crop (optional)
            additional_context: Additional context from user
        
        Returns:
            Dict with pest diagnosis results
        """
        try:
            # Validate image quality
            validation = self.validate_image_quality(image_data)
            
            if not validation['valid']:
                return {
                    'success': False,
                    'error': 'poor_image_quality',
                    'validation': validation
                }
            
            # Compress image
            compressed_image = self.compress_image(image_data)
            
            # Encode image to base64
            image_base64 = base64.b64encode(compressed_image).decode('utf-8')
            
            # Build prompt for pest identification
            prompt = self._build_pest_identification_prompt(crop_type, additional_context)
            
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
                    'temperature': 0.3  # Lower temperature for more consistent diagnosis
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            analysis_text = response_body['content'][0]['text']
            
            # Parse structured diagnosis from response
            diagnosis = self._parse_pest_diagnosis_response(analysis_text)
            
            # Generate diagnosis ID
            diagnosis_id = f"pest_{uuid.uuid4().hex[:12]}"
            
            # Store image in S3
            s3_key = f"images/pest-photos/{user_id}/{diagnosis_id}.jpg"
            self.s3_client.put_object(
                Bucket='rise-application-data',
                Key=s3_key,
                Body=compressed_image,
                ContentType='image/jpeg',
                Metadata={
                    'user_id': user_id,
                    'diagnosis_id': diagnosis_id,
                    'crop_type': crop_type or 'unknown',
                    'timestamp': str(int(datetime.now().timestamp()))
                }
            )
            
            # Store diagnosis in DynamoDB
            self._store_pest_diagnosis(
                diagnosis_id=diagnosis_id,
                user_id=user_id,
                s3_key=s3_key,
                diagnosis=diagnosis,
                crop_type=crop_type
            )
            
            return {
                'success': True,
                'diagnosis_id': diagnosis_id,
                's3_key': s3_key,
                **diagnosis
            }
        
        except Exception as e:
            logger.error(f"Pest identification error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_pest_identification_prompt(self, 
                                         crop_type: Optional[str],
                                         additional_context: Optional[str]) -> str:
        """Build prompt for pest identification"""
        
        prompt = """You are an expert agricultural entomologist specializing in pest identification and integrated pest management. 
Analyze this image and provide a detailed pest diagnosis.

"""
        
        if crop_type:
            prompt += f"Crop Type: {crop_type}\n"
        
        if additional_context:
            prompt += f"Additional Context: {additional_context}\n"
        
        prompt += """
Please provide your analysis in the following structured format:

1. PESTS IDENTIFIED (list all pests found, or "None" if no pests detected):
   - Pest Species: [Common and scientific name]
   - Confidence: [percentage, e.g., 85%]
   - Lifecycle Stage: [egg/larva/pupa/nymph/adult]
   - Population Density: [low/medium/high]
   - Severity: [low/medium/high/critical]

2. PEST CHARACTERISTICS OBSERVED:
   - Physical features visible in the image
   - Damage patterns on the crop
   - Location on plant (leaves, stems, roots, etc.)

3. INTEGRATED PEST MANAGEMENT RECOMMENDATIONS (prioritized):
   
   A. BIOLOGICAL CONTROLS (Priority 1):
      - Natural predators and parasitoids
      - Beneficial insects to introduce
      - Biological pesticides (Bt, neem, etc.)
   
   B. CULTURAL CONTROLS (Priority 2):
      - Crop rotation recommendations
      - Sanitation practices
      - Trap crops and companion planting
      - Physical barriers
   
   C. CHEMICAL TREATMENTS (Last Resort):
      - Pesticide Name: [specific product]
      - Active Ingredient: [chemical name]
      - Dosage: [exact amount per liter/hectare]
      - Application Method: [spray, soil drench, etc.]
      - Application Timing: [time of day, crop stage]
      - Frequency: [how often to apply]
      - Pre-Harvest Interval: [days before harvest]
      - Safety Precautions: [PPE, handling, storage]
      - Environmental Precautions: [water sources, beneficial insects]

4. LIFECYCLE AND TIMING INFORMATION:
   - Current lifecycle stage implications
   - Most vulnerable stages for control
   - Optimal timing for interventions
   - Expected pest development timeline

5. MONITORING AND THRESHOLD LEVELS:
   - How to monitor pest populations
   - Economic threshold levels
   - Action threshold recommendations

6. PREVENTIVE MEASURES:
   - Steps to prevent future infestations
   - Early detection methods
   - Resistant crop varieties (if available)

7. PROGNOSIS:
   - Expected outcome with recommended treatment
   - Potential yield impact if untreated
   - Timeline for pest control

If multiple pests are detected, prioritize recommendations by urgency and potential crop damage.

If the image quality is poor or pests are not clearly visible, indicate what specific improvements are needed for better identification.
"""
        
        return prompt
    
    def _parse_pest_diagnosis_response(self, analysis_text: str) -> Dict[str, Any]:
        """
        Parse structured pest diagnosis from AI response
        
        Args:
            analysis_text: Raw text response from Bedrock
        
        Returns:
            Structured diagnosis dict
        """
        pests = []
        confidence_score = 0.0
        severity = 'unknown'
        lifecycle_stage = 'unknown'
        population_density = 'unknown'
        
        # Extract pest information
        lines = analysis_text.split('\n')
        current_section = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Detect sections
            if 'pests identified' in line_lower:
                current_section = 'pests'
            elif 'biological controls' in line_lower:
                current_section = 'biological'
            elif 'chemical treatments' in line_lower:
                current_section = 'chemical'
            
            # Extract pest information
            if current_section == 'pests':
                if 'pest species:' in line_lower:
                    pest_name = line.split(':', 1)[1].strip()
                    pests.append(pest_name)
                
                if 'confidence:' in line_lower:
                    try:
                        conf_str = line.split(':', 1)[1].strip().replace('%', '')
                        confidence_score = float(conf_str) / 100
                    except:
                        pass
                
                if 'lifecycle stage:' in line_lower:
                    stage_str = line.split(':', 1)[1].strip().lower()
                    if any(stage in stage_str for stage in self.lifecycle_stages):
                        lifecycle_stage = stage_str
                
                if 'population density:' in line_lower:
                    density_str = line.split(':', 1)[1].strip().lower()
                    if density_str in ['low', 'medium', 'high']:
                        population_density = density_str
                
                if 'severity:' in line_lower:
                    severity_str = line.split(':', 1)[1].strip().lower()
                    if severity_str in self.severity_levels:
                        severity = severity_str
        
        # If no pests found, assume no infestation
        if not pests or 'none' in analysis_text.lower()[:200]:
            pests = ['No pests detected']
            confidence_score = 0.9
            severity = 'low'
            lifecycle_stage = 'N/A'
            population_density = 'none'
        
        # Default confidence if not extracted
        if confidence_score == 0.0:
            confidence_score = 0.75
        
        return {
            'pests': pests,
            'confidence_score': confidence_score,
            'severity': severity,
            'lifecycle_stage': lifecycle_stage,
            'population_density': population_density,
            'full_analysis': analysis_text,
            'multiple_pests': len(pests) > 1,
            'biological_controls': self._extract_biological_controls(analysis_text),
            'cultural_controls': self._extract_cultural_controls(analysis_text),
            'chemical_treatments': self._extract_chemical_treatments(analysis_text),
            'preventive_measures': self._extract_prevention(analysis_text)
        }
    
    def _extract_biological_controls(self, analysis_text: str) -> List[Dict[str, str]]:
        """Extract biological control recommendations from analysis"""
        controls = []
        
        # Simplified extraction - in production, use more sophisticated NLP
        if 'biological controls' in analysis_text.lower():
            controls.append({
                'type': 'biological',
                'description': 'Biological control methods recommended - see full analysis'
            })
        
        if 'natural predators' in analysis_text.lower() or 'beneficial insects' in analysis_text.lower():
            controls.append({
                'type': 'predators',
                'description': 'Natural predators available - see full analysis'
            })
        
        if 'neem' in analysis_text.lower() or 'bt' in analysis_text.lower():
            controls.append({
                'type': 'biopesticide',
                'description': 'Biological pesticides recommended - see full analysis'
            })
        
        return controls
    
    def _extract_cultural_controls(self, analysis_text: str) -> List[Dict[str, str]]:
        """Extract cultural control recommendations from analysis"""
        controls = []
        
        if 'crop rotation' in analysis_text.lower():
            controls.append({
                'type': 'rotation',
                'description': 'Crop rotation recommended - see full analysis'
            })
        
        if 'sanitation' in analysis_text.lower() or 'remove' in analysis_text.lower():
            controls.append({
                'type': 'sanitation',
                'description': 'Sanitation practices recommended - see full analysis'
            })
        
        if 'trap crop' in analysis_text.lower() or 'companion planting' in analysis_text.lower():
            controls.append({
                'type': 'planting',
                'description': 'Strategic planting methods recommended - see full analysis'
            })
        
        return controls
    
    def _extract_chemical_treatments(self, analysis_text: str) -> List[Dict[str, str]]:
        """Extract chemical treatment recommendations from analysis"""
        treatments = []
        
        if 'chemical treatment' in analysis_text.lower() or 'pesticide' in analysis_text.lower():
            treatments.append({
                'type': 'chemical',
                'description': 'Chemical treatment available as last resort - see full analysis for dosage and safety'
            })
        
        return treatments
    
    def _extract_prevention(self, analysis_text: str) -> List[str]:
        """Extract preventive measures from analysis"""
        # Simplified extraction
        return ['See full analysis for detailed preventive measures']
    
    def _store_pest_diagnosis(self,
                             diagnosis_id: str,
                             user_id: str,
                             s3_key: str,
                             diagnosis: Dict[str, Any],
                             crop_type: Optional[str]) -> None:
        """Store pest diagnosis in DynamoDB"""
        try:
            item = {
                'diagnosis_id': diagnosis_id,
                'user_id': user_id,
                'image_s3_key': s3_key,
                'diagnosis_result': diagnosis,
                'confidence_score': diagnosis.get('confidence_score', 0.0),
                'severity': diagnosis.get('severity', 'unknown'),
                'pests': diagnosis.get('pests', []),
                'lifecycle_stage': diagnosis.get('lifecycle_stage', 'unknown'),
                'population_density': diagnosis.get('population_density', 'unknown'),
                'crop_type': crop_type or 'unknown',
                'follow_up_status': 'pending',
                'created_timestamp': int(datetime.now().timestamp())
            }
            
            self.pest_diagnosis_table.put_item(Item=item)
            logger.info(f"Pest diagnosis stored: {diagnosis_id}")
        
        except Exception as e:
            logger.error(f"Error storing pest diagnosis: {e}")
    
    def get_pest_diagnosis_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get pest diagnosis history for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of records to return
        
        Returns:
            List of pest diagnosis records
        """
        try:
            response = self.pest_diagnosis_table.query(
                IndexName='UserPestDiagnosisIndex',
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            return response.get('Items', [])
        
        except Exception as e:
            logger.error(f"Error retrieving pest diagnosis history: {e}")
            return []
    
    def update_follow_up_status(self, 
                                diagnosis_id: str,
                                status: str,
                                notes: Optional[str] = None) -> bool:
        """
        Update follow-up status for a pest diagnosis
        
        Args:
            diagnosis_id: Diagnosis ID
            status: New status (e.g., 'treated', 'controlled', 'worsened')
            notes: Optional notes
        
        Returns:
            Success boolean
        """
        try:
            update_expr = 'SET follow_up_status = :status, updated_timestamp = :ts'
            expr_values = {
                ':status': status,
                ':ts': int(datetime.now().timestamp())
            }
            
            if notes:
                update_expr += ', follow_up_notes = :notes'
                expr_values[':notes'] = notes
            
            self.pest_diagnosis_table.update_item(
                Key={'diagnosis_id': diagnosis_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating follow-up status: {e}")
            return False
    
    def add_pest_knowledge(self,
                          pest_name: str,
                          scientific_name: str,
                          common_hosts: List[str],
                          lifecycle_info: Dict[str, Any],
                          control_methods: Dict[str, Any]) -> bool:
        """
        Add pest information to knowledge base
        
        Args:
            pest_name: Common name of pest
            scientific_name: Scientific name
            common_hosts: List of common host crops
            lifecycle_info: Lifecycle information
            control_methods: Control method recommendations
        
        Returns:
            Success boolean
        """
        try:
            pest_id = f"pest_{pest_name.lower().replace(' ', '_')}"
            
            item = {
                'pest_id': pest_id,
                'pest_name': pest_name,
                'scientific_name': scientific_name,
                'common_hosts': common_hosts,
                'lifecycle_info': lifecycle_info,
                'control_methods': control_methods,
                'created_timestamp': int(datetime.now().timestamp()),
                'updated_timestamp': int(datetime.now().timestamp())
            }
            
            self.pest_knowledge_table.put_item(Item=item)
            logger.info(f"Pest knowledge added: {pest_name}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error adding pest knowledge: {e}")
            return False
    
    def get_pest_knowledge(self, pest_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve pest information from knowledge base
        
        Args:
            pest_name: Common name of pest
        
        Returns:
            Pest information dict or None
        """
        try:
            pest_id = f"pest_{pest_name.lower().replace(' ', '_')}"
            
            response = self.pest_knowledge_table.get_item(
                Key={'pest_id': pest_id}
            )
            
            return response.get('Item')
        
        except Exception as e:
            logger.error(f"Error retrieving pest knowledge: {e}")
            return None


# Tool functions for agent integration

def create_pest_tools(region: str = "us-east-1") -> PestIdentificationTools:
    """
    Factory function to create pest identification tools instance
    
    Args:
        region: AWS region
    
    Returns:
        PestIdentificationTools instance
    """
    return PestIdentificationTools(region=region)


def analyze_pest(image_data: bytes, 
                user_id: str,
                crop_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Tool function for analyzing pest from image
    
    Args:
        image_data: Image bytes
        user_id: User ID
        crop_type: Optional crop type
    
    Returns:
        Pest diagnosis results
    """
    tools = create_pest_tools()
    return tools.analyze_pest_image(image_data, user_id, crop_type)
