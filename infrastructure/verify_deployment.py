#!/usr/bin/env python3
"""
RISE Infrastructure Verification Script
Checks if all AWS resources are properly deployed
"""

import sys
from aws_services import AWSServices, enable_bedrock_models


def print_header(text):
    """Print formatted header"""
    print()
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)
    print()


def print_section(text):
    """Print formatted section"""
    print()
    print(f"📋 {text}")
    print("-" * 70)


def main():
    """Main verification function"""
    print_header("RISE Infrastructure Verification")
    
    # Initialize AWS services
    try:
        services = AWSServices()
        print(f"✅ AWS SDK initialized (Region: {services.region})")
    except Exception as e:
        print(f"❌ Failed to initialize AWS SDK: {e}")
        sys.exit(1)
    
    # Run comprehensive verification
    print_section("Verifying Infrastructure Components")
    results = services.verify_infrastructure()
    
    # Display DynamoDB tables
    print_section("DynamoDB Tables")
    all_tables_ok = True
    for table, exists in results['dynamodb_tables'].items():
        status = "✅" if exists else "❌"
        print(f"  {status} {table}")
        if not exists:
            all_tables_ok = False
    
    if all_tables_ok:
        print("\n  ✅ All DynamoDB tables are ready")
    else:
        print("\n  ⚠️  Some tables are missing. Run 'cdk deploy' to create them.")
    
    # Display S3 buckets
    print_section("S3 Buckets")
    all_buckets_ok = True
    for bucket, exists in results['s3_buckets'].items():
        status = "✅" if exists else "❌"
        print(f"  {status} {bucket}")
        if not exists:
            all_buckets_ok = False
    
    if all_buckets_ok:
        print("\n  ✅ All S3 buckets are ready")
    else:
        print("\n  ⚠️  Some buckets are missing. Run 'cdk deploy' to create them.")
    
    # Display Bedrock access
    print_section("Amazon Bedrock Access")
    bedrock_result = results['bedrock_access']
    
    if bedrock_result.get('success'):
        print(f"  ✅ Bedrock accessible in {bedrock_result['region']}")
        print(f"  📊 Available models: {bedrock_result['total_models']}")
        print()
        
        if bedrock_result['total_models'] > 0:
            print("  Available Models:")
            for model in bedrock_result['available_models']:
                print(f"    • {model['modelName']}")
                print(f"      ID: {model['modelId']}")
                print(f"      Provider: {model['providerName']}")
                print(f"      Input: {', '.join(model['inputModalities'])}")
                print(f"      Output: {', '.join(model['outputModalities'])}")
                print()
        else:
            print("  ⚠️  No Claude 3 Sonnet or Nova models found.")
            print("  Please enable model access in AWS Console.")
            print()
            enable_bedrock_models(services.region)
    else:
        print(f"  ❌ Bedrock not accessible")
        print(f"  Error: {bedrock_result.get('error', 'Unknown error')}")
        print()
        enable_bedrock_models(services.region)
    
    # Overall status
    print_section("Overall Status")
    status = results['overall_status']
    
    if status == 'ready':
        print("  ✅ All infrastructure components are ready!")
        print()
        print("  Next steps:")
        print("    1. Update .env file with resource names")
        print("    2. Deploy Lambda functions for API endpoints")
        print("    3. Test API Gateway endpoints")
        print("    4. Configure OpenTelemetry for observability")
        print("    5. Run application: streamlit run app.py")
        return 0
    
    elif status == 'partial':
        print("  ⚠️  Infrastructure is partially deployed")
        print()
        print("  Action required:")
        print("    1. Review missing components above")
        print("    2. Run 'cd infrastructure && cdk deploy'")
        print("    3. Enable Bedrock model access if needed")
        print("    4. Run this verification again")
        return 1
    
    else:
        print("  ❌ Infrastructure not deployed")
        print()
        print("  Action required:")
        print("    1. cd infrastructure")
        print("    2. ./deploy.sh")
        print("    3. Enable Bedrock model access in AWS Console")
        print("    4. Run this verification again")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
