"""Service for handling search operations."""
import logging
from typing import List, Dict, Any
from serpapi import GoogleSearch
from datetime import datetime, timedelta
import json
from openai import AzureOpenAI
import asyncio
from ..config.settings import (
    SERPAPI_KEY, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_CHAT_DEPLOYMENT_NAME, OPENAI_API_VERSION
)
from urllib.parse import urlparse
import streamlit as st

def create_search_query(fi_name: str, months: int = None) -> str:
    """Create a search query for adverse news."""
    logging.warning(f"create_search_query called with fi_name: '{fi_name}', months: {months}")
    logging.warning(f"Called from: {__file__}")
    
    if not fi_name:
        logging.warning("Empty fi_name provided to create_search_query")
        return ""
        
    # List of terms indicating potential adverse news
    adverse_terms = [
        "launder", "fraud", "terroris", "crime", "convict",
        "sanction", "penalty", "fine", "lawsuit", "litigation",
        "scandal", "violation", "misconduct", "investigation",
        "regulatory", "enforcement", "illegal", "corrupt",
        "breach", "compliance"
    ]
    
    # Create the query with adverse terms and exact match for institution name
    adverse_query = " OR ".join(f'"{term}"' for term in adverse_terms)
    
    # Add date filter if months is specified
    date_filter = f" when:{months}m" if months and months > 0 else ""
    
    # Combine everything with exact match for institution name
    query = f'"{fi_name}" AND ({adverse_query}){date_filter}'
    logging.warning(f"Generated search query: {query}")
    
    return query

async def analyze_news_article(client: AzureOpenAI, article: Dict) -> Dict[str, Any]:
    """Analyze a news article using AI to determine if it's adverse news and assign a score."""
    prompt = f"""Analyze this news article and determine if it contains adverse news about the subject:
Title: {article['title']}
Snippet: {article['snippet']}

Please analyze and provide:
1. Is this adverse news? (true/false)
2. Score (0-100, where 100 is most severe adverse news)
3. Brief summary of the news (max 2 sentences)
4. Reason for the score (max 2 sentences)

Respond in JSON format with the following structure:
{{
    "is_adverse": boolean,
    "score": number,
    "summary": string,
    "reason": string
}}"""

    try:
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model=AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing news articles for adverse information. Focus on regulatory, legal, financial, and reputational risks."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
        )

        # Parse the JSON response
        analysis = json.loads(response.choices[0].message.content)
        return {
            **article,
            "analysis": analysis
        }
    except Exception as e:
        logging.error(f"Error analyzing article: {str(e)}")
        return {
            **article,
            "analysis": {
                "is_adverse": False,
                "score": 0,
                "summary": "Error in analysis",
                "reason": str(e)
            }
        }

async def analyze_content(content: str) -> Dict[str, Any]:
    """Analyze content using AI to determine if it's adverse news and assign a score."""
    prompt = f"""Analyze this content and determine if it contains adverse news about the subject:
Content: {content}

Please analyze and provide:
1. Is this adverse news? (true/false)
2. Score (0-100, where 100 is most severe adverse news)
3. Brief summary of the news (max 2 sentences)
4. Reason for the score (max 2 sentences)

Respond in JSON format with the following structure:
{{
    "is_adverse": boolean,
    "score": number,
    "summary": string,
    "reason": string
}}"""

    try:
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model=AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing news articles for adverse information. Focus on regulatory, legal, financial, and reputational risks."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
        )

        # Parse the JSON response
        analysis = json.loads(response.choices[0].message.content)
        return analysis
    except Exception as e:
        logging.error(f"Error analyzing content: {str(e)}")
        return {
            "is_adverse": False,
            "score": 0,
            "summary": "Error in analysis",
            "reason": str(e)
        }

async def analyze_results_summary(analyzed_results: List[Dict]) -> Dict:
    """Create an overall summary of the analyzed results."""
    if not analyzed_results:
        return {
            "has_adverse_news": False,
            "summary": "No adverse news found.",
            "highest_risk_score": 0,
            "total_articles": 0
        }
    
    # Calculate metrics
    total_articles = len(analyzed_results)
    risk_scores = [r['analysis']['score'] for r in analyzed_results]
    highest_risk_score = max(risk_scores) if risk_scores else 0
    avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
    
    # Prepare content for summary analysis
    content_for_summary = "\n\n".join([
        f"Article {i+1}:\nTitle: {r.get('title', 'No title')}\n"
        f"Summary: {r['analysis'].get('summary', 'No summary')}\n"
        f"Risk Score: {r['analysis'].get('score', 0)}"
        for i, r in enumerate(analyzed_results[:5])  # Limit to top 5 for summary
    ])
    
    # Get AI to create overall summary
    prompt = f"""Analyze these adverse news results and provide an overall assessment:

{content_for_summary}

Additional metrics:
- Total articles found: {total_articles}
- Average risk score: {avg_risk_score:.1f}
- Highest risk score: {highest_risk_score}

Please provide a brief summary (2-3 sentences) that captures:
1. The overall severity of adverse news
2. The main types of issues found
3. A general recommendation

Respond in JSON format:
{{
    "summary": "your 2-3 sentence summary here"
}}"""

    try:
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model=AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing adverse news and providing clear, actionable summaries."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
        )
        
        summary = json.loads(response.choices[0].message.content)
        
        return {
            "has_adverse_news": True,
            "summary": summary['summary'],
            "highest_risk_score": highest_risk_score,
            "total_articles": total_articles
        }
        
    except Exception as e:
        logging.error(f"Error creating summary: {str(e)}")
        return {
            "has_adverse_news": True,
            "summary": "Error generating summary.",
            "highest_risk_score": highest_risk_score,
            "total_articles": total_articles
        }

async def search_internet(query: str, num_results: int = 10, min_score: float = 50.0, months: int = 6) -> List[Dict]:
    """Search the internet and return a list of URLs with analysis.
    
    Args:
        query: Search query string
        num_results: Number of results to fetch
        min_score: Minimum score threshold for including results (0-100)
        months: Number of months to look back in search
    """
    logging.warning(f"search_internet called with query: '{query}'")
    logging.warning(f"Requesting {num_results} results from search, looking back {months} months")
    
    if not query:
        logging.warning("Empty query provided to search_internet")
        return []
        
    try:
        # Initialize the SerpAPI client
        params = {
            "api_key": SERPAPI_KEY,
            "engine": "google",
            "q": query,
            "num": num_results,  # Request the specified number of results
            "gl": "us",    # Search in US
            "hl": "en",    # English results
            "tbs": f"qdr:m{months}"  # Dynamic time range based on user input
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "error" in results:
            logging.error(f"SerpAPI error: {results['error']}")
            return []
            
        # Get results from organic_results
        search_results = results.get("organic_results", [])
        logging.warning(f"Received {len(search_results)} results from search")
        
        if not search_results:
            logging.warning("No results found")
            return []
            
        analyzed_results = []
        analyzed_count = 0
        skipped_count = 0
        
        # Calculate cutoff date based on user-specified months
        cutoff_date = datetime.now() - timedelta(days=30 * months)
        
        for result in search_results:
            try:
                # Extract and validate the date if available
                result_date_str = result.get('date')
                if result_date_str:
                    try:
                        result_date = datetime.strptime(result_date_str, '%Y-%m-%d')
                        if result_date < cutoff_date:
                            logging.info(f"Skipped: Result too old ({result_date_str})")
                            skipped_count += 1
                            continue
                    except ValueError:
                        logging.warning(f"Could not parse date: {result_date_str}")
                
                # Extract source domain from the link
                domain = urlparse(result['link']).netloc
                
                # Prepare source with domain type
                if domain.endswith('.gov'):
                    source_type = '.gov'
                elif domain.endswith('.org'):
                    source_type = '.org'
                else:
                    source_type = '.com'
                    
                result['source'] = f"{result.get('source', domain)} ({source_type})"
                
                # Combine title and snippet for analysis
                content_to_analyze = f"{result.get('title', '')} {result.get('snippet', '')}"
                
                # Only add if we have some content to analyze
                if content_to_analyze.strip():
                    analyzed_count += 1
                    # Analyze the content
                    analysis = await analyze_content(content_to_analyze)
                    
                    if analysis and analysis.get('is_adverse', False):
                        # Check if the score meets the minimum threshold
                        if analysis['score'] >= min_score:
                            result['analysis'] = analysis
                            analyzed_results.append(result)
                            logging.warning(f"Found adverse news (score: {analysis['score']}) from {domain}")
                        else:
                            skipped_count += 1
                            logging.info(f"Skipped: Score too low ({analysis['score']} < {min_score})")
                    else:
                        skipped_count += 1
                        logging.info("Not considered adverse news")
                else:
                    skipped_count += 1
                    logging.info("Skipped: No content to analyze")
                
            except Exception as e:
                skipped_count += 1
                logging.error(f"Error processing result {result}: {str(e)}")
                continue
                
        logging.warning(f"Processed {analyzed_count} results, skipped {skipped_count}")
        logging.warning(f"Found {len(analyzed_results)} relevant adverse news items")
        
        # Sort results by score in descending order
        analyzed_results.sort(key=lambda x: x['analysis']['score'], reverse=True)
        
        return analyzed_results
        
    except Exception as e:
        logging.error(f"Error in search_internet: {str(e)}")
        return []

# Export only the necessary functions
__all__ = ['create_search_query', 'search_internet', 'analyze_content', 'analyze_results_summary']
