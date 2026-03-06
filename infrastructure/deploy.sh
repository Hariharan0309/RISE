#!/bin/bash
# RISE Infrastructure Deployment Script

set -e

export AWS_PROFILE=AdministratorAccess-696874273327
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN

echo "🚀 RISE Infrastructure Deployment"
echo "=================================="

# Check if AWS CLI is configured
if ! aws sts get-caller-identity --profile AdministratorAccess-696874273327 &> /dev/null; then
    echo "❌ Error: AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Get AWS account and region
AWS_ACCOUNT=$(aws sts get-caller-identity --profile AdministratorAccess-696874273327 --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}

echo "📍 Deploying to Account: $AWS_ACCOUNT"
echo "📍 Region: $AWS_REGION"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing CDK dependencies..."
pip install -q -r requirements.txt

# Check if CDK is bootstrapped
echo "🔍 Checking CDK bootstrap status..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region $AWS_REGION &> /dev/null; then
    echo "⚙️  Bootstrapping CDK (first-time setup)..."
    cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION
else
    echo "✅ CDK already bootstrapped"
fi

# Synthesize CloudFormation template
echo "🔨 Synthesizing CloudFormation template..."
cdk synth

# Deploy the stack
echo "🚀 Deploying RISE infrastructure..."
cdk deploy --require-approval never

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Check AWS Console for deployed resources"
echo "  2. Note the API Gateway endpoint URLs"
echo "  3. Update .env file with resource names"
echo "  4. Configure Amazon Bedrock model access"
echo ""
