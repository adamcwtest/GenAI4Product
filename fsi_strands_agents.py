import boto3
import os
from strands import Agent


def verify_aws_session():
    """
    Verifies AWS credentials and returns a valid session.

    Returns:
        tuple: (boto3.Session, boto3.credentials.Credentials)
    Raises:
        Exception: If credentials are invalid or missing
    """
    session = boto3.Session(profile_name='XXXXXX')
    credentials = session.get_credentials()
    if not credentials:
        raise Exception("Failed to load AWS credentials")
    if hasattr(credentials, 'get_frozen_credentials'):
        frozen = credentials.get_frozen_credentials()
        if not frozen.access_key or not frozen.secret_key:
            raise Exception("Invalid credentials detected")
    return session, credentials


def collaborative_analysis():
    """
    Performs a multi-phase analysis of AWS Financial Services opportunities using specialized AI agents.

    The analysis consists of four phases:
    1. Market Analysis: Identifies key customer needs in financial services
    2. Technical Architecture: Proposes AWS services and patterns to address needs
    3. Product Requirements: Defines specific products and features to build
    4. Final Synthesis: Consolidates insights into prioritized recommendations

    Each phase builds upon insights from previous phases to create a comprehensive analysis.
    """
    try:
        # Set up AWS credentials
        session, credentials = verify_aws_session()
        os.environ['AWS_ACCESS_KEY_ID'] = credentials.access_key
        os.environ['AWS_SECRET_ACCESS_KEY'] = credentials.secret_key
        if credentials.token:
            os.environ['AWS_SESSION_TOKEN'] = credentials.token
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

        # Phase 1: Market Analysis
        print("\n=== Phase 1: Market Analysis ===")
        strategist = Agent(model="anthropic.claude-v2")
        market_prompt = """You are a strategic advisor analyzing market opportunities. 
        What are the top 3 pressing needs of financial services customers that AWS should address? 
        Focus on specific industry challenges and provide concrete examples."""

        market_analysis = strategist(market_prompt)
        print(market_analysis)

        # Phase 2: Technical Architecture Review
        print("\n=== Phase 2: Technical Architecture ===")
        architect = Agent(model="anthropic.claude-v2")
        arch_prompt = f"""You are an expert AWS Solutions Architect specializing in financial services.
        Based on this market analysis: {market_analysis}
        What specific AWS services and architectural patterns should be built? 
        Consider:
        - Security and compliance requirements
        - Scalability and performance needs
        - Integration with existing systems
        - Cost optimization opportunities"""

        architecture_insights = architect(arch_prompt)
        print("\nArchitecture Recommendations:")
        print(architecture_insights)

        # Phase 3: Product Requirements
        print("\n=== Phase 3: Product Requirements ===")
        product = Agent(model="anthropic.claude-v2")
        product_prompt = f"""You are a product manager focused on financial services technology.
        Based on:
        Market Analysis: {market_analysis}
        Architecture Recommendations: {architecture_insights}

        Define specific products AWS should build, including:
        1. Core features and capabilities
        2. Priority order for development
        3. Potential timeline and phases
        4. Success metrics and KPIs"""

        product_insights = product(product_prompt)
        print("\nProduct Recommendations:")
        print(product_insights)

        # Phase 4: Final Synthesis
        print("\n=== Phase 4: Final Synthesis ===")
        synthesis_prompt = f"""As a strategic advisor, synthesize all insights into actionable recommendations:
        Market Analysis: {market_analysis}
        Architecture: {architecture_insights}
        Product: {product_insights}

        Provide:
        1. Prioritized list of what AWS should build
        2. Key success factors and risks
        3. Implementation considerations
        4. Expected market impact"""

        final_recommendations = strategist(synthesis_prompt)
        print("\nFinal Recommendations:")
        print(final_recommendations)

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print("\nDebug information:")
        print(f"Response type: {type(response) if 'response' in locals() else 'Not available'}")


def main():
    """
    Main entry point for the AWS Financial Services analysis program.
    """
    collaborative_analysis()


if __name__ == "__main__":
    main()
