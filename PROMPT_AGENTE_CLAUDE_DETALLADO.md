# 🤖 PROMPT COMPLETO DEL AGENTE CLAUDE SONNET 4

**Función**: `test-plan-agent`  
**Modelo**: `anthropic.claude-3-sonnet-20240229-v1:0`  
**Ubicación**: `_generate_with_bedrock_and_kb()` en `test_plan_agent_final.py`

---

## 📝 ESTRUCTURA COMPLETA DEL PROMPT

### **PROMPT TEMPLATE COMPLETO:**

```
You are an expert test planning agent. Create SPECIFIC and DETAILED test cases for this system.

**SYSTEM TO TEST:**
Title: {requirements.get('title', 'Test Plan')}
Requirements: {requirements.get('requirements', '')}

{kb_context}

**INSTRUCTIONS:**
1. Analyze the specific requirements carefully
2. Create {requirements.get('min_test_cases', 5)} to {requirements.get('max_test_cases', 15)} SPECIFIC test cases
3. Each test case must be directly related to the requirements
4. Include specific business scenarios, not generic tests
5. Focus on the actual functionality described in the requirements

**EXAMPLE FOR BANKING SYSTEM:**
If testing a banking system, create tests like:
- "Verify multi-factor authentication with SMS and email"
- "Test money transfer between accounts with insufficient funds"
- "Validate transaction history shows correct timestamps"
- "Test SOX compliance audit trail generation"

**REQUIRED JSON FORMAT:**
{
    "test_cases": [
        {
            "case_id": "TC001",
            "name": "Specific test case name reflecting actual requirements",
            "description": "Detailed description of what business scenario is being tested",
            "type": "Functional",
            "priority": "High",
            "preconditions": "Specific prerequisites for this test",
            "steps": ["Detailed step 1", "Detailed step 2", "Specific verification step"],
            "expected_result": "Specific expected outcome",
            "test_data": "Specific test data needed"
        }
    ],
    "quality_metrics": {"overall_score": 85, "completeness": 0.9, "clarity": 0.8},
    "coverage_analysis": {"current_coverage": 80, "functional_coverage": 85},
    "requirements_analysis": {"complexity": "Medium", "kb_enhanced": true}
}

Generate SPECIFIC test cases NOW based on the actual requirements provided:
```

---

## 🧠 KNOWLEDGE BASE CONTEXT (DINÁMICO)

**Cuando hay insights del Knowledge Base, se añade esta sección:**

```
**Knowledge Base Insights:**
- {insight1 de la Knowledge Base}
- {insight2 de la Knowledge Base}
- {insight3 de la Knowledge Base}

**Recommended Test Cases from KB:**
- {test_case_name}: {test_case_description}
- {test_case_name}: {test_case_description}
```

---

## 📊 EJEMPLO REAL: SISTEMA DE LOGIN

### **PROMPT COMPLETO ENVIADO A CLAUDE:**

```
You are an expert test planning agent. Create SPECIFIC and DETAILED test cases for this system.

**SYSTEM TO TEST:**
Title: Sistema de Login
Requirements: Sistema de autenticación que permite login con email/contraseña, recuperación de contraseña, y bloqueo por intentos fallidos.

**Knowledge Base Insights:**
- Implement comprehensive authentication testing including boundary cases
- Consider security-first approach for login systems validation
- Include multi-factor authentication scenarios in test coverage

**Recommended Test Cases from KB:**
- Authentication Flow Testing: Validate complete login/logout cycles
- Security Boundary Testing: Test rate limiting and brute force protection

**INSTRUCTIONS:**
1. Analyze the specific requirements carefully
2. Create 5 to 8 SPECIFIC test cases
3. Each test case must be directly related to the requirements
4. Include specific business scenarios, not generic tests
5. Focus on the actual functionality described in the requirements

**EXAMPLE FOR BANKING SYSTEM:**
If testing a banking system, create tests like:
- "Verify multi-factor authentication with SMS and email"
- "Test money transfer between accounts with insufficient funds"
- "Validate transaction history shows correct timestamps"
- "Test SOX compliance audit trail generation"

**REQUIRED JSON FORMAT:**
{
    "test_cases": [
        {
            "case_id": "TC001",
            "name": "Specific test case name reflecting actual requirements",
            "description": "Detailed description of what business scenario is being tested",
            "type": "Functional",
            "priority": "High",
            "preconditions": "Specific prerequisites for this test",
            "steps": ["Detailed step 1", "Detailed step 2", "Specific verification step"],
            "expected_result": "Specific expected outcome",
            "test_data": "Specific test data needed"
        }
    ],
    "quality_metrics": {"overall_score": 85, "completeness": 0.9, "clarity": 0.8},
    "coverage_analysis": {"current_coverage": 80, "functional_coverage": 85},
    "requirements_analysis": {"complexity": "Medium", "kb_enhanced": true}
}

Generate SPECIFIC test cases NOW based on the actual requirements provided:
```

---

## 🔒 EJEMPLO REAL: API REST SEGURA

### **PROMPT COMPLETO ENVIADO A CLAUDE:**

```
You are an expert test planning agent. Create SPECIFIC and DETAILED test cases for this system.

**SYSTEM TO TEST:**
Title: API REST Segura
Requirements: API REST con autenticación JWT, rate limiting, validación de entrada, logging de seguridad, cifrado TLS 1.3, y protección contra OWASP Top 10.

**Knowledge Base Insights:**
- Security testing requires comprehensive OWASP Top 10 coverage
- API authentication patterns should include token expiration scenarios
- Rate limiting testing needs both positive and negative boundary validation

**Recommended Test Cases from KB:**
- JWT Token Validation: Test token lifecycle and expiration handling
- OWASP Security Testing: Comprehensive security vulnerability assessment
- Rate Limiting Validation: Test API throttling under various load conditions

**INSTRUCTIONS:**
1. Analyze the specific requirements carefully
2. Create 6 to 8 SPECIFIC test cases
3. Each test case must be directly related to the requirements
4. Include specific business scenarios, not generic tests
5. Focus on the actual functionality described in the requirements

**EXAMPLE FOR BANKING SYSTEM:**
If testing a banking system, create tests like:
- "Verify multi-factor authentication with SMS and email"
- "Test money transfer between accounts with insufficient funds"
- "Validate transaction history shows correct timestamps"
- "Test SOX compliance audit trail generation"

**REQUIRED JSON FORMAT:**
{
    "test_cases": [
        {
            "case_id": "TC001",
            "name": "Specific test case name reflecting actual requirements",
            "description": "Detailed description of what business scenario is being tested",
            "type": "Functional",
            "priority": "High",
            "preconditions": "Specific prerequisites for this test",
            "steps": ["Detailed step 1", "Detailed step 2", "Specific verification step"],
            "expected_result": "Specific expected outcome",
            "test_data": "Specific test data needed"
        }
    ],
    "quality_metrics": {"overall_score": 85, "completeness": 0.9, "clarity": 0.8},
    "coverage_analysis": {"current_coverage": 80, "functional_coverage": 85},
    "requirements_analysis": {"complexity": "Medium", "kb_enhanced": true}
}

Generate SPECIFIC test cases NOW based on the actual requirements provided:
```

---

## ⚙️ PARÁMETROS DE CONFIGURACIÓN CLAUDE

### **Configuración Bedrock Runtime:**

```json
{
    "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
    "body": {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4000,
        "temperature": 0.3,
        "top_p": 0.9,
        "messages": [
            {
                "role": "user", 
                "content": "{PROMPT_COMPLETO_ARRIBA}"
            }
        ]
    }
}
```

### **Explicación de Parámetros:**
- **`max_tokens: 4000`**: Permite respuestas extensas con casos detallados
- **`temperature: 0.3`**: Baja creatividad, alta consistencia y precisión
- **`top_p: 0.9`**: Equilibrio entre diversidad e coherencia
- **`anthropic_version`**: Versión de API Bedrock específica

---

## 🔄 FLUJO COMPLETO DE CONSTRUCCIÓN DEL PROMPT

### **1. Base del Prompt**
```python
prompt = f"""You are an expert test planning agent. Create SPECIFIC and DETAILED test cases for this system.

**SYSTEM TO TEST:**
Title: {requirements.get('title', 'Test Plan')}
Requirements: {requirements.get('requirements', '')}
```

### **2. Knowledge Base Context (Dinámico)**
```python
kb_context = ""
if kb_insights.get('insights'):
    kb_context = f"""
**Knowledge Base Insights:**
{chr(10).join('- ' + insight for insight in kb_insights['insights'])}

**Recommended Test Cases from KB:**
{chr(10).join('- ' + tc.get('name', 'Test case') + ': ' + tc.get('description', '') for tc in kb_insights.get('recommended_test_cases', []))}
"""
```

### **3. Instrucciones Dinámicas**
```python
**INSTRUCTIONS:**
1. Analyze the specific requirements carefully
2. Create {requirements.get('min_test_cases', 5)} to {requirements.get('max_test_cases', 15)} SPECIFIC test cases
3. Each test case must be directly related to the requirements
4. Include specific business scenarios, not generic tests
5. Focus on the actual functionality described in the requirements
```

### **4. Formato JSON Requerido**
```python
**REQUIRED JSON FORMAT:**
{
    "test_cases": [
        {
            "case_id": "TC001",
            "name": "Specific test case name reflecting actual requirements",
            "description": "Detailed description of what business scenario is being tested",
            "type": "Functional",
            "priority": "High",
            "preconditions": "Specific prerequisites for this test",
            "steps": ["Detailed step 1", "Detailed step 2", "Specific verification step"],
            "expected_result": "Specific expected outcome",
            "test_data": "Specific test data needed"
        }
    ],
    "quality_metrics": {"overall_score": 85, "completeness": 0.9, "clarity": 0.8},
    "coverage_analysis": {"current_coverage": 80, "functional_coverage": 85},
    "requirements_analysis": {"complexity": "Medium", "kb_enhanced": true}
}
```

---

## 🎯 CARACTERÍSTICAS CLAVE DEL PROMPT

### **✅ FORTALEZAS IDENTIFICADAS:**

1. **🎯 Especificidad Forzada**: 
   - "Create SPECIFIC and DETAILED test cases"
   - "Each test case must be directly related to the requirements"
   - "Include specific business scenarios, not generic tests"

2. **📝 Ejemplos Concretos**:
   - Proporciona ejemplos específicos para sistemas bancarios
   - Muestra el nivel de detalle esperado

3. **🧠 Knowledge Base Integration**:
   - Incluye insights dinámicos de la KB
   - Incorpora recomendaciones especializadas

4. **📊 Formato Estructurado**:
   - JSON schema estricto
   - Campos obligatorios bien definidos
   - Métricas de calidad incluidas

5. **🔢 Parámetros Dinámicos**:
   - Rango de casos configurable
   - Adaptación automática al contexto

### **⚙️ ELEMENTOS DINÁMICOS:**

- **Title & Requirements**: Se sustituyen desde el input del usuario
- **KB Context**: Se genera automáticamente desde Knowledge Base VH6SRH9ZNO
- **Test Case Range**: min_test_cases a max_test_cases configurables
- **Examples**: Contextuales según el tipo de sistema

### **🛡️ ROBUSTEZ:**

- **Instrucciones Claras**: Reduce ambigüedad en la respuesta
- **Formato Fijo**: JSON schema garantiza estructura consistente
- **Ejemplos Específicos**: Guían al modelo hacia el nivel de detalle correcto
- **Knowledge Base**: Añade contexto especializado automáticamente

---

## 📊 CALIDAD DEL PROMPT CONFIRMADA

**Basado en los resultados obtenidos:**
- ✅ **Quality Scores**: 75-90/100
- ✅ **Especificidad**: Casos altamente específicos generados
- ✅ **Diversidad**: Functional, Security, Performance
- ✅ **Coherencia**: Estructura consistente en todas las respuestas
- ✅ **KB Integration**: Insights especializados incluidos efectivamente

**Este prompt es la razón por la cual el agente genera casos de prueba de calidad profesional en lugar de casos genéricos.**

---

## 🚀 PROPUESTAS DE OPTIMIZACIÓN DEL PROMPT

### **OBJETIVO**: Mejorar Quality Score >95/100 y reducir tiempo de respuesta <20 segundos

---

## 🎯 OPTIMIZACIONES DE CALIDAD

### **1. PROMPT ESTRUCTURADO CON CHAIN-OF-THOUGHT**

**Propuesta**: Añadir razonamiento paso a paso para mejorar la calidad analítica.

```
**ANALYSIS PROCESS:**
Before generating test cases, follow this reasoning:

Step 1: REQUIREMENT ANALYSIS
- Identify core functionalities: [list main features]
- Classify complexity level: [Simple|Medium|Complex]
- Detect security requirements: [Yes/No + details]

Step 2: TEST STRATEGY
- Primary test types needed: [Functional|Security|Performance|Integration]
- Critical risk areas: [list top 3 risks]
- Coverage priorities: [rank by business impact]

Step 3: TEST CASE GENERATION
Based on analysis above, generate specific test cases...
```

**Beneficios**:
- ✅ Mejora consistencia analítica
- ✅ Reduce casos genéricos
- ✅ Aumenta relevancia contextual

### **2. CONTEXTO DIMENSIONAL ESPECÍFICO**

**Propuesta**: Estructurar el contexto por dimensiones específicas.

```
**SYSTEM CONTEXT:**
Domain: {Auto-detect: Financial|Healthcare|E-commerce|Security|General}
Complexity: {Auto-calculate based on requirements length and keywords}
Criticality: {Auto-assess: High|Medium|Low based on security/compliance keywords}

**TESTING FOCUS AREAS:**
Primary: {Main functionality testing}
Secondary: {Edge cases and error handling}
Critical: {Security, compliance, performance requirements}
```

**Beneficios**:
- ✅ Contexto más preciso
- ✅ Casos mejor priorizados
- ✅ Cobertura más completa

### **3. EJEMPLOS CONTEXTUALES DINÁMICOS**

**Propuesta**: Reemplazar ejemplos fijos con ejemplos dinámicos según el dominio.

```python
# Lógica para generar ejemplos contextuales
def get_contextual_examples(requirements_text, domain):
    if "financial" in domain or "bank" in requirements_text.lower():
        return BANKING_EXAMPLES
    elif "api" in requirements_text.lower() or "rest" in requirements_text.lower():
        return API_EXAMPLES
    elif "login" in requirements_text.lower() or "auth" in requirements_text.lower():
        return AUTH_EXAMPLES
    # etc...
```

**Ejemplos específicos por dominio**:
- **Banking**: SOX compliance, PCI DSS, anti-money laundering
- **Healthcare**: HIPAA compliance, patient data security
- **E-commerce**: Payment processing, inventory management
- **APIs**: Rate limiting, authentication, data validation

---

## ⚡ OPTIMIZACIONES DE RENDIMIENTO

### **4. PROMPT COMPACTO CON DIRECTIVAS CLARAS**

**Problema actual**: Prompt muy extenso puede aumentar tiempo de procesamiento.

**Propuesta**: Versión compacta pero más directiva.

```
ROLE: Expert test case generator
TASK: Create {N} specific test cases for: {title}
REQUIREMENTS: {requirements}
KB_INSIGHTS: {insights}

CONSTRAINTS:
- Each case MUST relate directly to requirements
- Include: name, description, steps (3-5), expected_result
- Types: Functional, Security, Performance, Integration
- NO generic cases like "verify system works"

OUTPUT: Valid JSON only, no explanations
```

**Beneficios**:
- ✅ Reduce tokens de entrada (~30% menos)
- ✅ Respuesta más directa
- ✅ Menor tiempo de procesamiento

### **5. RESPUESTA PROGRESIVA PARA SISTEMAS COMPLEJOS**

**Problema actual**: JSON parsing falla con respuestas >15K caracteres.

**Propuesta**: Generación en lotes para sistemas complejos.

```
**GENERATION STRATEGY:**
If requirements > 500 chars OR min_test_cases > 8:
  Generate in batches of 4-5 cases max per request
  Use multiple focused prompts instead of one large prompt

**BATCH PROMPT EXAMPLE:**
Generate test cases 1-4 focusing on: {core_functionality}
Next request: Generate test cases 5-8 focusing on: {security_aspects}
```

**Beneficios**:
- ✅ Evita JSON parsing errors
- ✅ Respuestas más específicas por área
- ✅ Mejor control de calidad

### **6. OPTIMIZACIÓN DE PARÁMETROS CLAUDE**

**Propuesta**: Ajustar parámetros para mejor rendimiento.

```json
// Parámetros actuales
{
    "max_tokens": 4000,      // Reducir a 2500
    "temperature": 0.3,      // Reducir a 0.1 para más consistencia
    "top_p": 0.9,           // Reducir a 0.8 para más focus
    "top_k": 40             // Añadir para más control
}

// Parámetros optimizados
{
    "max_tokens": 2500,      // Respuestas más concisas
    "temperature": 0.1,      // Máxima consistencia
    "top_p": 0.8,           // Mayor focus
    "top_k": 40,            // Control adicional
    "stop_sequences": ["```"] // Para evitar código innecesario
}
```

---

## 🧠 OPTIMIZACIONES DE KNOWLEDGE BASE

### **7. KB QUERY INTELIGENTE CON FILTROS**

**Propuesta**: Consultas más específicas a la Knowledge Base.

```python
def intelligent_kb_query(requirements, title):
    # Extraer keywords clave
    keywords = extract_keywords(requirements)
    domain = detect_domain(title, requirements)
    
    # Query específico por dominio
    kb_query = f"""
    Domain: {domain}
    Keywords: {', '.join(keywords)}
    Focus: test planning best practices for {domain}
    Context: {requirements[:200]}...
    """
    
    return kb_query
```

**Beneficios**:
- ✅ Insights más relevantes
- ✅ Menos ruido en el contexto
- ✅ Mejor integración KB-Claude

### **8. KB CONTEXT ESTRUCTURADO**

**Propuesta**: Organizar insights de KB en categorías.

```
**KNOWLEDGE BASE CONTEXT:**

Testing Patterns:
{pattern-specific insights}

Domain Best Practices:
{domain-specific best practices}

Common Pitfalls:
{anti-patterns to avoid}

Quality Criteria:
{what makes a good test case in this domain}
```

---

## 📊 OPTIMIZACIONES DE FORMATO Y VALIDACIÓN

### **9. JSON SCHEMA MÁS ESTRICTO**

**Propuesta**: Schema más detallado para mejor parsing.

```json
{
    "test_cases": [
        {
            "case_id": "TC001",
            "name": "string (max 100 chars)",
            "description": "string (max 200 chars)",
            "type": "enum[Functional,Security,Performance,Integration,Usability]",
            "priority": "enum[Critical,High,Medium,Low]",
            "preconditions": "string (max 150 chars)",
            "steps": ["string array (3-7 items, max 100 chars each)"],
            "expected_result": "string (max 150 chars)",
            "test_data": "string (max 100 chars)",
            "estimated_time": "string (format: XhYm)",
            "automation_level": "enum[Manual,Semi-automated,Automated]"
        }
    ]
}
```

### **10. VALIDACIÓN EN TIEMPO REAL**

**Propuesta**: Validar respuesta antes del parsing completo.

```python
def validate_response_structure(response_text):
    # Verificar que contiene JSON válido
    # Verificar campos obligatorios
    # Verificar límites de caracteres
    # Return True/False + error details
    
def progressive_parsing(response_text):
    # Intentar parsing completo
    # Si falla, intentar parsing parcial
    # Si falla, usar text fallback mejorado
```

---

## 🎯 OPTIMIZACIONES AVANZADAS

### **11. PROMPT ADAPTATIVO POR COMPLEJIDAD**

**Propuesta**: Diferentes prompts según complejidad detectada.

```python
def select_prompt_strategy(requirements):
    complexity = calculate_complexity(requirements)
    
    if complexity == "Simple":
        return SIMPLE_PROMPT_TEMPLATE  # Más directo, menos contexto
    elif complexity == "Medium":
        return STANDARD_PROMPT_TEMPLATE  # Prompt actual
    else:  # Complex
        return DETAILED_PROMPT_TEMPLATE  # Más estructura, Chain-of-Thought
```

### **12. MEMORY CACHE PARA PATRONES COMUNES**

**Propuesta**: Cache de patrones de respuesta exitosos.

```python
# Cache de patterns exitosos
SUCCESSFUL_PATTERNS = {
    "login_systems": {
        "common_cases": ["successful_login", "failed_auth", "password_recovery"],
        "quality_factors": ["specific_steps", "error_handling", "security_focus"]
    },
    "api_systems": {
        "common_cases": ["auth_validation", "rate_limiting", "data_validation"],
        "quality_factors": ["http_codes", "boundary_testing", "security_headers"]
    }
}
```

### **13. A/B TESTING DE PROMPTS**

**Propuesta**: Sistema para probar diferentes versiones de prompts.

```python
PROMPT_VARIANTS = {
    "current": current_prompt,
    "optimized_v1": chain_of_thought_prompt,
    "optimized_v2": compact_directive_prompt,
    "optimized_v3": contextual_examples_prompt
}

# Métricas para comparar
- Average quality score
- Response time
- JSON parsing success rate
- User satisfaction
```

---

## 📈 MÉTRICAS DE ÉXITO ESPERADAS

### **Mejoras Cuantificables**:

| Métrica | Actual | Meta Optimizada | Mejora |
|---------|--------|-----------------|---------|
| Quality Score | 75-90/100 | 90-98/100 | +10-15% |
| Tiempo Respuesta | 23-48s | 15-30s | ~35% más rápido |
| JSON Parse Success | ~85% | >95% | +10% |
| Especificidad Cases | Alta | Muy Alta | +15% |
| KB Integration | Buena | Excelente | +20% |

### **Beneficios Cualitativos Esperados**:
- ✅ Casos más específicos y ejecutables
- ✅ Mejor cobertura de edge cases
- ✅ Reducción de casos genéricos a ~0%
- ✅ Mayor consistencia entre ejecuciones
- ✅ Mejor adaptación al contexto del dominio

---

## 🛠️ PLAN DE IMPLEMENTACIÓN SUGERIDO

### **Fase 1: Optimizaciones Inmediatas** (1-2 semanas)
1. Ajustar parámetros Claude (temperature: 0.1, max_tokens: 2500)
2. Implementar prompt compacto para casos simples
3. Añadir validación de respuesta mejorada

### **Fase 2: Mejoras Estructurales** (2-3 semanas)
1. Implementar Chain-of-Thought para casos complejos
2. Desarrollar ejemplos contextuales dinámicos
3. Mejorar KB query inteligente

### **Fase 3: Optimizaciones Avanzadas** (3-4 semanas)
1. Sistema de prompt adaptativo
2. A/B testing framework
3. Memory cache para patrones comunes

### **Fase 4: Validación y Refinamiento** (1-2 semanas)
1. Testing exhaustivo con métricas
2. Comparación A/B con prompt actual
3. Ajustes finales basados en resultados

---

*Propuestas de optimización basadas en análisis de rendimiento actual y mejores prácticas de prompt engineering para Claude Sonnet - Octubre 2025*
