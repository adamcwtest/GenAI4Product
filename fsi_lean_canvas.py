import boto3
from typing import Dict, List, Optional

try:
    session = boto3.Session(profile_name='XXXXXXXXXX')
    bedrock_agent = session.client(service_name='bedrock-agent', region_name='us-east-1')
    bedrock_agent_runtime = session.client(service_name='bedrock-agent-runtime', region_name='us-east-1')

    kb_name = 'XXXXXXXXXX'
    kb = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_name)
    model_id = "amazon.nova-pro-v1:0"
    model_arn = f'arn:aws:bedrock:us-east-1::foundation-model/{model_id}'

except Exception as e:
    print(f"Error initializing AWS services: {e}")
    raise

def select_segment() -> str:
    segments = ["Banking", "Insurance", "Capital Markets", "Payments"]
    print("\nAvailable segments:")
    for idx, segment in enumerate(segments, 1):
        print(f"{idx}. {segment}")

    while True:
        try:
            choice = int(input("\nSelect a segment (1-4): "))
            if 1 <= choice <= 4:
                return segments[choice - 1]
            print("Please select a number between 1 and 4")
        except ValueError:
            print("Please enter a valid number")

def create_customer_personas(segment: str) -> Optional[str]:
    persona_prompt = f"""
    Create 3 detailed {segment} customer personas:

    For each persona, include:
    1. Role/Title
    2. Organization (type/size)
    3. Key Responsibilities 
    4. Pain Points
    5. Goals
    6. Tech Comfort (1-5)
    7. Decision Power (influencer/recommender/approver)
    8. Success Metrics
    9. Communication Preferences
    10. Daily Challenges

    Ensure diversity in:
    - Technical vs. business roles
    - Organization sizes
    - Tech maturity levels
    - {segment}-specific challenges
    """

    try:
        response = bedrock_agent_runtime.retrieve_and_generate(
            input={'text': persona_prompt},
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
        return response['output']['text']
    except Exception as e:
        print(f"Error creating customer personas: {e}")
        return None

def create_lean_canvas(product_idea: str, personas: str, segment: str) -> Optional[str]:
    lean_canvas_prompt = f"""
        Generate a detailed, actionable Lean Canvas for the following product idea and customer personas, incorporating industry-specific insights and analysis:

        ## INPUT
        Product Idea:
        {product_idea}

        Customer Personas:
        {personas}

        Industry Context:
        {segment}

        ## OUTPUT REQUIREMENTS
        Create a comprehensive, industry-specific Lean Canvas with thorough analysis of each section. For each component, provide:
        - Bullet points with specific, measurable details
        - Brief explanations of reasoning
        - Relevant industry benchmarks or standards where applicable

        ### 1. Problem Statement
        - Identify and prioritize the top 3 most critical customer pain points with severity ratings (1-10)
        - Describe the consequences of these problems (financial, operational, emotional) 
        - List current alternatives and their limitations
        - Include relevant industry statistics validating these problems

        ### 2. Customer Segments
        - Define primary and secondary customer segments with demographic and psychographic details
        - Identify early adopters with specific characteristics and acquisition strategy
        - Estimate segment sizes with potential reach
        - Map problems to specific segments

        ### 3. Unique Value Proposition
        - Create a clear, compelling statement addressing primary pain points (25 words max)
        - Articulate 3-5 key differentiators from alternatives
        - Explain the transformation promised to customers
        - Include potential high-concept pitch (X for Y analogy)

        ### 4. Solution Architecture
        - Detail top 3 features directly mapped to identified problems
        - Define clear MVP scope with timeline and resource requirements
        - Include user stories for key functionality
        - Address technical feasibility and implementation challenges
        - Outline future development roadmap (post-MVP)

        ### 5. Channels
        - Specify detailed customer acquisition channels with cost estimates for each
        - Include customer retention strategies
        - Map customer journey touchpoints
        - Prioritize channels based on segment preferences and cost-effectiveness
        - Address industry-specific distribution challenges

        ### 6. Revenue Streams
        - Detail primary and secondary revenue models with projected percentages
        - Include specific pricing strategy with comparative analysis
        - Project revenue timeline with key milestones
        - Analyze price sensitivity within target segments
        - Include lifetime value calculations and retention economics

        ### 7. Cost Structure
        - Break down fixed costs with specific line items and amounts
        - Estimate variable costs per unit/customer
        - Calculate customer acquisition costs (CAC)
        - Project burn rate and runway
        - Identify cost optimization opportunities
        - Include regulatory compliance costs specific to {segment}

        ### 8. Key Metrics
        - Define 5-7 specific KPIs with target values and tracking frequency
        - Include both leading and lagging indicators
        - Set specific activation, retention, and referral metrics
        - Determine breakeven points and profitability metrics
        - Establish data collection and analysis methods

        ### 9. Competitive Differentiation
        - Identify truly sustainable advantages (IP, exclusive relationships, network effects)
        - Detail distinctive elements that create customer preference
        - Detail how these advantages deliver customer value
        - Explain what makes your offering distinctive and difficult to replicate
        - Address sustainability of advantages over time

        ### 10. Regulatory & Risk Assessment
        - Identify industry-specific regulatory requirements
        - Outline compliance strategy and costs
        - Assess major business risks with mitigation approaches
        - Consider ethical implications and potential reputation impacts

        Format the Lean Canvas as a structured business plan with clear sections, substantiated assumptions, and actionable next steps for validation. Include an executive summary highlighting the 3-5 most critical insights from the canvas.
        """

    try:
        response = bedrock_agent_runtime.retrieve_and_generate(
            input={'text': lean_canvas_prompt},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kb_name,
                    'modelArn': model_arn,
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': 20,
                            'overrideSearchType': 'HYBRID'
                        }
                    }
                }
            }
        )
        return response['output']['text']
    except Exception as e:
        print(f"Error creating lean canvas: {e}")
        return None

def main():
    try:
        print("Welcome to the Financial Services Product Planning Tool")

        # Select segment
        segment = select_segment()
        print(f"\nCreating Customer Personas for {segment} segment...")

        # Create personas
        personas = create_customer_personas(segment)
        if personas:
            print("\nCustomer Personas Created Successfully!")
            print("\nPersona Details:")
            print(personas)

            # Get product idea
            product_idea = input("\nEnter your product idea: ")

            # Create lean canvas
            print("\nGenerating Lean Canvas...")
            lean_canvas = create_lean_canvas(product_idea, personas, segment)  # Added segment parameter

            if lean_canvas:
                print("\nLean Canvas:")
                print(lean_canvas)
            else:
                print("Unable to generate lean canvas.")
        else:
            print("Unable to create customer personas.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
