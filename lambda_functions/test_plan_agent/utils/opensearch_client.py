"""
OpenSearch Client for Team-Based Index Access
Connects to OpenSearch and retrieves documents from team-specific indices
"""

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from typing import List, Dict, Any, Optional

class OpenSearchClient:
    """
    Client for accessing OpenSearch with team-based index routing
    """
    
    # OpenSearch configuration
    OPENSEARCH_ENDPOINT = 'vpc-rag-opensearch-clean-qodnaopeuroal2f6intbz7i5xy.eu-west-1.es.amazonaws.com'
    REGION = 'eu-west-1'
    
    # Team to index mapping
    # Discovered from OpenSearch cluster
    TEAM_INDEX_MAPPING = {
        'darwin': ['rag-documents-darwin'],
        'deltasmile': ['rag-documents-deltasmile'],
        'mulesoft': ['rag-documents-mulesoft'],
        'sap': ['rag-documents-sap', 'rag-documents-sapv2', 'rag-documents-saplcorp'],
        'saplcorp': ['rag-documents-saplcorp']
    }
    
    # All indices for users without team (general search across all team indices)
    ALL_TEAM_INDICES = [
        'rag-documents-darwin',
        'rag-documents-deltasmile', 
        'rag-documents-mulesoft',
        'rag-documents-sap',
        'rag-documents-sapv2',
        'rag-documents-saplcorp',
        'rag-documents',  # General index
        'rag-documents-gadea',
        'rag-documents-pds'
    ]
    
    def __init__(self):
        """Initialize OpenSearch client"""
        self.client = self._create_client()
    
    def _create_client(self) -> OpenSearch:
        """Create authenticated OpenSearch client"""
        # Get AWS credentials from Lambda execution role
        session = boto3.Session()
        credentials = session.get_credentials()
        
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            self.REGION,
            'es',
            session_token=credentials.token
        )
        
        client = OpenSearch(
            hosts=[{'host': self.OPENSEARCH_ENDPOINT, 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=3,  # Reduced to 3s to fail fast
            max_retries=0  # No retries
        )
        
        return client
    
    def get_indices_for_team(self, team: Optional[str]) -> List[str]:
        """
        Get the appropriate indices for a team
        
        Args:
            team: Team name (darwin, deltasmile, etc.) or None
            
        Returns:
            List of index names to search
        """
        if not team or team not in self.TEAM_INDEX_MAPPING:
            # User has no team or team not recognized
            # Return all indices (general search across all documents)
            return self.ALL_TEAM_INDICES
        
        # Return team-specific indices
        team_indices = self.TEAM_INDEX_MAPPING.get(team, [])
        return team_indices if team_indices else self.ALL_TEAM_INDICES
    
    def search_documents(
        self, 
        query: str, 
        team: Optional[str] = None,
        max_results: int = 5,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents in team-specific indices
        
        Args:
            query: Search query (e.g., requirements text)
            team: Team name for index selection
            max_results: Maximum number of results to return
            min_score: Minimum relevance score (0-1)
            
        Returns:
            List of relevant documents with their content and metadata
        """
        try:
            # Get indices for this team
            indices = self.get_indices_for_team(team)
            
            if not indices:
                print(f"⚠️ No indices found for team: {team}")
                return []
            
            # Detailed logging for verification
            print("=" * 80)
            print("🔍 OPENSEARCH QUERY DETAILS")
            print("=" * 80)
            print(f"👥 Team: {team if team else 'NO TEAM (using all indices)'}")
            print(f"📚 Indices to search: {indices}")
            print(f"📝 Query: {query[:100]}...")
            print(f"🎯 Max results: {max_results}")
            print(f"⭐ Min score: {min_score}")
            print("=" * 80)
            
            # Build search query
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["content^2", "title", "description"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                "size": max_results,
                "min_score": min_score,
                "_source": ["content", "title", "description", "metadata"]
            }
            
            # Execute search across team indices
            response = self.client.search(
                index=','.join(indices),  # Search across multiple indices
                body=search_body
            )
            
            # Extract and format results
            results = []
            indices_used = set()
            for hit in response['hits']['hits']:
                result = {
                    'score': hit['_score'],
                    'index': hit['_index'],
                    'content': hit['_source'].get('content', ''),
                    'title': hit['_source'].get('title', ''),
                    'description': hit['_source'].get('description', ''),
                    'metadata': hit['_source'].get('metadata', {})
                }
                results.append(result)
                indices_used.add(hit['_index'])
            
            # Detailed results logging
            print("=" * 80)
            print("✅ OPENSEARCH RESULTS")
            print("=" * 80)
            print(f"📊 Total documents found: {len(results)}")
            print(f"📚 Indices that returned results: {list(indices_used)}")
            print(f"📈 Score range: {min([r['score'] for r in results]) if results else 0:.2f} - {max([r['score'] for r in results]) if results else 0:.2f}")
            
            # Show which index each result came from
            for i, result in enumerate(results[:3], 1):  # Show top 3
                print(f"\n   Result {i}:")
                print(f"   └─ Index: {result['index']}")
                print(f"   └─ Score: {result['score']:.2f}")
                print(f"   └─ Title: {result['title'][:60]}...")
            
            if len(results) > 3:
                print(f"\n   ... and {len(results) - 3} more results")
            
            print("=" * 80)
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching OpenSearch: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_similar_test_cases(
        self,
        requirements: str,
        team: Optional[str] = None,
        max_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get similar test cases from team's knowledge base
        
        Args:
            requirements: Functional requirements text
            team: Team name
            max_results: Maximum number of similar cases to return
            
        Returns:
            List of similar test cases with their details
        """
        # Search for similar test cases
        results = self.search_documents(
            query=requirements,
            team=team,
            max_results=max_results,
            min_score=0.6  # Higher threshold for test cases
        )
        
        # Filter and format test case results
        test_cases = []
        for result in results:
            # Check if document is a test case
            if 'test' in result.get('title', '').lower() or \
               'test' in result.get('content', '').lower():
                test_cases.append({
                    'title': result['title'],
                    'content': result['content'],
                    'relevance_score': result['score'],
                    'source_index': result['index']
                })
        
        return test_cases
    
    def get_best_practices(
        self,
        topic: str,
        team: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get best practices from team's knowledge base
        
        Args:
            topic: Topic to search for (e.g., "testing", "quality")
            team: Team name
            max_results: Maximum number of practices to return
            
        Returns:
            List of best practices
        """
        # Search for best practices
        results = self.search_documents(
            query=f"best practices {topic}",
            team=team,
            max_results=max_results,
            min_score=0.5
        )
        
        return [{
            'title': r['title'],
            'content': r['content'],
            'relevance': r['score']
        } for r in results]
    
    @classmethod
    def update_team_mapping(cls, team_mapping: Dict[str, List[str]]):
        """
        Update the team to index mapping
        
        Args:
            team_mapping: Dictionary mapping team names to their indices
        """
        cls.TEAM_INDEX_MAPPING = team_mapping
        print(f"✅ Updated team index mapping: {team_mapping}")
