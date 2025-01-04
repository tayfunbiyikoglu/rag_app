"""Service for handling content analysis using Azure OpenAI."""
import logging
from typing import Dict
import os
from langchain_community.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from ..config.settings import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_CHAT_DEPLOYMENT_NAME

def analyze_content(content: str, url: str) -> Dict:
    """Analyze content using Azure OpenAI."""
    system_prompt = """You are a financial risk analyst specialized in evaluating news articles for potential risks and adverse events.
    You must analyze the content carefully to distinguish between:
    1. Policy/compliance documents that describe preventive measures
    2. Actual incidents, violations, or regulatory actions
    
    Only consider content as high risk if there are ACTUAL incidents, violations, or regulatory actions.
    DO NOT assign high risk scores to policy documents or preventive measures unless they mention actual incidents.
    
    You must ALWAYS respond with a valid Python dictionary containing exactly these keys:
    - summary (str): A concise summary of the content
    - reliability_score (int): Score from 0-100
    - relevancy_score (int): Score from 0-100
    - key_findings (list): A list of strings containing key findings, e.g., ["finding1", "finding2", ...]
    
    Example response format:
    {
        "summary": "Brief summary here",
        "reliability_score": 75,
        "relevancy_score": 60,
        "key_findings": ["First key finding", "Second key finding"]
    }
    
    Scoring Guidelines:
    - Reliability Score (0-100): Based on source credibility and content quality
    - Relevancy Score (0-100): How relevant the content is to ACTUAL financial misconduct (not just policy)
      * Score 0-20: Policy/compliance documents with no incidents
      * Score 30-50: Mentions of potential risks or minor issues
      * Score 60-80: Confirmed incidents or regulatory actions
      * Score 80-100: Major confirmed violations with significant impact
    
    DO NOT include any other text, markdown formatting, or code blocks in your response.
    ONLY return the Python dictionary."""

    user_prompt = f"""Analyze the following content from {url} and determine if it describes actual incidents or just policy/compliance measures.
    Consider the source and context carefully.
    
    Content: {content[:10000]}"""

    try:
        chat = AzureChatOpenAI(
            openai_api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            deployment_name=AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
            openai_api_version="2023-05-15",
            temperature=0.7,
            max_tokens=1000
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = chat(messages)
        response_text = response.content.strip()
        
        # Clean up the response
        if response_text.startswith('```python'):
            response_text = response_text[8:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # Log the raw response for debugging
        logging.debug(f"Raw OpenAI response: {response_text}")

        # Safely evaluate the response
        import ast
        try:
            analysis = ast.literal_eval(response_text)
            
            # Validate the response format
            required_keys = {'summary', 'reliability_score', 'relevancy_score', 'key_findings'}
            if not all(key in analysis for key in required_keys):
                raise ValueError("Missing required keys in response")
            
            if not isinstance(analysis['reliability_score'], int) or not isinstance(analysis['relevancy_score'], int):
                raise ValueError("Scores must be integers")
            
            if not (0 <= analysis['reliability_score'] <= 100) or not (0 <= analysis['relevancy_score'] <= 100):
                raise ValueError("Scores must be between 0 and 100")
            
            if not isinstance(analysis['key_findings'], list):
                raise ValueError("key_findings must be a list")
            
            # Check if the content appears to be a policy document
            policy_indicators = {
                'policy': 'internal policy document',
                'procedure': 'procedural document',
                'terms and conditions': 'terms and conditions document',
                'privacy notice': 'privacy notice',
                'compliance statement': 'compliance document',
                'code of conduct': 'code of conduct document',
                'annual report': 'annual report',
                'corporate governance': 'corporate governance document',
                'regulatory disclosure': 'regulatory disclosure document'
            }
            
            if analysis['relevancy_score'] < 30:
                found_indicators = [desc for term, desc in policy_indicators.items() if term in content.lower()]
                if found_indicators:
                    analysis['relevancy_score'] = 0
                    indicator_text = found_indicators[0] if len(found_indicators) == 1 else 'corporate document'
                    analysis['summary'] = f"Content appears to be a {indicator_text} without adverse findings. " + analysis['summary']
                else:
                    analysis['summary'] = "Low relevancy score: Content does not contain significant adverse news findings. " + analysis['summary']
            
            return analysis

        except Exception as e:
            logging.error(f"Failed to parse OpenAI response: {str(e)}")
            logging.error(f"Response text: {response_text}")
            return {
                "summary": "Error parsing analysis response.",
                "reliability_score": 0,
                "relevancy_score": 0,
                "key_findings": []
            }

    except Exception as e:
        logging.error(f"Azure OpenAI Error: {str(e)}")
        return {
            "summary": f"Error during analysis: {str(e)}",
            "reliability_score": 0,
            "relevancy_score": 0,
            "key_findings": []
        }
