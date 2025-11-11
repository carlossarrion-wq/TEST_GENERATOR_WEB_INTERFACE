# IAM Authentication Deployment Guide

Complete guide for deploying real IAM authentication for the Test Plan Generator application.

## Overview

This guide will help you set up real AWS IAM authentication instead of the mockup login. The solution uses:
- **Lambda Function**: `iam_authenticator.py` - Handles authentication
- **API Gateway**: REST API endpoint for the frontend
- **AWS STS**: Generates temporary credentials
- **Frontend**: Updated to call real authentication endpoint

---

## Prerequisites

- AWS CLI configured with appropriate credentials
- Permissions to create Lambda functions, IAM roles, and API Gateway
- Account ID: `701055077130`
- Region: `eu-west-1`

---

## Step 1: Create IAM Role for Lambda

### 1.1 Create Trust Policy

Create file `iam-auth-trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### 1.2 Create the Role

```bash
aws iam create-role \
  --role-name test-plan-generator-iam-auth-role \
  --assume-role-policy-document file://iam-auth-trust-policy.json \
  --region eu-west-1
```

### 1.3 Create Permission Policy

Create file `iam-auth-permissions-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sts:GetCallerIdentity",
        "sts:GetSessionToken"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:eu-west-1:701055077130:log-group:/aws/lambda/test-plan-generator-iam-auth:*"
    }
  ]
}
```

### 1.4 Attach Policy to Role

```bash
aws iam put-role-policy \
  --role-name test-plan-generator-iam-auth-role \
  --policy-name iam-auth-permissions \
  --policy-document file://iam-auth-permissions-policy.json \
  --region eu-west-1
```

---

## Step 2: Deploy Lambda Function

### 2.1 Create Lambda Function

```bash
cd lambda_functions

# Create deployment package
zip iam_authenticator.zip iam_authenticator.py

# Create Lambda function
aws lambda create-function \
  --function-name test-plan-generator-iam-auth \
  --runtime python3.11 \
  --role arn:aws:iam::701055077130:role/test-plan-generator-iam-auth-role \
  --handler iam_authenticator.lambda_handler \
  --zip-file fileb://iam_authenticator.zip \
  --timeout 30 \
  --memory-size 256 \
  --region eu-west-1 \
  --environment "Variables={REGION=eu-west-1}"
```

### 2.2 Or Use Deployment Script

```bash
chmod +x deploy_iam_authenticator.sh
./deploy_iam_authenticator.sh
```

---

## Step 3: Create API Gateway

### 3.1 Create REST API

```bash
# Create API
API_ID=$(aws apigateway create-rest-api \
  --name "test-plan-generator-auth-api" \
  --description "Authentication API for Test Plan Generator" \
  --region eu-west-1 \
  --query 'id' \
  --output text)

echo "API ID: $API_ID"
```

### 3.2 Get Root Resource ID

```bash
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --region eu-west-1 \
  --query 'items[0].id' \
  --output text)

echo "Root Resource ID: $ROOT_ID"
```

### 3.3 Create /auth Resource

```bash
AUTH_RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part auth \
  --region eu-west-1 \
  --query 'id' \
  --output text)

echo "Auth Resource ID: $AUTH_RESOURCE_ID"
```

### 3.4 Create /auth/iam-login Resource

```bash
LOGIN_RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $AUTH_RESOURCE_ID \
  --path-part iam-login \
  --region eu-west-1 \
  --query 'id' \
  --output text)

echo "Login Resource ID: $LOGIN_RESOURCE_ID"
```

### 3.5 Create POST Method

```bash
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $LOGIN_RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE \
  --region eu-west-1
```

### 3.6 Create OPTIONS Method (for CORS)

```bash
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $LOGIN_RESOURCE_ID \
  --http-method OPTIONS \
  --authorization-type NONE \
  --region eu-west-1
```

### 3.7 Integrate Lambda with POST Method

```bash
# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function \
  --function-name test-plan-generator-iam-auth \
  --region eu-west-1 \
  --query 'Configuration.FunctionArn' \
  --output text)

# Create integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $LOGIN_RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
  --region eu-west-1
```

### 3.8 Grant API Gateway Permission to Invoke Lambda

```bash
aws lambda add-permission \
  --function-name test-plan-generator-iam-auth \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:eu-west-1:701055077130:$API_ID/*/*" \
  --region eu-west-1
```

### 3.9 Deploy API

```bash
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --region eu-west-1
```

### 3.10 Get API Endpoint URL

```bash
API_ENDPOINT="https://$API_ID.execute-api.eu-west-1.amazonaws.com/prod/auth/iam-login"
echo "API Endpoint: $API_ENDPOINT"
```

**Save this URL! You'll need it for the frontend configuration.**

---

## Step 4: Update Frontend

### 4.1 Update API Configuration

Edit `js/api-service.js` and add the authentication endpoint:

```javascript
const API_CONFIG = {
    // Existing endpoints...
    AUTH_IAM_LOGIN: 'https://YOUR_API_ID.execute-api.eu-west-1.amazonaws.com/prod/auth/iam-login'
};
```

### 4.2 Update Login Function

The `login.html` file needs to be updated to call the real API. The updated code is already in place, but ensure the API endpoint is configured correctly.

---

## Step 5: Test the Authentication

### 5.1 Test Lambda Locally

```bash
cd lambda_functions
python3 iam_authenticator.py
```

### 5.2 Test via API Gateway

```bash
curl -X POST \
  https://YOUR_API_ID.execute-api.eu-west-1.amazonaws.com/prod/auth/iam-login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test-user",
    "password": "test-password"
  }'
```

### 5.3 Test from Frontend

1. Open the application in a browser
2. Enter IAM username and password
3. Click "Sign In with IAM"
4. Check browser console for API calls and responses

---

## Step 6: Configure CORS (if needed)

If you encounter CORS errors, configure CORS on API Gateway:

```bash
# Enable CORS for the resource
aws apigateway put-method-response \
  --rest-api-id $API_ID \
  --resource-id $LOGIN_RESOURCE_ID \
  --http-method POST \
  --status-code 200 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Origin": true}' \
  --region eu-west-1

# Update integration response
aws apigateway put-integration-response \
  --rest-api-id $API_ID \
  --resource-id $LOGIN_RESOURCE_ID \
  --http-method POST \
  --status-code 200 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Origin": "'\'*\'"}' \
  --region eu-west-1

# Redeploy
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --region eu-west-1
```

---

## Troubleshooting

### Lambda Execution Errors

Check CloudWatch Logs:
```bash
aws logs tail /aws/lambda/test-plan-generator-iam-auth --follow --region eu-west-1
```

### API Gateway 403 Errors

Verify Lambda permissions:
```bash
aws lambda get-policy \
  --function-name test-plan-generator-iam-auth \
  --region eu-west-1
```

### CORS Issues

- Ensure OPTIONS method is configured
- Check response headers include `Access-Control-Allow-Origin: *`
- Verify preflight requests are handled correctly

---

## Security Considerations

⚠️ **IMPORTANT SECURITY NOTES:**

1. **This is a simplified implementation** - In production, you should:
   - Use AWS Cognito for user management
   - Implement proper password hashing
   - Add rate limiting
   - Use HTTPS only
   - Implement MFA

2. **Never expose IAM credentials** directly in the frontend

3. **Use temporary credentials** (STS tokens) with limited permissions

4. **Implement proper session management** with token expiration

5. **Add logging and monitoring** for security events

---

## Next Steps

1. ✅ Deploy Lambda function
2. ✅ Create API Gateway endpoint
3. ✅ Update frontend configuration
4. ⏳ Test authentication flow
5. ⏳ Monitor CloudWatch logs
6. ⏳ Implement additional security measures

---

## Support

For issues or questions:
- Check CloudWatch Logs
- Review API Gateway execution logs
- Test Lambda function independently
- Verify IAM permissions

---

## Quick Reference

**Lambda Function:** `test-plan-generator-iam-auth`  
**IAM Role:** `test-plan-generator-iam-auth-role`  
**API Gateway:** `test-plan-generator-auth-api`  
**Endpoint:** `/auth/iam-login`  
**Region:** `eu-west-1`  
**Account:** `701055077130`
