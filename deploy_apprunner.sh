#!/bin/bash
# RISE AWS App Runner Deployment Script

set -e

# Disable AWS CLI pager to prevent script from hanging or failing on JSON outputs
export AWS_PAGER=""

echo "======================================================================"
echo "  RISE - AWS App Runner Deployment"
echo "======================================================================"
echo ""

# Configuration
AWS_PROFILE=${AWS_PROFILE:-AdministratorAccess-696874273327}
AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text)
ECR_REPOSITORY_NAME="rise-farming-assistant"
APP_RUNNER_SERVICE_NAME="rise-farming-assistant"
IMAGE_TAG=${IMAGE_TAG:-$(date +%Y%m%d_%H%M%S)}

echo "📋 Configuration:"
echo "   AWS Profile: $AWS_PROFILE"
echo "   AWS Region: $AWS_REGION"
echo "   AWS Account: $AWS_ACCOUNT"
echo "   ECR Repository: $ECR_REPOSITORY_NAME"
echo "   App Runner Service: $APP_RUNNER_SERVICE_NAME"
echo "   Image Tag: $IMAGE_TAG"
echo ""

# Step 1: Create ECR repository if it doesn't exist
echo "📦 Step 1: Setting up ECR repository..."
if aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION --profile $AWS_PROFILE 2>/dev/null; then
    echo "   ✅ ECR repository already exists"
else
    echo "   Creating ECR repository..."
    aws ecr create-repository \
        --repository-name $ECR_REPOSITORY_NAME \
        --region $AWS_REGION \
        --profile $AWS_PROFILE \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256
    echo "   ✅ ECR repository created"
fi

ECR_URI="${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"
echo "   ECR URI: $ECR_URI"
echo ""

# Step 2: Build Docker image
echo "🔨 Step 2: Building Docker image..."
docker build -t $ECR_REPOSITORY_NAME:$IMAGE_TAG .
echo "   ✅ Docker image built successfully"
echo ""

# Step 3: Tag image for ECR
echo "🏷️  Step 3: Tagging image for ECR..."
docker tag $ECR_REPOSITORY_NAME:$IMAGE_TAG $ECR_URI:$IMAGE_TAG
docker tag $ECR_REPOSITORY_NAME:$IMAGE_TAG $ECR_URI:latest
echo "   ✅ Image tagged"
echo ""

# Step 4: Login to ECR
echo "🔐 Step 4: Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | \
    docker login --username AWS --password-stdin $ECR_URI
echo "   ✅ Logged in to ECR"
echo ""

# Step 5: Push image to ECR
echo "⬆️  Step 5: Pushing image to ECR..."
docker push $ECR_URI:$IMAGE_TAG
docker push $ECR_URI:latest
echo "   ✅ Image pushed to ECR"
echo ""

# Step 6: Create or update App Runner service
echo "🚀 Step 6: Deploying to App Runner..."

# Check if service exists
if aws apprunner list-services --region $AWS_REGION --profile $AWS_PROFILE | \
   grep -q $APP_RUNNER_SERVICE_NAME 2>/dev/null; then
    echo "   Updating existing App Runner service..."
    
    # Get service ARN
    SERVICE_ARN=$(aws apprunner list-services \
        --region $AWS_REGION \
        --profile $AWS_PROFILE \
        --query "ServiceSummaryList[?ServiceName=='$APP_RUNNER_SERVICE_NAME'].ServiceArn" \
        --output text)
    
    # Update service
    aws apprunner update-service \
        --service-arn $SERVICE_ARN \
        --region $AWS_REGION \
        --profile $AWS_PROFILE \
        --source-configuration "ImageRepository={ImageIdentifier=$ECR_URI:$IMAGE_TAG,ImageRepositoryType=ECR,ImageConfiguration={Port=8080}},AutoDeploymentsEnabled=true"
    
    echo "   ✅ App Runner service updated"
else
    echo "   Creating new App Runner service..."
    
    # Create IAM role for App Runner if it doesn't exist
    ROLE_NAME="AppRunnerECRAccessRole"
    if aws iam get-role --role-name $ROLE_NAME --profile $AWS_PROFILE 2>/dev/null; then
        echo "   ✅ IAM role already exists"
    else
        echo "   Creating IAM role for App Runner..."
        
        # Create trust policy
        cat > /tmp/trust-policy.json << EOF
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
        
        aws iam create-role \
            --role-name $ROLE_NAME \
            --assume-role-policy-document file:///tmp/trust-policy.json \
            --profile $AWS_PROFILE
        
        aws iam attach-role-policy \
            --role-name $ROLE_NAME \
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess \
            --profile $AWS_PROFILE
        
        echo "   ✅ IAM role created"
        
        # Wait for role to be available
        sleep 10
    fi
    
    ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT}:role/${ROLE_NAME}"
    
    # Create App Runner service
    aws apprunner create-service \
        --service-name $APP_RUNNER_SERVICE_NAME \
        --region $AWS_REGION \
        --profile $AWS_PROFILE \
        --source-configuration "{
            \"ImageRepository\": {
                \"ImageIdentifier\": \"$ECR_URI:$IMAGE_TAG\",
                \"ImageRepositoryType\": \"ECR\",
                \"ImageConfiguration\": {
                    \"Port\": \"8080\",
                    \"RuntimeEnvironmentVariables\": {
                        \"AWS_REGION\": \"$AWS_REGION\",
                        \"APP_ENV\": \"production\",
                        \"DEBUG\": \"False\"
                    }
                }
            },
            \"AutoDeploymentsEnabled\": true,
            \"AuthenticationConfiguration\": {
                \"AccessRoleArn\": \"$ROLE_ARN\"
            }
        }" \
        --instance-configuration "{
            \"Cpu\": \"1 vCPU\",
            \"Memory\": \"2 GB\"
        }" \
        --health-check-configuration "{
            \"Protocol\": \"HTTP\",
            \"Path\": \"/_stcore/health\",
            \"Interval\": 10,
            \"Timeout\": 5,
            \"HealthyThreshold\": 1,
            \"UnhealthyThreshold\": 5
        }"
    
    echo "   ✅ App Runner service created"
fi

echo ""
echo "======================================================================"
echo "  Deployment Summary"
echo "======================================================================"
echo ""
echo "✅ Docker image built and pushed to ECR"
echo "✅ App Runner service deployed"
echo ""
echo "📍 Getting service URL..."

# Wait a moment for service to be created
sleep 5

# Get service URL
SERVICE_URL=$(aws apprunner list-services \
    --region $AWS_REGION \
    --profile $AWS_PROFILE \
    --query "ServiceSummaryList[?ServiceName=='$APP_RUNNER_SERVICE_NAME'].ServiceUrl" \
    --output text)

if [ -n "$SERVICE_URL" ]; then
    echo ""
    echo "🌐 Application URL: https://$SERVICE_URL"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Wait 2-3 minutes for the service to fully deploy"
    echo "   2. Access your application at: https://$SERVICE_URL"
    echo "   3. Monitor deployment: aws apprunner describe-service --service-arn <arn> --region $AWS_REGION"
    echo ""
else
    echo ""
    echo "⚠️  Service URL not yet available. Check AWS Console for status."
    echo ""
fi

echo "======================================================================"
echo "  Deployment Complete!"
echo "======================================================================"
