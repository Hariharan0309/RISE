# RISE Integration Tests

## Overview

This document describes the comprehensive integration tests for the RISE (Rural Innovation and Sustainable Ecosystem) farming assistant application. These tests verify that all AWS services work together correctly and that end-to-end user workflows function as expected.

## Test Coverage

### 1. API Gateway to Lambda Integration (`TestAPIGatewayLambdaIntegration`)

Tests the integration between API Gateway and Lambda functions for major endpoints:

- **test_voice_query_endpoint_integration**: Tests voice transcription API endpoint
  - Verifies API Gateway event structure
  - Tests Lambda invocation with voice data
  - Validates response format and status codes

- **test_image_diagnosis_endpoint_integration**: Tests crop disease diagnosis API endpoint
  - Verifies image upload through API Gateway
  - Tests Lambda invocation with image data
  - Validates diagnosis response structure

### 2. Lambda to DynamoDB Integration (`TestLambdaDynamoDBIntegration`)

Tests CRUD operations between Lambda functions and DynamoDB tables:

- **test_create_user_profile**: Tests user profile creation
  - Validates user data structure
  - Tests DynamoDB put_item operation
  - Verifies data persistence

- **test_store_diagnosis_history**: Tests diagnosis history storage
  - Validates diagnosis data structure
  - Tests storing diagnosis results
  - Verifies metadata storage

- **test_query_user_diagnosis_history**: Tests querying diagnosis history
  - Tests Global Secondary Index (GSI) queries
  - Validates query results
  - Tests pagination support

### 3. Lambda to S3 Integration (`TestLambdaS3Integration`)

Tests file upload and retrieval operations with S3:

- **test_upload_crop_image**: Tests crop image upload
  - Validates image data upload
  - Tests metadata attachment
  - Verifies content type settings

- **test_upload_audio_file**: Tests audio file upload
  - Validates audio data upload
  - Tests WAV format handling
  - Verifies S3 key structure

- **test_retrieve_image_with_presigned_url**: Tests presigned URL generation
  - Validates URL generation
  - Tests expiration settings
  - Verifies secure access

### 4. AWS AI Service Integrations (`TestAWSServiceIntegrations`)

Tests integration with AWS AI/ML services:

- **test_bedrock_multimodal_analysis**: Tests Amazon Bedrock
  - Validates multimodal image analysis
  - Tests Claude 3 Sonnet model invocation
  - Verifies disease identification response

- **test_translate_service_integration**: Tests Amazon Translate
  - Validates Hindi to English translation
  - Tests language code handling
  - Verifies translation accuracy

- **test_transcribe_service_integration**: Tests Amazon Transcribe
  - Validates audio transcription job creation
  - Tests job status monitoring
  - Verifies transcription completion

- **test_polly_service_integration**: Tests Amazon Polly
  - Validates text-to-speech synthesis
  - Tests Indic language voice (Aditi)
  - Verifies audio stream generation

### 5. End-to-End Workflows (`TestEndToEndWorkflows`)

Tests complete user workflows across multiple services:

- **test_voice_query_workflow**: Tests complete voice query flow
  - Audio upload to S3
  - Transcription with Amazon Transcribe
  - Translation with Amazon Translate
  - Voice response generation with Amazon Polly
  - Validates entire pipeline integration

## Running the Tests

### Prerequisites

```bash
# Install test dependencies
pip install -r requirements-test.txt
```

### Run All Integration Tests

```bash
# From RISE directory
python -m unittest tests.test_integration -v

# Or from tests directory
cd tests
python -m unittest test_integration -v
```

### Run Specific Test Classes

```bash
# Test API Gateway integration only
python -m unittest tests.test_integration.TestAPIGatewayLambdaIntegration -v

# Test DynamoDB integration only
python -m unittest tests.test_integration.TestLambdaDynamoDBIntegration -v

# Test S3 integration only
python -m unittest tests.test_integration.TestLambdaS3Integration -v

# Test AWS AI services only
python -m unittest tests.test_integration.TestAWSServiceIntegrations -v

# Test end-to-end workflows only
python -m unittest tests.test_integration.TestEndToEndWorkflows -v
```

### Run Specific Tests

```bash
# Test voice query endpoint
python -m unittest tests.test_integration.TestAPIGatewayLambdaIntegration.test_voice_query_endpoint_integration -v

# Test Bedrock integration
python -m unittest tests.test_integration.TestAWSServiceIntegrations.test_bedrock_multimodal_analysis -v
```

## Test Architecture

### Mocking Strategy

The integration tests use Python's `unittest.mock` library to mock AWS service calls. This approach:

- **Avoids actual AWS costs**: No real AWS resources are created or used
- **Ensures test reliability**: Tests don't depend on external services
- **Enables fast execution**: Tests run in milliseconds
- **Supports CI/CD**: Tests can run in any environment without AWS credentials

### Test Structure

Each test follows this pattern:

1. **Setup**: Mock AWS clients and services
2. **Execute**: Call the function/service being tested
3. **Verify**: Assert expected behavior and responses
4. **Cleanup**: Automatic cleanup via mocks

## Integration Test Scenarios

### Scenario 1: Voice Query Processing

```
User speaks query → API Gateway → Lambda → Transcribe → Translate → Bedrock → Polly → Response
```

**Tested Components:**
- API Gateway event handling
- Lambda function invocation
- S3 audio storage
- Transcribe job management
- Translate text conversion
- Bedrock AI analysis
- Polly voice synthesis

### Scenario 2: Image Diagnosis

```
User uploads image → API Gateway → Lambda → S3 → Bedrock → DynamoDB → Response
```

**Tested Components:**
- API Gateway image handling
- Lambda function invocation
- S3 image storage
- Bedrock multimodal analysis
- DynamoDB diagnosis storage
- Presigned URL generation

### Scenario 3: Market Data Retrieval

```
User requests prices → API Gateway → Lambda → DynamoDB → Cache → Response
```

**Tested Components:**
- API Gateway request handling
- Lambda function invocation
- DynamoDB query operations
- User profile retrieval
- Location-based filtering

## Error Handling Tests

The integration tests also cover error scenarios:

- Service unavailability
- Invalid input data
- Network timeouts
- Permission errors
- Resource not found errors

## Performance Considerations

Integration tests are designed to:

- Execute quickly (< 1 second total)
- Run in parallel when possible
- Minimize resource usage
- Support CI/CD pipelines

## Future Enhancements

Planned additions to integration tests:

1. **Real AWS Integration Tests**: Optional tests that use actual AWS services
2. **Load Testing**: Performance tests with concurrent requests
3. **Chaos Engineering**: Tests with simulated failures
4. **Security Testing**: Authentication and authorization tests
5. **Data Validation**: Schema validation for all API responses

## Troubleshooting

### Common Issues

**Issue**: Tests not discovered
```bash
# Solution: Ensure you're in the correct directory
cd RISE
python -m unittest discover -s tests -p "test_*.py" -v
```

**Issue**: Import errors
```bash
# Solution: Install dependencies
pip install -r tests/requirements-test.txt
```

**Issue**: Mock not working
```bash
# Solution: Check patch decorator targets
# Ensure you're patching where the object is used, not where it's defined
```

## Best Practices

1. **Keep tests independent**: Each test should be able to run in isolation
2. **Use descriptive names**: Test names should clearly describe what they test
3. **Mock external dependencies**: Never make real AWS calls in unit/integration tests
4. **Verify all assertions**: Each test should have clear assertions
5. **Clean up resources**: Use setUp/tearDown for test fixtures

## Contributing

When adding new integration tests:

1. Follow the existing test structure
2. Add tests for both success and failure cases
3. Update this README with new test descriptions
4. Ensure tests run quickly (< 100ms per test)
5. Use meaningful assertions with clear error messages

## Related Documentation

- [Testing Strategy](./README.md)
- [Lambda Functions](../tools/)
- [Infrastructure](../infrastructure/)
- [API Documentation](../docs/API.md)

## Contact

For questions about integration tests, contact the RISE development team.
