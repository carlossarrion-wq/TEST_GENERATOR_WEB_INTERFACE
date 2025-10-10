"""
Database utilities for Test Plan Generator Lambda functions
Shared database connection and common functions
"""

import pymysql
import json
import os
from datetime import datetime, date
from decimal import Decimal

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.environ.get('RDS_HOST', 'test-plan-generator-db.czuimyk2qu10.eu-west-1.rds.amazonaws.com'),
    'user': os.environ.get('RDS_USER', 'admin'),
    'password': os.environ.get('RDS_PASSWORD', 'TempPassword123!'),
    'database': os.environ.get('RDS_DATABASE', 'testplangenerator'),
    'port': int(os.environ.get('RDS_PORT', '3306')),
    'charset': 'utf8mb4',
    'connect_timeout': 60,
    'read_timeout': 60,
    'write_timeout': 60,
    'autocommit': True
}

class DatabaseConnection:
    """Database connection context manager"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def __enter__(self):
        try:
            self.connection = pymysql.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor(pymysql.cursors.DictCursor)
            return self.cursor
        except Exception as e:
            print(f"Database connection error: {e}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

def serialize_datetime(obj):
    """Convert datetime and decimal objects to JSON serializable format"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def create_response(status_code, body, headers=None):
    """Create standardized API Gateway response"""
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body, default=serialize_datetime)
    }

def create_error_response(status_code, error_message, error_type="GeneralError"):
    """Create standardized error response"""
    return create_response(status_code, {
        'error': {
            'type': error_type,
            'message': error_message
        }
    })

def validate_required_fields(data, required_fields):
    """Validate that required fields are present in data"""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

def generate_plan_id():
    """Generate unique test plan ID"""
    import time
    import random
    timestamp = str(int(time.time()))
    random_num = str(random.randint(1000, 9999))
    return f"TP-{timestamp}-{random_num}"

def generate_case_id(test_plan_id):
    """Generate test case ID for a given test plan"""
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM test_cases 
            WHERE test_plan_id = (SELECT id FROM test_plans WHERE plan_id = %s)
            AND is_deleted = FALSE
        """, (test_plan_id,))
        
        result = cursor.fetchone()
        count = result['count'] if result else 0
        
        return f"TC-{str(count + 1).zfill(3)}"

def get_test_plan_by_plan_id(plan_id):
    """Get test plan internal ID by plan_id"""
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT id FROM test_plans 
            WHERE plan_id = %s AND is_deleted = FALSE
        """, (plan_id,))
        
        result = cursor.fetchone()
        return result['id'] if result else None

def handle_cors_preflight():
    """Handle CORS preflight requests"""
    return create_response(200, {}, {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    })

# SQL Queries Templates
QUERIES = {
    'get_test_plan_summary': """
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
            COUNT(tc.id) as test_cases_count
        FROM test_plans tp
        LEFT JOIN test_cases tc ON tp.id = tc.test_plan_id AND tc.is_deleted = FALSE
        WHERE tp.plan_id = %s AND tp.is_deleted = FALSE
        GROUP BY tp.id
    """,
    
    'get_test_cases_by_plan': """
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
            tc.updated_at,
            COUNT(ts.id) as steps_count
        FROM test_cases tc
        LEFT JOIN test_steps ts ON tc.id = ts.test_case_id
        WHERE tc.test_plan_id = %s AND tc.is_deleted = FALSE
        GROUP BY tc.id
        ORDER BY tc.case_order
    """,
    
    'get_test_steps_by_case': """
        SELECT 
            id,
            step_number,
            description,
            created_at,
            updated_at
        FROM test_steps
        WHERE test_case_id = %s
        ORDER BY step_number
    """,
    
    'get_chat_messages_by_plan': """
        SELECT 
            id,
            message_type,
            content,
            message_order,
            created_at
        FROM chat_messages
        WHERE test_plan_id = %s
        ORDER BY message_order
    """
}
