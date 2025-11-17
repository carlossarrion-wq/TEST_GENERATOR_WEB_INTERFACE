#!/usr/bin/env python3
"""
Script para actualizar y desplegar la Lambda de Jira con la corrección de descripciones
"""
import os
import zipfile
import shutil
import boto3

print("=" * 80)
print("ACTUALIZANDO Y DESPLEGANDO LAMBDA DE JIRA")
print("=" * 80)

# 1. Copiar el archivo corregido
print("\n1. Copiando archivo corregido...")
shutil.copy('lambda_functions/jira_integration.py', 'lambda_functions/temp_extract/jira_integration.py')
print("✓ Archivo copiado")

# 2. Crear nuevo ZIP con todas las dependencias
print("\n2. Creando nuevo paquete ZIP...")
zip_path = 'lambda_functions/jira_integration_fixed.zip'

# Eliminar ZIP anterior si existe
if os.path.exists(zip_path):
    os.remove(zip_path)

# Crear nuevo ZIP
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    # Recorrer todos los archivos en temp_extract
    for root, dirs, files in os.walk('lambda_functions/temp_extract'):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, 'lambda_functions/temp_extract')
            zipf.write(file_path, arcname)
            
zip_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
print(f"✓ Paquete creado: {zip_size:.2f} MB")

# 3. Desplegar a AWS Lambda
print("\n3. Desplegando a AWS Lambda...")
lambda_client = boto3.client('lambda', region_name='eu-west-1')

with open(zip_path, 'rb') as f:
    zip_content = f.read()
    
response = lambda_client.update_function_code(
    FunctionName='jira-integration-python',
    ZipFile=zip_content
)

print(f"✓ Lambda actualizada: {response['FunctionName']}")
print(f"  - Versión: {response['Version']}")
print(f"  - Tamaño: {response['CodeSize']} bytes")
print(f"  - Estado: {response['LastUpdateStatus']}")

print("\n" + "=" * 80)
print("✅ DESPLIEGUE COMPLETADO")
print("=" * 80)
print("\nEspera unos segundos para que la Lambda se actualice completamente.")
print("Luego prueba importar tickets desde Jira en la aplicación web.")
