"""
Script to discover OpenSearch indices and map them to teams
"""

import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# OpenSearch configuration
OPENSEARCH_ENDPOINT = 'vpc-rag-opensearch-clean-qodnaopeuroal2f6intbz7i5xy.eu-west-1.es.amazonaws.com'
REGION = 'eu-west-1'

# Teams
TEAMS = ['darwin', 'deltasmile', 'mulesoft', 'sap', 'saplcorp']

def get_opensearch_client():
    """Create OpenSearch client with AWS authentication"""
    # Get AWS credentials
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

def discover_indices():
    """Discover all indices in OpenSearch"""
    try:
        print("🔍 Connecting to OpenSearch...")
        client = get_opensearch_client()
        
        print(f"📡 Endpoint: {OPENSEARCH_ENDPOINT}")
        print(f"🌍 Region: {REGION}\n")
        
        # Get all indices
        print("📋 Fetching all indices...")
        indices = client.cat.indices(format='json')
        
        print(f"✅ Found {len(indices)} indices\n")
        print("=" * 80)
        print("ALL INDICES:")
        print("=" * 80)
        
        index_names = []
        for idx in indices:
            index_name = idx['index']
            # Skip system indices (starting with .)
            if not index_name.startswith('.'):
                index_names.append(index_name)
                print(f"  • {index_name}")
        
        print(f"\n📊 Total non-system indices: {len(index_names)}\n")
        
        # Map indices to teams
        print("=" * 80)
        print("TEAM → INDICES MAPPING:")
        print("=" * 80)
        
        team_mapping = {}
        
        for team in TEAMS:
            team_indices = [idx for idx in index_names if team.lower() in idx.lower()]
            team_mapping[team] = team_indices
            
            print(f"\n🏢 {team.upper()}:")
            if team_indices:
                for idx in team_indices:
                    print(f"  ✓ {idx}")
            else:
                print(f"  ⚠️  No indices found")
        
        # Check for unassigned indices
        assigned_indices = set()
        for indices_list in team_mapping.values():
            assigned_indices.update(indices_list)
        
        unassigned = [idx for idx in index_names if idx not in assigned_indices]
        
        if unassigned:
            print(f"\n⚠️  UNASSIGNED INDICES:")
            for idx in unassigned:
                print(f"  • {idx}")
        
        # Generate Python code for mapping
        print("\n" + "=" * 80)
        print("PYTHON CODE FOR MAPPING:")
        print("=" * 80)
        print("\nTEAM_INDEX_MAPPING = {")
        for team, indices_list in team_mapping.items():
            if indices_list:
                print(f"    '{team}': {indices_list},")
            else:
                print(f"    '{team}': [],  # No indices found")
        print("}")
        
        # Save to JSON file
        output = {
            'opensearch_endpoint': OPENSEARCH_ENDPOINT,
            'region': REGION,
            'total_indices': len(index_names),
            'all_indices': index_names,
            'team_mapping': team_mapping,
            'unassigned_indices': unassigned
        }
        
        with open('opensearch_indices_mapping.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Mapping saved to: opensearch_indices_mapping.json")
        
        return team_mapping
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    print("🚀 OpenSearch Indices Discovery Tool\n")
    discover_indices()
