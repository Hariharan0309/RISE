# RISE Lambda Function Unit Tests

This directory contains comprehensive unit tests for all RISE Lambda functions, covering authentication, voice processing, AI integration, data validation, and error handling.

## Test Structure

```
tests/
├── test_lambda_functions.py      # Main Lambda function tests
├── test_authentication_lambda.py # Authentication and authorization tests
├── test_data_validation.py       # Data validation and transformation tests
├── test_error_handling.py        # Error handling and edge case tests
├── test_config.py                # Test configuration and utilities
├── run_tests.py                  # Test runner script
├── requirements-test.txt         # Testing dependencies
└── README.md                     # This file
```

## Test Categories

### 1. Authentication and Authorization Tests (`test_authentication_lambda.py`)

Tests for user authentication, session management, and access control:

- **User Authentication**: Login, token validation, credential verification
- **Session Management**: Session creation, validation, expiration handling
- **Permission Checking**: Role-based access control (farmer, expert, admin)
- **Token Handling**: JWT validation, expiration, refresh tokens
- **Security**: Invalid credentials, expired sessions, unauthorized access

### 2. Voice Processing Tests (`test_lambda_functions.py`)

Tests for voice-related Lambda functions:

- **Audio Upload**: File validation, S3 storage, size limits, format checking
- **Speech-to-Text**: Transcription accuracy, language detection, noise handling
- **Text-to-Speech**: Voice synthesis, language support, audio quality
- **Language Detection**: Multi-language support, confidence scoring
- **Error Handling**: Invalid audio, service failures, timeout scenarios

### 3. AI Integration Tests (`test_lambda_functions.py`)

Tests for AI-powered analysis functions:

- **Image Analysis**: Crop disease detection, confidence scoring, treatment recommendations
- **Soil Analysis**: Soil type classification, fertility assessment, NPK analysis
- **Pest Identification**: Pest species detection, lifecycle stage, IPM recommendations
- **Bedrock Integration**: Model invocation, response parsing, error handling
- **Quality Validation**: Image quality checks, blur detection, lighting analysis

### 4. Data Validation Tests (`test_data_validation.py`)

Tests for input validation and data transformation:

- **User ID Validation**: Format checking, character validation, length limits
- **Location Validation**: State/district validation, coordinate parsing
- **Content Type Validation**: MIME type checking, allowed formats
- **Base64 Validation**: Encoding validation, size limits, corruption detection
- **Soil Test Data**: pH validation, NPK level checking, organic matter validation
- **Text Sanitization**: XSS prevention, length limits, character filtering

### 5. Error Handling Tests (`test_error_handling.py`)

Tests for error scenarios and edge cases:

- **AWS Service Failures**: S3 unavailable, Bedrock throttling, DynamoDB errors
- **Network Issues**: Connection timeouts, endpoint failures, credential errors
- **Resource Limits**: Memory constraints, file size limits, concurrent requests
- **Data Corruption**: Invalid base64, corrupted images, malformed JSON
- **Timeout Scenarios**: Long-running operations, service timeouts
- **Concurrency**: Race conditions, simultaneous requests, cache consistency

## Running Tests

### Prerequisites

1. Install testing dependencies:
```bash
pip install -r tests/requirements-test.txt
```

2. Set up AWS credentials (for mocking):
```bash
export AWS_ACCESS_KEY_ID=testing
export AWS_SECRET_ACCESS_KEY=testing
export AWS_DEFAULT_REGION=us-east-1
```

### Basic Test Execution

Run all tests:
```bash
python tests/run_tests.py
```

Run with different verbosity levels:
```bash
python tests/run_tests.py -v 0  # Quiet
python tests/run_tests.py -v 1  # Normal
python tests/run_tests.py -v 2  # Verbose (default)
```

Run specific test pattern:
```bash
python tests/run_tests.py -p "authentication"
python tests/run_tests.py -p "voice"
python tests/run_tests.py -p "validation"
```

### Coverage Analysis

Run tests with coverage analysis:
```bash
python tests/run_tests.py --coverage
```

This generates:
- Console coverage report
- HTML coverage report in `tests/coverage_html/`

### Individual Test Files

Run specific test files:
```bash
python -m unittest tests.test_authentication_lambda
python -m unittest tests.test_data_validation
python -m unittest tests.test_error_handling
```

Run specific test classes:
```bash
python -m unittest tests.test_lambda_functions.TestAudioUploadLambda
python -m unittest tests.test_authentication_lambda.TestAuthenticationLambda
```

Run specific test methods:
```bash
python -m unittest tests.test_lambda_functions.TestAudioUploadLambda.test_valid_audio_upload
```

## Test Configuration

### Environment Variables

Tests use the following environment variables:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=testing
AWS_SECRET_ACCESS_KEY=testing
AWS_DEFAULT_REGION=us-east-1

# Service Configuration
S3_BUCKET=rise-test-bucket
DIAGNOSIS_TABLE=RISE-DiagnosisHistory-Test
FARM_DATA_TABLE=RISE-FarmData-Test
USER_PROFILES_TABLE=RISE-UserProfiles-Test

# Lambda Configuration
MAX_FILE_SIZE=10485760  # 10MB
MAX_IMAGE_SIZE=5242880  # 5MB
```

### Mock Services

Tests use `moto` library to mock AWS services:

- **S3**: File upload/download operations
- **DynamoDB**: Data storage and retrieval
- **Bedrock**: AI model invocations
- **Translate**: Text translation
- **Transcribe**: Speech-to-text
- **Polly**: Text-to-speech
- **Cognito**: User authentication

### Test Data

Common test data is defined in `test_config.py`:

```python
# Sample user data
TEST_USER_ID = 'test_farmer_001'
SAMPLE_LOCATION = {'state': 'Karnataka', 'district': 'Bangalore'}
SAMPLE_SOIL_DATA = {'ph': 6.5, 'nitrogen': 'medium'}

# Sample file data
SAMPLE_AUDIO_DATA = base64.b64encode(b'fake audio').decode('utf-8')
SAMPLE_IMAGE_DATA = base64.b64encode(b'fake image').decode('utf-8')
```

## Test Utilities

### Custom Assertions

```python
from tests.test_config import TestAssertions

# Assert Lambda response format
TestAssertions.assert_lambda_response(self, response, 200, True)

# Assert diagnosis result structure
TestAssertions.assert_diagnosis_result(self, result)

# Assert soil analysis result structure
TestAssertions.assert_soil_analysis_result(self, result)
```

### Event Builders

```python
from tests.test_config import TestEventBuilder

# Build test events
audio_event = TestEventBuilder.audio_upload_event()
image_event = TestEventBuilder.image_analysis_event(crop_type='wheat')
soil_event = TestEventBuilder.soil_analysis_event(analysis_type='test_data')
```

### Mock Responses

```python
from tests.test_config import TestConfig

# Create mock AWS responses
bedrock_response = TestConfig.create_mock_bedrock_response('disease')
translate_response = TestConfig.create_mock_translate_response('Hello', 'hi')
polly_response = TestConfig.create_mock_polly_response('Test text')
```

## Test Coverage Goals

### Target Coverage Metrics

- **Overall Coverage**: >90%
- **Function Coverage**: >95%
- **Branch Coverage**: >85%
- **Line Coverage**: >90%

### Coverage Areas

1. **Happy Path**: All successful operations
2. **Error Paths**: All error conditions and exceptions
3. **Edge Cases**: Boundary conditions, empty inputs, maximum limits
4. **Integration Points**: AWS service interactions, external APIs
5. **Security**: Authentication, authorization, input validation

## Continuous Integration

### GitHub Actions Integration

```yaml
name: Lambda Function Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt
      - name: Run tests
        run: python tests/run_tests.py --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: lambda-tests
        name: Lambda Function Tests
        entry: python tests/run_tests.py
        language: system
        pass_filenames: false
```

## Best Practices

### Test Organization

1. **One test class per Lambda function**
2. **Group related tests in methods**
3. **Use descriptive test method names**
4. **Include both positive and negative test cases**
5. **Test edge cases and boundary conditions**

### Test Data Management

1. **Use consistent test data across tests**
2. **Create reusable test fixtures**
3. **Mock external dependencies**
4. **Clean up resources after tests**
5. **Use deterministic test data**

### Error Testing

1. **Test all error conditions**
2. **Verify error messages and codes**
3. **Test timeout scenarios**
4. **Test resource exhaustion**
5. **Test concurrent access patterns**

### Performance Testing

1. **Test with realistic data sizes**
2. **Measure response times**
3. **Test memory usage**
4. **Test concurrent load**
5. **Profile critical paths**

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `tools/` directory is in Python path
2. **AWS Credentials**: Use test credentials, not real ones
3. **Mock Failures**: Verify moto library versions
4. **Timeout Issues**: Increase test timeouts for slow operations
5. **Memory Issues**: Use smaller test data for memory-constrained tests

### Debug Mode

Run tests with debug output:
```bash
python -m unittest tests.test_lambda_functions -v
```

Enable logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Isolation

Ensure tests are isolated:
- Use fresh mocks for each test
- Clean up resources in tearDown methods
- Don't rely on test execution order
- Use unique identifiers for test data

## Contributing

### Adding New Tests

1. **Create test class** for new Lambda function
2. **Add to test runner** in `run_tests.py`
3. **Update documentation** in this README
4. **Ensure coverage** meets targets
5. **Test error conditions** thoroughly

### Test Naming Convention

```python
def test_<function>_<scenario>_<expected_result>(self):
    """Test <function> with <scenario> should <expected_result>"""
```

Examples:
- `test_authenticate_user_valid_credentials_success`
- `test_upload_audio_invalid_format_error`
- `test_analyze_image_poor_quality_rejection`

### Code Review Checklist

- [ ] Tests cover happy path and error cases
- [ ] Test names are descriptive
- [ ] Mocks are properly configured
- [ ] Resources are cleaned up
- [ ] Coverage targets are met
- [ ] Documentation is updated