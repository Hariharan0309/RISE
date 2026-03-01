# RISE Infrastructure Deployment Guide

Complete guide for deploying RISE AWS infrastructure using CDK.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Amazon Bedrock Configuration](#amazon-bedrock-configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- **AWS CLI** (v2.x or higher)
  ```bash
  aws --version
  ```

- **AWS CDK CLI** (v2.100.0 or higher)
  ```bash
  npm install -g aws-cdk
  cdk --version
  ```

- **Python** (3.9 or higher)
  ```bash
  python3 --version
  ```

- **Node.js** (14.x or higher, for CDK CLI)
  ```bash
  node --version
  ```

### AWS Account Setup

1. **AWS Account**: Active AWS account with appropriate permissions
2. **IAM Permissions**: User/role with permissions for:
   - CloudFormation
   - DynamoDB
   - S3
   - CloudFront
   - API Gateway
   - IAM
   - Lambda
   - Bedrock

3. **AWS Credentials**: Configure AWS CLI
   ```bash
   aws configure
   ```

## Quick Start

For rapid deployment, use the automated script:

```bash
cd infrastructure
./deploy.sh
```

This script will:
1. Create virtual environment
2. Install dependencies
3. Bootstrap CDK (if needed)
4. Synthesize CloudFormation template
5. Deploy infrastructure

## Detailed Setup

### Step 1: Install Dependencies

```bash
cd infrastructure

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate  # Windows

# Install CDK dependencies
pip install -r requirements.txt
```

### Step 2: Bootstrap CDK

First-time setup for your AWS account/region:

```bash
# Get your AWS account ID
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=us-east-1  # Change as needed

# Bootstrap CDK
cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION
```

### Step 3: Review Infrastructure

Preview what will be created:

```bash
# Synthesize CloudFormation template
cdk synth

# View differences (if updating existing stack)
cdk diff
```

### Step 4: Deploy Infrastructure

```bash
# Deploy with confirmation prompts
cdk deploy

# Deploy without prompts (for automation)
cdk deploy --require-approval never
```

### Step 5: Note Outputs

After deployment, CDK will output important values:
- API Gateway endpoint URLs
- S3 bucket names
- CloudFront distribution domain
- DynamoDB table names

Save these for application configuration.

## Amazon Bedrock Configuration

### Enable Model Access

Amazon Bedrock requires explicit model access enablement:

1. **Open AWS Console**
   - Navigate to Amazon Bedrock service
   - Select your deployment region (e.g., us-east-1)

2. **Access Model Access Page**
   - Click "Model access" in left sidebar
   - Click "Manage model access" button

3. **Enable Required Models**
   - ✅ **Anthropic - Claude 3 Sonnet** (anthropic.claude-3-sonnet-20240229-v1:0)
   - ✅ **Amazon - Nova** (all variants)
     - Amazon Nova Micro
     - Amazon Nova Lite
     - Amazon Nova Pro

4. **Save and Wait**
   - Click "Save changes"
   - Wait 2-5 minutes for access to be granted
   - Status will change from "In progress" to "Access granted"

### Verify Bedrock Access

```bash
# Run verification script
python aws_services.py
```

Expected output:
```
Amazon Bedrock Access:
  ✅ Bedrock accessible in us-east-1
  📊 Available models: 2
     - Claude 3 Sonnet (anthropic.claude-3-sonnet-20240229-v1:0)
     - Amazon Nova Pro (amazon.nova-pro-v1:0)
```

### Programmatic Verification

```python
from aws_services import AWSServices

services = AWSServices(region='us-east-1')
result = services.verify_bedrock_access()

if result['success']:
    print(f"✅ Bedrock ready with {result['total_models']} models")
else:
    print(f"❌ Error: {result['error']}")
```

## Verification

### Verify All Infrastructure

```bash
# Run comprehensive verification
python aws_services.py
```

This checks:
- ✅ All 6 DynamoDB tables created
- ✅ S3 bucket created with lifecycle policies
- ✅ Amazon Bedrock model access
- ✅ Overall infrastructure status

### Manual Verification

#### DynamoDB Tables

```bash
# List all RISE tables
aws dynamodb list-tables --query "TableNames[?starts_with(@, 'RISE-')]"
```

Expected tables:
- RISE-UserProfiles
- RISE-FarmData
- RISE-DiagnosisHistory
- RISE-ResourceSharing
- RISE-BuyingGroups
- RISE-ResourceBookings

#### S3 Bucket

```bash
# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Check bucket exists
aws s3 ls s3://rise-application-data-$ACCOUNT_ID
```

#### API Gateway

```bash
# List REST APIs
aws apigateway get-rest-apis --query "items[?name=='RISE-API']"

# List WebSocket APIs
aws apigatewayv2 get-apis --query "Items[?Name=='RISE-WebSocket-API']"
```

#### CloudFront Distribution

```bash
# List distributions
aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='RISE CDN Distribution']"
```

## OpenTelemetry Setup

### Install OpenTelemetry Collector

```bash
# Download and install OTEL Collector
# For Linux
wget https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.91.0/otelcol_0.91.0_linux_amd64.tar.gz
tar -xvf otelcol_0.91.0_linux_amd64.tar.gz

# For Mac
brew install opentelemetry-collector
```

### Configure OTEL Collector

```bash
# Use provided configuration
cp otel-config.yaml /etc/otelcol/config.yaml

# Start collector
otelcol --config=/etc/otelcol/config.yaml
```

### Verify OTEL

```bash
# Check health endpoint
curl http://localhost:13133/

# Check metrics endpoint
curl http://localhost:8888/metrics
```

## Update Application Configuration

After successful deployment, update your `.env` file:

```bash
# Get outputs from CDK
cdk deploy --outputs-file outputs.json

# Update .env with actual values
cat outputs.json
```

Update `.env`:
```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# DynamoDB Tables (already configured)
DYNAMODB_USER_PROFILES_TABLE=RISE-UserProfiles
DYNAMODB_FARM_DATA_TABLE=RISE-FarmData
DYNAMODB_DIAGNOSIS_HISTORY_TABLE=RISE-DiagnosisHistory
DYNAMODB_RESOURCE_SHARING_TABLE=RISE-ResourceSharing
DYNAMODB_BUYING_GROUPS_TABLE=RISE-BuyingGroups
DYNAMODB_RESOURCE_BOOKINGS_TABLE=RISE-ResourceBookings

# S3 Bucket
S3_BUCKET_NAME=rise-application-data-123456789012

# API Gateway
API_GATEWAY_REST_URL=https://abc123.execute-api.us-east-1.amazonaws.com/v1
API_GATEWAY_WEBSOCKET_URL=wss://xyz789.execute-api.us-east-1.amazonaws.com/production

# CloudFront
CLOUDFRONT_DOMAIN=d1234567890.cloudfront.net

# Amazon Bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1

# OpenTelemetry
OTEL_SERVICE_NAME=rise-farming-assistant
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

## Troubleshooting

### Common Issues

#### 1. CDK Bootstrap Error

**Error**: `This stack uses assets, so the toolkit stack must be deployed`

**Solution**:
```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

#### 2. Insufficient Permissions

**Error**: `User is not authorized to perform: cloudformation:CreateStack`

**Solution**: Ensure IAM user/role has required permissions. Attach policies:
- `AdministratorAccess` (for testing)
- Or custom policy with specific permissions

#### 3. Bedrock Model Access Denied

**Error**: `AccessDeniedException: Could not access model`

**Solution**: Enable model access in AWS Console (see [Amazon Bedrock Configuration](#amazon-bedrock-configuration))

#### 4. S3 Bucket Name Conflict

**Error**: `Bucket name already exists`

**Solution**: S3 bucket names are globally unique. The CDK stack uses account ID suffix to avoid conflicts. If still failing, check for existing bucket.

#### 5. DynamoDB Table Already Exists

**Error**: `Table already exists`

**Solution**: 
```bash
# Delete existing tables (WARNING: deletes data)
aws dynamodb delete-table --table-name RISE-UserProfiles

# Or update CDK stack to use existing tables
```

#### 6. CloudFormation Stack Rollback

**Error**: Stack creation failed and rolled back

**Solution**:
```bash
# Check CloudFormation events for specific error
aws cloudformation describe-stack-events --stack-name RiseStack

# Delete failed stack and retry
cdk destroy
cdk deploy
```

### Debugging Tips

1. **Check CloudFormation Console**
   - View stack events for detailed error messages
   - Check resource creation status

2. **Enable CDK Debug Mode**
   ```bash
   cdk deploy --verbose
   ```

3. **Validate Template**
   ```bash
   cdk synth > template.yaml
   aws cloudformation validate-template --template-body file://template.yaml
   ```

4. **Check Service Quotas**
   ```bash
   # Check DynamoDB limits
   aws service-quotas get-service-quota \
     --service-code dynamodb \
     --quota-code L-F98FE922
   ```

## Cost Estimation

Estimated monthly costs for RISE infrastructure (light usage):

| Service | Usage | Estimated Cost |
|---------|-------|----------------|
| DynamoDB | 1M reads, 500K writes | $1.25 |
| S3 | 10GB storage, 100K requests | $0.50 |
| CloudFront | 10GB transfer | $1.00 |
| API Gateway | 1M requests | $3.50 |
| Lambda | 1M invocations, 512MB | $2.00 |
| Bedrock | 1M tokens | $3.00 |
| **Total** | | **~$11.25/month** |

**Note**: Costs scale with usage. Monitor with AWS Cost Explorer.

## Cleanup

To delete all infrastructure:

```bash
# Delete CDK stack
cdk destroy

# Confirm deletion
# Type 'y' when prompted
```

**⚠️ WARNING**: This permanently deletes:
- All DynamoDB tables and data
- S3 bucket and contents
- CloudFront distribution
- API Gateway endpoints
- All configurations

**Backup data before destroying!**

## Next Steps

After successful deployment:

1. ✅ Verify all resources created
2. ✅ Enable Bedrock model access
3. ✅ Update `.env` configuration
4. ✅ Test API endpoints
5. ✅ Deploy Lambda functions
6. ✅ Configure OpenTelemetry
7. ✅ Run application tests

Proceed to [Phase 3: Create base orchestrator agent](../tasks.md#phase-1-foundation--strands-agents-setup)

## Support

For issues:
- Check [Troubleshooting](#troubleshooting) section
- Review [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- Check [RISE GitHub Issues](https://github.com/your-repo/issues)
