"""Configuration settings for the application."""
import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Streamlit page
def setup_streamlit():
    st.set_page_config(
        page_title="Adverse News Search",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="auto"
    )

# API Keys and configuration
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
if not SERPAPI_KEY:
    raise ValueError("SERPAPI_KEY not found in environment variables. Please set it in your .env file.")

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
if not AZURE_OPENAI_API_KEY:
    raise ValueError("AZURE_OPENAI_API_KEY not found in environment variables. Please set it in your .env file.")

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
if not AZURE_OPENAI_ENDPOINT:
    raise ValueError("AZURE_OPENAI_ENDPOINT not found in environment variables. Please set it in your .env file.")

AZURE_OPENAI_CHAT_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
if not AZURE_OPENAI_CHAT_DEPLOYMENT_NAME:
    raise ValueError("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME not found in environment variables. Please set it in your .env file.")

# Search configuration
MAX_INITIAL_RESULTS = int(os.getenv("MAX_INITIAL_RESULTS", "30"))
MIN_COMPOSITE_SCORE = int(os.getenv("MIN_COMPOSITE_SCORE", "30"))

# Domain priority scores
DOMAIN_PRIORITIES = {
    '.gov': 100,
    '.org': 80,
    'major_news': 90,  # For major news outlets
    '.com': 60,
    '.net': 60,
    'default': 40
}

# Major news domains
MAJOR_NEWS_DOMAINS = [
    'reuters.com', 'bloomberg.com', 'ft.com', 'wsj.com',
    'nytimes.com', 'forbes.com', 'cnbc.com', 'financial-news.co.uk'
]

# Risk terms and their weights
RISK_TERMS = {
    'fine': 10,
    'penalty': 10,
    'million': 8,
    'billion': 9,
    'investigation': 8,
    'fraud': 12,
    'laundering': 12,
    'criminal': 10,
    'illegal': 9,
    'violation': 8,
    'sanction': 10,
    'lawsuit': 9,
    'court': 8,
    'regulatory': 7,
    'enforcement': 9,
    'breach': 8,
    'misconduct': 9,
    'allegation': 7,
    'charged': 10,
    'guilty': 11,
    'convicted': 11,
    'settlement': 9,
    'probe': 7,
    'scandal': 9
}
