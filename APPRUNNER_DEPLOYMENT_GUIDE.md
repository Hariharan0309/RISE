# RISE - AWS App Runner Deployment Guide

This guide walks you through deploying the RISE Streamlit application to AWS App Runner using Docker.

## Prerequisites

### 1. Install Docker
```bash
# Check if Docker is installed
docker --version

# If not installed, install Docker:
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io

# macOS
brew install docker

# Start Docker daemon
sudo systemctl start docker  # Linux
# or open Docker Desktop on macOS
```

### 2. AWS CLI Configuration
```bash
# Verify AWS CLI is configured
aws sts get-caller-identity --profile AdministratorAccess-696874273327

# If not configured, set up AWS SSO
aws configure sso
```

### 3. Required AWS Permissions
Ensure your AWS account has permissions for:
- Amazon ECR (Elastic Container Registry)
- AWS App Runner
- IAM (for creating service roles)

## Deployment Steps

### Option 1: Automated Deployment (Recommended)

Run the deployment script:

```bash
./deploy_apprunner.sh
```

This script will:
1. Create an ECR repository (if it doesn't exist)
2. Build the Docker image
3. Push the image to ECR
4. Create or update the App Runner service
5. Display the application URL

### Option 2: Manual Deployment

#### Step 1: Create ECR Repository

```bash
AWS_REGION=us-east-1
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO_NAME="rise-farming-assistant"

aws ecr create-repository \
    --repository-name $ECR_REPO_NAME \
    --region $AWS_REGION \
    --image-scanning-configuration scanOnPush=true
```

#### Step 2: Build Docker Image

```bash
docker build -t rise-farming-assistant:latest .
```

#### Step 3: Tag and Push to ECR

```bash
# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    ${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Tag image
docker tag rise-farming-assistant:latest \
    ${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/rise-farming-assistant:latest

# Push image
docker push ${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/rise-farming-assistant:latest
```

#### Step 4: Create IAM Role for App Runner

```bash
# Create trust policy
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "build.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
    --role-name AppRunnerECRAccessRole \
    --assume-role-policy-document file://trust-policy.json

# Attach policy
aws iam attach-role-policy \
    --role-name AppRunnerECRAccessRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess
```

#### Step 5: Create App Runner Service

```bash
aws apprunner create-service \
    --service-name rise-farming-assistant \
    --region $AWS_REGION \
    --source-configuration file://apprunner-config.json \
    --instance-configuration Cpu=1vCPU,Memory=2GB \
    --health-check-configuration Protocol=HTTP,Path=/_stcore/health,Interval=10,Timeout=5,HealthyThreshold=1,UnhealthyThreshold=5
```

Create `apprunner-config.json`:
```json
{
  "ImageRepository": {
    "ImageIdentifier": "<AWS_ACCOUNT>.dkr.ecr.us-east-1.amazonaws.com/rise-farming-assistant:latest",
    "ImageRepositoryType": "ECR",
    "ImageConfiguration": {
      "Port": "8501",
      "RuntimeEnvironmentVariables": {
        "AWS_REGION": "us-east-1",
        "APP_ENV": "production",
        "DEBUG": "False"
      }
    }
  },
  "AutoDeploymentsEnabled": true,
  "AuthenticationConfiguration": {
    "AccessRoleArn": "arn:aws:iam::<AWS_ACCOUNT>:role/AppRunnerECRAccessRole"
  }
}
```

## Post-Deployment

### 1. Get Service URL

```bash
aws apprunner list-services --region us-east-1 \
    --query "ServiceSummaryList[?ServiceName=='rise-farming-assistant'].ServiceUrl" \
    --output text
```

### 2. Monitor Deployment Status

```bash
# Get service ARN
SERVICE_ARN=$(aws apprunner list-services --region us-east-1 \
    --query "ServiceSummaryList[?ServiceName=='rise-farming-assistant'].ServiceArn" \
    --output text)

# Check service status
aws apprunner describe-service \
    --service-arn $SERVICE_ARN \
    --region us-east-1 \
    --query 'Service.Status'
```

### 3. View Logs

```bash
# App Runner automatically sends logs to CloudWatch
# View logs in AWS Console:
# CloudWatch > Log groups > /aws/apprunner/rise-farming-assistant/...
```

## Environment Variables

To add environment variables to your App Runner service:

```bash
aws apprunner update-service \
    --service-arn $SERVICE_ARN \
    --region us-east-1 \
    --source-configuration '{
        "ImageRepository": {
            "ImageConfiguration": {
                "RuntimeEnvironmentVariables": {
                    "AWS_REGION": "us-east-1",
                    "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
                    "APP_ENV": "production",
                    "DEBUG": "False"
                }
            }
        }
    }'
```

## Scaling Configuration

App Runner automatically scales based on traffic. To configure scaling:

```bash
aws apprunner update-service \
    --service-arn $SERVICE_ARN \
    --region us-east-1 \
    --auto-scaling-configuration-arn <auto-scaling-config-arn>
```

Create auto-scaling configuration:

```bash
aws apprunner create-auto-scaling-configuration \
    --auto-scaling-configuration-name rise-auto-scaling \
    --max-concurrency 100 \
    --min-size 1 \
    --max-size 10
```

## Cost Optimization

### App Runner Pricing (us-east-1)
- **Compute**: $0.064 per vCPU-hour + $0.007 per GB-hour
- **Memory**: Included in compute pricing
- **Requests**: $0.40 per million requests

### Estimated Monthly Cost
For 1 vCPU, 2 GB RAM, running 24/7:
- Compute: ~$46/month
- 1M requests: $0.40
- **Total**: ~$46-50/month

### Cost Saving Tips
1. Use auto-scaling to scale down during low traffic
2. Set minimum instances to 1
3. Use CloudWatch alarms to monitor costs
4. Consider pausing service during non-business hours (if applicable)

## Troubleshooting

### Issue: Service fails to start

**Check logs:**
```bash
aws logs tail /aws/apprunner/rise-farming-assistant/<service-id>/application --follow
```

**Common causes:**
- Port mismatch (ensure Dockerfile exposes 8501)
- Missing dependencies in requirements.txt
- AWS credentials not configured properly

### Issue: Health check failing

**Solution:**
- Verify health check path: `/_stcore/health`
- Increase health check timeout
- Check if Streamlit is binding to 0.0.0.0

### Issue: Image push fails

**Solution:**
```bash
# Re-authenticate with ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    ${AWS_ACCOUNT}.dkr.ecr.us-east-1.amazonaws.com
```

### Issue: Permission denied errors

**Solution:**
- Verify IAM role has correct permissions
- Check App Runner service role has ECR access
- Ensure AWS profile has necessary permissions

## Updating the Application

### Deploy New Version

```bash
# Build new image
docker build -t rise-farming-assistant:v2 .

# Tag and push
docker tag rise-farming-assistant:v2 \
    ${AWS_ACCOUNT}.dkr.ecr.us-east-1.amazonaws.com/rise-farming-assistant:latest

docker push ${AWS_ACCOUNT}.dkr.ecr.us-east-1.amazonaws.com/rise-farming-assistant:latest

# App Runner will automatically deploy the new version (if auto-deploy is enabled)
```

### Manual Deployment Trigger

```bash
aws apprunner start-deployment \
    --service-arn $SERVICE_ARN \
    --region us-east-1
```

## Monitoring

### CloudWatch Metrics

App Runner automatically publishes metrics:
- `2xxStatusResponses` - Successful requests
- `4xxStatusResponses` - Client errors
- `5xxStatusResponses` - Server errors
- `RequestLatency` - Response time
- `ActiveInstances` - Number of running instances

### Create CloudWatch Dashboard

```bash
# Create dashboard for monitoring
aws cloudwatch put-dashboard \
    --dashboard-name RISE-AppRunner \
    --dashboard-body file://dashboard-config.json
```

## Security Best Practices

1. **Use VPC Connector** (Optional):
   - Connect App Runner to VPC for private resource access
   - Isolate database and cache access

2. **Enable WAF** (Optional):
   - Protect against common web exploits
   - Add rate limiting

3. **Use Secrets Manager**:
   - Store sensitive configuration in AWS Secrets Manager
   - Reference secrets in environment variables

4. **Enable Encryption**:
   - App Runner encrypts data in transit (HTTPS)
   - ECR images are encrypted at rest

## Cleanup

To delete the App Runner service and resources:

```bash
# Delete App Runner service
aws apprunner delete-service \
    --service-arn $SERVICE_ARN \
    --region us-east-1

# Delete ECR repository
aws ecr delete-repository \
    --repository-name rise-farming-assistant \
    --region us-east-1 \
    --force

# Delete IAM role
aws iam detach-role-policy \
    --role-name AppRunnerECRAccessRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess

aws iam delete-role --role-name AppRunnerECRAccessRole
```

## Additional Resources

- [AWS App Runner Documentation](https://docs.aws.amazon.com/apprunner/)
- [Streamlit Deployment Guide](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [AWS ECR Documentation](https://docs.aws.amazon.com/ecr/)

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review App Runner service events
3. Verify AWS service quotas
4. Contact AWS Support if needed

---

**Last Updated:** March 6, 2026  
**Version:** 1.0.0
