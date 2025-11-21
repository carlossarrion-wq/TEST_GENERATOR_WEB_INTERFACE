#!/bin/bash

# Deploy the fixed async Lambda function
# This script replaces the current Lambda code with the async-fixed version

set -e

echo "🚀 Deploying Fixed Async Lambda Function"
echo "========================================"

FUNCTION_NAME="test-plan-generator-ai"
REGION="eu-west-1"

# Step 1: Backup current version
echo "📦 Step 1: Backing up current version..."
cp ai_test_generator_optimized.py ai_test_generator_optimized.backup.py
echo "✅ Backup created: ai_test_generator_optimized.backup.py"

# Step 2: Replace with fixed version
echo "🔄 Step 2: Replacing with fixed async version..."
cp ai_test_generator_async_fixed.py ai_test_generator_optimized.py
echo "✅ File replaced"

# Step 3: Create deployment package
echo "📦 Step 3: Creating deployment package..."
cd ..
zip -r lambda_functions/ai_test_generator_optimized.zip lambda_functions/ai_test_generator_optimized.py lambda_functions/db_utils.py lambda_functions/test_plan_agent/ -x "*.pyc" -x "*__pycache__*" -x "*.backup.py"
cd lambda_functions
echo "✅ Deployment package created"

# Step 4: Deploy to AWS Lambda
echo "🚀 Step 4: Deploying to AWS Lambda..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://ai_test_generator_optimized.zip \
    --region $REGION \
    --no-cli-pager

echo "⏳ Waiting for Lambda update to complete..."
aws lambda wait function-updated \
    --function-name $FUNCTION_NAME \
    --region $REGION

echo ""
echo "✅ DEPLOYMENT SUCCESSFUL!"
echo "========================================"
echo "Function: $FUNCTION_NAME"
echo "Region: $REGION"
echo ""
echo "🔍 Key Changes:"
echo "  - Async invocation using Lambda client"
echo "  - Immediate task_id return (no 30s timeout)"
echo "  - Background processing with 120s timeout"
echo "  - True async architecture"
echo ""
echo "📊 Verify deployment:"
echo "  aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Configuration.[LastModified,State,LastUpdateStatus]'"
echo ""
