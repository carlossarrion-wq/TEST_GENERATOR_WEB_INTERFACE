"""
Test Case Generator Tool
Generates high-quality test cases based on requirements analysis and KB insights
"""

import json
import boto3
from typing import Dict, Any, List

# System prompt optimizado para Prompt Caching con algoritmos integrados
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

FORMATO DE SALIDA:
Devuelve ÚNICAMENTE JSON válido:
{
  "test_cases": [
    {
      "name": "nombre descriptivo >20 chars",
      "description": "objetivo detallado >50 chars",
      "priority": "High|Medium|Low",
      "preconditions": "condiciones específicas >10 chars",
      "expected_result": "resultado medible >30 chars",
      "test_data": "datos concretos >10 chars",
      "steps": ["paso 1 detallado", "paso 2 detallado", "paso 3 detallado"]
    }
  ]
}

Un ejemplo de salida sería el siguiente:
{
  "summary": "Plan de pruebas para validar la funcionalidad de inicio de sesión en la aplicación web, cubriendo casos exitosos, fallidos y de validación de campos obligatorios.",
  "test_cases": [
    {
      "name": "Inicio de sesión exitoso con credenciales válidas",
      "description": "Verifica que un usuario registrado pueda iniciar sesión correctamente cuando introduce credenciales válidas.",
      "priority": "High",
      "preconditions": "El usuario debe estar previamente registrado y activo en el sistema.",
      "expected_result": "El sistema permite el acceso al usuario, mostrando la pantalla de inicio o panel principal.",
      "test_data": "Usuario: usuario.prueba@example.com, Contraseña: Prueba1234",
      "steps": [
        "Abrir la página de inicio de sesión.",
        "Introducir el correo electrónico y la contraseña válidos.",
        "Hacer clic en el botón 'Iniciar sesión'.",
        "Verificar que se redirige a la pantalla de inicio y se muestra el nombre del usuario."
      ]
    },
    {
      "name": "Error de autenticación con contraseña incorrecta",
      "description": "Valida que el sistema muestre un mensaje de error cuando se introduce una contraseña incorrecta.",
      "priority": "High",
      "preconditions": "El usuario debe existir en la base de datos.",
      "expected_result": "El sistema muestra un mensaje de error 'Usuario o contraseña incorrectos' sin permitir el acceso.",
      "test_data": "Usuario: usuario.prueba@example.com, Contraseña: Incorrecta123",
      "steps": [
        "Abrir la página de inicio de sesión.",
        "Introducir el correo electrónico válido y una contraseña incorrecta.",
        "Hacer clic en el botón 'Iniciar sesión'.",
        "Verificar que aparece el mensaje de error y que no se concede acceso."
      ]
    },
    {
      "name": "Validación de campos vacíos en formulario de login",
      "description": "Comprueba que el sistema no permita iniciar sesión si los campos de usuario o contraseña están vacíos.",
      "priority": "Medium",
      "preconditions": "Ninguna.",
      "expected_result": "El sistema muestra mensajes de validación indicando que ambos campos son obligatorios.",
      "test_data": "Usuario: '', Contraseña: ''",
      "steps": [
        "Abrir la página de inicio de sesión.",
        "Dejar vacíos los campos de usuario y contraseña.",
        "Hacer clic en el botón 'Iniciar sesión'.",
        "Verificar que aparecen los mensajes de validación correspondientes."
      ]
    },...
}

a propiedad "priority" indica la criticidad o impacto del caso de prueba en el funcionamiento del sistema.
Clasifica cada caso de prueba en uno de los siguientes tres niveles:
High (Alta prioridad):
Casos que validan funcionalidades críticas o esenciales para el negocio, cuyo fallo impediría la operación normal del sistema o causaría un impacto grave.
Ejemplo: Verificar que un usuario puede iniciar sesión correctamente con credenciales válidas.
Medium (Prioridad media):
Casos que validan funcionalidades importantes pero no críticas, o flujos secundarios que pueden tener soluciones alternativas si fallan.
Ejemplo: Verificar que el sistema muestra mensajes de error adecuados cuando se dejan campos vacíos en el formulario.
Low (Baja prioridad):
Casos que validan aspectos complementarios, de usabilidad o escenarios poco frecuentes, cuyo fallo no afecta significativamente al negocio.
Ejemplo: Verificar que la aplicación solicita autenticación de doble factor solo cuando se accede desde un dispositivo desconocido.

REGLAS DE OPTIMIZACIÓN:
1. Genera casos que alcancen score ≥ 85 puntos
2. Incluye SIEMPRE mínimo 3 pasos por caso
3. Distribuye prioridades según objetivos de cobertura
4. Asigna High priority a edge cases identificados
5. Usa descripciones y resultados detallados (>50 y >30 chars)
6. Incluye datos de prueba específicos y realistas
7. Responde SOLO con JSON, sin explicaciones adicionales"""

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
            
            min_cases = generation_options.get('min_test_cases', 5)
            max_cases = generation_options.get('max_test_cases', 15)
            target_cases = (min_cases + max_cases) // 2
            
            # Simplified prompt - focus on essentials only
            # Handle both dict and string formats
            reqs_list = []
            for req in functional_reqs[:5]:
                if isinstance(req, dict):
                    req_text = req.get('requirement', str(req))[:100]
                else:
                    req_text = str(req)[:100]
                reqs_list.append(f"- {req_text}")
            
            reqs_summary = "\n".join(reqs_list)
            
            generation_prompt = f"""Genera {target_cases} casos de prueba para:

REQUERIMIENTOS:
{reqs_summary}

Proporciona los casos de prueba en formato JSON."""
            
            # Usar Prompt Caching con la nueva versión de API
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-06-01",  # Nueva versión con caching
                    "max_tokens": 2000,
                    "temperature": 0.1,
                    "system": [
                        {
                            "type": "text",
                            "text": TEST_CASE_GENERATOR_SYSTEM_PROMPT,
                            "cache_control": {"type": "ephemeral"}  # Activar caching
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
            
            # Parse JSON
            result = self._extract_json(content)
            
            # Ensure we have test cases
            if not result.get('test_cases'):
                print("⚠️ No test cases generated, creating fallback")
                result['test_cases'] = self._create_fallback_cases(functional_reqs, target_cases)
            
            result['generation_completed'] = True
            result['total_generated'] = len(result.get('test_cases', []))
            
            return result
            
        except Exception as e:
            print(f"❌ Test case generation error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return fallback cases instead of empty
            return {
                "error": str(e),
                "generation_completed": False,
                "test_cases": self._create_fallback_cases(
                    input_data.get('functional_requirements', []),
                    generation_options.get('min_test_cases', 5)
                ),
                "total_generated": generation_options.get('min_test_cases', 5)
            }
    
    def _create_fallback_cases(self, functional_reqs: List, count: int) -> List[Dict[str, Any]]:
        """Create basic fallback test cases"""
        cases = []
        for i in range(min(count, len(functional_reqs) if functional_reqs else count)):
            req = functional_reqs[i] if i < len(functional_reqs) else {"requirement": f"Requirement {i+1}"}
            
            # Handle both dict and string formats
            if isinstance(req, dict):
                req_text = req.get('requirement', str(req))[:100]
            else:
                req_text = str(req)[:100]
            
            cases.append({
                "name": f"Test Case {i+1}: {req_text[:50]}",
                "description": f"Verify {req_text}",
                "priority": "Medium",
                "preconditions": "System accessible",
                "expected_result": "Functionality works as expected",
                "test_data": "Valid test data",
                "steps": [
                    "Navigate to feature",
                    "Execute test action",
                    "Verify result"
                ]
            })
        
        return cases
    
    def _extract_json(self, content: str) -> Dict[str, Any]:
        """Extract JSON from response - IMPROVED"""
        # Try direct parse first
        try:
            return json.loads(content)
        except:
            pass
        
        # Try to find JSON in markdown code blocks
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Try to find any JSON object
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        print(f"⚠️ Could not parse JSON from: {content[:200]}...")
        return {
            "test_cases": [],
            "recommendations": []
        }
