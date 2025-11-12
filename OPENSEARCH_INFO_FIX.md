# OpenSearch Info Fix - Resumen de Cambios

## 🎯 Problema Identificado

El campo `opensearch_info` no aparecía en la respuesta de la API aunque el agente LangChain lo generaba correctamente. El usuario reportó: "No veo yo donde puedo visualizar el apartado de los indices que se han usado".

## 🔧 Solución Implementada

### Cambio Realizado

**Archivo**: `lambda_functions/ai_test_generator_optimized.py`

**Línea modificada**: ~178 (en la función `generate_test_plan_with_langchain`)

Se agregó el campo `opensearch_info` al objeto de respuesta:

```python
return create_response(201, {
    'message': 'Test plan generated with LangChain specialized workflow',
    'plan_id': plan_id,
    'test_cases_created': len(created_cases),
    'execution_time_seconds': round(execution_time, 2),
    'model_used': 'langchain-haiku-4.5-specialized',
    'processing_method': agent_data.get('execution_metadata', {}).get('processing_method', 'langchain_workflow'),
    'tools_used': agent_data.get('execution_metadata', {}).get('tools_used', []),
    'quality_score': quality_metrics.get('overall_score', 0),
    'coverage_percentage': coverage_analysis.get('current_coverage', 0),
    'opensearch_info': agent_data.get('opensearch_info', {}),  # ✅ AGREGADO
    'test_cases': created_cases
})
```

### Deployment

**Función Lambda**: `test-plan-generator-ai`
**Región**: `eu-west-1`
**Estado**: ✅ Actualizada exitosamente
**Fecha**: 2025-11-12 15:40:52 UTC
**CodeSha256**: `JXbs0kJDa6iaLhDmUO6PK6f3oFvb2Tn3JigUwRYORnQ=`

## 📊 Estructura del Campo opensearch_info

El campo `opensearch_info` ahora incluye:

```json
{
  "opensearch_info": {
    "team": "darwin",
    "indices_used": [
      "darwin-knowledge-base",
      "darwin-test-cases"
    ],
    "insights_retrieved": 15
  }
}
```

### Campos:
- **team**: Equipo del usuario (darwin, deltasmile, mulesoft, sap, saplcorp, o null para general)
- **indices_used**: Lista de índices de OpenSearch consultados
- **insights_retrieved**: Número total de documentos recuperados

## 🧪 Cómo Verificar

### 1. Desde la Interfaz Web

1. Abre la consola del navegador (F12)
2. Ve a la pestaña "Console"
3. Genera un nuevo test plan
4. Busca en los logs:
   ```
   📊 Full Response Data:
   {
     ...
     "opensearch_info": {
       "team": "darwin",
       "indices_used": ["darwin-knowledge-base"],
       "insights_retrieved": 10
     }
   }
   ```

### 2. Verificación Manual con AWS CLI

```bash
# Invocar la función directamente
aws lambda invoke \
  --function-name test-plan-generator-ai \
  --region eu-west-1 \
  --payload file://test_payload.json \
  response.json

# Ver la respuesta
cat response.json | jq '.opensearch_info'
```

### 3. Verificación en CloudWatch Logs

```bash
# Ver logs recientes
aws logs tail /aws/lambda/test-plan-generator-ai \
  --region eu-west-1 \
  --follow \
  --format short
```

Busca líneas como:
```
🔍 OpenSearch Query - Team: darwin
📚 Retrieved 10 documents from indices: ['darwin-knowledge-base']
```

## 🔄 Flujo Completo de Datos

```
1. Usuario genera test plan con user_team="darwin"
   ↓
2. Lambda recibe request y extrae user_team
   ↓
3. CompleteLangChainAgent se inicializa con user_team
   ↓
4. KnowledgeBaseRetriever usa OpenSearchClient
   ↓
5. OpenSearchClient consulta índices específicos del equipo
   ↓
6. Retriever retorna insights con indices_used
   ↓
7. Agent incluye opensearch_info en final_response
   ↓
8. Lambda incluye opensearch_info en API response ✅
   ↓
9. Frontend recibe y muestra opensearch_info
```

## 📝 Archivos Involucrados en la Solución

1. **lambda_functions/test_plan_agent/utils/opensearch_client.py**
   - Gestiona conexiones a OpenSearch
   - Implementa routing por equipo
   - Retorna resultados con campo `index`

2. **lambda_functions/test_plan_agent/tools/knowledge_base_retriever.py**
   - Usa OpenSearchClient
   - Recopila `indices_used` de los resultados
   - Retorna diccionario con `indices_used`

3. **lambda_functions/test_plan_agent/complete_langchain_agent.py**
   - Recibe `user_team` en constructor
   - Extrae `kb_insights` del workflow
   - Construye `opensearch_info` en `_create_final_response()`

4. **lambda_functions/ai_test_generator_optimized.py** ✅ MODIFICADO
   - Extrae `user_team` del request
   - Pasa team al agent
   - **AHORA incluye `opensearch_info` en la respuesta**

5. **js/api-service.js**
   - Logs completos de la respuesta
   - Muestra opensearch_info si está presente

6. **js/app.js**
   - Envía `user_team` en el request
   - Logs de información del equipo

## ✅ Estado Actual

- [x] OpenSearchClient implementado con routing por equipo
- [x] KnowledgeBaseRetriever retorna indices_used
- [x] CompleteLangChainAgent incluye opensearch_info
- [x] Lambda handler incluye opensearch_info en respuesta
- [x] Lambda function desplegada
- [ ] Verificar opensearch_info en respuesta real

## 🎯 Próximos Pasos

1. **Probar la generación de un test plan** desde la interfaz web
2. **Verificar en la consola del navegador** que aparece opensearch_info
3. **Confirmar que los índices correctos** se están usando según el equipo
4. **Documentar los resultados** de las pruebas

## 📞 Soporte

Si opensearch_info aún no aparece:

1. Verifica que el usuario tenga un `user_team` asignado
2. Revisa los logs de CloudWatch para errores
3. Confirma que la Lambda Layer de LangChain está correctamente configurada
4. Verifica que OpenSearch está accesible desde la Lambda

---

**Última actualización**: 2025-11-12 15:40 UTC
**Estado**: ✅ Desplegado y listo para pruebas
