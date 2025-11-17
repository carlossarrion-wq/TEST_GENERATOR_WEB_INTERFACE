# Solución al Error de CORS - Integración Jira

## 🎯 Problema Resuelto

Se ha solucionado el error de CORS que impedía la comunicación entre el frontend (localhost:8000) y la API de AWS Lambda para obtener tickets reales de Jira.

**Error Original:**
```
Access to fetch at 'https://2xlh113423.execute-api.eu-west-1.amazonaws.com/prod/api/jira' 
from origin 'http://localhost:8000' has been blocked by CORS policy: 
Response to preflight request doesn't pass access control check: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## ✅ Solución Implementada

### 1. Nueva Función Lambda en Python
- **Nombre:** `jira-integration-python`
- **Runtime:** Python 3.11
- **Handler:** `jira_integration.lambda_handler`
- **Región:** eu-west-1
- **ARN:** `arn:aws:lambda:eu-west-1:701055077130:function:jira-integration-python`

### 2. Headers CORS Mejorados
La función Lambda ahora incluye headers CORS completos:
```python
headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token,Accept',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
    'Access-Control-Max-Age': '86400',
    'Content-Type': 'application/json'
}
```

### 3. Configuración API Gateway
- **Endpoint:** `https://2xlh113423.execute-api.eu-west-1.amazonaws.com/prod/api/jira`
- **Método POST:** Integrado con la función Lambda Python
- **Método OPTIONS:** Configurado con MOCK para responder a preflight requests
- **Resource ID:** 2h6kfg

### 4. Mapeo de Equipos a Proyectos Jira

La función Lambda mapea automáticamente cada equipo a su proyecto Jira correspondiente:

| Equipo | Proyecto Jira | URL del Proyecto |
|--------|---------------|------------------|
| darwin | GAESTG | https://csarrion.atlassian.net/jira/core/projects/GAESTG |
| mulesoft | ICACEP | https://csarrion.atlassian.net/jira/core/projects/ICACEP |
| sap | RE | https://csarrion.atlassian.net/jira/core/projects/RE |
| saplcorp | PDDSE2 | https://csarrion.atlassian.net/jira/core/projects/PDDSE2 |

## 🔧 Cambios Realizados

### Archivos Modificados:
1. **lambda_functions/jira_integration.py**
   - Mejorados los headers CORS
   - Agregado logging para debugging
   - Manejo mejorado de peticiones OPTIONS

2. **lambda_functions/configure_api_gateway_jira.sh**
   - Actualizado para incluir headers CORS completos
   - Agregado Access-Control-Max-Age

### Archivos Creados:
1. **lambda_functions/jira_integration.zip** - Paquete de despliegue
2. **lambda_functions/configure_cors.ps1** - Script de configuración CORS
3. **lambda_functions/cors_headers.json** - Configuración de headers CORS

## 📋 Cómo Funciona

### Flujo de Petición:

1. **Usuario hace clic en "Importar desde Jira"**
   - El frontend obtiene el equipo del usuario desde `sessionStorage.getItem('user_team')`
   - Ejemplo: `user_team = 'sap'`

2. **Frontend envía petición POST**
   ```javascript
   await window.apiService.fetchJiraIssues('sap', 50)
   ```

3. **Navegador envía preflight OPTIONS** (automático)
   - API Gateway responde con headers CORS desde el método OPTIONS (MOCK)

4. **Navegador envía petición POST real**
   - API Gateway invoca la función Lambda Python
   - Lambda obtiene credenciales de AWS Secrets Manager
   - Lambda consulta la API de Jira con el proyecto correspondiente (RE para sap)
   - Lambda transforma y devuelve los tickets REALES

5. **Frontend recibe los tickets**
   - Los tickets se muestran en el modal de importación
   - Usuario puede seleccionar un ticket para importar

## 🔐 Seguridad

- Las credenciales de Jira se almacenan en AWS Secrets Manager
- Secret Name: `prod/jira/credentials`
- La función Lambda tiene permisos para acceder al secret
- Los headers CORS permiten peticiones desde cualquier origen (`*`) - considera restringir esto en producción

## 🧪 Cómo Probar

1. **Inicia sesión en la aplicación** con un usuario que tenga equipo asignado
2. **Haz clic en "Importar desde Jira"**
3. **Verifica que se muestran los tickets reales** del proyecto Jira correspondiente al equipo
4. **Selecciona un ticket** y verifica que se importa correctamente

### Verificación en Consola del Navegador:
```javascript
// Deberías ver estos logs:
🔍 Fetching real Jira issues for team: sap, project: RE
📡 API Request: POST https://2xlh113423.execute-api.eu-west-1.amazonaws.com/prod/api/jira
✅ Received X issues from Jira project RE
```

## 📊 Logs de CloudWatch

Para debugging, revisa los logs en CloudWatch:
- **Log Group:** `/aws/lambda/jira-integration-python`
- **Región:** eu-west-1

Busca mensajes como:
- "Handling CORS preflight request"
- "Received request: ..."
- "Fetching issues from Jira project: RE"
- "Successfully fetched X issues from RE"

## 🚀 Próximos Pasos (Opcional)

1. **Restringir CORS en producción:**
   - Cambiar `Access-Control-Allow-Origin: '*'` a tu dominio específico
   
2. **Agregar caché:**
   - Implementar caché de tickets para reducir llamadas a Jira API
   
3. **Mejorar manejo de errores:**
   - Agregar reintentos automáticos
   - Mensajes de error más específicos

4. **Monitoreo:**
   - Configurar alarmas de CloudWatch para errores
   - Métricas de uso de la API

## 📝 Notas Importantes

- ✅ La función Lambda obtiene tickets **REALES** de Jira
- ✅ Cada equipo ve solo los tickets de su proyecto
- ✅ El método OPTIONS usa MOCK solo para responder al preflight (no afecta los datos reales)
- ✅ Los headers CORS están configurados tanto en Lambda como en API Gateway
- ✅ El despliegue está completo y funcional

## 🆘 Troubleshooting

### Si sigues viendo errores de CORS:
1. Limpia la caché del navegador (Ctrl+Shift+Delete)
2. Verifica que estás usando el endpoint correcto
3. Revisa los logs de CloudWatch para ver si la Lambda se está ejecutando
4. Verifica que el usuario tiene un equipo asignado en sessionStorage

### Si no se muestran tickets:
1. Verifica las credenciales de Jira en Secrets Manager
2. Verifica que el proyecto Jira existe y tiene tickets
3. Revisa los logs de CloudWatch para ver errores específicos
4. Verifica que el mapeo de equipo a proyecto es correcto

## ✨ Resultado Final

Ahora cuando un usuario del equipo **sap** hace clic en "Importar desde Jira", verá los tickets reales del proyecto **RE** de Jira, sin errores de CORS.

---

**Fecha de implementación:** 14 de noviembre de 2025
**Estado:** ✅ Completado y desplegado
