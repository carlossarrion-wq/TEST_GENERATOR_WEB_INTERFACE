import boto3
import time
import json

print("=" * 80)
print("FULL INTEGRATION TEST - RDS + OpenSearch + Bedrock")
print("=" * 80)

# Create clients
rds_client = boto3.client('rds', region_name='eu-west-1')
lambda_client = boto3.client('lambda', region_name='eu-west-1')

# Wait for RDS modification to complete
print("\n⏳ Waiting for RDS to complete VPC migration...")
max_wait = 600  # 10 minutes
start_time = time.time()

while True:
    elapsed = time.time() - start_time
    
    if elapsed > max_wait:
        print(f"\n⚠️ Timeout after {max_wait/60} minutes")
        break
    
    response = rds_client.describe_db_instances(DBInstanceIdentifier='test-plan-generator-db')
    db_instance = response['DBInstances'][0]
    status = db_instance['DBInstanceStatus']
    vpc_id = db_instance['DBSubnetGroup']['VpcId']
    pending = db_instance.get('PendingModifiedValues', {})
    
    print(f"   Status: {status}, VPC: {vpc_id}, Pending: {bool(pending)}")
    
    if status == 'available' and not pending and vpc_id == 'vpc-04ba39cd0772a280b':
        print(f"\n✅ RDS migration completed! (took {elapsed/60:.1f} minutes)")
        print(f"   New VPC: {vpc_id}")
        print(f"   Security Groups: {[sg['VpcSecurityGroupId'] for sg in db_instance['VpcSecurityGroups']]}")
        break
    
    time.sleep(15)

# Now test Lambda
print("\n" + "=" * 80)
print("TESTING LAMBDA FUNCTION")
print("=" * 80)

test_payload = {
    "httpMethod": "POST",
    "body": json.dumps({
        "action": "generate-plan",
        "title": "Shopping Cart Test Plan",
        "requirements": "Test shopping cart functionality including add to cart, remove from cart, update quantities, and checkout process.",
        "user_team": "mulesoft",
        "coverage_percentage": 80,
        "min_test_cases": 3,
        "max_test_cases": 6,
        "selected_test_types": ["functional", "negative"]
    })
}

print(f"\n🧪 Invoking Lambda: test-plan-generator-ai")
print(f"📝 Team: mulesoft")

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
        
        if 'body' in response_payload:
            body = json.loads(response_payload['body'])
            
            print(f"\n📊 Results:")
            print(f"   - Plan ID: {body.get('plan_id', 'N/A')}")
            print(f"   - Test Cases: {body.get('test_cases_created', 0)}")
            print(f"   - Execution Time: {body.get('execution_time_seconds', 0)}s")
            print(f"   - Quality Score: {body.get('quality_score', 0)}/100")
            print(f"   - Coverage: {body.get('coverage_percentage', 0)}%")
            
            # Check OpenSearch
            if 'opensearch_info' in body:
                opensearch_info = body['opensearch_info']
                print(f"\n🔍 OpenSearch Integration:")
                print(f"   - Team: {opensearch_info.get('team', 'N/A')}")
                print(f"   - Indices Used: {opensearch_info.get('indices_used', [])}")
                print(f"   - Documents Retrieved: {opensearch_info.get('insights_retrieved', 0)}")
                
                if opensearch_info.get('insights_retrieved', 0) > 0:
                    print("\n🎉 SUCCESS! OpenSearch is working!")
                else:
                    print("\n⚠️ OpenSearch connected but no documents found (indices may be empty)")
            else:
                print("\n⚠️ No opensearch_info in response")
            
            # Save full response
            with open('full_integration_test_response.json', 'w') as f:
                json.dump(body, f, indent=2)
            print(f"\n📄 Full response saved to: full_integration_test_response.json")
        else:
            print(f"\n❌ Unexpected response format: {response_payload}")
    else:
        print(f"❌ Lambda failed with status: {lambda_response['StatusCode']}")
        print(f"Response: {response_payload}")
        
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
