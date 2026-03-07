# AWS App Runner Deployment Setup - Complete ✅

## What Has Been Created

### 1. Docker Configuration
- ✅ **Dockerfile** - Optimized for AWS App Runner with health checks
- ✅ **.dockerignore** - Excludes unnecessary files from Docker image
- ✅ **Streamlit config** - Production-ready configuration embedded in Docker image

### 2. Deployment Scripts
- ✅ **deploy_apprunner.sh** - Automated deployment script
  - Creates ECR repository
  - Builds and pushes Docker image
  - Deploys to App Runner
  - Handles IAM roles automatically

### 3. Documentation
- ✅ **APPRUNNER_DEPLOYMENT_GUIDE.md** - Comprehensive deployment guide
  - Prerequisites
  - Step-by-step instructions
  - Troubleshooting
  - Cost optimization
  - Monitoring setup

- ✅ **DEPLOY_NOW.md** - Quick start guide for immediate deployment

## Application Configuration

### Docker Image Specifications
- **Base Image**: Python 3.12-slim
- **Port**: 8501 (Streamlit default)
- **Health Check**: `/_stcore/health` endpoint
- **Environment**: Production-optimized

### App Runner Configuration
- **CPU**: 1 vCPU
- **Memory**: 2 GB RAM
- **Auto-scaling**: 1-10 instances
- **Health Check Interval**: 30 seconds
- **Deployment**: Auto-deploy on ECR push

## Deployment Options

### Option 1: Automated (Recommended)
```bash
./deploy_apprunner.sh
```

### Option 2: Manual
Follow steps in `APPRUNNER_DEPLOYMENT_GUIDE.md`

## What Happens During Deployment

1. **ECR Repository Creation**
   - Repository: `rise-farming-assistant`
   - Region: us-east-1
   - Encryption: AES256
   - Image scanning: Enabled

2. **Docker Image Build**
   - Installs all dependencies from requirements.txt
   - Configures Streamlit for production
   - Sets up health checks
   - Optimizes for container deployment

3. **Image Push to ECR**
   - Tags: `latest` and custom tag
   - Authenticated push to ECR
   - Image available for App Runner

4. **App Runner Service Creation**
   - Creates IAM role for ECR access
   - Deploys container
   - Configures auto-scaling
   - Sets up health monitoring
   - Provides HTTPS endpoint

## Post-Deployment

### Your Application Will Be Available At:
```
https://<random-id>.us-east-1.awsapprunner.com
```

### Features Enabled:
- ✅ HTTPS (automatic SSL certificate)
- ✅ Auto-scaling based on traffic
- ✅ Health monitoring
- ✅ CloudWatch logging
- ✅ Zero-downtime deployments
- ✅ Automatic restarts on failure

## Cost Breakdown

### AWS App Runner
- **Compute**: $0.064/vCPU-hour + $0.007/GB-hour
- **Requests**: $0.40 per million requests

### Monthly Estimate (24/7 operation)
- 1 vCPU × 730 hours = $46.72
- 2 GB × 730 hours = $10.22
- **Total**: ~$57/month (before request charges)

### Cost Optimization Tips
1. Use auto-scaling (scale to 0 when idle)
2. Set minimum instances to 1
3. Monitor usage with CloudWatch
4. Consider pausing during off-hours

## Monitoring & Logs

### CloudWatch Logs
Automatically created log groups:
- `/aws/apprunner/rise-farming-assistant/<service-id>/application`
- `/aws/apprunner/rise-farming-assistant/<service-id>/service`

### Metrics Available
- Request count (2xx, 4xx, 5xx)
- Request latency
- Active instances
- CPU and memory utilization

## Security Features

### Built-in Security
- ✅ HTTPS/TLS encryption
- ✅ Automatic security patches
- ✅ IAM-based access control
- ✅ VPC integration support
- ✅ Secrets Manager integration

### AWS Services Access
The application can access:
- Amazon Bedrock (for AI models)
- DynamoDB (for data storage)
- S3 (for file storage)
- CloudWatch (for logging)

## Updating Your Application

### Deploy New Version
```bash
# Make code changes
git add .
git commit -m "Update feature"

# Deploy
./deploy_apprunner.sh
```

App Runner will:
1. Build new Docker image
2. Push to ECR
3. Automatically deploy (if auto-deploy enabled)
4. Perform zero-downtime deployment

## Troubleshooting

### Common Issues

**Issue**: Docker build fails
**Solution**: Check Dockerfile syntax and dependencies in requirements.txt

**Issue**: ECR push fails
**Solution**: Re-authenticate with ECR:
```bash
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

**Issue**: App Runner service fails health checks
**Solution**: 
- Verify Streamlit is running on port 8501
- Check health endpoint: `/_stcore/health`
- Review CloudWatch logs

**Issue**: Application errors
**Solution**: Check CloudWatch logs for detailed error messages

## Next Steps

1. **Deploy Now**: Run `./deploy_apprunner.sh`
2. **Monitor**: Check AWS Console for deployment status
3. **Test**: Access your application URL
4. **Configure**: Add environment variables if needed
5. **Scale**: Adjust auto-scaling settings based on traffic

## Additional Configuration

### Add Environment Variables
```bash
aws apprunner update-service \
    --service-arn <service-arn> \
    --source-configuration '{
        "ImageRepository": {
            "ImageConfiguration": {
                "RuntimeEnvironmentVariables": {
                    "CUSTOM_VAR": "value"
                }
            }
        }
    }'
```

### Configure Custom Domain
1. Get App Runner service URL
2. Create CNAME record in your DNS
3. Configure custom domain in App Runner

### Enable VPC Access
For private resource access (RDS, ElastiCache):
```bash
aws apprunner create-vpc-connector \
    --vpc-connector-name rise-vpc-connector \
    --subnets subnet-xxx subnet-yyy \
    --security-groups sg-xxx
```

## Resources

- **AWS App Runner Console**: https://console.aws.amazon.com/apprunner
- **ECR Console**: https://console.aws.amazon.com/ecr
- **CloudWatch Logs**: https://console.aws.amazon.com/cloudwatch
- **Documentation**: See `APPRUNNER_DEPLOYMENT_GUIDE.md`

## Support

For deployment issues:
1. Check `APPRUNNER_DEPLOYMENT_GUIDE.md` troubleshooting section
2. Review CloudWatch logs
3. Check AWS Service Health Dashboard
4. Contact AWS Support if needed

---

## Ready to Deploy?

Run this command to start deployment:

```bash
./deploy_apprunner.sh
```

The deployment will take 3-5 minutes. You'll receive your application URL when complete.

---

**Setup Date**: March 6, 2026  
**Status**: ✅ Ready for Deployment  
**Deployment Method**: AWS App Runner with Docker
