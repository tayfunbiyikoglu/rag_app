import os
from dotenv import load_dotenv
import logging
from src.utils.confluence_loader import ConfluenceKnowledgeBase

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Log environment variables (without showing sensitive values)
logger.info("Environment variables loaded:")
for var in ["CONFLUENCE_URL", "CONFLUENCE_USERNAME", "CONFLUENCE_API_TOKEN", "CONFLUENCE_SPACE_KEY"]:
    logger.info(f"{var}: {'[SET]' if os.getenv(var) else '[MISSING]'}")

# Create instance and load data
logger.info("Creating ConfluenceKnowledgeBase instance...")
confluence_kb = ConfluenceKnowledgeBase()
logger.info("Loading space content...")
documents = confluence_kb.load_space_content()
logger.info("Processing and storing documents...")
confluence_kb.process_and_store_documents(documents)
