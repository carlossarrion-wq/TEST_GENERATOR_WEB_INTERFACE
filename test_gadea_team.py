"""
Test script to verify gadea team integration with OpenSearch
"""
import boto3
import json
import time

def test_gadea_team():
    """Test Lambda with gadea team"""
    
    print("="*80)
    print("Testing GADEA Team Integration")
    print("="*80)
    
    # Wait for Lambda to be ready
    print("\n⏳ Waiting 15 seconds for Lambda to be ready...")
    time.sleep(15)
    
    lambda_client = boto3.client('lambda', region_name='eu-west-1')
    
    payload = {
        "httpMethod": "POST",
        "body": json.dumps({
            "project_key": "GADEA-001",
            "functional_requirements": "Sistema de gestión de perfiles de usuario con creación, edición y validación de datos",
            "user_team": "gadea"
        })
    }
    
    try:
        print("\n🚀 Invoking Lambda with team: gadea")
        response = lambda_client.invoke(
            FunctionName='test-plan-generator-ai',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            body = json.loads(result.get('body', '{}'))
            
            print("\n" + "="*80)
            print("✅ RESULTADO")
            print("="*80)
            print(f"Status: {result.get('statusCode')}")
            print(f"Execution Time: {body.get('execution_time_seconds', 'N/A')}s")
            
            # OpenSearch info
            opensearch_info = body.get('opensearch_info', {})
            if opensearch_info:
                print(f"\n📚 OpenSearch Info:")
                print(f"   Team: {opensearch_info.get('team', 'N/A')}")
                print(f"   Indices Used: {opensearch_info.get('indices_used', [])}")
                print(f"   Documents Retrieved: {opensearch_info.get('insights_retrieved', 0)}")
            
            # Test cases
            test_cases = body.get('test_cases', [])
            print(f"\n📝 Test Cases Generated: {len(test_cases)}")
            
            # Quality
            quality_score = body.get('quality_score', 0)
            print(f"⭐ Quality Score: {quality_score}/100")
            
            # Save response
            with open('test_gadea_response.json', 'w', encoding='utf-8') as f:
                json.dump(body, f, indent=2, ensure_ascii=False)
            
            print("\n📄 Full response saved to: test_gadea_response.json")
            
            # Verify gadea index was used
            if opensearch_info.get('team') == 'gadea':
                indices_used = opensearch_info.get('indices_used', [])
                if 'rag-documents-gadea' in indices_used:
                    print("\n🎉 ¡SUCCESS! Gadea team is using the correct index!")
                    return True
                else:
                    print(f"\n⚠️  WARNING: Expected 'rag-documents-gadea' but got: {indices_used}")
                    return False
            else:
                print(f"\n⚠️  WARNING: Expected team 'gadea' but got: {opensearch_info.get('team')}")
                return False
        else:
            print(f"\n❌ Error: Status {result.get('statusCode')}")
            print(f"Message: {result.get('body', 'No message')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    import sys
    success = test_gadea_team()
    sys.exit(0 if success else 1)
