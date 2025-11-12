# Fix del Modelo Bedrock - Claude Haiku 4.5

## 🎯 Problema Identificado

El sistema no podía generar test cases debido a un error de validación de AWS Bedrock:

```
An error occurred (ValidationException) when calling the InvokeModel operation: 
Invocation of model ID anthropic.claude-haiku-4-5-20251001-v1:0 with on-demand throughput 
isn't supported. Retry your request with the ID or ARN of an inference profile that contains this model.
```

## 🔍 Causa Raíz

AWS Bedrock cambió la forma de invocar Claude Haiku 4.5. Ahora requiere usar **inference profiles** en lugar de model IDs directos. El inference profile correcto para la región EU es:

```
eu.anthropic.claude-haiku-4-5-20251001-v1:0
```

## ✅ Solución Implementada

### 1. Actualización de Variables de Entorno

Se actualizó la variable `BEDROCK_MODEL_ID` en la Lambda `test-plan-generator-ai`:

**Antes:**
```
BEDROCK_MODEL_ID=anthropic.claude-haiku-4-5-20251001-v1:0
```

**Después:**
```
BEDROCK_MODEL_ID=eu.anthropic.claude-haiku-4-5-20251001-v1:0
```

### 2. Verificación del Código del Agente

El código en `complete_langchain_agent.py` ya estaba correctamente configurado (línea 73):

```python
self.model_id = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"
```

### 3. Deployment Completado

**Función Lambda**: `test-plan-generator-ai`
**Región**: `eu-west-1`
**Estado**: ✅ Actualizada exitosamente
**Fecha**: 2025-11-12 14:48:19 UTC
**CodeSha256**: `JXbs0kJDa6iaLhDmUO6PK6f3oFvb2Tn3JigUwRYORnQ=`

## 📊 Configuración Final

### Variables de Entorno de la Lambda

```json
{
  "KNOWLEDGE_BASE_ID": "VH6SRH9ZNO",
  "BEDROCK_MODEL_ID": "eu.anthropic.claude-haiku-4-5-20251001-v1:0",
  "RDS_HOST": "test-plan-generator-db.czuimyk2qu10.eu-west-1.rds.amazonaws.com",
  "RDS_USER": "admin",
  "RDS_PASSWORD": "TempPassword123!",
  "RDS_DATABASE": "testplangenerator",
  "RDS_PORT": "3306"
}
```

### Lambda Layer

- **Layer ARN**: `arn:aws:lambda:eu-west-1:701055077130:layer:test-plan-generator-langchain:3`
- **Tamaño**: 51,054,657 bytes
- **Contenido**: LangChain, boto3, y todas las dependencias necesarias

## 🧪 Cómo Probar

### 1. Desde la Interfaz Web

1. Abre la aplicación web
2. Crea un nuevo test plan con cualquier título y requerimientos
3. Selecciona tu equipo (mulesoft, darwin, etc.)
4. Haz clic en "Generate Test Plan"
5. Verifica que se generen los test cases correctamente

### 2. Verificar en CloudWatch Logs

```bash
aws logs tail /aws/lambda/test-plan-generator-ai \
  --region eu-west-1 \
  --follow \
  --format short
```

Deberías ver logs como:
```
🚀 Initializing LangChain Agent with Haiku 4.5 and specialized tools (Team: mulesoft)
🧠 Generating test plan with LangChain specialized workflow
✅ Bedrock client initialized with Haiku 4.5
```

### 3. Verificar Respuesta de la API

La respuesta debe incluir:
```json
{
  "message": "Test plan generated with LangChain specialized workflow",
  "plan_id": "TP-XXXXXX",
  "test_cases_created": 10,
  "model_used": "langchain-haiku-4.5-specialized",
  "opensearch_info": {
    "team": "mulesoft",
    "indices_used": ["mulesoft-knowledge-base"],
    "insights_retrieved": 5
  },
  "test_cases": [...]
}
```

## 📝 Archivos Modificados

1. **Lambda Environment Variables** (via AWS CLI)
   - Actualizado `BEDROCK_MODEL_ID` a inference profile

2. **lambda_functions/ai_test_generator_optimized.py**
   - Ya incluía el campo `opensearch_info` en la respuesta (fix anterior)

3. **lambda_functions/test_plan_agent/complete_langchain_agent.py**
   - Ya estaba configurado correctamente con el inference profile

## 🔄 Diferencias entre Model ID e Inference Profile

### Model ID (Antiguo - No funciona)
```
anthropic.claude-haiku-4-5-20251001-v1:0
```

### Inference Profile (Nuevo - Correcto)
```
eu.anthropic.claude-haiku-4-5-20251001-v1:0
```

El prefijo `eu.` indica que es un inference profile para la región de Europa, que proporciona:
- ✅ Mejor latencia en Europa
- ✅ Cumplimiento con regulaciones de datos EU
- ✅ Soporte para on-demand throughput
- ✅ Optimización de costos

## ⚠️ Notas Importantes

1. **Región**: El inference profile `eu.` solo funciona en la región `eu-west-1`
2. **Fallback**: Si el agente LangChain no está disponible, el sistema usa un método fallback que también utiliza el mismo modelo
3. **Compatibilidad**: Este cambio es compatible con todas las funcionalidades existentes (OpenSearch, team routing, etc.)

## 🎯 Próximos Pasos

1. ✅ Probar la generación de test cases desde la interfaz web
2. ✅ Verificar que `opensearch_info` aparece en la respuesta
3. ✅ Confirmar que los índices correctos se usan según el equipo
4. ✅ Monitorear logs de CloudWatch para errores

## 📞 Troubleshooting

Si aún hay problemas:

1. **Verificar la variable de entorno**:
   ```bash
   aws lambda get-function-configuration \
     --function-name test-plan-generator-ai \
     --region eu-west-1 \
     --query 'Environment.Variables.BEDROCK_MODEL_ID'
   ```

2. **Verificar permisos de IAM**:
   - La Lambda debe tener permisos para `bedrock:InvokeModel`
   - El rol debe permitir acceso al inference profile

3. **Verificar logs**:
   ```bash
   aws logs tail /aws/lambda/test-plan-generator-ai \
     --region eu-west-1 \
     --since 5m
   ```

---

**Última actualización**: 2025-11-12 14:48 UTC
**Estado**: ✅ Desplegado y listo para pruebas
**Modelo**: Claude Haiku 4.5 (via EU Inference Profile)
