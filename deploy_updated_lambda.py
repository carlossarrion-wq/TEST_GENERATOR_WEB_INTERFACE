"""
Script to deploy the updated Lambda function with correct OpenSearch indices
"""
import subprocess
import sys
import os

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode == 0

def main():
    print("="*80)
    print("Deploying Updated Lambda Function")
    print("="*80)
    
    # Change to lambda_functions directory
    lambda_dir = "lambda_functions"
    
    print("\n📦 Step 1: Creating deployment package...")
    if not run_command("python ../create_langchain_zip.py", cwd=lambda_dir):
        print("❌ Failed to create deployment package")
        return False
    
    print("\n🚀 Step 2: Updating Lambda function code...")
    zip_file = os.path.join(lambda_dir, "ai_test_generator_optimized.zip")
    
    cmd = f'aws lambda update-function-code --function-name test-plan-generator-ai --zip-file fileb://{zip_file} --region eu-west-1'
    if not run_command(cmd):
        print("❌ Failed to update Lambda function")
        return False
    
    print("\n✅ Lambda function updated successfully!")
    print("\n" + "="*80)
    print("Deployment Complete!")
    print("="*80)
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
