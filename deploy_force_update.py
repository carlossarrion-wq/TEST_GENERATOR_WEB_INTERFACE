import boto3
import time

# Force update Lambda function
lambda_client = boto3.client('lambda', region_name='eu-west-1')

print("🔄 Forcing Lambda to reload code...")
print("Step 1: Updating environment variable to force reload...")

# Update environment to force reload
response = lambda_client.update_function_configuration(
    FunctionName='test-plan-generator-plans-crud',
    Environment={
        'Variables': {
            'RDS_HOST': 'test-plan-generator-db.czuimyk2qu10.eu-west-1.rds.amazonaws.com',
            'KNOWLEDGE_BASE_ID': 'VH6SRH9ZNO',
            'RDS_DATABASE': 'testplangenerator',
            'RDS_PASSWORD': 'TempPassword123!',
            'RDS_PORT': '3306',
            'RDS_USER': 'admin',
            'BEDROCK_MODEL_ID': 'eu.anthropic.claude-haiku-4-5-20251001-v1:0',
            'FORCE_UPDATE': str(int(time.time()))  # Force cache invalidation
        }
    }
)

print(f"✅ Environment updated. Waiting for function to be ready...")
time.sleep(5)

print("Step 2: Redeploying code...")
with open('lambda_functions/ai_test_generator_langchain.zip', 'rb') as f:
    zip_content = f.read()

response = lambda_client.update_function_code(
    FunctionName='test-plan-generator-plans-crud',
    ZipFile=zip_content,
    Publish=True  # Publish new version
)

print(f"✅ Code updated. New version: {response['Version']}")
print(f"✅ CodeSha256: {response['CodeSha256']}")
print(f"✅ LastModified: {response['LastModified']}")
print("\n🎉 Lambda function forcefully updated!")
