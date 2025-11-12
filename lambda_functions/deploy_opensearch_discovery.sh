#!/bin/bash

# Script to deploy OpenSearch Index Discovery Lambda
# This Lambda discovers all indices in the OpenSearch cluster

echo "=========================================="
echo "  OpenSearch Index Discovery Deployment"
echo "=========================================="
echo ""

LAMBDA_NAME="opensearch-index-discovery"
REGION="eu-west-1"
RUNTIME="python3.12"
HANDLER="opensearch_index_discovery.lambda_handler"
TIMEOUT=60
MEMORY=512

# VPC Configuration (same as your OpenSearch)
# You need to get these values from your OpenSearch VPC configuration
# SUBNET_IDS="subnet-xxxxx,subnet-yyyyy"
# SECURITY_GROUP_IDS="sg-xxxxx"

echo "📦 Step 1: Creating deployment package..."
echo ""

# Create temporary directory
rm -rf temp_opensearch_discovery
mkdir -p temp_opensearch_discovery

# Copy Lambda function
cp opensearch_index_discovery.py temp_opensearch_discovery/

# Install dependencies
echo "📥 Installing dependencies..."
pip install opensearchpy requests-aws4auth -t temp_opensearch_discovery/ --quiet

# Create ZIP file
cd temp_opensearch_discovery
echo "🗜️  Creating ZIP file..."
zip -r ../opensearch_index_discovery.zip . -q
cd ..

echo "✅ Package created: opensearch_index_discovery.zip"
echo ""

# Check if Lambda exists
echo "🔍 Checking if Lambda function exists..."
if aws lambda get-function --function-name $LAMBDA_NAME --region $REGION 2>/dev/null; then
    echo "📝 Lambda exists, updating code..."
    aws lambda update-function-code \
        --function-name $LAMBDA_NAME \
        --zip-file fileb://opensearch_index_discovery.zip \
        --region $REGION
    
    echo "✅ Lambda code updated!"
else
    echo "⚠️  Lambda does not exist."
    echo ""
    echo "To create the Lambda, you need to:"
    echo "1. Get the VPC Subnet IDs from your OpenSearch configuration"
    echo "2. Get the Security Group IDs from your OpenSearch configuration"
    echo "3. Get the Lambda execution role ARN"
    echo ""
    echo "Then run:"
    echo ""
    echo "aws lambda create-function \\"
    echo "  --function-name $LAMBDA_NAME \\"
    echo "  --runtime $RUNTIME \\"
    echo "  --role YOUR_LAMBDA_ROLE_ARN \\"
    echo "  --handler $HANDLER \\"
    echo "  --zip-file fileb://opensearch_index_discovery.zip \\"
    echo "  --timeout $TIMEOUT \\"
    echo "  --memory-size $MEMORY \\"
    echo "  --region $REGION \\"
    echo "  --vpc-config SubnetIds=SUBNET_ID_1,SUBNET_ID_2,SecurityGroupIds=SG_ID"
    echo ""
fi

# Cleanup
echo ""
echo "🧹 Cleaning up..."
rm -rf temp_opensearch_discovery

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "To test the Lambda, run:"
echo "aws lambda invoke --function-name $LAMBDA_NAME --region $REGION output.json"
echo ""
