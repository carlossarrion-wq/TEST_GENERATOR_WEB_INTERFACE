# Guía de Verificación - OpenSearch con Enrutamiento por Equipos

## 📋 Resumen

Esta guía te ayudará a verificar que el sistema está usando correctamente los índices de OpenSearch específicos para cada equipo durante la generación de casos de prueba.

## 🔍 Métodos de Verificación

### 1. Verificación en el Frontend (Consola del Navegador)

Cuando generes un plan de pruebas, abre la **Consola de Desarrollador** (F12) y busca los siguientes logs:

#### A. Información del Equipo
```
👥 Team del usuario: darwin
🔍 OpenSearch: Se usarán índices específicos del equipo darwin
```

#### B. Respuesta de la API
```
📡 API Response: 201
📦 Response Data: {
  "plan_id": "TP-1234567890-5678",
  "test_cases_created": 10,
  "opensearch_info": {
    "team": "darwin",
    "indices_used": ["darwin-test-cases", "darwin-best-practices"],
    "insights_retrieved": 3
  }
}
```

#### C. Información Detallada de OpenSearch
```
🔍 OpenSearch Info: {
  "team": "darwin",
  "indices_used": ["darwin-test-cases", "darwin-best-practices"],
  "insights_retrieved": 3
}
```

### 2. Verificación en CloudWatch Logs

#### Paso 1: Acceder a CloudWatch
1. Ve a AWS Console → CloudWatch → Log groups
2. Busca el log group: `/aws/lambda/ai-test-generator-optimized`
3. Abre el stream de logs más reciente

#### Paso 2: Buscar Logs de OpenSearch

Busca estos patrones en los logs:

##### A. Detalles de la Consulta
```
================================================================================
🔍 OPENSEARCH QUERY DETAILS
================================================================================
👥 Team: darwin
📚 Indices to search: ['darwin-test-cases', 'darwin-best-practices']
📝 Query: Test planning for: Sistema de autenticación - El sistema debe permitir...
🎯 Max results: 5
⭐ Min score: 0.5
================================================================================
```

##### B. Resultados de OpenSearch
```
================================================================================
✅ OPENSEARCH RESULTS
================================================================================
📊 Total documents found: 3
📚 Indices that returned results: ['darwin-test-cases', 'darwin-best-practices']
📈 Score range: 0.75 - 0.92

   Result 1:
   └─ Index: darwin-test-cases
   └─ Score: 0.92
   └─ Title: Test Case Template for Authentication Systems...

   Result 2:
   └─ Index: darwin-best-practices
   └─ Score: 0.85
   └─ Title: Best Practices for Security Testing...

   Result 3:
   └─ Index: darwin-test-cases
   └─ Score: 0.75
   └─ Title: Sample Test Cases for Login Functionality...
================================================================================
```

##### C. Confirmación del Knowledge Retriever
```
✅ Retrieved 3 insights from OpenSearch
📚 Indices used: ['darwin-test-cases', 'darwin-best-practices']
```

### 3. Verificación por Equipo

#### Equipos Configurados

| Equipo | Índices Esperados | Comportamiento |
|--------|-------------------|----------------|
| `darwin` | `darwin-*` | Solo busca en índices de darwin |
| `deltasmile` | `deltasmile-*` | Solo busca en índices de deltasmile |
| `mulesoft` | `mulesoft-*` | Solo busca en índices de mulesoft |
| `sap` | `sap-*` | Solo busca en índices de sap |
| `saplcorp` | `saplcorp-*` | Solo busca en índices de saplcorp |
| `null` o sin equipo | Todos los índices | Busca en todos los índices disponibles |

### 4. Pruebas de Verificación

#### Test 1: Usuario con Equipo Asignado

**Pasos:**
1. Inicia sesión con un usuario que tenga tag `Team: darwin`
2. Genera un plan de pruebas
3. Verifica en la consola del navegador:
   - ✅ `Team del usuario: darwin`
   - ✅ `indices_used` contiene solo índices de darwin

**Resultado Esperado:**
```json
{
  "opensearch_info": {
    "team": "darwin",
    "indices_used": ["darwin-test-cases", "darwin-best-practices"],
    "insights_retrieved": 3
  }
}
```

#### Test 2: Usuario sin Equipo Asignado

**Pasos:**
1. Inicia sesión con un usuario sin tag `Team`
2. Genera un plan de pruebas
3. Verifica en la consola del navegador:
   - ✅ `Sin equipo asignado: Se usarán todos los índices disponibles`
   - ✅ `indices_used` contiene índices de múltiples equipos

**Resultado Esperado:**
```json
{
  "opensearch_info": {
    "team": null,
    "indices_used": ["darwin-test-cases", "mulesoft-docs", "sap-guidelines"],
    "insights_retrieved": 5
  }
}
```

#### Test 3: Comparación entre Equipos

**Objetivo:** Verificar que diferentes equipos obtienen diferentes índices

**Pasos:**
1. Genera un plan con usuario del equipo `darwin`
2. Genera un plan con usuario del equipo `mulesoft`
3. Compara los `indices_used` en ambas respuestas

**Resultado Esperado:**
- Usuario darwin: Solo índices `darwin-*`
- Usuario mulesoft: Solo índices `mulesoft-*`

## 🛠️ Comandos Útiles

### Ver Logs en Tiempo Real (AWS CLI)

```bash
# Ver logs del Lambda principal
aws logs tail /aws/lambda/ai-test-generator-optimized --follow --region eu-west-1

# Filtrar solo logs de OpenSearch
aws logs tail /aws/lambda/ai-test-generator-optimized --follow --region eu-west-1 | grep "OPENSEARCH"

# Ver logs de los últimos 10 minutos
aws logs tail /aws/lambda/ai-test-generator-optimized --since 10m --region eu-west-1
```

### Buscar Logs Específicos

```bash
# Buscar por equipo específico
aws logs filter-log-events \
  --log-group-name /aws/lambda/ai-test-generator-optimized \
  --filter-pattern "Team: darwin" \
  --region eu-west-1

# Buscar resultados de OpenSearch
aws logs filter-log-events \
  --log-group-name /aws/lambda/ai-test-generator-optimized \
  --filter-pattern "OPENSEARCH RESULTS" \
  --region eu-west-1
```

## 📊 Interpretación de Resultados

### ✅ Funcionamiento Correcto

**Indicadores:**
- Los logs muestran el equipo correcto
- `indices_used` contiene solo índices del equipo
- Los documentos recuperados provienen de los índices correctos
- El score de relevancia es > 0.5

**Ejemplo:**
```
Team: darwin
Indices: ['darwin-test-cases', 'darwin-best-practices']
Results: 3 documents from darwin indices
```

### ⚠️ Posibles Problemas

#### Problema 1: No se encuentran documentos
```
📊 Total documents found: 0
📚 Indices that returned results: []
```

**Causas posibles:**
- Los índices del equipo están vacíos
- El query no coincide con ningún documento
- El `min_score` es demasiado alto

**Solución:**
1. Verifica que los índices existen en OpenSearch
2. Revisa el contenido de los índices
3. Ajusta el `min_score` si es necesario

#### Problema 2: Se usan índices incorrectos
```
Team: darwin
Indices used: ['mulesoft-docs', 'sap-guidelines']
```

**Causas posibles:**
- El mapeo de equipos no está actualizado
- El equipo del usuario no se está pasando correctamente

**Solución:**
1. Verifica el tag `Team` del usuario en IAM
2. Revisa `TEAM_INDEX_MAPPING` en `opensearch_client.py`
3. Confirma que el frontend está enviando `user_team`

#### Problema 3: Usuario sin equipo no ve todos los índices
```
Team: null
Indices used: []
```

**Causa:**
- `TEAM_INDEX_MAPPING` está vacío

**Solución:**
1. Ejecuta el Lambda de descubrimiento de índices
2. Actualiza `TEAM_INDEX_MAPPING` con los índices reales

## 🔧 Troubleshooting

### 1. No aparece información de OpenSearch en la respuesta

**Verifica:**
```javascript
// En la consola del navegador
console.log(sessionStorage.getItem('user_team'));
```

Si es `null`, el usuario no tiene tag de equipo asignado.

### 2. Los logs no aparecen en CloudWatch

**Verifica:**
- El Lambda tiene permisos para escribir en CloudWatch
- Espera 1-2 minutos para que los logs aparezcan
- Revisa el log group correcto

### 3. Error de conexión a OpenSearch

**Logs esperados:**
```
❌ Error searching OpenSearch: Connection timeout
```

**Solución:**
- Verifica que el Lambda está en la misma VPC que OpenSearch
- Confirma los security groups
- Revisa el endpoint de OpenSearch

## 📝 Checklist de Verificación

- [ ] El frontend muestra el equipo del usuario en la consola
- [ ] La respuesta de la API incluye `opensearch_info`
- [ ] Los `indices_used` corresponden al equipo del usuario
- [ ] Los logs de CloudWatch muestran los detalles de la consulta
- [ ] Los logs de CloudWatch muestran los resultados de OpenSearch
- [ ] Los documentos recuperados provienen de los índices correctos
- [ ] Usuarios sin equipo pueden acceder a todos los índices
- [ ] Diferentes equipos obtienen diferentes índices

## 🎯 Próximos Pasos

1. **Descubrir Índices Reales:**
   - Ejecuta el Lambda `opensearch-index-discovery`
   - Obtén la lista de índices disponibles

2. **Actualizar Mapeo:**
   - Actualiza `TEAM_INDEX_MAPPING` en `opensearch_client.py`
   - Despliega los cambios

3. **Pruebas Completas:**
   - Prueba con usuarios de cada equipo
   - Verifica los logs para cada caso
   - Documenta los resultados

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs de CloudWatch
2. Verifica la configuración de IAM tags
3. Confirma que OpenSearch está accesible desde el Lambda
4. Revisa el mapeo de equipos a índices

---

**Última actualización:** 12/11/2025
**Versión:** 1.0
