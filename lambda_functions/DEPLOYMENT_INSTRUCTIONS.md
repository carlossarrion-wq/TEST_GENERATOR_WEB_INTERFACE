# 📋 INSTRUCCIONES DE DEPLOYMENT - Lambda Optimizada

## 🎯 Objetivo
Desplegar la Lambda optimizada con Haiku 4.5 y prompt caching para reducir tiempos de generación de tests de 29+ segundos a menos de 10 segundos.

---

## 📦 Archivos Incluidos

1. **ai_test_generator_optimized.py** - Lambda optimizada con Haiku 4.5
2. **deploy_optimized.sh** - Script automatizado de deployment
3. **db_utils.py** - Utilidades de base de datos (compartido)

---

## 🚀 OPCIÓN 1: Deployment Automatizado (Recomendado)

### Paso 1: Dar permisos de ejecución al script
```bash
cd lambda_functions
chmod +x deploy_optimized.sh
```

### Paso 2: Ejecutar el script
```bash
./deploy_optimized.sh
```

El script automáticamente:
- ✅ Empaqueta la Lambda en ZIP
- ✅ Verifica si la función existe
- ✅ Actualiza el código
- ✅ Configura variables de entorno
- ✅ Ajusta timeout y memoria

---

## 🔧 OPCIÓN 2: Deployment Manual

### Paso 1: Empaquetar Lambda
```bash
cd lambda_functions
zip ai_test_generator_optimized.zip ai_test_generator_optimized.py db_utils.py
```

### Paso 2: Crear función Lambda (si no existe)
```bash
aws lambda create-function \
  --function-name test-plan-generator-ai-optimized \
  --runtime python3.11 \
  --role arn:aws:iam::701055077130:role/lambda-execution-role \
  --handler ai_test_generator_optimized.lambda_handler \
  --zip-file fileb://ai_test_generator_optimized.zip \
  --timeout 60 \
  --memory-size 512 \
  --region eu-west-1
```

### Paso 3: Actualizar código (si ya existe)
```bash
aws lambda update-function-code \
  --function-name test-plan-generator-ai-optimized \
  --zip-file fileb://ai_test_generator_optimized.zip \
  --region eu-west-1
```

### Paso 4: Configurar variables de entorno
```bash
aws lambda update-function-configuration \
  --function-name test-plan-generator-ai-optimized \
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
  --region eu-west-1
```

### Paso 5: Asociar Layer de dependencias
```bash
aws lambda update-function-configuration \
  --function-name test-plan-generator-ai-optimized \
  --layers arn:aws:lambda:eu-west-1:701055077130:layer:lambda-dependencies:1 \
  --region eu-west-1
```

### Paso 6: Configurar permisos IAM
La función necesita permisos para:
- ✅ Bedrock (invoke model)
- ✅ Bedrock Agent (retrieve from Knowledge Base)
- ✅ RDS (conexión a base de datos)
- ✅ CloudWatch Logs

---

## 🔗 Integración con API Gateway

### Actualizar endpoint existente
```bash
# Obtener ID del API Gateway
API_ID="2xlh113423"

# Actualizar integración
aws apigatewayv2 update-integration \
  --api-id $API_ID \
  --integration-id <INTEGRATION_ID> \
  --integration-uri arn:aws:lambda:eu-west-1:701055077130:function:test-plan-generator-ai-optimized \
  --region eu-west-1
```

### O crear nuevo endpoint
```bash
# Crear ruta POST /ai/generate-plan
aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "POST /ai/generate-plan" \
  --target "integrations/<INTEGRATION_ID>" \
  --region eu-west-1
```

---

## ✅ Verificación Post-Deployment

### 1. Verificar función Lambda
```bash
aws lambda get-function \
  --function-name test-plan-generator-ai-optimized \
  --region eu-west-1
```

### 2. Ver logs en CloudWatch
```bash
aws logs tail /aws/lambda/test-plan-generator-ai-optimized \
  --follow \
  --region eu-west-1
```

### 3. Invocar función de prueba
```bash
aws lambda invoke \
  --function-name test-plan-generator-ai-optimized \
  --payload '{"httpMethod":"POST","body":"{\"action\":\"generate-plan\",\"title\":\"Test Plan\",\"requirements\":\"Test requirements\"}"}' \
  --region eu-west-1 \
  response.json

cat response.json
```

---

## 📊 Métricas a Monitorear

Después del deployment, monitorear:

1. **Tiempo de ejecución** - Debe ser < 10 segundos
2. **Errores** - Debe ser 0%
3. **Timeouts** - Debe ser 0
4. **Costo** - Reducción del 70% vs Sonnet 4
5. **Tokens procesados** - Reducción del 90% con caching

### Ver métricas en CloudWatch
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=test-plan-generator-ai-optimized \
  --start-time 2025-01-11T00:00:00Z \
  --end-time 2025-01-11T23:59:59Z \
  --period 3600 \
  --statistics Average,Maximum \
  --region eu-west-1
```

---

## 🐛 Troubleshooting

### Error: "ResourceNotFoundException"
**Solución:** La función no existe, usar comando de creación (Paso 2 manual)

### Error: "AccessDeniedException" 
**Solución:** Verificar permisos IAM del rol de ejecución

### Error: "Timeout"
**Solución:** Aumentar timeout a 90 segundos si es necesario

### Error: "Memory exceeded"
**Solución:** Aumentar memoria a 1024 MB

### Error: "Knowledge Base not found"
**Solución:** Verificar KNOWLEDGE_BASE_ID=VH6SRH9ZNO

---

## 🔄 Rollback

Si hay problemas, hacer rollback a versión anterior:

```bash
# Listar versiones
aws lambda list-versions-by-function \
  --function-name test-plan-generator-ai-optimized \
  --region eu-west-1

# Hacer rollback a versión anterior
aws lambda update-alias \
  --function-name test-plan-generator-ai-optimized \
  --name PROD \
  --function-version <VERSION_NUMBER> \
  --region eu-west-1
```

---

## 📝 Checklist de Deployment

- [ ] Script de deployment ejecutado sin errores
- [ ] Variables de entorno configuradas correctamente
- [ ] Layer de dependencias asociado
- [ ] Permisos IAM verificados
- [ ] Timeout configurado a 60 segundos
- [ ] Memoria configurada a 512 MB
- [ ] API Gateway actualizado (si aplica)
- [ ] Logs de CloudWatch funcionando
- [ ] Test de invocación exitoso
- [ ] Métricas monitoreadas
- [ ] Tiempos de respuesta < 10 segundos verificados

---

**Última actualización:** 11/04/2025
**Versión:** 1.0 - Lambda Optimizada con Haiku 4.5
