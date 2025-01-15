"""Service for handling content analysis using Azure OpenAI."""
import logging
from typing import Dict, List
from datetime import datetime
from langchain_community.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from ..config.settings import (
    AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, 
    AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
    MIN_RELIABILITY_SCORE, MIN_RELEVANCY_SCORE
)

def analyze_content(content: str, url: str, additional_sources: List[str] = None) -> Dict:
    """Analyze content using Azure OpenAI with enhanced verification."""
    system_prompt = """You are a financial risk analyst specialized in evaluating news articles for potential risks and adverse events.
    Analyze the content carefully and provide a structured assessment including:
    1. Verification of news authenticity and reliability
    2. Cross-reference with additional sources when available
    3. Extraction of key dates, entities, and events
    4. Assessment of current status (ongoing/resolved)
    5. Identification of any legal proceedings or regulatory actions
    
    You must ALWAYS respond with a valid Python dictionary containing these keys:
    - summary (str): A concise summary of the content
    - date (str): The date of the news article (YYYY-MM-DD format)
    - adversity_score (int): Score from 1-10
    - reliability_score (int): Score from 1-100
    - relevancy_score (int): Score from 1-100
    - key_findings (list): Key findings as bullet points
    - legal_status (str): Current status of any legal proceedings
    - next_steps (list): Recommended follow-up actions
    - sources_analysis (dict): Assessment of each source's credibility
    
    Scoring Guidelines:
    - adversity_score (1-10):
        1-2: Minor issues or policy documents
        3-4: Potential risks or concerns
        5-6: Moderate violations or investigations
        7-8: Serious confirmed incidents
        9-10: Critical violations with major impact
    
    - reliability_score (1-100):
        Consider source credibility, cross-verification, and documentation
    
    - relevancy_score (1-100):
        Based on direct involvement and impact on the entity
    
    DO NOT include any other text or formatting in your response.
    ONLY return the Python dictionary."""

    user_prompt = f"""Analyze the following content from {url}.
    Additional sources: {', '.join(additional_sources) if additional_sources else 'None'}
    
    Content: {content[:10000]}"""

    try:
        chat = AzureChatOpenAI(
            openai_api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            deployment_name=AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
            openai_api_version="2023-05-15",
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = chat(messages)
        analysis = eval(response.content)

        # Filter out low-quality results
        if (analysis.get('reliability_score', 0) < MIN_RELIABILITY_SCORE or 
            analysis.get('relevancy_score', 0) < MIN_RELEVANCY_SCORE):
            logging.info(f"Article filtered out due to low scores: Reliability={analysis.get('reliability_score')}, Relevancy={analysis.get('relevancy_score')}")
            return None

        # Add metadata
        analysis['analysis_timestamp'] = datetime.now().isoformat()
        analysis['primary_source'] = url
        analysis['additional_sources'] = additional_sources or []

        return analysis

    except Exception as e:
        logging.error(f"Error in analyze_content: {str(e)}")
        return None
