#!/bin/bash

echo "🚀 Deployment Script - Lambda Optimizada para Generación de Tests"
echo "=================================================================="
echo ""

LAMBDA_FUNCTION_NAME="test-plan-generator-ai-optimized"
REGION="eu-west-1"
ZIP_FILE="ai_test_generator_optimized.zip"

echo "📦 Paso 1: Empaquetando Lambda optimizada..."
cd "$(dirname "$0")"

if [ -f "$ZIP_FILE" ]; then
    rm "$ZIP_FILE"
    echo "   ✓ Archivo ZIP anterior eliminado"
fi

zip -q "$ZIP_FILE" ai_test_generator_optimized.py db_utils.py
echo "   ✓ Lambda empaquetada: $ZIP_FILE"
echo ""

echo "📋 Paso 2: Verificando función Lambda en AWS..."
FUNCTION_EXISTS=$(aws lambda get-function --function-name "$LAMBDA_FUNCTION_NAME" --region "$REGION" 2>&1)

if echo "$FUNCTION_EXISTS" | grep -q "ResourceNotFoundException"; then
    echo "   ⚠️  Función no existe, será necesario crearla manualmente"
    echo ""
    echo "   Usa este comando para crear la función:"
    echo "   aws lambda create-function \\"
    echo "     --function-name $LAMBDA_FUNCTION_NAME \\"
    echo "     --runtime python3.11 \\"
    echo "     --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \\"
    echo "     --handler ai_test_generator_optimized.lambda_handler \\"
    echo "     --zip-file fileb://$ZIP_FILE \\"
    echo "     --timeout 60 \\"
    echo "     --memory-size 512 \\"
    echo "     --region $REGION"
    echo ""
else
    echo "   ✓ Función Lambda encontrada"
    echo ""
    
    echo "📤 Paso 3: Actualizando código de Lambda..."
    aws lambda update-function-code \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --zip-file "fileb://$ZIP_FILE" \
        --region "$REGION" \
        --no-cli-pager
    
    if [ $? -eq 0 ]; then
        echo "   ✓ Código actualizado exitosamente"
    else
        echo "   ❌ Error actualizando código"
        exit 1
    fi
    echo ""
    
    echo "⚙️  Paso 4: Configurando variables de entorno..."
    aws lambda update-function-configuration \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --environment "Variables={
            KNOWLEDGE_BASE_ID=VH6SRH9ZNO,
            BEDROCK_MODEL_ID=anthropic.claude-3-5-haiku-20241022-v1:0,
            RDS_HOST=test-plan-generator-db.czuimyk2qu10.eu-west-1.rds.amazonaws.com,
            RDS_USER=admin,
            RDS_PASSWORD=TempPassword123!,
            RDS_DATABASE=testplangenerator,
            RDS_PORT=3306
        }" \
        --timeout 60 \
        --memory-size 512 \
        --region "$REGION" \
        --no-cli-pager
    
    if [ $? -eq 0 ]; then
        echo "   ✓ Configuración actualizada"
    else
        echo "   ❌ Error actualizando configuración"
        exit 1
    fi
    echo ""
fi

echo "✅ Deployment completado!"
echo ""
echo "📊 Información de la función:"
echo "   Nombre: $LAMBDA_FUNCTION_NAME"
echo "   Región: $REGION"
echo "   Runtime: Python 3.11"
echo "   Timeout: 60 segundos"
echo "   Memory: 512 MB"
echo "   Modelo: Haiku 4.5"
echo ""
echo "🔗 Próximos pasos:"
echo "   1. Verificar logs en CloudWatch"
echo "   2. Probar la función con un test plan"
echo "   3. Medir tiempos de respuesta"
echo "   4. Actualizar API Gateway si es necesario"
echo ""
