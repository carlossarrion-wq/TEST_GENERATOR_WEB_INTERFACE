"""
Lambda Function: Jira Integration
Fetches real Jira issues from Atlassian API based on user's team project
"""

import json
import os
import boto3
import requests
from requests.auth import HTTPBasicAuth
from botocore.exceptions import ClientError

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager', region_name='eu-west-1')

def get_jira_credentials():
    """
    Retrieve Jira credentials from AWS Secrets Manager
    """
    secret_name = os.environ.get('JIRA_SECRET_NAME', 'prod/jira/credentials')
    
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        
        return {
            'url': secret.get('jiraUrl', 'https://csarrion.atlassian.net'),
            'email': secret.get('jiraEmail'),
            'api_token': secret.get('jiraApiToken')
        }
    except ClientError as e:
        print(f"Error retrieving Jira credentials: {e}")
        raise Exception("Failed to retrieve Jira credentials from Secrets Manager")

def extract_text_from_adf(adf_content):
    """
    Extract plain text from Atlassian Document Format (ADF)
    
    Args:
        adf_content: ADF content (dict or string)
    
    Returns:
        Plain text string
    """
    if not adf_content:
        return 'No description provided'
    
    # If it's already a string, return it
    if isinstance(adf_content, str):
        return adf_content
    
    # If it's not a dict, convert to string
    if not isinstance(adf_content, dict):
        return str(adf_content)
    
    # Extract text from ADF structure
    def extract_text_recursive(node):
        if not isinstance(node, dict):
            return ''
        
        text_parts = []
        
        # If node has text, add it
        if 'text' in node:
            text_parts.append(node['text'])
        
        # Process content array recursively
        if 'content' in node and isinstance(node['content'], list):
            for child in node['content']:
                child_text = extract_text_recursive(child)
                if child_text:
                    text_parts.append(child_text)
        
        return ' '.join(text_parts)
    
    extracted_text = extract_text_recursive(adf_content)
    return extracted_text.strip() if extracted_text else 'No description provided'

def fetch_jira_issues(project_key, credentials, max_results=50):
    """
    Fetch issues from Jira using REST API
    
    Args:
        project_key: Jira project key (e.g., 'GAESTG', 'ICACEP')
        credentials: Dict with url, email, api_token
        max_results: Maximum number of issues to fetch
    
    Returns:
        List of issues with relevant fields
    """
    jira_url = credentials['url']
    auth = HTTPBasicAuth(credentials['email'], credentials['api_token'])
    
    # JQL query to get issues from the project
    jql = f'project = {project_key} ORDER BY updated DESC'
    
    # API endpoint - Using the new JQL search API
    search_url = f"{jira_url}/rest/api/3/search/jql"
    
    # Request body (POST request)
    payload = {
        'jql': jql,
        'maxResults': max_results,
        'fields': ['summary', 'description', 'issuetype', 'status', 'priority', 'assignee', 'labels', 'created', 'updated']
    }
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"Fetching issues from Jira project: {project_key}")
        response = requests.post(search_url, json=payload, headers=headers, auth=auth, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        issues = data.get('issues', [])
        
        print(f"Successfully fetched {len(issues)} issues from {project_key}")
        
        # Transform issues to simplified format
        transformed_issues = []
        for issue in issues:
            fields = issue.get('fields', {})
            
            # Get assignee name
            assignee = fields.get('assignee')
            assignee_name = 'Unassigned'
            if assignee:
                assignee_name = assignee.get('displayName', 'Unassigned')
            
            # Get issue type
            issue_type = fields.get('issuetype', {})
            type_name = issue_type.get('name', 'Task').lower()
            
            # Get status
            status = fields.get('status', {})
            status_name = status.get('name', 'To Do')
            
            # Get priority
            priority = fields.get('priority', {})
            priority_name = priority.get('name', 'Medium')
            
            # Extract description text from ADF format
            description_raw = fields.get('description')
            description_text = extract_text_from_adf(description_raw)
            
            transformed_issue = {
                'key': issue.get('key'),
                'type': type_name,
                'summary': fields.get('summary', ''),
                'description': description_text,
                'status': status_name,
                'priority': priority_name,
                'assignee': assignee_name,
                'labels': fields.get('labels', []),
                'created': fields.get('created', ''),
                'updated': fields.get('updated', '')
            }
            
            transformed_issues.append(transformed_issue)
        
        return transformed_issues
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Jira issues: {e}")
        raise Exception(f"Failed to fetch issues from Jira: {str(e)}")

def lambda_handler(event, context):
    """
    Lambda handler for Jira integration
    
    Expected event structure:
    {
        "team": "darwin" | "mulesoft" | "sap" | "saplcorp",
        "maxResults": 50 (optional)
    }
    """
    
    # Enhanced CORS headers for better compatibility
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token,Accept',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
        'Access-Control-Max-Age': '86400',
        'Content-Type': 'application/json'
    }
    
    # Handle OPTIONS request for CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        print("Handling CORS preflight request")
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'CORS preflight successful'})
        }
    
    # Log the incoming request for debugging
    print(f"Received request: {json.dumps(event, default=str)}")
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        team = body.get('team')
        max_results = body.get('maxResults', 50)
        
        # Validate team parameter
        if not team:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Missing required parameter: team'
                })
            }
        
        # Map team to Jira project key
        team_project_mapping = {
            'darwin': 'GAESTG',
            'mulesoft': 'ICACEP',
            'sap': 'RE',
            'saplcorp': 'PDDSE2'
        }
        
        project_key = team_project_mapping.get(team.lower())
        
        if not project_key:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': f'Invalid team: {team}. Valid teams: darwin, mulesoft, sap, saplcorp'
                })
            }
        
        # Get Jira credentials
        credentials = get_jira_credentials()
        
        # Fetch issues from Jira
        issues = fetch_jira_issues(project_key, credentials, max_results)
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'team': team,
                'project_key': project_key,
                'issues': issues,
                'total_count': len(issues)
            })
        }
        
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': str(e),
                'message': 'Internal server error'
            })
        }
