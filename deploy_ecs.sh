#!/bin/bash
# RISE AWS ECS Fargate Deployment Script

set -e

# Disable AWS CLI pager
export AWS_PAGER=""

echo "======================================================================"
echo "  RISE - AWS ECS Fargate Deployment"
echo "======================================================================"
echo ""

# Configuration
AWS_PROFILE=${AWS_PROFILE:-AdministratorAccess-696874273327}
AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text)
ECR_REPOSITORY_NAME="rise-farming-assistant"
CLUSTER_NAME="rise-cluster"
SERVICE_NAME="rise-service"
TASK_FAMILY="rise-task"
ALB_NAME="rise-alb"
TG_NAME="rise-tg"
IMAGE_TAG=${IMAGE_TAG:-$(date +%Y%m%d_%H%M%S)}

# Use inference profile ID (required for ConverseStream on-demand; direct model ID not supported)
BEDROCK_MODEL_ID=${BEDROCK_MODEL_ID:-global.anthropic.claude-sonnet-4-20250514-v1:0}

echo "📋 Configuration:"
echo "   AWS Region: $AWS_REGION"
echo "   ECR Repository: $ECR_REPOSITORY_NAME"
echo "   ECS Cluster: $CLUSTER_NAME"
echo "   Image Tag: $IMAGE_TAG"
echo "   Bedrock Model: $BEDROCK_MODEL_ID"

# Step 1: ECR (assume it exists, just build and push)
ECR_URI="${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"
echo "🔨 Step 1: Building Docker image..."
docker build -t $ECR_REPOSITORY_NAME:$IMAGE_TAG .
docker tag $ECR_REPOSITORY_NAME:$IMAGE_TAG $ECR_URI:$IMAGE_TAG
docker tag $ECR_REPOSITORY_NAME:$IMAGE_TAG $ECR_URI:latest

aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | docker login --username AWS --password-stdin $ECR_URI
docker push $ECR_URI:$IMAGE_TAG
docker push $ECR_URI:latest

VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --profile $AWS_PROFILE --region $AWS_REGION)
if [ "$VPC_ID" = "None" ] || [ -z "$VPC_ID" ]; then
    echo "No default VPC found! Falling back to first available VPC."
    VPC_ID=$(aws ec2 describe-vpcs --query "Vpcs[0].VpcId" --output text --profile $AWS_PROFILE --region $AWS_REGION)
fi

SUBNETS_TEXT=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text --profile $AWS_PROFILE --region $AWS_REGION)
# Convert tab-separated or space-separated strong to array
SUBNETS_ARRAY=($SUBNETS_TEXT)

ALB_SG_ID=$(aws ec2 describe-security-groups --group-names rise-alb-sg --profile $AWS_PROFILE --region $AWS_REGION --query "SecurityGroups[0].GroupId" --output text 2>/dev/null || true)
if [ -z "$ALB_SG_ID" ] || [ "$ALB_SG_ID" = "None" ]; then
    echo "Creating ALB SG..."
    ALB_SG_ID=$(aws ec2 create-security-group --group-name rise-alb-sg --description "ALB Security Group" --vpc-id $VPC_ID --profile $AWS_PROFILE --region $AWS_REGION --query "GroupId" --output text)
    aws ec2 authorize-security-group-ingress --group-id $ALB_SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0 --profile $AWS_PROFILE --region $AWS_REGION
fi

ECS_SG_ID=$(aws ec2 describe-security-groups --group-names rise-ecs-sg --profile $AWS_PROFILE --region $AWS_REGION --query "SecurityGroups[0].GroupId" --output text 2>/dev/null || true)
if [ -z "$ECS_SG_ID" ] || [ "$ECS_SG_ID" = "None" ]; then
    echo "Creating ECS SG..."
    ECS_SG_ID=$(aws ec2 create-security-group --group-name rise-ecs-sg --description "ECS Security Group" --vpc-id $VPC_ID --profile $AWS_PROFILE --region $AWS_REGION --query "GroupId" --output text)
    aws ec2 authorize-security-group-ingress --group-id $ECS_SG_ID --protocol tcp --port 8080 --source-group $ALB_SG_ID --profile $AWS_PROFILE --region $AWS_REGION
fi

TG_ARN=$(aws elbv2 describe-target-groups --names $TG_NAME --profile $AWS_PROFILE --region $AWS_REGION --query "TargetGroups[0].TargetGroupArn" --output text 2>/dev/null || true)
if [ -z "$TG_ARN" ] || [ "$TG_ARN" = "None" ]; then
    echo "Creating Target Group..."
    TG_ARN=$(aws elbv2 create-target-group --name $TG_NAME --protocol HTTP --port 8080 --vpc-id $VPC_ID --target-type ip --health-check-path "/_stcore/health" --health-check-protocol HTTP --health-check-interval-seconds 15 --health-check-timeout-seconds 5 --healthy-threshold-count 2 --unhealthy-threshold-count 3 --profile $AWS_PROFILE --region $AWS_REGION --query "TargetGroups[0].TargetGroupArn" --output text)
    aws elbv2 modify-target-group-attributes --target-group-arn $TG_ARN --attributes Key=stickiness.enabled,Value=true Key=stickiness.type,Value=lb_cookie --profile $AWS_PROFILE --region $AWS_REGION
fi

ALB_ARN=$(aws elbv2 describe-load-balancers --names $ALB_NAME --profile $AWS_PROFILE --region $AWS_REGION --query "LoadBalancers[0].LoadBalancerArn" --output text 2>/dev/null || true)
if [ -z "$ALB_ARN" ] || [ "$ALB_ARN" = "None" ]; then
    echo "Creating ALB..."
    ALB_ARN=$(aws elbv2 create-load-balancer --name $ALB_NAME --subnets "${SUBNETS_ARRAY[@]}" --security-groups $ALB_SG_ID --scheme internet-facing --type application --profile $AWS_PROFILE --region $AWS_REGION --query "LoadBalancers[0].LoadBalancerArn" --output text)
fi

LISTENER_ARN=$(aws elbv2 describe-listeners --load-balancer-arn $ALB_ARN --profile $AWS_PROFILE --region $AWS_REGION --query "Listeners[0].ListenerArn" --output text 2>/dev/null || true)
if [ -z "$LISTENER_ARN" ] || [ "$LISTENER_ARN" = "None" ]; then
    echo "Creating ALB Listener..."
    aws elbv2 create-listener --load-balancer-arn $ALB_ARN --protocol HTTP --port 80 --default-actions Type=forward,TargetGroupArn=$TG_ARN --profile $AWS_PROFILE --region $AWS_REGION
fi

aws ecs create-cluster --cluster-name $CLUSTER_NAME --profile $AWS_PROFILE --region $AWS_REGION >/dev/null

aws logs create-log-group --log-group-name /ecs/$TASK_FAMILY --profile $AWS_PROFILE --region $AWS_REGION 2>/dev/null || true

ROLE_NAME="ecsTaskExecutionRole"
ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT}:role/${ROLE_NAME}"
if ! aws iam get-role --role-name $ROLE_NAME --profile $AWS_PROFILE >/dev/null 2>&1; then
    cat > /tmp/ecs-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
    aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document file:///tmp/ecs-trust-policy.json --profile $AWS_PROFILE
    aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy --profile $AWS_PROFILE

    cat > /tmp/bedrock-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    }
  ]
}
EOF
    aws iam put-role-policy --role-name $ROLE_NAME --policy-name BedrockAccessPolicy --policy-document file:///tmp/bedrock-policy.json --profile $AWS_PROFILE
    sleep 5
fi

cat > /tmp/task-def.json << EOF
{
  "family": "$TASK_FAMILY",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "rise-container",
      "image": "$ECR_URI:$IMAGE_TAG",
      "portMappings": [
        {
          "containerPort": 8080,
          "hostPort": 8080,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {"name": "APP_ENV", "value": "production"},
        {"name": "AWS_REGION", "value": "$AWS_REGION"},
        {"name": "DEBUG", "value": "False"},
        {"name": "BEDROCK_MODEL_ID", "value": "$BEDROCK_MODEL_ID"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/$TASK_FAMILY",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "$ROLE_ARN",
  "taskRoleArn": "$ROLE_ARN"
}
EOF
TASK_DEF_ARN=$(aws ecs register-task-definition --cli-input-json file:///tmp/task-def.json --profile $AWS_PROFILE --region $AWS_REGION --query "taskDefinition.taskDefinitionArn" --output text)

SUBNETS_COMMA=$(IFS=,; echo "${SUBNETS_ARRAY[*]}")

if aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --profile $AWS_PROFILE --region $AWS_REGION | grep -q '"status": "ACTIVE"'; then
    echo "Updating ECS Service..."
    aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --task-definition $TASK_DEF_ARN --force-new-deployment --profile $AWS_PROFILE --region $AWS_REGION >/dev/null
else
    echo "Creating ECS Service..."
    aws ecs create-service --cluster $CLUSTER_NAME --service-name $SERVICE_NAME --task-definition $TASK_DEF_ARN --desired-count 1 --launch-type FARGATE --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS_COMMA],securityGroups=[$ECS_SG_ID],assignPublicIp=ENABLED}" --load-balancers "targetGroupArn=$TG_ARN,containerName=rise-container,containerPort=8080" --profile $AWS_PROFILE --region $AWS_REGION >/dev/null
fi

ALB_DNS=$(aws elbv2 describe-load-balancers --names $ALB_NAME --profile $AWS_PROFILE --region $AWS_REGION --query "LoadBalancers[0].DNSName" --output text)

echo "======================================================================"
echo "✅ ECS Deploy initiated!"
echo "🌐 URL: http://$ALB_DNS"
echo "It may take 3-5 minutes for ECS to provision the instance."
echo "======================================================================"
