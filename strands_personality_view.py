import boto3
from strands import Agent, tool
# Coordinating multiple agents for debate

# Initialize AWS sessions and clients
session = boto3.Session(profile_name='XXXXXX')
bedrock_agent_runtime = session.client(service_name='bedrock-agent-runtime', region_name='us-east-1')

model_id = "anthropic.claude-3-haiku-20240307-v1:0"

# Big Five personality types with their key characteristics
personality_traits = {
    "Openness": "creative, innovative, values novelty",
    "Conscientiousness": "organized, detail-oriented, systematic", 
    "Extraversion": "social, collaborative, outgoing",
    "Agreeableness": "cooperative, empathetic, team-focused",
    "Neuroticism": "cautious, risk-aware, security-focused"
}

product = input("What product are you building? ")
features = input("List five to ten key features of your product separated by commas: ")

@tool
def prioritize_features(features_list: str, criteria: str) -> str:
    """Tool to systematically prioritize features based on given criteria"""
    return f"Prioritizing {features_list} based on {criteria}"

@tool
def risk_assessment(feature: str) -> str:
    """Tool to assess risks associated with a feature"""
    return f"Risk analysis for {feature}: evaluating security, compliance, and implementation risks"

@tool
def user_feedback_analysis(feature: str) -> str:
    """Tool to analyze user feedback and social impact"""
    return f"User feedback analysis for {feature}: examining user engagement and social aspects"

def demonstrate_personality_product_management():
    """Demonstrate agent debate coordinating personality-based agents"""
    
    scenario = f"A financial services company needs to prioritize features for their ({product}): ({features})."
    
    # Create specialized agents for debate
    agents = {}
    
    for trait, description in personality_traits.items():
        if trait == "Conscientiousness":
            agent = Agent(
                model=model_id,
                tools=[prioritize_features, risk_assessment],
                system_prompt=f"You are a {description} product manager in a team debate. Use systematic analysis and defend your prioritization with data."
            )
        elif trait == "Neuroticism":
            agent = Agent(
                model=model_id,
                tools=[risk_assessment],
                system_prompt=f"You are a {description} product manager in a team debate. Focus on risks and challenge others' assumptions about security."
            )
        elif trait == "Extraversion":
            agent = Agent(
                model=model_id,
                tools=[user_feedback_analysis],
                system_prompt=f"You are a {description} product manager in a team debate. Advocate for user engagement and respond to others' points."
            )
        else:
            agent = Agent(
                model=model_id,
                system_prompt=f"You are a {description} product manager in a team debate. Apply your personality traits and engage with others' viewpoints."
            )
        
        agents[trait] = agent
    
    # Conduct debate rounds
    debate_history = []
    
    # Round 1: Initial positions
    print("\n=== DEBATE ROUND 1: Initial Positions ===")
    for trait, agent in agents.items():
        prompt = f"State your initial feature prioritization for: {scenario}"
        response = agent(prompt)
        debate_history.append(f"{trait}: {response}")
        print(f"\n{trait} Agent: {response}")
    
    # Round 2: Responses to others
    print("\n=== DEBATE ROUND 2: Responses and Rebuttals ===")
    previous_positions = "\n".join(debate_history)
    
    for trait, agent in agents.items():
        prompt = f"Respond to your colleagues' positions and defend/modify your prioritization. Previous positions:\n{previous_positions}"
        response = agent(prompt)
        print(f"\n{trait} Agent Response: {response}")
    
    # Round 3: Consensus building
    print("\n=== DEBATE ROUND 3: Seeking Consensus ===")
    for trait, agent in agents.items():
        prompt = f"Given all perspectives shared, what compromises can you make while staying true to your personality? Work toward team consensus on feature prioritization."
        response = agent(prompt)
        print(f"\n{trait} Agent Consensus: {response}")
    
    return "Debate completed - see output above"

# Execute demonstration
if __name__ == "__main__":
    result = demonstrate_personality_product_management()
    print(f"\n=== Final Result ===\n{result}")