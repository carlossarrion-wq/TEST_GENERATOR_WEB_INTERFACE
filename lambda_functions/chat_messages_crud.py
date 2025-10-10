"""
Chat Messages CRUD Lambda Function
Handles all CRUD operations for chat messages in test plans
"""

import json
from db_utils import (
    DatabaseConnection, create_response, create_error_response,
    validate_required_fields, get_test_plan_by_plan_id,
    handle_cors_preflight, QUERIES
)

def lambda_handler(event, context):
    """Main Lambda handler for chat messages CRUD operations"""
    
    # Handle CORS preflight requests
    if event['httpMethod'] == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        method = event['httpMethod']
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        # Route based on HTTP method and path
        if method == 'GET':
            if 'plan_id' not in path_parameters:
                return create_error_response(400, "Plan ID is required", "ValidationError")
            return get_chat_messages(path_parameters['plan_id'], query_parameters)
        
        elif method == 'POST':
            if 'plan_id' not in path_parameters:
                return create_error_response(400, "Plan ID is required for creating message", "ValidationError")
            body = json.loads(event['body']) if event['body'] else {}
            return create_chat_message(path_parameters['plan_id'], body)
        
        elif method == 'DELETE':
            if 'plan_id' not in path_parameters:
                return create_error_response(400, "Plan ID is required for deletion", "ValidationError")
            return clear_chat_history(path_parameters['plan_id'])
        
        else:
            return create_error_response(405, f"Method {method} not allowed", "MethodNotAllowed")
    
    except json.JSONDecodeError:
        return create_error_response(400, "Invalid JSON in request body", "JSONDecodeError")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return create_error_response(500, "Internal server error", "InternalServerError")

def get_chat_messages(plan_id, query_params):
    """Get all chat messages for a specific test plan"""
    try:
        # Get test plan internal ID
        test_plan_internal_id = get_test_plan_by_plan_id(plan_id)
        if not test_plan_internal_id:
            return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
        
        # Parse query parameters
        limit = int(query_params.get('limit', 100))
        offset = int(query_params.get('offset', 0))
        message_type = query_params.get('type')  # 'user' or 'assistant'
        
        # Validate limit
        if limit > 200:
            limit = 200
        
        with DatabaseConnection() as cursor:
            # Build query with optional filtering
            base_query = QUERIES['get_chat_messages_by_plan']
            params = [test_plan_internal_id]
            
            # Add message type filter if specified
            if message_type and message_type in ['user', 'assistant']:
                base_query = base_query.replace(
                    "ORDER BY message_order",
                    "AND cm.message_type = %s ORDER BY message_order"
                )
                params.append(message_type)
            
            # Add pagination
            base_query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(base_query, params)
            messages = cursor.fetchall()
            
            # Get total count
            count_query = """
                SELECT COUNT(*) as total
                FROM chat_messages cm
                WHERE cm.test_plan_id = %s
            """
            count_params = [test_plan_internal_id]
            
            if message_type and message_type in ['user', 'assistant']:
                count_query += " AND cm.message_type = %s"
                count_params.append(message_type)
            
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()['total']
            
            return create_response(200, {
                'plan_id': plan_id,
                'messages': messages,
                'pagination': {
                    'total': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + limit < total_count
                }
            })
    
    except Exception as e:
        print(f"Error getting chat messages for plan {plan_id}: {str(e)}")
        return create_error_response(500, "Error retrieving chat messages", "DatabaseError")

def create_chat_message(plan_id, data):
    """Create a new chat message for a test plan"""
    try:
        # Validate required fields
        required_fields = ['message_type', 'content']
        validate_required_fields(data, required_fields)
        
        # Get test plan internal ID
        test_plan_internal_id = get_test_plan_by_plan_id(plan_id)
        if not test_plan_internal_id:
            return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
        
        # Validate message type
        valid_types = ['user', 'assistant']
        if data['message_type'] not in valid_types:
            return create_error_response(400, f"Message type must be one of: {', '.join(valid_types)}", "ValidationError")
        
        # Validate content is not empty
        if not data['content'].strip():
            return create_error_response(400, "Message content cannot be empty", "ValidationError")
        
        with DatabaseConnection() as cursor:
            # Get next message order
            cursor.execute("""
                SELECT COALESCE(MAX(message_order), 0) + 1 as next_order
                FROM chat_messages 
                WHERE test_plan_id = %s
            """, (test_plan_internal_id,))
            
            result = cursor.fetchone()
            message_order = result['next_order'] if result else 1
            
            # Insert chat message
            insert_query = """
                INSERT INTO chat_messages (
                    test_plan_id, message_type, content, message_order
                ) VALUES (
                    %s, %s, %s, %s
                )
            """
            
            cursor.execute(insert_query, (
                test_plan_internal_id, data['message_type'], 
                data['content'].strip(), message_order
            ))
            
            # Get the created message
            message_id = cursor.lastrowid
            cursor.execute("""
                SELECT 
                    id,
                    message_type,
                    content,
                    message_order,
                    created_at
                FROM chat_messages
                WHERE id = %s
            """, (message_id,))
            
            created_message = cursor.fetchone()
            
            return create_response(201, {
                'message': 'Chat message created successfully',
                'chat_message': created_message
            })
    
    except ValueError as e:
        return create_error_response(400, str(e), "ValidationError")
    except Exception as e:
        print(f"Error creating chat message for plan {plan_id}: {str(e)}")
        return create_error_response(500, "Error creating chat message", "DatabaseError")

def clear_chat_history(plan_id):
    """Clear all chat messages for a test plan"""
    try:
        # Get test plan internal ID
        test_plan_internal_id = get_test_plan_by_plan_id(plan_id)
        if not test_plan_internal_id:
            return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
        
        with DatabaseConnection() as cursor:
            # Get count before deletion
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM chat_messages 
                WHERE test_plan_id = %s
            """, (test_plan_internal_id,))
            
            result = cursor.fetchone()
            deleted_count = result['count'] if result else 0
            
            # Delete all chat messages for the plan
            cursor.execute("""
                DELETE FROM chat_messages 
                WHERE test_plan_id = %s
            """, (test_plan_internal_id,))
            
            return create_response(200, {
                'message': f'Chat history cleared for plan {plan_id}',
                'deleted_messages': deleted_count
            })
    
    except Exception as e:
        print(f"Error clearing chat history for plan {plan_id}: {str(e)}")
        return create_error_response(500, "Error clearing chat history", "DatabaseError")

def add_conversation_pair(plan_id, user_message, assistant_message):
    """Add a user-assistant message pair to maintain conversation flow"""
    try:
        # Get test plan internal ID
        test_plan_internal_id = get_test_plan_by_plan_id(plan_id)
        if not test_plan_internal_id:
            return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
        
        # Validate messages
        if not user_message.strip() or not assistant_message.strip():
            return create_error_response(400, "Both user and assistant messages must be provided", "ValidationError")
        
        with DatabaseConnection() as cursor:
            # Get next message order
            cursor.execute("""
                SELECT COALESCE(MAX(message_order), 0) as last_order
                FROM chat_messages 
                WHERE test_plan_id = %s
            """, (test_plan_internal_id,))
            
            result = cursor.fetchone()
            last_order = result['last_order'] if result else 0
            
            # Insert user message
            cursor.execute("""
                INSERT INTO chat_messages (
                    test_plan_id, message_type, content, message_order
                ) VALUES (
                    %s, %s, %s, %s
                )
            """, (test_plan_internal_id, 'user', user_message.strip(), last_order + 1))
            
            user_message_id = cursor.lastrowid
            
            # Insert assistant message
            cursor.execute("""
                INSERT INTO chat_messages (
                    test_plan_id, message_type, content, message_order
                ) VALUES (
                    %s, %s, %s, %s
                )
            """, (test_plan_internal_id, 'assistant', assistant_message.strip(), last_order + 2))
            
            assistant_message_id = cursor.lastrowid
            
            # Get both created messages
            cursor.execute("""
                SELECT 
                    id,
                    message_type,
                    content,
                    message_order,
                    created_at
                FROM chat_messages
                WHERE id IN (%s, %s)
                ORDER BY message_order
            """, (user_message_id, assistant_message_id))
            
            created_messages = cursor.fetchall()
            
            return create_response(201, {
                'message': 'Conversation pair added successfully',
                'chat_messages': created_messages
            })
    
    except Exception as e:
        print(f"Error adding conversation pair for plan {plan_id}: {str(e)}")
        return create_error_response(500, "Error adding conversation pair", "DatabaseError")

def get_conversation_context(plan_id, last_n_messages=10):
    """Get recent conversation context for AI processing"""
    try:
        # Get test plan internal ID
        test_plan_internal_id = get_test_plan_by_plan_id(plan_id)
        if not test_plan_internal_id:
            return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
        
        with DatabaseConnection() as cursor:
            # Get recent messages
            cursor.execute("""
                SELECT 
                    message_type,
                    content,
                    message_order,
                    created_at
                FROM chat_messages
                WHERE test_plan_id = %s
                ORDER BY message_order DESC
                LIMIT %s
            """, (test_plan_internal_id, last_n_messages))
            
            messages = cursor.fetchall()
            
            # Reverse to get chronological order
            messages.reverse()
            
            # Format for AI context
            conversation_context = []
            for msg in messages:
                conversation_context.append({
                    'role': msg['message_type'],  # 'user' or 'assistant'
                    'content': msg['content'],
                    'timestamp': msg['created_at']
                })
            
            return create_response(200, {
                'plan_id': plan_id,
                'conversation_context': conversation_context,
                'message_count': len(messages)
            })
    
    except Exception as e:
        print(f"Error getting conversation context for plan {plan_id}: {str(e)}")
        return create_error_response(500, "Error getting conversation context", "DatabaseError")

def search_chat_messages(plan_id, search_query, limit=50):
    """Search chat messages by content"""
    try:
        # Get test plan internal ID
        test_plan_internal_id = get_test_plan_by_plan_id(plan_id)
        if not test_plan_internal_id:
            return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
        
        if not search_query.strip():
            return create_error_response(400, "Search query cannot be empty", "ValidationError")
        
        with DatabaseConnection() as cursor:
            # Search messages
            cursor.execute("""
                SELECT 
                    id,
                    message_type,
                    content,
                    message_order,
                    created_at
                FROM chat_messages
                WHERE test_plan_id = %s 
                AND content LIKE %s
                ORDER BY message_order DESC
                LIMIT %s
            """, (test_plan_internal_id, f"%{search_query.strip()}%", limit))
            
            messages = cursor.fetchall()
            
            return create_response(200, {
                'plan_id': plan_id,
                'search_query': search_query,
                'messages': messages,
                'result_count': len(messages)
            })
    
    except Exception as e:
        print(f"Error searching chat messages for plan {plan_id}: {str(e)}")
        return create_error_response(500, "Error searching chat messages", "DatabaseError")
