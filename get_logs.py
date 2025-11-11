import boto3
import json
from datetime import datetime

logs_client = boto3.client('logs', region_name='eu-west-1')

# Get the most recent log stream
response = logs_client.describe_log_streams(
    logGroupName='/aws/lambda/test-plan-generator-ai',
    orderBy='LastEventTime',
    descending=True,
    limit=1
)

if response['logStreams']:
    log_stream_name = response['logStreams'][0]['logStreamName']
    print(f"Most recent log stream: {log_stream_name}\n")
    
    # Get log events
    events_response = logs_client.get_log_events(
        logGroupName='/aws/lambda/test-plan-generator-ai',
        logStreamName=log_stream_name,
        limit=100
    )
    
    print("=" * 80)
    print("LOG EVENTS:")
    print("=" * 80)
    
    for event in events_response['events']:
        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
        message = event['message']
        print(f"\n[{timestamp}]")
        print(message)
        print("-" * 80)
else:
    print("No log streams found")
