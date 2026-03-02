"""
RISE Diagnosis History Lambda Function
Lambda function for retrieving and managing diagnosis history with filtering and sorting
"""

import boto3
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for DynamoDB Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class DiagnosisHistoryService:
    """Service for managing diagnosis history"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize diagnosis history service
        
        Args:
            region: AWS region
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        
        # DynamoDB tables
        self.diagnosis_table = self.dynamodb.Table('RISE-DiagnosisHistory')
        self.pest_diagnosis_table = self.dynamodb.Table('RISE-PestDiagnosisHistory')
        
        logger.info(f"Diagnosis history service initialized in region {region}")
    
    def get_diagnosis_history(self,
                             user_id: str,
                             limit: int = 20,
                             filters: Optional[Dict[str, Any]] = None,
                             sort_by: str = 'timestamp',
                             sort_order: str = 'desc') -> Dict[str, Any]:
        """
        Get diagnosis history for a user with filtering and sorting
        
        Args:
            user_id: User ID
            limit: Maximum number of records
            filters: Optional filters (severity, crop_type, date_range, follow_up_status)
            sort_by: Field to sort by (timestamp, confidence_score, severity)
            sort_order: Sort order (asc, desc)
        
        Returns:
            Dict with diagnosis history and metadata
        """
        try:
            # Query both disease and pest diagnosis tables
            disease_diagnoses = self._query_disease_diagnoses(user_id, limit)
            pest_diagnoses = self._query_pest_diagnoses(user_id, limit)
            
            # Combine and normalize
            all_diagnoses = []
            
            for diag in disease_diagnoses:
                all_diagnoses.append({
                    **diag,
                    'diagnosis_type': 'disease'
                })
            
            for diag in pest_diagnoses:
                all_diagnoses.append({
                    **diag,
                    'diagnosis_type': 'pest'
                })
            
            # Apply filters
            if filters:
                all_diagnoses = self._apply_filters(all_diagnoses, filters)
            
            # Sort
            all_diagnoses = self._sort_diagnoses(all_diagnoses, sort_by, sort_order)
            
            # Limit results
            all_diagnoses = all_diagnoses[:limit]
            
            # Calculate statistics
            stats = self._calculate_statistics(all_diagnoses)
            
            return {
                'success': True,
                'count': len(all_diagnoses),
                'diagnoses': all_diagnoses,
                'statistics': stats,
                'filters_applied': filters or {},
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        
        except Exception as e:
            logger.error(f"Error retrieving diagnosis history: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _query_disease_diagnoses(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Query disease diagnoses from DynamoDB"""
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
            logger.error(f"Error querying disease diagnoses: {e}")
            return []
    
    def _query_pest_diagnoses(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Query pest diagnoses from DynamoDB"""
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
            logger.error(f"Error querying pest diagnoses: {e}")
            return []
    
    def _apply_filters(self, diagnoses: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to diagnosis list"""
        filtered = diagnoses
        
        # Filter by severity
        if 'severity' in filters and filters['severity']:
            severity_filter = filters['severity'].lower()
            filtered = [d for d in filtered if d.get('severity', '').lower() == severity_filter]
        
        # Filter by crop type
        if 'crop_type' in filters and filters['crop_type']:
            crop_filter = filters['crop_type'].lower()
            filtered = [d for d in filtered if crop_filter in d.get('crop_type', '').lower()]
        
        # Filter by follow-up status
        if 'follow_up_status' in filters and filters['follow_up_status']:
            status_filter = filters['follow_up_status'].lower()
            filtered = [d for d in filtered if d.get('follow_up_status', '').lower() == status_filter]
        
        # Filter by date range
        if 'date_from' in filters and filters['date_from']:
            date_from = int(filters['date_from'])
            filtered = [d for d in filtered if d.get('created_timestamp', 0) >= date_from]
        
        if 'date_to' in filters and filters['date_to']:
            date_to = int(filters['date_to'])
            filtered = [d for d in filtered if d.get('created_timestamp', 0) <= date_to]
        
        # Filter by diagnosis type
        if 'diagnosis_type' in filters and filters['diagnosis_type']:
            type_filter = filters['diagnosis_type'].lower()
            filtered = [d for d in filtered if d.get('diagnosis_type', '').lower() == type_filter]
        
        return filtered
    
    def _sort_diagnoses(self, diagnoses: List[Dict[str, Any]], sort_by: str, sort_order: str) -> List[Dict[str, Any]]:
        """Sort diagnosis list"""
        reverse = (sort_order.lower() == 'desc')
        
        if sort_by == 'timestamp':
            return sorted(diagnoses, key=lambda x: x.get('created_timestamp', 0), reverse=reverse)
        elif sort_by == 'confidence_score':
            return sorted(diagnoses, key=lambda x: float(x.get('confidence_score', 0)), reverse=reverse)
        elif sort_by == 'severity':
            severity_order = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
            return sorted(diagnoses, key=lambda x: severity_order.get(x.get('severity', 'low'), 0), reverse=reverse)
        else:
            return diagnoses
    
    def _calculate_statistics(self, diagnoses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics from diagnosis history"""
        if not diagnoses:
            return {
                'total_diagnoses': 0,
                'severity_distribution': {},
                'average_confidence': 0.0,
                'follow_up_status_distribution': {},
                'diagnosis_type_distribution': {}
            }
        
        severity_counts = {}
        follow_up_counts = {}
        type_counts = {}
        total_confidence = 0.0
        
        for diag in diagnoses:
            # Severity distribution
            severity = diag.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Follow-up status distribution
            status = diag.get('follow_up_status', 'pending')
            follow_up_counts[status] = follow_up_counts.get(status, 0) + 1
            
            # Diagnosis type distribution
            diag_type = diag.get('diagnosis_type', 'unknown')
            type_counts[diag_type] = type_counts.get(diag_type, 0) + 1
            
            # Confidence score
            total_confidence += float(diag.get('confidence_score', 0))
        
        return {
            'total_diagnoses': len(diagnoses),
            'severity_distribution': severity_counts,
            'average_confidence': total_confidence / len(diagnoses) if diagnoses else 0.0,
            'follow_up_status_distribution': follow_up_counts,
            'diagnosis_type_distribution': type_counts
        }
    
    def update_follow_up_status(self,
                                diagnosis_id: str,
                                status: str,
                                notes: Optional[str] = None,
                                diagnosis_type: str = 'disease') -> Dict[str, Any]:
        """
        Update follow-up status for a diagnosis
        
        Args:
            diagnosis_id: Diagnosis ID
            status: New status (pending, treatment_applied, improving, worsened, resolved)
            notes: Optional follow-up notes
            diagnosis_type: Type of diagnosis (disease or pest)
        
        Returns:
            Success response
        """
        try:
            # Select appropriate table
            table = self.diagnosis_table if diagnosis_type == 'disease' else self.pest_diagnosis_table
            
            update_expr = 'SET follow_up_status = :status, updated_timestamp = :ts'
            expr_values = {
                ':status': status,
                ':ts': int(datetime.now().timestamp())
            }
            
            if notes:
                update_expr += ', follow_up_notes = :notes'
                expr_values[':notes'] = notes
            
            table.update_item(
                Key={'diagnosis_id': diagnosis_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
            
            return {
                'success': True,
                'diagnosis_id': diagnosis_id,
                'status': status,
                'updated_timestamp': expr_values[':ts']
            }
        
        except Exception as e:
            logger.error(f"Error updating follow-up status: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_diagnosis_comparison(self,
                                diagnosis_ids: List[str],
                                diagnosis_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get comparison data for multiple diagnoses (treatment progress tracking)
        
        Args:
            diagnosis_ids: List of diagnosis IDs to compare
            diagnosis_types: Optional list of diagnosis types (disease/pest) for each ID
        
        Returns:
            Comparison data
        """
        try:
            if not diagnosis_types:
                diagnosis_types = ['disease'] * len(diagnosis_ids)
            
            diagnoses = []
            
            for diag_id, diag_type in zip(diagnosis_ids, diagnosis_types):
                table = self.diagnosis_table if diag_type == 'disease' else self.pest_diagnosis_table
                
                response = table.get_item(Key={'diagnosis_id': diag_id})
                
                if 'Item' in response:
                    diagnoses.append({
                        **response['Item'],
                        'diagnosis_type': diag_type
                    })
            
            if not diagnoses:
                return {
                    'success': False,
                    'error': 'No diagnoses found'
                }
            
            # Sort by timestamp
            diagnoses.sort(key=lambda x: x.get('created_timestamp', 0))
            
            # Calculate progress metrics
            progress = self._calculate_progress(diagnoses)
            
            return {
                'success': True,
                'count': len(diagnoses),
                'diagnoses': diagnoses,
                'progress': progress,
                'timeline': self._create_timeline(diagnoses)
            }
        
        except Exception as e:
            logger.error(f"Error getting diagnosis comparison: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_progress(self, diagnoses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate treatment progress from diagnosis sequence"""
        if len(diagnoses) < 2:
            return {
                'status': 'insufficient_data',
                'message': 'Need at least 2 diagnoses to track progress'
            }
        
        first = diagnoses[0]
        latest = diagnoses[-1]
        
        # Severity progression
        severity_order = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        first_severity = severity_order.get(first.get('severity', 'low'), 1)
        latest_severity = severity_order.get(latest.get('severity', 'low'), 1)
        
        severity_change = first_severity - latest_severity  # Positive = improvement
        
        # Confidence change
        first_confidence = float(first.get('confidence_score', 0))
        latest_confidence = float(latest.get('confidence_score', 0))
        confidence_change = latest_confidence - first_confidence
        
        # Determine overall progress
        if severity_change > 0:
            progress_status = 'improving'
        elif severity_change < 0:
            progress_status = 'worsening'
        else:
            progress_status = 'stable'
        
        return {
            'status': progress_status,
            'severity_change': severity_change,
            'confidence_change': confidence_change,
            'first_diagnosis_date': first.get('created_timestamp'),
            'latest_diagnosis_date': latest.get('created_timestamp'),
            'days_elapsed': (latest.get('created_timestamp', 0) - first.get('created_timestamp', 0)) / 86400,
            'total_diagnoses': len(diagnoses)
        }
    
    def _create_timeline(self, diagnoses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create timeline of diagnosis events"""
        timeline = []
        
        for diag in diagnoses:
            timeline.append({
                'diagnosis_id': diag.get('diagnosis_id'),
                'timestamp': diag.get('created_timestamp'),
                'date': datetime.fromtimestamp(diag.get('created_timestamp', 0)).strftime('%Y-%m-%d %H:%M'),
                'severity': diag.get('severity'),
                'confidence': float(diag.get('confidence_score', 0)),
                'follow_up_status': diag.get('follow_up_status', 'pending'),
                'diagnosis_type': diag.get('diagnosis_type', 'unknown')
            })
        
        return timeline
    
    def generate_diagnosis_report(self,
                                 diagnosis_id: str,
                                 diagnosis_type: str = 'disease',
                                 include_images: bool = False) -> Dict[str, Any]:
        """
        Generate comprehensive diagnosis report
        
        Args:
            diagnosis_id: Diagnosis ID
            diagnosis_type: Type of diagnosis (disease or pest)
            include_images: Whether to include image URLs
        
        Returns:
            Report data
        """
        try:
            # Get diagnosis
            table = self.diagnosis_table if diagnosis_type == 'disease' else self.pest_diagnosis_table
            response = table.get_item(Key={'diagnosis_id': diagnosis_id})
            
            if 'Item' not in response:
                return {
                    'success': False,
                    'error': 'Diagnosis not found'
                }
            
            diagnosis = response['Item']
            
            # Generate presigned URL for image if requested
            image_url = None
            if include_images and 'image_s3_key' in diagnosis:
                try:
                    image_url = self.s3_client.generate_presigned_url(
                        'get_object',
                        Params={
                            'Bucket': 'rise-application-data',
                            'Key': diagnosis['image_s3_key']
                        },
                        ExpiresIn=3600  # 1 hour
                    )
                except Exception as e:
                    logger.error(f"Error generating presigned URL: {e}")
            
            # Build report
            report = {
                'diagnosis_id': diagnosis_id,
                'diagnosis_type': diagnosis_type,
                'created_date': datetime.fromtimestamp(diagnosis.get('created_timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                'crop_type': diagnosis.get('crop_type', 'Unknown'),
                'severity': diagnosis.get('severity', 'unknown'),
                'confidence_score': float(diagnosis.get('confidence_score', 0)),
                'diseases_or_pests': diagnosis.get('diseases', []) or diagnosis.get('pests', []),
                'full_analysis': diagnosis.get('diagnosis_result', {}).get('full_analysis', ''),
                'treatment_recommendations': diagnosis.get('diagnosis_result', {}).get('treatment_recommendations', []),
                'preventive_measures': diagnosis.get('diagnosis_result', {}).get('preventive_measures', []),
                'follow_up_status': diagnosis.get('follow_up_status', 'pending'),
                'follow_up_notes': diagnosis.get('follow_up_notes', ''),
                'image_url': image_url
            }
            
            return {
                'success': True,
                'report': report
            }
        
        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for diagnosis history operations
    
    Event structure:
    {
        "action": "get_history" | "update_status" | "compare" | "generate_report",
        "user_id": "string",
        "diagnosis_id": "string",  # For update_status, generate_report
        "diagnosis_ids": ["string"],  # For compare
        "filters": {},  # For get_history
        "sort_by": "string",  # For get_history
        "sort_order": "string",  # For get_history
        "limit": int,  # For get_history
        "status": "string",  # For update_status
        "notes": "string",  # For update_status
        "diagnosis_type": "string"  # disease or pest
    }
    """
    try:
        service = DiagnosisHistoryService()
        
        action = event.get('action')
        
        if action == 'get_history':
            result = service.get_diagnosis_history(
                user_id=event['user_id'],
                limit=event.get('limit', 20),
                filters=event.get('filters'),
                sort_by=event.get('sort_by', 'timestamp'),
                sort_order=event.get('sort_order', 'desc')
            )
        
        elif action == 'update_status':
            result = service.update_follow_up_status(
                diagnosis_id=event['diagnosis_id'],
                status=event['status'],
                notes=event.get('notes'),
                diagnosis_type=event.get('diagnosis_type', 'disease')
            )
        
        elif action == 'compare':
            result = service.get_diagnosis_comparison(
                diagnosis_ids=event['diagnosis_ids'],
                diagnosis_types=event.get('diagnosis_types')
            )
        
        elif action == 'generate_report':
            result = service.generate_diagnosis_report(
                diagnosis_id=event['diagnosis_id'],
                diagnosis_type=event.get('diagnosis_type', 'disease'),
                include_images=event.get('include_images', False)
            )
        
        else:
            result = {
                'success': False,
                'error': f'Unknown action: {action}'
            }
        
        return {
            'statusCode': 200 if result.get('success') else 400,
            'body': json.dumps(result, cls=DecimalEncoder),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
    
    except Exception as e:
        logger.error(f"Lambda handler error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
