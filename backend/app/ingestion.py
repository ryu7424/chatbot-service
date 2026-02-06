from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
import numpy as np
from app.database import SessionLocal
from app.models import DocumentChunk
import logging

# Mock Embeddings for Prototype (dimension 1536 to match OpenAI)
class MockEmbeddings(Embeddings):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Return random vectors normalized
        return [np.random.rand(1536).tolist() for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        return np.random.rand(1536).tolist()

class IngestionService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        self.embeddings = MockEmbeddings() # Replace with OpenAIEmbeddings() in prod
        self.db = SessionLocal()

    def process_documents(self, documents: List[Document]):
        logging.info(f"Processing {len(documents)} documents...")
        
        chunks_to_save = []
        
        for doc in documents:
            # 1. Split
            chunks = self.text_splitter.split_documents([doc])
            
            # 2. Embed (Batching recommended in real impl)
            texts = [c.page_content for c in chunks]
            vectors = self.embeddings.embed_documents(texts)
            
            # 3. Prepare for DB
            for i, chunk in enumerate(chunks):
                db_chunk = DocumentChunk(
                    source_id=chunk.metadata.get("source_id"),
                    chunk_index=i,
                    content=chunk.page_content,
                    embedding=vectors[i],
                    metadata_=chunk.metadata # ACLs are here
                )
                chunks_to_save.append(db_chunk)
        
        # 4. Save
        try:
            self.db.bulk_save_objects(chunks_to_save)
            self.db.commit()
            logging.info(f"Saved {len(chunks_to_save)} chunks to DB.")
        except Exception as e:
            self.db.rollback()
            logging.error(f"Failed to save chunks: {e}")
            raise e
        finally:
            self.db.close()

if __name__ == "__main__":
    # Test Run
    from app.loaders import SecureConfluenceLoader, SecureJiraLoader
    
    logging.basicConfig(level=logging.INFO)
    
    # 1. Load
    conf_loader = SecureConfluenceLoader("http://mock", "user", "key")
    jira_loader = SecureJiraLoader("http://mock", "user", "key")
    
    docs = []
    docs.extend(conf_loader.load())
    docs.extend(jira_loader.load("project=ALL"))
    
    # 2. Ingest
    ingestion = IngestionService()
    ingestion.process_documents(docs)
