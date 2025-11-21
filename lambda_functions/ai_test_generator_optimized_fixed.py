import json
import boto3
import os
import time
import uuid
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
lambda_client = boto3.client('lambda', region_name='eu-west-1')

KNOWLEDGE_BASE_ID = os.environ.get('KNOWLEDGE_BASE_ID', 'VH6SRH9ZNO')
MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'eu.anthropic.claude-haiku-4-5-20251001-v1:0')
LAMBDA_FUNCTION_NAME = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'test-plan-generator-ai')

def lambda_handler(event, context):
    # Handle async task processing (direct Lambda invocation)
    if 'action' in event and event['action'] == 'process-async-task':
        task_id = event.get('task_id')
        data = event.get('data')
        if task_id and data:
            process_async_task(task_id, data)
            return {'statusCode': 200, 'body': json.dumps({'message': 'Task processed'})}
    
    # Handle HTTP requests
    if 'httpMethod' not in event:
        return create_error_response(400, "Invalid event format", "InvalidEvent")
    
    if event['httpMethod'] == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        method = event['httpMethod']
        path_parameters = event.get('pathParameters') or {}
        
        body = json.loads(event['body']) if event['body'] else {}
        action = path_parameters.get('action', body.get('action'))
        
        # Handle async endpoints
        if action == 'async':
            if method == 'POST':
                return start_async_generation(body)
            else:
                return create_error_response(405, f"Method {method} not allowed for async", "MethodNotAllowed")
        elif action == 'async-status':
            if method == 'GET':
                task_id = path_parameters.get('task_id')
                if not task_id:
                    return create_error_response(400, "Task ID required", "ValidationError")
                return get_async_status(task_id)
            else:
                return create_error_response(405, f"Method {method} not allowed for async-status", "MethodNotAllowed")
        
        # Handle synchronous endpoints
        if method != 'POST':
            return create_error_response(405, f"Method {method} not allowed", "MethodNotAllowed")
        
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

def start_async_generation(data):
    """Start asynchronous test plan generation and return task_id immediately"""
    try:
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        print(f"🚀 Starting async generation with task_id: {task_id}")
        
        # Store initial task state in MySQL
        with DatabaseConnection() as cursor:
            cursor.execute("""
                INSERT INTO async_tasks (task_id, status, request_data, message)
                VALUES (%s, %s, %s, %s)
            """, (task_id, 'processing', json.dumps(data), 'Generando plan de pruebas...'))
        
        # Invoke Lambda asynchronously to process in background
        # This allows us to return immediately without waiting for completion
        try:
            payload = {
                'task_id': task_id,
                'action': 'process-async-task',
                'data': data
            }
            
            print(f"📤 Invoking Lambda asynchronously for task {task_id}")
            lambda_client.invoke(
                FunctionName=LAMBDA_FUNCTION_NAME,
                InvocationType='Event',  # Asynchronous invocation
                Payload=json.dumps(payload)
            )
            print(f"✅ Async invocation successful for task {task_id}")
            
        except Exception as invoke_error:
            print(f"❌ Failed to invoke async Lambda: {str(invoke_error)}")
            # Update task status to failed
            with DatabaseConnection() as cursor:
                cursor.execute("""
                    UPDATE async_tasks 
                    SET status = %s, error_message = %s, message = %s, completed_at = NOW()
                    WHERE task_id = %s
                """, ('failed', str(invoke_error), f'Error al iniciar procesamiento: {str(invoke_error)}', task_id))
            
            return create_error_response(500, f"Failed to start async processing: {str(invoke_error)}", "AsyncInvokeError")
        
        # Return task_id immediately (Lambda will process in background)
        return create_response(202, {
            'task_id': task_id,
            'status': 'processing',
            'message': 'Generación iniciada. Use el task_id para consultar el estado.'
        })
    
    except Exception as e:
        print(f"Error starting async generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_error_response(500, f"Error starting async generation: {str(e)}", "AsyncStartError")

def process_async_task(task_id, data):
    """Process async task in background (called by async Lambda invocation)"""
    try:
        print(f"🔄 Processing async task {task_id}")
        
        # Update status to processing
        with DatabaseConnection() as cursor:
            cursor.execute("""
                UPDATE async_tasks 
                SET message = %s
                WHERE task_id = %s
            """, ('Generando casos de prueba con IA...', task_id))
        
        # Generate test plan
        result = generate_test_plan_with_langchain(data)
        
        # Parse the result
        result_body = json.loads(result['body'])
        
        if result['statusCode'] == 201:
            # Success - update task with completed status
            with DatabaseConnection() as cursor:
                cursor.execute("""
                    UPDATE async_tasks 
                    SET status = %s, result_data = %s, message = %s, completed_at = NOW()
                    WHERE task_id = %s
                """, ('completed', json.dumps(result_body), 'Plan de pruebas generado exitosamente', task_id))
            print(f"✅ Task {task_id} completed successfully")
        else:
            # Error - update task with failed status
            with DatabaseConnection() as cursor:
                cursor.execute("""
                    UPDATE async_tasks 
                    SET status = %s, error_message = %s, message = %s, completed_at = NOW()
                    WHERE task_id = %s
                """, ('failed', json.dumps(result_body), result_body.get('error', 'Error al generar plan de pruebas'), task_id))
            print(f"❌ Task {task_id} failed: {result_body.get('error')}")
    
    except Exception as gen_error:
        # Handle generation errors
        print(f"❌ Generation error for task {task_id}: {str(gen_error)}")
        import traceback
        traceback.print_exc()
        
        with DatabaseConnection() as cursor:
            cursor.execute("""
                UPDATE async_tasks 
                SET status = %s, error_message = %s, message = %s, completed_at = NOW()
                WHERE task_id = %s
            """, ('failed', str(gen_error), f'Error interno: {str(gen_error)}', task_id))

def get_async_status(task_id):
    """Get the status of an async task from MySQL"""
    try:
        print(f"📊 Checking status for task_id: {task_id}")
        
        with DatabaseConnection() as cursor:
            cursor.execute("""
                SELECT task_id, status, result_data, error_message, message, created_at
                FROM async_tasks
                WHERE task_id = %s
            """, (task_id,))
            
            task = cursor.fetchone()
        
        if not task:
            return create_error_response(404, f"Task {task_id} not found", "TaskNotFound")
        
        status = task['status']
        
        if status == 'completed':
            # Return the completed result
            result = json.loads(task['result_data'])
            return create_response(200, {
                'status': 'completed',
                'result': result
            })
        elif status == 'failed':
            # Return the error
            error = task.get('error_message', 'Unknown error')
            return create_response(200, {
                'status': 'failed',
                'error': error,
                'message': task.get('message', 'Error al generar plan de pruebas')
            })
        else:
            # Still processing
            return create_response(200, {
                'status': 'processing',
                'message': task.get('message', 'Procesando...'),
                'created_at': task.get('created_at').isoformat() if task.get('created_at') else None
            })
    
    except Exception as e:
        print(f"Error getting async status: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_error_response(500, f"Error getting task status: {str(e)}", "AsyncStatusError")

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
            error_msg = agent_result.get('error', 'Agent failed to generate test plan')
            return create_error_response(500, error_msg, "AgentError")
        
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
            msg_type = msg['message_type']
            msg_content = msg['content'][:200]
            history_text += f"{msg_type}: {msg_content}\n"
        
        # System prompt with VERY explicit past tense instructions
        system_prompt = (
            "Eres un asistente experto en testing. Proporciona respuestas útiles y concisas sobre planes de prueba.\n\n"
            "🚨 REGLA ABSOLUTAMENTE CRÍTICA - TIEMPO VERBAL 🚨\n"
            "ESTA ES LA REGLA MÁS IMPORTANTE QUE DEBES SEGUIR:\n\n"
            "Cuando el usuario te pida realizar cambios en los casos de prueba (modificar nombres, descripciones, agregar casos, etc.), "
            "las modificaciones se ejecutan INSTANTÁNEAMENTE y de forma AUTOMÁTICA en el momento en que el usuario envía su mensaje. "
            "Para cuando tú generas tu respuesta, la acción YA ESTÁ 100% COMPLETADA.\n\n"
            "Por lo tanto:\n"
            "✅ SIEMPRE usa tiempo PASADO (pretérito perfecto compuesto): 'He cambiado', 'He modificado', 'He actualizado'\n"
            "❌ NUNCA JAMÁS uses tiempo FUTURO: 'Voy a cambiar', 'Cambiaré', 'Procederé a'\n\n"
            "PATRONES OBLIGATORIOS para responder:\n"
            "Usuario: 'Modifica el nombre del caso TC-001 a X'\n"
            "Tú DEBES responder: 'He cambiado el nombre del caso TC-001 de [nombre anterior] a [X]'\n"
            "Tú NO DEBES responder: 'Voy a cambiar el nombre...' ❌❌❌\n\n"
            "Usuario: 'Agrega un nuevo caso de prueba para Y'\n"
            "Tú DEBES responder: 'He creado el caso TC-XXX para validar Y'\n"
            "Tú NO DEBES responder: 'Voy a crear un caso...' ❌❌❌\n\n"
            "Usuario: 'Elimina el caso TC-005'\n"
            "Tú DEBES responder: 'He eliminado el caso TC-005'\n"
            "Tú NO DEBES responder: 'Voy a eliminar...' ❌❌❌\n\n"
            "RECUERDA: La acción YA OCURRIÓ. El usuario NO está esperando que hagas algo - ya está hecho. "
            "Solo necesita que CONFIRMES lo que ya se completó usando tiempo PASADO."
        )
        
        user_prompt = f"""Contexto del Plan:
- Título: {plan_context['title']}
- Casos de Prueba: {plan_context['test_cases_count']}

Conversación Reciente:
{history_text}

Usuario: {user_message}

IMPORTANTE: Si el usuario te pidió hacer algún cambio, ese cambio YA ESTÁ HECHO. Usa tiempo PASADO para confirmarlo.
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
