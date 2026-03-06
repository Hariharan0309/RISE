# RISE Production Configuration

**Generated:** Fri Mar  6 08:12:03 PM IST 2026

## Infrastructure Endpoints

- **API Gateway:** https://7uqvymxydd.execute-api.us-east-1.amazonaws.com/v1/
- **CloudFront CDN:** https://d1420mjs1cmoa6.cloudfront.net
- **S3 Bucket:** rise-application-data-696874273327

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

Update the following in `.env.production`:

```bash
# OpenWeather API (Free tier available)
OPENWEATHER_API_KEY=your_key_here
# Get from: https://openweathermap.org/api

# AgMarkNet API (Optional)
AGMARKNET_API_URL=https://api.data.gov.in/resource/
```

### 2. CloudWatch Alarms

Set up monitoring alarms:

```bash
python setup_cloudwatch_alarms.py
```

### 3. SNS Notifications

Subscribe to alarm notifications:

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:696874273327:RISE-Alarms \
  --protocol email \
  --notification-endpoint your-email@example.com
```

## Testing Production Endpoints

### Test API Gateway

```bash
curl https://7uqvymxydd.execute-api.us-east-1.amazonaws.com/v1/
```

### Test CloudFront

```bash
curl https://d1420mjs1cmoa6.cloudfront.net
```

### Test DynamoDB Access

```bash
aws dynamodb describe-table --table-name RISE-UserProfiles
```

## Running the Application

### Development Mode

```bash
streamlit run app.py
```

### Production Mode

```bash
# Load production environment
export $(cat .env.production | xargs)

# Run with production settings
streamlit run app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true
```

## Monitoring

### CloudWatch Logs

- API Gateway: `/aws/apigateway/RISE-API`
- Lambda: `/aws/lambda/rise-*`

### CloudWatch Metrics

View metrics in AWS Console:
- API Gateway: Requests, Latency, Errors
- DynamoDB: Read/Write Capacity, Throttles
- CloudFront: Requests, Data Transfer

### Cost Monitoring

```bash
# View current month costs
aws ce get-cost-and-usage \
  --time-period Start=2026-03-01,End=2026-03-06 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

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

```bash
# Create on-demand backup
aws dynamodb create-backup \
  --table-name RISE-UserProfiles \
  --backup-name RISE-UserProfiles-backup-$(date +%Y%m%d)
```

### S3 Versioning

Versioning is enabled. Recover deleted objects:

```bash
aws s3api list-object-versions \
  --bucket rise-application-data-696874273327 \
  --prefix images/
```

## Troubleshooting

### Clear CloudFront Cache

```bash
aws cloudfront create-invalidation \
  --distribution-id $(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='RISE CDN Distribution'].Id" --output text) \
  --paths "/*"
```

### Check API Gateway Logs

```bash
aws logs tail /aws/apigateway/RISE-API --follow
```

### Check DynamoDB Metrics

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=RISE-UserProfiles \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

---

**Last Updated:** Fri Mar  6 08:12:03 PM IST 2026
