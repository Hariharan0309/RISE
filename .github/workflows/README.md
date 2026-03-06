# RISE CI/CD Pipeline Documentation

## Overview

The RISE platform uses GitHub Actions for continuous integration and continuous deployment (CI/CD). The pipeline implements automated testing, security scanning, and blue-green deployment strategy for zero-downtime releases.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CI/CD Pipeline Flow                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Code Push/PR                                               │
│       │                                                     │
│       ├──► Code Quality Checks (Black, Flake8, Pylint)     │
│       │                                                     │
│       ├──► Unit Tests (pytest with coverage)               │
│       │                                                     │
│       ├──► Security Scanning (Bandit, Safety)              │
│       │                                                     │
│       └──► Integration Tests (AWS services)                │
│                                                             │
│  [develop branch]                                           │
│       │                                                     │
│       ├──► Build Infrastructure (CDK synth)                │
│       │                                                     │
│       ├──► Deploy to Staging                               │
│       │                                                     │
│       └──► Smoke Tests                                     │
│                                                             │
│  [main branch]                                              │
│       │                                                     │
│       ├──► Build Infrastructure (CDK synth)                │
│       │                                                     │
│       ├──► Blue-Green Deployment                           │
│       │    ├─► Prepare Green Environment                   │
│       │    ├─► Deploy Green Stack                          │
│       │    ├─► Health Checks                               │
│       │    ├─► Gradual Traffic Switch (10→25→50→75→100%)  │
│       │    └─► Monitor Metrics                             │
│       │                                                     │
│       ├──► Post-Deployment Validation                      │
│       │    ├─► End-to-End Tests                            │
│       │    ├─► Verify CloudWatch Metrics                   │
│       │    └─► Send Notifications                          │
│       │                                                     │
│       └──► Cleanup Old Blue Environment                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Workflow Triggers

### Push Events
- **main branch**: Full production deployment with blue-green strategy
- **develop branch**: Staging deployment
- **feature/** branches**: Code quality and unit tests only

### Pull Request Events
- **To main**: All tests + integration tests
- **To develop**: Code quality + unit tests

## Pipeline Jobs

### 1. Code Quality Checks
**Purpose**: Ensure code meets quality standards

**Tools**:
- Black: Code formatting
- Flake8: Linting
- Pylint: Static analysis

**Runs on**: All branches

### 2. Unit Tests
**Purpose**: Validate individual components

**Tools**:
- pytest: Test runner
- pytest-cov: Coverage reporting
- codecov: Coverage tracking

**Coverage Target**: >80%

**Runs on**: All branches

### 3. Integration Tests
**Purpose**: Validate AWS service integrations

**Services Tested**:
- DynamoDB operations
- S3 file operations
- Lambda function invocations
- Bedrock API calls

**Runs on**: develop and main branches only

### 4. Security Scanning
**Purpose**: Identify security vulnerabilities

**Tools**:
- Bandit: Python security scanner
- Safety: Dependency vulnerability checker

**Runs on**: All branches

### 5. Build Infrastructure
**Purpose**: Synthesize CloudFormation templates

**Tool**: AWS CDK

**Outputs**: CloudFormation templates in cdk.out/

**Runs on**: develop and main branches

### 6. Deploy to Staging
**Purpose**: Deploy to staging environment for testing

**Environment**: staging.rise-farming.com

**Steps**:
1. Deploy CDK stacks
2. Run smoke tests
3. Validate deployment

**Runs on**: develop branch only

### 7. Deploy to Production (Blue-Green)
**Purpose**: Zero-downtime production deployment

**Environment**: rise-farming.com

**Strategy**: Blue-Green Deployment

**Steps**:
1. **Prepare**: Tag current environment as "blue"
2. **Deploy Green**: Deploy new version to "green" environment
3. **Health Checks**: Validate green environment health
4. **Traffic Switch**: Gradually shift traffic (10% → 25% → 50% → 75% → 100%)
5. **Monitor**: Watch metrics for 10 minutes
6. **Rollback**: Automatic rollback on failure

**Runs on**: main branch only

### 8. Post-Deployment Validation
**Purpose**: Validate production deployment

**Tests**:
- End-to-end user workflows
- CloudWatch metrics verification
- Performance benchmarks

**Runs on**: main branch after successful deployment

### 9. Cleanup Blue Environment
**Purpose**: Remove old blue environment after successful green deployment

**Wait Period**: 1 hour monitoring period

**Runs on**: main branch after validation

## Blue-Green Deployment Details

### Traffic Shift Strategy

The pipeline implements gradual traffic shifting to minimize risk:

1. **10% Traffic**: Initial canary deployment
   - Monitor for 1 minute
   - Check error rates and latency
   
2. **25% Traffic**: Expanded canary
   - Monitor for 1 minute
   - Validate metrics
   
3. **50% Traffic**: Half traffic
   - Monitor for 1 minute
   - Compare blue vs green performance
   
4. **75% Traffic**: Majority traffic
   - Monitor for 1 minute
   - Final validation
   
5. **100% Traffic**: Full cutover
   - Update Route53 DNS
   - Complete migration

### Health Check Criteria

Green environment must pass all checks:

- ✓ API health endpoint returns 200
- ✓ Database connectivity verified
- ✓ S3 bucket access confirmed
- ✓ Bedrock integration operational
- ✓ Voice services available
- ✓ Translation services working
- ✓ Response time < 3 seconds
- ✓ Error rate < 5%

### Automatic Rollback

Rollback triggers:
- Health check failure at any traffic percentage
- Error rate > 10%
- Latency p99 > 10 seconds
- Lambda throttles > 50
- API 5XX errors > 100

Rollback process:
1. Immediately switch 100% traffic back to blue
2. Update Route53 to blue environment
3. Send critical alert to team
4. Preserve green environment for debugging

## Monitoring During Deployment

### Metrics Tracked

**Application Metrics**:
- Error rate (%)
- Request latency (p50, p95, p99)
- Request count
- API 4XX/5XX errors

**Infrastructure Metrics**:
- CPU utilization (%)
- Memory utilization (%)
- Lambda errors and throttles
- DynamoDB throttles

**Thresholds**:
- Error rate: Warning at 5%, Critical at 10%
- Latency p95: Warning at 3s, Critical at 5s
- CPU: Warning at 80%
- Memory: Warning at 85%

### Alerting

**SNS Topic**: rise-deployment-alerts

**Alert Types**:
- Warning: Threshold exceeded but not critical
- Critical: Immediate action required
- Success: Deployment completed successfully

## Required GitHub Secrets

### Staging Environment
- `AWS_ACCESS_KEY_ID`: AWS access key for staging
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for staging

### Production Environment
- `AWS_ACCESS_KEY_ID_PROD`: AWS access key for production
- `AWS_SECRET_ACCESS_KEY_PROD`: AWS secret key for production

## Environment Variables

- `AWS_REGION`: ap-south-1 (Mumbai)
- `PYTHON_VERSION`: 3.11
- `NODE_VERSION`: 18

## Usage

### Deploy to Staging
```bash
git checkout develop
git add .
git commit -m "Your changes"
git push origin develop
```

The pipeline will automatically:
1. Run all tests
2. Deploy to staging
3. Run smoke tests

### Deploy to Production
```bash
git checkout main
git merge develop
git push origin main
```

The pipeline will automatically:
1. Run all tests
2. Deploy using blue-green strategy
3. Monitor deployment
4. Rollback on failure

### Manual Rollback
If you need to manually rollback:

```bash
python scripts/blue_green_deploy.py --environment production --action rollback
```

## Troubleshooting

### Pipeline Failures

**Code Quality Failure**:
- Run `black .` to format code
- Run `flake8 .` to check linting
- Fix reported issues

**Test Failure**:
- Run `pytest tests/ -v` locally
- Fix failing tests
- Ensure >80% coverage

**Deployment Failure**:
- Check CloudWatch logs
- Review health check output
- Verify AWS credentials
- Check CDK synth output

### Health Check Failures

**API Unreachable**:
- Verify security groups
- Check API Gateway configuration
- Validate Lambda function deployment

**Database Connection Failed**:
- Check DynamoDB table status
- Verify IAM permissions
- Check VPC configuration (if applicable)

**High Latency**:
- Review Lambda function logs
- Check DynamoDB capacity
- Verify CloudFront caching

## Best Practices

1. **Always test in staging first**: Merge to develop before main
2. **Monitor deployments**: Watch CloudWatch during production deployments
3. **Keep blue environment**: Don't cleanup immediately after deployment
4. **Review metrics**: Check post-deployment metrics before cleanup
5. **Document changes**: Include deployment notes in commit messages

## Support

For pipeline issues:
1. Check GitHub Actions logs
2. Review CloudWatch logs
3. Contact DevOps team
4. Create issue in repository

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Blue-Green Deployment Guide](https://docs.aws.amazon.com/whitepapers/latest/blue-green-deployments/)
