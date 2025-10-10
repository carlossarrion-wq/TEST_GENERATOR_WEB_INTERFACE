# 🚀 Lambda Desplegada en AWS

## ✅ Despliegue Exitoso

**Fecha**: 10/01/2025
**Región**: eu-west-1 (Irlanda)
**Stage**: dev
**Stack**: test-plan-generator-jira-dev

## 📡 API Endpoints

### Base URL
```
https://2xlh113423.execute-api.eu-west-1.amazonaws.com/dev
```

### Endpoints Disponibles

#### 1. Importar Issues de Jira
```
POST https://2xlh113423.execute-api.eu-west-1.amazonaws.com/dev/jira/import
```

**Request Body:**
```json
{
  "projectKey": "PDDSE2",
  "maxResults": 10
}
```

**Con filtros:**
```json
{
  "projectKey": "PDDSE2",
  "filters": {
    "issueTypes": ["Story", "Bug"],
    "status": ["To Do", "In Progress"]
  },
  "maxResults": 20
}
```

#### 2. Obtener Issues Específicos
```
POST https://2xlh113423.execute-api.eu-west-1.amazonaws.com/dev/jira/issues
```

**Request Body:**
```json
{
  "issueKeys": ["PDDSE2-1", "PDDSE2-2", "PDDSE2-3"]
}
```

#### 3. Endpoints Alternativos (mismo comportamiento)
```
POST https://2xlh113423.execute-api.eu-west-1.amazonaws.com/dev/import
POST https://2xlh113423.execute-api.eu-west-1.amazonaws.com/dev/issues
```

## 🔧 Funciones Lambda Desplegadas

| Función | ARN | Tamaño |
|---------|-----|--------|
| jiraIntegration | arn:aws:lambda:eu-west-1:701055077130:function:test-plan-generator-jira-dev-jiraIntegration:1 | 895 kB |
| jiraImport | arn:aws:lambda:eu-west-1:701055077130:function:test-plan-generator-jira-dev-jiraImport:1 | 895 kB |
| getIssues | arn:aws:lambda:eu-west-1:701055077130:function:test-plan-generator-jira-dev-getIssues:1 | 895 kB |

## 🔐 Configuración

### Variables de Entorno (Configuradas)
- ✅ JIRA_URL: https://csarrion.atlassian.net
- ✅ JIRA_EMAIL: carlos.sarrion@es.ibm.com
- ✅ JIRA_API_TOKEN: Configurado
- ✅ AWS_NODEJS_CONNECTION_REUSE_ENABLED: 1

### Configuración Lambda
- **Runtime**: Node.js 18.x
- **Memoria**: 512 MB
- **Timeout**: 30 segundos
- **CORS**: Habilitado

## 📝 Ejemplos de Uso

### Ejemplo 1: Importar issues con curl

```bash
curl -X POST https://2xlh113423.execute-api.eu-west-1.amazonaws.com/dev/jira/import \
  -H "Content-Type: application/json" \
  -d '{
    "projectKey": "PDDSE2",
    "maxResults": 5
  }'
```

### Ejemplo 2: Obtener issues específicos

```bash
curl -X POST https://2xlh113423.execute-api.eu-west-1.amazonaws.com/dev/jira/issues \
  -H "Content-Type: application/json" \
  -d '{
    "issueKeys": ["PDDSE2-1", "PDDSE2-2"]
  }'
```

### Ejemplo 3: Desde JavaScript (Frontend)

```javascript
// Importar issues
const response = await fetch('https://2xlh113423.execute-api.eu-west-1.amazonaws.com/dev/jira/import', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    projectKey: 'PDDSE2',
    filters: {
      issueTypes: ['Story'],
      status: ['To Do']
    },
    maxResults: 10
  })
});

const data = await response.json();
console.log('Issues:', data.issues);
console.log('Total:', data.pagination.total);
```

## 🧪 Testing en Producción

### Test Rápido
```bash
# Test de conectividad
curl -X POST https://2xlh113423.execute-api.eu-west-1.amazonaws.com/dev/jira/import \
  -H "Content-Type: application/json" \
  -d '{"projectKey":"PDDSE2","maxResults":1}'
```

**Respuesta Esperada:**
```json
{
  "success": true,
  "issues": [],
  "pagination": {
    "total": 0,
    "startAt": 0,
    "maxResults": 1,
    "returned": 0
  },
  "statistics": {
    "total": 0,
    "byStatus": {},
    "byPriority": {},
    "byIssueType": {}
  },
  "query": {
    "jql": "project = PDDSE2",
    "executedAt": "2025-01-10T..."
  }
}
```

## 📊 Monitoreo

### CloudWatch Logs
```bash
# Ver logs en tiempo real
serverless logs -f jiraImport --tail

# Ver logs de las últimas 2 horas
serverless logs -f jiraImport --startTime 2h
```

### CloudWatch Metrics
- Invocaciones
- Errores
- Duración
- Throttles

**Acceso**: AWS Console → CloudWatch → Logs → `/aws/lambda/test-plan-generator-jira-dev-*`

## 🔄 Actualizar Despliegue

```bash
# Redesplegar después de cambios
cd lambda
serverless deploy --stage dev

# Desplegar solo una función
serverless deploy function -f jiraImport --stage dev
```

## 🗑️ Eliminar Despliegue

```bash
# CUIDADO: Esto eliminará todos los recursos
cd lambda
serverless remove --stage dev
```

## 🔗 Integración con Frontend

### Actualizar en tu aplicación web

En tu archivo `js/app.js`, actualiza la URL base:

```javascript
const LAMBDA_API_BASE = 'https://2xlh113423.execute-api.eu-west-1.amazonaws.com/dev';

// Función para importar issues
async function importJiraIssues(projectKey, filters = {}) {
  const response = await fetch(`${LAMBDA_API_BASE}/jira/import`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      projectKey,
      filters,
      maxResults: 50
    })
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}

// Uso
try {
  const result = await importJiraIssues('PDDSE2', {
    issueTypes: ['Story', 'Bug'],
    status: ['To Do']
  });
  
  console.log(`Found ${result.pagination.total} issues`);
  result.issues.forEach(issue => {
    console.log(`${issue.key}: ${issue.summary}`);
  });
} catch (error) {
  console.error('Error importing issues:', error);
}
```

## 💰 Costos Estimados

**Uso Moderado (1000 requests/día):**
- Lambda: ~$0.20/mes
- API Gateway: ~$3.50/mes
- CloudWatch Logs: ~$0.50/mes
- **Total: ~$4.20/mes**

## 📚 Recursos Adicionales

- [AWS Lambda Console](https://eu-west-1.console.aws.amazon.com/lambda/home?region=eu-west-1#/functions)
- [API Gateway Console](https://eu-west-1.console.aws.amazon.com/apigateway/home?region=eu-west-1)
- [CloudWatch Logs](https://eu-west-1.console.aws.amazon.com/cloudwatch/home?region=eu-west-1#logsV2:log-groups)

## ✅ Estado Actual

- ✅ Lambda desplegada y funcionando
- ✅ API Gateway configurado
- ✅ CORS habilitado
- ✅ Credenciales de Jira configuradas
- ✅ Logs habilitados
- ✅ Retry automático configurado
- ✅ Manejo de errores robusto

**La Lambda está lista para recibir requests desde tu aplicación web.**
