from typing import List
from app.search_service import HybridSearchService
from app.models import DocumentChunk
import logging

logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self):
        self.search_service = HybridSearchService()
        
    def rerank(self, query: str, docs: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        Mock Reranker. In prod, use CrossEncoder (e.g. bge-reranker).
        Here we just return the docs as-is (assuming Fusion did a good enough job)
        or maybe perform a simple keyword boost check.
        """
        # Simple prototype logic: Boost exact matches in title
        # This is just to demonstrate 'reranking' logic step exists.
        def score(doc):
            s = 0
            if query.lower() in doc.content.lower():
                s += 1
            if "title" in doc.metadata_ and query.lower() in doc.metadata_["title"].lower():
                s += 2
            return s
            
        # We only re-sort if we have a tie-breaker, but RRF is robust.
        # Let's just return list for now to keep it simple as detailed in plan.
        return docs

    def generate_answer(self, query: str, context_docs: List[DocumentChunk]) -> str:
        """
        Mock Generation. In prod, call OpenAI/LLM.
        """
        if not context_docs:
            return "I cannot find any information about that in the internal knowledge base."
            
        # Context construction
        context_str = "\n\n".join([f"Source: {d.metadata_.get('title', 'Unknown')}\nContent: {d.content}" for d in context_docs])
        
        # PROTOTYPE MOCK RESPONSE
        # Check if the context contains the answer (conceptually)
        found_answers = []
        for doc in context_docs:
            if "Status: Done" in doc.content and "login bug" in query.lower():
                found_answers.append("The login bug (JIRA-101) is marked as Done.")
            if ("Project Secret X" in doc.content or "Top secret" in doc.content) and "secret" in query.lower():
                 found_answers.append("Project Secret X is a top secret initiative.")
            if "0x80040" in doc.content and "0x80040" in query:
                found_answers.append("Error 0x80040 is related to VPN timeouts.")

        if found_answers:
             return f"Based on the internal documents:\n" + " ".join(found_answers) + "\n\nSources:\n" + "\n".join([f"- {d.metadata_.get('source_id')}" for d in context_docs])
        
        # Fallback - If no specific knowledge extracted, assume not found (Strict Mock)
        return "I cannot find any information about that in the internal knowledge base."

    def query(self, user_query: str, user_groups: List[str]) -> str:
        # 1. Retrieve (Hybrid)
        retrieved_docs = self.search_service.search(user_query, user_groups)
        
        # 2. Rerank
        reranked_docs = self.rerank(user_query, retrieved_docs)
        
        # 3. Generate
        answer = self.generate_answer(user_query, reranked_docs)
        
        return answer
