"""
RISE Diagnosis History Tools
Tools for managing diagnosis history, follow-up tracking, and treatment progress
"""

import boto3
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class DiagnosisHistoryTools:
    """Tools for diagnosis history management"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize diagnosis history tools
        
        Args:
            region: AWS region
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        
        # DynamoDB tables
        self.diagnosis_table = self.dynamodb.Table('RISE-DiagnosisHistory')
        self.pest_diagnosis_table = self.dynamodb.Table('RISE-PestDiagnosisHistory')
        
        logger.info(f"Diagnosis history tools initialized in region {region}")
    
    def get_diagnosis_history(self,
                             user_id: str,
                             limit: int = 20,
                             filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get diagnosis history for a user with optional filtering
        
        Args:
            user_id: User ID
            limit: Maximum number of records
            filters: Optional filters
        
        Returns:
            List of diagnosis records
        """
        try:
            # Query disease diagnoses
            disease_response = self.diagnosis_table.query(
                IndexName='UserDiagnosisIndex',
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id},
                ScanIndexForward=False,
                Limit=limit
            )
            
            # Query pest diagnoses
            pest_response = self.pest_diagnosis_table.query(
                IndexName='UserPestDiagnosisIndex',
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id},
                ScanIndexForward=False,
                Limit=limit
            )
            
            # Combine results
            all_diagnoses = []
            
            for diag in disease_response.get('Items', []):
                all_diagnoses.append({
                    **self._convert_decimals(diag),
                    'diagnosis_type': 'disease'
                })
            
            for diag in pest_response.get('Items', []):
                all_diagnoses.append({
                    **self._convert_decimals(diag),
                    'diagnosis_type': 'pest'
                })
            
            # Sort by timestamp
            all_diagnoses.sort(key=lambda x: x.get('created_timestamp', 0), reverse=True)
            
            # Apply filters if provided
            if filters:
                all_diagnoses = self._apply_filters(all_diagnoses, filters)
            
            return all_diagnoses[:limit]
        
        except Exception as e:
            logger.error(f"Error retrieving diagnosis history: {e}", exc_info=True)
            return []
    
    def _convert_decimals(self, obj: Any) -> Any:
        """Convert Decimal types to float for JSON serialization"""
        if isinstance(obj, dict):
            return {k: self._convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals(item) for item in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        return obj
    
    def _apply_filters(self, diagnoses: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to diagnosis list"""
        filtered = diagnoses
        
        if 'severity' in filters and filters['severity']:
            filtered = [d for d in filtered if d.get('severity', '').lower() == filters['severity'].lower()]
        
        if 'crop_type' in filters and filters['crop_type']:
            filtered = [d for d in filtered if filters['crop_type'].lower() in d.get('crop_type', '').lower()]
        
        if 'follow_up_status' in filters and filters['follow_up_status']:
            filtered = [d for d in filtered if d.get('follow_up_status', '').lower() == filters['follow_up_status'].lower()]
        
        if 'diagnosis_type' in filters and filters['diagnosis_type']:
            filtered = [d for d in filtered if d.get('diagnosis_type', '').lower() == filters['diagnosis_type'].lower()]
        
        return filtered
    
    def update_follow_up_status(self,
                                diagnosis_id: str,
                                status: str,
                                notes: Optional[str] = None,
                                diagnosis_type: str = 'disease') -> bool:
        """
        Update follow-up status for a diagnosis
        
        Args:
            diagnosis_id: Diagnosis ID
            status: New status
            notes: Optional notes
            diagnosis_type: Type of diagnosis
        
        Returns:
            Success boolean
        """
        try:
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
            
            logger.info(f"Updated follow-up status for {diagnosis_id}: {status}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating follow-up status: {e}", exc_info=True)
            return False
    
    def get_diagnosis_by_id(self,
                           diagnosis_id: str,
                           diagnosis_type: str = 'disease') -> Optional[Dict[str, Any]]:
        """
        Get a specific diagnosis by ID
        
        Args:
            diagnosis_id: Diagnosis ID
            diagnosis_type: Type of diagnosis
        
        Returns:
            Diagnosis record or None
        """
        try:
            table = self.diagnosis_table if diagnosis_type == 'disease' else self.pest_diagnosis_table
            
            response = table.get_item(Key={'diagnosis_id': diagnosis_id})
            
            if 'Item' in response:
                return self._convert_decimals(response['Item'])
            
            return None
        
        except Exception as e:
            logger.error(f"Error retrieving diagnosis: {e}", exc_info=True)
            return None
    
    def compare_diagnoses(self, diagnosis_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple diagnoses for treatment progress tracking
        
        Args:
            diagnosis_ids: List of diagnosis IDs
        
        Returns:
            Comparison data
        """
        try:
            diagnoses = []
            
            for diag_id in diagnosis_ids:
                # Try disease table first
                diag = self.get_diagnosis_by_id(diag_id, 'disease')
                if diag:
                    diag['diagnosis_type'] = 'disease'
                    diagnoses.append(diag)
                else:
                    # Try pest table
                    diag = self.get_diagnosis_by_id(diag_id, 'pest')
                    if diag:
                        diag['diagnosis_type'] = 'pest'
                        diagnoses.append(diag)
            
            if not diagnoses:
                return {
                    'success': False,
                    'error': 'No diagnoses found'
                }
            
            # Sort by timestamp
            diagnoses.sort(key=lambda x: x.get('created_timestamp', 0))
            
            # Calculate progress
            progress = self._calculate_progress(diagnoses)
            
            return {
                'success': True,
                'diagnoses': diagnoses,
                'progress': progress,
                'count': len(diagnoses)
            }
        
        except Exception as e:
            logger.error(f"Error comparing diagnoses: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_progress(self, diagnoses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate treatment progress metrics"""
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
        
        severity_change = first_severity - latest_severity
        
        # Determine progress status
        if severity_change > 0:
            progress_status = 'improving'
        elif severity_change < 0:
            progress_status = 'worsening'
        else:
            progress_status = 'stable'
        
        # Calculate days elapsed
        days_elapsed = (latest.get('created_timestamp', 0) - first.get('created_timestamp', 0)) / 86400
        
        return {
            'status': progress_status,
            'severity_change': severity_change,
            'first_severity': first.get('severity'),
            'latest_severity': latest.get('severity'),
            'days_elapsed': round(days_elapsed, 1),
            'total_diagnoses': len(diagnoses)
        }
    
    def generate_report(self,
                       diagnosis_id: str,
                       diagnosis_type: str = 'disease') -> Optional[str]:
        """
        Generate text report for a diagnosis
        
        Args:
            diagnosis_id: Diagnosis ID
            diagnosis_type: Type of diagnosis
        
        Returns:
            Report text or None
        """
        try:
            diagnosis = self.get_diagnosis_by_id(diagnosis_id, diagnosis_type)
            
            if not diagnosis:
                return None
            
            # Build report
            report = f"""
RISE - Crop Diagnosis Report
{'=' * 50}

Diagnosis ID: {diagnosis_id}
Type: {diagnosis_type.title()}
Date: {datetime.fromtimestamp(diagnosis.get('created_timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S')}
Crop Type: {diagnosis.get('crop_type', 'Unknown')}

SEVERITY: {diagnosis.get('severity', 'unknown').upper()}
CONFIDENCE: {diagnosis.get('confidence_score', 0)*100:.1f}%
FOLLOW-UP STATUS: {diagnosis.get('follow_up_status', 'pending').upper()}

{'DISEASES DETECTED' if diagnosis_type == 'disease' else 'PESTS IDENTIFIED'}:
{self._format_list(diagnosis.get('diseases', []) or diagnosis.get('pests', []))}

DETAILED ANALYSIS:
{diagnosis.get('diagnosis_result', {}).get('full_analysis', 'No detailed analysis available')}

TREATMENT RECOMMENDATIONS:
{self._format_treatments(diagnosis.get('diagnosis_result', {}).get('treatment_recommendations', []))}

PREVENTIVE MEASURES:
{self._format_list(diagnosis.get('diagnosis_result', {}).get('preventive_measures', []))}

FOLLOW-UP NOTES:
{diagnosis.get('follow_up_notes', 'No follow-up notes')}

{'=' * 50}
Generated by RISE - Rural Innovation and Sustainable Ecosystem
Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            return report
        
        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            return None
    
    def _format_list(self, items: List[str]) -> str:
        """Format list items for report"""
        if not items:
            return "None"
        return '\n'.join(f"  - {item}" for item in items)
    
    def _format_treatments(self, treatments: List[Dict[str, str]]) -> str:
        """Format treatment recommendations for report"""
        if not treatments:
            return "See detailed analysis above"
        
        formatted = []
        for treatment in treatments:
            formatted.append(f"  {treatment.get('type', 'Treatment').title()}:")
            formatted.append(f"    {treatment.get('description', '')}")
        
        return '\n'.join(formatted)
    
    def get_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get diagnosis statistics for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Statistics dict
        """
        try:
            diagnoses = self.get_diagnosis_history(user_id, limit=100)
            
            if not diagnoses:
                return {
                    'total_diagnoses': 0,
                    'severity_distribution': {},
                    'follow_up_status_distribution': {},
                    'diagnosis_type_distribution': {}
                }
            
            severity_counts = {}
            status_counts = {}
            type_counts = {}
            
            for diag in diagnoses:
                severity = diag.get('severity', 'unknown')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                status = diag.get('follow_up_status', 'pending')
                status_counts[status] = status_counts.get(status, 0) + 1
                
                diag_type = diag.get('diagnosis_type', 'unknown')
                type_counts[diag_type] = type_counts.get(diag_type, 0) + 1
            
            return {
                'total_diagnoses': len(diagnoses),
                'severity_distribution': severity_counts,
                'follow_up_status_distribution': status_counts,
                'diagnosis_type_distribution': type_counts
            }
        
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}", exc_info=True)
            return {}


# Factory function
def create_diagnosis_history_tools(region: str = "us-east-1") -> DiagnosisHistoryTools:
    """
    Factory function to create diagnosis history tools instance
    
    Args:
        region: AWS region
    
    Returns:
        DiagnosisHistoryTools instance
    """
    return DiagnosisHistoryTools(region=region)
