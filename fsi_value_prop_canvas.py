import boto3
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class CanvasComponent(Enum):
    CUSTOMER_JOBS = "customer_jobs"
    CUSTOMER_PAINS = "customer_pains"
    CUSTOMER_GAINS = "customer_gains"
    PRODUCTS_SERVICES = "products_services"
    PAIN_RELIEVERS = "pain_relievers"
    GAIN_CREATORS = "gain_creators"


@dataclass
class ValuePropositionCanvas:
    # Customer Profile
    customer_jobs: List[str]
    customer_pains: List[str]
    customer_gains: List[str]
    # Value Map
    products_services: List[str]
    pain_relievers: List[str]
    gain_creators: List[str]


class FSIValuePropositionAnalyzer:
    def __init__(self):
        try:
            self.session = boto3.Session(
                profile_name='XXXXXXXX'
            )
            self.bedrock_runtime = self.session.client(
                service_name='bedrock-runtime',
                region_name='us-east-1'
            )
            self.model_id = "anthropic.claude-v2"

        except Exception as e:
            print(f"Error initializing AWS services: {e}")
            raise

    def _get_bedrock_response(self, prompt: str) -> str:
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.7,
                "top_p": 1
            })

            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=body
            )

            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']

        except Exception as e:
            print(f"Error getting Bedrock response: {e}")
            raise

    def analyze_component(self, component: CanvasComponent, user_input: str) -> List[str]:
        prompts = {
            # Customer Profile components
            CanvasComponent.CUSTOMER_JOBS: """Identify the specific functional, emotional, and social jobs financial institutions are trying to complete with cloud-based solutions:
                                            1. Extract both explicit jobs (stated objectives) and implicit jobs (unstated needs)
                                            2. Prioritize jobs based on their criticality to daily operations, regulatory compliance, and competitive advantage
                                            3. Distinguish between operational jobs (e.g., data processing), social jobs (e.g., market positioning), and emotional jobs (e.g., confidence in security)

                                            Format each job with importance level (High/Medium/Low) and job type:
                                            - [Importance] [Job Type]: [Specific job description with action verb] """,

            CanvasComponent.CUSTOMER_PAINS: """Analyze the specific obstacles, risks, and negative experiences financial institutions encounter:
                                            1. Identify tangible pains (measurable costs, time delays, compliance failures)
                                            2. Capture intangible pains (frustrations, fears, reputation concerns)
                                            3. Assess the severity of each pain and its frequency of occurrence

                                            Format each pain with severity (Severe/Moderate/Minor) and occurrence pattern:
                                            - [Severity] [Frequency]: [Specific pain point with contextual impact] """,

            CanvasComponent.CUSTOMER_GAINS: """Extract the specific outcomes, benefits and positive experiences financial institutions expect:
                                            1. Categorize as essential gains (must-have), expected gains (should-have), or desired gains (nice-to-have)
                                            2. Include both quantitative gains (measurable improvements) and qualitative gains (experiences)
                                            3. Identify how gains translate to competitive advantage or organizational transformation

                                            Format each gain with importance category and measurability:
                                            - [Importance Category] [Measurable/Experiential]: [Specific gain with outcome description] """,

            # Value Map components
            CanvasComponent.PRODUCTS_SERVICES: """Enumerate the tangible offerings and their specific capabilities that address identified jobs:
                                               1. Differentiate between core platform components and specialized modules
                                               2. Highlight unique technological differentiators and proprietary features
                                               3. Indicate whether each offering is primary, secondary, or complementary

                                               Format each product/service with its classification and primary job addressed:
                                               - [Component Type] [Offering Name]: [Specific capabilities and how they facilitate which jobs] """,

            CanvasComponent.PAIN_RELIEVERS: """Detail how specific features directly address and mitigate each customer pain point:
                                            1. Link each pain reliever to specific customer pains identified earlier
                                            2. Quantify the extent of relief provided where possible (e.g., reduction percentages, time saved)
                                            3. Explain the mechanism through which relief is delivered

                                            Format each pain reliever with referenced pain point and relief mechanism:
                                            - [Feature Name] [Addresses Pain]: [How specifically it eliminates or reduces the pain, with metrics where possible] """,

            CanvasComponent.GAIN_CREATORS: """Articulate how specific capabilities amplify or create each customer gain:
                                          1. Connect each gain creator to specific customer gains identified earlier
                                          2. Differentiate between direct gain enablers and gain enhancers
                                          3. Include both immediate and long-term gain creation potential

                                          Format each gain creator with referenced gain and creation mechanism:
                                          - [Feature/Capability] [Enables Gain]: [How specifically it creates or amplifies the gain, with timeframe for realization] """
        }

        prompt = f"{prompts[component]}\n\nContext: {user_input}\n\nProvide the analysis as a bullet-point list, with each item on a new line starting with a dash (-)."
        response = self._get_bedrock_response(prompt)

        # Parse the response into a list of items
        items = [item.strip('- ').strip() for item in response.split('\n') if item.strip().startswith('-')]
        return items

    def create_canvas(self, jobs_input: str, pains_input: str, gains_input: str,
                      products_services_input: str, pain_relievers_input: str,
                      gain_creators_input: str) -> ValuePropositionCanvas:
        canvas = ValuePropositionCanvas(
            # Customer Profile
            customer_jobs=self.analyze_component(CanvasComponent.CUSTOMER_JOBS, jobs_input),
            customer_pains=self.analyze_component(CanvasComponent.CUSTOMER_PAINS, pains_input),
            customer_gains=self.analyze_component(CanvasComponent.CUSTOMER_GAINS, gains_input),
            # Value Map
            products_services=self.analyze_component(CanvasComponent.PRODUCTS_SERVICES, products_services_input),
            pain_relievers=self.analyze_component(CanvasComponent.PAIN_RELIEVERS, pain_relievers_input),
            gain_creators=self.analyze_component(CanvasComponent.GAIN_CREATORS, gain_creators_input)
        )
        return canvas


def main():
    analyzer = FSIValuePropositionAnalyzer()

    print("\nValue Proposition Canvas Generator for Financial Services")
    print("======================================================")

    print("\n=== CUSTOMER PROFILE ===")

    print("\nPlease describe the customer jobs/tasks (What does your customer try to get done?):")
    jobs_input = input()

    print("\nPlease describe the customer pains/challenges (What are your customer's pain points and frustrations?):")
    pains_input = input()

    print(
        "\nPlease describe the desired customer gains/benefits (What outcomes and benefits does your customer want?):")
    gains_input = input()

    print("\n=== VALUE MAP ===")

    print("\nPlease describe your products and services (What do you offer to customers?):")
    products_services_input = input()

    print("\nPlease describe your pain relievers (How do your offerings address customer pains?):")
    pain_relievers_input = input()

    print("\nPlease describe your gain creators (How do your offerings create customer gains?):")
    gain_creators_input = input()

    print("\nAnalyzing inputs...")
    canvas = analyzer.create_canvas(
        jobs_input, pains_input, gains_input,
        products_services_input, pain_relievers_input, gain_creators_input
    )

    print("\n=== Value Proposition Canvas Analysis ===")

    print("\n--- CUSTOMER PROFILE ---")

    print("\nCustomer Jobs:")
    for job in canvas.customer_jobs:
        print(f"- {job}")

    print("\nCustomer Pains:")
    for pain in canvas.customer_pains:
        print(f"- {pain}")

    print("\nCustomer Gains:")
    for gain in canvas.customer_gains:
        print(f"- {gain}")

    print("\n--- VALUE MAP ---")

    print("\nProducts & Services:")
    for product_service in canvas.products_services:
        print(f"- {product_service}")

    print("\nPain Relievers:")
    for pain_reliever in canvas.pain_relievers:
        print(f"- {pain_reliever}")

    print("\nGain Creators:")
    for gain_creator in canvas.gain_creators:
        print(f"- {gain_creator}")


if __name__ == "__main__":
    main()
