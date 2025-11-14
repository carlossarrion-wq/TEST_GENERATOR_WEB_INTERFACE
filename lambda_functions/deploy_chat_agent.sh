#!/bin/bash

# Deploy Chat Agent Lambda Function
# This script creates and deploys the chat agent Lambda function to AWS

set -e  # Exit on error

echo "=========================================="
echo "🚀 DEPLOYING CHAT AGENT LAMBDA FUNCTION"
echo "=========================================="
echo ""

# Configuration
FUNCTION_NAME="chat-agent"
RUNTIME="python3.11"
HANDLER="chat_agent.lambda_handler"
TIMEOUT=30
MEMORY_SIZE=512
REGION="eu-west-1"
ZIP_FILE="chat_agent.zip"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} AWS CLI found"

# Check if we're in the lambda_functions directory
if [ ! -f "chat_agent.py" ]; then
    echo -e "${RED}❌ chat_agent.py not found. Please run this script from the lambda_functions directory.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} chat_agent.py found"
echo ""

# Step 1: Create ZIP file
echo "📦 Step 1: Creating deployment package..."
if [ -f "$ZIP_FILE" ]; then
    rm "$ZIP_FILE"
    echo "   Removed existing $ZIP_FILE"
fi

zip -q "$ZIP_FILE" chat_agent.py
echo -e "${GREEN}✓${NC} Created $ZIP_FILE"
echo ""

# Step 2: Check if function exists
echo "🔍 Step 2: Checking if Lambda function exists..."
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &> /dev/null; then
    echo -e "${YELLOW}⚠${NC}  Function $FUNCTION_NAME already exists"
    echo ""
    
    # Update existing function
    echo "📤 Step 3: Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$ZIP_FILE" \
        --region "$REGION" \
        --output json > /dev/null
    
    echo -e "${GREEN}✓${NC} Function code updated"
    
    # Update configuration
    echo "⚙️  Step 4: Updating function configuration..."
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --timeout "$TIMEOUT" \
        --memory-size "$MEMORY_SIZE" \
        --region "$REGION" \
        --output json > /dev/null
    
    echo -e "${GREEN}✓${NC} Function configuration updated"
else
    echo -e "${GREEN}✓${NC} Function does not exist, will create new one"
    echo ""
    
    # Get IAM role ARN
    echo "🔐 Step 3: Getting IAM role..."
    ROLE_NAME="lambda-execution-role"
    ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text 2>/dev/null || echo "")
    
    if [ -z "$ROLE_ARN" ]; then
        echo -e "${RED}❌ IAM role '$ROLE_NAME' not found.${NC}"
        echo ""
        echo "Please create the role first with the following policy:"
        echo ""
        cat << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:eu-west-1::foundation-model/eu.anthropic.claude-haiku-4-5-20251001-v1:0"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
EOF
        echo ""
        exit 1
    fi
    
    echo -e "${GREEN}✓${NC} Found IAM role: $ROLE_ARN"
    echo ""
    
    # Create new function
    echo "📤 Step 4: Creating new Lambda function..."
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --role "$ROLE_ARN" \
        --handler "$HANDLER" \
        --zip-file "fileb://$ZIP_FILE" \
        --timeout "$TIMEOUT" \
        --memory-size "$MEMORY_SIZE" \
        --region "$REGION" \
        --description "Interactive chat agent for test case management using Claude Haiku 4.5" \
        --output json > /dev/null
    
    echo -e "${GREEN}✓${NC} Lambda function created"
fi

echo ""

# Step 5: Get function info
echo "📋 Step 5: Getting function information..."
FUNCTION_ARN=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --query 'Configuration.FunctionArn' --output text)
LAST_MODIFIED=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --query 'Configuration.LastModified' --output text)

echo -e "${GREEN}✓${NC} Function deployed successfully"
echo ""

# Display summary
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "Function Name:    $FUNCTION_NAME"
echo "Function ARN:     $FUNCTION_ARN"
echo "Runtime:          $RUNTIME"
echo "Handler:          $HANDLER"
echo "Timeout:          ${TIMEOUT}s"
echo "Memory:           ${MEMORY_SIZE}MB"
echo "Region:           $REGION"
echo "Last Modified:    $LAST_MODIFIED"
echo ""

# Check if API Gateway integration exists
echo "🔍 Checking API Gateway integration..."
API_ID="2xlh113423"  # Your API Gateway ID
RESOURCE_PATH="/chat-agent"

# Try to find the resource
RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id "$API_ID" \
    --region "$REGION" \
    --query "items[?path=='$RESOURCE_PATH'].id" \
    --output text 2>/dev/null || echo "")

if [ -z "$RESOURCE_ID" ]; then
    echo -e "${YELLOW}⚠${NC}  API Gateway resource '$RESOURCE_PATH' not found"
    echo ""
    echo "Next steps:"
    echo "1. Create API Gateway resource: $RESOURCE_PATH"
    echo "2. Create POST method"
    echo "3. Integrate with Lambda: $FUNCTION_NAME"
    echo "4. Enable CORS"
    echo "5. Deploy API"
    echo ""
    echo "Or use AWS Console:"
    echo "https://console.aws.amazon.com/apigateway/home?region=$REGION#/apis/$API_ID/resources"
else
    echo -e "${GREEN}✓${NC} API Gateway resource found: $RESOURCE_ID"
    echo ""
    echo "API Endpoint:"
    echo "https://$API_ID.execute-api.$REGION.amazonaws.com/prod$RESOURCE_PATH"
fi

echo ""
echo "=========================================="
echo "📝 TESTING"
echo "=========================================="
echo ""
echo "Test locally:"
echo "  cd lambda_functions"
echo "  python chat_agent.py"
echo ""
echo "Test with AWS CLI:"
echo "  aws lambda invoke \\"
echo "    --function-name $FUNCTION_NAME \\"
echo "    --region $REGION \\"
echo "    --payload file://test_chat_payload.json \\"
echo "    response.json"
echo ""
echo "View logs:"
echo "  aws logs tail /aws/lambda/$FUNCTION_NAME --follow --region $REGION"
echo ""

# Cleanup
echo "🧹 Cleaning up..."
# Keep the ZIP file for reference
echo -e "${GREEN}✓${NC} Deployment package saved as: $ZIP_FILE"
echo ""

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
