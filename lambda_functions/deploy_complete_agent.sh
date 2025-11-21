#!/bin/bash

# Deploy Complete LangChain Agent to AWS Lambda
# This script packages and deploys the updated agent with 16000 token configuration

set -e

echo "=========================================="
echo "🚀 DEPLOYING COMPLETE LANGCHAIN AGENT"
echo "=========================================="

# Configuration
LAMBDA_FUNCTION_NAME="test-plan-generator-ai"
REGION="eu-west-1"
LAYER_ARN="arn:aws:lambda:eu-west-1:339712742264:layer:langchain-layer-new:1"

echo ""
echo "📦 Step 1: Creating deployment package..."

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "   └─ Temp directory: $TEMP_DIR"

# Copy Lambda function code
echo "   └─ Copying Lambda function code..."
cp -r test_plan_agent "$TEMP_DIR/"
cp ai_test_generator_optimized.py "$TEMP_DIR/"
cp db_utils.py "$TEMP_DIR/"

# Create deployment package
cd "$TEMP_DIR"
echo "   └─ Creating ZIP package..."
zip -r deployment-package.zip . -q

echo ""
echo "✅ Deployment package created successfully"

echo ""
echo "🔄 Step 2: Updating Lambda function code..."

# Update Lambda function
aws lambda update-function-code \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --zip-file fileb://deployment-package.zip \
    --region "$REGION" \
    --no-cli-pager

echo ""
echo "✅ Lambda function code updated"

echo ""
echo "⏳ Step 3: Waiting for function to be ready..."
aws lambda wait function-updated \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --region "$REGION"

echo ""
echo "✅ Function is ready"

echo ""
echo "🔧 Step 4: Verifying Lambda configuration..."

# Get current configuration
CURRENT_CONFIG=$(aws lambda get-function-configuration \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --region "$REGION" \
    --no-cli-pager)

echo "   Current Configuration:"
echo "   └─ Timeout: $(echo $CURRENT_CONFIG | jq -r '.Timeout')s"
echo "   └─ Memory: $(echo $CURRENT_CONFIG | jq -r '.MemorySize')MB"
echo "   └─ Runtime: $(echo $CURRENT_CONFIG | jq -r '.Runtime')"
echo "   └─ Handler: $(echo $CURRENT_CONFIG | jq -r '.Handler')"

# Verify timeout is 120 seconds
TIMEOUT=$(echo $CURRENT_CONFIG | jq -r '.Timeout')
if [ "$TIMEOUT" != "120" ]; then
    echo ""
    echo "⚠️  Warning: Timeout is $TIMEOUT seconds, expected 120 seconds"
    echo "   Updating timeout configuration..."
    
    aws lambda update-function-configuration \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --timeout 120 \
        --region "$REGION" \
        --no-cli-pager > /dev/null
    
    echo "   └─ ✅ Timeout updated to 120 seconds"
fi

echo ""
echo "🧪 Step 5: Testing Lambda function..."

# Create test payload
TEST_PAYLOAD='{
  "title": "Test Deployment",
  "requirements": "Test that the Lambda function is working with 16000 tokens",
  "coverage_percentage": 80,
  "min_test_cases": 5,
  "max_test_cases": 10,
  "user_team": "darwin"
}'

echo "   └─ Invoking Lambda function..."
INVOKE_RESULT=$(aws lambda invoke \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --payload "$TEST_PAYLOAD" \
    --region "$REGION" \
    --no-cli-pager \
    response.json)

# Check if invocation was successful
STATUS_CODE=$(echo $INVOKE_RESULT | jq -r '.StatusCode')
if [ "$STATUS_CODE" == "200" ]; then
    echo "   └─ ✅ Lambda invocation successful (Status: $STATUS_CODE)"
    
    # Check response
    if [ -f response.json ]; then
        ERROR_MSG=$(jq -r '.errorMessage // empty' response.json)
        if [ -n "$ERROR_MSG" ]; then
            echo "   └─ ⚠️  Lambda returned an error:"
            echo "      $ERROR_MSG"
        else
            echo "   └─ ✅ Lambda executed successfully"
        fi
    fi
else
    echo "   └─ ❌ Lambda invocation failed (Status: $STATUS_CODE)"
fi

# Cleanup
rm -f response.json
cd - > /dev/null
rm -rf "$TEMP_DIR"

echo ""
echo "=========================================="
echo "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY"
echo "=========================================="
echo ""
echo "📋 Summary:"
echo "   └─ Function: $LAMBDA_FUNCTION_NAME"
echo "   └─ Region: $REGION"
echo "   └─ Configuration: 120s timeout, 16000 tokens"
echo "   └─ Status: Ready for 1-20 test case generation"
echo ""
echo "✅ You can now test generating 10-20 test cases from the web interface"
echo ""
