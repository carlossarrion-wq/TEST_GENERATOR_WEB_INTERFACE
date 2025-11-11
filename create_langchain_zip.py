import zipfile
import os

def create_langchain_deployment_zip():
    """Create deployment ZIP with LangChain agent and all tools"""
    
    zip_filename = 'lambda_functions/ai_test_generator_langchain.zip'
    
    files_to_include = [
        # Main Lambda file
        'lambda_functions/ai_test_generator_optimized.py',
        'lambda_functions/db_utils.py',
        
        # LangChain Agent
        'lambda_functions/test_plan_agent/__init__.py',
        'lambda_functions/test_plan_agent/complete_langchain_agent.py',
        
        # Tools
        'lambda_functions/test_plan_agent/tools/__init__.py',
        'lambda_functions/test_plan_agent/tools/requirements_analyzer.py',
        'lambda_functions/test_plan_agent/tools/knowledge_base_retriever.py',
        'lambda_functions/test_plan_agent/tools/test_case_generator.py',
        'lambda_functions/test_plan_agent/tools/coverage_calculator.py',
        'lambda_functions/test_plan_agent/tools/quality_validator.py',
        
        # Utils
        'lambda_functions/test_plan_agent/utils/__init__.py',
        'lambda_functions/test_plan_agent/utils/logging_config.py',
        'lambda_functions/test_plan_agent/utils/response_helpers.py',
        'lambda_functions/test_plan_agent/utils/redis_memory.py',
    ]
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files_to_include:
            if os.path.exists(file_path):
                # Calculate archive name (remove lambda_functions/ prefix)
                archive_name = file_path.replace('lambda_functions/', '')
                zipf.write(file_path, archive_name)
                print(f"✅ Added: {archive_name}")
            else:
                print(f"⚠️  Not found: {file_path}")
    
    # Get file size
    file_size = os.path.getsize(zip_filename)
    print(f"\n✅ ZIP created: {zip_filename}")
    print(f"📦 Size: {file_size:,} bytes ({file_size/1024:.2f} KB)")
    
    return zip_filename, file_size

if __name__ == '__main__':
    zip_file, size = create_langchain_deployment_zip()
    print(f"\n🎉 Ready to deploy!")
    print(f"Command: aws lambda update-function-code --function-name test-plan-generator-plans-crud --zip-file fileb://{zip_file} --region eu-west-1")
