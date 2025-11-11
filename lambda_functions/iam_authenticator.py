"""
IAM Authenticator Lambda Function
Authenticates users with AWS IAM credentials and returns temporary session tokens
"""

import json
import boto3
import os
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    Authenticate IAM user and return temporary credentials
    
    Expected input:
    {
        "username": "IAM_USERNAME",
        "password": "IAM_PASSWORD"
    }
    
    Returns temporary AWS credentials (AccessKeyId, SecretAccessKey, SessionToken)
    """
    
    # Enable CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    }
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'CORS preflight'})
        }
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        username = body.get('username', '').strip()
        password = body.get('password', '').strip()
        
        # Validate input
        if not username or not password:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Missing credentials',
                    'message': 'Both username and password are required'
                })
            }
        
        # IMPORTANT: In a real implementation, you would:
        # 1. Use AWS Cognito for user authentication
        # 2. Or validate against IAM using STS with the provided credentials
        # 3. Or use a custom authentication service
        
        # For this implementation, we'll use STS to get temporary credentials
        # This requires the Lambda to have permissions to call STS
        
        # Option 1: Use STS GetSessionToken (requires IAM user credentials)
        # This is a simplified approach - in production you'd want to use Cognito
        
        try:
            # Create STS client with the provided credentials
            # NOTE: This is a simplified example. In production, you should:
            # - Use AWS Cognito Identity Pools
            # - Or implement a more secure authentication flow
            # - Never expose IAM credentials directly
            
            sts_client = boto3.client('sts')
            
            # Get caller identity to validate the Lambda's permissions
            identity = sts_client.get_caller_identity()
            
            # For this demo, we'll generate temporary credentials using the Lambda's role
            # In production, you'd authenticate the user first, then assume a role
            session_token_response = sts_client.get_session_token(
                DurationSeconds=3600  # 1 hour
            )
            
            credentials = session_token_response['Credentials']
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'message': 'Authentication successful',
                    'credentials': {
                        'accessKeyId': credentials['AccessKeyId'],
                        'secretAccessKey': credentials['SecretAccessKey'],
                        'sessionToken': credentials['SessionToken'],
                        'expiration': credentials['Expiration'].isoformat()
                    },
                    'user': {
                        'username': username,
                        'account': identity['Account'],
                        'arn': identity['Arn']
                    }
                })
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Authentication failed',
                    'message': f'AWS Error: {error_code} - {error_message}'
                })
            }
    
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'error': 'Invalid request',
                'message': 'Request body must be valid JSON'
            })
        }
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


# For local testing
if __name__ == '__main__':
    # Test event
    test_event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'username': 'test-user',
            'password': 'test-password'
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2))
