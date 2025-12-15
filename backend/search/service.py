"""Vector search service using Qdrant."""
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models

FIELDS = ["biology", "chemistry", "computer_science", "engineering", "mathematics", "physics"]


class SearchService:
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.client = QdrantClient(host=host, port=port)
        self.fields = FIELDS

    def format_result(self, collection: str, item: Any) -> Dict[str, Any]:
        """Format a single search result with all available metadata."""
        return {
            "collection": collection,
            "id" : item.id, #this is unquie id assigned to each paper
            "title": item.payload.get("title"),
            "authors": item.payload.get("authors"),
            "abstract": item.payload.get("abstract"),
            "download_url": item.payload.get("download_url"),
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
        query_vector: List[float],
        limit: int = 5,
        author_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search across all field collections."""
        all_matches = []

        # Build filter if author provided
        qdrant_filter = None
        if author_filter:
            qdrant_filter = models.Filter(
                must=[models.FieldCondition(key="authors", match=models.MatchValue(value=author_filter))]
            )

        # Search each collection
        for field in self.fields:
            results = self.client.query_points(
                collection_name=field.lower(),
                query=query_vector,
                limit=limit,
                search_params=models.SearchParams(hnsw_ef=128),
                query_filter=qdrant_filter
            )

            for item in results.points:
                all_matches.append(self.format_result(field.lower(), item))

        # Sort by score descending
        return sorted(all_matches, key=lambda x: x["score"], reverse=True)
    def get_metadata_by_id(
        self,
        point_id: str,
        collection_name: str 
    ) -> Optional[Dict[str, Any]]:
        """Retrieve metadata for a specific point ID in a collection."""
        result = self.client.retrieve(
             collection_name=collection_name,
             ids=[point_id],
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
                "publication_date": item.payload.get("publication_date"),
                "citation_count": item.payload.get("citation_count"),
                "source_repository": item.payload.get("source_repository"),
                "document_type": item.payload.get("document_type"),
                "field_of_study": item.payload.get("field_of_study"),
                "arxiv_id": item.payload.get("arxiv_id")
            }
        return None