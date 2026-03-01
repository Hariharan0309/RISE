# RISE Infrastructure

This directory contains AWS CDK infrastructure code for the RISE (Rural Innovation and Sustainable Ecosystem) platform.

## Overview

The infrastructure is defined using AWS CDK (Cloud Development Kit) in Python and includes:

- **DynamoDB Tables**: 6 tables for user profiles, farm data, diagnosis history, resource sharing, buying groups, and bookings
- **S3 Buckets**: Storage for images, audio, documents, and static content with lifecycle policies
- **CloudFront Distribution**: CDN for global content delivery with optimized caching
- **API Gateway**: REST API and WebSocket API for real-time features
- **IAM Roles**: Permissions for Lambda functions to access Bedrock and other AWS services

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. AWS CDK CLI installed (`npm install -g aws-cdk`)
3. Python 3.9 or higher
4. Virtual environment activated

## Installation

```bash
cd infrastructure
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Deployment

### Bootstrap CDK (first time only)

```bash
cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```

### Deploy the stack

```bash
# Synthesize CloudFormation template
cdk synth

# Deploy to AWS
cdk deploy

# Deploy with auto-approval (for CI/CD)
cdk deploy --require-approval never
```

## Infrastructure Components

### DynamoDB Tables

1. **RISE-UserProfiles**
   - Partition Key: `user_id`
   - GSIs: PhoneIndex, LocationIndex
   - Stores farmer profiles, preferences, and farm details

2. **RISE-FarmData**
   - Partition Key: `farm_id`
   - Sort Key: `timestamp`
   - Stores time-series farm data, crop data, soil analysis

3. **RISE-DiagnosisHistory**
   - Partition Key: `diagnosis_id`
   - Stores crop disease diagnosis results and treatment recommendations

4. **RISE-ResourceSharing**
   - Partition Key: `resource_id`
   - Sort Key: `availability_date`
   - GSIs: LocationResourceIndex, OwnerResourceIndex
   - Stores equipment listings for sharing

5. **RISE-BuyingGroups**
   - Partition Key: `group_id`
   - GSIs: LocationGroupIndex, StatusGroupIndex
   - Stores cooperative buying group information

6. **RISE-ResourceBookings**
   - Partition Key: `booking_id`
   - GSIs: RenterBookingIndex, OwnerBookingIndex, ResourceBookingIndex
   - Stores equipment booking transactions

### S3 Bucket Structure

```
rise-application-data-{account}/
├── images/
│   ├── crop-photos/        # Lifecycle: IA after 90 days, Glacier after 1 year
│   ├── soil-samples/
│   └── thumbnails/         # Lifecycle: IA after 90 days
├── audio/
│   ├── voice-queries/      # Lifecycle: Delete after 30 days
│   └── responses/
├── documents/
│   ├── government-schemes/
│   └── agricultural-guides/
└── static-content/         # CloudFront cache: 1 year TTL
    ├── crop-database/
    └── educational-materials/
```

### API Gateway Endpoints

**REST API** (`/api/v1/`):
- `/auth/*` - Authentication endpoints
- `/voice/*` - Voice processing (transcribe, synthesize, translate)
- `/diagnosis/*` - Crop disease, pest identification, soil analysis
- `/intelligence/*` - Weather, market prices, government schemes
- `/community/*` - Forums, resource sharing, buying groups
- `/financial/*` - Profitability calculator, loan products
- `/sharing/*` - Equipment availability, bookings, local economy metrics

**WebSocket API** (`/ws/`):
- Real-time features: weather alerts, market updates, community chat, equipment availability

### CloudFront Distribution

- **Static Content**: 1-year TTL for educational materials and crop database
- **Images**: 7-day TTL with compression enabled
- **Price Class**: 200 (US, Europe, Asia, Middle East, Africa)
- **Logging**: Enabled for analytics

## Configuration

The stack uses context values from `cdk.json` and can be customized:

```bash
# Deploy to specific account/region
cdk deploy --context account=123456789012 --context region=us-east-1
```

## Monitoring

All resources include:
- CloudWatch metrics and logging
- API Gateway request/error tracking
- DynamoDB capacity monitoring
- S3 access logging

## Cost Optimization

- **DynamoDB**: Pay-per-request billing mode
- **S3**: Lifecycle policies for automatic archival
- **CloudFront**: Optimized caching to reduce origin requests
- **API Gateway**: Caching enabled with 6-hour TTL

## Security

- **Encryption**: All data encrypted at rest (DynamoDB, S3)
- **TLS**: HTTPS enforced via CloudFront
- **IAM**: Least privilege access for Lambda functions
- **S3**: Block all public access enabled
- **Point-in-time Recovery**: Enabled for all DynamoDB tables

## Cleanup

To delete all resources:

```bash
cdk destroy
```

**Warning**: This will delete all data. Ensure backups are taken before destroying the stack.

## Troubleshooting

### Common Issues

1. **Bootstrap Error**: Run `cdk bootstrap` first
2. **Permission Denied**: Ensure AWS credentials have sufficient permissions
3. **Resource Limits**: Check AWS service quotas for your account
4. **Deployment Timeout**: Increase timeout in `cdk.json` context

## Next Steps

After infrastructure deployment:

1. Note the API Gateway endpoint URLs from CDK outputs
2. Update `.env` file with resource names and endpoints
3. Deploy Lambda functions for API endpoints
4. Configure Amazon Bedrock model access
5. Set up OpenTelemetry for observability

## Support

For issues or questions, refer to:
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [RISE Project README](../README.md)
- [Design Document](../.kiro/specs/rise-farming-assistant/design.md)
