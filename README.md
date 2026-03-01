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
- **Cloud Platform:** AWS (Lambda, DynamoDB, S3, API Gateway)
- **Languages:** Python 3.13+

## Project Structure

```
RISE/
├── agents/                 # Strands agent implementations
├── tools/                  # Agent tools and utilities
├── ui/                     # Streamlit UI components
├── data/                   # Data storage
├── tests/                  # Test suite
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

### Amazon Bedrock Access

1. Navigate to Amazon Bedrock console
2. Request model access for Claude 3 Sonnet
3. Wait for approval (usually instant for most regions)

### DynamoDB Tables

Tables will be created automatically on first use:
- RISE-UserProfiles
- RISE-FarmData
- RISE-DiagnosisHistory
- RISE-ResourceSharing
- RISE-BuyingGroups
- RISE-ResourceBookings

### S3 Bucket

Create an S3 bucket for storing images and documents:
```bash
aws s3 mb s3://rise-application-data --region us-east-1
```

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

- ✅ **Phase 1:** Foundation & Strands Agents Setup (Current)
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
