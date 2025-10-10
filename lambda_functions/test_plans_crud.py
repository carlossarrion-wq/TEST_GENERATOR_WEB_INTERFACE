"""
Test Plans CRUD Lambda Function
Handles all CRUD operations for test plans
"""

import json
from db_utils import (
    DatabaseConnection, create_response, create_error_response,
    validate_required_fields, generate_plan_id, handle_cors_preflight,
    QUERIES
)

def lambda_handler(event, context):
    """Main Lambda handler for test plans CRUD operations"""
    
    # Handle CORS preflight requests
    if event['httpMethod'] == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        method = event['httpMethod']
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        # Route based on HTTP method and path
        if method == 'GET':
            if 'plan_id' in path_parameters:
                return get_test_plan(path_parameters['plan_id'])
            else:
                return get_test_plans(query_parameters)
        
        elif method == 'POST':
            body = json.loads(event['body']) if event['body'] else {}
            return create_test_plan(body)
        
        elif method == 'PUT':
            if 'plan_id' not in path_parameters:
                return create_error_response(400, "Plan ID is required for update", "ValidationError")
            body = json.loads(event['body']) if event['body'] else {}
            return update_test_plan(path_parameters['plan_id'], body)
        
        elif method == 'DELETE':
            if 'plan_id' not in path_parameters:
                return create_error_response(400, "Plan ID is required for deletion", "ValidationError")
            return delete_test_plan(path_parameters['plan_id'])
        
        else:
            return create_error_response(405, f"Method {method} not allowed", "MethodNotAllowed")
    
    except json.JSONDecodeError:
        return create_error_response(400, "Invalid JSON in request body", "JSONDecodeError")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return create_error_response(500, "Internal server error", "InternalServerError")

def get_test_plans(query_params):
    """Get all test plans with optional filtering"""
    try:
        # Parse query parameters
        limit = int(query_params.get('limit', 50))
        offset = int(query_params.get('offset', 0))
        status = query_params.get('status')
        search = query_params.get('search')
        
        # Validate limit
        if limit > 100:
            limit = 100
        
        with DatabaseConnection() as cursor:
            # Build dynamic query
            base_query = """
                SELECT 
                    tp.id,
                    tp.plan_id,
                    tp.title,
                    tp.reference,
                    tp.requirements,
                    tp.coverage_percentage,
                    tp.min_test_cases,
                    tp.max_test_cases,
                    tp.selected_test_types,
                    tp.status,
                    tp.created_at,
                    tp.updated_at,
                    COALESCE(COUNT(tc.id), 0) as test_cases_count
                FROM test_plans tp
                LEFT JOIN test_cases tc ON tp.id = tc.test_plan_id AND tc.is_deleted = FALSE
                WHERE tp.is_deleted = FALSE
            """
            
            params = []
            
            # Add status filter
            if status:
                base_query += " AND tp.status = %s"
                params.append(status)
            
            # Add search filter
            if search:
                base_query += " AND (tp.title LIKE %s OR tp.requirements LIKE %s OR tp.reference LIKE %s)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term])
            
            # Add grouping, ordering, and pagination
            base_query += """
                GROUP BY tp.id
                ORDER BY tp.created_at DESC
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            
            cursor.execute(base_query, params)
            test_plans = cursor.fetchall()
            
            # Get total count for pagination
            count_query = """
                SELECT COUNT(*) as total
                FROM test_plans tp
                WHERE tp.is_deleted = FALSE
            """
            count_params = []
            
            if status:
                count_query += " AND tp.status = %s"
                count_params.append(status)
            
            if search:
                count_query += " AND (tp.title LIKE %s OR tp.requirements LIKE %s OR tp.reference LIKE %s)"
                count_params.extend([search_term, search_term, search_term])
            
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()['total']
            
            # Parse JSON fields
            for plan in test_plans:
                if plan['selected_test_types']:
                    try:
                        plan['selected_test_types'] = json.loads(plan['selected_test_types'])
                    except json.JSONDecodeError:
                        plan['selected_test_types'] = []
            
            return create_response(200, {
                'test_plans': test_plans,
                'pagination': {
                    'total': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + limit < total_count
                }
            })
    
    except Exception as e:
        print(f"Error getting test plans: {str(e)}")
        return create_error_response(500, "Error retrieving test plans", "DatabaseError")

def get_test_plan(plan_id):
    """Get a specific test plan by plan_id"""
    try:
        with DatabaseConnection() as cursor:
            # Get test plan details
            cursor.execute(QUERIES['get_test_plan_summary'], (plan_id,))
            test_plan = cursor.fetchone()
            
            if not test_plan:
                return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
            
            # Parse JSON fields
            if test_plan['selected_test_types']:
                try:
                    test_plan['selected_test_types'] = json.loads(test_plan['selected_test_types'])
                except json.JSONDecodeError:
                    test_plan['selected_test_types'] = []
            
            # Get test cases for this plan
            cursor.execute(QUERIES['get_test_cases_by_plan'], (test_plan['id'],))
            test_cases = cursor.fetchall()
            
            # Get chat messages for this plan
            cursor.execute(QUERIES['get_chat_messages_by_plan'], (test_plan['id'],))
            chat_messages = cursor.fetchall()
            
            # Build complete response
            response_data = {
                'test_plan': test_plan,
                'test_cases': test_cases,
                'chat_messages': chat_messages
            }
            
            return create_response(200, response_data)
    
    except Exception as e:
        print(f"Error getting test plan {plan_id}: {str(e)}")
        return create_error_response(500, "Error retrieving test plan", "DatabaseError")

def create_test_plan(data):
    """Create a new test plan"""
    try:
        # Validate required fields
        required_fields = ['title', 'requirements']
        validate_required_fields(data, required_fields)
        
        # Generate plan ID
        plan_id = generate_plan_id()
        
        # Set defaults
        coverage_percentage = data.get('coverage_percentage', 80)
        min_test_cases = data.get('min_test_cases', 5)
        max_test_cases = data.get('max_test_cases', 15)
        selected_test_types = data.get('selected_test_types', ['unit', 'integration'])
        status = data.get('status', 'draft')
        reference = data.get('reference', '')
        
        # Validate coverage percentage
        if not (10 <= coverage_percentage <= 100):
            return create_error_response(400, "Coverage percentage must be between 10 and 100", "ValidationError")
        
        # Validate test case limits
        if min_test_cases > max_test_cases:
            return create_error_response(400, "Minimum test cases cannot be greater than maximum", "ValidationError")
        
        # Validate status
        valid_statuses = ['draft', 'active', 'completed', 'archived']
        if status not in valid_statuses:
            return create_error_response(400, f"Status must be one of: {', '.join(valid_statuses)}", "ValidationError")
        
        with DatabaseConnection() as cursor:
            # Insert test plan
            insert_query = """
                INSERT INTO test_plans (
                    plan_id, title, reference, requirements, coverage_percentage,
                    min_test_cases, max_test_cases, selected_test_types, status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            cursor.execute(insert_query, (
                plan_id, data['title'], reference, data['requirements'],
                coverage_percentage, min_test_cases, max_test_cases,
                json.dumps(selected_test_types), status
            ))
            
            # Get the created test plan's internal ID
            test_plan_internal_id = cursor.lastrowid
            
            # Process and save test cases if provided
            test_cases_saved = 0
            if 'testCases' in data and isinstance(data['testCases'], list):
                print(f"Processing {len(data['testCases'])} test cases...")
                
                for test_case in data['testCases']:
                    try:
                        # Insert test case
                        test_case_query = """
                            INSERT INTO test_cases (
                                test_plan_id, case_id, name, description, priority,
                                preconditions, expected_result, test_data
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        
                        cursor.execute(test_case_query, (
                            test_plan_internal_id,
                            test_case.get('id', f'TC-{test_cases_saved + 1:03d}'),
                            test_case.get('name', f'Test Case {test_cases_saved + 1}'),
                            test_case.get('description', ''),
                            test_case.get('priority', 'Medium'),
                            test_case.get('preconditions', ''),
                            test_case.get('expectedResult', ''),
                            test_case.get('testData', '')
                        ))
                        
                        test_case_internal_id = cursor.lastrowid
                        
                        # Insert test steps if provided
                        if 'steps' in test_case and isinstance(test_case['steps'], list):
                            for step in test_case['steps']:
                                step_query = """
                                    INSERT INTO test_steps (test_case_id, step_number, description)
                                    VALUES (%s, %s, %s)
                                """
                                cursor.execute(step_query, (
                                    test_case_internal_id,
                                    step.get('number', 1),
                                    step.get('description', '')
                                ))
                        
                        test_cases_saved += 1
                        
                    except Exception as step_error:
                        print(f"Error saving test case {test_case.get('id', 'unknown')}: {str(step_error)}")
                        # Continue with other test cases even if one fails
                        continue
                
                print(f"Successfully saved {test_cases_saved} test cases")
            
            # Get the created test plan with updated test case count
            cursor.execute(QUERIES['get_test_plan_summary'], (plan_id,))
            created_plan = cursor.fetchone()
            
            # Parse JSON fields
            if created_plan['selected_test_types']:
                try:
                    created_plan['selected_test_types'] = json.loads(created_plan['selected_test_types'])
                except json.JSONDecodeError:
                    created_plan['selected_test_types'] = []
            
            return create_response(201, {
                'message': 'Test plan created successfully',
                'test_plan': created_plan,
                'test_cases_saved': test_cases_saved
            })
    
    except ValueError as e:
        return create_error_response(400, str(e), "ValidationError")
    except Exception as e:
        print(f"Error creating test plan: {str(e)}")
        return create_error_response(500, "Error creating test plan", "DatabaseError")

def update_test_plan(plan_id, data):
    """Update an existing test plan"""
    try:
        with DatabaseConnection() as cursor:
            # Check if test plan exists
            cursor.execute("SELECT id FROM test_plans WHERE plan_id = %s AND is_deleted = FALSE", (plan_id,))
            existing_plan = cursor.fetchone()
            
            if not existing_plan:
                return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
            
            # Build dynamic update query
            update_fields = []
            params = []
            
            # Handle updatable fields
            updatable_fields = [
                'title', 'reference', 'requirements', 'coverage_percentage',
                'min_test_cases', 'max_test_cases', 'status'
            ]
            
            for field in updatable_fields:
                if field in data and data[field] is not None:
                    update_fields.append(f"{field} = %s")
                    params.append(data[field])
            
            # Handle selected_test_types specially (JSON field)
            if 'selected_test_types' in data:
                update_fields.append("selected_test_types = %s")
                params.append(json.dumps(data['selected_test_types']))
            
            if not update_fields:
                return create_error_response(400, "No valid fields to update", "ValidationError")
            
            # Validate coverage percentage if provided
            if 'coverage_percentage' in data:
                if not (10 <= data['coverage_percentage'] <= 100):
                    return create_error_response(400, "Coverage percentage must be between 10 and 100", "ValidationError")
            
            # Validate test case limits if provided
            if 'min_test_cases' in data and 'max_test_cases' in data:
                if data['min_test_cases'] > data['max_test_cases']:
                    return create_error_response(400, "Minimum test cases cannot be greater than maximum", "ValidationError")
            
            # Validate status if provided
            if 'status' in data:
                valid_statuses = ['draft', 'active', 'completed', 'archived']
                if data['status'] not in valid_statuses:
                    return create_error_response(400, f"Status must be one of: {', '.join(valid_statuses)}", "ValidationError")
            
            # Build and execute update query
            update_query = f"""
                UPDATE test_plans 
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE plan_id = %s AND is_deleted = FALSE
            """
            params.append(plan_id)
            
            cursor.execute(update_query, params)
            
            # Get updated test plan
            cursor.execute(QUERIES['get_test_plan_summary'], (plan_id,))
            updated_plan = cursor.fetchone()
            
            # Parse JSON fields
            if updated_plan['selected_test_types']:
                try:
                    updated_plan['selected_test_types'] = json.loads(updated_plan['selected_test_types'])
                except json.JSONDecodeError:
                    updated_plan['selected_test_types'] = []
            
            return create_response(200, {
                'message': 'Test plan updated successfully',
                'test_plan': updated_plan
            })
    
    except Exception as e:
        print(f"Error updating test plan {plan_id}: {str(e)}")
        return create_error_response(500, "Error updating test plan", "DatabaseError")

def delete_test_plan(plan_id):
    """Soft delete a test plan and all associated data"""
    try:
        with DatabaseConnection() as cursor:
            # Check if test plan exists
            cursor.execute("SELECT id FROM test_plans WHERE plan_id = %s AND is_deleted = FALSE", (plan_id,))
            existing_plan = cursor.fetchone()
            
            if not existing_plan:
                return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
            
            test_plan_internal_id = existing_plan['id']
            
            # Soft delete test plan
            cursor.execute("""
                UPDATE test_plans 
                SET is_deleted = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE plan_id = %s
            """, (plan_id,))
            
            # Soft delete associated test cases
            cursor.execute("""
                UPDATE test_cases 
                SET is_deleted = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE test_plan_id = %s
            """, (test_plan_internal_id,))
            
            # Delete chat messages (hard delete since they don't have is_deleted flag)
            cursor.execute("""
                DELETE FROM chat_messages 
                WHERE test_plan_id = %s
            """, (test_plan_internal_id,))
            
            # Delete test steps (hard delete, will be cascaded)
            cursor.execute("""
                DELETE FROM test_steps 
                WHERE test_case_id IN (
                    SELECT id FROM test_cases WHERE test_plan_id = %s
                )
            """, (test_plan_internal_id,))
            
            return create_response(200, {
                'message': f'Test plan {plan_id} deleted successfully'
            })
    
    except Exception as e:
        print(f"Error deleting test plan {plan_id}: {str(e)}")
        return create_error_response(500, "Error deleting test plan", "DatabaseError")
