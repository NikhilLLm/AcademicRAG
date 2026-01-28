"""
Centralized Qdrant client configuration.
This module provides a singleton Qdrant client instance to avoid redundant connections.
"""
import os
import logging
from typing import Optional
from qdrant_client import QdrantClient
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Qdrant configuration from environment variables
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Collection names
PAPERS_COLLECTION = os.getenv("PAPERS_COLLECTION", "papers_semantic_v1")
PDF_VECTORS_COLLECTION = os.getenv("PDF_VECTORS_COLLECTION", "pdf_vectors_v2")

# Singleton client instance
_qdrant_client: Optional[QdrantClient] = None


def get_qdrant_client(
    url: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: int = 10,
    prefer_grpc: bool = False
) -> QdrantClient:
    """
    Get or create a Qdrant client instance (singleton pattern).
    
    Args:
        url: Qdrant server URL (defaults to env var QDRANT_URL)
        api_key: Qdrant API key (defaults to env var QDRANT_API_KEY)
        timeout: Request timeout in seconds
        prefer_grpc: Whether to prefer gRPC over HTTP
        
    Returns:
        QdrantClient instance
        
    Raises:
        ValueError: If URL or API key are not provided and not in environment
    """
    global _qdrant_client
    
    # Use provided values or fall back to environment variables
    qdrant_url = url or QDRANT_URL
    qdrant_api_key = api_key or QDRANT_API_KEY
    
    # Validate credentials
    if not qdrant_url:
        raise ValueError(
            "QDRANT_URL not found. Please set it in .env file or pass as argument."
        )
    if not qdrant_api_key:
        raise ValueError(
            "QDRANT_API_KEY not found. Please set it in .env file or pass as argument."
        )
    
    # Create client if it doesn't exist
    if _qdrant_client is None:
        try:
            _qdrant_client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
                timeout=timeout,
                prefer_grpc=prefer_grpc
            )
            logger.info(f"✅ Connected to Qdrant at {qdrant_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            raise
    
    return _qdrant_client


def reset_qdrant_client():
    """
    Reset the singleton client instance.
    Useful for testing or reconnecting with different credentials.
    """
    global _qdrant_client
    _qdrant_client = None
    logger.info("Qdrant client instance reset")


# Convenience function to get collection names
def get_collection_name(collection_type: str = "papers_semantic_v1") -> str:
    """
    Get the collection name for a specific type.
    
    Args:
        collection_type: Type of collection ("papers" or "pdf_vectors")
        
    Returns:
        Collection name string
    """
    if collection_type == "papers_semantic_v1":
        return PAPERS_COLLECTION
    elif collection_type == "pdf_vectors_v2":
        return PDF_VECTORS_COLLECTION
    else:
        raise ValueError(f"Unknown collection type: {collection_type}")
