"""
Requirements Analyzer Tool
Analyzes requirements to extract functional requirements, edge cases, and risk areas
"""

import json
import boto3
from typing import Dict, Any, List

# System prompt optimizado para Prompt Caching
REQUIREMENTS_ANALYZER_SYSTEM_PROMPT = """Eres un experto analista de requerimientos de software con más de 15 años de experiencia.

TU MISIÓN:
Analizar requerimientos funcionales y extraer información estructurada para testing.

CAPACIDADES:
- Identificar requerimientos funcionales explícitos e implícitos
- Detectar edge cases y condiciones de frontera
- Evaluar áreas de riesgo técnico y de negocio
- Clasificar complejidad del proyecto

FORMATO DE SALIDA:
Devuelve ÚNICAMENTE JSON válido con esta estructura:
{
  "functional_requirements": ["req1", "req2", ...],
  "edge_cases": ["edge1", "edge2", ...],
  "risk_areas": ["risk1", "risk2", ...],
  "complexity_analysis": {
    "complexity_level": "Low|Medium|High",
    "reasoning": "explicación detallada"
  }
}

REGLAS:
1. Sé exhaustivo en la identificación de requerimientos
2. Prioriza edge cases críticos
3. Evalúa riesgos técnicos y de negocio
4. Responde SOLO con JSON, sin explicaciones adicionales"""

class RequirementsAnalyzerTool:
    """Tool for analyzing requirements and extracting key information"""
    
    def __init__(self):
        self.name = "requirements_analyzer"
        self.description = """Analyzes software requirements to extract:
- Functional requirements
- Edge cases and boundary conditions
- Risk areas and potential issues
- Complexity assessment
Use this tool first to understand what needs to be tested."""
        
        self.bedrock_client = boto3.client('bedrock-runtime', region_name='eu-west-1')
        self.model_id = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute requirements analysis"""
        try:
            requirements = input_data.get('requirements', '')
            
            if not requirements:
                return {
                    "error": "No requirements provided",
                    "analysis_completed": False
                }
            
            # Analyze with Haiku 4.5 + Prompt Caching
            analysis_prompt = f"""Analiza los siguientes requerimientos:

REQUERIMIENTOS:
{requirements}

Proporciona el análisis completo en formato JSON."""
            
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
                            "text": REQUIREMENTS_ANALYZER_SYSTEM_PROMPT,
                            "cache_control": {"type": "ephemeral"}  # Activar caching
                        }
                    ],
                    "messages": [{
                        "role": "user",
                        "content": analysis_prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            # Parse JSON
            result = self._extract_json(content)
            result['analysis_completed'] = True
            
            return result
            
        except Exception as e:
            return {
                "error": str(e),
                "analysis_completed": False,
                "functional_requirements": [],
                "edge_cases": [],
                "risk_areas": []
            }
    
    def _extract_json(self, content: str) -> Dict[str, Any]:
        """Extract JSON from response"""
        try:
            return json.loads(content)
        except:
            import re
            json_match = re.search(r'{[\s\S]*}', content)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass
            return {
                "functional_requirements": [],
                "edge_cases": [],
                "risk_areas": [],
                "complexity_analysis": {"complexity_level": "Medium", "reasoning": "Could not parse"}
            }
