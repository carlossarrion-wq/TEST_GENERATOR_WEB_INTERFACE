import boto3
import time
import json

print("=" * 80)
print("OPENSEARCH UPDATE MONITOR & TEST")
print("=" * 80)

# Create clients
opensearch_client = boto3.client('opensearch', region_name='eu-west-1')
lambda_client = boto3.client('lambda', region_name='eu-west-1')

# Wait for OpenSearch update to complete
print("\n⏳ Waiting for OpenSearch domain update to complete...")
print("This typically takes 5-15 minutes.\n")

max_wait_time = 900  # 15 minutes
start_time = time.time()
check_interval = 30  # Check every 30 seconds

while True:
    elapsed = time.time() - start_time
    
    if elapsed > max_wait_time:
        print(f"\n⚠️ Timeout: Update took longer than {max_wait_time/60} minutes")
        print("You may need to check the AWS Console for the domain status.")
        break
    
    # Check domain status
    response = opensearch_client.describe_domain(DomainName='rag-opensearch-clean')
    processing = response['DomainStatus']['Processing']
    
    if not processing:
        print(f"\n✅ OpenSearch domain update completed! (took {elapsed/60:.1f} minutes)")
        
        # Verify the access policy was updated
        access_policies = json.loads(response['DomainStatus']['AccessPolicies'])
        principals = access_policies['Statement'][0]['Principal']['AWS']
        
        print("\n📋 Updated Access Policy Principals:")
        for principal in principals:
            print(f"   - {principal}")
        
        # Now test the Lambda function
        print("\n" + "=" * 80)
        print("TESTING LAMBDA WITH OPENSEARCH")
        print("=" * 80)
        
        test_payload = {
            "httpMethod": "POST",
            "body": json.dumps({
                "action": "generate-plan",
                "title": "Login Module Test Plan",
                "requirements": "Test user authentication and authorization for the login module. Verify login with valid credentials, invalid credentials, password reset, session management, and security features.",
                "user_team": "darwin",
                "coverage_percentage": 80,
                "min_test_cases": 3,
                "max_test_cases": 8,
                "selected_test_types": ["functional", "negative", "security"]
            })
        }
        
        print(f"\n🧪 Invoking Lambda: test-plan-generator-ai")
        print(f"📝 Test payload: {json.dumps(test_payload, indent=2)}")
        
        try:
            lambda_response = lambda_client.invoke(
                FunctionName='test-plan-generator-ai',
                InvocationType='RequestResponse',
                Payload=json.dumps(test_payload)
            )
            
            response_payload = json.loads(lambda_response['Payload'].read())
            
            print("\n" + "=" * 80)
            print("LAMBDA RESPONSE")
            print("=" * 80)
            
            if lambda_response['StatusCode'] == 200:
                print("✅ Lambda invocation successful!")
                
                # Parse the response
                if 'body' in response_payload:
                    body = json.loads(response_payload['body'])
                    
                    # Check for OpenSearch info
                    if 'opensearch_info' in body:
                        opensearch_info = body['opensearch_info']
                        print(f"\n🔍 OpenSearch Integration:")
                        print(f"   - Status: {opensearch_info.get('status', 'N/A')}")
                        print(f"   - Team: {opensearch_info.get('team', 'N/A')}")
                        print(f"   - Indices Used: {opensearch_info.get('indices_used', [])}")
                        print(f"   - Documents Retrieved: {opensearch_info.get('documents_retrieved', 0)}")
                        
                        if opensearch_info.get('status') == 'success':
                            print("\n🎉 SUCCESS! OpenSearch is working correctly!")
                        else:
                            print(f"\n⚠️ OpenSearch returned status: {opensearch_info.get('status')}")
                            if 'error' in opensearch_info:
                                print(f"   Error: {opensearch_info['error']}")
                    else:
                        print("\n⚠️ No opensearch_info in response")
                    
                    # Show test cases if generated
                    if 'test_cases' in body:
                        print(f"\n📊 Generated {len(body['test_cases'])} test cases")
                    
                    print(f"\n📄 Full response saved to: opensearch_test_response.json")
                    with open('opensearch_test_response.json', 'w') as f:
                        json.dump(body, f, indent=2)
                else:
                    print(f"\n⚠️ Unexpected response format: {response_payload}")
            else:
                print(f"❌ Lambda invocation failed with status: {lambda_response['StatusCode']}")
                print(f"Response: {response_payload}")
                
        except Exception as e:
            print(f"\n❌ Error testing Lambda: {str(e)}")
            import traceback
            traceback.print_exc()
        
        break
    
    # Still processing
    minutes_elapsed = elapsed / 60
    print(f"⏳ Still processing... ({minutes_elapsed:.1f} minutes elapsed)")
    time.sleep(check_interval)

print("\n" + "=" * 80)
