# Approach de Integración con Jira

## Visión General

Este documento describe el enfoque técnico para integrar la aplicación de generación de planes de prueba con Jira, permitiendo importar issues/historias de usuario como base para generar casos de prueba.

## Arquitectura de la Integración

### 1. Componentes Principales

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Frontend      │────────▶│  Lambda Function │────────▶│   Jira API      │
│   (Web App)     │◀────────│  (AWS Lambda)    │◀────────│   (REST API)    │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

### 2. Flujo de Integración

#### Fase 1: Autenticación con Jira
1. **Configuración de Credenciales:**
   - API Token de Jira (almacenado en AWS Secrets Manager)
   - URL de la instancia de Jira
   - Email del usuario

2. **Métodos de Autenticación:**
   - Basic Auth (email + API token)
   - OAuth 2.0 (para mayor seguridad en producción)

#### Fase 2: Importación de Issues

**Endpoint Lambda:** `/jira/import`

**Request:**
```json
{
  "jiraUrl": "https://your-domain.atlassian.net",
  "projectKey": "PROJ",
  "filters": {
    "issueTypes": ["Story", "Epic", "Task"],
    "status": ["To Do", "In Progress"],
    "labels": ["testing", "qa"],
    "sprint": "Sprint 23"
  },
  "maxResults": 50
}
```

**Response:**
```json
{
  "success": true,
  "issues": [
    {
      "id": "PROJ-123",
      "key": "PROJ-123",
      "summary": "Implementar login de usuario",
      "description": "Como usuario quiero poder...",
      "issueType": "Story",
      "priority": "High",
      "status": "In Progress",
      "assignee": "john.doe@company.com",
      "labels": ["authentication", "security"],
      "customFields": {
        "acceptanceCriteria": "...",
        "storyPoints": 5
      }
    }
  ],
  "totalCount": 45
}
```

#### Fase 3: Generación de Plan de Pruebas desde Jira

**Endpoint Lambda:** `/testplan/generate-from-jira`

**Request:**
```json
{
  "jiraIssues": ["PROJ-123", "PROJ-124", "PROJ-125"],
  "planTitle": "Plan de Pruebas - Sprint 23",
  "coveragePercentage": 80,
  "minTestCases": 10,
  "maxTestCases": 30,
  "includeAcceptanceCriteria": true,
  "testTypes": ["functional", "integration", "e2e"]
}
```

**Proceso:**
1. Recuperar detalles completos de los issues de Jira
2. Extraer acceptance criteria y descripción
3. Analizar con IA (Bedrock) para generar casos de prueba
4. Mapear prioridad de issue a prioridad de test cases
5. Generar casos de prueba estructurados

## Implementación Técnica

### 1. Función Lambda - Estructura

```
lambda-jira-integration/
├── src/
│   ├── handlers/
│   │   ├── jiraImport.js          # Importar issues de Jira
│   │   ├── jiraAuth.js            # Autenticación con Jira
│   │   └── testPlanGenerator.js   # Generar plan desde Jira
│   ├── services/
│   │   ├── jiraClient.js          # Cliente HTTP para Jira API
│   │   └── bedrockService.js      # Servicio de IA (Bedrock)
│   ├── utils/
│   │   ├── jiraParser.js          # Parser de respuestas Jira
│   │   ├── testCaseMapper.js      # Mapeo issue → test case
│   │   └── validators.js          # Validación de datos
│   └── index.js                   # Entry point
├── tests/
│   └── unit/
├── package.json
└── serverless.yml                 # Configuración Serverless Framework
```

### 2. Jira REST API - Endpoints Clave

#### Buscar Issues (JQL)
```
GET /rest/api/3/search
Query Parameters:
  - jql: project = PROJ AND type = Story
  - fields: summary,description,priority,status,assignee
  - maxResults: 50
  - startAt: 0
```

#### Obtener Issue Individual
```
GET /rest/api/3/issue/{issueIdOrKey}
Query Parameters:
  - fields: *all
  - expand: renderedFields,changelog
```

#### Obtener Campos Personalizados
```
GET /rest/api/3/field
```

### 3. Mapeo de Datos Jira → Test Cases

| Campo Jira | Campo Test Case | Transformación |
|------------|-----------------|----------------|
| Summary | Test Case Name | Directo |
| Description | Test Description | Extraer contexto |
| Acceptance Criteria | Expected Result | Parsear criterios |
| Priority | Test Priority | Mapeo: High→High, Medium→Medium, Low→Low |
| Story Points | Test Complexity | Estimación de pasos |
| Labels | Test Tags | Directo |
| Components | Test Categories | Agrupación |

### 4. Prompt Engineering para IA

**Template de Prompt:**
```
Eres un experto QA Engineer. Genera casos de prueba detallados basados en el siguiente issue de Jira:

ISSUE: {issueKey}
TÍTULO: {summary}
DESCRIPCIÓN: {description}
CRITERIOS DE ACEPTACIÓN:
{acceptanceCriteria}

PRIORIDAD: {priority}
TIPO: {issueType}

REQUISITOS:
- Generar entre {minTestCases} y {maxTestCases} casos de prueba
- Cobertura objetivo: {coveragePercentage}%
- Incluir casos positivos y negativos
- Considerar edge cases
- Cada caso debe tener: ID, Nombre, Descripción, Prioridad, Precondiciones, Pasos, Resultado Esperado, Datos de Prueba

FORMATO DE SALIDA: JSON
```

### 5. Optimización

**Estrategia de Caché:**
- Caché en memoria de Lambda (para requests dentro de la misma ejecución)
- Lambda mantiene conexiones HTTP reutilizables
- Respuestas comprimidas (gzip) desde Jira API
- Paginación eficiente para grandes volúmenes de issues

### 6. Seguridad

#### Almacenamiento de Credenciales
```javascript
// AWS Secrets Manager
{
  "jiraApiToken": "ATATT3xFfGF0...",
  "jiraEmail": "user@company.com",
  "jiraUrl": "https://company.atlassian.net"
}
```

#### Variables de Entorno Lambda
```yaml
environment:
  JIRA_SECRET_NAME: prod/jira/credentials
  BEDROCK_MODEL_ID: anthropic.claude-3-sonnet-20240229-v1:0
  AWS_REGION: eu-west-1
```

#### IAM Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:prod/jira/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    }
  ]
}
```

## Casos de Uso

### Caso 1: Importar Issues de un Sprint
```javascript
// Frontend request
const response = await fetch('/api/jira/import', {
  method: 'POST',
  body: JSON.stringify({
    projectKey: 'ECOM',
    filters: {
      sprint: 'Sprint 23',
      issueTypes: ['Story', 'Bug']
    }
  })
});
```

### Caso 2: Generar Plan desde Issues Seleccionados
```javascript
// Usuario selecciona 5 issues en la UI
const selectedIssues = ['ECOM-101', 'ECOM-102', 'ECOM-103', 'ECOM-104', 'ECOM-105'];

const testPlan = await fetch('/api/testplan/generate-from-jira', {
  method: 'POST',
  body: JSON.stringify({
    jiraIssues: selectedIssues,
    planTitle: 'Plan de Pruebas - Checkout Flow',
    coveragePercentage: 85,
    minTestCases: 15,
    maxTestCases: 25
  })
});
```

### Caso 3: Sincronización Bidireccional (Futuro)
- Crear issues en Jira desde test cases fallidos
- Actualizar estado de issues cuando tests pasan
- Vincular test cases con issues (trazabilidad)

## Manejo de Errores

### Errores Comunes y Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| 401 Unauthorized | Token inválido | Renovar API token |
| 404 Not Found | Issue no existe | Validar issue key |
| 429 Rate Limit | Demasiadas requests | Implementar backoff exponencial |
| 500 Jira Error | Error en Jira | Retry con backoff |
| Timeout | Request lento | Aumentar timeout, paginar |

### Estrategia de Retry
```javascript
const retryConfig = {
  maxRetries: 3,
  backoffMultiplier: 2,
  initialDelay: 1000,
  maxDelay: 10000,
  retryableErrors: [429, 500, 502, 503, 504]
};
```

## Métricas y Monitoreo

### CloudWatch Metrics
- `JiraAPICallCount` - Número de llamadas a Jira API
- `JiraAPILatency` - Latencia de llamadas
- `TestPlanGenerationTime` - Tiempo de generación
- `ErrorRate` - Tasa de errores por tipo
- `BedrockInvocationCount` - Número de invocaciones a Bedrock

### CloudWatch Logs
```javascript
// Structured logging
logger.info('Jira import started', {
  projectKey: 'PROJ',
  filterCount: 3,
  requestId: context.requestId
});
```

## Roadmap de Implementación

### Fase 1: MVP (2 semanas)
- [x] Diseño de interfaz con modal de Jira
- [ ] Lambda básica para importar issues
- [ ] Autenticación con API token
- [ ] Búsqueda simple por proyecto
- [ ] Generación de test plan desde 1 issue

### Fase 2: Funcionalidad Completa (3 semanas)
- [ ] Filtros avanzados (JQL)
- [ ] Generación desde múltiples issues
- [ ] Mapeo inteligente de campos
- [ ] Manejo robusto de errores
- [ ] Optimización de llamadas a Jira API

### Fase 3: Optimización (2 semanas)
- [ ] Paginación de resultados
- [ ] Búsqueda incremental
- [ ] Webhooks de Jira
- [ ] Sincronización bidireccional
- [ ] Analytics y métricas

## Consideraciones Adicionales

### Escalabilidad
- Lambda puede procesar hasta 1000 issues concurrentemente
- API Gateway con throttling configurado
- Procesamiento paralelo de múltiples issues
- Timeout de Lambda: 5 minutos (ajustable según necesidad)

### Costos Estimados (mensual)
- Lambda: ~$5 (1M invocaciones)
- Secrets Manager: ~$0.40
- API Gateway: ~$3.50
- Bedrock (Claude 3 Sonnet): ~$10-15 (según uso)
- **Total: ~$19-24/mes** (uso moderado)

### Alternativas Consideradas
1. **Jira Webhooks:** Para sincronización en tiempo real
2. **Jira Connect App:** Para integración más profunda
3. **GraphQL API:** Para queries más eficientes (Jira Cloud)
4. **ElastiCache/Redis:** Para caché distribuido (descartado por simplicidad y costos)
5. **DynamoDB:** Para persistencia de caché (descartado - no necesario para MVP)

## Conclusión

Este approach proporciona una integración robusta, escalable y segura con Jira, permitiendo a los usuarios importar issues y generar planes de prueba de forma automática. La arquitectura serverless sin estado (stateless) garantiza simplicidad, costos bajos y alta disponibilidad. Al eliminar DynamoDB del diseño, reducimos la complejidad operacional y los puntos de fallo, manteniendo un diseño limpio y eficiente.

## Referencias

- [Jira REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Serverless Framework Documentation](https://www.serverless.com/framework/docs)
