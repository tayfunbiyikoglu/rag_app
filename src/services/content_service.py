"""Service for handling content scraping and analysis."""
import logging
import requests
import tempfile
import os
import pypdf
from bs4 import BeautifulSoup
from datetime import datetime
import re
from typing import Dict
from ..config.settings import RISK_TERMS, DOMAIN_PRIORITIES, MAJOR_NEWS_DOMAINS

def scrape_content(url: str) -> str:
    """Scrape content from a URL, handling both web pages and PDFs."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        # Handle PDFs
        if url.lower().endswith('.pdf') or 'application/pdf' in response.headers.get('Content-Type', '').lower():
            return _handle_pdf_content(response.content)
        
        # Handle web pages
        return _handle_webpage_content(response.text)
            
    except Exception as e:
        return f"Error scraping content: {str(e)}"

def _handle_pdf_content(content: bytes) -> str:
    """Handle PDF content extraction."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_file.write(content)
        temp_file_path = temp_file.name

    try:
        pdf_text = []
        with open(temp_file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            for page in pdf_reader.pages:
                pdf_text.append(page.extract_text())
        
        os.unlink(temp_file_path)
        return "\n".join(pdf_text)
    except Exception as e:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise e

def _handle_webpage_content(html_content: str) -> str:
    """Handle webpage content extraction."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    return soup.get_text(separator=' ', strip=True)

def get_domain_priority(url: str) -> int:
    """Calculate domain priority score."""
    if '.gov' in url:
        return DOMAIN_PRIORITIES['.gov']
    elif '.org' in url:
        return DOMAIN_PRIORITIES['.org']
    elif any(domain in url for domain in MAJOR_NEWS_DOMAINS):
        return DOMAIN_PRIORITIES['major_news']
    elif '.com' in url or '.net' in url:
        return DOMAIN_PRIORITIES['.com']
    return DOMAIN_PRIORITIES['default']

def extract_date(url: str, content: str) -> str:
    """Extract publication date from URL or content."""
    try:
        # Common date patterns
        patterns = [
            r'/(20\d{2}/\d{2}/\d{2})/',
            r'/(20\d{2}-\d{2}-\d{2})/',
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+20\d{2}',
            r'\d{4}-\d{2}-\d{2}',
        ]
        
        # Check URL first
        for pattern in patterns[:2]:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Check content
        for pattern in patterns[2:]:
            match = re.search(pattern, content)
            if match:
                return match.group(0)
        
        return "Unknown"
    except:
        return "Unknown"

def quick_analyze(url: str, content: str) -> Dict:
    """Perform quick preliminary analysis of a source."""
    risk_score = _calculate_risk_score(content)
    domain_score = get_domain_priority(url)
    recency_score = _calculate_recency_score(url, content)
    
    # Adjust domain score for company's own domain
    if 'crediteurope' in url.lower():
        if risk_score < 20:  # If it's just policy content
            domain_score = 0
            risk_score = 0
    
    composite_score = (
        risk_score * 0.6 +
        domain_score * 0.25 +
        recency_score * 0.15
    )
    
    return {
        'url': url,
        'preliminary_score': risk_score,
        'domain_score': domain_score,
        'recency_score': recency_score,
        'composite_score': composite_score,
        'is_policy_doc': risk_score == 0 and 'crediteurope' in url.lower()
    }

def _calculate_risk_score(content: str) -> float:
    """Calculate risk score based on content analysis."""
    risk_score = 0
    content_lower = content.lower()
    
    # Define context patterns that indicate positive/policy content
    policy_patterns = [
        r'compliance\s+policy',
        r'risk\s+management',
        r'governance',
        r'our\s+commitment',
        r'we\s+ensure',
        r'our\s+approach',
        r'our\s+policy',
        r'our\s+framework',
        r'prevention\s+of',
        r'controls?\s+and\s+procedures'
    ]
    
    # Check if this is a policy/compliance document
    is_policy_doc = any(re.search(pattern, content_lower) for pattern in policy_patterns)
    
    # If it's a policy document, check for actual incidents vs policy statements
    if is_policy_doc:
        # Look for patterns that indicate actual incidents
        incident_patterns = [
            r'(was|were)\s+(fined|penalized|sanctioned)',
            r'(found|discovered)\s+(violation|breach|misconduct)',
            r'investigation\s+revealed',
            r'regulatory\s+action\s+taken',
            r'enforcement\s+action',
            r'failed\s+to\s+comply'
        ]
        
        has_incidents = any(re.search(pattern, content_lower) for pattern in incident_patterns)
        
        if not has_incidents:
            return 0  # It's a clean policy document
    
    # If not a policy document or if it contains actual incidents, proceed with risk scoring
    for term, weight in RISK_TERMS.items():
        # Don't just count occurrences, look for negative context
        negative_contexts = [
            f"{term}.+(found|discovered|revealed|confirmed|proven)",
            f"{term}.+(investigation|prosecution|penalty|fine)",
            f"(involved|engaged)\s+in\s+{term}",
            f"(evidence|proof)\s+of\s+{term}"
        ]
        
        for context in negative_contexts:
            if re.search(context, content_lower):
                risk_score += weight * 2  # Double weight for confirmed negative context
                break
        else:
            # Only add base weight if term exists but without negative context
            if term in content_lower:
                risk_score += weight * 0.5
    
    return min(100, risk_score)

def _calculate_recency_score(url: str, content: str) -> float:
    """Calculate recency score based on publication date."""
    date_str = extract_date(url, content)
    if date_str != "Unknown":
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            days_old = (datetime.now() - date).days
            return max(0, 100 - (days_old / 365) * 15)
        except:
            return 50
    return 50
