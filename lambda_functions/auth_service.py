"""
Authentication Service Lambda Function
Handles AWS Access Key/Secret Key authentication using real AWS STS validation
"""

import json
import hmac
import hashlib
import time
import base64
import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from db_utils import (
    DatabaseConnection, create_response, create_error_response,
    validate_required_fields, handle_cors_preflight
)

# Configuration
SESSION_DURATION = 3600 * 8  # 8 hours in seconds
SECRET_KEY = os.environ.get('AUTH_SECRET_KEY', 'your-secret-key-here')  # Should be set in Lambda environment

def lambda_handler(event, context):
    """Main Lambda handler for authentication operations"""
    
    # Handle CORS preflight requests
    if event['httpMethod'] == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        method = event['httpMethod']
        path = event.get('path', '')
        
        if method == 'POST':
            body = json.loads(event['body']) if event['body'] else {}
            
            if '/auth/login' in path:
                return authenticate_user(body)
            elif '/auth/validate' in path:
                return validate_session(body)
            elif '/auth/refresh' in path:
                return refresh_session(body)
            else:
                return create_error_response(404, "Authentication endpoint not found", "NotFound")
        
        elif method == 'DELETE':
            if '/auth/logout' in path:
                body = json.loads(event['body']) if event['body'] else {}
                return logout_user(body)
            else:
                return create_error_response(404, "Authentication endpoint not found", "NotFound")
        
        else:
            return create_error_response(405, f"Method {method} not allowed", "MethodNotAllowed")
    
    except json.JSONDecodeError:
        return create_error_response(400, "Invalid JSON in request body", "JSONDecodeError")
    except Exception as e:
        print(f"Unexpected error in auth service: {str(e)}")
        return create_error_response(500, "Internal server error", "InternalServerError")

def authenticate_user(data):
    """Authenticate user with real AWS Access Key and Secret Key"""
    try:
        # Validate required fields
        required_fields = ['access_key', 'secret_key']
        validate_required_fields(data, required_fields)
        
        access_key = data['access_key'].strip()
        secret_key = data['secret_key'].strip()
        
        # Validate AWS credentials by calling STS get-caller-identity
        aws_user_info = validate_aws_credentials(access_key, secret_key)
        if not aws_user_info:
            return create_error_response(401, "Invalid AWS Access Key or Secret Key", "AuthenticationError")
        
        with DatabaseConnection() as cursor:
            # Check if user exists in our system (by access key)
            cursor.execute("""
                SELECT id, access_key, is_active, last_login_at, 
                       created_at, updated_at, permissions
                FROM auth_users 
                WHERE access_key = %s AND is_deleted = FALSE
            """, (access_key,))
            
            user = cursor.fetchone()
            
            # If user doesn't exist, create a new one with default permissions
            if not user:
                print(f"Creating new user for AWS Access Key: {access_key}")
                cursor.execute("""
                    INSERT INTO auth_users (access_key, secret_key_hash, permissions, is_active)
                    VALUES (%s, %s, %s, %s)
                """, (
                    access_key,
                    'AWS_VALIDATED',  # We don't store the secret key, just mark as AWS validated
                    '["test_plans:read", "test_plans:write", "test_cases:read", "test_cases:write", "ai:generate"]',
                    True
                ))
                
                user_id = cursor.lastrowid
                
                # Get the newly created user
                cursor.execute("""
                    SELECT id, access_key, is_active, last_login_at, 
                           created_at, updated_at, permissions
                    FROM auth_users 
                    WHERE id = %s
                """, (user_id,))
                
                user = cursor.fetchone()
            
            if not user['is_active']:
                return create_error_response(401, "Account is deactivated", "AuthenticationError")
            
            # Generate session token
            session_token = generate_session_token(user['id'], access_key)
            expires_at = int(time.time()) + SESSION_DURATION
            
            # Store session in database
            cursor.execute("""
                INSERT INTO auth_sessions (user_id, session_token, expires_at, created_at)
                VALUES (%s, %s, FROM_UNIXTIME(%s), CURRENT_TIMESTAMP)
                ON DUPLICATE KEY UPDATE 
                    session_token = VALUES(session_token),
                    expires_at = VALUES(expires_at),
                    updated_at = CURRENT_TIMESTAMP
            """, (user['id'], session_token, expires_at))
            
            # Update last login time
            cursor.execute("""
                UPDATE auth_users 
                SET last_login_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (user['id'],))
            
            # Parse permissions
            permissions = []
            if user['permissions']:
                try:
                    permissions = json.loads(user['permissions'])
                except json.JSONDecodeError:
                    permissions = ["test_plans:read", "test_plans:write", "test_cases:read", "test_cases:write", "ai:generate"]
            
            return create_response(200, {
                'message': 'Authentication successful',
                'session_token': session_token,
                'expires_at': expires_at,
                'expires_in': SESSION_DURATION,
                'user': {
                    'id': user['id'],
                    'access_key': user['access_key'],
                    'permissions': permissions,
                    'aws_user_info': aws_user_info,
                    'last_login_at': user['last_login_at'].isoformat() if user['last_login_at'] else None
                }
            })
    
    except ValueError as e:
        return create_error_response(400, str(e), "ValidationError")
    except Exception as e:
        print(f"Error during authentication: {str(e)}")
        return create_error_response(500, "Authentication error", "AuthenticationError")

def validate_aws_credentials(access_key, secret_key):
    """
    Validate AWS credentials by calling STS get-caller-identity
    Returns user info if valid, None if invalid
    """
    try:
        # Create boto3 STS client with provided credentials
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='us-east-1'  # STS is available in all regions, use us-east-1 as default
        )
        
        # Try to get caller identity - this will fail if credentials are invalid
        response = sts_client.get_caller_identity()
        
        # If we get here, credentials are valid
        return {
            'user_id': response.get('UserId'),
            'account': response.get('Account'),
            'arn': response.get('Arn')
        }
        
    except ClientError as e:
        # Invalid credentials or other AWS error
        error_code = e.response['Error']['Code']
        print(f"AWS credentials validation failed: {error_code} - {e.response['Error']['Message']}")
        return None
        
    except NoCredentialsError:
        print("No AWS credentials provided")
        return None
        
    except Exception as e:
        print(f"Unexpected error validating AWS credentials: {str(e)}")
        return None

def validate_session(data):
    """Validate a session token"""
    try:
        # Validate required fields
        required_fields = ['session_token']
        validate_required_fields(data, required_fields)
        
        session_token = data['session_token']
        
        with DatabaseConnection() as cursor:
            # Get session and user info
            cursor.execute("""
                SELECT s.id, s.user_id, s.expires_at, u.access_key, u.is_active, u.permissions
                FROM auth_sessions s
                JOIN auth_users u ON s.user_id = u.id
                WHERE s.session_token = %s AND u.is_deleted = FALSE
            """, (session_token,))
            
            session = cursor.fetchone()
            
            if not session:
                return create_error_response(401, "Invalid session token", "AuthenticationError")
            
            if not session['is_active']:
                return create_error_response(401, "Account is deactivated", "AuthenticationError")
            
            # Check if session is expired
            current_time = int(time.time())
            expires_at = int(session['expires_at'].timestamp())
            
            if current_time > expires_at:
                # Clean up expired session
                cursor.execute("DELETE FROM auth_sessions WHERE id = %s", (session['id'],))
                return create_error_response(401, "Session expired", "SessionExpired")
            
            # Parse permissions
            permissions = []
            if session['permissions']:
                try:
                    permissions = json.loads(session['permissions'])
                except json.JSONDecodeError:
                    permissions = []
            
            return create_response(200, {
                'valid': True,
                'expires_at': expires_at,
                'expires_in': expires_at - current_time,
                'user': {
                    'id': session['user_id'],
                    'access_key': session['access_key'],
                    'permissions': permissions
                }
            })
    
    except ValueError as e:
        return create_error_response(400, str(e), "ValidationError")
    except Exception as e:
        print(f"Error validating session: {str(e)}")
        return create_error_response(500, "Session validation error", "AuthenticationError")

def refresh_session(data):
    """Refresh an existing session"""
    try:
        # Validate required fields
        required_fields = ['session_token']
        validate_required_fields(data, required_fields)
        
        session_token = data['session_token']
        
        with DatabaseConnection() as cursor:
            # Get session and user info
            cursor.execute("""
                SELECT s.id, s.user_id, s.expires_at, u.access_key, u.is_active
                FROM auth_sessions s
                JOIN auth_users u ON s.user_id = u.id
                WHERE s.session_token = %s AND u.is_deleted = FALSE
            """, (session_token,))
            
            session = cursor.fetchone()
            
            if not session:
                return create_error_response(401, "Invalid session token", "AuthenticationError")
            
            if not session['is_active']:
                return create_error_response(401, "Account is deactivated", "AuthenticationError")
            
            # Check if session is expired
            current_time = int(time.time())
            expires_at = int(session['expires_at'].timestamp())
            
            if current_time > expires_at:
                # Clean up expired session
                cursor.execute("DELETE FROM auth_sessions WHERE id = %s", (session['id'],))
                return create_error_response(401, "Session expired", "SessionExpired")
            
            # Generate new session token and extend expiration
            new_session_token = generate_session_token(session['user_id'], session['access_key'])
            new_expires_at = current_time + SESSION_DURATION
            
            # Update session
            cursor.execute("""
                UPDATE auth_sessions 
                SET session_token = %s, expires_at = FROM_UNIXTIME(%s), updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_session_token, new_expires_at, session['id']))
            
            return create_response(200, {
                'message': 'Session refreshed successfully',
                'session_token': new_session_token,
                'expires_at': new_expires_at,
                'expires_in': SESSION_DURATION
            })
    
    except ValueError as e:
        return create_error_response(400, str(e), "ValidationError")
    except Exception as e:
        print(f"Error refreshing session: {str(e)}")
        return create_error_response(500, "Session refresh error", "AuthenticationError")

def logout_user(data):
    """Logout user and invalidate session"""
    try:
        # Validate required fields
        required_fields = ['session_token']
        validate_required_fields(data, required_fields)
        
        session_token = data['session_token']
        
        with DatabaseConnection() as cursor:
            # Delete session
            cursor.execute("DELETE FROM auth_sessions WHERE session_token = %s", (session_token,))
            
            return create_response(200, {
                'message': 'Logged out successfully'
            })
    
    except ValueError as e:
        return create_error_response(400, str(e), "ValidationError")
    except Exception as e:
        print(f"Error during logout: {str(e)}")
        return create_error_response(500, "Logout error", "AuthenticationError")

def generate_session_token(user_id, access_key):
    """Generate a secure session token"""
    timestamp = str(int(time.time()))
    data = f"{user_id}:{access_key}:{timestamp}"
    
    # Create HMAC signature
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Combine data and signature
    token_data = f"{data}:{signature}"
    
    # Base64 encode for safe transport
    return base64.b64encode(token_data.encode('utf-8')).decode('utf-8')

def verify_secret_key(provided_key, stored_hash):
    """Verify secret key against stored hash"""
    # Hash the provided key
    provided_hash = hashlib.sha256(provided_key.encode('utf-8')).hexdigest()
    
    # Compare hashes
    return hmac.compare_digest(provided_hash, stored_hash)

def hash_secret_key(secret_key):
    """Hash a secret key for storage (utility function)"""
    return hashlib.sha256(secret_key.encode('utf-8')).hexdigest()

# Authentication middleware function for other Lambda functions
def validate_request_auth(event):
    """
    Validate authentication for incoming requests
    To be imported and used by other Lambda functions
    
    Returns: (is_valid, user_info, error_response)
    """
    try:
        # Get session token from headers
        headers = event.get('headers', {})
        auth_header = headers.get('Authorization', '') or headers.get('authorization', '')
        
        if not auth_header:
            return False, None, create_error_response(401, "Authorization header required", "AuthenticationError")
        
        # Extract token (format: "Bearer <token>")
        if not auth_header.startswith('Bearer '):
            return False, None, create_error_response(401, "Invalid authorization format", "AuthenticationError")
        
        session_token = auth_header[7:]  # Remove "Bearer " prefix
        
        with DatabaseConnection() as cursor:
            # Get session and user info
            cursor.execute("""
                SELECT s.id, s.user_id, s.expires_at, u.access_key, u.is_active, u.permissions
                FROM auth_sessions s
                JOIN auth_users u ON s.user_id = u.id
                WHERE s.session_token = %s AND u.is_deleted = FALSE
            """, (session_token,))
            
            session = cursor.fetchone()
            
            if not session:
                return False, None, create_error_response(401, "Invalid session token", "AuthenticationError")
            
            if not session['is_active']:
                return False, None, create_error_response(401, "Account is deactivated", "AuthenticationError")
            
            # Check if session is expired
            current_time = int(time.time())
            expires_at = int(session['expires_at'].timestamp())
            
            if current_time > expires_at:
                # Clean up expired session
                cursor.execute("DELETE FROM auth_sessions WHERE id = %s", (session['id'],))
                return False, None, create_error_response(401, "Session expired", "SessionExpired")
            
            # Parse permissions
            permissions = []
            if session['permissions']:
                try:
                    permissions = json.loads(session['permissions'])
                except json.JSONDecodeError:
                    permissions = []
            
            user_info = {
                'id': session['user_id'],
                'access_key': session['access_key'],
                'permissions': permissions
            }
            
            return True, user_info, None
    
    except Exception as e:
        print(f"Error validating request auth: {str(e)}")
        return False, None, create_error_response(500, "Authentication validation error", "AuthenticationError")
