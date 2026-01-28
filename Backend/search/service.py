"""Vector search service using Qdrant."""
import os
import fitz
import requests  # Fixed import - requests is not from fastapi
from io import BytesIO
from typing import List, Dict, Any, Optional
from qdrant_client.http import models
from Backend.database.qdrant_client import get_qdrant_client, get_collection_name

FIELDS = ["biology", "chemistry", "computer_science", "engineering", "mathematics", "physics"]
PAGE_CACHE = {}

class SearchService:
    def __init__(
        self,
        collection_name: str = None
    ):
        """
        Initialize SearchService with centralized Qdrant client.
        
        Args:
            collection_name: Optional collection name (defaults to papers collection from env)
        """
        self.client = get_qdrant_client()
        self.collection_name = collection_name or get_collection_name("papers_semantic_v1")
        
    


    def get_num_pages_cached(self,pdf_url:str)->int:
        if pdf_url in PAGE_CACHE:
            return PAGE_CACHE[pdf_url]
    
        response = requests.get(pdf_url, timeout=10)
        with fitz.open(stream=BytesIO(response.content), filetype="pdf") as doc:
            PAGE_CACHE[pdf_url] = doc.page_count
    
        return PAGE_CACHE[pdf_url]

    def format_result(self, item: Any) -> Dict[str, Any]:
     
     
     return {
        "id": item.id,
        "title": item.payload.get("title"),
        "authors": item.payload.get("authors"),
        "abstract": item.payload.get("abstract"),
        "download_url": item.payload.get("download_url"),
        "num_pages":item.payload.get("num_pages"),
        "publication_date": item.payload.get("publication_date"),
        "citation_count": item.payload.get("citation_count"),
        "source_repository": item.payload.get("source_repository"),
        "document_type": item.payload.get("document_type"),
        "field_of_study": item.payload.get("field_of_study"),
        "arxiv_id": item.payload.get("arxiv_id"),
        "score": item.score,
    }
    def search(
        self,
        dense_embedding: List[float],
        sparse_embedding: Dict[str, List[float]],
        limit: int,
        author_filter: Optional[str] = None,
        field_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
    
        must_conditions = []
    
        if author_filter:
            must_conditions.append(
                models.FieldCondition(
                    key="authors",
                    match=models.MatchValue(value=author_filter),
                )
            )
    
        if field_filter:
            must_conditions.append(
                models.FieldCondition(
                    key="field_of_study",
                    match=models.MatchValue(value=field_filter),
                )
            )
    
        qdrant_filter = (
            models.Filter(must=must_conditions)
            if must_conditions else None
        )
        page_limit_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="num_pages",
                    range=models.Range(lte=30)   # ≤ 30 pages
                )
            ]
        )

    
        # ✅ Dense prefetch
        dense_prefetch = models.Prefetch(
            query=dense_embedding,          # <-- ONLY List[float]
            using="dense",
            limit=limit,
        )
    
        # ✅ Sparse prefetch
        sparse_prefetch = models.Prefetch(
            query=models.SparseVector(
                indices=sparse_embedding["indices"],
                values=sparse_embedding["values"],
            ),
            using="bm25",
            limit=limit,
        )
    
        results = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[dense_prefetch, sparse_prefetch],
            query=models.FusionQuery(
                fusion=models.Fusion.RRF
            ),
            limit=limit,
            with_payload=True,
            query_filter=page_limit_filter,
        )
        # filter_point_num_pages=[] # using this here will reduce the redundancy ovre format result to call the api arXiv for page count as in this already have all query point just we need to filter them here
        
    
        return [self.format_result(point) for point in results.points]
    
    def get_metadata_by_id(
        self,
        point_id: str, 
    ) -> Optional[Dict[str, Any]]:
        """Retrieve metadata for a specific point ID in a collection."""
        result = self.client.retrieve(
             ids=[point_id],
             collection_name=self.collection_name,
             with_payload=True,
             with_vectors=False
         )
        #result is list 
        if result and len(result)>0:
            item = result[0]

            return {
                "title": item.payload.get("title"),
                "authors": item.payload.get("authors"),
                "abstract": item.payload.get("abstract"),
                "download_url": item.payload.get("download_url"),
                "num_pages":item.payload.get("num_pages"),
                "publication_date": item.payload.get("publication_date"),
                "citation_count": item.payload.get("citation_count"),
                "source_repository": item.payload.get("source_repository"),
                "document_type": item.payload.get("document_type"),
                "field_of_study": item.payload.get("field_of_study"),
                "arxiv_id": item.payload.get("arxiv_id")
            }
        return None