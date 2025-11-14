"""
Interactive Chat Agent for Test Case Management
Uses Claude Haiku 4.5 to process natural language commands and modify test cases
"""

import json
import boto3
import re
from typing import Dict, List, Any, Optional

# Initialize Bedrock client
bedrock_client = boto3.client('bedrock-runtime', region_name='eu-west-1')
MODEL_ID = 'eu.anthropic.claude-haiku-4-5-20251001-v1:0'

# System prompt for Claude
SYSTEM_PROMPT = """Eres un asistente especializado en gestión de casos de prueba. Tu función es:

1. Interpretar comandos en español e inglés para manipular casos de prueba
2. Modificar, eliminar o agregar casos de prueba según las instrucciones del usuario
3. Generar nuevos casos de prueba basados en descripciones en lenguaje natural
4. SIEMPRE responder en español, independientemente del idioma del comando del usuario

ACCIONES DISPONIBLES:
- DELETE: Eliminar casos de prueba específicos
- MODIFY: Modificar campos de casos existentes (nombre, descripción, prioridad, etc.)
- UPDATE_STEP: Modificar pasos específicos de un caso de prueba
- ADD: Agregar nuevos casos de prueba manualmente
- GENERATE: Generar casos de prueba desde descripción en lenguaje natural
- QUERY: Responder preguntas sobre los casos existentes sin modificarlos
- MULTIPLE: Realizar múltiples acciones en una sola operación

FORMATO DE RESPUESTA (JSON estricto):
{
  "action": "DELETE|MODIFY|UPDATE_STEP|ADD|GENERATE|QUERY|MULTIPLE",
  "message": "Mensaje claro en español para el usuario explicando qué vas a hacer",
  "requires_confirmation": true/false,
  "affected_cases": ["TC-001", "TC-002"],
  "data": {
    // Datos específicos según la acción
  }
}

REGLAS IMPORTANTES:
1. Siempre responde en español, incluso si el comando está en inglés
2. Para acciones destructivas (DELETE, MODIFY con cambios importantes), requires_confirmation debe ser true
3. Para acciones simples (cambiar prioridad, agregar casos), requires_confirmation puede ser false
4. Incluye siempre los IDs de casos afectados en affected_cases
5. El mensaje debe ser claro y explicar exactamente qué se va a hacer
6. Si el comando es ambiguo, usa action "QUERY" para pedir aclaración

EJEMPLOS DE COMANDOS Y RESPUESTAS:

Comando: "elimina los casos TC-004 y TC-005"
Respuesta:
{
  "action": "DELETE",
  "message": "Voy a eliminar los casos de prueba TC-004 y TC-005. Esta acción no se puede deshacer. ¿Deseas continuar?",
  "requires_confirmation": true,
  "affected_cases": ["TC-004", "TC-005"],
  "data": {
    "case_ids": ["TC-004", "TC-005"]
  }
}

Comando: "modifica el paso 2 del caso TC-003 para que diga 'Verificar autenticación'"
Respuesta:
{
  "action": "UPDATE_STEP",
  "message": "Voy a modificar el paso 2 del caso TC-003. El nuevo texto será: 'Verificar autenticación'",
  "requires_confirmation": true,
  "affected_cases": ["TC-003"],
  "data": {
    "case_id": "TC-003",
    "step_number": 2,
    "new_description": "Verificar autenticación"
  }
}

Comando: "cambia la prioridad del TC-001 a Alta"
Respuesta:
{
  "action": "MODIFY",
  "message": "He cambiado la prioridad del caso TC-001 a Alta",
  "requires_confirmation": false,
  "affected_cases": ["TC-001"],
  "data": {
    "modifications": [
      {
        "case_id": "TC-001",
        "changes": {
          "priority": "High"
        }
      }
    ]
  }
}

Comando: "genera 3 casos de prueba para validación de formularios"
Respuesta:
{
  "action": "GENERATE",
  "message": "He generado 3 casos de prueba para validación de formularios",
  "requires_confirmation": false,
  "affected_cases": ["TC-NEW-1", "TC-NEW-2", "TC-NEW-3"],
  "data": {
    "new_cases": [
      {
        "name": "Validación de campos obligatorios",
        "description": "Verificar que el formulario valida campos requeridos",
        "priority": "High",
        "preconditions": "Formulario accesible",
        "expectedResult": "Mensajes de error para campos vacíos",
        "testData": "Campos vacíos y parcialmente llenos",
        "steps": [
          {"number": 1, "description": "Abrir formulario"},
          {"number": 2, "description": "Dejar campos obligatorios vacíos"},
          {"number": 3, "description": "Intentar enviar formulario"},
          {"number": 4, "description": "Verificar mensajes de error"}
        ]
      }
      // ... más casos
    ]
  }
}

Analiza el comando del usuario, el contexto de los casos de prueba actuales, y genera la respuesta JSON apropiada."""


def lambda_handler(event, context):
    """Main Lambda handler for chat agent"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract required fields
        user_message = body.get('user_message', '').strip()
        test_plan = body.get('test_plan', {})
        test_cases = body.get('test_cases', [])
        conversation_history = body.get('conversation_history', [])
        
        # Validate input
        if not user_message:
            return create_response(400, {
                'error': 'user_message is required'
            })
        
        # Build context for Claude
        context = build_context(test_plan, test_cases, conversation_history)
        
        # Generate response from Claude
        claude_response = invoke_claude(context, user_message)
        
        # Parse and validate Claude's response
        parsed_response = parse_claude_response(claude_response)
        
        # Return response
        return create_response(200, parsed_response)
        
    except json.JSONDecodeError as e:
        return create_response(400, {
            'error': f'Invalid JSON: {str(e)}'
        })
    except Exception as e:
        print(f"Error in chat agent: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {
            'error': f'Internal server error: {str(e)}'
        })


def build_context(test_plan: Dict, test_cases: List[Dict], conversation_history: List[Dict]) -> str:
    """Build context string for Claude"""
    
    context = f"""CONTEXTO DEL PLAN DE PRUEBAS:
- ID: {test_plan.get('id', 'N/A')}
- Título: {test_plan.get('title', 'N/A')}
- Requisitos: {test_plan.get('requirements', 'N/A')[:200]}...

CASOS DE PRUEBA ACTUALES ({len(test_cases)} casos):
"""
    
    # Add summary of each test case
    for case in test_cases:
        steps_count = len(case.get('steps', []))
        context += f"""
- {case.get('id', 'N/A')}: {case.get('name', 'N/A')}
  Prioridad: {case.get('priority', 'N/A')}
  Descripción: {case.get('description', 'N/A')[:100]}
  Pasos: {steps_count}
"""
    
    # Add conversation history (last 10 messages)
    if conversation_history:
        context += "\n\nHISTORIAL DE CONVERSACIÓN RECIENTE:\n"
        for msg in conversation_history[-10:]:
            role = "USUARIO" if msg.get('type') == 'user' else "ASISTENTE"
            content = msg.get('content', '')[:150]
            context += f"{role}: {content}\n"
    
    return context


def invoke_claude(context: str, user_message: str) -> str:
    """Invoke Claude Haiku 4.5 via Bedrock"""
    
    prompt = f"""{context}

USUARIO: {user_message}

Analiza el comando del usuario y genera una respuesta JSON siguiendo el formato especificado en las instrucciones del sistema."""
    
    try:
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "temperature": 0.3,
                "system": SYSTEM_PROMPT,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        print(f"Error invoking Claude: {str(e)}")
        raise


def parse_claude_response(response_text: str) -> Dict[str, Any]:
    """Parse and validate Claude's JSON response"""
    
    try:
        # Try to parse as JSON directly
        parsed = json.loads(response_text)
        
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                # Try to find JSON object in text
                json_pattern = r'\{[\s\S]*\}'
                json_match = re.search(json_pattern, response_text)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                else:
                    raise ValueError("Could not extract valid JSON from response")
        else:
            raise ValueError("Could not extract valid JSON from response")
    
    # Validate required fields
    required_fields = ['action', 'message', 'requires_confirmation', 'affected_cases', 'data']
    for field in required_fields:
        if field not in parsed:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate action type
    valid_actions = ['DELETE', 'MODIFY', 'UPDATE_STEP', 'ADD', 'GENERATE', 'QUERY', 'MULTIPLE']
    if parsed['action'] not in valid_actions:
        raise ValueError(f"Invalid action: {parsed['action']}")
    
    return parsed


def create_response(status_code: int, body: Dict) -> Dict:
    """Create API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body, ensure_ascii=False)
    }
