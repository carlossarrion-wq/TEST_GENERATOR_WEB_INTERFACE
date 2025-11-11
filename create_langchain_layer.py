import zipfile
import os
from pathlib import Path

def create_langchain_layer_zip():
    """Create Lambda Layer ZIP with LangChain dependencies"""
    
    source_dir = Path("langchain-layer-new/python")
    output_file = "langchain-layer-new.zip"
    
    print(f"Creating LangChain Lambda Layer ZIP...")
    print(f"Source: {source_dir}")
    print(f"Output: {output_file}")
    
    file_count = 0
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the python directory
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Calculate the archive name (relative to langchain-layer-new)
                arcname = os.path.relpath(file_path, "langchain-layer-new")
                zipf.write(file_path, arcname)
                file_count += 1
                if file_count % 100 == 0:
                    print(f"  Added {file_count} files...")
                
        print(f"✅ Added {file_count} files from {source_dir}")
    
    # Get file size
    size = os.path.getsize(output_file)
    size_mb = size / (1024 * 1024)
    
    print(f"\n✅ ZIP created: {output_file}")
    print(f"📦 Size: {size:,} bytes ({size_mb:.2f} MB)")
    print(f"\n🎉 Ready to deploy!")
    print(f"Command: aws lambda publish-layer-version --layer-name test-plan-generator-langchain --zip-file fileb://{output_file} --compatible-runtimes python3.11 --region eu-west-1")

if __name__ == "__main__":
    create_langchain_layer_zip()
