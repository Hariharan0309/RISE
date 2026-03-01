"""
Test basic project setup and configuration
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from agents.orchestrator import get_orchestrator

def test_config_loaded():
    """Test that configuration is loaded"""
    assert Config.APP_NAME == "RISE"
    assert Config.AWS_REGION is not None
    assert Config.BEDROCK_MODEL_ID is not None

def test_supported_languages():
    """Test that all required languages are configured"""
    expected_languages = ["en", "hi", "ta", "te", "kn", "bn", "gu", "mr", "pa"]
    
    for lang in expected_languages:
        assert lang in Config.SUPPORTED_LANGUAGES

def test_orchestrator_initialization():
    """Test that orchestrator can be initialized"""
    orchestrator = get_orchestrator()
    assert orchestrator is not None
    
    status = orchestrator.get_status()
    assert "agent_initialized" in status
    assert "aws_configured" in status

def test_project_structure():
    """Test that required directories exist"""
    required_dirs = ["agents", "tools", "ui", "data", "tests"]
    
    for dir_name in required_dirs:
        assert os.path.isdir(dir_name), f"Directory {dir_name} should exist"

def test_required_files():
    """Test that required files exist"""
    required_files = [
        "app.py",
        "config.py",
        "requirements.txt",
        ".env.example",
        "README.md"
    ]
    
    for file_name in required_files:
        assert os.path.isfile(file_name), f"File {file_name} should exist"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
