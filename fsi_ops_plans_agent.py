"""
FSI Operations Plans Analysis Agent
This module provides functionality to analyze financial services operations plans using
AWS Bedrock Agent and Knowledge Base services. It supports two types of analysis:
1. Summary Analysis - High-level overview of business documents
2. Detailed Insights - In-depth analysis of strategic and operational elements

The module uses a combination of Knowledge Base queries and Agent insights to process
and analyze document content.
"""

import boto3
import time
import random
from botocore.exceptions import ClientError
from typing import Dict
from textwrap3 import wrap, fill

# AWS Service Configuration
session = boto3.Session(profile_name='XXXXXXXXX')
bedrock_agent = session.client(service_name='bedrock-agent', region_name='us-east-1')
bedrock_agent_runtime = session.client(service_name='bedrock-agent-runtime', region_name='us-east-1')

# Configuration Constants
kb_name = 'XXXXXXXXX'
agent_id = 'XXXXXXXXX'
agent_alias_id = 'XXXXXXXXX'
session_id = 'XXXXXXXXX'
kb = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_name)
model_id = "amazon.nova-pro-v1:0"
model_arn = f'arn:aws:bedrock:us-east-1::foundation-model/{model_id}'


def retry_with_backoff(func, max_retries=3, initial_backoff=1, max_backoff=20):
    """
    Execute a function with exponential backoff retry logic for handling AWS API throttling.

    Args:
        func: Callable to be executed with retry logic
        max_retries: Maximum number of retry attempts before failing
        initial_backoff: Starting backoff time in seconds
        max_backoff: Maximum backoff time in seconds

    Returns:
        The result of the function call if successful

    Raises:
        ClientError: If max retries exceeded or non-throttling error occurs
    """
    for retries in range(max_retries + 1):
        try:
            return func()
        except (ClientError, Exception) as e:
            is_throttling = (
                isinstance(e, ClientError) and
                e.response['Error']['Code'].lower() in ['throttlingexception', 'toomanyrequestsexception']
            ) or 'throttling' in str(e).lower()

            if not is_throttling:
                raise

            if retries == max_retries:
                raise

            # Calculate backoff with exponential increase
            max_backoff_current = min(initial_backoff * (2 ** retries), max_backoff)
            # Apply full jitter: random value between 0 and max_backoff_current
            sleep_time = random.uniform(0, max_backoff_current)

            print(f"Request throttled. Attempt {retries + 1} of {max_retries}. "
                  f"Retrying in {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)


def query_knowledge_base(query: str, prompt: str) -> Dict:
    """
    Query the Bedrock Knowledge Base with contextual prompting.

    Args:
        query: The user's input query to analyze
        prompt: Structured prompt template to guide the analysis

    Returns:
        Dict containing:
            - results: List of retrieved documents with content, relevance score, and location

    Example:
        response = query_knowledge_base("Q4 performance", summary_prompt)
    """

    def perform_query():
        return bedrock_agent_runtime.retrieve(
            knowledgeBaseId=kb_name,
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 5
                }
            },
            retrievalQuery={
                'text': f"{prompt}\n\nContext: {query}"
            }
        )

    try:
        response = retry_with_backoff(perform_query)

        retrieved_results = []
        if 'retrievalResults' in response:
            for result in response['retrievalResults']:
                retrieved_results.append({
                    'content': result.get('content', ''),
                    'score': result.get('score', 0),
                    'location': result.get('location', {})
                })
        return {'results': retrieved_results}
    except Exception as e:
        print(f"Error querying knowledge base: {e}")
        return {'results': []}


def get_agent_insights(query: str, kb_results: Dict, prompt: str) -> Dict:
    """
    Generate AI-powered insights using Bedrock Agent based on knowledge base results.

    Args:
        query: Original user query
        kb_results: Results from knowledge base query
        prompt: Analysis framework prompt

    Returns:
        Dict containing:
            - insights: Structured analysis based on knowledge base content
            - error: Error message if processing fails
    """
    try:
        # Verify agent exists
        try:
            agent = bedrock_agent.get_agent(agentId=agent_id)
        except bedrock_agent.exceptions.ResourceNotFoundException:
            return {'response': 'Agent not found. Please verify the agent ID.'}

        # Format KB results into a string
        kb_context = ""
        for result in kb_results.get('results', []):
            if isinstance(result, dict) and 'content' in result:
                kb_context += f"\n{result['content']}"

        # Combine KB results with prompt for agent analysis
        input_text = f"{prompt}\n\nKnowledge Base Context:\n{kb_context}\n\nQuery Context: {query}"

        def perform_invoke():
            return bedrock_agent_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=input_text
            )

        agent_response = retry_with_backoff(perform_invoke)

        # Process the response
        completion = ""
        for event in agent_response.get('completion', []):
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    completion += chunk['bytes'].decode()
        return {'insights': completion.strip()}

    except Exception as e:
        print(f"Error getting agent insights: {e}")
        return {'error': str(e)}


def print_section_header(text):
    print(f"\n{text.upper()}")
    print("=" * len(text))


def print_subsection_header(text):
    print(f"\n{text}")
    print("-" * len(text))


def format_kb_findings(results_list, width=80):  # width parameter controls line length
    """
    Format and display knowledge base query results in a readable format.

    Args:
        results_list: List of knowledge base results to format
        width: Maximum line width for text wrapping

    The function handles:
        - Proper sentence formatting and punctuation
        - Text wrapping for readability
        - Hierarchical display of nested content
        - Clean presentation of multiple insights
    """
    for idx, result in enumerate(results_list, 1):
        print(f"\nInsight #{idx}")
        print("------------")

        def format_value(value):
            if isinstance(value, str):
                # Split into sentences and clean up
                sentences = [s.strip() for s in value.split('.') if s.strip()]
                # Recombine sentences with proper spacing and punctuation
                return '. '.join(sentences) + ('.' if sentences else '')
            elif isinstance(value, dict):
                formatted_parts = []
                for sub_key, sub_value in value.items():
                    if sub_value:
                        formatted_sub_value = format_value(sub_value)
                        if formatted_sub_value:
                            formatted_parts.append(formatted_sub_value)
                return '. '.join(formatted_parts)
            elif isinstance(value, list):
                # Join list items into coherent sentences
                return '. '.join(str(item).strip() for item in value if str(item).strip())
            else:
                return str(value).strip()

        if isinstance(result, dict):
            for key, value in result.items():
                if value and key.lower() not in ['id', 'metadata', 'score']:
                    formatted_text = format_value(value)
                    if formatted_text:
                        # Wrap text into paragraphs using textwrap3
                        wrapped_text = fill(formatted_text,
                                            width=width,
                                            break_long_words=False,
                                            replace_whitespace=False)
                        paragraphs = wrapped_text.split('\n\n')  # Split on double newlines for paragraphs
                        for paragraph in paragraphs:
                            if paragraph.strip():
                                print(f"\n{paragraph.strip()}")
        else:
            formatted_text = format_value(result)
            if formatted_text:
                # Wrap text into paragraphs using textwrap3
                wrapped_text = fill(formatted_text,
                                    width=width,
                                    break_long_words=False,
                                    replace_whitespace=False)
                paragraphs = wrapped_text.split('\n\n')
                for paragraph in paragraphs:
                    if paragraph.strip():
                        print(f"\n{paragraph.strip()}")

        print("\n" + "-" * 50)


def clean_text(text):
    """Helper function to clean and format text"""
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Ensure proper spacing after punctuation
    text = text.replace('.', '. ').replace('  ', ' ')
    # Capitalize first letter of sentences
    sentences = text.split('. ')
    sentences = [s.capitalize() for s in sentences if s]
    return '. '.join(sentences)


def process_summary(query: str) -> Dict:
    """
    Generate a high-level summary analysis of business documents.

    Analyzes documents across key areas:
        - Purpose & Context
        - Business Performance
        - Strategic Priorities
        - Incremental Headcount Initiatives
        - Non-Linear Investments

    Args:
        query: User's analysis request

    Returns:
        Dict containing knowledge base results and agent insights
    """
    summary_prompt = """For a collection of business documents containing standardized sections, please analyze and extract the key insights across all responses. Use the following structured approach:

## Purpose & Context Section
- Extract the stated mission, vision, and core objectives of the organization/team
- Identify market conditions and external factors influencing operations
- Summarize key challenges and opportunities mentioned
- Note any significant shifts in purpose or strategic direction compared to previous periods

## Business Performance Section
- Identify key performance metrics and their current status
- Extract growth rates, financial indicators, and market position data
- Summarize operational achievements and shortfalls
- Highlight customer/client satisfaction indicators and trends
- Note any performance patterns or anomalies across responses

## Strategic Priorities Section
- List all strategic initiatives in order of stated priority
- Identify common themes and divergences across responses
- Extract timelines, success metrics, and resource allocations for each priority
- Summarize how these priorities align with the stated purpose and context
- Note any shifts in strategic focus compared to previous periods

## Incremental Headcount Initiatives Section
- For each initiative (1-5):
  * Summarize the initiative's purpose and expected outcomes
  * Extract specific headcount requests and their justifications
  * Identify potential ROI or business impact projections
  * Note dependencies or risks associated with staffing these initiatives
  * Compare urgency and importance across initiatives

## Non-Linear Investments Section
- Identify proposed high-risk/high-reward investments
- Extract innovative or transformative initiatives that could significantly alter business trajectory
- Summarize resource requirements and expected outcomes
- Note evaluation criteria for success/failure
- Identify common themes in non-linear thinking across responses

## Synthesis and Integration
- Highlight alignment or misalignment between purpose, performance, and priorities
- Identify resource allocation patterns across incremental and non-linear investments
- Extract consensus views on business direction and prioritization
- Note contradictions or tensions in strategic thinking across documents
- Summarize the most compelling opportunities for organizational focus

Please present findings in a clear, concise format with supporting evidence from the documents. Where appropriate, include visualizations of key data points or relationship patterns across the sections.
"""

    try:
        kb_results = query_knowledge_base(query, summary_prompt)
        time.sleep(1)  # Add delay between KB and agent calls
        agent_insights = get_agent_insights(
            prompt=summary_prompt,
            kb_results=kb_results,
            query=query
        )

        return {
            "kb_results": kb_results,
            "agent_insights": agent_insights
        }
    except Exception as e:
        print(f"Error processing summary: {e}")
        return {"error": str(e)}


def process_insights(query: str) -> Dict:
    """
    Perform detailed analysis of business documents focusing on strategic elements.

    Analyzes documents across key areas:
        - Strategic Landscape Assessment
        - Performance Review
        - Operational Vulnerabilities

    The analysis identifies:
        - Business challenges and opportunities
        - Performance metrics and trends
        - Operational risks and mitigation strategies

    Args:
        query: User's analysis request

    Returns:
        Dict containing knowledge base results and agent insights
    """
    detailed_prompt = """For each response document in the collection, please extract and synthesize the key insights and strategic information across the following sections:

## Strategic Landscape Assessment
- Identify the primary tailwinds and headwinds affecting the business
- Summarize disruptive ideas being proposed or implemented
- Extract key competitive advantages (both current and durable)
- Highlight potential acquisition targets mentioned

## Performance Review
- Catalog major disappointments, misses, and "dirty laundry" issues
- Identify "silent threats" or "dogs not barking" concerns
- Summarize status of commitments/goals with clear yes/no achievement indicators
- List unexpected positive surprises and how they're being leveraged
- Flag any "watermelon goals" (technically achieved but problematically)

## Operational Vulnerabilities
- Note customer concentration issues (>10% dependencies) and mitigation strategies
- Identify programs lacking single-threaded leadership
- Compile "paper cut" issues affecting customer experience with resolution timelines
- Summarize enterprise-readiness gaps as perceived by customers
- List organizational axioms/beliefs being challenged

## Output Format
For each section, present findings in bullet point format with:
1. Clear identification of the issue/opportunity
2. Current status or assessment
3. Planned actions and timelines where available
4. Potential strategic implications

Please highlight contradictions or inconsistencies across documents and identify recurring themes that appear across multiple responses.
"""

    try:
        kb_results = query_knowledge_base(query, detailed_prompt)
        time.sleep(1)  # Add delay between KB and agent calls
        agent_insights = get_agent_insights(
            prompt=detailed_prompt,
            kb_results=kb_results,
            query=query
        )

        return {
            "kb_results": kb_results,
            "agent_insights": agent_insights
        }
    except Exception as e:
        print(f"Error processing insights: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    try:
        query = input("What would you like to analyze? ")

        print("\nChoose analysis type:")
        print("1. Summary Analysis")
        print("2. Detailed Insights")
        choice = input("Enter your choice (1 or 2): ")

        if choice == "1":
            print_section_header("SUMMARY ANALYSIS")
            results = process_summary(query)

            if results is None:
                print("No results returned")
            elif "error" in results:
                print(f"Error: {results['error']}")
            else:
                print_subsection_header("Knowledge Base Findings")
                format_kb_findings(results["kb_results"]["results"])

                print_subsection_header("Agent Summary Insights")
                print(results["agent_insights"].get("insights", ""))

        elif choice == "2":
            print_section_header("DETAILED INSIGHTS")
            results = process_insights(query)

            if results is None:
                print("No results returned")
            elif "error" in results:
                print(f"Error: {results['error']}")
            else:
                print_subsection_header("Knowledge Base Findings")
                format_kb_findings(results["kb_results"]["results"])

                print_subsection_header("Agent Detailed Insights")
                print(results["agent_insights"].get("insights", ""))

        else:
            print("Invalid choice. Please select 1 or 2.")

    except Exception as e:
        print(f"Error processing results: {str(e)}")
        raise
