from typing import List, Dict, Any
from sqlalchemy import text, func
from app.database import SessionLocal
from app.models import DocumentChunk
from app.ingestion import MockEmbeddings
import logging

logger = logging.getLogger(__name__)

class HybridSearchService:
    def __init__(self):
        self.embeddings = MockEmbeddings()

    def search(self, query_text: str, allowed_groups: List[str], limit: int = 5) -> List[DocumentChunk]:
        """
        Performs Hybrid Search (Vector + Keyword) with ACL filtering.
        Uses Reciprocal Rank Fusion (RRF) to combine results.
        """
        session = SessionLocal()
        try:
            # 1. Vector Search (Dense)
            query_vec = self.embeddings.embed_query(query_text)
            # Use l2_distance (Euclidean) or cosine_distance
            # Note: pgvector < 0.5.0 uses operators, 0.5.0+ has functions but operators still work
            # For cosine similarity we often want 1 - cosine_distance.
            # Here we just order by distance ASC (closest first).
            dense_results = session.query(DocumentChunk).filter(
                text("metadata->'allowed_groups' ?| :groups")
            ).order_by(
                DocumentChunk.embedding.l2_distance(query_vec)
            ).params(groups=allowed_groups).limit(limit * 2).all()

            # 2. Keyword Search (Sparse)
            # Using basic ILIKE for prototype simplicity or plain to_tsvector call
            # Ideally: filter(DocumentChunk.content.op("@@")(func.websearch_to_tsquery(query_text)))
            # But let's check if 'english' config exists. Default postgres usually has it.
            sparse_results = session.query(DocumentChunk).filter(
                text("metadata->'allowed_groups' ?| :groups"),
                func.to_tsvector('english', DocumentChunk.content).op('@@')(func.websearch_to_tsquery('english', query_text))
            ).params(groups=allowed_groups).limit(limit * 2).all()

            # 3. Reciprocal Rank Fusion (RRF)
            fused_scores = {}
            k = 60 # RRF constant

            # Rank Dense
            for rank, doc in enumerate(dense_results):
                if doc.id not in fused_scores:
                    fused_scores[doc.id] = {"doc": doc, "score": 0.0}
                fused_scores[doc.id]["score"] += 1.0 / (k + rank + 1)

            # Rank Sparse
            for rank, doc in enumerate(sparse_results):
                if doc.id not in fused_scores:
                    fused_scores[doc.id] = {"doc": doc, "score": 0.0}
                fused_scores[doc.id]["score"] += 1.0 / (k + rank + 1)

            # Sort by fused score DESC
            sorted_results = sorted(
                fused_scores.values(), 
                key=lambda x: x["score"], 
                reverse=True
            )
            
            return [item["doc"] for item in sorted_results[:limit]]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
        finally:
            session.close()
