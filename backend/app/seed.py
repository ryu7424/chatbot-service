from app.ingestion import IngestionService
from sqlalchemy import text
from app.database import engine
from langchain_core.documents import Document

def seed():
    # Clear DB first to be clean
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE document_chunks"))
        conn.commit()
        
    service = IngestionService()
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
            page_content="Project Secret X is a top secret initiative to build a space elevator. Status: Planning.", 
            metadata={
                "source_id": "SECRET-001", 
                "title": "Project Secret X",
                "allowed_groups": ["group:executives"]
            }
        ),
    ]
    service.process_documents(docs)
    print("Seeding complete: Secret X and VPN docs added.")

if __name__ == "__main__":
    seed()
