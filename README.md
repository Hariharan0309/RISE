# RISE - Rural Innovation and Sustainable Ecosystem

AI-Powered Farming Assistant built with AWS Strands Agents and Streamlit

## Overview

RISE is a comprehensive, voice-first AI assistant designed to empower smallholder farmers across rural India with practical intelligence to improve agricultural outcomes, market access, and sustainable practices.

## Features

- 🎤 Voice-first multilingual interface (9 Indic languages)
- 🌿 AI-powered crop disease and pest diagnosis
- 🌍 Soil analysis and crop recommendations
- ☁️ Weather-integrated smart farming alerts
- 💰 Real-time market intelligence and pricing
- 🤝 Community resource sharing and cooperative buying
- 📋 Government scheme navigation
- 💵 Financial planning and profitability calculators

## Technology Stack

- **AI Framework:** AWS Strands Agents SDK
- **Frontend:** Streamlit
- **AI/ML Services:** Amazon Bedrock (Claude 3 Sonnet)
- **Cloud Platform:** AWS (DynamoDB, S3, API Gateway, ECS for app; Lambdas optional)
- **Languages:** Python 3.13+

## Project Structure

```
RISE/
├── agents/                 # Strands agent implementations
├── tools/                  # Agent tools and utilities
├── ui/                     # Streamlit UI components
├── data/                   # Data storage
├── tests/                  # Test suite
├── infrastructure/         # AWS CDK infrastructure code
│   ├── stacks/             # CDK stack definitions
│   ├── app.py              # CDK application entry point
│   ├── aws_services.py     # AWS service utilities
│   ├── deploy.sh           # Deployment script
│   ├── verify_deployment.py # Infrastructure verification
│   └── README.md           # Infrastructure documentation
├── app.py                  # Main Streamlit application
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
└── .env.example           # Environment variables template
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd RISE
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your AWS credentials and configuration
```

Required environment variables:
- `AWS_REGION`: Your AWS region (e.g., us-east-1)
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `BEDROCK_MODEL_ID`: Amazon Bedrock model ID

### 5. Run the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## AWS Services Setup

RISE uses AWS CDK for infrastructure as code. All AWS resources are defined and deployed automatically.

### Quick Infrastructure Deployment

```bash
cd infrastructure
./deploy.sh
```

This will create:
- 6 DynamoDB tables with GSIs
- S3 bucket with lifecycle policies
- CloudFront CDN distribution
- API Gateway (REST + WebSocket)
- IAM roles for Bedrock access

### Detailed Infrastructure Setup

See [infrastructure/DEPLOYMENT_GUIDE.md](infrastructure/DEPLOYMENT_GUIDE.md) for comprehensive instructions.

### Amazon Bedrock Access

After infrastructure deployment, enable Bedrock model access:

1. Navigate to Amazon Bedrock console
2. Click "Model access" in the left sidebar
3. Click "Manage model access"
4. Enable:
   - ✅ Anthropic Claude 3 Sonnet
   - ✅ Amazon Nova (all variants)
5. Save changes and wait for approval

### Verify Infrastructure

```bash
cd infrastructure
python verify_deployment.py
```

This checks:
- ✅ All DynamoDB tables created
- ✅ S3 bucket configured
- ✅ Bedrock model access enabled
- ✅ Overall infrastructure status

### Lambdas and the Chatbot

- **Lambda functions are not deployed by default.** The CDK stack in `infrastructure/` creates DynamoDB, S3, API Gateway, CloudFront, and IAM roles (including a Bedrock role for future Lambdas), but it does **not** define or deploy the Lambda handler code in `tools/*_lambda.py` (e.g. `image_analysis_lambda`, `pest_analysis_lambda`, `soil_analysis_lambda`, `fertilizer_recommendation_lambda`, etc.).
- **The chatbot does not use those Lambdas.** The Strands orchestrator in `agents/orchestrator.py` uses Bedrock (ConverseStream) with **no tools registered** (`tools=[]`). Image analysis from the chat flow is a placeholder (Phase 3). All text chat is handled by the LLM only.
- **The Streamlit app uses in-process tools, not Lambdas.** For example, the image uploader (`ui/image_uploader.py`) uses `DiseaseIdentificationTools` directly in the same process and calls Bedrock from the app. So the current deployment (e.g. ECS or local Streamlit) does not require any Lambda functions to be deployed for the chatbot or image features to work.
- The `tools/*_lambda.py` modules are optional entry points for API Gateway, event-driven pipelines, or other serverless callers. If you want to expose those as HTTP APIs or event handlers, you would need to add Lambda resources to the CDK stack (or a separate stack) and deploy them.

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black .
```

## Implementation Phases

- ✅ **Phase 1:** Foundation & Strands Agents Setup
  - ✅ Task 1: Initialize project structure
  - ✅ Task 2: Set up core AWS services infrastructure
- ⏳ **Phase 2:** Voice & Multilingual Tools
- ⏳ **Phase 3:** AI-Powered Crop Diagnosis
- ⏳ **Phase 4:** Soil Intelligence & Recommendations
- ⏳ **Phase 5:** Weather Integration
- ⏳ **Phase 6:** Market Intelligence
- ⏳ **Phase 7:** Government Schemes
- ⏳ **Phase 8:** Financial Planning
- ⏳ **Phase 9:** Community Features
- ⏳ **Phase 10:** Resource Sharing System

## Contributing

This project is part of the AI for Bharat Hackathon. Contributions are welcome!

## License

See LICENSE file for details.

## Support

For issues and questions, please open a GitHub issue.

---

Built with ❤️ for Indian farmers using AWS Strands Agents
