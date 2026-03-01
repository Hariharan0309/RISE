"""
RISE Configuration Module
Centralized configuration management
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # AWS Configuration
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    # Amazon Bedrock Configuration
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
    BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")
    
    # Application Configuration
    APP_NAME = os.getenv("APP_NAME", "RISE")
    APP_ENV = os.getenv("APP_ENV", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # Streamlit Configuration
    STREAMLIT_SERVER_PORT = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    STREAMLIT_SERVER_ADDRESS = os.getenv("STREAMLIT_SERVER_ADDRESS", "localhost")
    
    # DynamoDB Tables
    DYNAMODB_USER_PROFILES_TABLE = os.getenv("DYNAMODB_USER_PROFILES_TABLE", "RISE-UserProfiles")
    DYNAMODB_FARM_DATA_TABLE = os.getenv("DYNAMODB_FARM_DATA_TABLE", "RISE-FarmData")
    DYNAMODB_DIAGNOSIS_HISTORY_TABLE = os.getenv("DYNAMODB_DIAGNOSIS_HISTORY_TABLE", "RISE-DiagnosisHistory")
    DYNAMODB_RESOURCE_SHARING_TABLE = os.getenv("DYNAMODB_RESOURCE_SHARING_TABLE", "RISE-ResourceSharing")
    DYNAMODB_BUYING_GROUPS_TABLE = os.getenv("DYNAMODB_BUYING_GROUPS_TABLE", "RISE-BuyingGroups")
    DYNAMODB_RESOURCE_BOOKINGS_TABLE = os.getenv("DYNAMODB_RESOURCE_BOOKINGS_TABLE", "RISE-ResourceBookings")
    
    # S3 Buckets
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "rise-application-data")
    
    # OpenTelemetry Configuration
    OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "rise-farming-assistant")
    OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    
    # Supported Languages
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "kn": "Kannada",
        "bn": "Bengali",
        "gu": "Gujarati",
        "mr": "Marathi",
        "pa": "Punjabi"
    }
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = [
            "AWS_REGION",
            "BEDROCK_MODEL_ID"
        ]
        
        missing = []
        for var in required_vars:
            if not getattr(cls, var):
                missing.append(var)
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True

# Validate configuration on import
if Config.APP_ENV == "production":
    Config.validate()
