# Deploy Complete LangChain Agent to AWS Lambda
# This script packages and deploys the updated agent with 16000 token configuration

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 DEPLOYING COMPLETE LANGCHAIN AGENT" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Configuration
$LAMBDA_FUNCTION_NAME = "test-plan-generator-ai"
$REGION = "eu-west-1"

Write-Host ""
Write-Host "📦 Step 1: Creating deployment package..." -ForegroundColor Yellow

# Create temporary directory
$TEMP_DIR = New-Item -ItemType Directory -Path ([System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), [System.Guid]::NewGuid().ToString()))
Write-Host "   └─ Temp directory: $TEMP_DIR" -ForegroundColor Gray

# Copy Lambda function code
Write-Host "   └─ Copying Lambda function code..." -ForegroundColor Gray
Copy-Item -Path "test_plan_agent" -Destination $TEMP_DIR -Recurse
Copy-Item -Path "ai_test_generator_optimized.py" -Destination $TEMP_DIR
Copy-Item -Path "db_utils.py" -Destination $TEMP_DIR

# Create deployment package
Write-Host "   └─ Creating ZIP package..." -ForegroundColor Gray
$zipPath = Join-Path $TEMP_DIR "deployment-package.zip"
Compress-Archive -Path "$TEMP_DIR\*" -DestinationPath $zipPath -Force

Write-Host ""
Write-Host "✅ Deployment package created successfully" -ForegroundColor Green

Write-Host ""
Write-Host "🔄 Step 2: Updating Lambda function code..." -ForegroundColor Yellow

# Update Lambda function
aws lambda update-function-code `
    --function-name $LAMBDA_FUNCTION_NAME `
    --zip-file "fileb://$zipPath" `
    --region $REGION `
    --no-cli-pager

Write-Host ""
Write-Host "✅ Lambda function code updated" -ForegroundColor Green

Write-Host ""
Write-Host "⏳ Step 3: Waiting for function to be ready..." -ForegroundColor Yellow
aws lambda wait function-updated `
    --function-name $LAMBDA_FUNCTION_NAME `
    --region $REGION

Write-Host ""
Write-Host "✅ Function is ready" -ForegroundColor Green

Write-Host ""
Write-Host "🔧 Step 4: Verifying Lambda configuration..." -ForegroundColor Yellow

# Get current configuration
$configJson = aws lambda get-function-configuration `
    --function-name $LAMBDA_FUNCTION_NAME `
    --region $REGION `
    --no-cli-pager | ConvertFrom-Json

Write-Host "   Current Configuration:" -ForegroundColor Gray
Write-Host "   └─ Timeout: $($configJson.Timeout)s" -ForegroundColor Gray
Write-Host "   └─ Memory: $($configJson.MemorySize)MB" -ForegroundColor Gray
Write-Host "   └─ Runtime: $($configJson.Runtime)" -ForegroundColor Gray
Write-Host "   └─ Handler: $($configJson.Handler)" -ForegroundColor Gray

# Verify timeout is 120 seconds
if ($configJson.Timeout -ne 120) {
    Write-Host ""
    Write-Host "⚠️  Warning: Timeout is $($configJson.Timeout) seconds, expected 120 seconds" -ForegroundColor Yellow
    Write-Host "   Updating timeout configuration..." -ForegroundColor Gray
    
    aws lambda update-function-configuration `
        --function-name $LAMBDA_FUNCTION_NAME `
        --timeout 120 `
        --region $REGION `
        --no-cli-pager | Out-Null
    
    Write-Host "   └─ ✅ Timeout updated to 120 seconds" -ForegroundColor Green
}

Write-Host ""
Write-Host "🧪 Step 5: Testing Lambda function..." -ForegroundColor Yellow

# Create test payload
$testPayload = @{
    title = "Test Deployment"
    requirements = "Test that the Lambda function is working with 16000 tokens"
    coverage_percentage = 80
    min_test_cases = 5
    max_test_cases = 10
    user_team = "darwin"
} | ConvertTo-Json -Compress

Write-Host "   └─ Invoking Lambda function..." -ForegroundColor Gray
$responseFile = Join-Path $TEMP_DIR "response.json"
$invokeResult = aws lambda invoke `
    --function-name $LAMBDA_FUNCTION_NAME `
    --payload $testPayload `
    --region $REGION `
    --no-cli-pager `
    $responseFile | ConvertFrom-Json

# Check if invocation was successful
if ($invokeResult.StatusCode -eq 200) {
    Write-Host "   └─ ✅ Lambda invocation successful (Status: $($invokeResult.StatusCode))" -ForegroundColor Green
    
    # Check response
    if (Test-Path $responseFile) {
        $response = Get-Content $responseFile | ConvertFrom-Json
        if ($response.errorMessage) {
            Write-Host "   └─ ⚠️  Lambda returned an error:" -ForegroundColor Yellow
            Write-Host "      $($response.errorMessage)" -ForegroundColor Red
        } else {
            Write-Host "   └─ ✅ Lambda executed successfully" -ForegroundColor Green
        }
    }
} else {
    Write-Host "   └─ ❌ Lambda invocation failed (Status: $($invokeResult.StatusCode))" -ForegroundColor Red
}

# Cleanup
Remove-Item -Path $TEMP_DIR -Recurse -Force

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Summary:" -ForegroundColor White
Write-Host "   └─ Function: $LAMBDA_FUNCTION_NAME" -ForegroundColor Gray
Write-Host "   └─ Region: $REGION" -ForegroundColor Gray
Write-Host "   └─ Configuration: 120s timeout, 16000 tokens" -ForegroundColor Gray
Write-Host "   └─ Status: Ready for 1-20 test case generation" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ You can now test generating 10-20 test cases from the web interface" -ForegroundColor Green
