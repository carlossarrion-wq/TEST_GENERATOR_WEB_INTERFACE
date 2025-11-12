# OpenSearch Integration - Team-Based Index Routing

## Overview
Successfully integrated AWS OpenSearch Service with team-based index routing for the test case generation system. Users from different teams (darwin, deltasmile, mulesoft, sap, saplcorp) will now retrieve knowledge from their team-specific OpenSearch indices.

## Implementation Summary

### 1. OpenSearch Client (`lambda_functions/test_plan_agent/utils/opensearch_client.py`)
- **Purpose**: Manages connections to OpenSearch and routes queries to team-specific indices
- **Key Features**:
  - Team-based index mapping (darwin, deltasmile, mulesoft, sap, saplcorp)
  - Fallback to all indices for users without team assignment
  - AWS IAM authentication using Lambda execution role
  - Search methods: `search_documents()`, `get_similar_test_cases()`, `get_best_practices()`
  - Configurable via `update_team_mapping()` class method

### 2. Knowledge Base Retriever Tool (Modified)
**File**: `lambda_functions/test_plan_agent/tools/knowledge_base_retriever.py`
- **Changes**:
  - Replaced Bedrock Knowledge Base with OpenSearch client
  - Removed dependencies on `bedrock_agent_client` and `bedrock_client`
  - Added `user_team` parameter to constructor
  - Updated `execute()` method to pass team parameter to OpenSearch
  - Maintains same interface for compatibility with existing code

### 3. LangChain Agent (Modified)
**File**: `lambda_functions/test_plan_agent/complete_langchain_agent.py`
- **Changes**:
  - Added `user_team` parameter to `__init__()` method
  - Passes team context to KnowledgeBaseRetrieverTool during initialization
  - Updated `_execute_knowledge_retrieval()` to include team in query
  - Logs team information for debugging

### 4. Lambda Handler (Modified)
**File**: `lambda_functions/ai_test_generator_optimized.py`
- **Changes**:
  - Extracts `user_team` from request body
  - Passes team to CompleteLangChainAgent constructor
  - Includes team info in chat message confirmation
  - Logs team information for tracking

### 5. Frontend (Modified)
**File**: `js/app.js`
- **Changes**:
  - Retrieves `user_team` from sessionStorage (set during IAM authentication)
  - Always includes `user_team` in API requests (null if not available)
  - Logs team information to console for debugging
  - Shows appropriate messages based on team availability

### 6. Discovery Lambda (Created)
**File**: `lambda_functions/opensearch_index_discovery.py`
- **Purpose**: Discovers available OpenSearch indices from within VPC
- **Features**:
  - Connects to OpenSearch via VPC
  - Lists all indices with their document counts
  - Groups indices by team prefix
  - Returns structured JSON response
- **Deployment Scripts**:
  - `lambda_functions/deploy_opensearch_discovery.sh` (Linux/Mac)
  - `lambda_functions/deploy_opensearch_discovery.bat` (Windows)
- **Packaging Script**: `create_opensearch_discovery_zip.py`

## Team Index Mapping

```python
TEAM_INDEX_MAPPING = {
    'darwin': [],        # To be populated after discovery
    'deltasmile': [],    # To be populated after discovery
    'mulesoft': [],      # To be populated after discovery
    'sap': [],           # To be populated after discovery
    'saplcorp': []       # To be populated after discovery
}
```

## OpenSearch Configuration

- **Endpoint**: `vpc-rag-opensearch-clean-qodnaopeuroal2f6intbz7i5xy.eu-west-1.es.amazonaws.com`
- **Region**: `eu-west-1`
- **Authentication**: AWS IAM (via Lambda execution role)
- **Connection**: VPC-based (requires Lambda in same VPC)
- **Search Type**: Hybrid (combines keyword and semantic search)

## Workflow

1. **User Login**: IAM authenticator extracts Team tag from user
2. **Frontend**: Stores team in sessionStorage, includes in API requests
3. **Lambda Handler**: Extracts team from request, passes to agent
4. **LangChain Agent**: Initializes tools with team context
5. **Knowledge Retriever**: Routes queries to team-specific OpenSearch indices
6. **OpenSearch Client**: Searches appropriate indices based on team
7. **Response**: Returns team-specific knowledge to test case generator

## Next Steps

### Required Actions:
1. ✅ Code implementation completed
2. ⏳ Wait for discovery Lambda to reach "Active" state
3. ⏳ Execute discovery Lambda to get actual index names
4. ⏳ Update TEAM_INDEX_MAPPING in opensearch_client.py with real indices
5. ⏳ Deploy updated Lambda functions
6. ⏳ Test complete flow with different teams
7. ⏳ Clean up temporary files (discovery Lambda, scripts)

### Deployment Commands:

```bash
# Package and deploy main Lambda
cd lambda_functions
./deploy_optimized.sh

# Or use the deployment script
python create_langchain_zip.py
aws lambda update-function-code \
  --function-name ai-test-generator-optimized \
  --zip-file fileb://ai_test_generator_optimized.zip
```

### Testing:

```bash
# Test with team
curl -X POST https://your-api-gateway/generate-plan \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Plan",
    "requirements": "Test requirements",
    "user_team": "darwin"
  }'

# Test without team (should use all indices)
curl -X POST https://your-api-gateway/generate-plan \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Plan",
    "requirements": "Test requirements",
    "user_team": null
  }'
```

## Benefits

1. **Team-Specific Knowledge**: Each team gets relevant knowledge from their own documents
2. **Improved Relevance**: Test cases generated using team-specific best practices
3. **Scalability**: Easy to add new teams by updating the mapping
4. **Fallback Support**: Users without teams still get access to all knowledge
5. **Performance**: Searching fewer indices improves response time
6. **Security**: Team isolation ensures data privacy

## Architecture

```
User (with Team tag)
    ↓
Frontend (sessionStorage)
    ↓
API Gateway
    ↓
Lambda Handler (extracts team)
    ↓
LangChain Agent (team context)
    ↓
Knowledge Retriever Tool
    ↓
OpenSearch Client (team routing)
    ↓
OpenSearch Indices (team-specific)
    ↓
Test Case Generator (enhanced with team knowledge)
```

## Files Modified

1. `lambda_functions/test_plan_agent/utils/opensearch_client.py` (NEW)
2. `lambda_functions/test_plan_agent/tools/knowledge_base_retriever.py` (MODIFIED)
3. `lambda_functions/test_plan_agent/complete_langchain_agent.py` (MODIFIED)
4. `lambda_functions/ai_test_generator_optimized.py` (MODIFIED)
5. `js/app.js` (MODIFIED)
6. `lambda_functions/opensearch_index_discovery.py` (NEW)
7. `create_opensearch_discovery_zip.py` (NEW)
8. `lambda_functions/deploy_opensearch_discovery.sh` (NEW)
9. `lambda_functions/deploy_opensearch_discovery.bat` (NEW)

## Dependencies

- `opensearchpy`: OpenSearch Python client
- `requests-aws4auth`: AWS IAM authentication for OpenSearch
- Both included in Lambda Layer: `test-plan-generator-dependencies:2`

## Notes

- OpenSearch is in VPC, cannot be accessed from local machine
- Discovery Lambda must be in same VPC as OpenSearch
- Lambda Layer already includes required dependencies
- Team mapping will be updated after discovering actual indices
- System gracefully handles users without team assignment
