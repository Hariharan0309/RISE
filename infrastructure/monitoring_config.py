"""
RISE Monitoring Configuration
Centralized monitoring configuration for all Lambda functions and services
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class MetricNamespace(str, Enum):
    """CloudWatch metric namespaces"""
    LAMBDA = "AWS/Lambda"
    API_GATEWAY = "AWS/ApiGateway"
    DYNAMODB = "AWS/DynamoDB"
    CUSTOM = "RISE/Application"
    AGRICULTURAL = "RISE/Agricultural"
    COST = "RISE/Cost"


class AlarmSeverity(str, Enum):
    """Alarm severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class LambdaMonitoringConfig:
    """Configuration for Lambda function monitoring"""
    function_name: str
    error_threshold: float = 5.0  # Error rate percentage
    duration_threshold_ms: int = 10000  # 10 seconds
    throttle_threshold: int = 10  # Number of throttles
    concurrent_executions_threshold: int = 100
    enable_detailed_metrics: bool = True
    alarm_severity: AlarmSeverity = AlarmSeverity.HIGH


@dataclass
class CustomMetricConfig:
    """Configuration for custom metrics"""
    metric_name: str
    namespace: MetricNamespace
    unit: str
    dimensions: Dict[str, str]
    description: str


# Lambda function monitoring configurations
LAMBDA_FUNCTIONS = {
    # Voice processing
    "audio_upload": LambdaMonitoringConfig(
        function_name="rise-audio-upload",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.HIGH
    ),
    
    # Disease and pest identification
    "image_analysis": LambdaMonitoringConfig(
        function_name="rise-image-analysis",
        duration_threshold_ms=15000,  # Image analysis takes longer
        alarm_severity=AlarmSeverity.CRITICAL
    ),
    "pest_analysis": LambdaMonitoringConfig(
        function_name="rise-pest-analysis",
        duration_threshold_ms=15000,
        alarm_severity=AlarmSeverity.CRITICAL
    ),
    "image_quality": LambdaMonitoringConfig(
        function_name="rise-image-quality",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.MEDIUM
    ),
    "diagnosis_history": LambdaMonitoringConfig(
        function_name="rise-diagnosis-history",
        duration_threshold_ms=3000,
        alarm_severity=AlarmSeverity.MEDIUM
    ),
    
    # Soil and crop analysis
    "soil_analysis": LambdaMonitoringConfig(
        function_name="rise-soil-analysis",
        duration_threshold_ms=10000,
        alarm_severity=AlarmSeverity.HIGH
    ),
    "fertilizer_recommendation": LambdaMonitoringConfig(
        function_name="rise-fertilizer-recommendation",
        duration_threshold_ms=8000,
        alarm_severity=AlarmSeverity.HIGH
    ),
    "crop_selection": LambdaMonitoringConfig(
        function_name="rise-crop-selection",
        duration_threshold_ms=8000,
        alarm_severity=AlarmSeverity.HIGH
    ),
    
    # Weather integration
    "weather": LambdaMonitoringConfig(
        function_name="rise-weather",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.HIGH
    ),
    "weather_alert": LambdaMonitoringConfig(
        function_name="rise-weather-alert",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.HIGH
    ),
    "climate_adaptive": LambdaMonitoringConfig(
        function_name="rise-climate-adaptive",
        duration_threshold_ms=8000,
        alarm_severity=AlarmSeverity.MEDIUM
    ),
    
    # Market intelligence
    "market_price": LambdaMonitoringConfig(
        function_name="rise-market-price",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.HIGH
    ),
    "selling_time": LambdaMonitoringConfig(
        function_name="rise-selling-time",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.MEDIUM
    ),
    "buyer_connection": LambdaMonitoringConfig(
        function_name="rise-buyer-connection",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.HIGH
    ),
    
    # Government schemes
    "government_scheme": LambdaMonitoringConfig(
        function_name="rise-government-scheme",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.HIGH
    ),
    "scheme_discovery": LambdaMonitoringConfig(
        function_name="rise-scheme-discovery",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.HIGH
    ),
    "scheme_application": LambdaMonitoringConfig(
        function_name="rise-scheme-application",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.HIGH
    ),
    
    # Financial planning
    "profitability_calculator": LambdaMonitoringConfig(
        function_name="rise-profitability-calculator",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.MEDIUM
    ),
    "loan_credit": LambdaMonitoringConfig(
        function_name="rise-loan-credit",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.HIGH
    ),
    
    # Community features
    "forum": LambdaMonitoringConfig(
        function_name="rise-forum",
        duration_threshold_ms=3000,
        alarm_severity=AlarmSeverity.MEDIUM
    ),
    "best_practice": LambdaMonitoringConfig(
        function_name="rise-best-practice",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.MEDIUM
    ),
    
    # Resource sharing
    "equipment_sharing": LambdaMonitoringConfig(
        function_name="rise-equipment-sharing",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.HIGH
    ),
    "buying_group": LambdaMonitoringConfig(
        function_name="rise-buying-group",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.HIGH
    ),
    "supplier_negotiation": LambdaMonitoringConfig(
        function_name="rise-supplier-negotiation",
        duration_threshold_ms=10000,
        alarm_severity=AlarmSeverity.MEDIUM
    ),
    "resource_alert": LambdaMonitoringConfig(
        function_name="rise-resource-alert",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.MEDIUM
    ),
    "availability_alert": LambdaMonitoringConfig(
        function_name="rise-availability-alert",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.MEDIUM
    ),
    "local_economy": LambdaMonitoringConfig(
        function_name="rise-local-economy",
        duration_threshold_ms=5000,
        alarm_severity=AlarmSeverity.LOW
    ),
}


# Custom agricultural metrics
AGRICULTURAL_METRICS = [
    CustomMetricConfig(
        metric_name="DiagnosisAccuracy",
        namespace=MetricNamespace.AGRICULTURAL,
        unit="Percent",
        dimensions={"Service": "CropDiagnosis"},
        description="Accuracy rate of crop disease diagnosis"
    ),
    CustomMetricConfig(
        metric_name="PestIdentificationAccuracy",
        namespace=MetricNamespace.AGRICULTURAL,
        unit="Percent",
        dimensions={"Service": "PestIdentification"},
        description="Accuracy rate of pest identification"
    ),
    CustomMetricConfig(
        metric_name="UserEngagement",
        namespace=MetricNamespace.AGRICULTURAL,
        unit="Count",
        dimensions={"Service": "Platform"},
        description="Number of active user sessions"
    ),
    CustomMetricConfig(
        metric_name="YieldImprovement",
        namespace=MetricNamespace.AGRICULTURAL,
        unit="Percent",
        dimensions={"Service": "Platform"},
        description="Average yield improvement for active users"
    ),
    CustomMetricConfig(
        metric_name="CostSavings",
        namespace=MetricNamespace.AGRICULTURAL,
        unit="None",
        dimensions={"Service": "Platform"},
        description="Total cost savings achieved by farmers (in rupees)"
    ),
    CustomMetricConfig(
        metric_name="EquipmentUtilization",
        namespace=MetricNamespace.AGRICULTURAL,
        unit="Percent",
        dimensions={"Service": "ResourceSharing"},
        description="Equipment utilization rate in resource sharing"
    ),
    CustomMetricConfig(
        metric_name="BulkPurchaseSavings",
        namespace=MetricNamespace.AGRICULTURAL,
        unit="Percent",
        dimensions={"Service": "CooperativeBuying"},
        description="Average savings from cooperative buying groups"
    ),
    CustomMetricConfig(
        metric_name="SchemeApplicationSuccess",
        namespace=MetricNamespace.AGRICULTURAL,
        unit="Percent",
        dimensions={"Service": "GovernmentSchemes"},
        description="Success rate of government scheme applications"
    ),
]


# API Gateway monitoring configuration
API_GATEWAY_CONFIG = {
    "api_name": "RISE-API",
    "stage": "v1",
    "latency_threshold_ms": 3000,  # 3 seconds for voice queries
    "error_rate_threshold": 5.0,  # 5% error rate
    "throttle_threshold": 100,
}


# DynamoDB monitoring configuration
DYNAMODB_TABLES = {
    "RISE-UserProfiles": {
        "read_capacity_threshold": 80,  # 80% of provisioned capacity
        "write_capacity_threshold": 80,
        "throttle_threshold": 10,
    },
    "RISE-FarmData": {
        "read_capacity_threshold": 80,
        "write_capacity_threshold": 80,
        "throttle_threshold": 10,
    },
    "RISE-DiagnosisHistory": {
        "read_capacity_threshold": 80,
        "write_capacity_threshold": 80,
        "throttle_threshold": 10,
    },
    "RISE-ResourceSharing": {
        "read_capacity_threshold": 80,
        "write_capacity_threshold": 80,
        "throttle_threshold": 10,
    },
    "RISE-BuyingGroups": {
        "read_capacity_threshold": 80,
        "write_capacity_threshold": 80,
        "throttle_threshold": 10,
    },
    "RISE-ResourceBookings": {
        "read_capacity_threshold": 80,
        "write_capacity_threshold": 80,
        "throttle_threshold": 10,
    },
}


# Cost monitoring configuration
COST_MONITORING_CONFIG = {
    "monthly_budget_usd": 1000,
    "alert_thresholds": [50, 75, 90, 100],  # Percentage of budget
    "services_to_monitor": [
        "Amazon Bedrock",
        "AWS Lambda",
        "Amazon DynamoDB",
        "Amazon S3",
        "Amazon CloudFront",
        "Amazon Translate",
        "Amazon Transcribe",
        "Amazon Polly",
    ],
}


# Error tracking configuration
ERROR_TRACKING_CONFIG = {
    "log_retention_days": 30,
    "error_patterns": [
        "ERROR",
        "Exception",
        "Traceback",
        "Failed",
        "Timeout",
        "ThrottlingException",
        "ServiceException",
    ],
    "critical_errors": [
        "BedrockException",
        "DynamoDBException",
        "S3Exception",
        "AuthenticationError",
    ],
}


def get_lambda_config(function_key: str) -> Optional[LambdaMonitoringConfig]:
    """Get monitoring configuration for a Lambda function"""
    return LAMBDA_FUNCTIONS.get(function_key)


def get_all_lambda_functions() -> List[str]:
    """Get list of all Lambda function names"""
    return [config.function_name for config in LAMBDA_FUNCTIONS.values()]


def get_critical_functions() -> List[str]:
    """Get list of critical Lambda functions"""
    return [
        config.function_name
        for config in LAMBDA_FUNCTIONS.values()
        if config.alarm_severity == AlarmSeverity.CRITICAL
    ]


def get_agricultural_metrics() -> List[CustomMetricConfig]:
    """Get list of custom agricultural metrics"""
    return AGRICULTURAL_METRICS
