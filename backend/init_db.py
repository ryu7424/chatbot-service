from app.database import engine, Base
from app.models import DocumentChunk
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    logger.info("Creating tables...")
    try:
        # Create vector extension if it doesn't exist (requires superuser, usually 'postgres')
        # In our docker-compose, we are 'admin' which should have privileges or we pre-init.
        # But 'admin' might not be superuser. Let's try.
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")

if __name__ == "__main__":
    init_db()
