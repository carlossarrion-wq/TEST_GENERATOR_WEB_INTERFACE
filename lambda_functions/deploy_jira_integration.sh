#!/bin/bash

# Deploy Jira Integration Lambda Function
# This script deploys the Lambda function that fetches real Jira issues

set -e

echo "=========================================="
echo "Deploying Jira Integration Lambda Function"
echo "=========================================="

FUNCTION_NAME="jira-integration"
REGION="eu-west-1"
ROLE_ARN="arn:aws:iam::339712742264:role/lambda-execution-role"
RUNTIME="python3.11"
HANDLER="jira_integration.lambda_handler"
TIMEOUT=30
MEMORY=512

# Create deployment package
echo "Creating deployment package..."
rm -f jira_integration.zip

# Install dependencies
echo "Installing dependencies..."
pip install --target ./package requests boto3 -q

# Create zip with dependencies
cd package
zip -r ../jira_integration.zip . -q
cd ..

# Add Lambda function code
zip -g jira_integration.zip jira_integration.py -q

echo "Deployment package created: jira_integration.zip"

# Check if function exists
echo "Checking if Lambda function exists..."
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "Function exists. Updating..."
    
    # Update function code
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://jira_integration.zip \
        --region $REGION
    
    echo "Waiting for function update to complete..."
    aws lambda wait function-updated --function-name $FUNCTION_NAME --region $REGION
    
    # Update function configuration
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --timeout $TIMEOUT \
        --memory-size $MEMORY \
        --environment "Variables={JIRA_SECRET_NAME=prod/jira/credentials}" \
        --region $REGION
    
    echo "Function updated successfully!"
else
    echo "Function does not exist. Creating..."
    
    # Create function
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --role $ROLE_ARN \
        --handler $HANDLER \
        --zip-file fileb://jira_integration.zip \
        --timeout $TIMEOUT \
        --memory-size $MEMORY \
        --environment "Variables={JIRA_SECRET_NAME=prod/jira/credentials}" \
        --region $REGION
    
    echo "Function created successfully!"
fi

# Get function ARN
FUNCTION_ARN=$(aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Configuration.FunctionArn' --output text)
echo "Function ARN: $FUNCTION_ARN"

# Add API Gateway permissions (if not already added)
echo "Adding API Gateway invoke permissions..."
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id apigateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --region $REGION 2>/dev/null || echo "Permission already exists"

# Clean up
echo "Cleaning up..."
rm -rf package
rm -f jira_integration.zip

echo ""
echo "=========================================="
echo "Deployment completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Configure Jira credentials in AWS Secrets Manager:"
echo "   Secret name: prod/jira/credentials"
echo "   Secret value: {\"jiraUrl\": \"https://csarrion.atlassian.net\", \"jiraEmail\": \"your-email@example.com\", \"jiraApiToken\": \"your-api-token\"}"
echo ""
echo "2. Add Lambda to API Gateway:"
echo "   - Create resource: /api/jira"
echo "   - Create POST method"
echo "   - Integration type: Lambda Function"
echo "   - Lambda Function: $FUNCTION_NAME"
echo "   - Enable CORS"
echo ""
echo "3. Deploy API Gateway changes"
echo ""
