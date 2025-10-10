# 📋 Plan de Implementación: Base de Datos RDS para Operaciones CRUD

## 🎯 Objetivo

Migrar el sistema de almacenamiento de planes de prueba desde LocalStorage a una base de datos AWS RDS con operaciones CRUD completas, proporcionando escalabilidad, persistencia y acceso multi-usuario.

## 📊 Análisis de la Situación Actual

### **Estructura de Datos LocalStorage**
```javascript
// Estructura actual en js/app.js
currentTestPlan = {
    id: "TP-1699123456789-0001",
    title: "User Authentication Test Plan", 
    reference: "JIRA-1234",
    requirements: "Users must be able to log in...",
    coverage: 80,
    minCases: 5,
    maxCases: 15,
    testCases: [
        {
            id: "TC-001",
            name: "Test login with valid credentials",
            description: "Verify successful login",
            priority: "High",
            preconditions: "System is accessible...",
            expectedResult: "User is logged in successfully",  
            testData: "Valid test data...",
            steps: [
                { number: 1, description: "Navigate to login page" },
                { number: 2, description: "Enter valid credentials" }
            ]
        }
    ],
    chatHistory: [
        { type: "user", content: "Add security test cases" },
        { type: "assistant", content: "I can help you..." }
    ],
    createdAt: "2024-01-15T10:30:00.000Z",
    lastModified: "2024-01-15T14:30:00.000Z"
}
```

### **Limitaciones Actuales**
- ❌ Datos solo locales (no compartibles)
- ❌ Sin backup automático
- ❌ Sin control de concurrencia
- ❌ Limitado por capacidad del navegador
- ❌ Sin auditoria de cambios
- ❌ Sin búsqueda avanzada

## 🏗️ Arquitectura Propuesta

### **Stack Tecnológico Híbrido**
```
Frontend (Existente) → API Gateway (EXISTENTE) → Lambda Functions → RDS MySQL + DynamoDB
     ↓                         ↓                      ↓              ↓
   HTML/CSS/JS         REST API - TEST_GENERATION_TOOL  Python 3.11   MySQL 8.0 + DynamoDB
```

### **API Gateway Existente**
- **ID**: `blnvunhvs3` 
- **Nombre**: REST API - TEST_GENERATION_TOOL
- **Tipo**: REGIONAL
- **Descripción**: API GATEWAY implementada en el TEST_GENERATION_TOOL
- **Creada**: 26 septiembre 2025
- **URL**: `https://blnvunhvs3.execute-api.eu-west-1.amazonaws.com/prod`

### **Arquitectura Híbrida**
- **RDS MySQL 8.0**: Almacenamiento principal para planes de prueba persistentes
- **DynamoDB**: Sesiones temporales y cache (mantienes funcionalidad existente)
- **S3**: Documentos y exportaciones (existente)
- **Python Lambda**: Todas las funciones en Python 3.11 (patrón consistente)
- **Amazon Bedrock**: Claude Sonnet 4 para generación IA (existente)

### **Componentes AWS**
- **RDS MySQL 8.0**: Base de datos principal para planes de prueba
- **DynamoDB**: Tabla `test-plan-sessions` (sesiones existentes)
- **S3**: Almacenamiento de documentos y exportaciones
- **API Gateway (EXISTENTE)**: REST API - TEST_GENERATION_TOOL
- **Lambda Functions**: Lógica de negocio en Python (nuevas CRUD + existentes)
- **Amazon Bedrock**: Servicios de IA
- **CloudWatch**: Monitoreo y logs

## 📊 Diseño de Base de Datos

### **Esquema Relacional**
```sql
-- Tabla principal: planes de prueba
test_plans (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    plan_id VARCHAR(50) UNIQUE,          -- TP-timestamp-random
    title VARCHAR(500) NOT NULL,
    reference VARCHAR(100),              -- Jira reference
    requirements TEXT,
    coverage_percentage TINYINT,
    min_test_cases TINYINT,
    max_test_cases TINYINT,
    selected_test_types JSON,            -- ["unit", "integration"]
    status ENUM('draft', 'active', 'completed', 'archived'),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
)

-- Tabla: casos de prueba
test_cases (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    test_plan_id BIGINT REFERENCES test_plans(id),
    case_id VARCHAR(20),                 -- TC-001, TC-002
    name VARCHAR(500),
    description TEXT,
    priority ENUM('High', 'Medium', 'Low'),
    preconditions TEXT,
    expected_result TEXT,
    test_data TEXT,
    case_order SMALLINT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
)

-- Tabla: pasos de prueba  
test_steps (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    test_case_id BIGINT REFERENCES test_cases(id),
    step_number TINYINT,
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- Tabla: historial de chat
chat_messages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    test_plan_id BIGINT REFERENCES test_plans(id),
    message_type ENUM('user', 'assistant'),
    content TEXT,
    message_order SMALLINT,
    created_at TIMESTAMP
)
```

## 🔧 Integración con API Gateway Existente

### **Recursos Actuales en REST API - TEST_GENERATION_TOOL**
```
✅ POST /generate-plan          - Generar plan de pruebas
✅ POST /create-manual-case     - Crear caso manual
✅ POST /upload-requirements    - Subir requerimientos
✅ POST /export-plan           - Exportar plan
✅ POST /hybrid_search         - Búsqueda híbrida
✅ POST /calculate-coverage    - Calcular cobertura
✅ POST /configure-plan        - Configurar plan
✅ PUT  /edit-case            - Editar caso
```

### **Nuevos Recursos CRUD a Añadir**

#### **POST /test-plans** - Crear Plan (Persistente)
```javascript
Request Body:
{
    "title": "User Authentication Test Plan",
    "reference": "JIRA-1234", 
    "requirements": "Users must be able to log in...",
    "coverage_percentage": 80,
    "min_test_cases": 5,
    "max_test_cases": 15,
    "selected_test_types": ["unit", "integration"]
}

Response:
{
    "success": true,
    "data": {
        "id": 123,
        "plan_id": "TP-1699123456789-0001",
        "title": "User Authentication Test Plan",
        "created_at": "2024-01-15T10:30:00.000Z"
    }
}
```

#### **GET /api/test-plans** - Listar Planes
```javascript
Query Parameters:
- page: número de página (default: 1)
- limit: elementos por página (default: 10)  
- status: filtro por estado
- search: búsqueda en título/requirements

Response:
{
    "success": true,
    "data": [
        {
            "id": 123,
            "plan_id": "TP-1699123456789-0001",
            "title": "User Authentication Test Plan",
            "reference": "JIRA-1234",
            "status": "draft",
            "test_cases_count": 8,
            "created_at": "2024-01-15T10:30:00.000Z"
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 5,
        "total_items": 48,
        "per_page": 10
    }
}
```

#### **GET /api/test-plans/{id}** - Obtener Plan Completo
```javascript
Response:
{
    "success": true,
    "data": {
        "id": 123,
        "plan_id": "TP-1699123456789-0001",
        "title": "User Authentication Test Plan",
        "reference": "JIRA-1234", 
        "requirements": "Users must be able to log in...",
        "coverage_percentage": 80,
        "min_test_cases": 5,
        "max_test_cases": 15,
        "selected_test_types": ["unit", "integration"],
        "status": "draft",
        "test_cases": [
            {
                "id": "TC-001",
                "name": "Test login with valid credentials",
                "description": "Verify successful login",
                "priority": "High",
                "preconditions": "System is accessible...",
                "expected_result": "User is logged in successfully",
                "test_data": "Valid test data...",
                "steps": [
                    { "number": 1, "description": "Navigate to login page" },
                    { "number": 2, "description": "Enter valid credentials" }
                ]
            }
        ],
        "chat_history": [
            { "type": "assistant", "content": "Test plan generated successfully!" }
        ],
        "created_at": "2024-01-15T10:30:00.000Z",
        "updated_at": "2024-01-15T14:30:00.000Z"  
    }
}
```

#### **PUT /api/test-plans/{id}** - Actualizar Plan
```javascript
Request Body:
{
    "title": "Updated Test Plan Title",
    "requirements": "Updated requirements...",
    "coverage_percentage": 90
}

Response:
{
    "success": true,
    "data": {
        "id": 123,
        "updated_at": "2024-01-15T16:30:00.000Z"
    }
}
```

#### **DELETE /api/test-plans/{id}** - Eliminar Plan (Soft Delete)
```javascript
Response:
{
    "success": true,
    "message": "Test plan deleted successfully"
}
```

### **2. Test Cases CRUD**

#### **POST /api/test-plans/{planId}/test-cases** - Crear Caso
```javascript
Request Body:
{
    "name": "Test login with valid credentials",
    "description": "Verify successful login", 
    "priority": "High",
    "preconditions": "System is accessible...",
    "expected_result": "User is logged in successfully",
    "test_data": "Valid test data...",
    "steps": [
        { "step_number": 1, "description": "Navigate to login page" },
        { "step_number": 2, "description": "Enter valid credentials" }
    ]
}
```

#### **PUT /api/test-cases/{id}** - Actualizar Caso
#### **DELETE /api/test-cases/{id}** - Eliminar Caso

### **3. Chat CRUD**

#### **POST /api/test-plans/{planId}/chat** - Enviar Mensaje
```javascript
Request Body:
{
    "message": "Add security test cases",
    "message_type": "user"
}

Response:
{
    "success": true,
    "data": {
        "user_message": {
            "id": 456,
            "content": "Add security test cases",
            "message_type": "user",
            "created_at": "2024-01-15T16:30:00.000Z"
        },
        "ai_response": {
            "id": 457, 
            "content": "I can help you add security test cases...",
            "message_type": "assistant",
            "created_at": "2024-01-15T16:30:05.000Z"
        }
    }
}
```

#### **GET /api/test-plans/{planId}/chat** - Obtener Historial

## 🚀 Plan de Implementación por Fases

### **FASE 1: Infraestructura AWS (Semana 1)**

#### **1.1 Configuración de VPC y Red**
```bash
# Scripts de AWS CLI
aws ec2 create-vpc --cidr-block 10.0.0.0/16
aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24
aws ec2 create-security-group --group-name test-plan-rds-sg
```

#### **1.2 Creación de RDS**
```bash
# Instancia MySQL 8.0
aws rds create-db-instance \
    --db-instance-identifier test-plan-generator-db \
    --db-instance-class db.t3.micro \
    --engine mysql \
    --engine-version 8.0.35 \
    --master-username admin \
    --master-user-password $DB_PASSWORD \
    --allocated-storage 20 \
    --db-name testplangenerator
```

#### **1.3 Creación de Tablas**
```sql
-- Ejecutar scripts SQL de creación de schema
-- Insertar datos de ejemplo para testing
-- Configurar índices para performance
```

### **FASE 2: Desarrollo de APIs Lambda (Semana 2-3)**

#### **2.1 Estructura de Funciones Lambda (Python)**
```
lambda-functions/
├── test_plans_crud/
│   ├── create_plan/
│   │   └── lambda_function.py      # POST /test-plans
│   ├── get_plans/
│   │   └── lambda_function.py      # GET /test-plans
│   ├── get_plan_by_id/
│   │   └── lambda_function.py      # GET /test-plans/{id}
│   ├── update_plan/
│   │   └── lambda_function.py      # PUT /test-plans/{id}
│   └── delete_plan/
│       └── lambda_function.py      # DELETE /test-plans/{id}
├── test_cases_crud/
│   ├── create_case/
│   │   └── lambda_function.py      # POST /test-plans/{id}/test-cases
│   ├── update_case/
│   │   └── lambda_function.py      # PUT /test-cases/{id}
│   └── delete_case/
│       └── lambda_function.py      # DELETE /test-cases/{id}
├── chat_crud/
│   ├── send_message/
│   │   └── lambda_function.py      # POST /test-plans/{id}/chat
│   └── get_history/
│       └── lambda_function.py      # GET /test-plans/{id}/chat
└── shared/
    ├── rds_connection.py           # Conexión a RDS MySQL
    ├── response_helpers.py         # Helpers para responses
    └── validation_utils.py         # Validación de inputs
```

#### **2.2 Ejemplo: Función Crear Plan (Python)**
```python
# lambda-functions/test_plans_crud/create_plan/lambda_function.py
import json
import logging
import pymysql
import uuid
import os
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """POST /test-plans - Crear plan de pruebas persistente en RDS"""
    logger.info("=== CREATE_PLAN STARTED ===")
    logger.info(f"Raw event received: {json.dumps(event, default=str)}")
    
    try:
        if event.get('httpMethod') == 'OPTIONS':
            logger.info("OPTIONS request detected, returning CORS response")
            return cors_response()
        
        logger.info("Processing POST request")
        
        # Manejo robusto del body - siguiendo patrón existente
        try:
            if 'body' in event:
                if event['body'] is None:
                    return error_response(400, 'Request body is null')
                
                if isinstance(event['body'], str):
                    body = json.loads(event['body'])
                else:
                    body = event['body']
            else:
                # Invocación directa
                body = event
                logger.info("Direct invocation detected, using event as body")
                
        except json.JSONDecodeError as e:
            return error_response(400, f'Invalid JSON in request body: {str(e)}')
        except Exception as e:
            return error_response(400, f'Error parsing request body: {str(e)}')
        
        # Validación de campos requeridos
        required_fields = ['title', 'requirements']
        missing_fields = [field for field in required_fields if field not in body]
        
        if missing_fields:
            return error_response(400, f'Missing required fields: {", ".join(missing_fields)}')
        
        # Validar tipos de prueba
        valid_test_types = ['unit', 'integration', 'performance', 'security', 'usability']
        selected_types = body.get('selected_test_types', [])
        
        if selected_types and not all(t in valid_test_types for t in selected_types):
            return error_response(400, f'Invalid test types. Must be one of: {", ".join(valid_test_types)}')
        
        # Validar porcentaje de cobertura
        coverage = body.get('coverage_percentage', 80)
        if not isinstance(coverage, (int, float)) or coverage < 10 or coverage > 100:
            return error_response(400, 'Coverage percentage must be between 10 and 100')
        
        # Generar plan_id único
        plan_id = f"TP-{int(datetime.now().timestamp())}-{str(uuid.uuid4())[:8].upper()}"
        current_time = datetime.utcnow()
        
        logger.info(f"Creating new test plan with ID: {plan_id}")
        
        # Conexión a RDS MySQL
        connection = get_rds_connection()
        
        try:
            with connection.cursor() as cursor:
                # Insertar plan en RDS
                sql = """
                    INSERT INTO test_plans 
                    (plan_id, title, reference, requirements, coverage_percentage, 
                     min_test_cases, max_test_cases, selected_test_types, status, 
                     created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(sql, (
                    plan_id,
                    body['title'],
                    body.get('reference'),
                    body['requirements'],
                    coverage,
                    body.get('min_test_cases', 5),
                    body.get('max_test_cases', 15),
                    json.dumps(selected_types),
                    'draft',
                    current_time,
                    current_time
                ))
                
                # Obtener el ID insertado
                plan_db_id = cursor.lastrowid
                
            connection.commit()
            logger.info(f"Test plan {plan_id} saved successfully to RDS")
            
            return success_response({
                'id': plan_db_id,
                'plan_id': plan_id,
                'title': body['title'],
                'status': 'draft',
                'created_at': current_time.isoformat(),
                'message': 'Test plan created successfully'
            })
            
        finally:
            connection.close()
        
    except Exception as e:
        logger.error(f"Error creating test plan: {str(e)}")
        return error_response(500, 'Internal server error', str(e))

def get_rds_connection():
    """Crear conexión a RDS MySQL"""
    return pymysql.connect(
        host=os.environ.get('RDS_HOST'),
        user=os.environ.get('RDS_USER'),
        password=os.environ.get('RDS_PASSWORD'),
        database=os.environ.get('RDS_DATABASE'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def success_response(data):
    return {
        'statusCode': 200,
        'headers': cors_headers(),
        'body': json.dumps({**data, 'timestamp': datetime.utcnow().isoformat()})
    }

def error_response(status_code, message, details=None):
    return {
        'statusCode': status_code,
        'headers': cors_headers(),
        'body': json.dumps({
            'error': message,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        })
    }

def cors_response():
    return {'statusCode': 200, 'headers': cors_headers(), 'body': ''}

def cors_headers():
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
```

#### **2.3 Configuración API Gateway (Usar API Existente)**
```bash
# Usar API Gateway existente
API_ID="blnvunhvs3"
ROOT_ID="u3l9nqqoma"

# Añadir nuevos recursos CRUD a la API existente

# 1. Crear recurso /test-plans
TEST_PLANS_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_ID \
    --path-part test-plans \
    --query 'id' \
    --output text)

# Métodos para /test-plans
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $TEST_PLANS_RESOURCE \
    --http-method GET \
    --authorization-type NONE

aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $TEST_PLANS_RESOURCE \
    --http-method POST \
    --authorization-type NONE

# 2. Crear recurso /test-plans/{id}
TEST_PLAN_ID_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $TEST_PLANS_RESOURCE \
    --path-part {id} \
    --query 'id' \
    --output text)

# Métodos para /test-plans/{id}
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $TEST_PLAN_ID_RESOURCE \
    --http-method GET \
    --authorization-type NONE

aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $TEST_PLAN_ID_RESOURCE \
    --http-method PUT \
    --authorization-type NONE

aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $TEST_PLAN_ID_RESOURCE \
    --http-method DELETE \
    --authorization-type NONE

# 3. Crear recurso /test-plans/{id}/test-cases
TEST_CASES_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $TEST_PLAN_ID_RESOURCE \
    --path-part test-cases \
    --query 'id' \
    --output text)

aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $TEST_CASES_RESOURCE \
    --http-method POST \
    --authorization-type NONE

# 4. Crear recurso /test-cases/{id}
TEST_CASE_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_ID \
    --path-part test-cases \
    --query 'id' \
    --output text)

TEST_CASE_ID_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $TEST_CASE_RESOURCE \
    --path-part {id} \
    --query 'id' \
    --output text)

aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $TEST_CASE_ID_RESOURCE \
    --http-method PUT \
    --authorization-type NONE

aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $TEST_CASE_ID_RESOURCE \
    --http-method DELETE \
    --authorization-type NONE

# 5. Crear recurso /test-plans/{id}/chat
CHAT_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $TEST_PLAN_ID_RESOURCE \
    --path-part chat \
    --query 'id' \
    --output text)

aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $CHAT_RESOURCE \
    --http-method GET \
    --authorization-type NONE

aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $CHAT_RESOURCE \
    --http-method POST \
    --authorization-type NONE
```

### **FASE 3: Migración del Frontend (Semana 4)**

#### **3.1 Crear Servicio API (js/api-service.js)**
```javascript
class APIService {
    constructor() {
        // Usar API Gateway existente: REST API - TEST_GENERATION_TOOL
        this.baseURL = 'https://blnvunhvs3.execute-api.eu-west-1.amazonaws.com/prod';
        this.headers = {
            'Content-Type': 'application/json',
            // Agregar autenticación si es necesario
        };
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.headers,
            ...options
        };
        
        const response = await fetch(url, config);
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        return await response.json();
    }
    
    // Test Plans
    async createTestPlan(planData) {
        return await this.request('/test-plans', {
            method: 'POST',
            body: JSON.stringify(planData)
        });
    }
    
    async getTestPlans(params = {}) {
        const query = new URLSearchParams(params).toString();
        return await this.request(`/test-plans?${query}`);
    }
    
    async getTestPlan(id) {
        return await this.request(`/test-plans/${id}`);
    }
    
    async updateTestPlan(id, planData) {
        return await this.request(`/test-plans/${id}`, {
            method: 'PUT',
            body: JSON.stringify(planData)
        });
    }
    
    async deleteTestPlan(id) {
        return await this.request(`/test-plans/${id}`, {
            method: 'DELETE'
        });
    }
    
    // Test Cases
    async createTestCase(planId, caseData) {
        return await this.request(`/test-plans/${planId}/test-cases`, {
            method: 'POST',
            body: JSON.stringify(caseData)
        });
    }
    
    async updateTestCase(caseId, caseData) {
        return await this.request(`/test-cases/${caseId}`, {
            method: 'PUT',
            body: JSON.stringify(caseData)
        });
    }
    
    async deleteTestCase(caseId) {
        return await this.request(`/test-cases/${caseId}`, {
            method: 'DELETE'
        });
    }
    
    // Chat
    async sendChatMessage(planId, message) {
        return await this.request(`/test-plans/${planId}/chat`, {
            method: 'POST',
            body: JSON.stringify({ message, message_type: 'user' })
        });
    }
    
    async getChatHistory(planId) {
        return await this.request(`/test-plans/${planId}/chat`);
    }
}

// Instancia global
window.apiService = new APIService();
```

#### **3.2 Modificar Funciones Existentes (js/app.js)**
```javascript
// Reemplazar función generateTestPlan
async function generateTestPlan() {
    const title = document.getElementById('plan-title').value.trim();
    const requirements = document.getElementById('requirements').value.trim();
    const coverage = document.getElementById('coverage').value;
    const minCases = parseInt(document.getElementById('min-cases').value);
    const maxCases = parseInt(document.getElementById('max-cases').value);
    const selectedTypes = [document.getElementById('selected-test-type').value];
    
    if (!title || !requirements) {
        alert('Please enter title and requirements');
        return;
    }
    
    const btn = event.target;
    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<div class="loading-spinner"></div> Generating test plan...';
    
    try {
        // Crear plan en base de datos
        const planResponse = await apiService.createTestPlan({
            title,
            requirements,
            coverage_percentage: parseInt(coverage),
            min_test_cases: minCases,
            max_test_cases: maxCases,
            selected_test_types: selectedTypes
        });
        
        currentTestPlan = planResponse.data;
        document.getElementById('plan-id').value = currentTestPlan.plan_id;
        
        // Generar casos de prueba (llamar Lambda de IA)
        // Aquí se integraría con la IA para generar casos
        
        // Mostrar resultados
        displayTestCases();
        showResultsSections();
        
    } catch (error) {
        console.error('Error generating test plan:', error);
        alert('Error generating test plan. Please try again.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
        updateGenerateButtonState();
    }
}

// Reemplazar función saveTestPlan  
async function saveTestPlan() {
    if (!currentTestPlan) {
        alert('No test plan to save');
        return;
    }
    
    try {
        const planData = {
            title: document.getElementById('plan-title').value,
            requirements: document.getElementById('requirements').value,
            coverage_percentage: parseInt(document.getElementById('coverage').value)
        };
        
        await apiService.updateTestPlan(currentTestPlan.id, planData);
        alert('Test plan saved successfully!');
        
    } catch (error) {
        console.error('Error saving test plan:', error);
        alert('Error saving test plan. Please try again.');
    }
}

// Reemplazar función para cargar planes
async function loadSavedPlans() {
    try {
        const response = await apiService.getTestPlans();
        const plans = response.data;
        
        // Mostrar planes en modal
        displaySavedPlans(plans);
        
    } catch (error) {
        console.error('Error loading plans:', error);
        alert('Error loading saved plans.');
    }
}
```

### **FASE 4: Migración de Datos (Semana 5)**

#### **4.1 Script de Migración desde LocalStorage**
```javascript
// migration/migrate-localstorage.js
async function migrateLocalStorageData() {
    const savedPlans = JSON.parse(localStorage.getItem('savedTestPlans') || '[]');
    
    if (savedPlans.length === 0) {
        console.log('No plans to migrate');
        return;
    }
    
    console.log(`Starting migration of ${savedPlans.length} plans...`);
    
    for (const plan of savedPlans) {
        try {
            // Crear plan en RDS
            const planResponse = await apiService.createTestPlan({
                title: plan.title,
                reference: plan.reference,
                requirements: plan.requirements,
                coverage_percentage: plan.coverage,
                min_test_cases: plan.minCases,
                max_test_cases: plan.maxCases,
                selected_test_types: plan.selectedTestTypes || []
            });
            
            const newPlanId = planResponse.data.id;
            
            // Migrar casos de prueba
            if (plan.testCases && plan.testCases.length > 0) {
                for (const testCase of plan.testCases) {
                    await apiService.createTestCase(newPlanId, {
                        name: testCase.name,
                        description: testCase.description,
                        priority: testCase.priority,
                        preconditions: testCase.preconditions,
                        expected_result: testCase.expectedResult,
                        test_data: testCase.testData,
                        steps: testCase.steps
                    });
                }
            }
            
            // Migrar historial de chat
            if (plan.chatHistory && plan.chatHistory.length > 0) {
                for (const message of plan.chatHistory) {
                    await apiService.sendChatMessage(newPlanId, message.content);
                }
            }
            
            console.log(`✅ Migrated plan: ${plan.title}`);
            
        } catch (error) {
            console.error(`❌ Failed to migrate plan: ${plan.title}`, error);
        }
    }
    
    console.log('Migration completed!');
    
    // Opcional: Limpiar localStorage después de migración exitosa
    // localStorage.removeItem('savedTestPlans');
}

// Ejecutar migración
// migrateLocalStorageData();
```

#### **4.2 Validación Post-Migración**
```javascript
// Verificar que todos los planes se migraron correctamente
async function validateMigration() {
    const response = await apiService.getTestPlans();
    console.log(`Total plans in database: ${response.pagination.total_items}`);
    
    // Comparar con LocalStorage
    const localPlans = JSON.parse(localStorage.getItem('savedTestPlans') || '[]');
    console.log(`Total plans in LocalStorage: ${localPlans.length}`);
}
```

### **FASE 5: Testing y Optimización (Semana 6)**

#### **5.1 Testing de APIs**
```javascript
// tests/api-tests.js
describe('Test Plans API', () => {
    test('should create test plan', async () => {
        const planData = {
            title: 'Test Plan API',
            requirements: 'API testing requirements',
            coverage_percentage: 80
        };
        
        const response = await apiService.createTestPlan(planData);
        expect(response.success).toBe(true);
        expect(response.data.title).toBe(planData.title);
    });
    
    test('should get test plans with pagination', async () => {
        const response = await apiService.getTestPlans({ page: 1, limit: 5 });
        expect(response.success).toBe(true);
        expect(response.data).toBeInstanceOf(Array);
        expect(response.pagination).toBeDefined();
    });
});
```

#### **5.2 Performance Testing**
```sql
-- Testing de consultas
EXPLAIN SELECT * FROM test_plans WHERE title LIKE '%authentication%';
EXPLAIN SELECT tp.*, COUNT(tc.id) as cases_count 
        FROM test_plans tp 
        LEFT JOIN test_cases tc ON tp.id = tc.test_plan_id 
        GROUP BY tp.id;
```

#### **5.3 Monitoreo CloudWatch**
```javascript
// Configurar métricas custom
const AWS = require('aws-sdk');
const cloudwatch = new AWS.CloudWatch();

async function logMetric(metricName, value, unit = 'Count') {
    await cloudwatch.putMetricData({
        Namespace: 'TestPlanGenerator',
        MetricData: [{
            MetricName: metricName,
            Value: value,
            Unit: unit,
            Timestamp: new Date()
        }]
    }).promise();
}
```

## 📋 Checklist de Implementación

### **Infraestructura**
- [ ] Crear VPC y subnets
- [ ] Configurar security groups
- [ ] Crear instancia RDS MySQL 8.0
- [ ] Ejecutar scripts de creación de tablas
- [ ] Configurar parameter groups optimizados
- [ ] Configurar backups automáticos

### **Backend APIs**
- [ ] Desarrollar Lambda functions para test-plans CRUD
- [ ] Desarrollar Lambda functions para test-cases CRUD  
- [ ] Desarrollar Lambda functions para chat CRUD
- [ ] Configurar API Gateway con recursos y métodos
- [ ] Implementar autenticación y autorización
- [ ] Configurar CORS policies

### **Frontend**
- [ ] Crear APIService class
- [ ] Modificar generateTestPlan() para usar APIs
- [ ] Modificar saveTestPlan() para usar APIs
- [ ] Modificar loadSavedPlans() para usar APIs
- [ ] Actualizar funciones de test cases CRUD
- [ ] Actualizar funciones de chat
- [ ] Implementar error handling robusto

### **Migración**
- [ ] Crear script de migración desde LocalStorage
- [ ] Testing de migración en entorno de desarrollo
- [ ] Validación de integridad de datos
- [ ] Plan de rollback en caso de problemas

### **Testing**
- [ ] Unit tests para Lambda functions
- [ ] Integration tests para APIs
- [ ] End-to-end tests para frontend
- [ ] Performance testing de consultas SQL
- [ ] Load testing de APIs

### **Deployment**
- [ ] Configurar CI/CD pipeline
- [ ] Deploy a entorno de staging
- [ ] User acceptance testing
- [ ] Deploy a producción
- [ ] Monitoreo post-deployment

## 📊 Estimación de Recursos y Costos

### **Recursos AWS (Mensual)**
```
RDS db.t3.micro (20GB):        ~$15-20
Lambda (1M requests):          ~$2-5  
API Gateway (1M requests):     ~$3-4
CloudWatch Logs:               ~$1-2
Data Transfer:                 ~$1-3

Total Estimado: $22-34/mes
```

### **Tiempo de Desarrollo**
```
Fase 1 - Infraestructura:     5-7 días
Fase 2 - APIs Backend:        10-14 días  
Fase 3 - Frontend:            7-10 días
Fase 4 - Migración:           3-5 días
Fase 5 - Testing:             5-7 días

Total: 30-43 días (6-8.5 semanas)
```

## 🚀 Siguientes Pasos

1. **Revisar y aprobar** este plan de implementación
2. **Configurar entorno AWS** con las credenciales necesarias
3. **Crear branch de desarrollo** para las modificaciones
4. **Comenzar con Fase 1**: Infraestructura AWS
5. **Desarrollo iterativo** con testing continuo
6. **Deploy gradual** con rollback plan

---

**Última actualización**: 9 de octubre de 2025  
**Versión del plan**: 1.0  
**Estado**: Pendiente de aprobación
