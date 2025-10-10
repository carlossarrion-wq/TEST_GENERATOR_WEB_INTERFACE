# Test Plan Generator - Jira Integration Lambda

AWS Lambda function para integración con Jira. Permite importar issues de Jira para su uso en la generación de planes de prueba.

## 📋 Características

- **Importación de Issues**: Buscar y recuperar issues de Jira usando JQL
- **Obtención de Issues Específicos**: Recuperar issues por sus keys
- **Parsing y Normalización**: Transformación de datos de Jira a formato estándar
- **Manejo de Errores**: Retry automático y mensajes de error descriptivos
- **CORS Habilitado**: Listo para consumo desde frontend

## 🏗️ Estructura del Proyecto

```
lambda/
├── src/
│   ├── handlers/
│   │   ├── jiraImport.js       # Handler para importar issues
│   │   └── getIssues.js        # Handler para obtener issues específicos
│   ├── services/
│   │   └── jiraClient.js       # Cliente HTTP para Jira API
│   ├── utils/
│   │   ├── validators.js       # Validación de requests
│   │   └── jiraParser.js       # Parsing de respuestas Jira
│   ├── config/
│   │   ├── jira-credentials.json           # Credenciales (NO subir a Git)
│   │   └── jira-credentials.example.json   # Plantilla de ejemplo
│   └── index.js                # Entry point principal
├── tests/
│   └── unit/                   # Tests unitarios
├── package.json
├── serverless.yml              # Configuración Serverless Framework
└── README.md
```

## 🚀 Instalación

### 1. Instalar Dependencias

```bash
cd lambda
npm install
```

### 2. Configurar Credenciales de Jira

Copia el archivo de ejemplo y completa con tus credenciales:

```bash
cp src/config/jira-credentials.example.json src/config/jira-credentials.json
```

Edita `src/config/jira-credentials.json`:

```json
{
  "jiraUrl": "https://your-domain.atlassian.net",
  "jiraEmail": "your-email@company.com",
  "jiraApiToken": "YOUR_JIRA_API_TOKEN_HERE"
}
```

**Cómo obtener un API Token de Jira:**
1. Ve a https://id.atlassian.com/manage-profile/security/api-tokens
2. Click en "Create API token"
3. Dale un nombre descriptivo
4. Copia el token generado

### 3. Instalar Serverless Framework (opcional)

```bash
npm install -g serverless
```

## 🧪 Desarrollo Local

### Ejecutar en Modo Offline

```bash
npm run invoke:local -- -f jiraImport -p test-event.json
```

O con serverless-offline:

```bash
serverless offline
```

La API estará disponible en `http://localhost:3001`

### Ejemplo de Test Event

Crea un archivo `test-event.json`:

```json
{
  "httpMethod": "POST",
  "path": "/jira/import",
  "body": "{\"projectKey\":\"PROJ\",\"maxResults\":10}"
}
```

## 📡 API Endpoints

### 1. Importar Issues de Jira

**Endpoint:** `POST /jira/import`

**Request Body:**
```json
{
  "projectKey": "PROJ",
  "filters": {
    "issueTypes": ["Story", "Bug"],
    "status": ["To Do", "In Progress"],
    "labels": ["testing"],
    "sprint": "Sprint 23"
  },
  "maxResults": 50,
  "startAt": 0
}
```

**Response:**
```json
{
  "success": true,
  "issues": [
    {
      "id": "10001",
      "key": "PROJ-123",
      "summary": "Implementar login",
      "description": "...",
      "issueType": "Story",
      "priority": "High",
      "status": "In Progress",
      "assignee": {...},
      "labels": ["authentication"],
      "created": "2025-01-09T10:00:00Z",
      "updated": "2025-01-09T15:00:00Z",
      "customFields": {...}
    }
  ],
  "pagination": {
    "total": 45,
    "startAt": 0,
    "maxResults": 50,
    "returned": 45
  },
  "statistics": {
    "total": 45,
    "byStatus": {...},
    "byPriority": {...},
    "byIssueType": {...}
  },
  "query": {
    "jql": "project = PROJ AND type in (\"Story\",\"Bug\")",
    "executedAt": "2025-01-09T15:30:00Z"
  }
}
```

### 2. Obtener Issues Específicos

**Endpoint:** `POST /jira/issues`

**Request Body:**
```json
{
  "issueKeys": ["PROJ-123", "PROJ-124", "PROJ-125"]
}
```

**Response:**
```json
{
  "success": true,
  "issues": [...],
  "summary": {
    "requested": 3,
    "found": 3,
    "missing": 0,
    "missingKeys": []
  },
  "fetchedAt": "2025-01-09T15:30:00Z"
}
```

## 🚢 Despliegue

### Desplegar a AWS

```bash
# Desarrollo
npm run deploy:dev

# Producción
npm run deploy:prod

# Región específica
serverless deploy --region us-east-1 --stage prod
```

### Variables de Entorno en AWS

Si prefieres usar variables de entorno en lugar del archivo de configuración:

```bash
serverless deploy --stage prod \
  --param="jiraUrl=https://your-domain.atlassian.net" \
  --param="jiraEmail=your-email@company.com" \
  --param="jiraApiToken=YOUR_TOKEN"
```

O configura en `serverless.yml`:

```yaml
provider:
  environment:
    JIRA_URL: ${param:jiraUrl}
    JIRA_EMAIL: ${param:jiraEmail}
    JIRA_API_TOKEN: ${param:jiraApiToken}
```

## 🧪 Testing

```bash
# Ejecutar tests
npm test

# Tests con coverage
npm run test:coverage

# Tests en modo watch
npm run test:watch
```

## 📊 Logs

### Ver logs en AWS

```bash
# Logs de función específica
serverless logs -f jiraImport --tail

# Logs de todas las funciones
serverless logs --tail
```

## 🔧 Configuración Avanzada

### Timeout y Memoria

Edita `serverless.yml`:

```yaml
provider:
  memorySize: 1024  # MB
  timeout: 60       # segundos
```

### Retry Strategy

El cliente de Jira tiene retry automático configurado:
- 3 reintentos máximo
- Backoff exponencial
- Retry en errores 429, 5xx

Para modificar, edita `src/services/jiraClient.js`:

```javascript
axiosRetry(this.client, {
  retries: 5,  // Cambiar número de reintentos
  retryDelay: axiosRetry.exponentialDelay
});
```

## 🐛 Troubleshooting

### Error: "Jira credentials not found"

Asegúrate de que existe `src/config/jira-credentials.json` con las credenciales correctas.

### Error: "Authentication failed"

Verifica que:
1. El API token es válido
2. El email es correcto
3. Tienes permisos en el proyecto de Jira

### Error: "Rate limit exceeded"

Jira tiene límites de rate:
- Cloud: ~100 requests/minuto
- Server: Depende de configuración

La función reintentará automáticamente después de un delay.

### Error: "Cannot connect to Jira"

Verifica que:
1. La URL de Jira es correcta
2. Tienes conectividad a internet
3. No hay firewall bloqueando

## 📝 Ejemplos de Uso

### Buscar todos los bugs de un proyecto

```bash
curl -X POST https://your-api.execute-api.eu-west-1.amazonaws.com/dev/jira/import \
  -H "Content-Type: application/json" \
  -d '{
    "projectKey": "PROJ",
    "filters": {
      "issueTypes": ["Bug"]
    }
  }'
```

### Buscar issues de un sprint específico

```bash
curl -X POST https://your-api.execute-api.eu-west-1.amazonaws.com/dev/jira/import \
  -H "Content-Type: application/json" \
  -d '{
    "projectKey": "PROJ",
    "filters": {
      "sprint": "Sprint 23",
      "status": ["In Progress", "To Do"]
    }
  }'
```

### Obtener issues específicos

```bash
curl -X POST https://your-api.execute-api.eu-west-1.amazonaws.com/dev/jira/issues \
  -H "Content-Type: application/json" \
  -d '{
    "issueKeys": ["PROJ-123", "PROJ-124"]
  }'
```

## 🔐 Seguridad

- ✅ Credenciales nunca en el código
- ✅ Archivo de credenciales en `.gitignore`
- ✅ HTTPS para comunicación con Jira
- ✅ Validación de inputs
- ✅ CORS configurado
- ✅ IAM roles con permisos mínimos

## 📚 Recursos

- [Jira REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Serverless Framework](https://www.serverless.com/framework/docs)

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

MIT License
