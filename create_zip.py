import zipfile
import os

# Cambiar al directorio lambda_functions
os.chdir('lambda_functions')

# Crear ZIP
with zipfile.ZipFile('ai_test_generator_optimized.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    # Add main files
    zipf.write('ai_test_generator_optimized.py')
    zipf.write('db_utils.py')
    
    # Add test_plan_agent directory recursively
    for root, dirs, files in os.walk('test_plan_agent'):
        for file in files:
            file_path = os.path.join(root, file)
            zipf.write(file_path)

print("ZIP creado exitosamente")
print(f"Tamaño: {os.path.getsize('ai_test_generator_optimized.zip')} bytes")
