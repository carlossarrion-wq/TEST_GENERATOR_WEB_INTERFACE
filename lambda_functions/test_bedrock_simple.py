import json
import boto3
import os
import time

bedrock_client = boto3.client('bedrock-runtime', region_name='eu-west-1')
MODEL_ID = 'anthropic.claude-haiku-4-5-20251001-v1:0'

def lambda_handler(event, context):
    print("Starting simple Bedrock test...")
    start_time = time.time()
    
    try:
        print(f"Using model: {MODEL_ID}")
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": "Say hello in one word"
                }
            ]
        }
        
        print("Calling Bedrock...")
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text']
        
        execution_time = time.time() - start_time
        
        print(f"Success! Execution time: {execution_time:.2f}s")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Bedrock test successful',
                'response': content,
                'execution_time': round(execution_time, 2),
                'model': MODEL_ID
            })
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"Error after {execution_time:.2f}s: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'execution_time': round(execution_time, 2)
            })
        }
