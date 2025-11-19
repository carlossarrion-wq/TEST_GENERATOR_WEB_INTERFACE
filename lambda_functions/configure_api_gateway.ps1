# Script para configurar endpoints asíncronos en API Gateway
# Configura POST /api/ai/async y GET /api/ai/async/{task_id}

$API_ID = "2xlh113423"
$REGION = "eu-west-1"
$LAMBDA_ARN = "arn:aws:lambda:eu-west-1:701055077130:function:test-plan-generator-ai"
$ROOT_RESOURCE_ID = "3zzhgqy2q1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Configurando API Gateway Async Endpoints" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Paso 1: Verificar si existe /api
Write-Host "📋 Paso 1: Verificando estructura /api..." -ForegroundColor Yellow
$apiResource = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/api'].id" --output text

if ([string]::IsNullOrWhiteSpace($apiResource)) {
    Write-Host "   Creando recurso /api..." -ForegroundColor Gray
    $apiResource = aws apigateway create-resource --rest-api-id $API_ID --parent-id $ROOT_RESOURCE_ID --path-part "api" --region $REGION --query 'id' --output text
    Write-Host "   ✅ Recurso /api creado: $apiResource" -ForegroundColor Green
} else {
    Write-Host "   ✅ Recurso /api ya existe: $apiResource" -ForegroundColor Green
}

# Paso 2: Verificar si existe /api/ai
Write-Host ""
Write-Host "📋 Paso 2: Verificando estructura /api/ai..." -ForegroundColor Yellow
$aiResource = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/api/ai'].id" --output text

if ([string]::IsNullOrWhiteSpace($aiResource)) {
    Write-Host "   Creando recurso /api/ai..." -ForegroundColor Gray
    $aiResource = aws apigateway create-resource --rest-api-id $API_ID --parent-id $apiResource --path-part "ai" --region $REGION --query 'id' --output text
    Write-Host "   ✅ Recurso /api/ai creado: $aiResource" -ForegroundColor Green
} else {
    Write-Host "   ✅ Recurso /api/ai ya existe: $aiResource" -ForegroundColor Green
}

# Paso 3: Crear /api/ai/async
Write-Host ""
Write-Host "📋 Paso 3: Creando /api/ai/async..." -ForegroundColor Yellow
$ErrorActionPreference = 'SilentlyContinue'
$asyncResource = aws apigateway create-resource --rest-api-id $API_ID --parent-id $aiResource --path-part "async" --region $REGION --query 'id' --output text
$ErrorActionPreference = 'Continue'

if ([string]::IsNullOrWhiteSpace($asyncResource)) {
    $asyncResource = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/api/ai/async'].id" --output text
    Write-Host "   ℹ️  Recurso /api/ai/async ya existe: $asyncResource" -ForegroundColor Cyan
} else {
    Write-Host "   ✅ Recurso /api/ai/async creado: $asyncResource" -ForegroundColor Green
}

# Paso 4: Configurar método POST en /api/ai/async
Write-Host ""
Write-Host "📋 Paso 4: Configurando método POST en /api/ai/async..." -ForegroundColor Yellow
$ErrorActionPreference = 'SilentlyContinue'
aws apigateway put-method --rest-api-id $API_ID --resource-id $asyncResource --http-method POST --authorization-type NONE --region $REGION | Out-Null
aws apigateway put-integration --rest-api-id $API_ID --resource-id $asyncResource --http-method POST --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" --region $REGION | Out-Null
$ErrorActionPreference = 'Continue'
Write-Host "   ✅ Método POST configurado" -ForegroundColor Green

# Paso 5: Crear /api/ai/async/{task_id}
Write-Host ""
Write-Host "📋 Paso 5: Creando /api/ai/async/{task_id}..." -ForegroundColor Yellow
$ErrorActionPreference = 'SilentlyContinue'
$taskIdResource = aws apigateway create-resource --rest-api-id $API_ID --parent-id $asyncResource --path-part "{task_id}" --region $REGION --query 'id' --output text
$ErrorActionPreference = 'Continue'

if ([string]::IsNullOrWhiteSpace($taskIdResource)) {
    $taskIdResource = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/api/ai/async/{task_id}'].id" --output text
    Write-Host "   ℹ️  Recurso /api/ai/async/{task_id} ya existe: $taskIdResource" -ForegroundColor Cyan
} else {
    Write-Host "   ✅ Recurso /api/ai/async/{task_id} creado: $taskIdResource" -ForegroundColor Green
}

# Paso 6: Configurar método GET en /api/ai/async/{task_id}
Write-Host ""
Write-Host "📋 Paso 6: Configurando método GET en /api/ai/async/{task_id}..." -ForegroundColor Yellow
$ErrorActionPreference = 'SilentlyContinue'
aws apigateway put-method --rest-api-id $API_ID --resource-id $taskIdResource --http-method GET --authorization-type NONE --request-parameters "method.request.path.task_id=true" --region $REGION | Out-Null
aws apigateway put-integration --rest-api-id $API_ID --resource-id $taskIdResource --http-method GET --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" --region $REGION | Out-Null
$ErrorActionPreference = 'Continue'
Write-Host "   ✅ Método GET configurado" -ForegroundColor Green

# Paso 7: Configurar CORS para ambos endpoints
Write-Host ""
Write-Host "📋 Paso 7: Configurando CORS..." -ForegroundColor Yellow
$ErrorActionPreference = 'SilentlyContinue'

# CORS para /api/ai/async
aws apigateway put-method --rest-api-id $API_ID --resource-id $asyncResource --http-method OPTIONS --authorization-type NONE --region $REGION | Out-Null
aws apigateway put-integration --rest-api-id $API_ID --resource-id $asyncResource --http-method OPTIONS --type MOCK --request-templates '{\"application/json\": \"{\\\"statusCode\\\": 200}\"}' --region $REGION | Out-Null
aws apigateway put-method-response --rest-api-id $API_ID --resource-id $asyncResource --http-method OPTIONS --status-code 200 --response-parameters "method.response.header.Access-Control-Allow-Headers=true,method.response.header.Access-Control-Allow-Methods=true,method.response.header.Access-Control-Allow-Origin=true" --region $REGION | Out-Null
aws apigateway put-integration-response --rest-api-id $API_ID --resource-id $asyncResource --http-method OPTIONS --status-code 200 --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,POST,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' --region $REGION | Out-Null

# CORS para /api/ai/async/{task_id}
aws apigateway put-method --rest-api-id $API_ID --resource-id $taskIdResource --http-method OPTIONS --authorization-type NONE --region $REGION | Out-Null
aws apigateway put-integration --rest-api-id $API_ID --resource-id $taskIdResource --http-method OPTIONS --type MOCK --request-templates '{\"application/json\": \"{\\\"statusCode\\\": 200}\"}' --region $REGION | Out-Null
aws apigateway put-method-response --rest-api-id $API_ID --resource-id $taskIdResource --http-method OPTIONS --status-code 200 --response-parameters "method.response.header.Access-Control-Allow-Headers=true,method.response.header.Access-Control-Allow-Methods=true,method.response.header.Access-Control-Allow-Origin=true" --region $REGION | Out-Null
aws apigateway put-integration-response --rest-api-id $API_ID --resource-id $taskIdResource --http-method OPTIONS --status-code 200 --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,POST,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' --region $REGION | Out-Null

$ErrorActionPreference = 'Continue'
Write-Host "   ✅ CORS configurado" -ForegroundColor Green

# Paso 8: Dar permisos a Lambda para ser invocada por API Gateway
Write-Host ""
Write-Host "📋 Paso 8: Configurando permisos Lambda..." -ForegroundColor Yellow
$sourceArn = "arn:aws:execute-api:${REGION}:701055077130:${API_ID}/*/*"
$ErrorActionPreference = 'SilentlyContinue'
aws lambda add-permission --function-name test-plan-generator-ai --statement-id apigateway-async-invoke --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn $sourceArn --region $REGION | Out-Null
$ErrorActionPreference = 'Continue'
Write-Host "   ✅ Permisos configurados" -ForegroundColor Green

# Paso 9: Desplegar cambios
Write-Host ""
Write-Host "📋 Paso 9: Desplegando cambios a stage 'prod'..." -ForegroundColor Yellow
aws apigateway create-deployment --rest-api-id $API_ID --stage-name prod --description "Deploy async endpoints for test generation" --region $REGION | Out-Null
Write-Host "   ✅ Cambios desplegados" -ForegroundColor Green

# Resumen
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ CONFIGURACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Endpoints configurados:" -ForegroundColor White
Write-Host "  POST   https://2xlh113423.execute-api.eu-west-1.amazonaws.com/prod/api/ai/async" -ForegroundColor Gray
Write-Host "  GET    https://2xlh113423.execute-api.eu-west-1.amazonaws.com/prod/api/ai/async/{task_id}" -ForegroundColor Gray
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor White
Write-Host "  1. Probar generación con 8-10 casos de prueba desde el frontend" -ForegroundColor Gray
Write-Host "  2. Verificar logs en CloudWatch: /aws/lambda/test-plan-generator-ai" -ForegroundColor Gray
Write-Host ""
