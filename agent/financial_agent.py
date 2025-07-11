from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda, RunnableConfig
from typing import Dict, TypedDict, Optional, List, Any
from enum import Enum
from agent.tools import (
    COMPANIES,
    tavily_search_financial_news,
    tavily_extract_financial_data,
    tavily_crawl_company_websites,
    tavily_map_financial_resources,
    get_transcript_data,
    generate_comprehensive_analysis,
    generate_comparative_analysis
)

class AnalysisType(str, Enum):
    FINANCIAL = "financial"
    NEWS = "news"
    TRANSCRIPT = "transcript"
    WEBSITE = "website"
    RESOURCES = "resources"
    FULL = "full"
    COMPARATIVE = "comparative"

class AnalysisState(TypedDict):
    user_query: str
    companies: List[str]
    analysis_type: Optional[AnalysisType]
    company_configs: Optional[List[Dict]]
    financial_data: Optional[Dict]
    news_data: Optional[Dict]
    transcript_data: Optional[Dict]
    website_data: Optional[Dict]
    resources_data: Optional[Dict]
    final_output: Optional[str]
    error_message: Optional[str]

workflow = StateGraph(AnalysisState)

def extract_companies_and_analysis_type(state: AnalysisState) -> Dict[str, Any]:
    """
    Extract companies and analysis type from user query
    """
    query = state["user_query"].lower()
    
    detected_companies = []
    company_configs = []
    
    for key, config in COMPANIES.items():
        if (config["symbol"].lower() in query or 
            config["name"].lower() in query or
            any(term.lower() in query for term in config["search_terms"])):
            detected_companies.append(config["name"])
            company_configs.append(config)
    
    if not detected_companies:
        if any(term in query for term in ["all", "compare", "comparison", "vs", "versus"]):
            detected_companies = [config["name"] for config in COMPANIES.values()]
            company_configs = list(COMPANIES.values())
    

    analysis_type = AnalysisType.FULL
    
    if "news" in query and not any(term in query for term in ["financial", "transcript", "website"]):
        analysis_type = AnalysisType.NEWS
    elif "transcript" in query or "earnings" in query or "concall" in query:
        analysis_type = AnalysisType.TRANSCRIPT
    elif "financial" in query or "ratios" in query or "balance sheet" in query:
        analysis_type = AnalysisType.FINANCIAL
    elif "website" in query or "crawl" in query:
        analysis_type = AnalysisType.WEBSITE
    elif "resources" in query or "map" in query or "documents" in query:
        analysis_type = AnalysisType.RESOURCES
    elif any(term in query for term in ["compare", "comparison", "vs", "versus"]) and len(company_configs) > 1:
        analysis_type = AnalysisType.COMPARATIVE
    elif "full" in query or "complete" in query or "comprehensive" in query:
        analysis_type = AnalysisType.FULL
    
    return {
        "companies": detected_companies,
        "company_configs": company_configs,
        "analysis_type": analysis_type
    }

def validate_request(state: AnalysisState) -> Dict[str, str]:
    """
    Validate if the request can be processed
    """
    if not state.get("company_configs") or len(state["company_configs"]) == 0:
        available_companies = ", ".join([config["name"] for config in COMPANIES.values()])
        return {
            "error_message": f"No supported companies detected in your query. "
                          f"Supported companies: {available_companies}. "
                          f"Please mention one or more of these companies in your query."
        }
    
    return {}

def fetch_financial_data(state: AnalysisState) -> Dict[str, Any]:
    """
    Fetch financial data for companies using Tavily Extract
    """
    if state["analysis_type"] not in [AnalysisType.FINANCIAL, AnalysisType.FULL, AnalysisType.COMPARATIVE]:
        return {}
    
    financial_results = {}
    
    for config in state["company_configs"]:
        try:
            result = tavily_extract_financial_data(config)
            financial_results[config["name"]] = result
        except Exception as e:
            financial_results[config["name"]] = {"error": str(e), "success": False}
    
    return {"financial_data": financial_results}

def fetch_news_data(state: AnalysisState) -> Dict[str, Any]:
    """
    Fetch news data for companies using Tavily Search
    """
    if state["analysis_type"] not in [AnalysisType.NEWS, AnalysisType.FULL, AnalysisType.COMPARATIVE]:
        return {}
    
    news_results = {}
    
    for config in state["company_configs"]:
        try:
            result = tavily_search_financial_news(config, days=30, max_results=10)
            news_results[config["name"]] = result
        except Exception as e:
            news_results[config["name"]] = {"error": str(e)}
    
    return {"news_data": news_results}

def fetch_transcript_data(state: AnalysisState) -> Dict[str, Any]:
    """
    Fetch transcript data for companies
    """
    if state["analysis_type"] not in [AnalysisType.TRANSCRIPT, AnalysisType.FULL, AnalysisType.COMPARATIVE]:
        return {}
    
    transcript_results = {}
    
    for config in state["company_configs"]:
        try:
            result = get_transcript_data(config)
            transcript_results[config["name"]] = result
        except Exception as e:
            transcript_results[config["name"]] = {"error": str(e), "success": False}
    
    return {"transcript_data": transcript_results}

def fetch_website_data(state: AnalysisState) -> Dict[str, Any]:
    """
    Crawl company websites using Tavily Crawl
    """
    if state["analysis_type"] != AnalysisType.WEBSITE:
        return {}
    
    website_results = {}
    
    for config in state["company_configs"]:
        try:
            result = tavily_crawl_company_websites(config, max_depth=2)
            website_results[config["name"]] = result
        except Exception as e:
            website_results[config["name"]] = {"error": str(e)}
    
    return {"website_data": website_results}

def fetch_resources_data(state: AnalysisState) -> Dict[str, Any]:
    """
    Map financial resources using Tavily Map
    """
    if state["analysis_type"] != AnalysisType.RESOURCES:
        return {}
    
    resources_results = {}
    
    for config in state["company_configs"]:
        try:
            result = tavily_map_financial_resources(config)
            resources_results[config["name"]] = result
        except Exception as e:
            resources_results[config["name"]] = {"error": str(e)}
    
    return {"resources_data": resources_results}

def generate_final_analysis(state: AnalysisState) -> Dict[str, str]:
    """
    Generate the final analysis based on collected data
    """
    try:
        if state.get("error_message"):
            return {"final_output": state["error_message"]}
        
        analysis_type = state["analysis_type"]
        company_configs = state["company_configs"]
        
        if analysis_type == AnalysisType.COMPARATIVE and len(company_configs) > 1:
            companies_data = []
            
            for config in company_configs:
                company_name = config["name"]
                
                financial_data = state.get("financial_data", {}).get(company_name)
                news_data = state.get("news_data", {}).get(company_name)
                transcript_data = state.get("transcript_data", {}).get(company_name)
                
                individual_analysis = generate_comprehensive_analysis(
                    company_config=config,
                    financial_data=financial_data,
                    news_data=news_data,
                    transcript_data=transcript_data,
                    analysis_type="full"
                )
                
                companies_data.append({
                    "company_name": company_name,
                    "analysis": individual_analysis
                })
            
            final_analysis = generate_comparative_analysis(companies_data)
            
        else:
            all_results = []
            
            for config in company_configs:
                company_name = config["name"]
                
                financial_data = state.get("financial_data", {}).get(company_name)
                news_data = state.get("news_data", {}).get(company_name)
                transcript_data = state.get("transcript_data", {}).get(company_name)
                website_data = state.get("website_data", {}).get(company_name)
                resources_data = state.get("resources_data", {}).get(company_name)
                
                if analysis_type == AnalysisType.WEBSITE:
                  if website_data:
                    result = generate_comprehensive_analysis(
                      company_config=config,
                      website_data=website_data,
                      analysis_type=analysis_type
                    )
                  else:
                    result = generate_comprehensive_analysis(
                      company_config=config,
                      analysis_type=analysis_type
                    )
                    
                elif analysis_type == AnalysisType.RESOURCES:
                  if resources_data:
                    result = generate_comprehensive_analysis(
                      company_config=config,
                      resources_data=resources_data,
                      analysis_type=analysis_type
                    )
                  else:
                    result = generate_comprehensive_analysis(
                      company_config=config,
                      analysis_type=analysis_type
                    )
                        
                else:
                    result = generate_comprehensive_analysis(
                        company_config=config,
                        financial_data=financial_data,
                        news_data=news_data,
                        transcript_data=transcript_data,
                        analysis_type=analysis_type
                    )
                
                all_results.append(result)
            
            final_analysis = "\n\n".join(all_results)
        
        return {"final_output": final_analysis}
        
    except Exception as e:
        return {"final_output": f"Error generating analysis: {str(e)}"}


workflow.add_node("extract_intent", RunnableLambda(extract_companies_and_analysis_type))
workflow.add_node("validate", RunnableLambda(validate_request))
workflow.add_node("fetch_financial", RunnableLambda(fetch_financial_data))
workflow.add_node("fetch_news", RunnableLambda(fetch_news_data))
workflow.add_node("fetch_transcript", RunnableLambda(fetch_transcript_data))
workflow.add_node("fetch_website", RunnableLambda(fetch_website_data))
workflow.add_node("fetch_resources", RunnableLambda(fetch_resources_data))
workflow.add_node("generate_analysis", RunnableLambda(generate_final_analysis))

workflow.set_entry_point("extract_intent")

def route_after_validation(state: AnalysisState) -> str:
    """Route to data fetching based on analysis type"""
    if state.get("error_message"):
        return "generate_analysis"
    
    analysis_type = state.get("analysis_type")
    
    if analysis_type in [AnalysisType.FINANCIAL]:
        return "fetch_financial"
    elif analysis_type == AnalysisType.NEWS:
        return "fetch_news"
    elif analysis_type == AnalysisType.TRANSCRIPT:
        return "fetch_transcript"
    elif analysis_type == AnalysisType.WEBSITE:
        return "fetch_website"
    elif analysis_type == AnalysisType.RESOURCES:
        return "fetch_resources"
    else:
        return "fetch_financial"


workflow.add_edge("extract_intent", "validate")

workflow.add_conditional_edges(
    "validate",
    route_after_validation,
    {
        "fetch_financial": "fetch_financial",
        "fetch_news": "fetch_news",
        "fetch_transcript": "fetch_transcript",
        "fetch_website": "fetch_website",
        "fetch_resources": "fetch_resources",
        "generate_analysis": "generate_analysis"
    }
)

workflow.add_edge("fetch_financial", "fetch_news")
workflow.add_edge("fetch_news", "fetch_transcript")
workflow.add_edge("fetch_transcript", "generate_analysis")


workflow.add_edge("generate_analysis", END)

financial_analyst = workflow.compile()

def analyze_query(query: str) -> str:
    """
    Main function to analyze user queries
    """
    try:
        result = financial_analyst.invoke(
            {"user_query": query},
            RunnableConfig(recursion_limit=50)
        )
        
        return result.get("final_output", "No analysis results available")
        
    except Exception as e:
        return f"Error processing your query: {str(e)}"


# if __name__ == "__main__":
#     while True:
#         try:
#             user_query = input("\nEnter your query (or 'quit' to exit): ").strip()
            
#             if user_query.lower() in ['quit', 'exit', 'q']:
#                 print("Thank you for using the Financial Analysis Agent!")
#                 break
            
#             if not user_query:
#                 print("Please enter a valid query.")
#                 continue
            
#             print(f"\nAnalyzing: {user_query}")
#             print("Processing...")
            
#             result = analyze_query(user_query)
#             print(f"\nAnalysis Result:")
#             print("-" * 50)
#             print(result)
#             print("=" * 70)
            
#         except KeyboardInterrupt:
#             print("\nAnalysis interrupted by user.")
#             break
#         except Exception as e:
#             print(f"Error: {str(e)}")
