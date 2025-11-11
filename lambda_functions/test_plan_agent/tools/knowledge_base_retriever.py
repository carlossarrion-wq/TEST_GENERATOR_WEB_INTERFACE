"""
Knowledge Base Retriever Tool
Retrieves relevant information from AWS Knowledge Base
"""

import json
import boto3
from typing import Dict, Any, List

class KnowledgeBaseRetrieverTool:
    """Tool for retrieving information from Knowledge Base"""
    
    def __init__(self, bedrock_agent_client=None, bedrock_client=None, knowledge_base_id=None, model_id=None):
        self.name = "knowledge_retriever"
        self.description = """Retrieves relevant testing best practices and guidelines from the knowledge base.
Use this tool to get specialized insights about testing methodologies, patterns, and recommendations."""
        
        self.bedrock_agent_client = bedrock_agent_client or boto3.client('bedrock-agent-runtime', region_name='eu-west-1')
        self.bedrock_client = bedrock_client or boto3.client('bedrock-runtime', region_name='eu-west-1')
        self.knowledge_base_id = knowledge_base_id or 'VH6SRH9ZNO'
        self.model_id = model_id or 'eu.anthropic.claude-haiku-4-5-20251001-v1:0'
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge base retrieval"""
        try:
            query = input_data.get('query', '')
            max_results = input_data.get('max_results', 3)
            
            if not query:
                return {
                    "error": "No query provided",
                    "insights": []
                }
            
            # Retrieve from Knowledge Base (optimized: 3 results, 400 chars each)
            kb_response = self.bedrock_agent_client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': min(max_results, 3),
                        'overrideSearchType': 'HYBRID'
                    }
                }
            )
            
            insights = []
            if 'retrievalResults' in kb_response:
                for result in kb_response['retrievalResults'][:3]:
                    content = result.get('content', {}).get('text', '')
                    if content:
                        insights.append({
                            'content': content[:400],  # Limit to 400 chars
                            'score': result.get('score', 0),
                            'source': result.get('location', {}).get('s3Location', {}).get('uri', 'Unknown')
                        })
            
            return {
                "insights": insights,
                "total_retrieved": len(insights),
                "query": query
            }
            
        except Exception as e:
            print(f"KB retrieval error: {str(e)}")
            return {
                "error": str(e),
                "insights": [],
                "total_retrieved": 0
            }
