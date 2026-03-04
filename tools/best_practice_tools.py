"""
RISE Best Practice Sharing Tools
Tools for submitting, validating, and tracking farming best practices
"""

import boto3
from boto3.dynamodb.conditions import Key, Attr
import logging
from typing import Dict, Any, List, Optional
import time
from datetime import datetime, timedelta
import uuid
import json

logger = logging.getLogger(__name__)


class BestPracticeTools:
    """Tools for best practice sharing with AI validation and tracking"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize best practice tools with AWS clients
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=region)
        self.translate_client = boto3.client('translate', region_name=region)
        
        # DynamoDB tables
        self.practices_table = self.dynamodb.Table('RISE-BestPractices')
        self.adoptions_table = self.dynamodb.Table('RISE-PracticeAdoptions')
        self.users_table = self.dynamodb.Table('RISE-UserProfiles')
        
        # Supported languages
        self.supported_languages = ['hi', 'en', 'ta', 'te', 'kn', 'bn', 'gu', 'mr', 'pa']
        
        logger.info(f"Best practice tools initialized in region {region}")
    
    def submit_practice(self,
                       user_id: str,
                       title: str,
                       description: str,
                       language: str,
                       category: Dict[str, str],
                       steps: List[str],
                       expected_benefits: Dict[str, Any],
                       resources_needed: Optional[List[str]] = None,
                       images: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Submit a new farming best practice
        
        Args:
            user_id: User identifier
            title: Practice title
            description: Detailed description
            language: Original language code
            category: Dict with crop_type, practice_type, region
            steps: List of implementation steps
            expected_benefits: Dict with yield_increase, cost_reduction, etc.
            resources_needed: Optional list of required resources
            images: Optional list of S3 image keys
        
        Returns:
            Dict with submission result
        """
        try:
            # Validate language
            if language not in self.supported_languages:
                return {
                    'success': False,
                    'error': f'Unsupported language: {language}'
                }
            
            # Validate practice using Bedrock
            validation_result = self._validate_practice(
                title, description, steps, expected_benefits, category
            )
            
            if not validation_result['is_valid']:
                return {
                    'success': False,
                    'error': 'Practice validation failed',
                    'reason': validation_result['reason'],
                    'suggestions': validation_result.get('suggestions', [])
                }
            
            # Generate practice ID
            practice_id = f"practice_{uuid.uuid4().hex[:12]}"
            timestamp = int(time.time() * 1000)
            
            # Create practice item
            practice_item = {
                'practice_id': practice_id,
                'timestamp': timestamp,
                'user_id': user_id,
                'title': title,
                'description': description,
                'original_language': language,
                'category': category,
                'steps': steps,
                'expected_benefits': expected_benefits,
                'resources_needed': resources_needed or [],
                'images': images or [],
                'validation_score': validation_result['validation_score'],
                'scientific_references': validation_result.get('references', []),
                'adoption_count': 0,
                'success_count': 0,
                'failure_count': 0,
                'avg_success_rate': 0.0,
                'total_feedback': 0,
                'status': 'active',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Save to DynamoDB
            self.practices_table.put_item(Item=practice_item)
            
            logger.info(f"Created practice {practice_id} by user {user_id}")
            
            return {
                'success': True,
                'practice_id': practice_id,
                'timestamp': timestamp,
                'validation_score': validation_result['validation_score'],
                'scientific_references': validation_result.get('references', [])
            }
        
        except Exception as e:
            logger.error(f"Error submitting practice: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _validate_practice(self,
                          title: str,
                          description: str,
                          steps: List[str],
                          expected_benefits: Dict[str, Any],
                          category: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate practice against scientific literature using Amazon Bedrock
        
        Args:
            title: Practice title
            description: Practice description
            steps: Implementation steps
            expected_benefits: Expected benefits
            category: Practice category
        
        Returns:
            Dict with validation results
        """
        try:
            validation_prompt = f"""You are an agricultural expert validating a farming best practice.

Practice Title: {title}
Category: {json.dumps(category)}
Description: {description}

Implementation Steps:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(steps))}

Expected Benefits:
{json.dumps(expected_benefits, indent=2)}

Validate this practice by:
1. Checking if it aligns with scientific agricultural principles
2. Assessing if the expected benefits are realistic
3. Identifying any potential risks or concerns
4. Finding relevant scientific references or studies

Respond with JSON only:
{{
  "is_valid": true/false,
  "validation_score": 0-100,
  "reason": "explanation",
  "references": ["reference1", "reference2"],
  "suggestions": ["suggestion1", "suggestion2"],
  "risk_assessment": "low/medium/high",
  "confidence": 0-1
}}"""
            
            request_body = {
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1000,
                'messages': [{
                    'role': 'user',
                    'content': validation_prompt
                }],
                'temperature': 0.3
            }
            
            response = self.bedrock_client.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            result_text = response_body['content'][0]['text']
            
            # Parse JSON response
            result = json.loads(result_text)
            
            # Ensure minimum validation score for acceptance
            if result['validation_score'] < 60:
                result['is_valid'] = False
                if not result.get('reason'):
                    result['reason'] = 'Practice does not meet minimum validation standards'
            
            return result
        
        except Exception as e:
            logger.error(f"Error validating practice: {e}")
            # Default to requiring manual review
            return {
                'is_valid': False,
                'validation_score': 0,
                'reason': 'Automatic validation failed, manual review required',
                'references': [],
                'suggestions': []
            }
    
    def get_practices(self,
                     category: Optional[Dict[str, str]] = None,
                     sort_by: str = 'recent',
                     limit: int = 20,
                     last_evaluated_key: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Get best practices with optional filtering and sorting
        
        Args:
            category: Optional category filter
            sort_by: Sort method ('recent', 'popular', 'success_rate')
            limit: Maximum number of practices to return
            last_evaluated_key: Pagination key
        
        Returns:
            Dict with practices and pagination info
        """
        try:
            query_params = {
                'Limit': limit,
                'FilterExpression': Attr('status').eq('active')
            }
            
            if last_evaluated_key:
                query_params['ExclusiveStartKey'] = last_evaluated_key
            
            # Scan with filter
            response = self.practices_table.scan(**query_params)
            
            practices = response.get('Items', [])
            
            # Apply category filter
            if category:
                practices = [
                    p for p in practices
                    if all(p['category'].get(k) == v for k, v in category.items())
                ]
            
            # Sort practices
            if sort_by == 'popular':
                practices.sort(key=lambda x: x.get('adoption_count', 0), reverse=True)
            elif sort_by == 'success_rate':
                practices.sort(key=lambda x: x.get('avg_success_rate', 0), reverse=True)
            else:  # recent
                practices.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            return {
                'success': True,
                'practices': practices,
                'count': len(practices),
                'last_evaluated_key': response.get('LastEvaluatedKey')
            }
        
        except Exception as e:
            logger.error(f"Error getting practices: {e}")
            return {
                'success': False,
                'error': str(e),
                'practices': []
            }
    
    def get_practice(self, practice_id: str) -> Dict[str, Any]:
        """
        Get a single practice by ID
        
        Args:
            practice_id: Practice identifier
        
        Returns:
            Dict with practice data
        """
        try:
            response = self.practices_table.get_item(
                Key={'practice_id': practice_id}
            )
            
            practice = response.get('Item')
            
            if not practice:
                return {
                    'success': False,
                    'error': 'Practice not found'
                }
            
            return {
                'success': True,
                'practice': practice
            }
        
        except Exception as e:
            logger.error(f"Error getting practice: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def adopt_practice(self,
                      practice_id: str,
                      user_id: str,
                      implementation_date: str,
                      notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Record a farmer adopting a practice
        
        Args:
            practice_id: Practice identifier
            user_id: User identifier
            implementation_date: Date of implementation
            notes: Optional implementation notes
        
        Returns:
            Dict with adoption result
        """
        try:
            # Generate adoption ID
            adoption_id = f"adoption_{uuid.uuid4().hex[:12]}"
            timestamp = int(time.time() * 1000)
            
            # Create adoption record
            adoption_item = {
                'adoption_id': adoption_id,
                'practice_id': practice_id,
                'user_id': user_id,
                'implementation_date': implementation_date,
                'notes': notes or '',
                'status': 'in_progress',
                'success': None,
                'feedback': None,
                'results': {},
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Save adoption
            self.adoptions_table.put_item(Item=adoption_item)
            
            # Update practice adoption count
            self.practices_table.update_item(
                Key={'practice_id': practice_id},
                UpdateExpression='SET adoption_count = adoption_count + :inc, updated_at = :now',
                ExpressionAttributeValues={
                    ':inc': 1,
                    ':now': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"User {user_id} adopted practice {practice_id}")
            
            return {
                'success': True,
                'adoption_id': adoption_id,
                'timestamp': timestamp
            }
        
        except Exception as e:
            logger.error(f"Error adopting practice: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def submit_feedback(self,
                       adoption_id: str,
                       user_id: str,
                       success: bool,
                       feedback: str,
                       results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit feedback on an adopted practice
        
        Args:
            adoption_id: Adoption identifier
            user_id: User identifier
            success: Whether practice was successful
            feedback: Detailed feedback
            results: Measured results (yield_change, cost_change, etc.)
        
        Returns:
            Dict with feedback submission result
        """
        try:
            # Get adoption record
            adoption_response = self.adoptions_table.get_item(
                Key={'adoption_id': adoption_id}
            )
            
            adoption = adoption_response.get('Item')
            
            if not adoption:
                return {
                    'success': False,
                    'error': 'Adoption record not found'
                }
            
            if adoption['user_id'] != user_id:
                return {
                    'success': False,
                    'error': 'Unauthorized: adoption belongs to different user'
                }
            
            # Update adoption record
            self.adoptions_table.update_item(
                Key={'adoption_id': adoption_id},
                UpdateExpression='SET #status = :status, success = :success, feedback = :feedback, results = :results, updated_at = :now',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'completed',
                    ':success': success,
                    ':feedback': feedback,
                    ':results': results,
                    ':now': datetime.utcnow().isoformat()
                }
            )
            
            # Update practice statistics
            practice_id = adoption['practice_id']
            self._update_practice_statistics(practice_id, success, results)
            
            # Send feedback to contributor
            self._send_contributor_feedback(practice_id, success, feedback, results)
            
            logger.info(f"Feedback submitted for adoption {adoption_id}")
            
            return {
                'success': True,
                'message': 'Feedback submitted successfully'
            }
        
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_practice_statistics(self,
                                   practice_id: str,
                                   success: bool,
                                   results: Dict[str, Any]):
        """
        Update practice success rate and statistics
        
        Args:
            practice_id: Practice identifier
            success: Whether adoption was successful
            results: Measured results
        """
        try:
            # Get current practice
            practice_response = self.practices_table.get_item(
                Key={'practice_id': practice_id}
            )
            
            practice = practice_response.get('Item')
            
            if not practice:
                return
            
            # Update counts
            success_count = practice.get('success_count', 0)
            failure_count = practice.get('failure_count', 0)
            total_feedback = practice.get('total_feedback', 0)
            
            if success:
                success_count += 1
            else:
                failure_count += 1
            
            total_feedback += 1
            
            # Calculate new success rate
            avg_success_rate = (success_count / total_feedback) * 100 if total_feedback > 0 else 0
            
            # Update practice
            self.practices_table.update_item(
                Key={'practice_id': practice_id},
                UpdateExpression='SET success_count = :sc, failure_count = :fc, total_feedback = :tf, avg_success_rate = :asr, updated_at = :now',
                ExpressionAttributeValues={
                    ':sc': success_count,
                    ':fc': failure_count,
                    ':tf': total_feedback,
                    ':asr': round(avg_success_rate, 2),
                    ':now': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Updated statistics for practice {practice_id}")
        
        except Exception as e:
            logger.error(f"Error updating practice statistics: {e}")
    
    def _send_contributor_feedback(self,
                                  practice_id: str,
                                  success: bool,
                                  feedback: str,
                                  results: Dict[str, Any]):
        """
        Send feedback notification to practice contributor
        
        Args:
            practice_id: Practice identifier
            success: Whether adoption was successful
            feedback: User feedback
            results: Measured results
        """
        try:
            # Get practice to find contributor
            practice_response = self.practices_table.get_item(
                Key={'practice_id': practice_id}
            )
            
            practice = practice_response.get('Item')
            
            if not practice:
                return
            
            contributor_id = practice['user_id']
            
            # Create feedback notification
            notification = {
                'type': 'practice_feedback',
                'practice_id': practice_id,
                'practice_title': practice['title'],
                'success': success,
                'feedback': feedback,
                'results': results,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # In production, send via SNS or store in notifications table
            logger.info(f"Feedback notification sent to user {contributor_id}")
        
        except Exception as e:
            logger.error(f"Error sending contributor feedback: {e}")
    
    def get_adoption_analytics(self, practice_id: str) -> Dict[str, Any]:
        """
        Get detailed analytics for a practice
        
        Args:
            practice_id: Practice identifier
        
        Returns:
            Dict with analytics data
        """
        try:
            # Get practice
            practice_result = self.get_practice(practice_id)
            
            if not practice_result['success']:
                return practice_result
            
            practice = practice_result['practice']
            
            # Get all adoptions
            adoptions_response = self.adoptions_table.scan(
                FilterExpression=Attr('practice_id').eq(practice_id)
            )
            
            adoptions = adoptions_response.get('Items', [])
            
            # Calculate analytics
            total_adoptions = len(adoptions)
            completed_adoptions = [a for a in adoptions if a.get('status') == 'completed']
            successful_adoptions = [a for a in completed_adoptions if a.get('success')]
            
            # Aggregate results
            yield_changes = []
            cost_changes = []
            
            for adoption in completed_adoptions:
                results = adoption.get('results', {})
                if 'yield_change' in results:
                    yield_changes.append(results['yield_change'])
                if 'cost_change' in results:
                    cost_changes.append(results['cost_change'])
            
            avg_yield_change = sum(yield_changes) / len(yield_changes) if yield_changes else 0
            avg_cost_change = sum(cost_changes) / len(cost_changes) if cost_changes else 0
            
            return {
                'success': True,
                'practice_id': practice_id,
                'analytics': {
                    'total_adoptions': total_adoptions,
                    'completed_adoptions': len(completed_adoptions),
                    'successful_adoptions': len(successful_adoptions),
                    'success_rate': practice.get('avg_success_rate', 0),
                    'avg_yield_change': round(avg_yield_change, 2),
                    'avg_cost_change': round(avg_cost_change, 2),
                    'validation_score': practice.get('validation_score', 0),
                    'adoption_trend': self._calculate_adoption_trend(adoptions)
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting adoption analytics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_adoption_trend(self, adoptions: List[Dict]) -> str:
        """
        Calculate adoption trend (increasing, stable, decreasing)
        
        Args:
            adoptions: List of adoption records
        
        Returns:
            Trend description
        """
        if len(adoptions) < 2:
            return 'insufficient_data'
        
        # Sort by creation date
        sorted_adoptions = sorted(
            adoptions,
            key=lambda x: x.get('created_at', '')
        )
        
        # Compare first half vs second half
        mid_point = len(sorted_adoptions) // 2
        first_half = sorted_adoptions[:mid_point]
        second_half = sorted_adoptions[mid_point:]
        
        if len(second_half) > len(first_half) * 1.2:
            return 'increasing'
        elif len(second_half) < len(first_half) * 0.8:
            return 'decreasing'
        else:
            return 'stable'
    
    def search_practices(self,
                        query: str,
                        category: Optional[Dict[str, str]] = None,
                        limit: int = 20) -> Dict[str, Any]:
        """
        Search practices by keyword
        
        Args:
            query: Search query
            category: Optional category filter
            limit: Maximum results
        
        Returns:
            Dict with search results
        """
        try:
            # Scan all active practices
            response = self.practices_table.scan(
                FilterExpression=Attr('status').eq('active'),
                Limit=limit * 2
            )
            
            practices = response.get('Items', [])
            
            # Filter by query
            query_lower = query.lower()
            filtered_practices = [
                p for p in practices
                if query_lower in p['title'].lower() or query_lower in p['description'].lower()
            ]
            
            # Apply category filter
            if category:
                filtered_practices = [
                    p for p in filtered_practices
                    if all(p['category'].get(k) == v for k, v in category.items())
                ]
            
            # Sort by relevance (simple: by success rate)
            filtered_practices.sort(key=lambda x: x.get('avg_success_rate', 0), reverse=True)
            
            return {
                'success': True,
                'practices': filtered_practices[:limit],
                'count': len(filtered_practices),
                'query': query
            }
        
        except Exception as e:
            logger.error(f"Error searching practices: {e}")
            return {
                'success': False,
                'error': str(e),
                'practices': []
            }
    
    def translate_practice(self,
                          practice_id: str,
                          target_language: str) -> Dict[str, Any]:
        """
        Translate a practice to target language
        
        Args:
            practice_id: Practice identifier
            target_language: Target language code
        
        Returns:
            Dict with translated practice
        """
        try:
            # Get practice
            practice_result = self.get_practice(practice_id)
            
            if not practice_result['success']:
                return practice_result
            
            practice = practice_result['practice']
            
            # Check if already in target language
            if practice['original_language'] == target_language:
                return {
                    'success': True,
                    'practice': practice,
                    'translated': False
                }
            
            # Translate title and description
            title_translation = self.translate_client.translate_text(
                Text=practice['title'],
                SourceLanguageCode=practice['original_language'],
                TargetLanguageCode=target_language
            )
            
            description_translation = self.translate_client.translate_text(
                Text=practice['description'],
                SourceLanguageCode=practice['original_language'],
                TargetLanguageCode=target_language,
                TerminologyNames=['rise-agricultural-terms']
            )
            
            # Translate steps
            translated_steps = []
            for step in practice['steps']:
                step_translation = self.translate_client.translate_text(
                    Text=step,
                    SourceLanguageCode=practice['original_language'],
                    TargetLanguageCode=target_language,
                    TerminologyNames=['rise-agricultural-terms']
                )
                translated_steps.append(step_translation['TranslatedText'])
            
            # Create translated practice
            translated_practice = practice.copy()
            translated_practice['title'] = title_translation['TranslatedText']
            translated_practice['description'] = description_translation['TranslatedText']
            translated_practice['steps'] = translated_steps
            translated_practice['translated_to'] = target_language
            
            return {
                'success': True,
                'practice': translated_practice,
                'translated': True,
                'source_language': practice['original_language'],
                'target_language': target_language
            }
        
        except Exception as e:
            logger.error(f"Error translating practice: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_contributions(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's contributed practices and impact
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with user contributions
        """
        try:
            # Get user's practices
            response = self.practices_table.scan(
                FilterExpression=Attr('user_id').eq(user_id) & Attr('status').eq('active')
            )
            
            practices = response.get('Items', [])
            
            # Calculate impact metrics
            total_practices = len(practices)
            total_adoptions = sum(p.get('adoption_count', 0) for p in practices)
            total_successful = sum(p.get('success_count', 0) for p in practices)
            avg_success_rate = sum(p.get('avg_success_rate', 0) for p in practices) / max(total_practices, 1)
            
            # Find most popular practice
            most_popular = max(practices, key=lambda x: x.get('adoption_count', 0)) if practices else None
            
            return {
                'success': True,
                'user_id': user_id,
                'contributions': {
                    'total_practices': total_practices,
                    'total_adoptions': total_adoptions,
                    'total_successful': total_successful,
                    'avg_success_rate': round(avg_success_rate, 2),
                    'most_popular_practice': {
                        'practice_id': most_popular['practice_id'],
                        'title': most_popular['title'],
                        'adoptions': most_popular.get('adoption_count', 0)
                    } if most_popular else None
                },
                'practices': practices
            }
        
        except Exception as e:
            logger.error(f"Error getting user contributions: {e}")
            return {
                'success': False,
                'error': str(e)
            }
