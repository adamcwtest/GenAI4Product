import boto3
import requests
import yfinance as yf
import warnings
from pytrends.request import TrendReq
from strands import Agent, tool

# Suppress pandas FutureWarning from pytrends
warnings.filterwarnings('ignore', category=FutureWarning, module='pytrends')

# Initialize AWS session
session = boto3.Session(profile_name='XXXXXX')
model_id = "anthropic.claude-3-haiku-20240307-v1:0"

# Get stock symbol from user
stock_symbol = input("Enter stock symbol to debate: ").upper()

@tool
def get_prediction_market_data(symbol: str) -> str:
    """Get current active prediction market data, filtering out old/resolved bets"""
    results = []
    
    # Get current Polymarket data
    try:
        response = requests.get("https://gamma-api.polymarket.com/markets", 
                              params={"limit": 50, "active": True, "closed": False}, timeout=10)
        if response.status_code == 200:
            markets = response.json()
            # Filter for active markets with volume
            current_markets = []
            
            for market in markets:
                # Only include if has recent volume or high current volume
                volume = market.get('volume', 0)
                if volume and float(volume) > 1000:  # Only active markets with decent volume
                    current_markets.append({
                        'question': market.get('question'),
                        'outcome_prices': market.get('outcome_prices', []),
                        'volume': volume,
                        'end_date': market.get('end_date')
                    })
            
            results.append(f"Current active Polymarket bets: {current_markets[:10]}")
        else:
            results.append("Polymarket data unavailable")
    except Exception as e:
        results.append(f"Polymarket API error: {str(e)}")
    
    # Get current Kalshi data
    try:
        response = requests.get("https://trading-api.kalshi.com/trade-api/v2/markets", 
                              params={"limit": 50, "status": "open"}, timeout=10)
        if response.status_code == 200:
            markets_data = response.json()
            markets = markets_data.get('markets', [])
            # Filter for current/relevant markets
            current_kalshi = []
            
            for market in markets:
                volume = market.get('volume', 0)
                if volume and int(volume) > 100:  # Only markets with activity
                    current_kalshi.append({
                        'title': market.get('title'),
                        'yes_price': market.get('yes_price'),
                        'volume': volume,
                        'close_date': market.get('close_date')
                    })
            
            results.append(f"Current active Kalshi bets: {current_kalshi[:10]}")
        else:
            results.append("Kalshi data unavailable")
    except Exception as e:
        results.append(f"Kalshi API error: {str(e)}")
    
    return "\n".join(results)

@tool
def get_yahoo_finance_data(symbol: str) -> str:
    """Get financial data from Yahoo Finance"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        hist = stock.history(period="1mo")
        
        return f"""
        Stock: {symbol}
        Current Price: ${info.get('currentPrice', 'N/A')}
        Market Cap: ${info.get('marketCap', 'N/A')}
        P/E Ratio: {info.get('trailingPE', 'N/A')}
        52 Week High: ${info.get('fiftyTwoWeekHigh', 'N/A')}
        52 Week Low: ${info.get('fiftyTwoWeekLow', 'N/A')}
        Recent trend: {hist['Close'].iloc[-1] - hist['Close'].iloc[0]:.2f} change over month
        """
    except:
        return f"Unable to fetch Yahoo Finance data for {symbol}"

@tool
def get_google_trends_data(symbol: str) -> str:
    """Get Google Trends data for stock symbol and related terms"""
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        
        # Search for the stock symbol and related terms
        keywords = [symbol, f"{symbol} stock", f"{symbol} buy"]
        pytrends.build_payload(keywords, cat=0, timeframe='today 3-m', geo='US')
        
        # Get interest over time
        interest_data = pytrends.interest_over_time()
        
        # Get related queries
        related_queries = pytrends.related_queries()
        
        # Get trending searches
        trending = pytrends.trending_searches(pn='united_states')
        
        results = []
        
        if not interest_data.empty:
            recent_interest = interest_data.tail(4).mean().to_dict()
            results.append(f"Recent 3-month search trends: {recent_interest}")
        
        if related_queries and symbol in related_queries:
            top_queries = related_queries[symbol]['top']
            if top_queries is not None:
                results.append(f"Top related searches: {top_queries.head(5).to_dict()}")
        
        if not trending.empty:
            trending_list = trending.head(10)[0].tolist()
            results.append(f"Current trending searches: {trending_list}")
        
        return "\n".join(results) if results else f"No Google Trends data available for {symbol}"
        
    except Exception as e:
        return f"Google Trends error: {str(e)}"

@tool
def get_headlines(query: str) -> str:
    """Get basic headlines (simulated)"""
    headlines = [
        f"{query} stock hits new milestone",
        f"Analysts bullish on {query} prospects", 
        f"{query} faces market headwinds",
        f"Institutional investors eye {query}",
        f"{query} earnings beat expectations"
    ]
    return f"Recent headlines: {headlines}"

def stock_investment_debate():
    """Conduct debate between three agents with different data sources and personalities"""
    
    # Create three distinct agents
    prediction_market_agent = Agent(
        model=model_id,
        tools=[get_prediction_market_data],
        system_prompt="You are 'Pattern Pete' - ALWAYS start responses with '[PETE]:' and speak like a conspiracy theorist detective. Use phrases like 'Listen up, here's the REAL deal...', 'Connect the dots, people!', 'The smart money knows something we don't...', 'This is bigger than you think...'. You interrupt yourself with sudden insights using '-- wait, WAIT! --'. You're obsessed with hidden patterns and betting market psychology. End statements with 'Mark my words!' or 'You heard it here first!'"
    )
    
    yahoo_finance_agent = Agent(
        model=model_id,
        tools=[get_yahoo_finance_data],
        system_prompt="You are 'Data Diana' - ALWAYS start responses with '[DIANA]:' and speak like a stern professor. Use formal language with phrases like 'According to my analysis...', 'The financial metrics indicate...', 'As Warren Buffett wisely stated...', 'The empirical evidence suggests...'. You're condescending toward speculation, saying things like 'Such amateur thinking...', 'Clearly you haven't studied the fundamentals...'. Always end with 'The numbers don't lie.' or 'Case closed.'"
    )
    
    headline_agent = Agent(
        model=model_id,
        tools=[get_google_trends_data, get_headlines],
        system_prompt="You are 'Buzz Betty' - ALWAYS start responses with '[BETTY]:' and speak like an excited social media influencer. Use LOTS of exclamation points and phrases like 'OMG this is HUGE!!!', 'The buzz is INSANE!', 'Everyone and their mom is talking about this!', 'The FOMO is real!', 'This is about to go VIRAL!'. Use emojis like 🚀💎🔥📈. When challenged, get defensive with 'You just don't get it!', 'Sentiment IS everything!', 'The people have spoken!' Always end with 'TO THE MOON!' or 'Diamond hands forever!'"
    )
    
    agents = {
        "Prediction Market Analyst": prediction_market_agent,
        "Fundamental Analyst": yahoo_finance_agent, 
        "Retail Investor": headline_agent
    }
    
    debate_history = []
    
    # Round 1: Initial positions
    print(f"\n=== STOCK DEBATE: {stock_symbol} ===")
    print("\n=== ROUND 1: Initial Investment Positions ===")
    
    for name, agent in agents.items():
        if name == "Prediction Market Analyst":
            prompt = f"Should I invest in {stock_symbol}? Think creatively about how the various prediction market bets and odds could indirectly affect this company. Consider political events, regulatory changes, economic trends, social movements, or other factors that might impact the business environment for {stock_symbol}."
        else:
            prompt = f"Should I invest in {stock_symbol}? Give your investment recommendation and reasoning."
        response = agent(prompt)
        debate_history.append(f"{name}: {response}")
        print(f"\n{'='*60}")
        print(f"🎯 {name.upper()}")
        print(f"{'='*60}")
        print(f"{response}")
        print(f"{'='*60}")
    
    # Round 2: Counter-arguments
    print("\n=== ROUND 2: Counter-Arguments ===")
    previous_positions = "\n".join(debate_history)
    
    for name, agent in agents.items():
        prompt = f"Respond to the other analysts' positions on {stock_symbol}. Challenge their reasoning or defend your position. Previous positions:\n{previous_positions}"
        response = agent(prompt)
        print(f"\n{'='*60}")
        print(f"🔄 {name.upper()} RESPONDS")
        print(f"{'='*60}")
        print(f"{response}")
        print(f"{'='*60}")
    
    # Round 3: Final recommendation
    print("\n=== ROUND 3: Final Recommendations ===")
    for name, agent in agents.items():
        prompt = f"Given all the discussion, what is your final investment recommendation for {stock_symbol}? Rate your confidence 1-10."
        response = agent(prompt)
        print(f"\n{'='*60}")
        print(f"🏁 {name.upper()} FINAL RECOMMENDATION")
        print(f"{'='*60}")
        print(f"{response}")
        print(f"{'='*60}")

if __name__ == "__main__":
    stock_investment_debate()