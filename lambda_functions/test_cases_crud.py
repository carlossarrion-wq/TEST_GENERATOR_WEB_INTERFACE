"""
Test Cases CRUD Lambda Function
Handles all CRUD operations for test cases
"""

import json
from db_utils import (
    DatabaseConnection, create_response, create_error_response,
    validate_required_fields, generate_case_id, get_test_plan_by_plan_id,
    handle_cors_preflight, QUERIES
)

def lambda_handler(event, context):
    """Main Lambda handler for test cases CRUD operations"""
    
    # Handle CORS preflight requests
    if event['httpMethod'] == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        method = event['httpMethod']
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        # Route based on HTTP method and path
        if method == 'GET':
            if 'case_id' in path_parameters:
                return get_test_case(path_parameters['case_id'])
            elif 'plan_id' in path_parameters:
                return get_test_cases_by_plan(path_parameters['plan_id'], query_parameters)
            else:
                return create_error_response(400, "Plan ID or Case ID is required", "ValidationError")
        
        elif method == 'POST':
            if 'plan_id' not in path_parameters:
                return create_error_response(400, "Plan ID is required for creating test case", "ValidationError")
            body = json.loads(event['body']) if event['body'] else {}
            return create_test_case(path_parameters['plan_id'], body)
        
        elif method == 'PUT':
            if 'case_id' not in path_parameters:
                return create_error_response(400, "Case ID is required for update", "ValidationError")
            body = json.loads(event['body']) if event['body'] else {}
            return update_test_case(path_parameters['case_id'], body)
        
        elif method == 'DELETE':
            if 'case_id' not in path_parameters:
                return create_error_response(400, "Case ID is required for deletion", "ValidationError")
            return delete_test_case(path_parameters['case_id'])
        
        else:
            return create_error_response(405, f"Method {method} not allowed", "MethodNotAllowed")
    
    except json.JSONDecodeError:
        return create_error_response(400, "Invalid JSON in request body", "JSONDecodeError")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return create_error_response(500, "Internal server error", "InternalServerError")

def get_test_cases_by_plan(plan_id, query_params):
    """Get all test cases for a specific test plan"""
    try:
        # Get test plan internal ID
        test_plan_internal_id = get_test_plan_by_plan_id(plan_id)
        if not test_plan_internal_id:
            return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
        
        # Parse query parameters
        include_steps = query_params.get('include_steps', 'false').lower() == 'true'
        priority = query_params.get('priority')
        
        with DatabaseConnection() as cursor:
            # Get test cases
            base_query = QUERIES['get_test_cases_by_plan']
            params = [test_plan_internal_id]
            
            # Add priority filter if specified
            if priority:
                base_query = base_query.replace(
                    "WHERE tc.test_plan_id = %s AND tc.is_deleted = FALSE",
                    "WHERE tc.test_plan_id = %s AND tc.is_deleted = FALSE AND tc.priority = %s"
                )
                params.append(priority)
            
            cursor.execute(base_query, params)
            test_cases = cursor.fetchall()
            
            # Get test steps for each case if requested
            if include_steps:
                for test_case in test_cases:
                    cursor.execute(QUERIES['get_test_steps_by_case'], (test_case['id'],))
                    test_case['test_steps'] = cursor.fetchall()
            
            return create_response(200, {
                'plan_id': plan_id,
                'test_cases': test_cases
            })
    
    except Exception as e:
        print(f"Error getting test cases for plan {plan_id}: {str(e)}")
        return create_error_response(500, "Error retrieving test cases", "DatabaseError")

def get_test_case(case_id):
    """Get a specific test case by case_id"""
    try:
        with DatabaseConnection() as cursor:
            # Get test case details
            cursor.execute("""
                SELECT 
                    tc.id,
                    tc.test_plan_id,
                    tp.plan_id,
                    tc.case_id,
                    tc.name,
                    tc.description,
                    tc.priority,
                    tc.preconditions,
                    tc.expected_result,
                    tc.test_data,
                    tc.case_order,
                    tc.created_at,
                    tc.updated_at
                FROM test_cases tc
                JOIN test_plans tp ON tc.test_plan_id = tp.id
                WHERE tc.case_id = %s AND tc.is_deleted = FALSE
            """, (case_id,))
            
            test_case = cursor.fetchone()
            
            if not test_case:
                return create_error_response(404, f"Test case {case_id} not found", "NotFound")
            
            # Get test steps for this case
            cursor.execute(QUERIES['get_test_steps_by_case'], (test_case['id'],))
            test_steps = cursor.fetchall()
            
            # Build complete response
            test_case['test_steps'] = test_steps
            
            return create_response(200, {
                'test_case': test_case
            })
    
    except Exception as e:
        print(f"Error getting test case {case_id}: {str(e)}")
        return create_error_response(500, "Error retrieving test case", "DatabaseError")

def create_test_case(plan_id, data):
    """Create a new test case for a test plan"""
    try:
        # Validate required fields
        required_fields = ['name', 'description']
        validate_required_fields(data, required_fields)
        
        # Get test plan internal ID
        test_plan_internal_id = get_test_plan_by_plan_id(plan_id)
        if not test_plan_internal_id:
            return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
        
        # Generate case ID
        case_id = generate_case_id(plan_id)
        
        # Set defaults
        priority = data.get('priority', 'Medium')
        preconditions = data.get('preconditions', '')
        expected_result = data.get('expected_result', '')
        test_data = data.get('test_data', '')
        test_steps = data.get('test_steps', [])
        
        # Validate priority
        valid_priorities = ['High', 'Medium', 'Low']
        if priority not in valid_priorities:
            return create_error_response(400, f"Priority must be one of: {', '.join(valid_priorities)}", "ValidationError")
        
        with DatabaseConnection() as cursor:
            # Get next case order
            cursor.execute("""
                SELECT COALESCE(MAX(case_order), 0) + 1 as next_order
                FROM test_cases 
                WHERE test_plan_id = %s AND is_deleted = FALSE
            """, (test_plan_internal_id,))
            
            result = cursor.fetchone()
            case_order = result['next_order'] if result else 1
            
            # Insert test case
            insert_query = """
                INSERT INTO test_cases (
                    test_plan_id, case_id, name, description, priority,
                    preconditions, expected_result, test_data, case_order
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            cursor.execute(insert_query, (
                test_plan_internal_id, case_id, data['name'], data['description'],
                priority, preconditions, expected_result, test_data, case_order
            ))
            
            # Get the created test case ID
            test_case_internal_id = cursor.lastrowid
            
            # Insert test steps if provided
            created_steps = []
            if test_steps:
                for i, step_description in enumerate(test_steps, 1):
                    if step_description and step_description.strip():
                        cursor.execute("""
                            INSERT INTO test_steps (test_case_id, step_number, description)
                            VALUES (%s, %s, %s)
                        """, (test_case_internal_id, i, step_description.strip()))
                        
                        created_steps.append({
                            'step_number': i,
                            'description': step_description.strip()
                        })
            
            # Get the complete created test case
            cursor.execute("""
                SELECT 
                    tc.id,
                    tc.case_id,
                    tc.name,
                    tc.description,
                    tc.priority,
                    tc.preconditions,
                    tc.expected_result,
                    tc.test_data,
                    tc.case_order,
                    tc.created_at,
                    tc.updated_at
                FROM test_cases tc
                WHERE tc.id = %s
            """, (test_case_internal_id,))
            
            created_case = cursor.fetchone()
            created_case['test_steps'] = created_steps
            
            return create_response(201, {
                'message': 'Test case created successfully',
                'test_case': created_case
            })
    
    except ValueError as e:
        return create_error_response(400, str(e), "ValidationError")
    except Exception as e:
        print(f"Error creating test case for plan {plan_id}: {str(e)}")
        return create_error_response(500, "Error creating test case", "DatabaseError")

def update_test_case(case_id, data):
    """Update an existing test case"""
    try:
        with DatabaseConnection() as cursor:
            # Check if test case exists
            cursor.execute("""
                SELECT id, test_plan_id FROM test_cases 
                WHERE case_id = %s AND is_deleted = FALSE
            """, (case_id,))
            existing_case = cursor.fetchone()
            
            if not existing_case:
                return create_error_response(404, f"Test case {case_id} not found", "NotFound")
            
            test_case_internal_id = existing_case['id']
            
            # Build dynamic update query
            update_fields = []
            params = []
            
            # Handle updatable fields
            updatable_fields = [
                'name', 'description', 'priority', 'preconditions',
                'expected_result', 'test_data', 'case_order'
            ]
            
            for field in updatable_fields:
                if field in data and data[field] is not None:
                    update_fields.append(f"{field} = %s")
                    params.append(data[field])
            
            # Validate priority if provided
            if 'priority' in data:
                valid_priorities = ['High', 'Medium', 'Low']
                if data['priority'] not in valid_priorities:
                    return create_error_response(400, f"Priority must be one of: {', '.join(valid_priorities)}", "ValidationError")
            
            # Update test case if there are fields to update
            if update_fields:
                update_query = f"""
                    UPDATE test_cases 
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE case_id = %s AND is_deleted = FALSE
                """
                params.append(case_id)
                cursor.execute(update_query, params)
            
            # Handle test steps update if provided
            if 'test_steps' in data:
                # Delete existing steps
                cursor.execute("""
                    DELETE FROM test_steps WHERE test_case_id = %s
                """, (test_case_internal_id,))
                
                # Insert new steps
                test_steps = data['test_steps']
                if test_steps:
                    for i, step_description in enumerate(test_steps, 1):
                        if step_description and step_description.strip():
                            cursor.execute("""
                                INSERT INTO test_steps (test_case_id, step_number, description)
                                VALUES (%s, %s, %s)
                            """, (test_case_internal_id, i, step_description.strip()))
            
            # Get updated test case with steps
            cursor.execute("""
                SELECT 
                    tc.id,
                    tc.case_id,
                    tc.name,
                    tc.description,
                    tc.priority,
                    tc.preconditions,
                    tc.expected_result,
                    tc.test_data,
                    tc.case_order,
                    tc.created_at,
                    tc.updated_at
                FROM test_cases tc
                WHERE tc.case_id = %s AND tc.is_deleted = FALSE
            """, (case_id,))
            
            updated_case = cursor.fetchone()
            
            # Get test steps
            cursor.execute(QUERIES['get_test_steps_by_case'], (updated_case['id'],))
            updated_case['test_steps'] = cursor.fetchall()
            
            return create_response(200, {
                'message': 'Test case updated successfully',
                'test_case': updated_case
            })
    
    except Exception as e:
        print(f"Error updating test case {case_id}: {str(e)}")
        return create_error_response(500, "Error updating test case", "DatabaseError")

def delete_test_case(case_id):
    """Soft delete a test case and all associated test steps"""
    try:
        with DatabaseConnection() as cursor:
            # Check if test case exists
            cursor.execute("""
                SELECT id FROM test_cases 
                WHERE case_id = %s AND is_deleted = FALSE
            """, (case_id,))
            existing_case = cursor.fetchone()
            
            if not existing_case:
                return create_error_response(404, f"Test case {case_id} not found", "NotFound")
            
            test_case_internal_id = existing_case['id']
            
            # Soft delete test case
            cursor.execute("""
                UPDATE test_cases 
                SET is_deleted = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE case_id = %s
            """, (case_id,))
            
            # Delete associated test steps (hard delete)
            cursor.execute("""
                DELETE FROM test_steps 
                WHERE test_case_id = %s
            """, (test_case_internal_id,))
            
            return create_response(200, {
                'message': f'Test case {case_id} deleted successfully'
            })
    
    except Exception as e:
        print(f"Error deleting test case {case_id}: {str(e)}")
        return create_error_response(500, "Error deleting test case", "DatabaseError")

def reorder_test_cases(plan_id, case_orders):
    """Reorder test cases within a test plan"""
    try:
        # Get test plan internal ID
        test_plan_internal_id = get_test_plan_by_plan_id(plan_id)
        if not test_plan_internal_id:
            return create_error_response(404, f"Test plan {plan_id} not found", "NotFound")
        
        with DatabaseConnection() as cursor:
            # Validate all case IDs belong to the plan
            case_ids = list(case_orders.keys())
            if not case_ids:
                return create_error_response(400, "No test cases provided for reordering", "ValidationError")
            
            placeholders = ', '.join(['%s'] * len(case_ids))
            cursor.execute(f"""
                SELECT case_id FROM test_cases 
                WHERE test_plan_id = %s AND case_id IN ({placeholders}) AND is_deleted = FALSE
            """, [test_plan_internal_id] + case_ids)
            
            valid_cases = [row['case_id'] for row in cursor.fetchall()]
            invalid_cases = set(case_ids) - set(valid_cases)
            
            if invalid_cases:
                return create_error_response(400, f"Invalid case IDs for plan {plan_id}: {', '.join(invalid_cases)}", "ValidationError")
            
            # Update case orders
            for case_id, new_order in case_orders.items():
                cursor.execute("""
                    UPDATE test_cases 
                    SET case_order = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE case_id = %s AND test_plan_id = %s AND is_deleted = FALSE
                """, (new_order, case_id, test_plan_internal_id))
            
            return create_response(200, {
                'message': f'Test cases reordered successfully for plan {plan_id}'
            })
    
    except Exception as e:
        print(f"Error reordering test cases for plan {plan_id}: {str(e)}")
        return create_error_response(500, "Error reordering test cases", "DatabaseError")
