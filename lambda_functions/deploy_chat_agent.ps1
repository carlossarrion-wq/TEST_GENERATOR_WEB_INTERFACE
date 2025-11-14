# Deploy Chat Agent Lambda Function
# PowerShell script for Windows

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 DEPLOYING CHAT AGENT LAMBDA FUNCTION" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$FUNCTION_NAME = "chat-agent"
$RUNTIME = "python3.11"
$HANDLER = "chat_agent.lambda_handler"
$TIMEOUT = 30
$MEMORY_SIZE = 512
$REGION = "eu-west-1"
$ZIP_FILE = "chat_agent.zip"

# Check if AWS CLI is installed
try {
    aws --version | Out-Null
    Write-Host "✓ AWS CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI is not installed. Please install it first." -ForegroundColor Red
    exit 1
}

# Check if we're in the lambda_functions directory
if (-not (Test-Path "chat_agent.py")) {
    Write-Host "❌ chat_agent.py not found. Please run this script from the lambda_functions directory." -ForegroundColor Red
    exit 1
}

Write-Host "✓ chat_agent.py found" -ForegroundColor Green
Write-Host ""

# Step 1: Create ZIP file
Write-Host "📦 Step 1: Creating deployment package..." -ForegroundColor Yellow
if (Test-Path $ZIP_FILE) {
    Remove-Item $ZIP_FILE
    Write-Host "   Removed existing $ZIP_FILE"
}

# Use PowerShell's Compress-Archive
Compress-Archive -Path "chat_agent.py" -DestinationPath $ZIP_FILE -Force
Write-Host "✓ Created $ZIP_FILE" -ForegroundColor Green
Write-Host ""

# Step 2: Check if function exists
Write-Host "🔍 Step 2: Checking if Lambda function exists..." -ForegroundColor Yellow
$functionExists = $false
try {
    aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>$null | Out-Null
    $functionExists = $true
    Write-Host "⚠  Function $FUNCTION_NAME already exists" -ForegroundColor Yellow
} catch {
    Write-Host "✓ Function does not exist, will create new one" -ForegroundColor Green
}

Write-Host ""

if ($functionExists) {
    # Update existing function
    Write-Host "📤 Step 3: Updating existing Lambda function..." -ForegroundColor Yellow
    aws lambda update-function-code `
        --function-name $FUNCTION_NAME `
        --zip-file "fileb://$ZIP_FILE" `
        --region $REGION `
        --output json | Out-Null
    
    Write-Host "✓ Function code updated" -ForegroundColor Green
    
    # Update configuration
    Write-Host "⚙️  Step 4: Updating function configuration..." -ForegroundColor Yellow
    aws lambda update-function-configuration `
        --function-name $FUNCTION_NAME `
        --timeout $TIMEOUT `
        --memory-size $MEMORY_SIZE `
        --region $REGION `
        --output json | Out-Null
    
    Write-Host "✓ Function configuration updated" -ForegroundColor Green
} else {
    # Get IAM role ARN
    Write-Host "🔐 Step 3: Getting IAM role..." -ForegroundColor Yellow
    $ROLE_NAME = "lambda-execution-role"
    
    try {
        $ROLE_ARN = aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text 2>$null
        
        if ([string]::IsNullOrEmpty($ROLE_ARN)) {
            throw "Role not found"
        }
        
        Write-Host "✓ Found IAM role: $ROLE_ARN" -ForegroundColor Green
        Write-Host ""
        
        # Create new function
        Write-Host "📤 Step 4: Creating new Lambda function..." -ForegroundColor Yellow
        aws lambda create-function `
            --function-name $FUNCTION_NAME `
            --runtime $RUNTIME `
            --role $ROLE_ARN `
            --handler $HANDLER `
            --zip-file "fileb://$ZIP_FILE" `
            --timeout $TIMEOUT `
            --memory-size $MEMORY_SIZE `
            --region $REGION `
            --description "Interactive chat agent for test case management using Claude Haiku 4.5" `
            --output json | Out-Null
        
        Write-Host "✓ Lambda function created" -ForegroundColor Green
    } catch {
        Write-Host "❌ IAM role '$ROLE_NAME' not found." -ForegroundColor Red
        Write-Host ""
        Write-Host "Please create the role first with the following policy:" -ForegroundColor Yellow
        Write-Host @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": ["arn:aws:bedrock:eu-west-1::foundation-model/eu.anthropic.claude-haiku-4-5-20251001-v1:0"]
    },
    {
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
"@
        exit 1
    }
}

Write-Host ""

# Step 5: Get function info
Write-Host "📋 Step 5: Getting function information..." -ForegroundColor Yellow
$FUNCTION_ARN = aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Configuration.FunctionArn' --output text
$LAST_MODIFIED = aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Configuration.LastModified' --output text

Write-Host "✓ Function deployed successfully" -ForegroundColor Green
Write-Host ""

# Display summary
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Function Name:    $FUNCTION_NAME"
Write-Host "Function ARN:     $FUNCTION_ARN"
Write-Host "Runtime:          $RUNTIME"
Write-Host "Handler:          $HANDLER"
Write-Host "Timeout:          ${TIMEOUT}s"
Write-Host "Memory:           ${MEMORY_SIZE}MB"
Write-Host "Region:           $REGION"
Write-Host "Last Modified:    $LAST_MODIFIED"
Write-Host ""

# Check if API Gateway integration exists
Write-Host "🔍 Checking API Gateway integration..." -ForegroundColor Yellow
$API_ID = "2xlh113423"
$RESOURCE_PATH = "/api/chat-agent"

try {
    $RESOURCE_ID = aws apigateway get-resources `
        --rest-api-id $API_ID `
        --region $REGION `
        --query "items[?path=='$RESOURCE_PATH'].id" `
        --output text 2>$null
    
    if ([string]::IsNullOrEmpty($RESOURCE_ID)) {
        Write-Host "⚠  API Gateway resource '$RESOURCE_PATH' not found" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "1. Create API Gateway resource: $RESOURCE_PATH"
        Write-Host "2. Create POST method"
        Write-Host "3. Integrate with Lambda: $FUNCTION_NAME"
        Write-Host "4. Enable CORS"
        Write-Host "5. Deploy API"
        Write-Host ""
        Write-Host "Or use AWS Console:" -ForegroundColor Cyan
        Write-Host "https://console.aws.amazon.com/apigateway/home?region=$REGION#/apis/$API_ID/resources"
    } else {
        Write-Host "✓ API Gateway resource found: $RESOURCE_ID" -ForegroundColor Green
        Write-Host ""
        Write-Host "API Endpoint:"
        Write-Host "https://$API_ID.execute-api.$REGION.amazonaws.com/prod$RESOURCE_PATH"
    }
} catch {
    Write-Host "⚠  Could not check API Gateway integration" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "📝 TESTING" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test with AWS CLI:"
Write-Host "  aws lambda invoke ``"
Write-Host "    --function-name $FUNCTION_NAME ``"
Write-Host "    --region $REGION ``"
Write-Host "    --payload file://test_chat_payload.json ``"
Write-Host "    response.json"
Write-Host ""
Write-Host "View logs:"
Write-Host "  aws logs tail /aws/lambda/$FUNCTION_NAME --follow --region $REGION"
Write-Host ""

Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
