#!/bin/bash
# RISE Production Configuration Script
# Updates environment variables with deployed infrastructure values

set -e

echo "🔧 RISE Production Configuration"
echo "=================================="
echo ""

# Set AWS profile and region
export AWS_PROFILE=AdministratorAccess-696874273327
AWS_REGION=${AWS_REGION:-us-east-1}

# Get AWS account ID
AWS_ACCOUNT=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text)

echo "📍 AWS Account: $AWS_ACCOUNT"
echo "📍 Region: $AWS_REGION"
echo ""

# Get CloudFormation stack outputs
echo "📋 Fetching infrastructure details..."

# Get API Gateway endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name RiseStack \
  --region $AWS_REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`RiseRestApiEndpointDE36018A`].OutputValue' \
  --output text)

# Get CloudFront distribution
CLOUDFRONT_DOMAIN=$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Comment=='RISE CDN Distribution'].DomainName" \
  --output text | head -1)

# Get S3 bucket name
S3_BUCKET="rise-application-data-${AWS_ACCOUNT}"

# Get DynamoDB table names
echo "  ✅ API Gateway: $API_ENDPOINT"
echo "  ✅ CloudFront: $CLOUDFRONT_DOMAIN"
echo "  ✅ S3 Bucket: $S3_BUCKET"
echo ""

# Create production .env file
echo "📝 Creating production environment configuration..."

cat > ../.env.production << EOF
# RISE Production Environment Configuration
# Generated: $(date)

# AWS Configuration
AWS_REGION=$AWS_REGION
AWS_ACCOUNT_ID=$AWS_ACCOUNT

# Amazon Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=$AWS_REGION

# Application Configuration
APP_NAME=RISE
APP_ENV=production
DEBUG=False

# Infrastructure Endpoints
API_GATEWAY_URL=$API_ENDPOINT
CLOUDFRONT_DOMAIN=$CLOUDFRONT_DOMAIN
S3_BUCKET_NAME=$S3_BUCKET

# DynamoDB Tables
DYNAMODB_USER_PROFILES_TABLE=RISE-UserProfiles
DYNAMODB_FARM_DATA_TABLE=RISE-FarmData
DYNAMODB_DIAGNOSIS_HISTORY_TABLE=RISE-DiagnosisHistory
DYNAMODB_PEST_DIAGNOSIS_HISTORY_TABLE=RISE-PestDiagnosisHistory
DYNAMODB_PEST_KNOWLEDGE_TABLE=RISE-PestKnowledgeBase
DYNAMODB_RESOURCE_SHARING_TABLE=RISE-ResourceSharing
DYNAMODB_BUYING_GROUPS_TABLE=RISE-BuyingGroups
DYNAMODB_RESOURCE_BOOKINGS_TABLE=RISE-ResourceBookings
DYNAMODB_CONVERSATION_HISTORY_TABLE=RISE-ConversationHistory
DYNAMODB_WEATHER_FORECAST_TABLE=RISE-WeatherForecast
DYNAMODB_MARKET_PRICES_TABLE=RISE-MarketPrices
DYNAMODB_GOVERNMENT_SCHEMES_TABLE=RISE-GovernmentSchemes

# OpenTelemetry Configuration
OTEL_SERVICE_NAME=rise-farming-assistant
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# External API Keys (CONFIGURE THESE)
OPENWEATHER_API_KEY=your_openweather_api_key_here
AGMARKNET_API_URL=https://api.data.gov.in/resource/

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
EOF

echo "  ✅ Created .env.production"
echo ""

# Create production config summary
cat > PRODUCTION_CONFIG.md << EOF
# RISE Production Configuration

**Generated:** $(date)

## Infrastructure Endpoints

- **API Gateway:** $API_ENDPOINT
- **CloudFront CDN:** https://$CLOUDFRONT_DOMAIN
- **S3 Bucket:** $S3_BUCKET

## DynamoDB Tables

- RISE-UserProfiles
- RISE-FarmData
- RISE-DiagnosisHistory
- RISE-PestDiagnosisHistory
- RISE-PestKnowledgeBase
- RISE-ResourceSharing
- RISE-BuyingGroups
- RISE-ResourceBookings
- RISE-ConversationHistory
- RISE-WeatherForecast
- RISE-MarketPrices
- RISE-GovernmentSchemes

## Required Configuration

### 1. External API Keys

Update the following in \`.env.production\`:

\`\`\`bash
# OpenWeather API (Free tier available)
OPENWEATHER_API_KEY=your_key_here
# Get from: https://openweathermap.org/api

# AgMarkNet API (Optional)
AGMARKNET_API_URL=https://api.data.gov.in/resource/
\`\`\`

### 2. CloudWatch Alarms

Set up monitoring alarms:

\`\`\`bash
python setup_cloudwatch_alarms.py
\`\`\`

### 3. SNS Notifications

Subscribe to alarm notifications:

\`\`\`bash
aws sns subscribe \\
  --topic-arn arn:aws:sns:$AWS_REGION:$AWS_ACCOUNT:RISE-Alarms \\
  --protocol email \\
  --notification-endpoint your-email@example.com
\`\`\`

## Testing Production Endpoints

### Test API Gateway

\`\`\`bash
curl $API_ENDPOINT
\`\`\`

### Test CloudFront

\`\`\`bash
curl https://$CLOUDFRONT_DOMAIN
\`\`\`

### Test DynamoDB Access

\`\`\`bash
aws dynamodb describe-table --table-name RISE-UserProfiles
\`\`\`

## Running the Application

### Development Mode

\`\`\`bash
streamlit run app.py
\`\`\`

### Production Mode

\`\`\`bash
# Load production environment
export \$(cat .env.production | xargs)

# Run with production settings
streamlit run app.py \\
  --server.port 8501 \\
  --server.address 0.0.0.0 \\
  --server.headless true
\`\`\`

## Monitoring

### CloudWatch Logs

- API Gateway: \`/aws/apigateway/RISE-API\`
- Lambda: \`/aws/lambda/rise-*\`

### CloudWatch Metrics

View metrics in AWS Console:
- API Gateway: Requests, Latency, Errors
- DynamoDB: Read/Write Capacity, Throttles
- CloudFront: Requests, Data Transfer

### Cost Monitoring

\`\`\`bash
# View current month costs
aws ce get-cost-and-usage \\
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \\
  --granularity MONTHLY \\
  --metrics BlendedCost \\
  --group-by Type=SERVICE
\`\`\`

## Security Checklist

- [x] Encryption at rest (DynamoDB, S3)
- [x] Encryption in transit (HTTPS/TLS)
- [x] IAM roles with least privilege
- [x] S3 block public access
- [x] API Gateway throttling
- [ ] Configure WAF rules (optional)
- [ ] Store API keys in Secrets Manager
- [ ] Enable CloudTrail logging

## Backup & Recovery

### DynamoDB Backups

\`\`\`bash
# Create on-demand backup
aws dynamodb create-backup \\
  --table-name RISE-UserProfiles \\
  --backup-name RISE-UserProfiles-backup-\$(date +%Y%m%d)
\`\`\`

### S3 Versioning

Versioning is enabled. Recover deleted objects:

\`\`\`bash
aws s3api list-object-versions \\
  --bucket $S3_BUCKET \\
  --prefix images/
\`\`\`

## Troubleshooting

### Clear CloudFront Cache

\`\`\`bash
aws cloudfront create-invalidation \\
  --distribution-id \$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='RISE CDN Distribution'].Id" --output text) \\
  --paths "/*"
\`\`\`

### Check API Gateway Logs

\`\`\`bash
aws logs tail /aws/apigateway/RISE-API --follow
\`\`\`

### Check DynamoDB Metrics

\`\`\`bash
aws cloudwatch get-metric-statistics \\
  --namespace AWS/DynamoDB \\
  --metric-name ConsumedReadCapacityUnits \\
  --dimensions Name=TableName,Value=RISE-UserProfiles \\
  --start-time \$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \\
  --end-time \$(date -u +%Y-%m-%dT%H:%M:%S) \\
  --period 300 \\
  --statistics Sum
\`\`\`

---

**Last Updated:** $(date)
EOF

echo "  ✅ Created PRODUCTION_CONFIG.md"
echo ""

echo "✅ Production configuration complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Review .env.production and add API keys"
echo "  2. Run: python setup_cloudwatch_alarms.py"
echo "  3. Subscribe to SNS notifications"
echo "  4. Test endpoints using PRODUCTION_CONFIG.md"
echo "  5. Deploy Lambda functions (if needed)"
echo ""
echo "📖 See PRODUCTION_CONFIG.md for detailed instructions"
