import os
import re
from io import BytesIO
from typing import Dict, List, Optional, Any
import requests
import fitz
from dotenv import load_dotenv
from tavily import TavilyClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
os.environ["GROQ_API_KEY"] = GROQ_API_KEY
os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

tavily_client = TavilyClient(TAVILY_API_KEY)


COMPANIES = {
    "pfc": {
        "name": "Power Finance Corporation",
        "symbol": "PFC",
        "screener_url": "https://www.screener.in/company/PFC/consolidated/",
        "search_terms": ["Power Finance Corporation", "PFC Limited", "PFC India"]
    },
    "rec": {
        "name": "Rural Electrification Corporation",
        "symbol": "RECLTD",
        "screener_url": "https://www.screener.in/company/RECLTD/consolidated/",
        "search_terms": ["Rural Electrification Corporation", "REC Limited", "REC India"]
    },
    "reliance": {
        "name": "Reliance Industries Limited",
        "symbol": "RELIANCE",
        "screener_url": "https://www.screener.in/company/RELIANCE/consolidated/",
        "search_terms": ["Reliance Industries", "RIL", "Mukesh Ambani"]
    },
    "adani_green": {
        "name": "Adani Green Energy Limited",
        "symbol": "ADANIGREEN",
        "screener_url": "https://www.screener.in/company/ADANIGREEN/consolidated/",
        "search_terms": ["Adani Green Energy", "AGEL", "Adani Green"]
    },
    "hdfc_bank": {
        "name": "HDFC Bank Limited",
        "symbol": "HDFCBANK",
        "screener_url": "https://www.screener.in/company/HDFCBANK/consolidated/",
        "search_terms": ["HDFC Bank", "HDFCBANK", "HDFC Banking"]
    }
}

def get_company_config(company_query: str) -> Optional[Dict]:
    """Get company configuration based on user query"""
    query_lower = company_query.lower()
    
    for key, config in COMPANIES.items():
        if (config["symbol"].lower() in query_lower or 
            config["name"].lower() in query_lower or
            any(term.lower() in query_lower for term in config["search_terms"])):
            return config
    
    return None


def tavily_search_financial_news(company_config: Dict, days: int = 30, max_results: int = 10) -> Dict[str, Any]:
    """
    Search for financial news about a specific company using Tavily Search
    """
    try:
        company_name = company_config["name"]
        search_terms = company_config["search_terms"]
        
        search_queries = [
            f"{company_name} financial results earnings",
            f"{company_name} stock price movement",
            f"{search_terms[0]} latest news"
        ]
        
        all_results = []
        for query in search_queries:
            try:
                response = tavily_client.search(
                    query=query,
                    topic="news",
                    search_depth="advanced",
                    max_results=max_results // len(search_queries),
                    days=days,
                    include_answer=True,
                    include_raw_content=True,
                    include_images=False
                )
                
                if response.get("results"):
                    all_results.extend(response["results"])
                    
            except Exception as e:
                print(f"Error in search query '{query}': {e}")
                continue
        
        return {
            "company": company_name,
            "results": all_results[:max_results],
            "total_found": len(all_results)
        }
        
    except Exception as e:
        return {"error": f"Failed to search news: {str(e)}"}

def tavily_extract_financial_data(company_config: Dict) -> Dict[str, Any]:
    """
    Extract financial data from screener.in using Tavily Extract
    """
    try:
        url = company_config["screener_url"]
        
        response = tavily_client.extract(
            urls=[url],
            extract_depth="advanced",
            format="markdown",
            include_images=False
        )
        
        if response.get("results") and len(response["results"]) > 0:
            return {
                "company": company_config["name"],
                "url": url,
                "content": response["results"][0].get("raw_content", ""),
                "success": True
            }
        else:
            return {
                "company": company_config["name"],
                "error": "No financial data extracted",
                "success": False
            }
            
    except Exception as e:
        return {
            "company": company_config["name"],
            "error": f"Failed to extract financial data: {str(e)}",
            "success": False
        }

def tavily_crawl_company_websites(company_config: Dict, max_depth: int = 2) -> Dict[str, Any]:
    """
    Crawl company's investor relations pages using Tavily Crawl
    """
    try:
        company_name = company_config["name"]
        
        search_response = tavily_client.search(
            query=f"{company_name} investor relations official website",
            search_depth="basic",
            max_results=5,
            include_raw_content=False
        )
        
        crawl_results = []
        for result in search_response.get("results", [])[:2]:
            try:
                url = result.get("url", "")
                if any(domain in url for domain in ["investor", "annual", "financial", "results"]):
                    
                    crawl_response = tavily_client.crawl(
                        url=url,
                        max_depth=max_depth,
                        max_breadth=10,
                        limit=20,
                        instructions=f"Find financial reports, earnings, and investor information for {company_name}",
                        extract_depth="basic",
                        format="markdown"
                    )
                    
                    if crawl_response.get("results"):
                        crawl_results.extend(crawl_response["results"])
                        
            except Exception as e:
                print(f"Error crawling {url}: {e}")
                continue
        
        return {
            "company": company_name,
            "crawled_pages": len(crawl_results),
            "results": crawl_results
        }
        
    except Exception as e:
        return {"error": f"Failed to crawl company websites: {str(e)}"}

def tavily_map_financial_resources(company_config: Dict) -> Dict[str, Any]:
    """
    Map financial resources and reports using Tavily Map
    """
    try:
        company_name = company_config["name"]
        
        search_response = tavily_client.search(
            query=f"{company_name} annual report financial statements BSE NSE",
            search_depth="basic",
            max_results=3
        )
        
        mapped_resources = []
        for result in search_response.get("results", []):
            try:
                url = result.get("url", "")
                
                map_response = tavily_client.map(
                    url=url,
                    max_depth=2,
                    max_breadth=15,
                    limit=30,
                    instructions=f"Map financial documents and reports for {company_name}"
                )
                
                if map_response.get("results"):
                    mapped_resources.append({
                        "base_url": map_response.get("base_url", ""),
                        "discovered_urls": map_response["results"]
                    })
                    
            except Exception as e:
                print(f"Error mapping {url}: {e}")
                continue
        
        return {
            "company": company_name,
            "mapped_sites": len(mapped_resources),
            "resources": mapped_resources
        }
        
    except Exception as e:
        return {"error": f"Failed to map financial resources: {str(e)}"}

def get_transcript_data(company_config: Dict) -> Dict[str, Any]:
    """
    Extract earnings call transcript data for a company
    """
    try:
        financial_data = tavily_extract_financial_data(company_config)
        
        if not financial_data.get("success"):
            return {"error": "Could not extract base financial data"}
        
        content = financial_data["content"]
        
        url_pattern = r'\[Transcript\]\((.*?)\)'
        urls = re.findall(url_pattern, content)
        
        if not urls:
            return {"error": "No transcript URLs found"}
        
        transcript_url = urls[0].strip().split()[0] if urls[0] else ""
        
        if transcript_url:
            transcript_content = extract_pdf_text(transcript_url)
            transcript_summary = analyze_transcript_with_llm(transcript_content, company_config["name"])
            
            return {
                "company": company_config["name"],
                "transcript_url": transcript_url,
                "transcript_content": transcript_content,
                "transcript_summary": transcript_summary,
                "success": True
            }
        else:
            return {"error": "Invalid transcript URL"}
            
    except Exception as e:
        return {"error": f"Failed to get transcript data: {str(e)}"}

def extract_pdf_text(url: str) -> str:
    """Extract text from PDF URL"""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        pdf_stream = BytesIO(response.content)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")

        text = ""
        for page in doc:
            text += page.get_text()

        return text.strip()
        
    except Exception as e:
        return f"Error extracting PDF text: {str(e)}"

def analyze_transcript_with_llm(text: str, company_name: str) -> str:
    """
    Analyze transcript using LLM with intelligent text splitting
    """
    try:
        if len(text) < 1000:
            return "Transcript too short for meaningful analysis"
        
        text_length = len(text)
        mid_point = text_length // 2
        
        break_point = mid_point
        for i in range(mid_point, min(mid_point + 1000, text_length)):
            if text[i] in '.!\n':
                break_point = i + 1
                break
        
        text_part1 = text[:break_point]
        text_part2 = text[break_point:]
        
        groq_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_retries=2,
        )

        messages_part1 = [
            SystemMessage(content=(
                f"You are analyzing an earnings call transcript for {company_name}. "
                "This is PART 1 of 2. Focus on:\n"
                "- Key financial highlights and metrics\n"
                "- Management commentary and tone\n"
                "- Business performance indicators\n"
                "- Forward-looking statements\n"
                "Provide detailed analysis but note this is partial."
            )),
            HumanMessage(content=f"Analyze this earnings call transcript part 1:\n\n{text_part1}")
        ]

        response_part1 = groq_llm.invoke(messages_part1)

        messages_part2 = [
            SystemMessage(content=(
                f"You are analyzing an earnings call transcript for {company_name}. "
                "This is PART 2 of 2. Focus on:\n"
                "- Q&A session insights\n"
                "- Management responses to analyst concerns\n"
                "- Guidance and outlook\n"
                "- Risk factors mentioned\n"
                "Provide comprehensive analysis for this final part."
            )),
            HumanMessage(content=f"Analyze this earnings call transcript part 2:\n\n{text_part2}")
        ]

        response_part2 = groq_llm.invoke(messages_part2)

        combine_response = groq_llm.invoke([
            SystemMessage(content=(
                f"Combine the insights from both parts of {company_name}'s earnings call transcript. "
                "Provide a comprehensive summary with:\n"
                "1. Executive Summary\n"
                "2. Key Financial Highlights\n"
                "3. Management Sentiment Analysis\n"
                "4. Strategic Initiatives\n"
                "5. Risk Assessment\n"
                "6. Overall Investment Thesis"
            )),
            HumanMessage(content=f"Combine these analyses:\n\nPart 1:\n{response_part1.content}\n\nPart 2:\n{response_part2.content}")
        ])
        
        return combine_response.content
        
    except Exception as e:
        return f"Error analyzing transcript: {str(e)}"

def generate_comprehensive_analysis(
    company_config: Dict,
    financial_data: Dict = None,
    news_data: Dict = None,
    transcript_data: Dict = None,
    analysis_type: str = "full"
) -> str:
    """
    Generate comprehensive financial analysis using all available data
    """
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )

        company_name = company_config["name"]
        
        content_sections = []
        
        if financial_data and financial_data.get("success"):
            content_sections.append(f"FINANCIAL DATA:\n{financial_data['content']}")
        
        if transcript_data and transcript_data.get("success"):
            content_sections.append(f"EARNINGS CALL ANALYSIS:\n{transcript_data['transcript_summary']}")
        
        if news_data and news_data.get("results"):
            news_content = "\n".join([
                f"- {result.get('title', '')}: {result.get('content', '')}"
                for result in news_data["results"][:5]
            ])
            content_sections.append(f"RECENT NEWS:\n{news_content}")
        
        content = "\n\n".join(content_sections)
        
        if not content.strip():
            return f"Insufficient data available for {company_name} analysis."

        if analysis_type == "financial":
            system_prompt = f"""You are an expert financial analyst specializing in Indian equity markets. 
            Analyze the financial data for {company_name} and provide:
            
            1. **Financial Health Assessment**
               - Key financial ratios and their interpretation
               - Liquidity, profitability, and solvency analysis
               - Risk assessment (Low/Medium/High) with reasoning
            
            2. **Performance Analysis**
               - Revenue and profit trends
               - Margin analysis
               - Comparison with industry benchmarks
            
            3. **Investment Perspective**
               - Strengths and weaknesses
               - Key risk factors
               - Growth prospects
            
            Be specific, data-driven, and provide actionable insights."""
            
        elif analysis_type == "news":
            system_prompt = f"""You are a financial news analyst specializing in Indian markets.
            Analyze the recent news about {company_name} and provide:
            
            1. **News Summary**
               - Key developments and events
               - Market impact assessment
            
            2. **Sentiment Analysis**
               - Overall news sentiment (Positive/Neutral/Negative)
               - Impact on stock performance
            
            3. **Strategic Implications**
               - Business impact
               - Competitive positioning
               - Future outlook
            
            Focus on market-moving news and investor-relevant information."""
            
        elif analysis_type == "transcript":
            system_prompt = f"""You are an earnings call specialist analyzing {company_name}'s management commentary.
            Provide:
            
            1. **Management Insights**
               - Key management statements
               - Strategic direction and guidance
            
            2. **Financial Performance Discussion**
               - Quarterly/annual performance highlights
               - Management's explanation of results
            
            3. **Forward-Looking Analysis**
               - Guidance and outlook
               - Strategic initiatives
               - Risk factors discussed
            
            Extract actionable insights from management commentary."""
            
        else:
            system_prompt = f"""You are a senior equity research analyst covering {company_name} in the Indian stock market.
            Provide a comprehensive investment analysis with:
            
            1. **Executive Summary**
               - Overall investment thesis
               - Key highlights and concerns
            
            2. **Financial Analysis**
               - Financial health and key ratios
               - Performance trends and benchmarking
            
            3. **Business Analysis**
               - Recent developments from news and earnings calls
               - Strategic positioning and competitive advantages
            
            4. **Risk Assessment**
               - Key risk factors and their likelihood
               - Risk mitigation strategies by management
            
            5. **Investment Recommendation**
               - Clear Buy/Hold/Sell recommendation with rationale
               - Target price reasoning (if applicable)
               - Time horizon for investment
            
            Be comprehensive, balanced, and provide actionable investment insights."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Analyze the following data for {company_name}:\n\n{content}")
        ]

        response = llm.invoke(messages)
        return response.content
        
    except Exception as e:
        return f"Error generating analysis for {company_config['name']}: {str(e)}"

def generate_comparative_analysis(companies_data: List[Dict]) -> str:
    """
    Generate comparative analysis across multiple companies
    """
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )

        company_names = [data["company_name"] for data in companies_data]
        
        system_prompt = f"""You are a senior equity research analyst comparing {', '.join(company_names)} 
        in the Indian stock market. Provide a comprehensive comparative analysis with:
        
        1. **Comparative Financial Health**
           - Key ratios comparison
           - Financial strength ranking
        
        2. **Business Performance Comparison**
           - Revenue and profit growth comparison
           - Market positioning analysis
        
        3. **Recent Developments**
           - News and events comparison
           - Management commentary insights
        
        4. **Risk-Return Analysis**
           - Risk assessment for each company
           - Expected return potential
        
        5. **Investment Recommendation**
           - Ranking from most to least attractive
           - Portfolio allocation suggestions
           - Sector-specific insights
        
        Provide actionable insights for portfolio construction."""

        content = ""
        for data in companies_data:
            content += f"\n\n{'='*50}\n"
            content += f"COMPANY: {data['company_name']}\n"
            content += f"{'='*50}\n"
            content += data.get('analysis', 'No analysis available')

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Compare these companies based on the following data:\n{content}")
        ]

        response = llm.invoke(messages)
        return response.content
        
    except Exception as e:
        return f"Error generating comparative analysis: {str(e)}"


def get_llm_response(raw_content: str, transcript_summary: str, news_data: str) -> str:
    """
    responsible for generating a comprehensive analysis using the provided data.
    """
    try:
        company_config = COMPANIES["pfc"]
        
        financial_data = {"success": True, "content": raw_content}
        transcript_data = {"success": True, "transcript_summary": transcript_summary}
        news_data_dict = {"results": [{"title": "News", "content": news_data}]}
        
        return generate_comprehensive_analysis(
            company_config=company_config,
            financial_data=financial_data,
            news_data=news_data_dict,
            transcript_data=transcript_data,
            analysis_type="full"
        )
        
    except Exception as e:
        return f"Error in legacy analysis: {str(e)}"