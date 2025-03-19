import boto3
import botocore

try:
    # First establish the session with the SSO profile
    session = boto3.Session(profile_name='XXXXXXXXXX')

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
    kb_name = 'XXXXXXXXXX'
    kb = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_name)

    model_id = "amazon.nova-pro-v1:0"
    model_arn = f'arn:aws:bedrock:us-east-1::foundation-model/{model_id}'

except Exception as e:
    print(f"Error initializing AWS services: {e}")
    raise

def create_advisory_board():
    # Define industry segments and core personas
    segments = {
        "Banking": 3,
        "Insurance": 3,
        "Capital Markets": 3,
        "Payments": 3
    }

    advisory_board_prompt = """
    Based on the financial services industry knowledge and personas, create a diverse customer advisory board with the following structure:
    
    For each member, provide:
    1. Role/Title
    2. Industry Segment
    3. Organization Type (e.g., Global Bank, Regional Insurer)
    4. Key Areas of Influence
    5. Primary Technology Focus
    
    Requirements:
    - 12 total members
    - Equal distribution across Banking, Insurance, Capital Markets, and Payments (3 each)
    - Mix of technical and business roles
    - Diverse organization sizes
    - Different geographic regions
    - Various technology maturity levels
    
    Format the response as a structured list of advisory board members.
    """

    try:
        # Get advisory board composition
        board_response = bedrock_agent_runtime.retrieve_and_generate(
            input={
                'text': advisory_board_prompt
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kb_name,
                    'modelArn': model_arn,
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': 10,
                            'overrideSearchType': 'HYBRID'
                        }
                    }
                }
            }
        )

        return board_response['output']['text']
    except Exception as e:
        print(f"Error creating advisory board: {e}")
        return None

def get_advisory_input(board_members, user_question):
    advisory_prompt = f"""
    Acting as the customer advisory board members described below:
    
    {board_members}
    
    Based on the knowledge base information about customer needs, feature requests, and industry requirements, provide detailed perspectives on the following question:
    
    {user_question}
    
    Format the response as follows:
    
    ## Key Strategic Insights
    - Top 3-5 strategic insights with specific feature implications
    
    ## Segment-Specific Requirements
    
    ### Banking
    Features Needed:
    - Critical feature requirement 1 with specific use case
    - Critical feature requirement 2 with specific use case
    Integration Points:
    - Required integration 1
    - Required integration 2
    Compliance Requirements:
    - Specific regulatory requirement
    
    ### Insurance
    Features Needed:
    - Critical feature requirement 1 with specific use case
    - Critical feature requirement 2 with specific use case
    Integration Points:
    - Required integration 1
    - Required integration 2
    Compliance Requirements:
    - Specific regulatory requirement
    
    ### Capital Markets
    Features Needed:
    - Critical feature requirement 1 with specific use case
    - Critical feature requirement 2 with specific use case
    Integration Points:
    - Required integration 1
    - Required integration 2
    Performance Requirements:
    - Specific performance metric
    
    ### Payments
    Features Needed:
    - Critical feature requirement 1 with specific use case
    - Critical feature requirement 2 with specific use case
    Integration Points:
    - Required integration 1
    - Required integration 2
    Security Requirements:
    - Specific security requirement
    
    ## Technical Requirements
    ### Core Features
    - Must-have feature 1 with business justification
    - Must-have feature 2 with business justification
    
    ### API Requirements
    - Required API capability 1
    - Required API capability 2
    
    ### Performance Metrics
    - Required performance threshold 1
    - Required performance threshold 2
    
    ## Implementation Priorities
    ### Immediate Needs (0-6 months)
    1. Feature priority 1 with business impact
    2. Feature priority 2 with business impact
    
    ### Medium Term (6-12 months)
    1. Feature priority 1 with business impact
    2. Feature priority 2 with business impact
    
    ### Long Term (12+ months)
    1. Feature priority 1 with business impact
    2. Feature priority 2 with business impact
    
    ## Risk Assessment
    ### Technical Risks
    - Risk 1 with mitigation strategy
    - Risk 2 with mitigation strategy
    
    ### Business Risks
    - Risk 1 with mitigation strategy
    - Risk 2 with mitigation strategy
    
    ### Compliance Risks
    - Risk 1 with mitigation strategy
    - Risk 2 with mitigation strategy
    
    ## Integration Considerations
    ### Current Systems
    - Integration requirement 1
    - Integration requirement 2
    
    ### Future Architecture
    - Architecture consideration 1
    - Architecture consideration 2
    
    ## Success Metrics
    ### Business KPIs
    - KPI 1 with target metric
    - KPI 2 with target metric
    
    ### Technical KPIs
    - KPI 1 with target metric
    - KPI 2 with target metric
    
    Ensure all recommendations:
    - Reference specific features from the knowledge base
    - Include concrete use cases
    - Provide measurable success criteria
    - Address regulatory requirements
    - Consider integration complexity
    - Account for different organization sizes
    - Factor in regional variations
    - Reflect technology maturity levels
    - Include specific performance requirements
    - Address security and compliance needs
    """

    try:
        # Get advisory board feedback with increased context retrieval
        advisory_response = bedrock_agent_runtime.retrieve_and_generate(
            input={
                'text': advisory_prompt
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kb_name,
                    'modelArn': model_arn,
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': 20,  # Increased for more comprehensive feature coverage
                            'overrideSearchType': 'HYBRID'
                        }
                    }
                }
            }
        )

        return advisory_response['output']['text']
    except Exception as e:
        print(f"Error getting advisory input: {e}")
        return None

def main():
    try:
        # Create the advisory board
        print("Creating Financial Services Advisory Board...")
        board_members = create_advisory_board()

        if board_members:
            print("\nAdvisory Board Created Successfully!")
            print("\nBoard Composition:")
            print(board_members)

            while True:
                # Get question from user
                user_question = input("\nEnter your question for the advisory board (or 'quit' to exit): ")

                if user_question.lower() == 'quit':
                    break

                # Get advisory board input
                print("\nGathering advisory board perspectives...")
                advisory_feedback = get_advisory_input(board_members, user_question)

                if advisory_feedback:
                    print("\nAdvisory Board Feedback:")
                    print(advisory_feedback)
                else:
                    print("Unable to gather advisory board feedback.")

        else:
            print("Unable to create advisory board.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
