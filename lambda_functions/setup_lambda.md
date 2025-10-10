# 🚀 Configuración de Funciones Lambda - Test Plan Generator

Esta guía proporciona instrucciones detalladas para configurar y desplegar las funciones Lambda necesarias para el Test Plan Generator con RDS MySQL.

## 📋 **Funciones Lambda Creadas**

1. **`test_plans_crud`** - CRUD completo para test plans
2. **`test_cases_crud`** - CRUD completo para test cases
3. **`chat_messages_crud`** - CRUD para mensajes de chat
4. **`ai_test_generator`** - Generación de test plans con AI (AWS Bedrock)

## 🔧 **Prerequisitos**

### **1. Dependencias Python**
Todas las funciones Lambda requieren:
```
pymysql==1.1.2
boto3==1.34.0
```

### **2. Infraestructura AWS Requerida**
- ✅ RDS MySQL 8.0 (ya configurado)
- ✅ VPC y Security Groups (ya configurados)
- ✅ API Gateway (existente)
- 📋 IAM Roles para Lambda
- 📋 Lambda Layers (opcional, para dependencias)

## 🏗️ **Paso 1: Crear IAM Role para Lambda**

### **1.1 Crear IAM Role**
```bash
# Crear rol para Lambda con acceso a RDS
aws iam create-role \
  --role-name TestPlanGeneratorLambdaRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }' \
  --tags Key=Project,Value=TestPlanGenerator
```

### **1.2 Attachar Políticas Necesarias**
```bash
# Política básica de Lambda
aws iam attach-role-policy \
  --role-name TestPlanGeneratorLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Política para VPC (acceso a RDS)
aws iam attach-role-policy \
  --role-name TestPlanGeneratorLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole

# Política para Bedrock (solo para ai_test_generator)
aws iam attach-role-policy \
  --role-name TestPlanGeneratorLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
```

### **1.3 Crear Política Personalizada para RDS**
```bash
# Crear política para acceso específico a RDS
aws iam create-policy \
  --policy-name TestPlanGeneratorRDSAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters"
        ],
        "Resource": "*"
      }
    ]
  }' \
  --tags Key=Project,Value=TestPlanGenerator

# Attachar la política
aws iam attach-role-policy \
  --role-name TestPlanGeneratorLambdaRole \
  --policy-arn arn:aws:iam::701055077130:policy/TestPlanGeneratorRDSAccess
```

## 📦 **Paso 2: Crear Lambda Layer (Recomendado)**

### **2.1 Preparar Dependencias**
```bash
# Crear directorio para layer
mkdir lambda-layer
cd lambda-layer
mkdir python

# Instalar dependencias
pip install pymysql boto3 -t python/

# Crear archivo ZIP
zip -r lambda-dependencies-layer.zip python/
```

### **2.2 Crear Layer en AWS**
```bash
aws lambda publish-layer-version \
  --layer-name test-plan-generator-dependencies \
  --description "Dependencies for Test Plan Generator Lambda functions" \
  --zip-file fileb://lambda-dependencies-layer.zip \
  --compatible-runtimes python3.9 python3.10 python3.11 \
  --compatible-architectures x86_64 arm64
```

## 🚀 **Paso 3: Crear Funciones Lambda**

### **3.1 Variables de Entorno Comunes**
```bash
# Variables que todas las funciones necesitan
export RDS_HOST="test-plan-generator-db.czuimyk2qu10.eu-west-1.rds.amazonaws.com"
export RDS_USER="admin"
export RDS_PASSWORD="TempPassword123!"
export RDS_DATABASE="testplangenerator"
export RDS_PORT="3306"
export VPC_ID="vpc-0599bd223876c0102"
export SUBNET_1="subnet-065a4b579b52d584d"
export SUBNET_2="subnet-0c868941683436d99"
export SECURITY_GROUP="sg-06182b620ead957bb"
export LAMBDA_ROLE_ARN="arn:aws:iam::701055077130:role/TestPlanGeneratorLambdaRole"

# Variables específicas para AI (Claude Sonnet 4 + Knowledge Base)
export KNOWLEDGE_BASE_ID="VH6SRH9ZNO"
export BEDROCK_MODEL_ID="arn:aws:bedrock:eu-west-1:701055077130:inference-profile/eu.anthropic.claude-sonnet-4-20250514-v1:0"
```

### **3.2 Función 1: test_plans_crud**
```bash
# Crear archivo ZIP con el código
zip test_plans_crud.zip test_plans_crud.py db_utils.py

# Crear función Lambda
aws lambda create-function \
  --function-name test-plan-generator-plans-crud \
  --runtime python3.11 \
  --role $LAMBDA_ROLE_ARN \
  --handler test_plans_crud.lambda_handler \
  --zip-file fileb://test_plans_crud.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{
    RDS_HOST=$RDS_HOST,
    RDS_USER=$RDS_USER,
    RDS_PASSWORD=$RDS_PASSWORD,
    RDS_DATABASE=$RDS_DATABASE,
    RDS_PORT=$RDS_PORT
  }" \
  --vpc-config SubnetIds=$SUBNET_1,$SUBNET_2,SecurityGroupIds=$SECURITY_GROUP \
  --tags Project=TestPlanGenerator,Function=CRUD \
  --architectures x86_64
```

### **3.3 Función 2: test_cases_crud**
```bash
# Crear archivo ZIP
zip test_cases_crud.zip test_cases_crud.py db_utils.py

# Crear función Lambda
aws lambda create-function \
  --function-name test-plan-generator-cases-crud \
  --runtime python3.11 \
  --role $LAMBDA_ROLE_ARN \
  --handler test_cases_crud.lambda_handler \
  --zip-file fileb://test_cases_crud.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{
    RDS_HOST=$RDS_HOST,
    RDS_USER=$RDS_USER,
    RDS_PASSWORD=$RDS_PASSWORD,
    RDS_DATABASE=$RDS_DATABASE,
    RDS_PORT=$RDS_PORT
  }" \
  --vpc-config SubnetIds=$SUBNET_1,$SUBNET_2,SecurityGroupIds=$SECURITY_GROUP \
  --tags Project=TestPlanGenerator,Function=CRUD \
  --architectures x86_64
```

### **3.4 Función 3: chat_messages_crud**
```bash
# Crear archivo ZIP
zip chat_messages_crud.zip chat_messages_crud.py db_utils.py

# Crear función Lambda
aws lambda create-function \
  --function-name test-plan-generator-chat-crud \
  --runtime python3.11 \
  --role $LAMBDA_ROLE_ARN \
  --handler chat_messages_crud.lambda_handler \
  --zip-file fileb://chat_messages_crud.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{
    RDS_HOST=$RDS_HOST,
    RDS_USER=$RDS_USER,
    RDS_PASSWORD=$RDS_PASSWORD,
    RDS_DATABASE=$RDS_DATABASE,
    RDS_PORT=$RDS_PORT
  }" \
  --vpc-config SubnetIds=$SUBNET_1,$SUBNET_2,SecurityGroupIds=$SECURITY_GROUP \
  --tags Project=TestPlanGenerator,Function=CRUD \
  --architectures x86_64
```

### **3.5 Función 4: ai_test_generator**
```bash
# Crear archivo ZIP
zip ai_test_generator.zip ai_test_generator.py db_utils.py

# Crear función Lambda (requiere más memoria para AI)
aws lambda create-function \
  --function-name test-plan-generator-ai \
  --runtime python3.11 \
  --role $LAMBDA_ROLE_ARN \
  --handler ai_test_generator.lambda_handler \
  --zip-file fileb://ai_test_generator.zip \
  --timeout 60 \
  --memory-size 512 \
  --environment Variables="{
    RDS_HOST=$RDS_HOST,
    RDS_USER=$RDS_USER,
    RDS_PASSWORD=$RDS_PASSWORD,
    RDS_DATABASE=$RDS_DATABASE,
    RDS_PORT=$RDS_PORT,
    KNOWLEDGE_BASE_ID=$KNOWLEDGE_BASE_ID,
    BEDROCK_MODEL_ID=$BEDROCK_MODEL_ID
  }" \
  --vpc-config SubnetIds=$SUBNET_1,$SUBNET_2,SecurityGroupIds=$SECURITY_GROUP \
  --tags Project=TestPlanGenerator,Function=AI \
  --architectures x86_64
```

## 🔗 **Paso 4: Configurar API Gateway**

### **4.1 Obtener API Gateway Existente**
```bash
# Listar APIs existentes
aws apigateway get-rest-apis --query 'items[?name==`TestPlanGeneratorAPI`]'

# Obtener ID del API Gateway (reemplazar con tu ID)
export API_ID="your_existing_api_id"
export ROOT_RESOURCE_ID="your_root_resource_id"
```

### **4.2 Crear Recursos y Métodos**

#### **4.2.1 Recurso /api/plans**
```bash
# Crear recurso /plans
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_RESOURCE_ID \
  --path-part plans

export PLANS_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[?pathPart==`plans`].id' \
  --output text)

# Crear métodos para /plans
for METHOD in GET POST OPTIONS; do
  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $PLANS_RESOURCE_ID \
    --http-method $METHOD \
    --authorization-type NONE
done

# Integración con Lambda
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $PLANS_RESOURCE_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-1:701055077130:function:test-plan-generator-plans-crud/invocations
```

#### **4.2.2 Recurso /api/plans/{plan_id}**
```bash
# Crear recurso para plan específico
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $PLANS_RESOURCE_ID \
  --path-part '{plan_id}'

export PLAN_DETAIL_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[?pathPart==`{plan_id}`].id' \
  --output text)

# Configurar métodos GET, PUT, DELETE
for METHOD in GET PUT DELETE OPTIONS; do
  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $PLAN_DETAIL_RESOURCE_ID \
    --http-method $METHOD \
    --authorization-type NONE
done
```

#### **4.2.3 Recurso /api/plans/{plan_id}/cases**
```bash
# Crear recurso para casos de test
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $PLAN_DETAIL_RESOURCE_ID \
  --path-part cases

export CASES_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[?pathPart==`cases`].id' \
  --output text)
```

### **4.3 Permisos Lambda**
```bash
# Dar permisos a API Gateway para invocar las Lambdas
aws lambda add-permission \
  --function-name test-plan-generator-plans-crud \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:eu-west-1:701055077130:$API_ID/*/*/*"

aws lambda add-permission \
  --function-name test-plan-generator-cases-crud \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:eu-west-1:701055077130:$API_ID/*/*/*"

aws lambda add-permission \
  --function-name test-plan-generator-chat-crud \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:eu-west-1:701055077130:$API_ID/*/*/*"

aws lambda add-permission \
  --function-name test-plan-generator-ai \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:eu-west-1:701055077130:$API_ID/*/*/*"
```

## 🧪 **Paso 5: Testing y Verificación**

### **5.1 Test Básico de Conexión**
```bash
# Test directo de función Lambda
aws lambda invoke \
  --function-name test-plan-generator-plans-crud \
  --payload '{
    "httpMethod": "GET",
    "path": "/api/plans",
    "queryStringParameters": {"limit": "10"},
    "headers": {"Content-Type": "application/json"}
  }' \
  response.json

cat response.json
```

### **5.2 Test API Gateway**
```bash
# Test a través de API Gateway (reemplazar con tu endpoint)
curl -X GET \
  "https://your-api-id.execute-api.eu-west-1.amazonaws.com/prod/api/plans?limit=5" \
  -H "Content-Type: application/json"
```

### **5.3 Test CRUD Completo**

#### **Crear Test Plan**
```bash
curl -X POST \
  "https://your-api-id.execute-api.eu-west-1.amazonaws.com/prod/api/plans" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "API Test Plan",
    "requirements": "Test the API endpoints for CRUD operations",
    "coverage_percentage": 85,
    "selected_test_types": ["integration", "functional"]
  }'
```

#### **Obtener Test Plans**
```bash
curl -X GET \
  "https://your-api-id.execute-api.eu-west-1.amazonaws.com/prod/api/plans" \
  -H "Content-Type: application/json"
```

#### **Crear Test Case**
```bash
curl -X POST \
  "https://your-api-id.execute-api.eu-west-1.amazonaws.com/prod/api/plans/TP-XXXX/cases" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test API Authentication",
    "description": "Verify API authentication works correctly",
    "priority": "High",
    "test_steps": [
      "Send request without authentication",
      "Verify 401 response",
      "Send request with valid token",
      "Verify 200 response"
    ]
  }'
```

## 🚨 **Consideraciones de Seguridad**

### **6.1 Rotación de Credenciales**
```bash
# Cambiar contraseña de RDS (hacer después del setup)
aws rds modify-db-instance \
  --db-instance-identifier test-plan-generator-db \
  --master-user-password "NewSecurePassword123!" \
  --apply-immediately
```

### **6.2 Configurar AWS Secrets Manager (Recomendado)**
```bash
# Crear secret para RDS
aws secretsmanager create-secret \
  --name "TestPlanGenerator/RDS/Credentials" \
  --description "RDS credentials for Test Plan Generator" \
  --secret-string '{
    "host": "test-plan-generator-db.czuimyk2qu10.eu-west-1.rds.amazonaws.com",
    "username": "admin",
    "password": "TempPassword123!",
    "database": "testplangenerator",
    "port": 3306
  }' \
  --tags Key=Project,Value=TestPlanGenerator
```

## 📊 **Paso 6: Monitoreo y Logs**

### **6.1 Configurar CloudWatch Alarms**
```bash
# Alarm para errores en Lambda
aws cloudwatch put-metric-alarm \
  --alarm-name "TestPlanGenerator-Lambda-Errors" \
  --alarm-description "High error rate in Lambda functions" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### **6.2 Configurar X-Ray (Opcional)**
```bash
# Habilitar X-Ray tracing
aws lambda put-function-configuration \
  --function-name test-plan-generator-plans-crud \
  --tracing-config Mode=Active
```

## 🔄 **Paso 7: Deployment y Actualizaciones**

### **7.1 Script de Deployment Automatizado**
```bash
#!/bin/bash
# deploy.sh

FUNCTIONS=("test-plan-generator-plans-crud" "test-plan-generator-cases-crud" "test-plan-generator-chat-crud" "test-plan-generator-ai")

for FUNCTION in "${FUNCTIONS[@]}"; do
  echo "Updating $FUNCTION..."
  
  # Crear ZIP
  zip ${FUNCTION}.zip ${FUNCTION}.py db_utils.py
  
  # Actualizar función
  aws lambda update-function-code \
    --function-name $FUNCTION \
    --zip-file fileb://${FUNCTION}.zip
  
  echo "$FUNCTION updated successfully"
done

echo "All functions updated!"
```

### **7.2 Deployment de API Gateway**
```bash
# Deploy API Gateway stage
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --description "Production deployment with RDS Lambda functions"
```

## 📝 **Endpoints API Finales**

Una vez configurado, tendrás los siguientes endpoints:

### **Test Plans**
- `GET /api/plans` - Listar test plans
- `POST /api/plans` - Crear test plan
- `GET /api/plans/{plan_id}` - Obtener test plan específico
- `PUT /api/plans/{plan_id}` - Actualizar test plan
- `DELETE /api/plans/{plan_id}` - Eliminar test plan

### **Test Cases**
- `GET /api/plans/{plan_id}/cases` - Listar test cases
- `POST /api/plans/{plan_id}/cases` - Crear test case
- `GET /api/cases/{case_id}` - Obtener test case específico
- `PUT /api/cases/{case_id}` - Actualizar test case
- `DELETE /api/cases/{case_id}` - Eliminar test case

### **Chat Messages**
- `GET /api/plans/{plan_id}/chat` - Obtener mensajes
- `POST /api/plans/{plan_id}/chat` - Enviar mensaje
- `DELETE /api/plans/{plan_id}/chat` - Limpiar historial

### **AI Generation**
- `POST /api/ai/generate-plan` - Generar test plan con AI
- `POST /api/ai/plans/{plan_id}/generate-cases` - Generar test cases
- `POST /api/ai/plans/{plan_id}/chat` - Chat con AI
- `POST /api/ai/plans/{plan_id}/improve-cases` - Mejorar test cases

## ✅ **Checklist Final**

- [ ] IAM Role creado con permisos correctos
- [ ] Funciones Lambda desplegadas
- [ ] Variables de entorno configuradas
- [ ] API Gateway endpoints configurados
- [ ] Permisos Lambda-API Gateway configurados
- [ ] Tests básicos ejecutados exitosamente
- [ ] Monitoreo CloudWatch configurado
- [ ] Documentación API actualizada
- [ ] Credenciales rotadas (recomendado)

## 🆘 **Troubleshooting Común**

### **Error: "Unable to connect to RDS"**
- Verificar security groups
- Confirmar que Lambda está en la VPC correcta
- Verificar credenciales RDS

### **Error: "Access Denied" en Bedrock**
- Verificar región (eu-west-1 configurada correctamente)
- Confirmar permisos IAM para Bedrock
- Verificar disponibilidad del modelo Claude en eu-west-1
- **IMPORTANTE**: Si Bedrock no está disponible en eu-west-1, cambiar a us-east-1 en ai_test_generator.py

### **Error: "Timeout" en Lambda**
- Aumentar timeout (máximo 15 min)
- Optimizar consultas de base de datos
- Verificar conexiones VPC

---

**🎉 ¡Setup Completado!** 

Tu Test Plan Generator ahora está funcionando con RDS MySQL y todas las funciones CRUD están disponibles a través de API Gateway.
