import os
import logging
from datetime import datetime, timedelta
import requests
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("financial_markets_summary.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Custom Tavily Search Tool since import path changed
class TavilySearchTool(BaseTool):
    name: str = "Tavily Search"
    description: str = "Search the web for relevant information using Tavily API"
    
    class TavilySearchToolSchema(BaseModel):
        query: str = Field(..., description="Search query to look up")
        
    args_schema: Type[BaseModel] = TavilySearchToolSchema
    
    def _run(self, query: str) -> str:
        try:
            api_key = os.getenv("TAVILY_API_KEY")
            if not api_key:
                return "Tavily API key not found. Please set TAVILY_API_KEY environment variable."
            
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": api_key,
                "query": query,
                "search_depth": "advanced",
                "include_answer": True,
                "include_images": True,
                "max_results": 5
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Format the results
            if data.get("results"):
                results = []
                for i, result in enumerate(data["results"][:3], 1):
                    results.append(f"{i}. {result.get('title', 'No title')}")
                    results.append(f"   URL: {result.get('url', 'No URL')}")
                    results.append(f"   Content: {result.get('content', 'No content')[:200]}...")
                    results.append("")
                
                if data.get("answer"):
                    results.insert(0, f"ANSWER: {data['answer']}\n\nSEARCH RESULTS:")
                
                return "\n".join(results)
            else:
                return "No results found for the query."
                
        except Exception as e:
            logger.error(f"Tavily search error: {str(e)}")
            return f"Search failed: {str(e)}"

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
        
    def send_message(self, text, parse_mode="HTML"):
        """Send message to Telegram channel"""
        if not self.token or not self.channel_id:
            logger.warning("Telegram credentials not found. Skipping Telegram send.")
            return False
            
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        
        # Telegram has a message length limit (4096 characters)
        if len(text) > 4096:
            parts = self.split_message(text)
            for part in parts:
                if not self.send_single_message(part, parse_mode):
                    return False
            return True
        else:
            return self.send_single_message(text, parse_mode)
    
    def send_single_message(self, text, parse_mode):
        """Send a single message to Telegram"""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        
        payload = {
            "chat_id": self.channel_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Message successfully sent to Telegram")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send message to Telegram: {str(e)}")
            return False
    
    def split_message(self, text, max_length=4096):
        """Split long message into parts"""
        parts = []
        while text:
            if len(text) <= max_length:
                parts.append(text)
                break
            else:
                # Find the last space within the limit
                split_index = text.rfind('\n', 0, max_length)
                if split_index == -1:
                    split_index = text.rfind(' ', 0, max_length)
                if split_index == -1:
                    split_index = max_length
                
                parts.append(text[:split_index])
                text = text[split_index:].lstrip()
        
        return parts

class FinancialMarketsCrew:
    def __init__(self):
        self.setup_environment()
        self.initialize_tools()
        self.telegram_bot = TelegramBot()
        
    def setup_environment(self):
        """Set up environment variables"""
        # Try to load from .env file if exists
        try:
            from dotenv import load_dotenv
            load_dotenv()
            logger.info("Loaded environment variables from .env file")
        except ImportError:
            logger.warning("python-dotenv not installed, using system environment variables")
        
        # Set default values if not found
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
        os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY", "your-tavily-api-key-here")
        os.environ["TELEGRAM_BOT_TOKEN"] = os.getenv("TELEGRAM_BOT_TOKEN", "your-telegram-bot-token-here")
        os.environ["TELEGRAM_CHANNEL_ID"] = os.getenv("TELEGRAM_CHANNEL_ID", "your-telegram-channel-id-here")
        
    def initialize_tools(self):
        """Initialize tools for agents"""
        self.search_tool = TavilySearchTool()
        
    def create_agents(self):
        """Create all the agents for the crew"""
        
        # Search Agent - finds financial news
        self.search_agent = Agent(
            role="Financial News Researcher",
            goal="Find the most relevant US financial news from the last trading day",
            backstory="You are an expert financial researcher with deep knowledge of markets and economics. "
                    "You know how to find the most impactful news that moves markets.",
            tools=[self.search_tool],
            verbose=True,
            allow_delegation=False
        )
        
        # Summary Agent - creates concise summary
        self.summary_agent = Agent(
            role="Financial Markets Analyst",
            goal="Create a concise summary (under 500 words) of the most important financial news and trading activity",
            backstory="You are a seasoned financial analyst who can distill complex market information into "
                    "clear, actionable insights for traders and investors.",
            verbose=True,
            allow_delegation=False
        )
        
        # Formatting Agent - formats content for Telegram
        self.formatting_agent = Agent(
            role="Content Formatter for Telegram",
            goal="Format the financial summary for optimal presentation on Telegram with proper formatting",
            backstory="You are a content specialist who knows how to format messages for Telegram with "
                    "proper HTML formatting, emojis, and structure that works well on mobile devices.",
            verbose=True,
            allow_delegation=False
        )
        
        # Translation Agent - translates content
        self.translation_agent = Agent(
            role="Multilingual Financial Translator",
            goal="Translate financial summaries into Arabic, Hindi, and Hebrew while maintaining format and accuracy",
            backstory="You are a professional translator specializing in financial content with fluency in "
                    "Arabic, Hindi, Hebrew, and English. You understand financial terminology in all these languages.",
            verbose=True,
            allow_delegation=False
        )
    
    def create_tasks(self):
        """Create tasks for each agent"""
        
        # Get the date for the search (previous trading day)
        search_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Task for Search Agent
        self.search_task = Task(
            description=f"Search for the most important US financial news and market movements from {search_date}. "
                       "Focus on major indices (DJIA, S&P 500, NASDAQ), key economic indicators, "
                       "significant corporate earnings, and Federal Reserve announcements. "
                       "Use the search tool to find relevant information from reputable financial sources "
                       "like Bloomberg, Reuters, CNBC, and Financial Times.",
            agent=self.search_agent,
            expected_output="A comprehensive list of the day's most important financial news with sources and URLs."
        )
        
        # Task for Summary Agent
        self.summary_task = Task(
            description="Create a concise summary (under 500 words) of the financial markets based on the research. "
                       "Highlight the most important news, market movements, and potential implications. "
                       "Structure the summary with clear sections: Market Overview, Key News, and Outlook. "
                       "Include key data points like index performance percentages.",
            agent=self.summary_agent,
            expected_output="A well-structured financial markets summary under 500 words with clear sections."
        )
        
        # Task for Formatting Agent
        self.formatting_task = Task(
            description="Format the financial summary for Telegram using HTML formatting. "
                       "Use bold for headings, emojis to make it visually appealing, and proper line breaks. "
                       "Ensure the message is optimized for mobile viewing and stays within Telegram's character limits. "
                       "Include relevant emojis like 📈, 📉, 💰, 🏦 to make it engaging.",
            agent=self.formatting_agent,
            expected_output="A beautifully formatted Telegram message with HTML tags and emojis."
        )
        
        # Task for Translation Agent
        self.translation_task = Task(
            description="Translate the formatted financial summary into Arabic, Hindi, and Hebrew. "
                       "Maintain the original format, structure, and financial terminology accuracy. "
                       "Provide all three translations along with the original English version.",
            agent=self.translation_agent,
            expected_output="The financial summary translated into Arabic, Hindi, and Hebrew while maintaining the original format."
        )
    
    def run_crew(self):
        """Execute the crew workflow"""
        try:
            logger.info("Initializing Financial Markets Crew...")
            
            # Create agents and tasks
            self.create_agents()
            self.create_tasks()
            
            # Form the crew
            financial_crew = Crew(
                agents=[
                    self.search_agent,
                    self.summary_agent,
                    self.formatting_agent,
                    self.translation_agent
                ],
                tasks=[
                    self.search_task,
                    self.summary_task,
                    self.formatting_task,
                    self.translation_task
                ],
                process=Process.sequential,
                verbose=True
            )
            
            # Execute the crew
            logger.info("Starting crew execution...")
            result = financial_crew.kickoff()
            
            # Send to Telegram
            self.send_to_telegram(result)
            
            logger.info("Crew execution completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in crew execution: {str(e)}")
            # Return a sample output for demonstration
            return self.get_sample_output()
    
    def send_to_telegram(self, message):
        """Send message to Telegram channel"""
        success = self.telegram_bot.send_message(message)
        if success:
            logger.info("Message successfully sent to Telegram")
        else:
            logger.error("Failed to send message to Telegram")
            # For demo purposes, print what would have been sent
            print("="*50)
            print("TELEGRAM MESSAGE (DEMO):")
            print("="*50)
            print(message)
            print("="*50)
        
        return success
    
    def get_sample_output(self):
        """Return a sample output for demonstration purposes"""
        return """
<b>📊 Daily Financial Markets Summary</b>
<i>December 15, 2023 | US Markets Close</i>

<b>📈 Market Overview:</b>
U.S. stocks closed mixed on Thursday as investors digested the Federal Reserve's policy decision. The Dow Jones Industrial Average rose 0.4%, while the S&P 500 edged up 0.1%. The Nasdaq Composite fell 0.3% as tech stocks faced pressure.

<b>🔑 Key News:</b>
• Federal Reserve held interest rates steady but signaled potential cuts in 2024
• Retail sales data came in stronger than expected, rising 0.6% in November
• Adobe shares dropped 6% after the company's revenue forecast disappointed investors
• Oil prices climbed 2.3% amid Middle East supply concerns

<b>📊 Major Indices Performance:</b>
• Dow Jones: +0.4% (36,577 points)
• S&P 500: +0.1% (4,643 points)
• Nasdaq: -0.3% (14,533 points)
• Russell 2000: +0.8% (1,923 points)

<b>🔮 Outlook:</b>
Markets are likely to remain volatile as investors assess the Fed's pivot and economic data. Focus will shift to upcoming housing data and consumer sentiment figures.

<b>🌐 Translations:</b>
<code>Arabic:</code>
ملخص أسواق المال اليومي: ارتفع مؤشر داو جونز 0.4٪ بينما انخفض Nasdaq 0.3٪. أبقى الاحتياطي الفيدرالي الأسعار دون تغيير لكنه أشار إلى تخفيضات محتملة في 2024.

<code>Hindi:</code>
दैनिक वित्तीय बाजार सारांश: डॉव जोन्स 0.4% बढ़ा जबकि Nasdaq 0.3% गिरा। फेडरल रिजर्व ने दरें अपरिवर्तित रखीं लेकिन 2024 में संभावित कटौती का संकेत दिया।

<code>Hebrew:</code>
סיכום שווקים פיננסיים יומי: Dow Jones עלה 0.4% while Nasdaq ירד 0.3%. הפדרל ריזרב השאיר את הריביות ללא שינוי אך רמז לקיצוצים אפשריים ב-2024.

#FinancialMarkets #Investing #Trading #Stocks
"""

# Example usage
if __name__ == "__main__":
    try:
        # Initialize and run the crew
        financial_crew = FinancialMarketsCrew()
        result = financial_crew.run_crew()
        
        # Print the result
        print("Financial Markets Summary Result:")
        print(result)
        
    except Exception as e:
        logger.error(f"Failed to generate financial summary: {str(e)}")
        print(f"An error occurred: {str(e)}")