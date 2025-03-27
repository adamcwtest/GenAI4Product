import boto3
import botocore

try:
    # First establish the session with the SSO profile
    session = boto3.Session(profile_name='XXXXXXX')

    # Create Bedrock clients using the session
    bedrock_agent = session.client(
        service_name='bedrock-agent',
        region_name='us-east-1'
    )

    bedrock_agent_runtime = session.client(
        service_name='bedrock-agent-runtime',
        region_name='us-east-1'
    )

    # Your existing code with the clients
    kb_name = 'XXXXXXX'
    kb = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_name)

    model_id = "amazon.nova-pro-v1:0"
    #model_id = "anthropic.claude-3-7-sonnet-20250219-v1:0"
    model_arn = f'arn:aws:bedrock:us-east-1::foundation-model/{model_id}'

    service = input("Enter a service: ")
    #query = f"Tell me about AWS {service} service and its main feature requests. Include common use cases driving each feature need"
    query = f"""
You are an AWS service expert providing detailed technical information.
For the AWS {service} service, analyze the top 3 most requested features:

## For each feature request, provide:
1. Feature Name and Description
2. Primary Use Case:
   - The core business problem it solves
   - Who needs this feature (persona)
   - Current workarounds if any

3. Business Value:
   - Quantifiable benefits (e.g., cost savings, time reduction)
   - Competitive advantage
   - Risk mitigation aspects

4. Real-World Application:
   - Industry-specific example
   - Technical implementation scenario
   - Integration points with other AWS services

5. Technical Considerations:
   - Current service limitations
   - Dependencies or prerequisites
   - Performance implications
   - Security considerations

Format the response as:

# Top Feature Requests for {service}

## 1. [Feature Name]
### Overview
[Brief feature description]

### Primary Use Case
- Problem: 
- Target Users:
- Current Workarounds:

### Business Value
- Benefits:
- Strategic Advantage:
- Risk Factors:

### Real-World Application
- Industry Example:
- Implementation Scenario:
- AWS Integration Points:

### Technical Considerations
- Limitations:
- Dependencies:
- Performance Impact:
- Security Notes:

[Repeat structure for features 2 and 3]

## Summary
- Most critical feature needs
- Common themes across requests
- Strategic recommendations
"""

    response = bedrock_agent_runtime.retrieve_and_generate(
        input={
            'text': query
        },
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': kb_name,
                'modelArn': model_arn,
                'retrievalConfiguration': {
                    'vectorSearchConfiguration': {
                        'numberOfResults': 15,
                        'overrideSearchType': 'HYBRID'
                    }
                }
            }
        }
    )

    # Print the response
    if 'output' in response and 'text' in response['output']:
        print("\nResponse:")
        print(response['output']['text'])
    else:
        print("No output in response")

except botocore.exceptions.ProfileNotFound as e:
    print(f"AWS Profile not found. Please check if you're logged in to AWS SSO: {e}")
except botocore.exceptions.ClientError as e:
    print(f"AWS API error occurred: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
