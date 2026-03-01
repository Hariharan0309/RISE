# MissionAI Farmer Agent

A voice-first, multimodal AI agent system designed to democratize advanced AI technology for rural Indian farmers. The system provides intelligent assistance across the entire farming lifecycle—from crop diagnosis to market selling to financial planning—through voice interaction in vernacular languages (Kannada, English, Hindi).

## Overview

MissionAI aims to deliver:
- **20-40% income rise** through intelligent decision support
- **20-30% reduction in pesticide use** through precise diagnosis and recommendations
- **Zero literacy barrier** with full voice interaction
- **Hyper-local intelligence** with location and time-specific advice

## Features

### Core Capabilities
- 🎤 **Voice-First Interaction**: Speak in Kannada, English, or Hindi
- 📸 **Multimodal Crop Diagnosis**: Upload crop images for instant disease identification
- 🌱 **Soil Analysis**: Get soil type classification and crop recommendations
- 🌦️ **Weather-Based Advice**: Receive proactive, hyper-local farming tips
- 💰 **Market Intelligence**: Real-time crop prices and marketplace access
- 🏛️ **Government Schemes**: Navigate schemes and check eligibility
- 📊 **Financial Planning**: Calculate costs, profits, and compare crop options
- 👥 **Community Forum**: Connect with local farmers and share experiences

### Specialized Agents
- **Manager Agent**: Central orchestrator for routing and coordination
- **Disease Diagnosis Agent**: Multimodal crop disease analysis
- **Soil Analysis Agent**: Soil classification and recommendations
- **Weather Advisor Agent**: Weather forecasts and farming activity timing
- **Market Price Agent**: Price comparison and marketplace facilitation
- **Schemes Navigator Agent**: Government scheme awareness and eligibility
- **Finance Calculator Agent**: Cost estimation and profitability analysis
- **Community Advisor Agent**: Local farmer knowledge and peer support

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Farmer User                            │
│                   (Voice/Image Input)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Streamlit UI                              │
│              (Mobile-Responsive Interface)                  │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
             ▼                                ▼
┌────────────────────────┐        ┌──────────────────────────┐
│   Amazon Transcribe    │        │      Image Storage       │
│   (Speech-to-Text)     │        │         (S3)             │
└────────────┬───────────┘        └──────────┬───────────────┘
             │                                │
             └────────────┬───────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Manager Agent                            │
│              (Intent Analysis & Routing)                    │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──────────┬──────────┬──────────┬──────────┐
             ▼          ▼          ▼          ▼          ▼
┌──────────────┐ ┌──────────┐ ┌─────────┐ ┌────────┐ ┌────────┐
│   Disease    │ │   Soil   │ │ Weather │ │ Market │ │Schemes │
│  Diagnosis   │ │ Analysis │ │ Advisor │ │  Price │ │Navigator│
└──────┬───────┘ └────┬─────┘ └────┬────┘ └───┬────┘ └───┬────┘
       │              │            │           │          │
       └──────────────┴────────────┴───────────┴──────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────┐
│              Amazon Bedrock (Claude 3.5 Sonnet)             │
│                    + AWS Services                           │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│         Amazon Polly (Text-to-Speech) + Translate           │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Audio Response                           │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

- **Agent Framework**: Strands Agents SDK (Python)
- **AI Model**: Amazon Bedrock - Claude 3.5 Sonnet / Sonnet 4
- **Voice Input**: Amazon Transcribe (Kannada, English, Hindi)
- **Voice Output**: Amazon Polly (Text-to-Speech)
- **Translation**: Amazon Translate
- **Frontend**: Streamlit (Mobile-responsive)
- **Image Processing**: PIL/Pillow
- **Storage**: Amazon S3
- **Testing**: pytest, hypothesis (property-based testing)

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- AWS Account with access to:
  - Amazon Bedrock (Claude models)
  - Amazon Transcribe
  - Amazon Polly
  - Amazon Translate
  - Amazon S3
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd missionai-farmer-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure AWS credentials**
   
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your AWS credentials:
   ```
   AWS_ACCESS_KEY_ID=your_access_key_here
   AWS_SECRET_ACCESS_KEY=your_secret_key_here
   AWS_DEFAULT_REGION=us-east-1
   ```

5. **Set up AWS services**
   
   - Enable Amazon Bedrock and request access to Claude models
   - Create an S3 bucket for image uploads
   - Ensure IAM permissions for Transcribe, Polly, and Translate

6. **Prepare mock data** (for development)
   ```bash
   # Mock data files will be created in the data/ directory
   # These include government schemes, market prices, and community posts
   ```

### Running the Application

1. **Start the Streamlit app**
   ```bash
   streamlit run ui/streamlit_app.py
   ```

2. **Access the application**
   
   Open your browser and navigate to `http://localhost:8501`

3. **For mobile testing**
   
   Use the network URL provided by Streamlit (e.g., `http://192.168.1.x:8501`)

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run only unit tests
pytest -m "not property_test"

# Run only property-based tests
pytest -m property_test

# Run specific test file
pytest tests/test_manager_agent.py
```

## Project Structure

```
missionai-farmer-agent/
├── agents/                 # Specialized agent implementations
│   ├── manager_agent.py
│   ├── disease_diagnosis_agent.py
│   ├── soil_analysis_agent.py
│   ├── weather_advisor_agent.py
│   ├── market_price_agent.py
│   ├── schemes_navigator_agent.py
│   ├── finance_calculator_agent.py
│   └── community_advisor_agent.py
├── tools/                  # Custom tool functions
│   ├── aws_services.py
│   ├── financial_tools.py
│   ├── market_tools.py
│   ├── weather_tools.py
│   └── community_tools.py
├── ui/                     # Streamlit frontend
│   └── streamlit_app.py
├── tests/                  # Unit and property-based tests
│   ├── test_manager_agent.py
│   ├── test_disease_diagnosis.py
│   ├── test_financial_tools.py
│   └── ...
├── data/                   # Mock data files
│   ├── schemes.json
│   ├── market_prices.json
│   ├── forum_posts.json
│   └── disease_database.json
├── .env.example           # Example environment variables
├── .gitignore            # Git ignore rules
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Usage Examples

### Voice Interaction
1. Click the "Speak" button
2. Speak your question in Kannada, English, or Hindi
3. The system transcribes and processes your request
4. Click "Listen" to hear the response

### Crop Disease Diagnosis
1. Navigate to the "Diagnose" tab
2. Upload a photo of your diseased crop
3. Optionally specify the crop type
4. Receive instant diagnosis with treatment recommendations

### Market Price Query
1. Navigate to the "Market" tab
2. Ask "What is the price of tomatoes in my area?"
3. View prices from multiple nearby markets
4. Create listings to sell your produce

### Financial Planning
1. Navigate to the "Finance" tab
2. Enter crop details, area, and expected prices
3. Get cost breakdown and profit projections
4. Compare multiple crop options

## Configuration

### AWS Service Configuration

Edit `.env` to customize AWS service settings:

```env
# Use specific Bedrock model
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# Configure S3 bucket
AWS_S3_BUCKET=your-bucket-name

# Set Polly voices for each language
AWS_POLLY_VOICE_ID_ENGLISH=Aditi
AWS_POLLY_VOICE_ID_HINDI=Aditi
AWS_POLLY_VOICE_ID_KANNADA=Aditi
```

### Feature Flags

Enable or disable features:

```env
ENABLE_OFFLINE_MODE=True
ENABLE_COMMUNITY_FORUM=True
ENABLE_VOICE_INPUT=True
```

### Mock Data (Development)

Use mock APIs during development:

```env
USE_MOCK_WEATHER_API=True
USE_MOCK_MARKET_API=True
```

## Troubleshooting

### AWS Credentials Issues
- Verify your AWS credentials are correct in `.env`
- Ensure IAM user has necessary permissions
- Check AWS region is supported for all services

### Bedrock Access
- Request access to Claude models in AWS Console
- Wait for approval (can take 1-2 business days)
- Verify model ID matches available models

### Voice Input Not Working
- Check microphone permissions in browser
- Ensure HTTPS or localhost (required for audio recording)
- Verify Amazon Transcribe supports your language code

### Image Upload Failures
- Check S3 bucket exists and is accessible
- Verify IAM permissions for S3 PutObject
- Ensure image size is under 5MB

### Slow Response Times
- Check AWS region latency
- Consider using mock APIs for development
- Enable caching for repeated queries

## Cost Estimation

Approximate AWS costs for 1000 monthly active users:

- **Amazon Bedrock (Claude)**: $50-100/month
- **Amazon Transcribe**: $20-40/month
- **Amazon Polly**: $10-20/month
- **Amazon Translate**: $5-10/month
- **Amazon S3**: $5-10/month

**Total**: ~$90-180/month

Costs vary based on usage patterns. Use mock APIs during development to minimize costs.

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions:
- Create an issue in the repository
- Contact: [Add contact information]

## Acknowledgments

- Built with Strands Agents SDK
- Powered by Amazon Bedrock and AWS AI Services
- Designed for rural Indian farmers

---

**Note**: This is a prototype system. Always verify AI recommendations with local agricultural experts before making critical farming decisions.
