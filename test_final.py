import boto3
import json
import time

print("Esperando 20 segundos para que Lambda esté listo...")
time.sleep(20)

print("\n" + "="*80)
print("PRUEBA FINAL - RDS + OpenSearch + Bedrock")
print("="*80)

lambda_client = boto3.client('lambda', region_name='eu-west-1')

test_payload = {
    "httpMethod": "POST",
    "body": json.dumps({
        "action": "generate-plan",
        "title": "Shopping Cart Test",
        "requirements": "Test add to cart, remove from cart, update quantities, and checkout process",
        "user_team": "mulesoft",
        "coverage_percentage": 80,
        "min_test_cases": 3,
        "max_test_cases": 5,
        "selected_test_types": ["functional"]
    })
}

print("\n🧪 Invocando Lambda...")
print(f"📝 Team: mulesoft")

try:
    response = lambda_client.invoke(
        FunctionName='test-plan-generator-ai',
        InvocationType='RequestResponse',
        Payload=json.dumps(test_payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    print("\n" + "="*80)
    print("RESULTADO")
    print("="*80)
    
    if response['StatusCode'] == 200:
        if 'body' in result:
            body = json.loads(result['body'])
            
            print(f"✅ Status: {response['StatusCode']}")
            print(f"\n📊 Resultados:")
            print(f"   - Plan ID: {body.get('plan_id', 'N/A')}")
            print(f"   - Test Cases: {body.get('test_cases_created', 0)}")
            print(f"   - Execution Time: {body.get('execution_time_seconds', 0)}s")
            print(f"   - Quality Score: {body.get('quality_score', 0)}/100")
            print(f"   - Coverage: {body.get('coverage_percentage', 0)}%")
            
            opensearch_info = body.get('opensearch_info', {})
            print(f"\n🔍 OpenSearch:")
            print(f"   - Team: {opensearch_info.get('team', 'N/A')}")
            print(f"   - Indices Used: {opensearch_info.get('indices_used', [])}")
            print(f"   - Documents Retrieved: {opensearch_info.get('insights_retrieved', 0)}")
            
            if opensearch_info.get('insights_retrieved', 0) > 0:
                print("\n🎉 ¡SUCCESS! OpenSearch está funcionando correctamente!")
            else:
                print("\n⚠️ OpenSearch conectó pero no encontró documentos (índices vacíos o sin coincidencias)")
            
            with open('test_final_response.json', 'w') as f:
                json.dump(body, f, indent=2)
            print(f"\n📄 Respuesta completa guardada en: test_final_response.json")
        else:
            print(f"❌ Error: {result}")
    else:
        print(f"❌ Lambda failed: {result}")
        
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
