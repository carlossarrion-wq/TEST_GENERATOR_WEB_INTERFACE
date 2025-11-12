"""
Script to invoke the OpenSearch index discovery Lambda
"""
import boto3
import json
import time

def invoke_discovery_lambda():
    """Invoke the discovery Lambda and display results"""
    
    # Wait a bit for Lambda to be ready
    print("⏳ Waiting 10 seconds for Lambda to be ready...")
    time.sleep(10)
    
    print("🚀 Invoking OpenSearch index discovery Lambda...")
    
    lambda_client = boto3.client('lambda', region_name='eu-west-1')
    
    try:
        response = lambda_client.invoke(
            FunctionName='opensearch-index-discovery',
            InvocationType='RequestResponse'
        )
        
        # Read response
        payload = json.loads(response['Payload'].read())
        
        # Save to file
        with open('opensearch_discovery_output.json', 'w') as f:
            json.dump(payload, f, indent=2)
        
        print("\n" + "="*80)
        print("✅ DISCOVERY RESULTS")
        print("="*80)
        
        if response['StatusCode'] == 200:
            body = json.loads(payload.get('body', '{}'))
            
            if body.get('success'):
                print(f"\n📊 Total indices found: {body['total_indices']}")
                print(f"\n📚 All indices:")
                for idx in body['all_indices']:
                    print(f"  • {idx}")
                
                print(f"\n🏢 Team mapping:")
                for team, indices in body['team_mapping'].items():
                    print(f"  {team}: {len(indices)} indices")
                    for idx in indices:
                        print(f"    - {idx}")
                
                if body['unassigned_indices']:
                    print(f"\n⚠️  Unassigned indices (not matched to any team):")
                    for idx in body['unassigned_indices']:
                        print(f"  • {idx}")
                
                print("\n" + "="*80)
                print("✅ Discovery completed successfully!")
                print("="*80)
                
                return body
            else:
                print(f"\n❌ Error: {body.get('error')}")
                print(f"Error type: {body.get('error_type')}")
                return None
        else:
            print(f"\n❌ Lambda invocation failed with status: {response['StatusCode']}")
            return None
            
    except Exception as e:
        print(f"\n❌ Error invoking Lambda: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    result = invoke_discovery_lambda()
    
    if result:
        print("\n📝 Results saved to: opensearch_discovery_output.json")
    else:
        print("\n⚠️  Discovery failed. Check the Lambda logs for details.")
