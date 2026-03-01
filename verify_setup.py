#!/usr/bin/env python3
"""
RISE Setup Verification Script
Run this to verify Phase 1 setup is complete
"""

import sys
import os
from pathlib import Path

def check_mark(condition):
    return "✅" if condition else "❌"

def verify_setup():
    """Verify all Phase 1 setup requirements"""
    
    print("=" * 60)
    print("RISE Phase 1 Setup Verification")
    print("=" * 60)
    print()
    
    all_checks_passed = True
    
    # 1. Check Python version
    print("1. Python Version Check")
    python_version = sys.version_info
    python_ok = python_version >= (3, 9)
    print(f"   {check_mark(python_ok)} Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    if not python_ok:
        print("   ⚠️  Python 3.9+ required")
        all_checks_passed = False
    print()
    
    # 2. Check virtual environment
    print("2. Virtual Environment Check")
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"   {check_mark(in_venv)} Virtual environment active")
    if not in_venv:
        print("   ⚠️  Run: source venv/bin/activate")
        all_checks_passed = False
    print()
    
    # 3. Check required packages
    print("3. Required Packages Check")
    required_packages = {
        'strands': 'Strands Agents SDK',
        'streamlit': 'Streamlit',
        'boto3': 'AWS SDK',
        'pytest': 'Testing Framework'
    }
    
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - Not installed")
            all_checks_passed = False
    print()
    
    # 4. Check project structure
    print("4. Project Structure Check")
    required_dirs = ['agents', 'tools', 'ui', 'data', 'tests']
    for dir_name in required_dirs:
        exists = Path(dir_name).is_dir()
        print(f"   {check_mark(exists)} {dir_name}/")
        if not exists:
            all_checks_passed = False
    print()
    
    # 5. Check required files
    print("5. Required Files Check")
    required_files = [
        'app.py',
        'config.py',
        'requirements.txt',
        '.env.example',
        'README.md',
        'agents/orchestrator.py',
        'tests/test_setup.py'
    ]
    
    for file_name in required_files:
        exists = Path(file_name).is_file()
        print(f"   {check_mark(exists)} {file_name}")
        if not exists:
            all_checks_passed = False
    print()
    
    # 6. Check configuration
    print("6. Configuration Check")
    try:
        from config import Config
        print(f"   ✅ Config module loads")
        print(f"   ✅ App name: {Config.APP_NAME}")
        print(f"   ✅ Supported languages: {len(Config.SUPPORTED_LANGUAGES)}")
    except Exception as e:
        print(f"   ❌ Config error: {e}")
        all_checks_passed = False
    print()
    
    # 7. Check orchestrator
    print("7. Orchestrator Agent Check")
    try:
        from agents.orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        status = orchestrator.get_status()
        print(f"   ✅ Orchestrator initializes")
        print(f"   ✅ Model: {status['model_id']}")
        print(f"   ✅ Region: {status['region']}")
    except Exception as e:
        print(f"   ❌ Orchestrator error: {e}")
        all_checks_passed = False
    print()
    
    # 8. Run tests
    print("8. Test Suite Check")
    try:
        import pytest
        result = pytest.main(['-v', 'tests/test_setup.py', '--tb=no', '-q'])
        if result == 0:
            print(f"   ✅ All tests passing")
        else:
            print(f"   ❌ Some tests failing")
            all_checks_passed = False
    except Exception as e:
        print(f"   ❌ Test error: {e}")
        all_checks_passed = False
    print()
    
    # Final summary
    print("=" * 60)
    if all_checks_passed:
        print("✅ Phase 1 Setup Complete!")
        print()
        print("Next steps:")
        print("1. Copy .env.example to .env and add AWS credentials")
        print("2. Enable Amazon Bedrock model access")
        print("3. Run: streamlit run app.py")
        print("4. Proceed to Task 2: Set up core AWS services")
        return 0
    else:
        print("❌ Setup Incomplete")
        print()
        print("Please fix the issues above and run again.")
        return 1

if __name__ == "__main__":
    sys.exit(verify_setup())
