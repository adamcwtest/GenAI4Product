import boto3
from typing import Dict, List, Optional
import json
import time
import random
from botocore.exceptions import ClientError
from enum import Enum

try:
    session = boto3.Session(profile_name='XXXXXXX')
    bedrock_agent = session.client(service_name='bedrock-agent', region_name='us-east-1')
    bedrock_agent_runtime = session.client(service_name='bedrock-agent-runtime', region_name='us-east-1')
    bedrock_runtime = session.client(service_name='bedrock-runtime', region_name='us-east-1')
    kb_name = 'XXXXXXX'
    kb = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_name)
    model_id = "amazon.nova-pro-v1:0"
    REQUEST_DELAY = 3  # seconds to wait between requests
    ERROR_DELAY = 5  # seconds to wait after an error
    MAX_RETRIES = 3  # maximum number of retries for throttled requests
    model_arn = f'arn:aws:bedrock:us-east-1::foundation-model/{model_id}'
except Exception as e:
    print(f"Error initializing AWS services: {e}")
    exit(1)


class CanvasField(Enum):
    VISION = "Vision"
    GOALS = "Goals"
    TARGET_CUSTOMERS = "Target Customers"
    CUSTOMER_PROBLEMS = "Customer Problems"
    VALUE_PROPOSITION = "Value Proposition"
    BUSINESS_MODEL = "Business Model"
    DIFFERENTIATORS = "Differentiators"
    STRATEGIC_ECOSYSTEM = "Strategic Ecosystem"
    SUCCESS_MEASURES = "Success Measures"
    STRATEGIC_BETS = "Strategic Bets"


def get_field_definition(field: CanvasField) -> str:
    """
    Returns the definition for each canvas field according to the Product Strategy Canvas.
    """
    definitions = {
        CanvasField.VISION: "Why do we exist? What future do we want to create?",
        CanvasField.GOALS: "What do we want to achieve in the next 1-3 years?",
        CanvasField.TARGET_CUSTOMERS: "Who are our most important customers?",
        CanvasField.CUSTOMER_PROBLEMS: "What customer problems are we solving?",
        CanvasField.VALUE_PROPOSITION: "How do we create value for customers?",
        CanvasField.BUSINESS_MODEL: "How do we capture value?",
        CanvasField.DIFFERENTIATORS: "How are we different from alternatives?",
        CanvasField.STRATEGIC_ECOSYSTEM: "What strategic relationships do we need?",
        CanvasField.SUCCESS_MEASURES: "How do we measure success?",
        CanvasField.STRATEGIC_BETS: "What strategic choices are we making?"
    }
    return definitions.get(field, "")


def query_knowledge_base(query: str) -> str:
    """
    Query the knowledge base using the Bedrock Agent Runtime
    """
    response = bedrock_agent_runtime.retrieve(
        knowledgeBaseId=kb_name,
        retrievalQuery={
            'text': query
        },
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': 5
            }
        }
    )

    # Extract relevant information from the retrieved results
    results = []
    for result in response['retrievalResults']:
        results.append(result['content']['text'])

    return "\n\n".join(results)


def generate_canvas_section(field: CanvasField, product_name: str, user_populated_fields: Dict[CanvasField, str] = None,
                            max_retries: int = 5) -> str:
    """
    Generate content for a specific section of the product strategy canvas with retry logic,
    taking into account user-provided content for other fields
    """
    field_definition = get_field_definition(field)

    # Build context from user-populated fields
    context_from_user = ""
    if user_populated_fields:
        context_parts = []
        for f, content in user_populated_fields.items():
            context_parts.append(f"For {f.value}, the user specified: {content}")
        context_from_user = "Consider this existing context:\n" + "\n".join(context_parts)

    prompt_context = f"""I need to create content for the '{field.value}' section of a Product Strategy Canvas for {product_name} 
                     focused on AWS Financial Services Industry. This section answers: '{field_definition}'.
                     {context_from_user}"""

    # First retrieve relevant information from the knowledge base
    kb_results = query_knowledge_base(prompt_context)

    # Implement retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            # Add a base delay between requests
            time.sleep(1)

            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "text": f"""
                                    You are an expert AWS product strategist specializing in financial services. Create the '{field.value}' section 
                                    of a Product Strategy Canvas for {product_name} focused on the AWS Financial Services Industry.

                                    This section should address: {field_definition}

                                    {context_from_user}

                                    Use this information from the knowledge base:
                                    {kb_results}

                                    Important guidelines:
                                    1. Ensure your response aligns with and complements any user-provided context
                                    2. Be specific and actionable, focusing on financial services industry needs
                                    3. Make sure the response is coherent with other sections of the canvas
                                    4. Keep the response concise but comprehensive
                                    5. Focus on AWS-specific solutions and capabilities where relevant
                                    """
                                }
                            ]
                        }
                    ]
                })
            )

            response_body = json.loads(response['body'].read().decode('utf-8'))
            return response_body.get('content', response_body.get('completion', ''))

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ThrottlingException':
                if attempt == max_retries - 1:
                    raise
                wait_time = (2 ** attempt) + random.random()
                print(f"Rate limited. Waiting {wait_time:.2f} seconds before retry...")
                time.sleep(wait_time)
                continue
            else:
                raise


def create_product_strategy_canvas(product_name: str, selected_fields: List[CanvasField],
                                   user_populated_fields: Dict[CanvasField, str] = None) -> Dict[str, Dict[str, str]]:
    """
    Create a complete product strategy canvas, using Nova Pro to populate unselected fields
    """
    if user_populated_fields is None:
        user_populated_fields = {}

    canvas = {}
    all_fields = list(CanvasField)

    # First, add the user-selected fields to the canvas
    for field in selected_fields:
        canvas[field.value] = {
            "description": get_field_definition(field),
            "content": user_populated_fields.get(field, "")
        }

    # Get unselected fields
    unselected_fields = [field for field in all_fields if field not in selected_fields]

    # Process fields with larger gaps between requests
    for field in unselected_fields:
        print(f"Using Bedrock to generate content for {field.value}...")

        # Build context from existing fields
        context_parts = []
        for f, data in canvas.items():
            if data["content"]:
                context_parts.append(f"{f}: {data['content']}")
        context = "\n".join(context_parts)

        try:
            generated_content = generate_bedrock_content(field, product_name, context)
            canvas[field.value] = {
                "description": get_field_definition(field),
                "content": generated_content
            }

            # Add a significant delay between requests to avoid throttling
            time.sleep(3)

        except Exception as e:
            print(f"Error generating content for {field.value}: {str(e)}")
            canvas[field.value] = {
                "description": get_field_definition(field),
                "content": "Error: Could not generate content"
            }
            time.sleep(5)  # Longer delay after an error

    return canvas


def generate_bedrock_content(field: CanvasField, product_name: str, context: str, max_retries: int = 3) -> str:
    """
    Generate content using Amazon Nova Pro with retry logic and proper response parsing
    """
    for attempt in range(max_retries):
        try:
            response = bedrock_runtime.invoke_model(
                modelId="amazon.nova-pro-v1:0",
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "text": f"""
                                    Generate content for the '{field.value}' section 
                                    of a Product Strategy Canvas for {product_name}.

                                    This section should address: {get_field_definition(field)}

                                    Consider this existing information from other sections:
                                    {context}

                                    Provide a focused, specific response that aligns with AWS 
                                    financial services industry best practices.
                                    """
                                }
                            ]
                        }
                    ],
                    "inferenceConfig": {
                        "temperature": 0.7,
                        "topP": 0.9,
                        "maxTokens": 500
                    }
                })
            )

            response_body = json.loads(response.get('body').read())

            # Nova Pro specific response parsing
            if 'output' in response_body:
                content = response_body['output']['message']['content'][0]['text']
                return content.strip()

            return "Error: Unexpected response format"

        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if attempt == max_retries - 1:
                    raise
                wait_time = (2 ** attempt) + random.random() * 2
                print(f"Rate limited. Waiting {wait_time:.2f} seconds before retry...")
                time.sleep(wait_time)
                continue
            else:
                raise

    return "Error: Could not generate content after multiple attempts"


def interactive_canvas_builder():
    """
    Interactive function to build a product strategy canvas with optional user inputs
    """
    print("Welcome to the Product Strategy Canvas Builder")
    product_name = input("Enter the product name: ")

    # Display available fields
    print("\nAvailable fields:")
    for i, field in enumerate(CanvasField, 1):
        print(f"{i}. {field.value}")

    # Get user selection
    selection = input("\nEnter the numbers of the fields you want to include (comma-separated, or 'all'): ")

    # Process field selection
    if selection.lower() == 'all':
        selected_fields = list(CanvasField)
    else:
        try:
            field_numbers = [int(x.strip()) for x in selection.split(',')]
            selected_fields = [list(CanvasField)[i - 1] for i in field_numbers]
        except (ValueError, IndexError):
            print("Invalid selection. Please enter valid numbers separated by commas.")
            return

    # Dictionary to store user-populated fields
    user_populated_fields = {}

    # Ask user if they want to provide input for any fields
    print("\nWould you like to provide input for any of the selected fields?")
    for field in selected_fields:
        while True:
            provide_input = input(f"Do you want to provide input for '{field.value}'? (y/n): ").lower()
            if provide_input in ['y', 'n']:
                break
            print("Please enter 'y' or 'n'")

        if provide_input == 'y':
            print(f"\nProvide input for {field.value}")
            print(f"This field answers: {get_field_definition(field)}")
            user_input = input("Your input: ").strip()
            if user_input:  # Only add if user provided non-empty input
                user_populated_fields[field] = user_input

    # Create the canvas with user-populated fields
    canvas = create_product_strategy_canvas(product_name, selected_fields, user_populated_fields)

    # Display the results
    display_canvas(canvas, product_name)


def display_canvas(canvas: Dict[str, Dict[str, str]], product_name: str):
    """
    Display the completed product strategy canvas
    """
    print(f"\nProduct Strategy Canvas for {product_name}")
    print("=" * 80)

    for field_name, field_data in canvas.items():
        print(f"\n{field_name}")
        print("-" * len(field_name))
        print(f"Description: {field_data['description']}")
        print(f"Content: {field_data['content']}")
        print()


if __name__ == "__main__":
    interactive_canvas_builder()
