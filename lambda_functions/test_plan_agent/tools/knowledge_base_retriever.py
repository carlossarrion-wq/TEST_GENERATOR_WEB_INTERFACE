"""
Knowledge Base Retriever Tool
Retrieves relevant information from OpenSearch (team-based indices)
"""

import json
from typing import Dict, Any, List, Optional
from ..utils.opensearch_client import OpenSearchClient

class KnowledgeBaseRetrieverTool:
    """Tool for retrieving information from OpenSearch Knowledge Base"""
    
    def __init__(self, opensearch_client: Optional[OpenSearchClient] = None, user_team: Optional[str] = None):
        self.name = "knowledge_retriever"
        self.description = """Retrieves relevant testing best practices and guidelines from the team's knowledge base.
Use this tool to get specialized insights about testing methodologies, patterns, and recommendations specific to the team."""
        
        self.opensearch_client = opensearch_client or OpenSearchClient()
        self.user_team = user_team
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge base retrieval from OpenSearch"""
        try:
            query = input_data.get('query', '')
            max_results = input_data.get('max_results', 3)
            team = input_data.get('team', self.user_team)
            
            if not query:
                return {
                    "error": "No query provided",
                    "insights": []
                }
            
            print(f"🔍 Retrieving knowledge for team '{team}' with query: {query[:100]}...")
            
            # Retrieve from OpenSearch using team-specific indices
            search_results = self.opensearch_client.search_documents(
                query=query,
                team=team,
                max_results=min(max_results, 5),
                min_score=0.5
            )
            
            # Format results as insights
            insights = []
            indices_used = set()
            for result in search_results[:3]:  # Limit to top 3 results
                content = result.get('content', '')
                if content:
                    index_name = result.get('index', 'unknown')
                    indices_used.add(index_name)
                    insights.append({
                        'content': content[:400],  # Limit to 400 chars for optimization
                        'score': result.get('score', 0),
                        'source': f"{index_name}/{result.get('title', 'Unknown')}",
                        'title': result.get('title', ''),
                        'index': index_name
                    })
            
            print(f"✅ Retrieved {len(insights)} insights from OpenSearch")
            print(f"📚 Indices used: {list(indices_used)}")
            
            return {
                "insights": insights,
                "total_retrieved": len(insights),
                "query": query,
                "team": team,
                "indices_used": list(indices_used)  # Include indices in response
            }
            
        except Exception as e:
            print(f"❌ OpenSearch retrieval error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "insights": [],
                "total_retrieved": 0
            }
