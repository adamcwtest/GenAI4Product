"""
Financial Services News Analysis Tool using AWS Bedrock and Nova Act 
https://nova.amazon.com/act

This module provides functionality to search for news headlines and analyze them
using AWS Bedrock's AI capabilities. It's designed to help financial services product
managers identify market trends and match them with relevant AWS features.
"""

from nova_act import NovaAct
import boto3

# Use existing session and model configuration
session = boto3.Session(profile_name='XXXXXXXX')
bedrock_runtime = session.client(service_name='bedrock-agent-runtime', region_name='us-east-1')
bedrock_agent = session.client(service_name='bedrock-agent', region_name='us-east-1')  # Add this line
model_id = "amazon.nova-pro-v1:0"
model_arn = f'arn:aws:bedrock:us-east-1::foundation-model/{model_id}'
kb_name = 'XXXXXXXX'
kb = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_name)  # Use bedrock_agent instead of bedrock_runtime


def run_nova_news_search(search_term):
    headlines = []

    with NovaAct(starting_page="https://news.google.com") as nova:
        # First perform the search
        search_result = nova.act(f"""
        1. Search for "{search_term}"
        2. Wait for results to load
        """)

        # Apply the date filter
        date_filter_result = nova.act("""
        1. Click on the Tools or date filter button
        2. Select "Past week" from the dropdown
        3. Wait for results to refresh
        """)

        try:
            # Read headlines after date filter is applied
            read_result = nova.act("""
            Stay on the current page.
            List all visible news headlines.
            Do not click on any headlines.
            Return the headlines as a comma-separated list.
            """)

            if hasattr(read_result, 'response') and read_result.response:
                headlines = [h.strip() for h in read_result.response.split(',')]

            # Clean up headlines
            headlines = [h for h in headlines if len(h) > 10 and 'click' not in h.lower()]

        except Exception as e:
            print(f"Error collecting headlines: {str(e)}")

    return headlines


def analyze_themes_with_bedrock(headlines):
    if not headlines:
        return "No headlines found to analyze."

    try:
        # Convert headlines array to a single string
        headlines_text = "\n".join(headlines)

        prompt = f"""As an AWS product manager selecting features for financial services customers:

        1. First, analyze these news headlines:
        {headlines_text}

        2. Identify the top 3-5 recurring themes or trends in these headlines.

        3. Then, for EACH identified theme/trend:
           a. Select precisely ONE matching AWS service feature from our financial services customer knowledge base
           b. Clearly explain how this specific feature directly addresses the identified news theme/trend
           c. Reference specific customer requests from our knowledge base that align with this need

        Please format your response as follows:

        NEWS ANALYSIS:
        - THEME 1: [Concise theme description from headlines]
          • KEY HEADLINES: [2-3 specific headlines supporting this theme]
          • TREND SUMMARY: [Brief explanation of this trend's significance]

        - THEME 2: [Repeat format]
          • KEY HEADLINES: [2-3 specific headlines supporting this theme]
          • TREND SUMMARY: [Brief explanation of this trend's significance]

        [Continue for all identified themes]

        FEATURE RECOMMENDATIONS:
        - FOR THEME 1: [Restate theme]
          • RECOMMENDED AWS FEATURE: [Specific feature name from knowledge base]
          • CUSTOMER REQUEST ALIGNMENT: [Reference specific customer request(s)]
          • SOLUTION FIT: [How this feature directly addresses the news theme/trend]

        - FOR THEME 2: [Repeat format]
          • RECOMMENDED AWS FEATURE: [Specific feature name from knowledge base]
          • CUSTOMER REQUEST ALIGNMENT: [Reference specific customer request(s)]
          • SOLUTION FIT: [How this feature directly addresses the news theme/trend]

        [Continue for all themes]

        STRATEGIC PRIORITIZATION:
        [Brief assessment of which theme+feature pairing appears most urgent based on news volume and customer demand]
        """

        response = bedrock_runtime.retrieve_and_generate(
            input={
                "text": prompt
            },
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": kb_name,
                    "modelArn": model_arn,
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {
                            "numberOfResults": 3
                        }
                    }
                }
            }
        )

        # The response is already a dictionary, no need for json.loads()
        return response.get('output', {}).get('text', 'No analysis generated')

    except Exception as e:
        print(f"Error analyzing themes: {str(e)}")
        return None


def main():
    while True:
        print("\nEnter a news search term (or 'quit' to exit):")
        user_input = input("> ").strip()

        if user_input.lower() == 'quit':
            break

        if user_input:
            print(f"\nSearching news for: {user_input}")
            try:
                headlines = run_nova_news_search(user_input)

                if headlines:
                    print("\nHeadlines found:")
                    for i, headline in enumerate(headlines, 1):
                        print(f"{i}. {headline}")

                    # Add back the Bedrock analysis
                    print("\nAnalyzing themes with Amazon Bedrock...")
                    analysis = analyze_themes_with_bedrock(headlines)
                    if analysis:
                        print("\nAnalysis Results:")
                        print(analysis)
                    else:
                        print("Unable to generate analysis")
                else:
                    print("No headlines found")

            except Exception as e:
                print(f"Error during search: {str(e)}")
                print("Please try again")
        else:
            print("Please enter a valid search term")


if __name__ == "__main__":
    main()

