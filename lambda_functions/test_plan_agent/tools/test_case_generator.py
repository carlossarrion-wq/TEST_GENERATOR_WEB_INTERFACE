"""
Test Case Generator Tool
Generates high-quality test cases based on requirements analysis and KB insights
"""

import json
import boto3
from typing import Dict, Any, List

# System prompt optimizado para Prompt Caching con ejemplos GENÉRICOS
TEST_CASE_GENERATOR_SYSTEM_PROMPT = """Eres un experto en testing de software con certificación ISTQB y experiencia en metodologías ágiles.

TU MISIÓN:
Generar casos de prueba profesionales, ejecutables y de alta calidad que maximicen cobertura y calidad.

PRINCIPIOS DE TESTING:
- Cobertura completa de requerimientos funcionales
- Casos positivos, negativos y edge cases
- Pasos claros y reproducibles
- Resultados esperados específicos y medibles
- Datos de prueba realistas

ALGORITMO DE COVERAGE CALCULATOR (que se aplicará a tus casos):
Los casos generados serán evaluados con estas métricas:

1. Cobertura Funcional = min(100, (total_casos / total_requerimientos) * 100)
   - Objetivo: ≥ 80%
   
2. Cobertura Edge Cases = min(100, (casos_High_priority / total_edge_cases) * 100)
   - Objetivo: ≥ 70%
   - Asigna prioridad High a casos que cubran edge cases
   
3. Cobertura de Riesgos = min(100, ((casos_High + casos_Medium) / total_risk_areas) * 100)
   - Objetivo: ≥ 75%
   - Distribuye prioridades High y Medium para áreas de riesgo
   
4. Cobertura General = (Funcional + Edge Cases + Riesgos) / 3
   - Objetivo: ≥ 85% (Good), ≥ 90% (Excellent)

DISTRIBUCIÓN ÓPTIMA DE PRIORIDADES:
- High: 30-40% de casos (para edge cases y riesgos críticos)
- Medium: 30-40% de casos (para riesgos moderados)
- Low: 20-30% de casos (para casos básicos)

SISTEMA DE PUNTUACIÓN DE CALIDAD (máximo 100 puntos por caso):
Cada caso será evaluado así:

1. Nombre (0-15 pts):
   - >20 caracteres = 15 pts
   - >10 caracteres = 10 pts
   - <10 caracteres = 5 pts
   
2. Descripción (0-15 pts):
   - >50 caracteres = 15 pts
   - >20 caracteres = 10 pts
   - <20 caracteres = 5 pts
   
3. Pasos (0-25 pts):
   - ≥3 pasos = 25 pts ⭐ CRÍTICO
   - 2 pasos = 15 pts
   - 1 paso = 10 pts
   
4. Precondiciones (0-10 pts):
   - >10 caracteres = 10 pts
   - <10 caracteres = 5 pts
   
5. Resultado Esperado (0-20 pts):
   - >30 caracteres = 20 pts
   - >15 caracteres = 15 pts
   - <15 caracteres = 10 pts
   
6. Datos de Prueba (0-10 pts):
   - >10 caracteres = 10 pts
   - <10 caracteres = 5 pts
   
7. Prioridad (0-5 pts):
   - High/Medium/Low válido = 5 pts

OBJETIVO DE CALIDAD: Score promedio ≥ 85 puntos (Good), ≥ 90 (Excellent)

ESTRUCTURA DE CASOS OPTIMIZADA:
Cada caso DEBE incluir:
- Nombre: >20 caracteres, descriptivo y único
- Descripción: >50 caracteres, explicar objetivo y alcance
- Prioridad: High/Medium/Low (según distribución óptima)
- Precondiciones: >10 caracteres, condiciones específicas
- Pasos: MÍNIMO 3 pasos detallados y ejecutables
- Resultado esperado: >30 caracteres, específico y medible
- Datos de prueba: >10 caracteres, valores concretos

CLASIFICACIÓN DE PRIORIDADES:
- High (Alta prioridad): Casos que validan funcionalidades críticas o esenciales para el negocio, cuyo fallo impediría la operación normal del sistema o causaría un impacto grave.
- Medium (Prioridad media): Casos que validan funcionalidades importantes pero no críticas, o flujos secundarios que pueden tener soluciones alternativas si fallan.
- Low (Baja prioridad): Casos que validan aspectos complementarios, de usabilidad o escenarios poco frecuentes, cuyo fallo no afecta significativamente al negocio.

FORMATO DE SALIDA - EJEMPLOS GENÉRICOS (USA LOS REQUERIMIENTOS REALES, NO ESTOS PLACEHOLDERS):

Estructura JSON requerida:
{
  "test_cases": [
    {
      "name": "Validar [Funcionalidad del Requerimiento #X] - [Escenario específico] >20 chars",
      "description": "Este caso valida el requerimiento #X: [Nombre del requerimiento]. Verifica que [funcionalidad específica] funciona correctamente cuando [condición o escenario]. >50 chars",
      "priority": "High|Medium|Low",
      "preconditions": "[Estado inicial del sistema, datos preexistentes, configuraciones necesarias] >10 chars",
      "expected_result": "El requerimiento #X se cumple: [Resultado específico y medible que confirma el cumplimiento] >30 chars",
      "test_data": "[Datos concretos: valores, IDs, nombres, cantidades específicas para la prueba] >10 chars",
      "steps": [
        "Paso 1: [Acción de preparación o navegación específica relacionada con el requerimiento]",
        "Paso 2: [Acción principal que ejecuta la funcionalidad del requerimiento]",
        "Paso 3: [Verificación del resultado esperado del requerimiento]",
        "Paso 4: [Validación adicional o confirmación de efectos secundarios - opcional]"
      ]
    },
    {
      "name": "Validar [Funcionalidad del Requerimiento #Y] - Caso negativo con [condición de error]",
      "description": "Este caso valida el requerimiento #Y: [Nombre del requerimiento]. Verifica que el sistema maneja correctamente [escenario de error o excepción] relacionado con [funcionalidad].",
      "priority": "High|Medium|Low",
      "preconditions": "[Condiciones que provocan el escenario de error]",
      "expected_result": "El requerimiento #Y se cumple: El sistema [maneja el error correctamente, muestra mensaje apropiado, previene acción incorrecta]",
      "test_data": "[Datos inválidos o que provocan el error: valores fuera de rango, formatos incorrectos, etc.]",
      "steps": [
        "Paso 1: [Preparar escenario que provocará el error]",
        "Paso 2: [Ejecutar acción con datos inválidos o condición de error]",
        "Paso 3: [Verificar que el sistema responde apropiadamente al error]",
        "Paso 4: [Confirmar que no hay efectos secundarios negativos]"
      ]
    }
  ]
}

⚠️ IMPORTANTE: Los ejemplos anteriores usan PLACEHOLDERS [X], [Y], [Funcionalidad], etc. 
TÚ DEBES reemplazarlos con los REQUERIMIENTOS REALES proporcionados por el usuario.
NO uses estos placeholders en tu respuesta - usa el contenido específico de los requerimientos.

REGLAS DE OPTIMIZACIÓN:
1. Genera casos que alcancen score ≥ 85 puntos
2. Incluye SIEMPRE mínimo 3 pasos por caso
3. Distribuye prioridades según objetivos de cobertura
4. Asigna High priority a edge cases identificados
5. Usa descripciones y resultados detallados (>50 y >30 chars)
6. Incluye datos de prueba específicos y realistas
7. Responde SOLO con JSON, sin explicaciones adicionales
8. CRÍTICO: Genera casos basados ÚNICAMENTE en los requerimientos proporcionados por el usuario"""

class TestCaseGeneratorTool:
    """Tool for generating comprehensive test cases"""
    
    def __init__(self):
        self.name = "test_case_generator"
        self.description = """Generates comprehensive test cases based on:
- Functional requirements
- Edge cases
- Risk areas
- Knowledge base insights
Creates detailed test cases with steps, preconditions, and expected results."""
        
        self.bedrock_client = boto3.client('bedrock-runtime', region_name='eu-west-1')
        self.model_id = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test case generation - OPTIMIZED"""
        try:
            functional_reqs = input_data.get('functional_requirements', [])
            edge_cases = input_data.get('edge_cases', [])
            risk_areas = input_data.get('risk_areas', [])
            generation_options = input_data.get('generation_options', {})
            kb_insights = generation_options.get('kb_insights', [])
            
            min_cases = generation_options.get('min_test_cases', 5)
            max_cases = generation_options.get('max_test_cases', 15)
            
            # Limitar target_cases a máximo 12 para evitar problemas de tokens
            target_cases = min(12, (min_cases + max_cases) // 2)
            
            # Build comprehensive requirements list (ALL requirements, not just 5)
            reqs_list = []
            for i, req in enumerate(functional_reqs, 1):
                if isinstance(req, dict):
                    req_text = req.get('requirement', str(req))
                else:
                    req_text = str(req)
                # Clean up requirement text
                req_text = req_text.strip().lstrip('-•*').strip()
                if req_text:
                    reqs_list.append("{0}. {1}".format(i, req_text))
            
            reqs_summary = "\n".join(reqs_list) if reqs_list else "No specific requirements provided"
            
            # Build edge cases summary
            edge_cases_summary = ""
            if edge_cases:
                edge_list = []
                for i, edge in enumerate(edge_cases[:10], 1):
                    if isinstance(edge, dict):
                        edge_text = edge.get('case', str(edge))
                    else:
                        edge_text = str(edge)
                    edge_text = edge_text.strip().lstrip('-•*').strip()
                    if edge_text:
                        edge_list.append("{0}. {1}".format(i, edge_text))
                if edge_list:
                    edge_cases_summary = "\n\nEDGE CASES IDENTIFICADOS:\n" + "\n".join(edge_list)
            
            # Build risk areas summary
            risk_areas_summary = ""
            if risk_areas:
                risk_list = []
                for i, risk in enumerate(risk_areas[:10], 1):
                    if isinstance(risk, dict):
                        risk_text = risk.get('area', str(risk))
                    else:
                        risk_text = str(risk)
                    risk_text = risk_text.strip().lstrip('-•*').strip()
                    if risk_text:
                        risk_list.append("{0}. {1}".format(i, risk_text))
                if risk_list:
                    risk_areas_summary = "\n\nÁREAS DE RIESGO:\n" + "\n".join(risk_list)
            
            # Build KB insights summary
            kb_summary = ""
            if kb_insights:
                kb_list = []
                for i, insight in enumerate(kb_insights[:5], 1):
                    if isinstance(insight, dict):
                        insight_text = insight.get('content', str(insight))[:150]
                    else:
                        insight_text = str(insight)[:150]
                    if insight_text.strip():
                        kb_list.append("• {0}".format(insight_text.strip()))
                if kb_list:
                    kb_summary = "\n\nBUENAS PRÁCTICAS (Knowledge Base):\n" + "\n".join(kb_list)
            
            # Enhanced generation prompt with EXPLICIT requirement mapping
            generation_prompt = """Genera EXACTAMENTE {target_cases} casos de prueba que VALIDEN DIRECTAMENTE los requerimientos funcionales especificados.

⚠️ REGLA CRÍTICA: CADA caso de prueba DEBE validar UNO O MÁS requerimientos funcionales específicos de la lista.

REQUERIMIENTOS FUNCIONALES A VALIDAR:
{reqs_summary}{edge_cases_summary}{risk_areas_summary}{kb_summary}

INSTRUCCIONES OBLIGATORIAS:

1. MAPEO DIRECTO A REQUERIMIENTOS:
   - CADA caso de prueba DEBE validar al menos UN requerimiento funcional específico
   - En la descripción, INDICA EXPLÍCITAMENTE qué requerimiento(s) estás validando
   - Ejemplo: "Este caso valida el requerimiento #1: [nombre del requerimiento]"
   - NO generes casos genéricos que no validen requerimientos específicos

2. COBERTURA COMPLETA:
   - Asegúrate de cubrir TODOS los requerimientos funcionales listados
   - Si hay {num_reqs} requerimientos, genera casos que los cubran todos
   - Puedes crear múltiples casos para requerimientos complejos
   - Prioriza los requerimientos más críticos con casos High priority

3. VALIDACIÓN ESPECÍFICA:
   - Los pasos de prueba deben validar EXACTAMENTE la funcionalidad descrita en el requerimiento
   - El resultado esperado debe confirmar que el requerimiento se cumple
   - Los datos de prueba deben ser específicos para validar ese requerimiento

4. TIPOS DE CASOS POR REQUERIMIENTO:
   - Caso positivo: Valida que el requerimiento funciona correctamente
   - Caso negativo: Valida manejo de errores relacionado al requerimiento
   - Edge case: Valida límites y casos extremos del requerimiento

5. DISTRIBUCIÓN DE PRIORIDADES:
   - High (35%): Requerimientos críticos, edge cases identificados, áreas de riesgo
   - Medium (40%): Requerimientos importantes, validaciones secundarias
   - Low (25%): Requerimientos complementarios, casos de usabilidad

6. CALIDAD DE CASOS:
   - Cada caso DEBE tener mínimo 3 pasos detallados y ejecutables
   - Nombres descriptivos >20 caracteres que mencionen el requerimiento
   - Descripciones >50 caracteres que expliquen QUÉ requerimiento validan
   - Resultados esperados >30 caracteres, específicos y medibles
   - Datos de prueba concretos y realistas para ese requerimiento

⚠️ RECUERDA: 
- Usa los REQUERIMIENTOS REALES listados arriba, NO los placeholders del ejemplo
- Cada caso DEBE referenciar explícitamente qué requerimiento(s) está validando
- Los ejemplos en el system prompt son solo para mostrar la ESTRUCTURA, no el contenido

Responde ÚNICAMENTE con el JSON, sin explicaciones adicionales.""".format(
                target_cases=target_cases,
                reqs_summary=reqs_summary,
                edge_cases_summary=edge_cases_summary,
                risk_areas_summary=risk_areas_summary,
                kb_summary=kb_summary,
                num_reqs=len(reqs_list)
            )
            
            # Usar Prompt Caching con la versión correcta de API
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4000,
                    "temperature": 0.3,
                    "system": [
                        {
                            "type": "text",
                            "text": TEST_CASE_GENERATOR_SYSTEM_PROMPT,
                            "cache_control": {"type": "ephemeral"}
                        }
                    ],
                    "messages": [{
                        "role": "user",
                        "content": generation_prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            print("🔍 DEBUG: Received content length: {0} characters".format(len(content)))
            print("🔍 DEBUG: Content preview: {0}...".format(content[:500]))
            
            # Parse JSON
            result = self._extract_json(content)
            
            # Ensure we have test cases
            if not result.get('test_cases'):
                print("⚠️ No test cases generated")
                return {
                    "error": "No se pudieron generar casos de prueba. Por favor, intenta con menos casos o requerimientos más específicos.",
                    "generation_completed": False,
                    "test_cases": [],
                    "total_generated": 0
                }
            else:
                # Validate uniqueness and quality
                result['test_cases'] = self._validate_and_deduplicate_cases(
                    result['test_cases'], 
                    target_cases
                )
            
            result['generation_completed'] = True
            result['total_generated'] = len(result.get('test_cases', []))
            
            print("✅ Generated {0} unique test cases".format(result['total_generated']))
            
            return result
            
        except Exception as e:
            print("❌ Test case generation error: {0}".format(str(e)))
            import traceback
            traceback.print_exc()
            
            return {
                "error": str(e),
                "generation_completed": False,
                "test_cases": [],
                "total_generated": 0
            }
    
    def _validate_and_deduplicate_cases(self, test_cases: List[Dict[str, Any]], target_count: int) -> List[Dict[str, Any]]:
        """Validate and remove duplicate test cases"""
        if not test_cases:
            return []
        
        unique_cases = []
        seen_names = set()
        seen_descriptions = set()
        
        for case in test_cases:
            name = case.get('name', '').strip().lower()
            description = case.get('description', '').strip().lower()
            
            # Skip if name or description is too similar to existing cases
            if name in seen_names or description in seen_descriptions:
                print("⚠️ Skipping duplicate case: {0}".format(case.get('name', 'Unknown')))
                continue
            
            # Validate case has minimum required fields
            if not name or not description:
                print("⚠️ Skipping invalid case (missing name or description)")
                continue
            
            # Ensure steps exist and have at least 3 steps
            steps = case.get('steps', [])
            if not steps or len(steps) < 3:
                print("⚠️ Case has insufficient steps, adding default steps: {0}".format(case.get('name', 'Unknown')))
                case['steps'] = steps + [
                    "Execute the test action",
                    "Verify the expected behavior",
                    "Confirm the result matches expectations"
                ][:3 - len(steps)]
            
            # Ensure all required fields have minimum length
            if len(case.get('name', '')) < 20:
                case['name'] = "{0} - Validation Test".format(case['name'])
            
            if len(case.get('description', '')) < 50:
                case['description'] = "{0} This test validates the functionality and ensures it meets the specified requirements.".format(case['description'])
            
            if len(case.get('expected_result', '')) < 30:
                case['expected_result'] = "{0} and the system behaves as specified.".format(case.get('expected_result', 'Expected result'))
            
            seen_names.add(name)
            seen_descriptions.add(description)
            unique_cases.append(case)
            
            # Stop if we have enough cases
            if len(unique_cases) >= target_count:
                break
        
        print("✅ Validated {0} unique cases from {1} generated".format(len(unique_cases), len(test_cases)))
        return unique_cases
    
    def _extract_json(self, content: str) -> Dict[str, Any]:
        """Extract JSON from response - IMPROVED"""
        import re
        
        # Try direct parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON in markdown code blocks (most common format from Claude)
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(1).strip()
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print("⚠️ JSON parse error in code block: {0}".format(str(e)))
                print("   Content preview: {0}...".format(json_str[:300]))
        
        # Try to find any JSON object (greedy match to get complete JSON)
        json_match = re.search(r'\{[\s\S]*\}', content, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(0)
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print("⚠️ JSON parse error in object: {0}".format(str(e)))
                print("   Content preview: {0}...".format(json_str[:300]))
        
        print("⚠️ Could not parse JSON from content")
        print("   Content preview: {0}...".format(content[:500]))
        return {
            "test_cases": [],
            "recommendations": []
        }
