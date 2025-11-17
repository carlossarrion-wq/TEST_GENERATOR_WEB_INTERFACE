# Implementación de Integración Real con Jira

## Resumen

Se ha implementado la integración real con la API de Jira para obtener incidencias reales de los proyectos específicos de cada equipo, reemplazando el sistema de datos mock anterior.

## Cambios Realizados

### 1. Lambda Function: Jira Integration (`lambda_functions/jira_integration.py`)

**Descripción:** Nueva función Lambda que se conecta a la API REST de Jira para obtener incidencias reales.

**Características:**
- Obtiene credenciales de Jira desde AWS Secrets Manager
- Mapea equipos a proyectos Jira específicos:
  - `darwin` → Proyecto `GAESTG`
  - `mulesoft` → Proyecto `ICACEP`
  - `sap` → Proyecto `RE`
  - `saplcorp` → Proyecto `PDDSE2`
- Utiliza autenticación Basic Auth con API Token
- Transforma respuestas de Jira a formato simplificado
- Manejo robusto de errores y timeouts

**Endpoint:** `/api/jira` (POST)

**Request:**
```json
{
  "team": "darwin",
  "maxResults": 50
}
```

**Response:**
```json
{
  "success": true,
  "team": "darwin",
  "project_key": "GAESTG",
  "issues": [
    {
      "key": "GAESTG-123",
      "type": "story",
      "summary": "Título de la incidencia",
      "description": "Descripción detallada...",
      "status": "In Progress",
      "priority": "High",
      "assignee": "John Doe",
      "labels": ["tag1", "tag2"],
      "created": "2024-01-15T10:30:00Z",
      "updated": "2024-01-20T14:45:00Z"
    }
  ],
  "total_count": 15
}
```

### 2. Script de Despliegue (`lambda_functions/deploy_jira_integration.sh`)

**Descripción:** Script bash para desplegar la Lambda function de Jira.

**Características:**
- Instala dependencias (requests, boto3)
- Crea paquete de despliegue
- Crea o actualiza la función Lambda
- Configura permisos de API Gateway
- Timeout: 30 segundos
- Memoria: 512 MB

**Uso:**
```bash
cd lambda_functions
chmod +x deploy_jira_integration.sh
./deploy_jira_integration.sh
```

### 3. API Service (`js/api-service.js`)

**Nuevo método:** `fetchJiraIssues(team, maxResults)`

```javascript
async fetchJiraIssues(team, maxResults = 50) {
    return await this.request('/api/jira', 'POST', {
        team: team,
        maxResults: maxResults
    });
}
```

### 4. Frontend - Función `openJiraImportModal()` (`js/app.js`)

**Cambios principales:**
- Detecta el equipo del usuario desde `sessionStorage`
- Valida que el equipo tenga proyecto Jira configurado
- Llama a la API real en lugar de generar datos mock
- Muestra badge visual con el proyecto Jira en el header del modal
- Manejo de errores con opción de reintentar
- Mensajes de carga específicos ("Cargando incidencias reales de Jira...")

**Badge del proyecto:**
```html
<span style="...gradient background...">${projectInfo.key}</span>
```

### 5. Validación de Equipos

**Equipos válidos actualizados (eliminado "deltasmile"):**
- `darwin`
- `mulesoft`
- `sap`
- `saplcorp`

**Archivos actualizados:**
- `login.html`: Array `validTeams`
- `lambda_functions/iam_authenticator.py`: Diccionario `TEAM_KEYWORDS`
- `js/app.js`: Objeto `JIRA_PROJECTS_BY_TEAM`

### 6. Configuración de Proyectos Jira (`js/app.js`)

```javascript
const JIRA_PROJECTS_BY_TEAM = {
    darwin: {
        key: 'GAESTG',
        name: 'Gestión de Aplicaciones y Servicios TG',
        url: 'https://csarrion.atlassian.net/jira/core/projects/GAESTG'
    },
    mulesoft: {
        key: 'ICACEP',
        name: 'Integración y Conectividad de Aplicaciones CEP',
        url: 'https://csarrion.atlassian.net/jira/core/projects/ICACEP'
    },
    sap: {
        key: 'RE',
        name: 'Reingeniería',
        url: 'https://csarrion.atlassian.net/jira/core/projects/RE'
    },
    saplcorp: {
        key: 'PDDSE2',
        name: 'Plataforma de Desarrollo y Despliegue SE2',
        url: 'https://csarrion.atlassian.net/jira/core/projects/PDDSE2'
    }
};
```

## Configuración Requerida

### 1. AWS Secrets Manager

Crear un secreto con las credenciales de Jira:

**Nombre del secreto:** `prod/jira/credentials`

**Contenido (JSON):**
```json
{
  "jiraUrl": "https://csarrion.atlassian.net",
  "jiraEmail": "tu-email@example.com",
  "jiraApiToken": "tu-api-token-de-jira"
}
```

**Cómo obtener el API Token de Jira:**
1. Ir a https://id.atlassian.com/manage-profile/security/api-tokens
2. Hacer clic en "Create API token"
3. Dar un nombre descriptivo (ej: "Test Generator Integration")
4. Copiar el token generado

**Crear el secreto con AWS CLI:**
```bash
aws secretsmanager create-secret \
    --name prod/jira/credentials \
    --description "Jira API credentials for Test Generator" \
    --secret-string '{
        "jiraUrl": "https://csarrion.atlassian.net",
        "jiraEmail": "tu-email@example.com",
        "jiraApiToken": "tu-api-token"
    }' \
    --region eu-west-1
```

### 2. Permisos IAM para Lambda

La función Lambda necesita los siguientes permisos:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:eu-west-1:*:secret:prod/jira/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:eu-west-1:*:*"
    }
  ]
}
```

### 3. API Gateway

**Configurar endpoint en API Gateway:**

1. Crear recurso: `/api/jira`
2. Crear método: `POST`
3. Tipo de integración: Lambda Function
4. Función Lambda: `jira-integration`
5. Habilitar CORS
6. Desplegar a stage `prod`

**Configuración CORS:**
- Access-Control-Allow-Origin: `*`
- Access-Control-Allow-Headers: `Content-Type,Authorization`
- Access-Control-Allow-Methods: `GET,POST,OPTIONS`

## Flujo de Funcionamiento

1. **Usuario hace clic en "Importar desde Jira"**
   - Frontend detecta el equipo del usuario desde `sessionStorage`
   - Valida que el equipo tenga proyecto Jira configurado

2. **Llamada a la API**
   - Frontend llama a `/api/jira` con el equipo del usuario
   - Lambda obtiene credenciales de Secrets Manager
   - Lambda mapea equipo → proyecto Jira
   - Lambda hace request a Jira API REST

3. **Procesamiento de respuesta**
   - Lambda transforma issues de Jira a formato simplificado
   - Frontend recibe y muestra las incidencias reales
   - Usuario puede filtrar, buscar y seleccionar incidencias

4. **Importación**
   - Usuario selecciona una incidencia
   - Datos se importan al formulario de generación de plan de pruebas

## Manejo de Errores

### Frontend
- **Sin equipo asignado:** Muestra mensaje informativo
- **Error de API:** Muestra mensaje de error con opción de reintentar
- **Sin incidencias:** Muestra estado vacío con sugerencias

### Backend
- **Credenciales inválidas:** Error 401 con mensaje descriptivo
- **Proyecto no encontrado:** Error 400 con equipos válidos
- **Timeout de Jira:** Error 500 con mensaje de timeout
- **Rate limiting:** Manejo automático con retry

## Testing

### Test Manual

1. **Verificar credenciales en Secrets Manager:**
```bash
aws secretsmanager get-secret-value \
    --secret-id prod/jira/credentials \
    --region eu-west-1
```

2. **Test de Lambda directamente:**
```bash
aws lambda invoke \
    --function-name jira-integration \
    --payload '{"body": "{\"team\": \"darwin\", \"maxResults\": 5}"}' \
    --region eu-west-1 \
    response.json

cat response.json | jq
```

3. **Test desde frontend:**
   - Iniciar sesión con usuario de equipo darwin
   - Hacer clic en "Importar desde Jira"
   - Verificar que se muestran incidencias reales del proyecto GAESTG

### Verificación de Logs

```bash
# Ver logs de Lambda
aws logs tail /aws/lambda/jira-integration --follow --region eu-west-1

# Filtrar errores
aws logs filter-log-events \
    --log-group-name /aws/lambda/jira-integration \
    --filter-pattern "ERROR" \
    --region eu-west-1
```

## Métricas y Monitoreo

### CloudWatch Metrics
- Invocaciones de Lambda
- Duración de ejecución
- Errores
- Throttles

### Alarmas Recomendadas
1. **Error Rate > 5%:** Alerta si más del 5% de las llamadas fallan
2. **Duration > 25s:** Alerta si las llamadas tardan más de 25 segundos
3. **Throttles > 0:** Alerta si hay throttling

## Costos Estimados

**Por mes (uso moderado):**
- Lambda invocations (1000 calls): ~$0.20
- Lambda duration (512MB, 5s avg): ~$0.80
- Secrets Manager: ~$0.40
- API Gateway: ~$3.50
- **Total: ~$4.90/mes**

## Troubleshooting

### Problema: "Error al cargar incidencias"

**Posibles causas:**
1. Credenciales de Jira incorrectas o expiradas
2. API Token revocado
3. Permisos insuficientes en Jira
4. Proyecto Jira no existe o usuario sin acceso

**Solución:**
1. Verificar credenciales en Secrets Manager
2. Regenerar API Token si es necesario
3. Verificar permisos del usuario en Jira
4. Confirmar que los proyectos existen

### Problema: "Timeout"

**Posibles causas:**
1. Jira API lenta
2. Demasiadas incidencias
3. Timeout de Lambda muy corto

**Solución:**
1. Reducir `maxResults` en la llamada
2. Aumentar timeout de Lambda a 60s
3. Implementar paginación

### Problema: "Sin equipo asignado"

**Causa:** Usuario no tiene tag "Team" en IAM

**Solución:**
1. Agregar tag "Team" al usuario IAM
2. Valor debe ser uno de: darwin, mulesoft, sap, saplcorp
3. Re-autenticarse en la aplicación

## Próximos Pasos (Mejoras Futuras)

1. **Caché de incidencias:** Implementar caché en DynamoDB o ElastiCache
2. **Paginación:** Implementar scroll infinito para grandes volúmenes
3. **Filtros avanzados:** JQL personalizado por usuario
4. **Webhooks:** Sincronización en tiempo real
5. **Sincronización bidireccional:** Crear issues en Jira desde test cases
6. **Analytics:** Dashboard de uso y métricas

## Referencias

- [Jira REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

## Contacto y Soporte

Para problemas o preguntas sobre esta integración, contactar al equipo de desarrollo.

---

**Última actualización:** 14 de noviembre de 2025  
**Versión:** 1.0.0  
**Autor:** AI Assistant (Cline)
