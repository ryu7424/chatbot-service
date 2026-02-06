from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from .database import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String, index=True) # e.g., CONF-1234, JIRA-555
    chunk_index = Column(Integer)
    content = Column(Text, nullable=False)
    
    # 1536 dimensions for OpenAI text-embedding-3-small
    # Adjust to 768 or 384 if using local models (e.g. BGE, BERT)
    embedding = Column(Vector(1536))
    
    # Metadata for ACL and citations
    # Example: {"allowed_roles": ["hr"], "url": "...", "title": "..."}
    metadata_ = Column("metadata", JSONB, nullable=False, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, source={self.source_id})>"
