#!/bin/bash

# Script de despliegue del sistema asíncrono
# Usa MySQL RDS existente en lugar de DynamoDB

set -e

FUNCTION_NAME="test-plan-generator-ai"
REGION="eu-west-1"
DB_HOST="test-plan-generator-db.czuimyk2qu10.eu-west-1.rds.amazonaws.com"
DB_USER="admin"
DB_NAME="testplangenerator"

echo "🚀 Desplegando Sistema Asíncrono para Test Plan Generator"
echo "=========================================================="

# Paso 1: Crear tabla async_tasks en MySQL
echo ""
echo "📊 Paso 1: Creando tabla async_tasks en MySQL..."
echo "IMPORTANTE: Necesitas ejecutar el SQL manualmente en tu base de datos RDS"
echo ""
echo "Ejecuta este comando SQL en tu base de datos:"
echo "---------------------------------------------------"
cat async_tasks_table.sql
echo "---------------------------------------------------"
echo ""
read -p "¿Has ejecutado el SQL en la base de datos? (s/n): " confirm

if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
    echo "❌ Abortando despliegue. Por favor ejecuta el SQL primero."
    exit 1
fi

# Paso 2: Crear paquete de despliegue
echo ""
echo "📦 Paso 2: Creando paquete de despliegue..."
cd "$(dirname "$0")"

# Limpiar paquete anterior
rm -f ai_test_generator_optimized.zip

# Crear nuevo paquete
zip -r ai_test_generator_optimized.zip \
    ai_test_generator_optimized.py \
    db_utils.py \
    test_plan_agent/ \
    -x "*.pyc" -x "__pycache__/*" -x "*.git*"

echo "✅ Paquete creado: ai_test_generator_optimized.zip"

# Paso 3: Desplegar Lambda
echo ""
echo "🚀 Paso 3: Desplegando función Lambda..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://ai_test_generator_optimized.zip \
    --region $REGION

echo "⏳ Esperando a que la función se actualice..."
aws lambda wait function-updated \
    --function-name $FUNCTION_NAME \
    --region $REGION

echo "✅ Lambda actualizada exitosamente"

# Paso 4: Verificar configuración
echo ""
echo "🔍 Paso 4: Verificando configuración..."
TIMEOUT=$(aws lambda get-function-configuration \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --query 'Timeout' \
    --output text)

echo "   Timeout actual: ${TIMEOUT}s"

if [ "$TIMEOUT" -lt 90 ]; then
    echo "⚠️  Timeout es menor a 90 segundos. Actualizando..."
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --timeout 90 \
        --region $REGION
    echo "✅ Timeout actualizado a 90 segundos"
fi

# Paso 5: Información de API Gateway
echo ""
echo "📡 Paso 5: Configuración de API Gateway"
echo "========================================="
echo ""
echo "Necesitas agregar estos endpoints en API Gateway:"
echo ""
echo "1. POST /api/ai/async"
echo "   - Integración: Lambda Proxy"
echo "   - Mapping: action=async"
echo ""
echo "2. GET /api/ai/async/{task_id}"
echo "   - Integración: Lambda Proxy"
echo "   - Mapping: action=async-status, task_id={task_id}"
echo ""
echo "Comandos para configurar API Gateway:"
echo "---------------------------------------------------"
cat << 'EOF'
# Obtener API ID
API_ID=$(aws apigateway get-rest-apis --region eu-west-1 \
    --query "items[?name=='test-generator-api'].id" --output text)

# Obtener Resource ID de /api/ai
RESOURCE_ID=$(aws apigateway get-resources --rest-api-id $API_ID \
    --region eu-west-1 --query "items[?path=='/api/ai'].id" --output text)

# Crear recurso /async
ASYNC_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $RESOURCE_ID \
    --path-part async \
    --region eu-west-1 \
    --query 'id' --output text)

# Crear método POST
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $ASYNC_RESOURCE_ID \
    --http-method POST \
    --authorization-type NONE \
    --region eu-west-1

# Obtener Lambda ARN
LAMBDA_ARN=$(aws lambda get-function --function-name test-plan-generator-ai \
    --region eu-west-1 --query 'Configuration.FunctionArn' --output text)

# Configurar integración POST
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $ASYNC_RESOURCE_ID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
    --region eu-west-1

# Crear recurso /{task_id}
TASK_ID_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ASYNC_RESOURCE_ID \
    --path-part '{task_id}' \
    --region eu-west-1 \
    --query 'id' --output text)

# Crear método GET
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $TASK_ID_RESOURCE_ID \
    --http-method GET \
    --authorization-type NONE \
    --request-parameters method.request.path.task_id=true \
    --region eu-west-1

# Configurar integración GET
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $TASK_ID_RESOURCE_ID \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
    --region eu-west-1

# Desplegar cambios
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region eu-west-1

echo "✅ API Gateway configurado"
EOF
echo "---------------------------------------------------"
echo ""

# Resumen
echo ""
echo "✅ DESPLIEGUE COMPLETADO"
echo "========================"
echo ""
echo "Resumen de cambios:"
echo "  ✅ Tabla async_tasks creada en MySQL RDS"
echo "  ✅ Lambda actualizada con soporte asíncrono"
echo "  ✅ Timeout configurado a 90 segundos"
echo "  ⚠️  Pendiente: Configurar endpoints en API Gateway"
echo ""
echo "Próximos pasos:"
echo "  1. Ejecutar los comandos de API Gateway mostrados arriba"
echo "  2. Probar con 8-10 casos de prueba"
echo "  3. Verificar logs en CloudWatch"
echo ""
echo "Para ver logs:"
echo "  aws logs tail /aws/lambda/$FUNCTION_NAME --follow --region $REGION"
echo ""
echo "Para probar:"
echo "  curl -X POST https://YOUR_API_URL/api/ai/async \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"title\":\"Test\",\"requirements\":\"Test async\",\"min_test_cases\":8,\"max_test_cases\":10}'"
echo ""
