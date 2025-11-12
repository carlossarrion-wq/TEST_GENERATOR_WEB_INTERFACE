"""
Test script to verify OpenSearch integration with team-based indices
"""
import boto3
import json
import time

def test_lambda_with_team(team_name):
    """Test Lambda with a specific team"""
    
    print("\n" + "="*80)
    print(f"Testing with team: {team_name if team_name else 'NO TEAM (all indices)'}")
    print("="*80)
    
    lambda_client = boto3.client('lambda', region_name='eu-west-1')
    
    payload = {
        "httpMethod": "POST",
        "body": json.dumps({
            "project_key": "TEST-001",
            "functional_requirements": "Sistema de autenticación de usuarios con login y registro",
            "user_team": team_name
        })
    }
    
    try:
        print(f"🚀 Invoking Lambda...")
        response = lambda_client.invoke(
            FunctionName='test-plan-generator-ai',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            body = json.loads(result.get('body', '{}'))
            
            print(f"\n✅ Status: {result.get('statusCode')}")
            print(f"⏱️  Execution time: {body.get('execution_time', 'N/A')}")
            
            # Check OpenSearch info
            opensearch_info = body.get('opensearch_info', {})
            if opensearch_info:
                print(f"\n📚 OpenSearch Info:")
                print(f"   Team: {opensearch_info.get('team', 'N/A')}")
                print(f"   Indices searched: {opensearch_info.get('indices_searched', [])}")
                print(f"   Documents found: {opensearch_info.get('documents_found', 0)}")
                print(f"   Indices used: {opensearch_info.get('indices_used', [])}")
                print(f"   Query time: {opensearch_info.get('query_time', 'N/A')}")
            
            # Check test cases
            test_cases = body.get('test_cases', [])
            print(f"\n📝 Generated {len(test_cases)} test cases")
            
            # Check quality
            quality_score = body.get('quality_score', 0)
            print(f"⭐ Quality score: {quality_score}/100")
            
            return True
        else:
            print(f"\n❌ Error: {result}")
            return False
            
    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*80)
    print("OpenSearch Team-Based Index Testing")
    print("="*80)
    
    # Wait for Lambda to be ready after deployment
    print("\n⏳ Waiting 15 seconds for Lambda to be ready...")
    time.sleep(15)
    
    # Test with different teams
    teams_to_test = [
        'darwin',
        'deltasmile',
        'mulesoft',
        'sap',
        'saplcorp',
        None  # No team - should search all indices
    ]
    
    results = {}
    for team in teams_to_test:
        team_key = team if team else 'no_team'
        results[team_key] = test_lambda_with_team(team)
        time.sleep(2)  # Small delay between tests
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for team, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{team:15} : {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed")
    
    return all_passed

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
