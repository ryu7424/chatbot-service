import pytest
from app.ingestion import IngestionService
from app.loaders import SecureConfluenceLoader
from app.database import SessionLocal
from app.models import DocumentChunk
from sqlalchemy import text

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

def test_acl_ingestion():
    # 1. Ingest Data
    loader = SecureConfluenceLoader("http://mock", "user", "key")
    docs = loader.load()
    service = IngestionService()
    service.process_documents(docs)
    
    # 2. Verify Data in DB
    session = SessionLocal()
    results = session.query(DocumentChunk).all()
    assert len(results) > 0
    
    # 3. Verify Metadata contains ACL
    sensitive_doc = next(r for r in results if "Top secret" in r.content)
    assert "allowed_groups" in sensitive_doc.metadata_
    assert "group:executives" in sensitive_doc.metadata_["allowed_groups"]
    session.close()

def test_acl_filtering_query():
    """
    Simulate a RAG retrieval with Metadata Filtering.
    """
    session = SessionLocal()
    
    # Scenario 1: User is an 'intern' (no access to RD)
    user_groups = ["group:interns"]
    
    # Filtering Logic (PostgreSQL JSONB containment @>)
    # But here we assume `metadata` field. 
    # Logic: WHERE metadata->'allowed_groups' ?| user_groups
    # Note: SQLAlchemy logic needed.
    
    # For this test, we accept if the logic *would* work or test python side filtering if SQL is complex to mock here without full PG setup
    # But we have full PG setup!
    
    query = session.query(DocumentChunk).filter(
        text("metadata->'allowed_groups' ?| :groups")
    ).params(groups=user_groups)
    
    # Intern should NOT see Secret X
    results = query.all()
    secret_docs = [r for r in results if "Top secret" in r.content]
    assert len(secret_docs) == 0
    
    # Scenario 2: User is 'executive'
    admin_groups = ["group:executives"]
    query_admin = session.query(DocumentChunk).filter(
        text("metadata->'allowed_groups' ?| :groups")
    ).params(groups=admin_groups)
    
    results_admin = query_admin.all()
    secret_docs_admin = [r for r in results_admin if "Top secret" in r.content]
    assert len(secret_docs_admin) > 0
    
    session.close()
