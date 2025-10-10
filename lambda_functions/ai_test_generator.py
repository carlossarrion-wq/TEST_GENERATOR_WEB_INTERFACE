"""
AI Test Generator Lambda Function
Generates test plans and test cases using AI based on requirements
"""

import json
import boto3
import os
from db_utils import (
    DatabaseConnection, create_response, create_error_response,
    validate_required_fields, generate_plan_id, generate_case_id,
    get_test_plan_by_plan_id, handle_cors_preflight
)

# Initialize AWS Bedrock clients
try:
    bedrock_client = boto3.client('bedrock-runtime', region_name='eu-west-1')
    bedrock_agent = boto3.client('bedrock-agent-runtime', region_name='eu-west-1')
    BEDROCK_AVAILABLE = True
except Exception as e:
    print(f"Bedrock not available: {e}")
    BEDROCK_AVAILABLE = False

# Configuration
knowledge_base_id = os.environ.get('KNOWLEDGE_BASE_ID')
# Usar Inference Profile para Claude Sonnet 4
model_id = os.environ.get('BEDROCK_MODEL_ID', 'arn:aws:bedrock:eu-west-1:701055077130:inference-profile/eu.anthropic.claude-sonnet-4-20250514-v1:0')

def lambda_handler(event, context):
    """Main Lambda handler for AI test generation"""
    
    # Handle CORS preflight requests
    if event['httpMethod'] == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        method = event['httpMethod']
        path_parameters = event.get('pathParameters') or {}
        
        if method != 'POST':
            return create_error_response(405, f"Method {method} not allowed", "MethodNotAllowed")
        
        body = json.loads(event['body']) if event['body'] else {}
        
        # Route based on action
        action = path_parameters.get('action', body.get('action'))
        
        if action == 'generate-plan':
            return generate_test_plan_with_ai(body)
        elif action == 'generate-cases':
            if 'plan_id' not in path_parameters:
                return create_error_response(400, "Plan ID is required for generating cases", "ValidationError")
            return generate_test_cases_with_ai(path_parameters['plan_id'], body)
        elif action == 'improve-cases':
            if 'plan_id' not in path_parameters:
                return create_error_response(400, "Plan ID is required for improving cases", "ValidationError")
            return improve_test_cases_with_ai(path_parameters['plan_id'], body)
        elif action == 'chat':
            if 'plan_id' not in path_parameters:
                return create_error_response(400, "Plan ID is required for chat", "ValidationError")
            return chat_with_ai(path_parameters['plan_id'], body)
        else:
            return create_error_response(400, "Invalid action. Supported actions: generate-plan, generate-cases, improve-cases, chat", "ValidationError")
    
    except json.JSONDecodeError:
        return create_error_response(400, "Invalid JSON in request body", "JSONDecodeError")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return create_error_response(500, "Internal server error", "InternalServerError")

def generate_test_plan_with_ai(data):
    """Generate a complete test plan with AI based on requirements"""
    try:
        # Validate required fields
        required_fields = ['title', 'requirements']
        validate_required_fields(data, required_fields)
        
        if not BEDROCK_AVAILABLE:
            return create_error_response(503, "AI service is not available", "ServiceUnavailable")
        
        # Extract parameters
        title = data['title']
        requirements = data['requirements']
        reference = data.get('reference', '')
        coverage_percentage = data.get('coverage_percentage', 80)
        min_test_cases = data.get('min_test_cases', 5)
        max_test_cases = data.get('max_test_cases', 15)
        selected_test_types = data.get('selected_test_types', ['unit', 'integration', 'functional'])
        
        # Generate test plan with AI
        ai_response = call_bedrock_for_test_plan(
            title, requirements, coverage_percentage, 
            min_test_cases, max_test_cases, selected_test_types
        )
        
        if not ai_response:
            return create_error_response(500, "Failed to generate test plan with AI", "AIGenerationError")
        
        # Parse AI response
        try:
            ai_plan = json.loads(ai_response)
        except json.JSONDecodeError:
            return create_error_response(500, "Invalid AI response format", "AIParsingError")
        
        # Create test plan in database
        plan_id = generate_plan_id()
        
        with DatabaseConnection() as cursor:
            # Insert test plan
            cursor.execute("""
                INSERT INTO test_plans (
                    plan_id, title, reference, requirements, coverage_percentage,
                    min_test_cases, max_test_cases, selected_test_types, status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                plan_id, title, reference, requirements,
                coverage_percentage, min_test_cases, max_test_cases,
                json.dumps(selected_test_types), 'draft'
            ))
            
            test_plan_internal_id = cursor.lastrowid
            
            # Insert generated test cases
            created_cases = []
            test_cases = ai_plan.get('test_cases', [])
            
            for i, test_case in enumerate(test_cases[:max_test_cases], 1):
                case_id = f"TC-{str(i).zfill(3)}"
                
                cursor.execute("""
                    INSERT INTO test_cases (
                        test_plan_id, case_id, name, description, priority,
                        preconditions, expected_result, test_data, case_order
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    test_plan_internal_id, case_id,
                    test_case.get('name', f'Test Case {i}'),
                    test_case.get('description', ''),
                    test_case.get('priority', 'Medium'),
                    test_case.get('preconditions', ''),
                    test_case.get('expected_result', ''),
                    test_case.get('test_data', ''),
                    i
                ))
                
                test_case_internal_id = cursor.lastrowid
                
                # Insert test steps if provided
                steps = test_case.get('steps', [])
                for step_num, step_desc in enumerate(steps, 1):
                    cursor.execute("""
                        INSERT INTO test_steps (test_case_id, step_number, description)
                        VALUES (%s, %s, %s)
                    """, (test_case_internal_id, step_num, step_desc))
                
                created_cases.append({
                    'case_id': case_id,
                    'name': test_case.get('name', f'Test Case {i}'),
                    'steps_count': len(steps)
                })
            
            # Add initial chat message
            cursor.execute("""
                INSERT INTO chat_messages (
                    test_plan_id, message_type, content, message_order
                ) VALUES (
                    %s, %s, %s, %s
                )
            """, (
                test_plan_internal_id, 'assistant',
                f"I've generated a comprehensive test plan '{title}' with {len(created_cases)} test cases based on your requirements. The test cases cover {', '.join(selected_test_types)} testing approaches with {coverage_percentage}% coverage target.",
                1
            ))
            
            return create_response(201, {
                'message': 'Test plan generated successfully with AI',
                'plan_id': plan_id,
                'test_cases_created': len(created_cases),
                'ai_summary': ai_plan.get('summary', 'Test plan generated successfully'),
                'created_cases': created_cases
            })
    
    except ValueError as e:
        return create_error_response(400, str(e), "ValidationError")
    except Exception as e:
        print(f"Error generating test plan with AI: {str(e)}")
        return create_error_response(500, "Error generating test plan with AI", "AIGenerationError")

def generate_test_cases_with_ai(plan_id, data):
    """Generate additional test cases for an existing test plan"""
    try:
        # Get test plan
        test_plan_internal_id = get_test_plan_by_plan_id(plan_id)
        if not test_plan_internal_id:
            return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
        
        if not BEDROCK_AVAILABLE:
            return create_error_response(503, "AI service is not available", "ServiceUnavailable")
        
        # Get additional requirements or focus areas
        additional_requirements = data.get('additional_requirements', '')
        focus_areas = data.get('focus_areas', [])
        count = min(data.get('count', 3), 10)  # Limit to 10 new cases
        
        with DatabaseConnection() as cursor:
            # Get existing test plan details
            cursor.execute("""
                SELECT title, requirements, selected_test_types, coverage_percentage
                FROM test_plans 
                WHERE plan_id = %s AND is_deleted = FALSE
            """, (plan_id,))
            
            plan_details = cursor.fetchone()
            if not plan_details:
                return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
            
            # Get existing test cases for context
            cursor.execute("""
                SELECT name, description FROM test_cases 
                WHERE test_plan_id = %s AND is_deleted = FALSE
                ORDER BY case_order
            """, (test_plan_internal_id,))
            
            existing_cases = cursor.fetchall()
            
            # Generate new test cases with AI
            ai_response = call_bedrock_for_additional_cases(
                plan_details, existing_cases, additional_requirements, 
                focus_areas, count
            )
            
            if not ai_response:
                return create_error_response(500, "Failed to generate test cases with AI", "AIGenerationError")
            
            # Parse AI response
            try:
                ai_cases = json.loads(ai_response)
            except json.JSONDecodeError:
                return create_error_response(500, "Invalid AI response format", "AIParsingError")
            
            # Get next case order
            cursor.execute("""
                SELECT COALESCE(MAX(case_order), 0) as max_order
                FROM test_cases 
                WHERE test_plan_id = %s AND is_deleted = FALSE
            """, (test_plan_internal_id,))
            
            result = cursor.fetchone()
            next_order = result['max_order'] + 1 if result else 1
            
            # Insert new test cases
            created_cases = []
            test_cases = ai_cases.get('test_cases', [])
            
            for i, test_case in enumerate(test_cases, next_order):
                case_id = generate_case_id(plan_id)
                
                cursor.execute("""
                    INSERT INTO test_cases (
                        test_plan_id, case_id, name, description, priority,
                        preconditions, expected_result, test_data, case_order
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    test_plan_internal_id, case_id,
                    test_case.get('name', f'Generated Test Case {i}'),
                    test_case.get('description', ''),
                    test_case.get('priority', 'Medium'),
                    test_case.get('preconditions', ''),
                    test_case.get('expected_result', ''),
                    test_case.get('test_data', ''),
                    i
                ))
                
                test_case_internal_id = cursor.lastrowid
                
                # Insert test steps
                steps = test_case.get('steps', [])
                for step_num, step_desc in enumerate(steps, 1):
                    cursor.execute("""
                        INSERT INTO test_steps (test_case_id, step_number, description)
                        VALUES (%s, %s, %s)
                    """, (test_case_internal_id, step_num, step_desc))
                
                created_cases.append({
                    'case_id': case_id,
                    'name': test_case.get('name', f'Generated Test Case {i}'),
                    'steps_count': len(steps)
                })
            
            return create_response(201, {
                'message': f'Generated {len(created_cases)} additional test cases with AI',
                'plan_id': plan_id,
                'created_cases': created_cases
            })
    
    except Exception as e:
        print(f"Error generating test cases for plan {plan_id}: {str(e)}")
        return create_error_response(500, "Error generating test cases with AI", "AIGenerationError")

def chat_with_ai(plan_id, data):
    """Chat with AI about the test plan"""
    try:
        # Validate required fields
        required_fields = ['message']
        validate_required_fields(data, required_fields)
        
        if not BEDROCK_AVAILABLE:
            return create_error_response(503, "AI service is not available", "ServiceUnavailable")
        
        user_message = data['message'].strip()
        if not user_message:
            return create_error_response(400, "Message cannot be empty", "ValidationError")
        
        # Get test plan internal ID
        test_plan_internal_id = get_test_plan_by_plan_id(plan_id)
        if not test_plan_internal_id:
            return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
        
        with DatabaseConnection() as cursor:
            # Get test plan context
            cursor.execute("""
                SELECT tp.title, tp.requirements, tp.selected_test_types,
                       COUNT(tc.id) as test_cases_count
                FROM test_plans tp
                LEFT JOIN test_cases tc ON tp.id = tc.test_plan_id AND tc.is_deleted = FALSE
                WHERE tp.plan_id = %s AND tp.is_deleted = FALSE
                GROUP BY tp.id
            """, (plan_id,))
            
            plan_context = cursor.fetchone()
            
            # Get recent chat history for context
            cursor.execute("""
                SELECT message_type, content
                FROM chat_messages
                WHERE test_plan_id = %s
                ORDER BY message_order DESC
                LIMIT 6
            """, (test_plan_internal_id,))
            
            recent_messages = cursor.fetchall()
            recent_messages.reverse()  # Chronological order
            
            # Generate AI response
            ai_response = call_bedrock_for_chat(plan_context, recent_messages, user_message)
            
            if not ai_response:
                return create_error_response(500, "Failed to get AI response", "AIGenerationError")
            
            # Get next message order
            cursor.execute("""
                SELECT COALESCE(MAX(message_order), 0) as last_order
                FROM chat_messages 
                WHERE test_plan_id = %s
            """, (test_plan_internal_id,))
            
            result = cursor.fetchone()
            last_order = result['last_order'] if result else 0
            
            # Save both messages
            cursor.execute("""
                INSERT INTO chat_messages (
                    test_plan_id, message_type, content, message_order
                ) VALUES (
                    %s, %s, %s, %s
                )
            """, (test_plan_internal_id, 'user', user_message, last_order + 1))
            
            cursor.execute("""
                INSERT INTO chat_messages (
                    test_plan_id, message_type, content, message_order
                ) VALUES (
                    %s, %s, %s, %s
                )
            """, (test_plan_internal_id, 'assistant', ai_response, last_order + 2))
            
            return create_response(200, {
                'plan_id': plan_id,
                'user_message': user_message,
                'ai_response': ai_response
            })
    
    except ValueError as e:
        return create_error_response(400, str(e), "ValidationError")
    except Exception as e:
        print(f"Error in AI chat for plan {plan_id}: {str(e)}")
        return create_error_response(500, "Error in AI chat", "AIChatError")

def call_bedrock_for_test_plan(title, requirements, coverage, min_cases, max_cases, test_types):
    """Call AWS Bedrock with Knowledge Base to generate a test plan using Claude Sonnet 4"""
    try:
        print(f"Using model ID: {model_id}")
        
        # Build context from Knowledge Base
        context_results = []
        if knowledge_base_id:
            try:
                search_query = f"test plan {' '.join(test_types)} {title} {requirements[:100]}"
                
                kb_response = bedrock_agent.retrieve(
                    knowledgeBaseId=knowledge_base_id,
                    retrievalQuery={'text': search_query},
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {
                            'numberOfResults': 5,
                            'overrideSearchType': 'HYBRID'
                        }
                    }
                )
                
                if 'retrievalResults' in kb_response:
                    for result in kb_response['retrievalResults']:
                        context_results.append({
                            'content': result.get('content', {}).get('text', ''),
                            'score': result.get('score', 0.0)
                        })
                
                print(f"Retrieved {len(context_results)} context results from Knowledge Base")
                
            except Exception as e:
                print(f"Knowledge Base retrieval failed: {str(e)}")
        
        # Build context from Knowledge Base results
        context_text = "\n\n".join([
            f"{result['content'][:300]}..."
            for result in context_results[:3]
        ])
        
        # Optimized prompts for Claude Sonnet 4
        system_prompt = "Genera casos de prueba profesionales en formato JSON. Devuelve únicamente JSON válido sin explicaciones adicionales."
        
        target_cases = (min_cases + max_cases) // 2
        
        user_prompt = f"""Genera entre {min_cases} y {max_cases} casos de prueba para:

PROYECTO: {title}
REQUERIMIENTOS: {requirements}
COBERTURA OBJETIVO: {coverage}%
TIPOS DE TESTING: {', '.join(test_types)}
NÚMERO DE CASOS: Entre {min_cases} y {max_cases} casos (objetivo: {target_cases})

{f"CONTEXTO DE KNOWLEDGE BASE:\\n{context_text}" if context_text else ""}

Devuelve JSON con esta estructura exacta:
{{
  "summary": "Resumen breve del plan de pruebas",
  "test_cases": [
    {{
      "name": "Nombre del caso de prueba",
      "description": "Descripción detallada",
      "priority": "High|Medium|Low",
      "preconditions": "Precondiciones necesarias",
      "expected_result": "Resultado esperado",
      "test_data": "Datos de prueba necesarios",
      "steps": ["Paso 1", "Paso 2", "Paso 3"]
    }}
  ]
}}"""
        
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "temperature": 0.1,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text']
        
        # Extract JSON from response using robust parsing
        return extract_json_from_response(content)
        
    except Exception as e:
        print(f"Error calling Bedrock for test plan: {str(e)}")
        return None

def call_bedrock_for_additional_cases(plan_details, existing_cases, additional_req, focus_areas, count):
    """Call AWS Bedrock with Knowledge Base to generate additional test cases using Claude Sonnet 4"""
    try:
        existing_names = [case['name'] for case in existing_cases]
        
        # Build context from Knowledge Base if available
        context_results = []
        if knowledge_base_id:
            try:
                search_query = f"test cases {' '.join(focus_areas)} {plan_details['title']}"
                
                kb_response = bedrock_agent.retrieve(
                    knowledgeBaseId=knowledge_base_id,
                    retrievalQuery={'text': search_query},
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {
                            'numberOfResults': 3,
                            'overrideSearchType': 'HYBRID'
                        }
                    }
                )
                
                if 'retrievalResults' in kb_response:
                    for result in kb_response['retrievalResults']:
                        context_results.append({
                            'content': result.get('content', {}).get('text', ''),
                            'score': result.get('score', 0.0)
                        })
                
            except Exception as e:
                print(f"Knowledge Base retrieval failed: {str(e)}")
        
        context_text = "\n\n".join([
            f"{result['content'][:200]}..."
            for result in context_results[:2]
        ])
        
        system_prompt = "Genera casos de prueba adicionales en formato JSON. Devuelve únicamente JSON válido sin explicaciones."
        
        user_prompt = f"""Genera {count} casos de prueba adicionales para:

PLAN: {plan_details['title']}
REQUERIMIENTOS ORIGINALES: {plan_details['requirements']}
REQUERIMIENTOS ADICIONALES: {additional_req}
ÁREAS DE ENFOQUE: {', '.join(focus_areas)}

CASOS EXISTENTES (NO DUPLICAR):
{', '.join(existing_names[:10])}

{f"CONTEXTO DE KNOWLEDGE BASE:\\n{context_text}" if context_text else ""}

Devuelve JSON:
{{
  "test_cases": [
    {{
      "name": "Nombre del caso de prueba",
      "description": "Descripción detallada",
      "priority": "High|Medium|Low",
      "preconditions": "Precondiciones",
      "expected_result": "Resultado esperado",
      "test_data": "Datos de prueba",
      "steps": ["Paso 1", "Paso 2", "Paso 3"]
    }}
  ]
}}"""
        
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 3000,
                "temperature": 0.1,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text']
        
        return extract_json_from_response(content)
        
    except Exception as e:
        print(f"Error calling Bedrock for additional cases: {str(e)}")
        return None

def improve_test_cases_with_ai(plan_id, data):
    """Improve existing test cases with AI suggestions"""
    try:
        # Get test plan internal ID
        test_plan_internal_id = get_test_plan_by_plan_id(plan_id)
        if not test_plan_internal_id:
            return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
        
        if not BEDROCK_AVAILABLE:
            return create_error_response(503, "AI service is not available", "ServiceUnavailable")
        
        improvement_focus = data.get('focus', 'general')  # general, coverage, edge-cases, etc.
        
        with DatabaseConnection() as cursor:
            # Get test plan and cases
            cursor.execute("""
                SELECT tp.title, tp.requirements, tc.case_id, tc.name, tc.description,
                       tc.priority, tc.preconditions, tc.expected_result
                FROM test_plans tp
                JOIN test_cases tc ON tp.id = tc.test_plan_id
                WHERE tp.plan_id = %s AND tp.is_deleted = FALSE AND tc.is_deleted = FALSE
                ORDER BY tc.case_order
            """, (plan_id,))
            
            cases = cursor.fetchall()
            
            if not cases:
                return create_error_response(404, "No test cases found for improvement", "NotFound")
            
            # Generate improvement suggestions
            suggestions = call_bedrock_for_improvements(cases, improvement_focus)
            
            if not suggestions:
                return create_error_response(500, "Failed to generate improvements", "AIGenerationError")
            
            return create_response(200, {
                'plan_id': plan_id,
                'improvement_suggestions': suggestions,
                'cases_analyzed': len(cases)
            })
    
    except Exception as e:
        print(f"Error improving test cases for plan {plan_id}: {str(e)}")
        return create_error_response(500, "Error improving test cases with AI", "AIImprovementError")

def call_bedrock_for_chat(plan_context, chat_history, user_message):
    """Call AWS Bedrock for chat conversation using Claude Sonnet 4"""
    try:
        history_text = ""
        for msg in chat_history[-4:]:  # Last 4 messages for context
            history_text += f"{msg['message_type']}: {msg['content']}\n"
        
        system_prompt = "Eres un asistente AI especializado en testing y planes de prueba. Proporciona respuestas útiles, conversacionales y enfocadas en mejores prácticas de testing."
        
        user_prompt = f"""Contexto del Test Plan:
- Título: {plan_context['title']}
- Requerimientos: {plan_context['requirements']}
- Casos de Prueba: {plan_context['test_cases_count']}

Conversación Reciente:
{history_text}

Usuario: {user_message}

Proporciona una respuesta útil e informativa sobre el test plan, estrategias de testing, o responde cualquier pregunta del usuario."""
        
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0.1,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        print(f"Error calling Bedrock for chat: {str(e)}")
        return "Lo siento, tengo problemas para generar una respuesta ahora mismo. Por favor intenta de nuevo más tarde."

def call_bedrock_for_improvements(cases, focus):
    """Call AWS Bedrock to get improvement suggestions using Claude Sonnet 4"""
    try:
        cases_text = ""
        for case in cases:
            cases_text += f"Case ID: {case['case_id']}\nName: {case['name']}\nDescription: {case['description']}\n\n"
        
        system_prompt = "Analiza casos de prueba y proporciona sugerencias de mejora específicas y accionables."
        
        user_prompt = f"""Analiza los siguientes casos de prueba con enfoque en {focus}:

{cases_text}

Proporciona sugerencias específicas y accionables para mejorar estos casos de prueba.
Enfócate en: cobertura de testing, casos edge, claridad, completitud y mejores prácticas.

Devuelve sugerencias en formato estructurado que ayude a mejorar la calidad general del test suite."""
        
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "temperature": 0.1,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        print(f"Error calling Bedrock for improvements: {str(e)}")
        return None

def extract_json_from_response(content: str):
    """Extract JSON from Claude's response using robust parsing"""
    try:
        # First try direct JSON parsing
        return json.loads(content)
    except json.JSONDecodeError:
        import re
        
        # Try to find JSON in code blocks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON pattern in the text
        json_pattern = r'{[\s\S]*}'
        json_match = re.search(json_pattern, content)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # If all fails, return empty structure
        print(f"Could not extract JSON from response: {content[:200]}...")
        return {"test_cases": []}
