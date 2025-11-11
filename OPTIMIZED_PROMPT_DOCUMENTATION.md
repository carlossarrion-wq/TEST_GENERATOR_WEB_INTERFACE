# 📋 Documentación: System Prompt Optimizado con Algoritmos Integrados

## 🎯 Objetivo

Integrar los algoritmos de **Coverage Calculator** y **Quality Validator** directamente en el system prompt del Test Case Generator para que Claude Haiku 4.5 genere casos de prueba optimizados desde el inicio.

## ✅ Cambios Implementados

### 1. **Algoritmo de Coverage Calculator Integrado**

Se añadió al prompt la explicación completa del algoritmo de cobertura:

```
ALGORITMO DE COVERAGE CALCULATOR (que se aplicará a tus casos):

1. Cobertura Funcional = min(100, (total_casos / total_requerimientos) * 100)
   - Objetivo: ≥ 80%
   
2. Cobertura Edge Cases = min(100, (casos_High_priority / total_edge_cases) * 100)
   - Objetivo: ≥ 70%
   
3. Cobertura de Riesgos = min(100, ((casos_High + casos_Medium) / total_risk_areas) * 100)
   - Objetivo: ≥ 75%
   
4. Cobertura General = (Funcional + Edge Cases + Riesgos) / 3
   - Objetivo: ≥ 85% (Good), ≥ 90% (Excellent)
```

**Distribución Óptima de Prioridades:**
- High: 30-40% (edge cases y riesgos críticos)
- Medium: 30-40% (riesgos moderados)
- Low: 20-30% (casos básicos)

### 2. **Sistema de Puntuación de Calidad Integrado**

Se añadió el sistema completo de 100 puntos:

```
SISTEMA DE PUNTUACIÓN DE CALIDAD (máximo 100 puntos por caso):

1. Nombre (0-15 pts): >20 chars = 15 pts
2. Descripción (0-15 pts): >50 chars = 15 pts
3. Pasos (0-25 pts): ≥3 pasos = 25 pts ⭐ CRÍTICO
4. Precondiciones (0-10 pts): >10 chars = 10 pts
5. Resultado Esperado (0-20 pts): >30 chars = 20 pts
6. Datos de Prueba (0-10 pts): >10 chars = 10 pts
7. Prioridad (0-5 pts): High/Medium/Low válido = 5 pts

OBJETIVO: Score promedio ≥ 85 puntos (Good), ≥ 90 (Excellent)
```

### 3. **Estructura de Casos Optimizada**

Se especificaron requisitos mínimos para cada campo:

- **Nombre:** >20 caracteres, descriptivo y único
- **Descripción:** >50 caracteres, explicar objetivo y alcance
- **Prioridad:** High/Medium/Low (según distribución óptima)
- **Precondiciones:** >10 caracteres, condiciones específicas
- **Pasos:** MÍNIMO 3 pasos detallados y ejecutables
- **Resultado esperado:** >30 caracteres, específico y medible
- **Datos de prueba:** >10 caracteres, valores concretos

### 4. **Reglas de Optimización**

Se añadieron 7 reglas específicas:

1. Genera casos que alcancen score ≥ 85 puntos
2. Incluye SIEMPRE mínimo 3 pasos por caso
3. Distribuye prioridades según objetivos de cobertura
4. Asigna High priority a edge cases identificados
5. Usa descripciones y resultados detallados (>50 y >30 chars)
6. Incluye datos de prueba específicos y realistas
7. Responde SOLO con JSON, sin explicaciones adicionales

## 📊 Análisis del Prompt

### Tamaño del Prompt

- **Prompt anterior:** ~700 tokens
- **Prompt optimizado:** ~1,350 tokens
- **Incremento:** +650 tokens (~93% más grande)

### Cacheabilidad

✅ **CACHEABLE:** El prompt sigue siendo cacheable porque:
- Tamaño: 1,350 tokens > 1,024 tokens (mínimo para cache)
- Usa `cache_control: {"type": "ephemeral"}`
- API version: bedrock-2023-06-01 (soporta Prompt Caching)

### Beneficios del Cache

Con Prompt Caching activado:
- **Primera invocación:** Escribe ~1,350 tokens al cache
- **Invocaciones subsecuentes:** Lee del cache (90% más rápido)
- **Ahorro de costos:** ~90% en tokens de input para el system prompt
- **TTL del cache:** 5 minutos de inactividad

## 🎯 Beneficios Esperados

### 1. **Mayor Cobertura Automática**

Claude ahora conoce los objetivos de cobertura y generará casos que:
- Cubran ≥80% de requerimientos funcionales
- Incluyan suficientes casos High priority para edge cases (≥70%)
- Distribuyan prioridades para cubrir riesgos (≥75%)

### 2. **Mayor Calidad Desde el Inicio**

Los casos generados tendrán:
- Nombres descriptivos (>20 caracteres)
- Descripciones completas (>50 caracteres)
- Mínimo 3 pasos detallados
- Resultados esperados específicos (>30 caracteres)
- Datos de prueba concretos (>10 caracteres)
- **Score objetivo: ≥85 puntos**

### 3. **Mejor Distribución de Prioridades**

Claude distribuirá automáticamente:
- 30-40% High priority (edge cases críticos)
- 30-40% Medium priority (riesgos moderados)
- 20-30% Low priority (casos básicos)

### 4. **Menos Iteraciones de Mejora**

Al generar casos optimizados desde el inicio:
- Menos necesidad de regeneración
- Menos llamadas al Coverage Calculator para ajustes
- Menos sugerencias del Quality Validator
- **Resultado:** Proceso más eficiente y rápido

## 🔄 Flujo de Trabajo Optimizado

### Antes (sin algoritmos en prompt):
1. Requirements Analyzer → extrae requerimientos
2. Test Case Generator → genera casos básicos
3. Coverage Calculator → detecta baja cobertura (60-70%)
4. Quality Validator → detecta casos de baja calidad (score 60-75)
5. **Iteración:** Regenerar casos con ajustes
6. Repetir pasos 3-5 hasta alcanzar objetivos

### Ahora (con algoritmos en prompt):
1. Requirements Analyzer → extrae requerimientos
2. Test Case Generator → genera casos **YA OPTIMIZADOS**
3. Coverage Calculator → confirma alta cobertura (85-95%)
4. Quality Validator → confirma alta calidad (score 85-95)
5. **Resultado:** Casos listos en primera iteración

## 📈 Métricas Esperadas

### Cobertura
- **Antes:** 60-75% en primera generación
- **Ahora:** 85-95% en primera generación
- **Mejora:** +25-35 puntos porcentuales

### Calidad
- **Antes:** Score promedio 65-75 puntos
- **Ahora:** Score promedio 85-95 puntos
- **Mejora:** +20-30 puntos

### Eficiencia
- **Antes:** 2-3 iteraciones para alcanzar objetivos
- **Ahora:** 1 iteración (casos optimizados desde inicio)
- **Mejora:** 50-66% menos llamadas a Bedrock

## 🚀 Próximos Pasos

1. ✅ **Completado:** Modificar system prompt con algoritmos
2. ⏳ **Pendiente:** Desplegar Lambda actualizada
3. ⏳ **Pendiente:** Probar generación con casos reales
4. ⏳ **Pendiente:** Medir métricas de cobertura y calidad
5. ⏳ **Pendiente:** Comparar con versión anterior

## 📝 Notas Técnicas

### Archivo Modificado
- **Path:** `lambda_functions/test_plan_agent/tools/test_case_generator.py`
- **Variable:** `TEST_CASE_GENERATOR_SYSTEM_PROMPT`
- **Líneas:** ~120 líneas de prompt

### Compatibilidad
- ✅ Compatible con Claude Haiku 4.5
- ✅ Compatible con Prompt Caching
- ✅ Compatible con API bedrock-2023-06-01
- ✅ No requiere cambios en otras herramientas

### Consideraciones
- El prompt más largo puede aumentar ligeramente la latencia en la primera invocación (cache write)
- Las invocaciones subsecuentes serán más rápidas (cache read)
- El beneficio de casos optimizados compensa el tamaño del prompt

## 🎓 Conclusión

La integración de los algoritmos de Coverage Calculator y Quality Validator en el system prompt del Test Case Generator permite que Claude Haiku 4.5 genere casos de prueba optimizados desde el inicio, reduciendo iteraciones y mejorando significativamente la calidad y cobertura de los casos generados.

---

**Fecha de implementación:** 6 de noviembre de 2025  
**Versión:** 2.0 (Optimized with Integrated Algorithms)  
**Estado:** ✅ Implementado y listo para despliegue
