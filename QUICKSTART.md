# RISE Quick Start Guide

## ✅ Phase 1 Complete: Foundation Setup

Congratulations! The RISE project foundation has been successfully initialized with Strands Agents SDK and Streamlit.

## What's Been Set Up

### 1. Project Structure
```
RISE/
├── agents/                 # Strands agent implementations
│   ├── __init__.py
│   └── orchestrator.py    # Main orchestrator agent
├── tools/                  # Agent tools (ready for Phase 2)
│   └── __init__.py
├── ui/                     # Streamlit UI components
├── data/                   # Data storage
├── tests/                  # Test suite
│   ├── __init__.py
│   └── test_setup.py      # Setup verification tests
├── app.py                  # Main Streamlit application
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
└── README.md              # Project documentation
```

### 2. Dependencies Installed
- ✅ strands-agents (1.28.0) - AI agent framework
- ✅ strands-agents-tools (0.2.21) - Agent tools library
- ✅ streamlit (1.54.0) - Web frontend
- ✅ boto3 (1.42.59) - AWS SDK
- ✅ pytest (9.0.2) - Testing framework
- ✅ black (26.1.0) - Code formatter

### 3. Virtual Environment
- ✅ Python 3.13.2 virtual environment created
- ✅ All dependencies installed in isolated environment

### 4. Configuration
- ✅ Environment variable template (.env.example)
- ✅ Centralized configuration module (config.py)
- ✅ Support for 9 Indic languages configured

### 5. Basic Agent Structure
- ✅ Orchestrator agent skeleton created
- ✅ AWS Bedrock integration prepared
- ✅ System prompt defined

## Next Steps

### 1. Configure AWS Credentials

Copy the environment template and add your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add:
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
```

### 2. Enable Amazon Bedrock Access

1. Go to AWS Console → Amazon Bedrock
2. Navigate to "Model access"
3. Request access to "Claude 3 Sonnet"
4. Wait for approval (usually instant)

### 3. Run the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run Streamlit app
streamlit run app.py
```

The app will open at `http://localhost:8501`

### 4. Run Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_setup.py -v
```

### 5. Code Formatting

```bash
# Format all Python files
black .

# Check formatting without changes
black . --check
```

## Verification Checklist

Run these commands to verify everything is working:

```bash
# 1. Check Python version
python --version  # Should be 3.13+

# 2. Verify virtual environment
which python  # Should point to venv/bin/python

# 3. Check installed packages
pip list | grep strands

# 4. Run tests
pytest tests/test_setup.py -v

# 5. Start Streamlit (Ctrl+C to stop)
streamlit run app.py
```

## What's Working Now

✅ Project structure initialized
✅ Virtual environment configured
✅ Dependencies installed
✅ Basic Streamlit UI running
✅ Configuration management
✅ Orchestrator agent skeleton
✅ Test suite passing

## What's Coming Next (Phase 2)

⏳ Voice processing tools (Amazon Transcribe)
⏳ Text-to-speech tools (Amazon Polly)
⏳ Translation tools (Amazon Translate)
⏳ Multilingual support implementation
⏳ Conversation context management

## Troubleshooting

### Issue: Import errors
**Solution:** Make sure virtual environment is activated:
```bash
source venv/bin/activate
```

### Issue: AWS credentials not found
**Solution:** Copy .env.example to .env and add your credentials

### Issue: Streamlit won't start
**Solution:** Check if port 8501 is available:
```bash
lsof -i :8501
```

### Issue: Tests failing
**Solution:** Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## Resources

- [Strands Agents Documentation](https://github.com/awslabs/strands-agents)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Project Spec](.kiro/specs/rise-farming-assistant/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the test output: `pytest tests/ -v`
3. Check the logs when running Streamlit
4. Refer to the spec documents in `.kiro/specs/rise-farming-assistant/`

---

**Status:** Phase 1 Complete ✅
**Next Task:** Task 2 - Set up core AWS services infrastructure
