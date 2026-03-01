"""
AWS Services Initialization Module
Provides helper functions to initialize and configure AWS services for RISE
"""

import boto3
import os
from typing import Dict, Any
from botocore.config import Config


class AWSServices:
    """AWS Services manager for RISE application"""
    
    def __init__(self, region: str = None):
        """
        Initialize AWS services
        
        Args:
            region: AWS region (defaults to environment variable or us-east-1)
        """
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.config = Config(
            region_name=self.region,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            }
        )
    
    def get_dynamodb_client(self):
        """Get DynamoDB client"""
        return boto3.client('dynamodb', config=self.config)
    
    def get_dynamodb_resource(self):
        """Get DynamoDB resource"""
        return boto3.resource('dynamodb', config=self.config)
    
    def get_s3_client(self):
        """Get S3 client"""
        return boto3.client('s3', config=self.config)
    
    def get_bedrock_client(self):
        """Get Amazon Bedrock runtime client"""
        return boto3.client('bedrock-runtime', config=self.config)
    
    def get_translate_client(self):
        """Get Amazon Translate client"""
        return boto3.client('translate', config=self.config)
    
    def get_transcribe_client(self):
        """Get Amazon Transcribe client"""
        return boto3.client('transcribe', config=self.config)
    
    def get_polly_client(self):
        """Get Amazon Polly client"""
        return boto3.client('polly', config=self.config)
    
    def get_comprehend_client(self):
        """Get Amazon Comprehend client"""
        return boto3.client('comprehend', config=self.config)
    
    def get_cloudwatch_client(self):
        """Get CloudWatch client"""
        return boto3.client('cloudwatch', config=self.config)
    
    def get_sns_client(self):
        """Get SNS client"""
        return boto3.client('sns', config=self.config)
    
    def get_eventbridge_client(self):
        """Get EventBridge client"""
        return boto3.client('events', config=self.config)
    
    def verify_bedrock_access(self) -> Dict[str, Any]:
        """
        Verify Amazon Bedrock model access
        
        Returns:
            Dictionary with available models and access status
        """
        try:
            bedrock = boto3.client('bedrock', config=self.config)
            response = bedrock.list_foundation_models()
            
            # Filter for Claude 3 Sonnet and Amazon Nova
            available_models = []
            for model in response.get('modelSummaries', []):
                model_id = model.get('modelId', '')
                if 'claude-3-sonnet' in model_id or 'nova' in model_id.lower():
                    available_models.append({
                        'modelId': model_id,
                        'modelName': model.get('modelName'),
                        'providerName': model.get('providerName'),
                        'inputModalities': model.get('inputModalities', []),
                        'outputModalities': model.get('outputModalities', [])
                    })
            
            return {
                'success': True,
                'region': self.region,
                'available_models': available_models,
                'total_models': len(available_models)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to access Amazon Bedrock. Ensure model access is enabled in AWS Console.'
            }
    
    def verify_table_exists(self, table_name: str) -> bool:
        """
        Verify if a DynamoDB table exists
        
        Args:
            table_name: Name of the DynamoDB table
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            dynamodb = self.get_dynamodb_client()
            dynamodb.describe_table(TableName=table_name)
            return True
        except dynamodb.exceptions.ResourceNotFoundException:
            return False
        except Exception as e:
            print(f"Error checking table {table_name}: {e}")
            return False
    
    def verify_bucket_exists(self, bucket_name: str) -> bool:
        """
        Verify if an S3 bucket exists
        
        Args:
            bucket_name: Name of the S3 bucket
            
        Returns:
            True if bucket exists, False otherwise
        """
        try:
            s3 = self.get_s3_client()
            s3.head_bucket(Bucket=bucket_name)
            return True
        except Exception as e:
            print(f"Error checking bucket {bucket_name}: {e}")
            return False
    
    def verify_infrastructure(self) -> Dict[str, Any]:
        """
        Verify all RISE infrastructure components
        
        Returns:
            Dictionary with verification results
        """
        results = {
            'dynamodb_tables': {},
            's3_buckets': {},
            'bedrock_access': {},
            'overall_status': 'unknown'
        }
        
        # Check DynamoDB tables
        tables = [
            'RISE-UserProfiles',
            'RISE-FarmData',
            'RISE-DiagnosisHistory',
            'RISE-ResourceSharing',
            'RISE-BuyingGroups',
            'RISE-ResourceBookings'
        ]
        
        for table in tables:
            results['dynamodb_tables'][table] = self.verify_table_exists(table)
        
        # Check S3 bucket
        account_id = boto3.client('sts').get_caller_identity()['Account']
        bucket_name = f"rise-application-data-{account_id}"
        results['s3_buckets'][bucket_name] = self.verify_bucket_exists(bucket_name)
        
        # Check Bedrock access
        results['bedrock_access'] = self.verify_bedrock_access()
        
        # Determine overall status
        all_tables_exist = all(results['dynamodb_tables'].values())
        all_buckets_exist = all(results['s3_buckets'].values())
        bedrock_accessible = results['bedrock_access'].get('success', False)
        
        if all_tables_exist and all_buckets_exist and bedrock_accessible:
            results['overall_status'] = 'ready'
        elif any([all_tables_exist, all_buckets_exist, bedrock_accessible]):
            results['overall_status'] = 'partial'
        else:
            results['overall_status'] = 'not_deployed'
        
        return results


def enable_bedrock_models(region: str = None):
    """
    Helper function to guide users through enabling Bedrock models
    
    Args:
        region: AWS region
    """
    region = region or os.getenv("AWS_REGION", "us-east-1")
    
    print("=" * 60)
    print("Amazon Bedrock Model Access Setup")
    print("=" * 60)
    print()
    print("To enable Amazon Bedrock models:")
    print()
    print("1. Open AWS Console and navigate to Amazon Bedrock")
    print(f"   https://{region}.console.aws.amazon.com/bedrock/home?region={region}#/modelaccess")
    print()
    print("2. Click 'Model access' in the left sidebar")
    print()
    print("3. Click 'Manage model access' button")
    print()
    print("4. Enable the following models:")
    print("   ✓ Anthropic - Claude 3 Sonnet")
    print("   ✓ Amazon - Nova (all variants)")
    print()
    print("5. Click 'Save changes' and wait for access to be granted")
    print()
    print("6. Run this verification again to confirm access")
    print()
    print("=" * 60)


if __name__ == "__main__":
    # Verify infrastructure when run directly
    print("Verifying RISE AWS Infrastructure...")
    print()
    
    services = AWSServices()
    results = services.verify_infrastructure()
    
    print("DynamoDB Tables:")
    for table, exists in results['dynamodb_tables'].items():
        status = "✅" if exists else "❌"
        print(f"  {status} {table}")
    
    print()
    print("S3 Buckets:")
    for bucket, exists in results['s3_buckets'].items():
        status = "✅" if exists else "❌"
        print(f"  {status} {bucket}")
    
    print()
    print("Amazon Bedrock Access:")
    bedrock_result = results['bedrock_access']
    if bedrock_result.get('success'):
        print(f"  ✅ Bedrock accessible in {bedrock_result['region']}")
        print(f"  📊 Available models: {bedrock_result['total_models']}")
        for model in bedrock_result['available_models']:
            print(f"     - {model['modelName']} ({model['modelId']})")
    else:
        print(f"  ❌ Bedrock not accessible: {bedrock_result.get('error', 'Unknown error')}")
        print()
        enable_bedrock_models()
    
    print()
    print(f"Overall Status: {results['overall_status'].upper()}")
