# Corrección: Casos de Prueba Duplicados

## 🔍 Problema Identificado

Los casos de prueba generados aparecían todos iguales con contenido genérico repetitivo:
- Mismo nombre: "Test Case 1: Requirement 1", "Test Case 2: Requirement 2", etc.
- Misma descripción: "Verify Requirement X"
- Mismas precondiciones: "System accessible"
- Mismo resultado esperado: "Functionality works as expected"

## 🎯 Causa Raíz

El problema estaba en el **Test Case Generator** (`test_case_generator.py`):

1. **Prompt demasiado simplificado**: Solo se enviaban los primeros 5 requerimientos truncados a 100 caracteres
2. **Falta de contexto**: No se incluían edge cases, risk areas ni insights del Knowledge Base
3. **Parámetros limitados**: 
   - Temperature: 0.1 (muy bajo, poca variedad)
   - Max tokens: 2000 (insuficiente para casos detallados)
4. **Sin validación de unicidad**: No se verificaba que los casos fueran diferentes

## ✅ Solución Implementada

### 1. Prompt Mejorado con Contexto Completo

**ANTES:**
```python
# Solo primeros 5 requerimientos truncados
for req in functional_reqs[:5]:
    req_text = req.get('requirement', str(req))[:100]
    reqs_list.append(f"- {req_text}")

generation_prompt = f"""Genera {target_cases} casos de prueba para:
REQUERIMIENTOS:
{reqs_summary}
Proporciona los casos de prueba en formato JSON."""
```

**DESPUÉS:**
```python
# TODOS los requerimientos completos
for i, req in enumerate(functional_reqs, 1):
    req_text = req_text.strip().lstrip('-•*').strip()
    if req_text:
        reqs_list.append(f"{i}. {req_text}")

# Incluir edge cases, risk areas y KB insights
generation_prompt = f"""Genera EXACTAMENTE {target_cases} casos de prueba ÚNICOS Y ESPECÍFICOS...

IMPORTANTE: Cada caso debe ser DIFERENTE y cubrir un aspecto ESPECÍFICO...

REQUERIMIENTOS FUNCIONALES:
{reqs_summary}

EDGE CASES IDENTIFICADOS:
{edge_cases_summary}

ÁREAS DE RIESGO:
{risk_areas_summary}

BUENAS PRÁCTICAS (Knowledge Base):
{kb_summary}

INSTRUCCIONES ESPECÍFICAS:
1. Genera {target_cases} casos de prueba DISTINTOS
2. Cada caso debe cubrir un requerimiento o escenario DIFERENTE
3. Incluye casos positivos, negativos y edge cases
4. Distribuye prioridades: ~35% High, ~40% Medium, ~25% Low
5. Cada caso DEBE tener mínimo 3 pasos detallados
6. Usa nombres descriptivos >20 caracteres
7. Descripciones >50 caracteres explicando el objetivo
8. Resultados esperados >30 caracteres, específicos y medibles
9. Datos de prueba concretos y realistas
..."""
```

### 2. Parámetros Optimizados

**ANTES:**
```python
"max_tokens": 2000,
"temperature": 0.1,
```

**DESPUÉS:**
```python
"max_tokens": 4000,  # Más espacio para casos detallados
"temperature": 0.3,  # Mayor variedad en las respuestas
```

### 3. Validación y Deduplicación

Nueva función `_validate_and_deduplicate_cases()`:

```python
def _validate_and_deduplicate_cases(self, test_cases, target_count):
    """Validate and remove duplicate test cases"""
    unique_cases = []
    seen_names = set()
    seen_descriptions = set()
    
    for case in test_cases:
        name = case.get('name', '').strip().lower()
        description = case.get('description', '').strip().lower()
        
        # Skip duplicates
        if name in seen_names or description in seen_descriptions:
            print(f"⚠️ Skipping duplicate case: {case.get('name')}")
            continue
        
        # Validate minimum requirements
        if not name or not description:
            continue
        
        # Ensure minimum 3 steps
        if len(case.get('steps', [])) < 3:
            case['steps'] = steps + ["Execute test", "Verify behavior", "Confirm result"]
        
        # Ensure minimum field lengths
        if len(case.get('name', '')) < 20:
            case['name'] = f"{case['name']} - Validation Test"
        
        if len(case.get('description', '')) < 50:
            case['description'] = f"{case['description']} This test validates..."
        
        seen_names.add(name)
        seen_descriptions.add(description)
        unique_cases.append(case)
    
    return unique_cases
```

### 4. Fallback Mejorado

**ANTES:**
```python
def _create_fallback_cases(self, functional_reqs, count):
    cases.append({
        "name": f"Test Case {i+1}: {req_text[:50]}",
        "description": f"Verify {req_text}",
        "priority": "Medium",
        "preconditions": "System accessible",
        "expected_result": "Functionality works as expected",
        ...
    })
```

**DESPUÉS:**
```python
def _create_fallback_cases(self, functional_reqs, count):
    # Casos específicos basados en cada requerimiento
    req_text = req_text.strip().lstrip('-•*').strip()
    priority = "High" if i < count * 0.35 else ("Medium" if i < count * 0.75 else "Low")
    
    cases.append({
        "name": f"Verificar funcionalidad: {req_text[:60]}",
        "description": f"Este caso de prueba valida que {req_text.lower()} funciona correctamente según los requerimientos especificados.",
        "priority": priority,
        "preconditions": "El sistema debe estar accesible y el usuario debe tener los permisos necesarios...",
        "expected_result": f"La funcionalidad {req_text[:40]} se ejecuta correctamente sin errores...",
        "test_data": f"Datos de prueba válidos para {req_text[:30]}",
        "steps": [
            f"Acceder a la funcionalidad relacionada con: {req_text[:50]}",
            "Ejecutar la acción de prueba con datos válidos",
            "Verificar que el resultado coincide con lo esperado",
            "Confirmar que no se generan errores en el proceso"
        ]
    })
```

## 📊 Resultados Esperados

Con estos cambios, ahora los casos de prueba generados serán:

✅ **Únicos**: Cada caso cubre un aspecto diferente de los requerimientos
✅ **Específicos**: Nombres y descripciones detalladas basadas en el contexto real
✅ **Completos**: Mínimo 3 pasos por caso, con precondiciones y resultados específicos
✅ **Variados**: Distribución adecuada de prioridades (High/Medium/Low)
✅ **Contextualizados**: Incluyen edge cases, risk areas y buenas prácticas del KB

## 🚀 Despliegue

**Fecha**: 13/11/2025 13:56 UTC
**Función Lambda**: `test-plan-generator-ai`
**Versión**: 1
**Estado**: ✅ Desplegado exitosamente

## 📝 Archivos Modificados

1. `lambda_functions/test_plan_agent/tools/test_case_generator.py`
   - Método `execute()`: Prompt mejorado con contexto completo
   - Nueva función `_validate_and_deduplicate_cases()`
   - Función `_create_fallback_cases()` mejorada
   - Parámetros optimizados (temperature: 0.3, max_tokens: 4000)

## 🧪 Pruebas Recomendadas

1. **Generar un plan de pruebas** con múltiples requerimientos
2. **Verificar que cada caso sea único** (nombres y descripciones diferentes)
3. **Confirmar distribución de prioridades** (~35% High, ~40% Medium, ~25% Low)
4. **Validar que cada caso tenga mínimo 3 pasos**
5. **Revisar logs de CloudWatch** para confirmar el funcionamiento

## 📞 Comandos Útiles

```bash
# Ver logs de la Lambda
python get_logs.py

# Redesplegar si es necesario
python deploy_test_case_fix.py
```

## 🎓 Lecciones Aprendidas

1. **Contexto es clave**: Enviar TODOS los requerimientos, no solo una muestra
2. **Validación post-generación**: Siempre verificar unicidad y calidad
3. **Parámetros del modelo**: Temperature y max_tokens afectan significativamente la calidad
4. **Fallback robusto**: Debe generar casos específicos, no genéricos
5. **Instrucciones explícitas**: El prompt debe ser muy específico sobre lo que NO hacer (no duplicar)
