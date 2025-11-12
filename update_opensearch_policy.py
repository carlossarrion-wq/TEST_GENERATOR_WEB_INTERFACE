import boto3
import json

# Create OpenSearch client
client = boto3.client('opensearch', region_name='eu-west-1')

# Define the access policy
policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": [
                    "arn:aws:iam::701055077130:role/rag-system-production-RAGEC2Role-hawdzi5Lrv3d",
                    "arn:aws:iam::701055077130:role/TestPlanGeneratorLambdaRole"
                ]
            },
            "Action": "es:*",
            "Resource": "arn:aws:es:eu-west-1:701055077130:domain/rag-opensearch-clean/*"
        }
    ]
}

# Convert policy to JSON string
policy_string = json.dumps(policy)

print("Updating OpenSearch domain access policy...")
print(f"Policy: {policy_string}")

try:
    # Update the domain configuration
    response = client.update_domain_config(
        DomainName='rag-opensearch-clean',
        AccessPolicies=policy_string
    )
    
    print("\n✅ Successfully updated OpenSearch access policy!")
    print(f"Update status: {response['DomainConfig']['AccessPolicies']['Status']['State']}")
    print("\nThe domain is now being updated. This may take several minutes.")
    print("You can check the status with:")
    print("aws opensearch describe-domain --domain-name rag-opensearch-clean --region eu-west-1 --query 'DomainStatus.Processing'")
    
except Exception as e:
    print(f"\n❌ Error updating policy: {str(e)}")
    import traceback
    traceback.print_exc()
