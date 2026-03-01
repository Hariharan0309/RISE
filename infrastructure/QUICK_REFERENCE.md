# RISE Infrastructure Quick Reference

## Quick Commands

### Deploy Infrastructure
```bash
cd infrastructure
./deploy.sh
```

### Verify Deployment
```bash
cd infrastructure
python verify_deployment.py
```

### Update Infrastructure
```bash
cd infrastructure
cdk deploy
```

### Destroy Infrastructure
```bash
cd infrastructure
cdk destroy
```

## Resource Names

### DynamoDB Tables
- `RISE-UserProfiles`
- `RISE-FarmData`
- `RISE-DiagnosisHistory`
- `RISE-ResourceSharing`
- `RISE-BuyingGroups`
- `RISE-ResourceBookings`

### S3 Bucket
- `rise-application-data-{account-id}`

### API Gateway
- REST API: `RISE-API` (stage: v1)
- WebSocket API: `RISE-WebSocket-API` (stage: production)

### IAM Role
- `BedrockExecutionRole`

## Common Tasks

### Check DynamoDB Tables
```bash
aws dynamodb list-tables --query "TableNames[?starts_with(@, 'RISE-')]"
```

### Check S3 Bucket
```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 ls s3://rise-application-data-$ACCOUNT_ID
```

### Check API Gateway
```bash
aws apigateway get-rest-apis --query "items[?name=='RISE-API']"
```

### Check Bedrock Models
```bash
aws bedrock list-foundation-models --query "modelSummaries[?contains(modelId, 'claude-3-sonnet') || contains(modelId, 'nova')]"
```

### View CloudFormation Stack
```bash
aws cloudformation describe-stacks --stack-name RiseStack
```

## API Endpoints

### REST API Base URL
```
https://{api-id}.execute-api.{region}.amazonaws.com/v1
```

### WebSocket API URL
```
wss://{api-id}.execute-api.{region}.amazonaws.com/production
```

### CloudFront Domain
```
https://{distribution-id}.cloudfront.net
```

## Environment Variables

Add to `.env`:
```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID={your-account-id}

# DynamoDB Tables
DYNAMODB_USER_PROFILES_TABLE=RISE-UserProfiles
DYNAMODB_FARM_DATA_TABLE=RISE-FarmData
DYNAMODB_DIAGNOSIS_HISTORY_TABLE=RISE-DiagnosisHistory
DYNAMODB_RESOURCE_SHARING_TABLE=RISE-ResourceSharing
DYNAMODB_BUYING_GROUPS_TABLE=RISE-BuyingGroups
DYNAMODB_RESOURCE_BOOKINGS_TABLE=RISE-ResourceBookings

# S3 Bucket
S3_BUCKET_NAME=rise-application-data-{your-account-id}

# API Gateway
API_GATEWAY_REST_URL=https://{api-id}.execute-api.us-east-1.amazonaws.com/v1
API_GATEWAY_WEBSOCKET_URL=wss://{api-id}.execute-api.us-east-1.amazonaws.com/production

# CloudFront
CLOUDFRONT_DOMAIN={distribution-id}.cloudfront.net

# Amazon Bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1
```

## Troubleshooting

### CDK Bootstrap Error
```bash
cdk bootstrap aws://{account-id}/{region}
```

### Bedrock Access Denied
1. Go to AWS Console → Amazon Bedrock
2. Click "Model access"
3. Enable Claude 3 Sonnet and Nova models

### Table Already Exists
```bash
# Delete table (WARNING: deletes data)
aws dynamodb delete-table --table-name RISE-UserProfiles
```

### Check CloudFormation Events
```bash
aws cloudformation describe-stack-events --stack-name RiseStack --max-items 10
```

## Cost Monitoring

### View Current Month Costs
```bash
aws ce get-cost-and-usage \
  --time-period Start=$(date -d "$(date +%Y-%m-01)" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

### Set Cost Alert
1. Go to AWS Billing Console
2. Create Budget
3. Set threshold (e.g., $20/month)
4. Add email notification

## Documentation

- **Full Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Summary**: [INFRASTRUCTURE_SUMMARY.md](INFRASTRUCTURE_SUMMARY.md)
- **CDK Docs**: [README.md](README.md)
- **Design Spec**: [../.kiro/specs/rise-farming-assistant/design.md](../.kiro/specs/rise-farming-assistant/design.md)

## Support

For issues:
1. Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) troubleshooting section
2. Run `python verify_deployment.py` for diagnostics
3. Check CloudFormation events for errors
4. Review AWS service quotas
