"""Service for handling search operations."""
import logging
from typing import List, Dict
from serpapi import GoogleSearch
from ..config.settings import SERPAPI_KEY, MAX_INITIAL_RESULTS, MIN_COMPOSITE_SCORE

def create_search_query(fi_name: str) -> str:
    """Create a search query for adverse news."""
    adverse_terms = [
        "launder", "fraud", "terroris", "crime", "convict",
        "smuggle", "embezzle", "investigate", "bribe", "corrupt",
        "enforcement", "violate", "sanction", "cartel", "breach",
        "suspected", "illegal", "scandal", "allegation", "prosecute",
        '"court case"', "fined", "guilt", "traffick", "miscond",
        '"tax evasion"', "ICIJ"
    ]

    terms_query = " OR ".join(adverse_terms)
    query = f'"{fi_name}" + {terms_query} (site:.gov OR site:.org OR site:.com OR site:.net) -("job hiring" OR "career opportunity" OR "we are hiring" OR "press release")'

    logging.info(f"Search query: {query}")
    return query

def search_internet(query: str, num_results: int = 10) -> List[str]:
    """Search the internet and return a list of URLs with two-phase analysis."""
    try:
        logging.info(f"Starting search with query: {query}")

        if not SERPAPI_KEY:
            logging.error("SERPAPI_KEY not found in environment variables")
            return []

        search = GoogleSearch({
            "q": query,
            "num": min(MAX_INITIAL_RESULTS, num_results * 2),
            "api_key": SERPAPI_KEY
        })

        results = search.get_dict()
        urls = []

        if "organic_results" in results:
            urls = [result['link'] for result in results['organic_results']]
            logging.info(f"Found {len(urls)} initial results")

        if not urls:
            logging.warning("No results found in search")
            return []

        return urls

    except Exception as e:
        logging.error(f"Search error: {str(e)}")
        return []
