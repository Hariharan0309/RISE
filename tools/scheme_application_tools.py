"""
RISE Scheme Application Tools
Tools for application assistance, document validation, and status tracking
"""

import boto3
import logging
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class SchemeApplicationTools:
    """Application assistance tools for RISE farming assistant"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize application tools with AWS clients
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        self.translate = boto3.client('translate', region_name=region)
        self.polly = boto3.client('polly', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        
        # DynamoDB tables
        self.applications_table = self.dynamodb.Table('RISE-SchemeApplications')
        self.schemes_table = self.dynamodb.Table('RISE-GovernmentSchemes')
        self.user_profiles_table = self.dynamodb.Table('RISE-UserProfiles')
        
        # Document format requirements
        self.document_formats = {
            'Aadhaar Card': {'formats': ['pdf', 'jpg', 'jpeg', 'png'], 'max_size_mb': 2},
            'Land Records': {'formats': ['pdf'], 'max_size_mb': 5},
            'Bank Passbook': {'formats': ['pdf', 'jpg', 'jpeg', 'png'], 'max_size_mb': 2},
            'Income Certificate': {'formats': ['pdf'], 'max_size_mb': 3},
            'Caste Certificate': {'formats': ['pdf'], 'max_size_mb': 3},
            'Passport Photo': {'formats': ['jpg', 'jpeg', 'png'], 'max_size_mb': 1}
        }
        
        logger.info(f"Application tools initialized in region {region}")
    
    def generate_application_wizard(self, user_id: str, scheme_id: str, 
                                   language: str = 'hi') -> Dict[str, Any]:
        """
        Generate voice-guided step-by-step application wizard
        
        Args:
            user_id: User identifier
            scheme_id: Scheme identifier
            language: Language code for voice guidance
        
        Returns:
            Dict with wizard steps and voice instructions
        """
        try:
            # Get scheme details
            scheme_response = self.schemes_table.get_item(Key={'scheme_id': scheme_id})
            
            if 'Item' not in scheme_response:
                return {
                    'success': False,
                    'error': f'Scheme not found: {scheme_id}'
                }
            
            scheme = self._convert_decimals(scheme_response['Item'])
            
            # Get user profile
            user_response = self.user_profiles_table.get_item(Key={'user_id': user_id})
            user_profile = self._convert_decimals(user_response.get('Item', {}))
            
            # Generate wizard steps using AI
            wizard_steps = self._generate_wizard_steps(scheme, user_profile, language)
            
            # Generate voice instructions for each step
            voice_instructions = []
            for step in wizard_steps:
                voice_audio = self._generate_voice_instruction(step, language)
                voice_instructions.append(voice_audio)
            
            return {
                'success': True,
                'scheme_id': scheme_id,
                'scheme_name': scheme['scheme_name'],
                'wizard_steps': wizard_steps,
                'voice_instructions': voice_instructions,
                'total_steps': len(wizard_steps),
                'estimated_time_minutes': len(wizard_steps) * 3,
                'language': language
            }
        
        except Exception as e:
            logger.error(f"Wizard generation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_documents(self, documents: List[Dict[str, Any]], 
                          scheme_id: str) -> Dict[str, Any]:
        """
        Validate document formats and completeness
        
        Args:
            documents: List of document objects with name, format, size, s3_key
            scheme_id: Scheme identifier
        
        Returns:
            Dict with validation results
        """
        try:
            # Get required documents for scheme
            scheme_response = self.schemes_table.get_item(Key={'scheme_id': scheme_id})
            
            if 'Item' not in scheme_response:
                return {
                    'success': False,
                    'error': f'Scheme not found: {scheme_id}'
                }
            
            scheme = self._convert_decimals(scheme_response['Item'])
            required_docs = scheme.get('required_documents', [])
            
            validation_results = []
            missing_documents = []
            
            # Check each required document
            for required_doc in required_docs:
                doc_found = False
                
                for doc in documents:
                    if doc['name'].lower() == required_doc.lower():
                        doc_found = True
                        
                        # Validate format and size
                        validation = self._validate_document_format(doc, required_doc)
                        validation_results.append(validation)
                        break
                
                if not doc_found:
                    missing_documents.append(required_doc)
            
            # Check for extra documents
            extra_documents = []
            for doc in documents:
                if doc['name'] not in required_docs:
                    extra_documents.append(doc['name'])
            
            # Overall validation status
            all_valid = all(v['valid'] for v in validation_results) and len(missing_documents) == 0
            
            return {
                'success': True,
                'all_valid': all_valid,
                'validation_results': validation_results,
                'missing_documents': missing_documents,
                'extra_documents': extra_documents,
                'total_documents': len(documents),
                'required_documents': len(required_docs),
                'validation_summary': self._generate_validation_summary(
                    validation_results, missing_documents
                )
            }
        
        except Exception as e:
            logger.error(f"Document validation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def submit_application(self, user_id: str, scheme_id: str, 
                          application_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit application with digital helper
        
        Args:
            user_id: User identifier
            scheme_id: Scheme identifier
            application_data: Application form data and documents
        
        Returns:
            Dict with submission confirmation
        """
        try:
            # Generate application ID
            application_id = f"APP_{uuid.uuid4().hex[:12].upper()}"
            
            # Validate documents first
            documents = application_data.get('documents', [])
            validation = self.validate_documents(documents, scheme_id)
            
            if not validation.get('all_valid', False):
                return {
                    'success': False,
                    'error': 'Document validation failed',
                    'validation_results': validation
                }
            
            # Get scheme details
            scheme_response = self.schemes_table.get_item(Key={'scheme_id': scheme_id})
            scheme = self._convert_decimals(scheme_response['Item'])
            
            # Create application record
            application_item = {
                'application_id': application_id,
                'user_id': user_id,
                'scheme_id': scheme_id,
                'scheme_name': scheme['scheme_name'],
                'application_data': application_data,
                'documents': documents,
                'status': 'submitted',
                'submission_timestamp': int(datetime.now().timestamp()),
                'last_updated': int(datetime.now().timestamp()),
                'status_history': [{
                    'status': 'submitted',
                    'timestamp': int(datetime.now().timestamp()),
                    'notes': 'Application submitted successfully'
                }],
                'tracking_number': self._generate_tracking_number(application_id)
            }
            
            # Store application
            self.applications_table.put_item(Item=application_item)
            
            # Send confirmation notification
            self.send_application_notification(user_id, application_id, 'submission_confirmation')
            
            # Generate submission receipt
            receipt = self._generate_submission_receipt(application_item)
            
            return {
                'success': True,
                'application_id': application_id,
                'tracking_number': application_item['tracking_number'],
                'status': 'submitted',
                'submission_timestamp': application_item['submission_timestamp'],
                'receipt': receipt,
                'next_steps': [
                    'Your application has been submitted successfully',
                    f'Track your application using ID: {application_id}',
                    'You will receive updates via SMS and voice notifications',
                    'Expected processing time: 15-30 days'
                ]
            }
        
        except Exception as e:
            logger.error(f"Application submission error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def track_application_status(self, application_id: str) -> Dict[str, Any]:
        """
        Track application status with detailed timeline
        
        Args:
            application_id: Application identifier
        
        Returns:
            Dict with current status and history
        """
        try:
            # Get application details
            app_response = self.applications_table.get_item(Key={'application_id': application_id})
            
            if 'Item' not in app_response:
                return {
                    'success': False,
                    'error': f'Application not found: {application_id}'
                }
            
            application = self._convert_decimals(app_response['Item'])
            
            # Calculate progress percentage
            status_progress = {
                'submitted': 20,
                'under_review': 40,
                'documents_verified': 60,
                'approved': 80,
                'disbursed': 100,
                'rejected': 0
            }
            
            current_status = application['status']
            progress = status_progress.get(current_status, 0)
            
            # Estimate completion date
            submission_date = datetime.fromtimestamp(application['submission_timestamp'])
            estimated_completion = submission_date + timedelta(days=30)
            
            # Generate status timeline
            timeline = self._generate_status_timeline(application['status_history'])
            
            return {
                'success': True,
                'application_id': application_id,
                'tracking_number': application['tracking_number'],
                'current_status': current_status,
                'progress_percentage': progress,
                'scheme_name': application['scheme_name'],
                'submission_date': submission_date.strftime('%Y-%m-%d'),
                'last_updated': datetime.fromtimestamp(application['last_updated']).strftime('%Y-%m-%d %H:%M'),
                'estimated_completion': estimated_completion.strftime('%Y-%m-%d'),
                'status_timeline': timeline,
                'next_action': self._get_next_action(current_status)
            }
        
        except Exception as e:
            logger.error(f"Status tracking error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_application_notification(self, user_id: str, application_id: str,
                                     notification_type: str) -> Dict[str, Any]:
        """
        Send notification for application updates
        
        Args:
            user_id: User identifier
            application_id: Application identifier
            notification_type: Type of notification
        
        Returns:
            Dict with notification status
        """
        try:
            # Get user profile for language preference
            user_response = self.user_profiles_table.get_item(Key={'user_id': user_id})
            user_profile = self._convert_decimals(user_response.get('Item', {}))
            language = user_profile.get('preferences', {}).get('language', 'hi')
            
            # Get application details
            app_response = self.applications_table.get_item(Key={'application_id': application_id})
            application = self._convert_decimals(app_response['Item'])
            
            # Generate notification message
            message = self._generate_notification_message(
                application, notification_type, language
            )
            
            # Send voice notification
            voice_audio = self._generate_voice_notification(message, language)
            
            # Send SMS notification
            phone_number = user_profile.get('phone_number')
            if phone_number:
                self._send_sms_notification(phone_number, message)
            
            return {
                'success': True,
                'notification_type': notification_type,
                'message': message,
                'voice_audio_url': voice_audio,
                'sent_timestamp': int(datetime.now().timestamp())
            }
        
        except Exception as e:
            logger.error(f"Notification error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    # Helper methods
    
    def _generate_wizard_steps(self, scheme: Dict[str, Any], 
                               user_profile: Dict[str, Any],
                               language: str) -> List[Dict[str, Any]]:
        """Generate step-by-step wizard instructions"""
        steps = []
        
        # Step 1: Scheme overview
        steps.append({
            'step_number': 1,
            'title': 'Scheme Overview',
            'description': f"Learn about {scheme['scheme_name']}",
            'instructions': [
                f"Scheme Name: {scheme['scheme_name']}",
                f"Benefit Amount: ₹{scheme.get('benefit_amount', 0):,.0f}",
                f"Category: {scheme['category'].replace('_', ' ').title()}"
            ],
            'action_required': 'Review and proceed',
            'estimated_time_minutes': 2
        })
        
        # Step 2: Eligibility confirmation
        steps.append({
            'step_number': 2,
            'title': 'Eligibility Confirmation',
            'description': 'Confirm you meet all eligibility criteria',
            'instructions': [
                'Review eligibility requirements',
                'Confirm your land ownership status',
                'Verify your farmer category'
            ],
            'action_required': 'Confirm eligibility',
            'estimated_time_minutes': 3
        })
        
        # Step 3: Document preparation
        required_docs = scheme.get('required_documents', [])
        steps.append({
            'step_number': 3,
            'title': 'Document Preparation',
            'description': 'Gather and prepare required documents',
            'instructions': [f"Prepare {doc}" for doc in required_docs],
            'action_required': 'Upload documents',
            'estimated_time_minutes': 10,
            'required_documents': required_docs
        })
        
        # Step 4: Form filling
        steps.append({
            'step_number': 4,
            'title': 'Application Form',
            'description': 'Fill in application details',
            'instructions': [
                'Enter personal information',
                'Provide farm details',
                'Add bank account information',
                'Review all entered information'
            ],
            'action_required': 'Complete form',
            'estimated_time_minutes': 8
        })
        
        # Step 5: Document upload
        steps.append({
            'step_number': 5,
            'title': 'Document Upload',
            'description': 'Upload all required documents',
            'instructions': [
                'Upload documents in correct format',
                'Ensure documents are clear and readable',
                'Verify all documents are uploaded'
            ],
            'action_required': 'Upload and verify',
            'estimated_time_minutes': 5
        })
        
        # Step 6: Review and submit
        steps.append({
            'step_number': 6,
            'title': 'Review and Submit',
            'description': 'Final review before submission',
            'instructions': [
                'Review all information carefully',
                'Check document uploads',
                'Confirm submission',
                'Save application ID for tracking'
            ],
            'action_required': 'Submit application',
            'estimated_time_minutes': 3
        })
        
        return steps
    
    def _generate_voice_instruction(self, step: Dict[str, Any], language: str) -> str:
        """Generate voice instruction for a wizard step"""
        try:
            # Create instruction text
            text = f"Step {step['step_number']}: {step['title']}. "
            text += f"{step['description']}. "
            text += "Instructions: " + ". ".join(step['instructions'][:3])
            
            # Translate if needed
            if language != 'en':
                translation = self.translate.translate_text(
                    Text=text,
                    SourceLanguageCode='en',
                    TargetLanguageCode=language
                )
                text = translation['TranslatedText']
            
            # Generate voice using Polly
            voice_id = 'Aditi' if language == 'hi' else 'Joanna'
            
            response = self.polly.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                Engine='neural'
            )
            
            # In production, save to S3 and return URL
            # For now, return placeholder
            audio_url = f"s3://rise-audio/wizard/{step['step_number']}.mp3"
            
            return audio_url
        
        except Exception as e:
            logger.error(f"Voice generation error: {e}")
            return ""
    
    def _validate_document_format(self, document: Dict[str, Any], 
                                  doc_name: str) -> Dict[str, Any]:
        """Validate individual document format"""
        requirements = self.document_formats.get(doc_name, {
            'formats': ['pdf', 'jpg', 'jpeg', 'png'],
            'max_size_mb': 5
        })
        
        doc_format = document.get('format', '').lower()
        doc_size_mb = document.get('size_mb', 0)
        
        valid = True
        issues = []
        
        # Check format
        if doc_format not in requirements['formats']:
            valid = False
            issues.append(f"Invalid format. Accepted: {', '.join(requirements['formats'])}")
        
        # Check size
        if doc_size_mb > requirements['max_size_mb']:
            valid = False
            issues.append(f"File too large. Max size: {requirements['max_size_mb']}MB")
        
        return {
            'document_name': doc_name,
            'valid': valid,
            'issues': issues,
            'format': doc_format,
            'size_mb': doc_size_mb,
            'requirements': requirements
        }
    
    def _generate_validation_summary(self, validation_results: List[Dict[str, Any]],
                                    missing_documents: List[str]) -> str:
        """Generate human-readable validation summary"""
        valid_count = sum(1 for v in validation_results if v['valid'])
        total_count = len(validation_results)
        
        summary = f"{valid_count}/{total_count} documents validated successfully. "
        
        if missing_documents:
            summary += f"Missing: {', '.join(missing_documents)}. "
        
        invalid_docs = [v['document_name'] for v in validation_results if not v['valid']]
        if invalid_docs:
            summary += f"Invalid: {', '.join(invalid_docs)}."
        
        return summary
    
    def _generate_tracking_number(self, application_id: str) -> str:
        """Generate human-readable tracking number"""
        # Extract last 8 characters and format
        short_id = application_id[-8:]
        return f"RISE-{short_id[:4]}-{short_id[4:]}"
    
    def _generate_submission_receipt(self, application: Dict[str, Any]) -> Dict[str, Any]:
        """Generate submission receipt"""
        return {
            'application_id': application['application_id'],
            'tracking_number': application['tracking_number'],
            'scheme_name': application['scheme_name'],
            'submission_date': datetime.fromtimestamp(
                application['submission_timestamp']
            ).strftime('%Y-%m-%d %H:%M:%S'),
            'status': application['status'],
            'documents_submitted': len(application['documents']),
            'receipt_message': 'Your application has been successfully submitted. '
                             'Please save your tracking number for future reference.'
        }
    
    def _generate_status_timeline(self, status_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate visual timeline from status history"""
        timeline = []
        
        for entry in status_history:
            timeline.append({
                'status': entry['status'],
                'date': datetime.fromtimestamp(entry['timestamp']).strftime('%Y-%m-%d'),
                'time': datetime.fromtimestamp(entry['timestamp']).strftime('%H:%M'),
                'notes': entry.get('notes', ''),
                'completed': True
            })
        
        return timeline
    
    def _get_next_action(self, current_status: str) -> str:
        """Get next action based on current status"""
        actions = {
            'submitted': 'Wait for initial review (3-5 days)',
            'under_review': 'Application is being reviewed by officials',
            'documents_verified': 'Documents verified, awaiting approval',
            'approved': 'Application approved, awaiting disbursement',
            'disbursed': 'Benefit amount has been disbursed to your account',
            'rejected': 'Application rejected. Contact local office for details'
        }
        
        return actions.get(current_status, 'Check status regularly for updates')
    
    def _generate_notification_message(self, application: Dict[str, Any],
                                      notification_type: str, language: str) -> str:
        """Generate notification message"""
        messages = {
            'submission_confirmation': f"Your application for {application['scheme_name']} has been submitted successfully. "
                                     f"Tracking number: {application['tracking_number']}",
            'status_update': f"Status update for {application['scheme_name']}: {application['status']}",
            'document_required': f"Additional documents required for {application['scheme_name']}",
            'approved': f"Congratulations! Your application for {application['scheme_name']} has been approved",
            'rejected': f"Your application for {application['scheme_name']} has been rejected. Please contact local office"
        }
        
        message = messages.get(notification_type, 'Application update')
        
        # Translate if needed
        if language != 'en':
            try:
                translation = self.translate.translate_text(
                    Text=message,
                    SourceLanguageCode='en',
                    TargetLanguageCode=language
                )
                message = translation['TranslatedText']
            except Exception as e:
                logger.error(f"Translation error: {e}")
        
        return message
    
    def _generate_voice_notification(self, message: str, language: str) -> str:
        """Generate voice notification"""
        try:
            voice_id = 'Aditi' if language == 'hi' else 'Joanna'
            
            response = self.polly.synthesize_speech(
                Text=message,
                OutputFormat='mp3',
                VoiceId=voice_id,
                Engine='neural'
            )
            
            # In production, save to S3 and return URL
            audio_url = f"s3://rise-audio/notifications/{uuid.uuid4().hex[:8]}.mp3"
            
            return audio_url
        
        except Exception as e:
            logger.error(f"Voice notification error: {e}")
            return ""
    
    def _send_sms_notification(self, phone_number: str, message: str):
        """Send SMS notification via SNS"""
        try:
            self.sns.publish(
                PhoneNumber=phone_number,
                Message=message
            )
            logger.info(f"SMS sent to {phone_number}")
        except Exception as e:
            logger.error(f"SMS sending error: {e}")
    
    def _convert_decimals(self, obj):
        """Convert Decimal objects to float for JSON serialization"""
        if isinstance(obj, list):
            return [self._convert_decimals(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._convert_decimals(value) for key, value in obj.items()}
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj


# Tool functions for agent integration

def create_application_tools(region: str = "us-east-1") -> SchemeApplicationTools:
    """
    Factory function to create application tools instance
    
    Args:
        region: AWS region
    
    Returns:
        SchemeApplicationTools instance
    """
    return SchemeApplicationTools(region=region)
