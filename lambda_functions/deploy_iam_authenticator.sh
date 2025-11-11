#!/bin/bash

# Deploy IAM Authenticator Lambda Function
# This script packages and deploys the IAM authentication Lambda

set -e  # Exit on error

echo "========================================="
echo "IAM Authenticator Lambda Deployment"
echo "========================================="
echo ""

# Configuration
FUNCTION_NAME="test-plan-generator-iam-auth"
REGION="eu-west-1"
RUNTIME="python3.11"
HANDLER="iam_authenticator.lambda_handler"
ROLE_NAME="test-plan-generator-iam-auth-role"
ZIP_FILE="iam_authenticator.zip"

echo "Configuration:"
echo "  Function Name: $FUNCTION_NAME"
echo "  Region: $REGION"
echo "  Runtime: $RUNTIME"
echo ""

# Step 1: Create deployment package
echo "Step 1: Creating deployment package..."
cd "$(dirname "$0")"

# Remove old zip if exists
if [ -f "$ZIP_FILE" ]; then
    rm "$ZIP_FILE"
    echo "  ✓ Removed old deployment package"
fi

# Create zip file
zip -q "$ZIP_FILE" iam_authenticator.py
echo "  ✓ Created $ZIP_FILE"
echo ""

# Step 2: Check if Lambda function exists
echo "Step 2: Checking if Lambda function exists..."
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &>/dev/null; then
    echo "  ✓ Function exists, updating code..."
    
    # Update function code
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$ZIP_FILE" \
        --region "$REGION" \
        --no-cli-pager
    
    echo "  ✓ Function code updated successfully"
else
    echo "  ✗ Function does not exist"
    echo ""
    echo "Creating new Lambda function..."
    echo ""
    echo "IMPORTANT: You need to create the IAM role first!"
    echo ""
    echo "Required IAM Role: $ROLE_NAME"
    echo "Required Permissions:"
    echo "  - sts:GetCallerIdentity"
    echo "  - sts:GetSessionToken"
    echo "  - logs:CreateLogGroup"
    echo "  - logs:CreateLogStream"
    echo "  - logs:PutLogEvents"
    echo ""
    echo "To create the role, run:"
    echo "  aws iam create-role --role-name $ROLE_NAME \\"
    echo "    --assume-role-policy-document file://iam-auth-trust-policy.json"
    echo ""
    echo "Then attach the necessary policies and run this script again."
    echo ""
    exit 1
fi

echo ""
echo "Step 3: Updating function configuration..."

# Update function configuration
aws lambda update-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --timeout 30 \
    --memory-size 256 \
    --region "$REGION" \
    --no-cli-pager \
    --environment "Variables={REGION=$REGION}" \
    > /dev/null

echo "  ✓ Configuration updated"
echo ""

# Step 4: Get function URL
echo "Step 4: Getting function information..."
FUNCTION_ARN=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --query 'Configuration.FunctionArn' --output text)
echo "  Function ARN: $FUNCTION_ARN"
echo ""

# Step 5: Check API Gateway integration
echo "Step 5: API Gateway Integration"
echo "  You need to create an API Gateway endpoint for this Lambda"
echo ""
echo "  Recommended setup:"
echo "    - API Type: REST API"
echo "    - Resource: /auth/iam-login"
echo "    - Method: POST"
echo "    - Integration: Lambda Function ($FUNCTION_NAME)"
echo "    - Enable CORS"
echo ""
echo "  After creating the API Gateway, update the frontend with the endpoint URL"
echo ""

echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Configure API Gateway endpoint (if not done)"
echo "2. Update frontend with API Gateway URL"
echo "3. Test the authentication flow"
echo ""
echo "To test locally:"
echo "  python3 iam_authenticator.py"
echo ""
