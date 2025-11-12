"""
Lambda function to discover OpenSearch indices
This runs inside AWS VPC so it can access the OpenSearch cluster
"""

import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# OpenSearch configuration
OPENSEARCH_ENDPOINT = 'vpc-rag-opensearch-clean-qodnaopeuroal2f6intbz7i5xy.eu-west-1.es.amazonaws.com'
REGION = 'eu-west-1'

# Teams to map
TEAMS = ['darwin', 'deltasmile', 'mulesoft', 'sap', 'saplcorp']

def get_opensearch_client():
    """Create OpenSearch client with AWS authentication"""
    # Get AWS credentials from Lambda execution role
    session = boto3.Session()
    credentials = session.get_credentials()
    
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        REGION,
        'es',
        session_token=credentials.token
    )
    
    client = OpenSearch(
        hosts=[{'host': OPENSEARCH_ENDPOINT, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30
    )
    
    return client

def lambda_handler(event, context):
    """
    Lambda handler to discover OpenSearch indices
    """
    try:
        print("🔍 Connecting to OpenSearch from Lambda...")
        print(f"📡 Endpoint: {OPENSEARCH_ENDPOINT}")
        print(f"🌍 Region: {REGION}")
        
        client = get_opensearch_client()
        
        # Get all indices
        print("📋 Fetching all indices...")
        indices = client.cat.indices(format='json')
        
        print(f"✅ Found {len(indices)} total indices")
        
        # Filter out system indices (starting with .)
        index_names = []
        for idx in indices:
            index_name = idx['index']
            if not index_name.startswith('.'):
                index_names.append(index_name)
                print(f"  • {index_name}")
        
        print(f"\n📊 Total non-system indices: {len(index_names)}")
        
        # Map indices to teams
        team_mapping = {}
        for team in TEAMS:
            team_indices = [idx for idx in index_names if team.lower() in idx.lower()]
            team_mapping[team] = team_indices
            print(f"🏢 {team}: {len(team_indices)} indices")
        
        # Check for unassigned indices
        assigned_indices = set()
        for indices_list in team_mapping.values():
            assigned_indices.update(indices_list)
        
        unassigned = [idx for idx in index_names if idx not in assigned_indices]
        
        # Prepare response
        response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'opensearch_endpoint': OPENSEARCH_ENDPOINT,
                'region': REGION,
                'total_indices': len(index_names),
                'all_indices': index_names,
                'team_mapping': team_mapping,
                'unassigned_indices': unassigned,
                'summary': {
                    'darwin': len(team_mapping.get('darwin', [])),
                    'deltasmile': len(team_mapping.get('deltasmile', [])),
                    'mulesoft': len(team_mapping.get('mulesoft', [])),
                    'sap': len(team_mapping.get('sap', [])),
                    'saplcorp': len(team_mapping.get('saplcorp', []))
                }
            }, indent=2)
        }
        
        print("\n✅ Discovery completed successfully")
        return response
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            })
        }
