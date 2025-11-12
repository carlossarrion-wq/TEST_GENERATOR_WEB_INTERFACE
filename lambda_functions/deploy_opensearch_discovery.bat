@echo off
REM Script to deploy OpenSearch Index Discovery Lambda (Windows version)

echo ==========================================
echo   OpenSearch Index Discovery Deployment
echo ==========================================
echo.

set LAMBDA_NAME=opensearch-index-discovery
set REGION=eu-west-1
set RUNTIME=python3.12
set HANDLER=opensearch_index_discovery.lambda_handler
set TIMEOUT=60
set MEMORY=512

echo Step 1: Creating deployment package...
echo.

REM Clean up previous builds
if exist temp_opensearch_discovery rmdir /s /q temp_opensearch_discovery
if exist opensearch_index_discovery.zip del opensearch_index_discovery.zip

REM Create temporary directory
mkdir temp_opensearch_discovery

REM Copy Lambda function
copy opensearch_index_discovery.py temp_opensearch_discovery\

REM Install dependencies
echo Installing dependencies...
pip install opensearchpy requests-aws4auth -t temp_opensearch_discovery\ --quiet

REM Create ZIP file
echo Creating ZIP file...
cd temp_opensearch_discovery
powershell Compress-Archive -Path * -DestinationPath ..\opensearch_index_discovery.zip -Force
cd ..

echo Package created: opensearch_index_discovery.zip
echo.

REM Check if Lambda exists and update
echo Checking if Lambda function exists...
aws lambda get-function --function-name %LAMBDA_NAME% --region %REGION% >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo Lambda exists, updating code...
    aws lambda update-function-code --function-name %LAMBDA_NAME% --zip-file fileb://opensearch_index_discovery.zip --region %REGION%
    echo Lambda code updated!
) else (
    echo.
    echo WARNING: Lambda does not exist.
    echo.
    echo To create the Lambda, you need to:
    echo 1. Get the VPC Subnet IDs from your OpenSearch configuration
    echo 2. Get the Security Group IDs from your OpenSearch configuration  
    echo 3. Get the Lambda execution role ARN
    echo.
    echo Then run:
    echo aws lambda create-function ^
    echo   --function-name %LAMBDA_NAME% ^
    echo   --runtime %RUNTIME% ^
    echo   --role YOUR_LAMBDA_ROLE_ARN ^
    echo   --handler %HANDLER% ^
    echo   --zip-file fileb://opensearch_index_discovery.zip ^
    echo   --timeout %TIMEOUT% ^
    echo   --memory-size %MEMORY% ^
    echo   --region %REGION% ^
    echo   --vpc-config SubnetIds=SUBNET_ID_1,SUBNET_ID_2,SecurityGroupIds=SG_ID
    echo.
)

REM Cleanup
echo.
echo Cleaning up...
rmdir /s /q temp_opensearch_discovery

echo.
echo ==========================================
echo   Deployment Complete!
echo ==========================================
echo.
echo To test the Lambda, run:
echo aws lambda invoke --function-name %LAMBDA_NAME% --region %REGION% output.json
echo.

pause
