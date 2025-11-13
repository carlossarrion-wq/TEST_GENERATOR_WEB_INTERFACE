#!/usr/bin/env python3
"""
Script para desplegar la corrección del generador de casos de prueba
"""

import boto3
import zipfile
import os
import sys
from pathlib import Path

def create_deployment_package():
    """Crear paquete de despliegue con los archivos actualizados"""
    print("📦 Creando paquete de despliegue...")
    
    zip_filename = 'ai_test_generator_fixed.zip'
    
    # Archivos a incluir en el paquete
    files_to_include = [
        'lambda_functions/ai_test_generator_optimized.py',
        'lambda_functions/db_utils.py',
        'lambda_functions/test_plan_agent/__init__.py',
        'lambda_functions/test_plan_agent/complete_langchain_agent.py',
        'lambda_functions/test_plan_agent/tools/__init__.py',
        'lambda_functions/test_plan_agent/tools/test_case_generator.py',
        'lambda_functions/test_plan_agent/tools/requirements_analyzer.py',
        'lambda_functions/test_plan_agent/tools/knowledge_base_retriever.py',
        'lambda_functions/test_plan_agent/tools/coverage_calculator.py',
        'lambda_functions/test_plan_agent/tools/quality_validator.py',
        'lambda_functions/test_plan_agent/utils/__init__.py',
        'lambda_functions/test_plan_agent/utils/logging_config.py',
        'lambda_functions/test_plan_agent/utils/response_helpers.py',
        'lambda_functions/test_plan_agent/utils/opensearch_client.py',
        'lambda_functions/test_plan_agent/utils/redis_memory.py',
    ]
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files_to_include:
            if os.path.exists(file_path):
                # Determinar la ruta dentro del ZIP
                if file_path.startswith('lambda_functions/'):
                    arcname = file_path.replace('lambda_functions/', '')
                else:
                    arcname = file_path
                
                zipf.write(file_path, arcname)
                print(f"  ✓ Agregado: {file_path}")
            else:
                print(f"  ⚠️ Archivo no encontrado: {file_path}")
    
    print(f"✅ Paquete creado: {zip_filename}")
    return zip_filename

def deploy_to_lambda(zip_filename, function_name='test-plan-generator-ai'):
    """Desplegar el paquete a Lambda"""
    print(f"\n🚀 Desplegando a Lambda: {function_name}")
    
    try:
        lambda_client = boto3.client('lambda', region_name='eu-west-1')
        
        # Leer el archivo ZIP
        with open(zip_filename, 'rb') as f:
            zip_content = f.read()
        
        # Actualizar el código de la función
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content,
            Publish=True
        )
        
        print(f"✅ Función actualizada exitosamente!")
        print(f"   Versión: {response['Version']}")
        print(f"   Última modificación: {response['LastModified']}")
        print(f"   Estado: {response['State']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al desplegar: {str(e)}")
        return False

def main():
    print("=" * 80)
    print("🔧 DESPLIEGUE DE CORRECCIÓN - GENERADOR DE CASOS DE PRUEBA")
    print("=" * 80)
    print()
    print("Cambios incluidos:")
    print("  • Prompt mejorado con contexto completo de requerimientos")
    print("  • Validación y deduplicación de casos generados")
    print("  • Fallback mejorado con casos específicos por requerimiento")
    print("  • Mayor temperatura (0.3) para más variedad")
    print("  • Más tokens (4000) para casos más detallados")
    print()
    
    # Crear paquete
    zip_filename = create_deployment_package()
    
    if not os.path.exists(zip_filename):
        print(f"❌ Error: No se pudo crear el paquete {zip_filename}")
        sys.exit(1)
    
    # Preguntar si desplegar
    print()
    response = input("¿Desplegar a Lambda? (s/n): ").strip().lower()
    
    if response == 's':
        success = deploy_to_lambda(zip_filename)
        
        if success:
            print()
            print("=" * 80)
            print("✅ DESPLIEGUE COMPLETADO")
            print("=" * 80)
            print()
            print("Próximos pasos:")
            print("  1. Probar la generación de casos de prueba en la interfaz web")
            print("  2. Verificar que los casos generados sean únicos y específicos")
            print("  3. Revisar los logs de CloudWatch para confirmar el funcionamiento")
            print()
            print("Comando para ver logs:")
            print("  python get_logs.py")
            print()
        else:
            print()
            print("❌ El despliegue falló. Revisa los errores anteriores.")
            sys.exit(1)
    else:
        print()
        print(f"ℹ️ Despliegue cancelado. El paquete {zip_filename} está listo para despliegue manual.")
        print()
        print("Para desplegar manualmente:")
        print(f"  1. Ve a la consola de AWS Lambda")
        print(f"  2. Selecciona la función 'ai-test-generator-optimized'")
        print(f"  3. Sube el archivo {zip_filename}")
        print()

if __name__ == '__main__':
    main()
