"""
RISE Custom Metrics Tracking
Implements custom agricultural metrics and business KPIs
"""

import boto3
from datetime import datetime
from typing import Dict, List, Optional, Any
from infrastructure.monitoring_config import (
    MetricNamespace,
    AGRICULTURAL_METRICS,
    get_agricultural_metrics,
)


class CustomMetricsTracker:
    """Tracks custom agricultural and business metrics"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize custom metrics tracker
        
        Args:
            region: AWS region
        """
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
    
    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "None",
        dimensions: Optional[Dict[str, str]] = None,
        namespace: str = MetricNamespace.CUSTOM.value,
        timestamp: Optional[datetime] = None
    ):
        """
        Put a custom metric to CloudWatch
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Metric unit
            dimensions: Metric dimensions
            namespace: CloudWatch namespace
            timestamp: Metric timestamp (defaults to now)
        """
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': timestamp or datetime.utcnow()
        }
        
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': k, 'Value': v} for k, v in dimensions.items()
            ]
        
        self.cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=[metric_data]
        )
    
    # Agricultural Metrics
    
    def track_diagnosis_accuracy(
        self,
        diagnosis_id: str,
        predicted_disease: str,
        actual_disease: Optional[str] = None,
        confidence_score: float = 0.0,
        user_feedback: Optional[str] = None
    ):
        """
        Track crop diagnosis accuracy
        
        Args:
            diagnosis_id: Unique diagnosis ID
            predicted_disease: AI-predicted disease
            actual_disease: Actual disease (from user feedback)
            confidence_score: AI confidence score
            user_feedback: User feedback (helpful/not_helpful)
        """
        # Store diagnosis data for accuracy calculation
        table = self.dynamodb.Table('RISE-DiagnosisHistory')
        
        # Update diagnosis with feedback
        if actual_disease or user_feedback:
            table.update_item(
                Key={'diagnosis_id': diagnosis_id},
                UpdateExpression='SET actual_disease = :actual, user_feedback = :feedback, updated_at = :updated',
                ExpressionAttributeValues={
                    ':actual': actual_disease,
                    ':feedback': user_feedback,
                    ':updated': datetime.utcnow().isoformat()
                }
            )
        
        # Calculate and emit accuracy metric
        if actual_disease:
            is_accurate = (predicted_disease.lower() == actual_disease.lower())
            accuracy = 100.0 if is_accurate else 0.0
            
            self.put_metric(
                metric_name='DiagnosisAccuracy',
                value=accuracy,
                unit='Percent',
                dimensions={'Service': 'CropDiagnosis'},
                namespace=MetricNamespace.AGRICULTURAL.value
            )
        
        # Emit confidence score metric
        self.put_metric(
            metric_name='DiagnosisConfidence',
            value=confidence_score,
            unit='Percent',
            dimensions={'Service': 'CropDiagnosis'},
            namespace=MetricNamespace.AGRICULTURAL.value
        )
    
    def track_pest_identification_accuracy(
        self,
        diagnosis_id: str,
        predicted_pest: str,
        actual_pest: Optional[str] = None,
        confidence_score: float = 0.0
    ):
        """Track pest identification accuracy"""
        if actual_pest:
            is_accurate = (predicted_pest.lower() == actual_pest.lower())
            accuracy = 100.0 if is_accurate else 0.0
            
            self.put_metric(
                metric_name='PestIdentificationAccuracy',
                value=accuracy,
                unit='Percent',
                dimensions={'Service': 'PestIdentification'},
                namespace=MetricNamespace.AGRICULTURAL.value
            )
        
        # Emit confidence score
        self.put_metric(
            metric_name='PestIdentificationConfidence',
            value=confidence_score,
            unit='Percent',
            dimensions={'Service': 'PestIdentification'},
            namespace=MetricNamespace.AGRICULTURAL.value
        )
    
    def track_user_engagement(
        self,
        user_id: str,
        session_duration_seconds: int,
        features_used: List[str],
        language: str
    ):
        """
        Track user engagement metrics
        
        Args:
            user_id: User ID
            session_duration_seconds: Session duration
            features_used: List of features used in session
            language: User's language
        """
        # Session duration
        self.put_metric(
            metric_name='SessionDuration',
            value=session_duration_seconds,
            unit='Seconds',
            dimensions={'Service': 'Platform', 'Language': language},
            namespace=MetricNamespace.AGRICULTURAL.value
        )
        
        # Features used count
        self.put_metric(
            metric_name='FeaturesUsedPerSession',
            value=len(features_used),
            unit='Count',
            dimensions={'Service': 'Platform'},
            namespace=MetricNamespace.AGRICULTURAL.value
        )
        
        # Active user count
        self.put_metric(
            metric_name='ActiveUsers',
            value=1,
            unit='Count',
            dimensions={'Service': 'Platform', 'Language': language},
            namespace=MetricNamespace.AGRICULTURAL.value
        )
    
    def track_yield_improvement(
        self,
        user_id: str,
        crop_type: str,
        baseline_yield: float,
        current_yield: float,
        season: str
    ):
        """
        Track yield improvement for farmers
        
        Args:
            user_id: User ID
            crop_type: Type of crop
            baseline_yield: Baseline yield before using RISE
            current_yield: Current yield after using RISE
            season: Growing season
        """
        improvement_percent = ((current_yield - baseline_yield) / baseline_yield) * 100
        
        self.put_metric(
            metric_name='YieldImprovement',
            value=improvement_percent,
            unit='Percent',
            dimensions={'Service': 'Platform', 'CropType': crop_type, 'Season': season},
            namespace=MetricNamespace.AGRICULTURAL.value
        )
        
        # Store in DynamoDB for historical tracking
        table = self.dynamodb.Table('RISE-FarmData')
        table.put_item(
            Item={
                'farm_id': user_id,
                'timestamp': int(datetime.utcnow().timestamp()),
                'data_type': 'yield_improvement',
                'crop_type': crop_type,
                'baseline_yield': baseline_yield,
                'current_yield': current_yield,
                'improvement_percent': improvement_percent,
                'season': season
            }
        )
    
    def track_cost_savings(
        self,
        user_id: str,
        savings_type: str,
        amount_saved_inr: float,
        category: str
    ):
        """
        Track cost savings achieved by farmers
        
        Args:
            user_id: User ID
            savings_type: Type of savings (fertilizer, pesticide, equipment, bulk_purchase)
            amount_saved_inr: Amount saved in Indian Rupees
            category: Savings category
        """
        self.put_metric(
            metric_name='CostSavings',
            value=amount_saved_inr,
            unit='None',  # Currency amount
            dimensions={'Service': 'Platform', 'SavingsType': savings_type, 'Category': category},
            namespace=MetricNamespace.AGRICULTURAL.value
        )
    
    def track_equipment_utilization(
        self,
        resource_id: str,
        equipment_type: str,
        hours_used: float,
        hours_available: float,
        location: str
    ):
        """
        Track equipment utilization in resource sharing
        
        Args:
            resource_id: Resource ID
            equipment_type: Type of equipment
            hours_used: Hours equipment was used
            hours_available: Total hours equipment was available
            location: Location (state)
        """
        utilization_percent = (hours_used / hours_available) * 100 if hours_available > 0 else 0
        
        self.put_metric(
            metric_name='EquipmentUtilization',
            value=utilization_percent,
            unit='Percent',
            dimensions={
                'Service': 'ResourceSharing',
                'EquipmentType': equipment_type,
                'Location': location
            },
            namespace=MetricNamespace.AGRICULTURAL.value
        )
        
        # Track income generated from sharing
        self.put_metric(
            metric_name='EquipmentSharingIncome',
            value=hours_used,  # Can be multiplied by rate
            unit='Count',
            dimensions={'Service': 'ResourceSharing', 'EquipmentType': equipment_type},
            namespace=MetricNamespace.AGRICULTURAL.value
        )
    
    def track_bulk_purchase_savings(
        self,
        group_id: str,
        product_type: str,
        retail_price: float,
        bulk_price: float,
        quantity: float,
        location: str
    ):
        """
        Track savings from cooperative buying groups
        
        Args:
            group_id: Buying group ID
            product_type: Type of product (seeds, fertilizer, pesticide)
            retail_price: Retail price per unit
            bulk_price: Bulk price per unit
            quantity: Quantity purchased
            location: Location (state)
        """
        savings_percent = ((retail_price - bulk_price) / retail_price) * 100
        total_savings = (retail_price - bulk_price) * quantity
        
        self.put_metric(
            metric_name='BulkPurchaseSavings',
            value=savings_percent,
            unit='Percent',
            dimensions={
                'Service': 'CooperativeBuying',
                'ProductType': product_type,
                'Location': location
            },
            namespace=MetricNamespace.AGRICULTURAL.value
        )
        
        self.put_metric(
            metric_name='BulkPurchaseTotalSavings',
            value=total_savings,
            unit='None',
            dimensions={'Service': 'CooperativeBuying', 'ProductType': product_type},
            namespace=MetricNamespace.AGRICULTURAL.value
        )
    
    def track_scheme_application_success(
        self,
        user_id: str,
        scheme_id: str,
        scheme_type: str,
        application_status: str,
        benefit_amount: float
    ):
        """
        Track government scheme application success
        
        Args:
            user_id: User ID
            scheme_id: Scheme ID
            scheme_type: Type of scheme
            application_status: Status (submitted, approved, rejected)
            benefit_amount: Benefit amount in INR
        """
        if application_status == 'approved':
            success_value = 100.0
            
            self.put_metric(
                metric_name='SchemeApplicationSuccess',
                value=success_value,
                unit='Percent',
                dimensions={'Service': 'GovernmentSchemes', 'SchemeType': scheme_type},
                namespace=MetricNamespace.AGRICULTURAL.value
            )
            
            self.put_metric(
                metric_name='SchemeBenefitAmount',
                value=benefit_amount,
                unit='None',
                dimensions={'Service': 'GovernmentSchemes', 'SchemeType': scheme_type},
                namespace=MetricNamespace.AGRICULTURAL.value
            )
    
    def track_feature_usage(
        self,
        feature_name: str,
        user_id: str,
        success: bool,
        duration_ms: Optional[int] = None
    ):
        """
        Track feature usage and success rate
        
        Args:
            feature_name: Name of the feature
            user_id: User ID
            success: Whether the feature usage was successful
            duration_ms: Duration in milliseconds
        """
        # Feature usage count
        self.put_metric(
            metric_name='FeatureUsage',
            value=1,
            unit='Count',
            dimensions={'Service': 'Platform', 'Feature': feature_name},
            namespace=MetricNamespace.CUSTOM.value
        )
        
        # Feature success rate
        success_value = 100.0 if success else 0.0
        self.put_metric(
            metric_name='FeatureSuccessRate',
            value=success_value,
            unit='Percent',
            dimensions={'Service': 'Platform', 'Feature': feature_name},
            namespace=MetricNamespace.CUSTOM.value
        )
        
        # Feature duration
        if duration_ms:
            self.put_metric(
                metric_name='FeatureDuration',
                value=duration_ms,
                unit='Milliseconds',
                dimensions={'Service': 'Platform', 'Feature': feature_name},
                namespace=MetricNamespace.CUSTOM.value
            )
    
    def track_translation_usage(
        self,
        source_language: str,
        target_language: str,
        character_count: int,
        success: bool
    ):
        """Track translation service usage"""
        self.put_metric(
            metric_name='TranslationUsage',
            value=character_count,
            unit='Count',
            dimensions={
                'Service': 'Translation',
                'SourceLanguage': source_language,
                'TargetLanguage': target_language
            },
            namespace=MetricNamespace.CUSTOM.value
        )
        
        if success:
            self.put_metric(
                metric_name='TranslationSuccess',
                value=1,
                unit='Count',
                dimensions={'Service': 'Translation'},
                namespace=MetricNamespace.CUSTOM.value
            )
    
    def track_voice_usage(
        self,
        service_type: str,  # transcribe or synthesize
        language: str,
        duration_seconds: Optional[float] = None,
        character_count: Optional[int] = None,
        success: bool = True
    ):
        """Track voice service usage (Transcribe/Polly)"""
        metric_name = f"Voice{service_type.capitalize()}Usage"
        
        if duration_seconds:
            self.put_metric(
                metric_name=metric_name,
                value=duration_seconds,
                unit='Seconds',
                dimensions={'Service': 'Voice', 'Language': language},
                namespace=MetricNamespace.CUSTOM.value
            )
        
        if character_count:
            self.put_metric(
                metric_name=metric_name,
                value=character_count,
                unit='Count',
                dimensions={'Service': 'Voice', 'Language': language},
                namespace=MetricNamespace.CUSTOM.value
            )
        
        if success:
            self.put_metric(
                metric_name=f"Voice{service_type.capitalize()}Success",
                value=1,
                unit='Count',
                dimensions={'Service': 'Voice', 'Language': language},
                namespace=MetricNamespace.CUSTOM.value
            )
    
    def get_metric_statistics(
        self,
        metric_name: str,
        namespace: str,
        start_time: datetime,
        end_time: datetime,
        period: int = 300,
        statistics: List[str] = ['Average', 'Sum', 'Maximum', 'Minimum'],
        dimensions: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Get statistics for a metric
        
        Args:
            metric_name: Metric name
            namespace: CloudWatch namespace
            start_time: Start time
            end_time: End time
            period: Period in seconds
            statistics: List of statistics to retrieve
            dimensions: Metric dimensions
            
        Returns:
            Metric statistics
        """
        params = {
            'Namespace': namespace,
            'MetricName': metric_name,
            'StartTime': start_time,
            'EndTime': end_time,
            'Period': period,
            'Statistics': statistics
        }
        
        if dimensions:
            params['Dimensions'] = dimensions
        
        response = self.cloudwatch.get_metric_statistics(**params)
        return response
