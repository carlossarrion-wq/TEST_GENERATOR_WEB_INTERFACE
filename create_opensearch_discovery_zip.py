"""
Script to create OpenSearch Discovery Lambda deployment package
"""

import os
import shutil
import zipfile
import subprocess
import sys

def create_deployment_package():
    """Create deployment package for OpenSearch Discovery Lambda"""
    
    print("=" * 80)
    print("Creating OpenSearch Discovery Lambda Package")
    print("=" * 80)
    print()
    
    # Configuration
    temp_dir = "temp_opensearch_discovery"
    zip_filename = "opensearch_index_discovery.zip"
    lambda_file = "lambda_functions/opensearch_index_discovery.py"
    
    # Clean up previous builds
    print("🧹 Cleaning up previous builds...")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    if os.path.exists(zip_filename):
        os.remove(zip_filename)
    
    # Create temp directory
    print("📁 Creating temporary directory...")
    os.makedirs(temp_dir)
    
    # Copy Lambda function
    print("📄 Copying Lambda function...")
    shutil.copy(lambda_file, os.path.join(temp_dir, "opensearch_index_discovery.py"))
    
    # Install dependencies
    print("📦 Installing dependencies...")
    print("   - opensearchpy")
    print("   - requests-aws4auth")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "opensearchpy", "requests-aws4auth",
            "-t", temp_dir,
            "--quiet"
        ])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("⚠️  Continuing without dependencies (they might already be in Lambda layer)")
    
    # Create ZIP file
    print("🗜️  Creating ZIP file...")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
                
    file_size = os.path.getsize(zip_filename) / (1024 * 1024)  # Convert to MB
    print(f"✅ ZIP file created: {zip_filename} ({file_size:.2f} MB)")
    
    # Clean up temp directory
    print("🧹 Cleaning up temporary files...")
    shutil.rmtree(temp_dir)
    
    print()
    print("=" * 80)
    print("Package created successfully!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Create the Lambda function with:")
    print()
    print("aws lambda create-function \\")
    print("  --function-name opensearch-index-discovery \\")
    print("  --runtime python3.12 \\")
    print("  --role arn:aws:iam::701055077130:role/TestPlanGeneratorLambdaRole \\")
    print("  --handler opensearch_index_discovery.lambda_handler \\")
    print(f"  --zip-file fileb://{zip_filename} \\")
    print("  --timeout 60 \\")
    print("  --memory-size 512 \\")
    print("  --region eu-west-1 \\")
    print("  --vpc-config SubnetIds=subnet-09d9eef6deec49835,SecurityGroupIds=sg-08fea11c4a73ef52f")
    print()
    print("2. Test the Lambda with:")
    print("aws lambda invoke --function-name opensearch-index-discovery --region eu-west-1 output.json")
    print()

if __name__ == "__main__":
    create_deployment_package()
