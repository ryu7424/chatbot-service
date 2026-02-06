import pytest
from app.rag import RAGPipeline
from app.ingestion import IngestionService
from app.database import SessionLocal, engine
from sqlalchemy import text
from langchain_core.documents import Document

@pytest.fixture(scope="module")
def setup_data():
    """Ingest some data for testing search"""
    # Clear DB
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE document_chunks"))
        conn.commit()

    docs = [
        Document(
            page_content="Error code 0x80040 occurs when the VPN handshake times out. Reboot the router.", 
            metadata={
                "source_id": "WIKI-100", 
                "title": "VPN Troubleshooting",
                "allowed_groups": ["group:everyone"]
            }
        ),
        Document(
            page_content="The cafeteria search is closed on weekends.", 
            metadata={
                "source_id": "WIKI-101", 
                "allowed_groups": ["group:everyone"]
            }
        ),
        Document(
            page_content="JIRA-555: Login page 500 status. Status: Done.", 
            metadata={
                "source_id": "JIRA-555", 
                "allowed_groups": ["group:dev"]
            }
        )
    ]
    
    service = IngestionService()
    service.process_documents(docs)
    yield
    # Cleanup if needed

def test_hybrid_search_keyword_accuracy(setup_data):
    """
    Test Phase 2 Verification: Retrieval Accuracy (Keyword)
    Query for '0x80040' should return WIKI-100.
    """
    pipeline = RAGPipeline()
    groups = ["group:everyone"]
    
    # Keyword specific
    results = pipeline.search_service.search("0x80040", groups)
    
    found = any("0x80040" in d.content for d in results)
    assert found, "Hybrid search failed to find specific keyword 0x80040"

def test_rag_generation_logic(setup_data):
    """
    Test Phase 2 Verification: Hallucination Check & User Context
    User 'dev' searching for JIRA-555 should get answer 'Done'.
    """
    pipeline = RAGPipeline()
    groups = ["group:dev"]
    
    answer = pipeline.query("Is the login bug (JIRA-555) fixed?", groups)
    assert "Done" in answer
    assert "JIRA-555" in answer

def test_rag_security_filtering_in_pipeline(setup_data):
    """
    Test Phase 2 Verification: RAG pipeline respects ACL.
    User 'marketing' (not in 'group:dev') should NOT see JIRA-555 info.
    """
    pipeline = RAGPipeline()
    groups = ["group:marketing"]
    
    # Try to fish for info
    answer = pipeline.query("Is the login bug JIRA-555 fixed?", groups)
    
    # Should get "I cannot find..." or generic fallback without the confidential info
    assert "Done" not in answer
    assert "I cannot find" in answer
