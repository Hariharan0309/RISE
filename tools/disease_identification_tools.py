"""
RISE Crop Disease Identification Tools
Tools for analyzing crop images and identifying diseases using Amazon Bedrock multimodal
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


class DiseaseIdentificationTools:
    """Crop disease identification tools using Amazon Bedrock multimodal"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize disease identification tools
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # DynamoDB table for diagnosis history
        self.diagnosis_table = self.dynamodb.Table('RISE-DiagnosisHistory')
        
        # Model configuration
        self.model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
        
        # Severity levels
        self.severity_levels = ['low', 'medium', 'high', 'critical']
        
        logger.info(f"Disease identification tools initialized in region {region}")
    
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
        Validate image quality for disease identification
        
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
                guidance.append('Try to capture the crop in a more balanced frame')
            
            # Basic blur detection (simplified)
            # In production, use more sophisticated algorithms
            
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
    
    def analyze_crop_image(self, 
                          image_data: bytes,
                          user_id: str,
                          crop_type: Optional[str] = None,
                          additional_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze crop image for disease identification using Bedrock multimodal
        
        Args:
            image_data: Image bytes
            user_id: User ID for tracking
            crop_type: Type of crop (optional)
            additional_context: Additional context from user
        
        Returns:
            Dict with diagnosis results
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
            
            # Build prompt for disease identification
            prompt = self._build_disease_identification_prompt(crop_type, additional_context)
            
            # Call Bedrock with multimodal input
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 2000,
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
                    'temperature': 0.3  # Lower temperature for more consistent medical-style diagnosis
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            analysis_text = response_body['content'][0]['text']
            
            # Parse structured diagnosis from response
            diagnosis = self._parse_diagnosis_response(analysis_text)
            
            # Generate diagnosis ID
            diagnosis_id = f"diag_{uuid.uuid4().hex[:12]}"
            
            # Store image in S3
            s3_key = f"images/crop-photos/{user_id}/{diagnosis_id}.jpg"
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
            self._store_diagnosis(
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
            logger.error(f"Disease identification error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_disease_identification_prompt(self, 
                                            crop_type: Optional[str],
                                            additional_context: Optional[str]) -> str:
        """Build prompt for disease identification"""
        
        prompt = """You are an expert agricultural pathologist specializing in crop disease identification. 
Analyze this crop image and provide a detailed diagnosis.

"""
        
        if crop_type:
            prompt += f"Crop Type: {crop_type}\n"
        
        if additional_context:
            prompt += f"Additional Context: {additional_context}\n"
        
        prompt += """
Please provide your analysis in the following structured format:

1. DISEASES DETECTED (list all diseases found, or "None" if healthy):
   - Disease Name: [Common and scientific name]
   - Confidence: [percentage, e.g., 85%]
   - Severity: [low/medium/high/critical]
   - Affected Area: [description of affected parts]

2. SYMPTOMS OBSERVED:
   - List visible symptoms in the image

3. TREATMENT RECOMMENDATIONS (prioritized by urgency):
   For each disease:
   - Immediate Actions: [what to do now]
   - Chemical Treatment: [specific fungicides/pesticides with dosage]
   - Organic Alternatives: [natural treatment options]
   - Application Timing: [when and how often]
   - Safety Precautions: [protective measures]

4. PREVENTIVE MEASURES:
   - Steps to prevent future occurrences

5. PROGNOSIS:
   - Expected outcome with treatment
   - Timeline for recovery

6. ADDITIONAL NOTES:
   - Any other relevant observations

If multiple diseases are detected, prioritize recommendations by urgency and potential impact on yield.

If the image quality is poor or the crop is not clearly visible, indicate what specific improvements are needed for better diagnosis.
"""
        
        return prompt
    
    def _parse_diagnosis_response(self, analysis_text: str) -> Dict[str, Any]:
        """
        Parse structured diagnosis from AI response
        
        Args:
            analysis_text: Raw text response from Bedrock
        
        Returns:
            Structured diagnosis dict
        """
        # This is a simplified parser. In production, use more robust parsing
        # or request JSON output from the model
        
        diseases = []
        confidence_score = 0.0
        severity = 'unknown'
        treatment_recommendations = []
        
        # Extract diseases (simplified pattern matching)
        lines = analysis_text.split('\n')
        current_section = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Detect sections
            if 'diseases detected' in line_lower:
                current_section = 'diseases'
            elif 'treatment recommendations' in line_lower:
                current_section = 'treatment'
            elif 'preventive measures' in line_lower:
                current_section = 'prevention'
            
            # Extract disease information
            if current_section == 'diseases' and 'disease name:' in line_lower:
                disease_name = line.split(':', 1)[1].strip()
                diseases.append(disease_name)
            
            # Extract confidence
            if 'confidence:' in line_lower:
                try:
                    conf_str = line.split(':', 1)[1].strip().replace('%', '')
                    confidence_score = float(conf_str) / 100
                except:
                    pass
            
            # Extract severity
            if 'severity:' in line_lower:
                severity_str = line.split(':', 1)[1].strip().lower()
                if severity_str in self.severity_levels:
                    severity = severity_str
        
        # If no diseases found, assume healthy
        if not diseases or 'none' in analysis_text.lower()[:200]:
            diseases = ['Healthy - No disease detected']
            confidence_score = 0.9
            severity = 'low'
        
        # Default confidence if not extracted
        if confidence_score == 0.0:
            confidence_score = 0.75
        
        return {
            'diseases': diseases,
            'confidence_score': confidence_score,
            'severity': severity,
            'full_analysis': analysis_text,
            'multiple_issues': len(diseases) > 1,
            'treatment_recommendations': self._extract_treatments(analysis_text),
            'preventive_measures': self._extract_prevention(analysis_text)
        }
    
    def _extract_treatments(self, analysis_text: str) -> List[Dict[str, str]]:
        """Extract treatment recommendations from analysis"""
        treatments = []
        
        # Simplified extraction - in production, use more sophisticated NLP
        if 'chemical treatment' in analysis_text.lower():
            treatments.append({
                'type': 'chemical',
                'description': 'Chemical treatment recommended - see full analysis'
            })
        
        if 'organic' in analysis_text.lower():
            treatments.append({
                'type': 'organic',
                'description': 'Organic alternatives available - see full analysis'
            })
        
        return treatments
    
    def _extract_prevention(self, analysis_text: str) -> List[str]:
        """Extract preventive measures from analysis"""
        # Simplified extraction
        return ['See full analysis for detailed preventive measures']
    
    def _store_diagnosis(self,
                        diagnosis_id: str,
                        user_id: str,
                        s3_key: str,
                        diagnosis: Dict[str, Any],
                        crop_type: Optional[str]) -> None:
        """Store diagnosis in DynamoDB"""
        try:
            item = {
                'diagnosis_id': diagnosis_id,
                'user_id': user_id,
                'image_s3_key': s3_key,
                'diagnosis_result': diagnosis,
                'confidence_score': diagnosis.get('confidence_score', 0.0),
                'severity': diagnosis.get('severity', 'unknown'),
                'diseases': diagnosis.get('diseases', []),
                'crop_type': crop_type or 'unknown',
                'follow_up_status': 'pending',
                'created_timestamp': int(datetime.now().timestamp())
            }
            
            self.diagnosis_table.put_item(Item=item)
            logger.info(f"Diagnosis stored: {diagnosis_id}")
        
        except Exception as e:
            logger.error(f"Error storing diagnosis: {e}")
    
    def get_diagnosis_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get diagnosis history for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of records to return
        
        Returns:
            List of diagnosis records
        """
        try:
            response = self.diagnosis_table.query(
                IndexName='UserDiagnosisIndex',
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            return response.get('Items', [])
        
        except Exception as e:
            logger.error(f"Error retrieving diagnosis history: {e}")
            return []
    
    def update_follow_up_status(self, 
                                diagnosis_id: str,
                                status: str,
                                notes: Optional[str] = None) -> bool:
        """
        Update follow-up status for a diagnosis
        
        Args:
            diagnosis_id: Diagnosis ID
            status: New status (e.g., 'treated', 'improved', 'worsened')
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
            
            self.diagnosis_table.update_item(
                Key={'diagnosis_id': diagnosis_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating follow-up status: {e}")
            return False


# Tool functions for agent integration

def create_disease_tools(region: str = "us-east-1") -> DiseaseIdentificationTools:
    """
    Factory function to create disease identification tools instance
    
    Args:
        region: AWS region
    
    Returns:
        DiseaseIdentificationTools instance
    """
    return DiseaseIdentificationTools(region=region)


def analyze_crop_disease(image_data: bytes, 
                         user_id: str,
                         crop_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Tool function for analyzing crop disease from image
    
    Args:
        image_data: Image bytes
        user_id: User ID
        crop_type: Optional crop type
    
    Returns:
        Diagnosis results
    """
    tools = create_disease_tools()
    return tools.analyze_crop_image(image_data, user_id, crop_type)
