import json
import boto3
import os
import time
from datetime import datetime
from db_utils import (
    DatabaseConnection, create_response, create_error_response,
    validate_required_fields, generate_plan_id, generate_case_id,
    get_test_plan_by_plan_id, handle_cors_preflight
)

# Import LangChain Agent
try:
    from test_plan_agent import CompleteLangChainAgent
    LANGCHAIN_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ LangChain Agent not available: {e}")
    LANGCHAIN_AGENT_AVAILABLE = False

bedrock_client = boto3.client('bedrock-runtime', region_name='eu-west-1')
bedrock_agent = boto3.client('bedrock-agent-runtime', region_name='eu-west-1')

KNOWLEDGE_BASE_ID = os.environ.get('KNOWLEDGE_BASE_ID', 'VH6SRH9ZNO')
MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'eu.anthropic.claude-haiku-4-5-20251001-v1:0')

def lambda_handler(event, context):
    if event['httpMethod'] == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        method = event['httpMethod']
        path_parameters = event.get('pathParameters') or {}
        
        if method != 'POST':
            return create_error_response(405, f"Method {method} not allowed", "MethodNotAllowed")
        
        body = json.loads(event['body']) if event['body'] else {}
        action = path_parameters.get('action', body.get('action'))
        
        if action == 'generate-plan':
            return generate_test_plan_with_langchain(body)
        elif action == 'chat':
            if 'plan_id' not in path_parameters:
                return create_error_response(400, "Plan ID required", "ValidationError")
            return chat_with_ai_optimized(path_parameters['plan_id'], body)
        else:
            return create_error_response(400, "Invalid action", "ValidationError")
    
    except json.JSONDecodeError:
        return create_error_response(400, "Invalid JSON", "JSONDecodeError")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_error_response(500, "Internal server error", "InternalServerError")

def generate_test_plan_with_langchain(data):
    """Generate test plan using complete LangChain agent with all specialized tools"""
    try:
        start_time = time.time()
        
        validate_required_fields(data, ['title', 'requirements'])
        
        title = data['title']
        requirements = data['requirements']
        reference = data.get('reference', '')
        coverage_percentage = data.get('coverage_percentage', 80)
        min_test_cases = data.get('min_test_cases', 5)
        max_test_cases = data.get('max_test_cases', 15)
        selected_test_types = data.get('selected_test_types', ['functional', 'negative'])
        user_team = data.get('user_team')  # Extract user team for OpenSearch routing
        
        if not LANGCHAIN_AGENT_AVAILABLE:
            print("⚠️ LangChain Agent not available, using fallback")
            return generate_test_plan_fallback(data)
        
        # Initialize LangChain Agent with all specialized tools and team context
        print(f"🚀 Initializing LangChain Agent with Haiku 4.5 and specialized tools (Team: {user_team})")
        agent = CompleteLangChainAgent(region='eu-west-1', user_team=user_team)
        
        # Prepare input for agent
        agent_input = {
            'title': title,
            'requirements': requirements,
            'coverage_percentage': coverage_percentage,
            'min_test_cases': min_test_cases,
            'max_test_cases': max_test_cases,
            'selected_test_types': selected_test_types
        }
        
        # Generate test plan using LangChain workflow
        print("🧠 Generating test plan with LangChain specialized workflow")
        agent_result = agent.generate_test_plan(agent_input)
        
        # Extract test cases from agent result
        if not agent_result.get('success'):
            return create_error_response(500, "Agent failed to generate test plan", "AgentError")
        
        agent_data = agent_result.get('data', {})
        test_cases = agent_data.get('test_cases', [])
        
        if not test_cases:
            return create_error_response(500, "No test cases generated", "AIGenerationError")
        
        # Save to database
        print("💾 Saving to database")
        plan_id = generate_plan_id()
        
        with DatabaseConnection() as cursor:
            cursor.execute("""
                INSERT INTO test_plans (
                    plan_id, title, reference, requirements, coverage_percentage,
                    min_test_cases, max_test_cases, selected_test_types, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                plan_id, title, reference, requirements,
                coverage_percentage, min_test_cases, max_test_cases,
                json.dumps(selected_test_types) if isinstance(selected_test_types, list) else selected_test_types, 'draft'
            ))
            
            test_plan_internal_id = cursor.lastrowid
            created_cases = []
            
            for i, test_case in enumerate(test_cases[:max_test_cases], 1):
                case_id = f"TC-{str(i).zfill(3)}"
                
                cursor.execute("""
                    INSERT INTO test_cases (
                        test_plan_id, case_id, name, description, priority,
                        preconditions, expected_result, test_data, case_order
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                
                steps = test_case.get('steps', [])
                steps_data = []
                for step_num, step_desc in enumerate(steps, 1):
                    cursor.execute("""
                        INSERT INTO test_steps (test_case_id, step_number, description)
                        VALUES (%s, %s, %s)
                    """, (test_case_internal_id, step_num, step_desc))
                    steps_data.append({
                        'step_number': step_num,
                        'description': step_desc
                    })
                
                created_cases.append({
                    'id': case_id,
                    'name': test_case.get('name', f'Test Case {i}'),
                    'description': test_case.get('description', ''),
                    'priority': test_case.get('priority', 'Medium'),
                    'preconditions': test_case.get('preconditions', ''),
                    'expectedResult': test_case.get('expected_result', ''),
                    'testData': test_case.get('test_data', ''),
                    'steps': steps_data
                })
            
            # Save initial chat message with team info
            team_info = f" (Equipo: {user_team})" if user_team else ""
            cursor.execute("""
                INSERT INTO chat_messages (
                    test_plan_id, message_type, content, message_order
                ) VALUES (%s, %s, %s, %s)
            """, (
                test_plan_internal_id, 'assistant',
                f"Plan de pruebas '{title}' generado con LangChain + Haiku 4.5{team_info}: {len(created_cases)} casos de alta calidad usando workflow especializado con 5 herramientas (Requirements Analyzer, Knowledge Base Retriever con OpenSearch, Test Case Generator, Coverage Calculator, Quality Validator).",
                1
            ))
            
            execution_time = time.time() - start_time
            
            # Extract quality metrics from agent result
            quality_metrics = agent_data.get('quality_metrics', {})
            coverage_analysis = agent_data.get('coverage_analysis', {})
            
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
                'opensearch_info': agent_data.get('opensearch_info', {}),
                'test_cases': created_cases
            })
    
    except ValueError as e:
        return create_error_response(400, str(e), "ValidationError")
    except Exception as e:
        print(f"Error generating test plan: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_error_response(500, f"Error generating test plan: {str(e)}", "AIGenerationError")

def generate_test_plan_fallback(data):
    """Fallback method if LangChain agent is not available"""
    try:
        print("⚠️ Using fallback method (direct Bedrock)")
        
        start_time = time.time()
        
        title = data['title']
        requirements = data['requirements']
        coverage_percentage = data.get('coverage_percentage', 80)
        min_test_cases = data.get('min_test_cases', 5)
        max_test_cases = data.get('max_test_cases', 15)
        selected_test_types = data.get('selected_test_types', ['functional', 'negative'])
        
        target_cases = (min_test_cases + max_test_cases) // 2
        
        system_prompt = """Eres un experto en testing de software. Genera casos de prueba de alta calidad."""
        
        user_prompt = f"""Genera {target_cases} casos de prueba para:

PROYECTO: {title}
REQUERIMIENTOS: {requirements}
COBERTURA: {coverage_percentage}%
TIPOS: {', '.join(selected_test_types)}

Devuelve JSON:
{{
  "test_cases": [
    {{
      "name": "nombre",
      "description": "descripción",
      "priority": "High|Medium|Low",
      "preconditions": "precondiciones",
      "expected_result": "resultado esperado",
      "test_data": "datos",
      "steps": ["paso 1", "paso 2"]
    }}
  ]
}}"""
        
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
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
        ai_plan = extract_json_from_response(content)
        
        # Save to database (same logic as above)
        plan_id = generate_plan_id()
        
        with DatabaseConnection() as cursor:
            cursor.execute("""
                INSERT INTO test_plans (
                    plan_id, title, reference, requirements, coverage_percentage,
                    min_test_cases, max_test_cases, selected_test_types, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                plan_id, title, data.get('reference', ''), requirements,
                coverage_percentage, min_test_cases, max_test_cases,
                json.dumps(selected_test_types), 'draft'
            ))
            
            test_plan_internal_id = cursor.lastrowid
            created_cases = []
            
            for i, test_case in enumerate(ai_plan.get('test_cases', [])[:max_test_cases], 1):
                case_id = f"TC-{str(i).zfill(3)}"
                
                cursor.execute("""
                    INSERT INTO test_cases (
                        test_plan_id, case_id, name, description, priority,
                        preconditions, expected_result, test_data, case_order
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                
                steps = test_case.get('steps', [])
                for step_num, step_desc in enumerate(steps, 1):
                    cursor.execute("""
                        INSERT INTO test_steps (test_case_id, step_number, description)
                        VALUES (%s, %s, %s)
                    """, (test_case_internal_id, step_num, step_desc))
                
                created_cases.append({
                    'case_id': case_id,
                    'name': test_case.get('name'),
                    'steps_count': len(steps)
                })
            
            cursor.execute("""
                INSERT INTO chat_messages (
                    test_plan_id, message_type, content, message_order
                ) VALUES (%s, %s, %s, %s)
            """, (test_plan_internal_id, 'assistant',
                  f"Plan generado (fallback): {len(created_cases)} casos", 1))
            
            execution_time = time.time() - start_time
            
            return create_response(201, {
                'message': 'Test plan generated (fallback mode)',
                'plan_id': plan_id,
                'test_cases_created': len(created_cases),
                'execution_time_seconds': round(execution_time, 2),
                'model_used': 'haiku-4.5-fallback',
                'created_cases': created_cases
            })
    
    except Exception as e:
        print(f"Fallback error: {str(e)}")
        return create_error_response(500, str(e), "FallbackError")

def chat_with_ai_optimized(plan_id, data):
    """Chat with AI using Haiku 4.5"""
    try:
        validate_required_fields(data, ['message'])
        
        user_message = data['message'].strip()
        if not user_message:
            return create_error_response(400, "Message cannot be empty", "ValidationError")
        
        test_plan_internal_id = get_test_plan_by_plan_id(plan_id)
        if not test_plan_internal_id:
            return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
        
        with DatabaseConnection() as cursor:
            cursor.execute("""
                SELECT tp.title, tp.requirements, tp.selected_test_types,
                       COUNT(tc.id) as test_cases_count
                FROM test_plans tp
                LEFT JOIN test_cases tc ON tp.id = tc.test_plan_id AND tc.is_deleted = FALSE
                WHERE tp.plan_id = %s AND tp.is_deleted = FALSE
                GROUP BY tp.id
            """, (plan_id,))
            
            plan_context = cursor.fetchone()
            
            cursor.execute("""
                SELECT message_type, content
                FROM chat_messages
                WHERE test_plan_id = %s
                ORDER BY message_order DESC
                LIMIT 4
            """, (test_plan_internal_id,))
            
            recent_messages = cursor.fetchall()
            recent_messages.reverse()
            
            ai_response = generate_chat_response_optimized(plan_context, recent_messages, user_message)
            
            if not ai_response:
                return create_error_response(500, "Failed to get AI response", "AIGenerationError")
            
            cursor.execute("""
                SELECT COALESCE(MAX(message_order), 0) as last_order
                FROM chat_messages 
                WHERE test_plan_id = %s
            """, (test_plan_internal_id,))
            
            result = cursor.fetchone()
            last_order = result['last_order'] if result else 0
            
            cursor.execute("""
                INSERT INTO chat_messages (
                    test_plan_id, message_type, content, message_order
                ) VALUES (%s, %s, %s, %s)
            """, (test_plan_internal_id, 'user', user_message, last_order + 1))
            
            cursor.execute("""
                INSERT INTO chat_messages (
                    test_plan_id, message_type, content, message_order
                ) VALUES (%s, %s, %s, %s)
            """, (test_plan_internal_id, 'assistant', ai_response, last_order + 2))
            
            return create_response(200, {
                'plan_id': plan_id,
                'user_message': user_message,
                'ai_response': ai_response
            })
    
    except ValueError as e:
        return create_error_response(400, str(e), "ValidationError")
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        return create_error_response(500, "Error in AI chat", "AIChatError")

def generate_chat_response_optimized(plan_context, chat_history, user_message):
    """Generate chat response using Haiku 4.5"""
    try:
        history_text = ""
        for msg in chat_history[-3:]:
            history_text += f"{msg['message_type']}: {msg['content'][:200]}\n"
        
        system_prompt = "Eres un asistente experto en testing. Proporciona respuestas útiles y concisas sobre planes de prueba."
        
        user_prompt = f"""Contexto del Plan:
- Título: {plan_context['title']}
- Casos de Prueba: {plan_context['test_cases_count']}

Conversación Reciente:
{history_text}

Usuario: {user_message}

Responde de forma útil y concisa."""
        
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
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
        print(f"Chat response error: {str(e)}")
        return "Lo siento, tengo problemas para generar una respuesta. Intenta de nuevo."

def extract_json_from_response(content):
    """Extract JSON from AI response"""
    if isinstance(content, dict):
        return content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        import re
        
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        json_pattern = r'{[\s\S]*}'
        json_match = re.search(json_pattern, content)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        print(f"Could not extract JSON from: {content[:200]}...")
        return {"test_cases": []}
