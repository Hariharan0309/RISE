# RISE Infrastructure Post-Deployment Checklist

Use this checklist after deploying the infrastructure to ensure everything is configured correctly.

## ✅ Deployment Verification

- [ ] **Run Verification Script**
  ```bash
  cd infrastructure
  python verify_deployment.py
  ```
  - [ ] All 6 DynamoDB tables created
  - [ ] S3 bucket created
  - [ ] Bedrock access verified
  - [ ] Overall status: READY

- [ ] **Check CloudFormation Stack**
  ```bash
  aws cloudformation describe-stacks --stack-name RiseStack --query "Stacks[0].StackStatus"
  ```
  - [ ] Status: `CREATE_COMPLETE` or `UPDATE_COMPLETE`

## ✅ Amazon Bedrock Configuration

- [ ] **Enable Model Access**
  1. [ ] Open AWS Console → Amazon Bedrock
  2. [ ] Navigate to "Model access"
  3. [ ] Click "Manage model access"
  4. [ ] Enable Anthropic Claude 3 Sonnet
  5. [ ] Enable Amazon Nova (all variants)
  6. [ ] Save changes
  7. [ ] Wait for "Access granted" status

- [ ] **Verify Model Access**
  ```bash
  aws bedrock list-foundation-models --query "modelSummaries[?contains(modelId, 'claude-3-sonnet')]"
  ```

## ✅ Environment Configuration

- [ ] **Get Resource Information**
  ```bash
  # Get account ID
  aws sts get-caller-identity --query Account --output text
  
  # Get API Gateway ID
  aws apigateway get-rest-apis --query "items[?name=='RISE-API'].id" --output text
  
  # Get CloudFront domain
  aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='RISE CDN Distribution'].DomainName" --output text
  ```

- [ ] **Update .env File**
  - [ ] Copy `.env.example` to `.env`
  - [ ] Set `AWS_REGION`
  - [ ] Set `AWS_ACCOUNT_ID`
  - [ ] Set `S3_BUCKET_NAME` (with account ID suffix)
  - [ ] Set `API_GATEWAY_REST_URL`
  - [ ] Set `API_GATEWAY_WEBSOCKET_URL`
  - [ ] Set `CLOUDFRONT_DOMAIN`
  - [ ] Set `BEDROCK_MODEL_ID`

- [ ] **Verify Configuration**
  ```bash
  python -c "from config import Config; Config.validate(); print('✅ Configuration valid')"
  ```

## ✅ DynamoDB Tables

- [ ] **Verify Table Creation**
  ```bash
  for table in RISE-UserProfiles RISE-FarmData RISE-DiagnosisHistory RISE-ResourceSharing RISE-BuyingGroups RISE-ResourceBookings; do
    aws dynamodb describe-table --table-name $table --query "Table.TableStatus" --output text
  done
  ```
  - [ ] All tables show `ACTIVE` status

- [ ] **Check GSIs**
  ```bash
  aws dynamodb describe-table --table-name RISE-UserProfiles --query "Table.GlobalSecondaryIndexes[*].IndexName"
  ```
  - [ ] UserProfiles: PhoneIndex, LocationIndex
  - [ ] ResourceSharing: LocationResourceIndex, OwnerResourceIndex
  - [ ] BuyingGroups: LocationGroupIndex, StatusGroupIndex
  - [ ] ResourceBookings: RenterBookingIndex, OwnerBookingIndex, ResourceBookingIndex

## ✅ S3 Bucket

- [ ] **Verify Bucket Creation**
  ```bash
  ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  aws s3 ls s3://rise-application-data-$ACCOUNT_ID
  ```

- [ ] **Check Lifecycle Policies**
  ```bash
  aws s3api get-bucket-lifecycle-configuration --bucket rise-application-data-$ACCOUNT_ID
  ```
  - [ ] Voice queries: 30-day deletion
  - [ ] Crop images: IA after 90 days, Glacier after 1 year
  - [ ] Thumbnails: IA after 90 days

- [ ] **Verify CORS Configuration**
  ```bash
  aws s3api get-bucket-cors --bucket rise-application-data-$ACCOUNT_ID
  ```

## ✅ API Gateway

- [ ] **Verify REST API**
  ```bash
  aws apigateway get-rest-apis --query "items[?name=='RISE-API']"
  ```
  - [ ] Stage: v1
  - [ ] Throttling configured
  - [ ] Caching enabled

- [ ] **Verify WebSocket API**
  ```bash
  aws apigatewayv2 get-apis --query "Items[?Name=='RISE-WebSocket-API']"
  ```
  - [ ] Stage: production
  - [ ] Auto-deploy enabled

- [ ] **Test API Endpoint**
  ```bash
  API_ID=$(aws apigateway get-rest-apis --query "items[?name=='RISE-API'].id" --output text)
  curl https://$API_ID.execute-api.us-east-1.amazonaws.com/v1/
  ```

## ✅ CloudFront Distribution

- [ ] **Verify Distribution**
  ```bash
  aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='RISE CDN Distribution']"
  ```
  - [ ] Status: Deployed
  - [ ] HTTPS enabled
  - [ ] Compression enabled

- [ ] **Test CloudFront**
  ```bash
  DOMAIN=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='RISE CDN Distribution'].DomainName" --output text)
  curl -I https://$DOMAIN
  ```

## ✅ IAM Roles

- [ ] **Verify Bedrock Execution Role**
  ```bash
  aws iam get-role --role-name RiseStack-BedrockExecutionRole*
  ```
  - [ ] Bedrock permissions attached
  - [ ] DynamoDB permissions attached
  - [ ] S3 permissions attached
  - [ ] Translate/Transcribe/Polly permissions attached

## ✅ Monitoring Setup

- [ ] **CloudWatch Logs**
  ```bash
  aws logs describe-log-groups --log-group-name-prefix /aws/rise
  ```

- [ ] **CloudWatch Metrics**
  - [ ] Navigate to CloudWatch Console
  - [ ] Check for RISE namespace
  - [ ] Verify metrics are being collected

- [ ] **Cost Monitoring**
  - [ ] Set up AWS Budget for $20/month
  - [ ] Enable cost alerts
  - [ ] Review Cost Explorer

## ✅ OpenTelemetry Configuration

- [ ] **Install OTEL Collector** (Optional for development)
  ```bash
  # For local development
  brew install opentelemetry-collector  # Mac
  # OR download from GitHub releases
  ```

- [ ] **Configure OTEL**
  - [ ] Copy `otel-config.yaml` to OTEL directory
  - [ ] Update AWS region in config
  - [ ] Start OTEL collector

- [ ] **Verify OTEL**
  ```bash
  curl http://localhost:13133/  # Health check
  ```

## ✅ Security Verification

- [ ] **S3 Bucket Security**
  ```bash
  aws s3api get-public-access-block --bucket rise-application-data-$ACCOUNT_ID
  ```
  - [ ] Block all public access: true

- [ ] **DynamoDB Encryption**
  ```bash
  aws dynamodb describe-table --table-name RISE-UserProfiles --query "Table.SSEDescription"
  ```
  - [ ] Encryption enabled

- [ ] **API Gateway HTTPS**
  - [ ] All endpoints use HTTPS
  - [ ] TLS 1.2+ enforced

## ✅ Application Testing

- [ ] **Test Application Startup**
  ```bash
  cd ..
  streamlit run app.py
  ```
  - [ ] Application starts without errors
  - [ ] Can connect to AWS services

- [ ] **Test AWS Service Connections**
  ```python
  from infrastructure.aws_services import AWSServices
  services = AWSServices()
  
  # Test DynamoDB
  dynamodb = services.get_dynamodb_resource()
  table = dynamodb.Table('RISE-UserProfiles')
  print(table.table_status)
  
  # Test S3
  s3 = services.get_s3_client()
  s3.list_buckets()
  
  # Test Bedrock
  result = services.verify_bedrock_access()
  print(result)
  ```

## ✅ Documentation

- [ ] **Update Project Documentation**
  - [ ] Note API Gateway endpoints in README
  - [ ] Document S3 bucket name
  - [ ] Update deployment instructions

- [ ] **Create Runbook**
  - [ ] Document common operations
  - [ ] Add troubleshooting steps
  - [ ] Include rollback procedures

## ✅ Backup and Disaster Recovery

- [ ] **Enable Point-in-Time Recovery**
  - [ ] Verify PITR enabled on all DynamoDB tables
  - [ ] Check S3 versioning enabled

- [ ] **Document Backup Procedures**
  - [ ] DynamoDB backup strategy
  - [ ] S3 backup strategy
  - [ ] Configuration backup

## 📊 Post-Deployment Summary

After completing all checklist items:

```bash
# Generate summary report
python verify_deployment.py > deployment_report.txt

# Review the report
cat deployment_report.txt
```

## 🎉 Deployment Complete!

If all items are checked:

✅ Infrastructure is fully deployed  
✅ All services are configured  
✅ Security is enabled  
✅ Monitoring is active  
✅ Application is ready to use  

## Next Steps

1. **Proceed to Phase 2**: Voice & Multilingual Tools
2. **Deploy Lambda Functions**: For API endpoints
3. **Test End-to-End**: Complete user workflows
4. **Monitor Performance**: Check CloudWatch metrics
5. **Optimize Costs**: Review and adjust resources

## Support

If any checklist item fails:
1. Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) troubleshooting
2. Review CloudFormation events
3. Check AWS service quotas
4. Verify IAM permissions

---

**Deployment Date**: _____________  
**Deployed By**: _____________  
**AWS Account**: _____________  
**Region**: _____________  
**Status**: ⬜ In Progress  ⬜ Complete  ⬜ Issues Found
