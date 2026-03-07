# Quick Deployment to AWS App Runner

## Ready to Deploy? Follow These Steps:

### 1. Verify Prerequisites ✅

```bash
# Check Docker
docker --version

# Check AWS credentials
aws sts get-caller-identity --profile AdministratorAccess-696874273327

# Check you're in the project directory
pwd  # Should show: .../RISE
```

### 2. Deploy with One Command 🚀

```bash
./deploy_apprunner.sh
```

This will:
- ✅ Create ECR repository
- ✅ Build Docker image
- ✅ Push to ECR
- ✅ Deploy to App Runner
- ✅ Provide your application URL

### 3. Wait for Deployment ⏳

The deployment takes approximately 3-5 minutes. You'll see:
```
====================================================================
  Deployment Complete!
====================================================================

🌐 Application URL: https://xxxxx.us-east-1.awsapprunner.com
```

### 4. Access Your Application 🌐

Once deployed, your RISE application will be available at the provided URL.

## What Gets Deployed?

- **Container**: Python 3.12 with Streamlit
- **Compute**: 1 vCPU, 2 GB RAM
- **Auto-scaling**: 1-10 instances based on traffic
- **Health checks**: Automatic monitoring
- **HTTPS**: Enabled by default
- **Logs**: CloudWatch Logs

## Estimated Cost

~$46-50/month for 24/7 operation with light traffic

## Troubleshooting

If deployment fails:

1. **Check Docker is running:**
   ```bash
   docker ps
   ```

2. **Verify AWS credentials:**
   ```bash
   aws sts get-caller-identity --profile AdministratorAccess-696874273327
   ```

3. **Check logs:**
   ```bash
   # View deployment script output
   # Check for error messages
   ```

4. **Manual deployment:**
   See `APPRUNNER_DEPLOYMENT_GUIDE.md` for step-by-step manual deployment

## After Deployment

### Monitor Your Service

```bash
# Get service status
aws apprunner list-services --region us-east-1 --profile AdministratorAccess-696874273327

# View logs
# Go to AWS Console > CloudWatch > Log groups > /aws/apprunner/rise-farming-assistant
```

### Update Your Application

To deploy updates:
```bash
# Make your code changes
# Then run the deployment script again
./deploy_apprunner.sh
```

App Runner will automatically deploy the new version with zero downtime.

## Need Help?

- **Full Guide**: See `APPRUNNER_DEPLOYMENT_GUIDE.md`
- **AWS Console**: https://console.aws.amazon.com/apprunner
- **CloudWatch Logs**: https://console.aws.amazon.com/cloudwatch

---

**Ready to deploy? Run:** `./deploy_apprunner.sh`
