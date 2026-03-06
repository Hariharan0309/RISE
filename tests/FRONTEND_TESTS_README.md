# RISE Frontend Testing Documentation

This document describes the frontend testing strategy for the RISE Streamlit application.

## Overview

The RISE frontend is built with **Streamlit** (Python web framework), not React. Therefore, our testing approach uses Python testing tools appropriate for Streamlit applications:

- **pytest** - Test framework
- **unittest.mock** - Mocking framework
- **Pillow** - Image processing for testing
- **Streamlit testing utilities** - Component testing

## Test Structure

```
tests/
├── test_frontend_app.py           # Main app.py tests
├── test_voice_recorder.py         # Voice recorder component tests
├── test_image_uploader.py         # Image uploader component tests
├── test_frontend_validation.py    # Form validation and session tests
├── run_frontend_tests.py          # Test runner script
└── FRONTEND_TESTS_README.md       # This file
```

## Test Categories

### 1. Application Tests (`test_frontend_app.py`)

Tests for the main Streamlit application (`app.py`):

#### App Initialization
- Language map completeness (9 Indic languages)
- Session state initialization
- Default values and data structures

#### Authentication Flow
- Valid authentication with proper credentials
- Invalid phone number rejection
- User ID generation from phone number
- Session creation after login

#### Chat Interface
- Chat history initialization
- Adding user messages
- Adding assistant messages
- Message ordering and timestamps
- Suggested questions functionality

#### Language Selection
- Language code mapping
- Language switching
- Default language (English)
- Language persistence in session

#### Session Management
- Session cleanup on logout
- Session ID format
- Session data persistence

#### Orchestrator Integration
- Orchestrator initialization
- Error handling when orchestrator unavailable
- Query processing structure

#### UI Components
- Feature badges content
- Tab structure (Chat, Diagnosis, History)
- Sidebar sections
- Responsive column layouts

#### Accessibility
- Multilingual labels
- Icon usage for visual clarity
- Help text availability

#### System Status
- Health check structure
- Status indicators (online/offline, agent active/inactive)

### 2. Voice Recorder Tests (`test_voice_recorder.py`)

Tests for voice recording and transcription (`ui/voice_recorder.py`):

#### Component Rendering
- English and Hindi labels
- Max duration parameter
- Waveform display toggle

#### Audio Data Handling
- Base64 encoding/decoding
- Component value structure
- Empty audio data handling

#### Recording Controls
- Recording state transitions (idle → recording → processing)
- Duration tracking
- Max duration enforcement
- Manual stop functionality

#### Audio Playback
- HTML audio player generation
- Supported audio formats (WAV, MP3, OGG)
- Playback controls

#### Waveform Visualization
- Waveform bar generation (30 bars)
- Animation during recording
- Reset after recording

#### Microphone Access
- Permission request handling
- Access denied error messages
- Microphone not available handling

#### Transcription Integration
- Successful transcription
- Transcription failure handling
- Confidence threshold validation

#### Language Support
- 9 supported languages
- Language-specific labels
- Fallback to English

#### Error Handling
- Audio processing errors
- Invalid audio format
- Empty recording
- Recording timeout

### 3. Image Uploader Tests (`test_image_uploader.py`)

Tests for image upload and disease diagnosis (`ui/image_uploader.py`):

#### Component Initialization
- Uploader creation with user ID and language
- Default language
- Disease tools initialization

#### Image Upload
- Supported formats (JPG, JPEG, PNG)
- File validation
- Image creation and reading

#### Image Preview
- Dimensions display
- File size calculation
- Format detection

#### Additional Context
- Crop type input
- Symptoms input
- Optional context handling

#### Image Analysis
- Successful analysis with diagnosis
- Poor image quality handling
- Analysis timeout

#### Diagnosis Display
- Severity indicators (🟢 low, 🟡 medium, 🟠 high, 🔴 critical)
- Confidence score display
- Disease list display
- Healthy crop detection
- Multiple issues warning

#### Treatment Recommendations
- Treatment structure (type, description)
- Treatment types (chemical, organic, cultural, biological)
- Preventive measures

#### Diagnosis History
- History filters (severity, status, type)
- Filter application
- Empty history handling

#### Statistics Summary
- Statistics structure
- High priority calculation
- Metrics display

#### Diagnosis Comparison
- Comparison selection (2+ diagnoses)
- Progress status (improving, stable, worsening)
- Severity change calculation
- Days elapsed calculation

#### Follow-up Tracking
- Status updates
- Notes addition
- Status icons

#### Report Generation
- Report structure
- Report content
- Download filename

#### Image Quality Validation
- Quality issues display
- Quality guidance
- Retry mechanism

### 4. Validation Tests (`test_frontend_validation.py`)

Tests for form validation and session management:

#### Input Validation
- Phone number validation (10 digits, numeric only)
- Name validation (non-empty)
- Location validation (optional)
- Crops input parsing

#### Input Sanitization
- XSS prevention
- Special character handling
- Whitespace trimming

#### Form Submission
- Complete form submission
- Partial form (optional fields empty)
- Invalid form rejection

#### Session State Management
- Session initialization
- Session after login
- Session cleanup
- Session persistence

#### Language Preferences
- Language selection
- Language persistence
- Invalid language fallback

#### Chat History Management
- Add message to history
- Chat history limit
- Clear chat history
- Message ordering

#### User Profile Management
- Profile creation
- Profile update
- Profile validation

#### Context Management
- Query context creation
- Context with history
- Empty context handling

#### Error Messages
- Validation error messages
- Multilingual error messages
- User-friendly errors

#### Data Persistence
- Session data structure
- Chat history persistence

#### Security Features
- User ID generation consistency
- Session ID uniqueness
- Sensitive data masking

## Running Tests

### Prerequisites

Install testing dependencies:
```bash
pip install -r tests/requirements-test.txt
```

### Run All Frontend Tests

```bash
python tests/run_frontend_tests.py
```

### Run with Coverage

```bash
python tests/run_frontend_tests.py --coverage
```

This generates:
- Console coverage report
- HTML coverage report in `tests/coverage_html_frontend/`

### Run Specific Test Pattern

```bash
# Run only app tests
python tests/run_frontend_tests.py -p app

# Run only voice recorder tests
python tests/run_frontend_tests.py -p voice

# Run only image uploader tests
python tests/run_frontend_tests.py -p image

# Run only validation tests
python tests/run_frontend_tests.py -p validation
```

### Run with Different Verbosity

```bash
# Quiet mode
python tests/run_frontend_tests.py -v 0

# Normal mode
python tests/run_frontend_tests.py -v 1

# Verbose mode (default)
python tests/run_frontend_tests.py -v 2
```

### Run Individual Test Files

```bash
# Using pytest
pytest tests/test_frontend_app.py -v
pytest tests/test_voice_recorder.py -v
pytest tests/test_image_uploader.py -v
pytest tests/test_frontend_validation.py -v

# Using unittest
python -m unittest tests.test_frontend_app
python -m unittest tests.test_voice_recorder
python -m unittest tests.test_image_uploader
python -m unittest tests.test_frontend_validation
```

### Run Specific Test Classes

```bash
pytest tests/test_frontend_app.py::TestAuthentication -v
pytest tests/test_voice_recorder.py::TestAudioDataHandling -v
pytest tests/test_image_uploader.py::TestImageAnalysis -v
```

### Run Specific Test Methods

```bash
pytest tests/test_frontend_app.py::TestAuthentication::test_valid_authentication -v
```

## Test Coverage Goals

### Target Metrics
- **Overall Coverage**: >85%
- **Function Coverage**: >90%
- **Branch Coverage**: >80%

### Coverage Areas

1. **Component Rendering**: All UI components render correctly
2. **User Interactions**: Form submissions, button clicks, input changes
3. **Data Validation**: Input validation and sanitization
4. **Session Management**: Session state and persistence
5. **Error Handling**: Graceful error handling and user feedback
6. **Accessibility**: Multilingual support, help text, icons
7. **Integration**: Component integration with backend services

## Testing Best Practices

### 1. Test Organization
- One test class per component or feature
- Descriptive test method names
- Group related tests together
- Test both success and failure cases

### 2. Mocking Strategy
- Mock external dependencies (AWS services, orchestrator)
- Use `unittest.mock.patch` for function mocking
- Create reusable mock fixtures
- Verify mock calls when appropriate

### 3. Test Data
- Use realistic test data
- Create helper functions for test data generation
- Test edge cases and boundary conditions
- Test with multilingual data

### 4. Assertions
- Use specific assertions (assertEqual, assertIn, etc.)
- Include descriptive assertion messages
- Test both positive and negative cases
- Verify data structures and types

### 5. Test Independence
- Each test should be independent
- Don't rely on test execution order
- Clean up resources after tests
- Use fresh mocks for each test

## Common Testing Patterns

### Testing Streamlit Components

```python
@patch('streamlit.text_input')
@patch('streamlit.button')
def test_form_submission(self, mock_button, mock_input):
    """Test form submission"""
    mock_input.return_value = "Test Input"
    mock_button.return_value = True
    
    # Test logic here
    assert mock_input.called
```

### Testing Session State

```python
@patch('streamlit.session_state')
def test_session_initialization(self, mock_session):
    """Test session state initialization"""
    mock_session.authenticated = False
    
    # Test logic
    assert mock_session.authenticated is False
```

### Testing Image Processing

```python
def test_image_upload(self):
    """Test image upload"""
    from PIL import Image
    import io
    
    # Create test image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes = img_bytes.getvalue()
    
    # Test with image bytes
    assert len(img_bytes) > 0
```

### Testing Audio Data

```python
def test_audio_encoding(self):
    """Test audio data encoding"""
    import base64
    
    audio_bytes = b'fake audio data'
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    # Verify encoding
    assert isinstance(audio_base64, str)
    
    # Verify can decode
    decoded = base64.b64decode(audio_base64)
    assert decoded == audio_bytes
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure parent directory is in Python path
   - Check all dependencies are installed

2. **Mock Failures**
   - Verify mock paths are correct
   - Check mock is applied before function call

3. **Streamlit Errors**
   - Some Streamlit features may not work in test environment
   - Mock Streamlit functions when necessary

4. **Image Processing Errors**
   - Ensure Pillow is installed
   - Use valid image formats (JPEG, PNG)

### Debug Mode

Enable verbose output:
```bash
python tests/run_frontend_tests.py -v 2
```

Run with pytest verbose mode:
```bash
pytest tests/test_frontend_app.py -vv
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Frontend Tests
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
      - name: Run frontend tests
        run: python tests/run_frontend_tests.py --coverage
```

## Contributing

### Adding New Tests

1. Create test file following naming convention: `test_frontend_*.py`
2. Organize tests into logical test classes
3. Use descriptive test method names
4. Add docstrings explaining what is being tested
5. Update this README with new test descriptions

### Test Naming Convention

```python
def test_<component>_<scenario>_<expected_result>(self):
    """Test <component> with <scenario> should <expected_result>"""
```

Examples:
- `test_authentication_valid_credentials_success`
- `test_voice_recorder_invalid_format_error`
- `test_image_uploader_poor_quality_rejection`

## Test Metrics

### Current Test Count
- **App Tests**: 50+ tests
- **Voice Recorder Tests**: 40+ tests
- **Image Uploader Tests**: 60+ tests
- **Validation Tests**: 50+ tests
- **Total**: 200+ frontend tests

### Test Execution Time
- Full suite: ~10-15 seconds
- Individual files: ~2-4 seconds each

## Future Enhancements

1. **Visual Regression Testing**: Screenshot comparison for UI changes
2. **Performance Testing**: Load time and responsiveness metrics
3. **Accessibility Testing**: WCAG compliance validation
4. **E2E Testing**: Full user workflow testing with Selenium
5. **Mobile Testing**: Responsive design validation on mobile viewports

## Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Pillow Documentation](https://pillow.readthedocs.io/)

## Support

For questions or issues with frontend tests:
1. Check this README for common patterns
2. Review existing test files for examples
3. Check test output for specific error messages
4. Ensure all dependencies are installed
