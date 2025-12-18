from app.database import engine, Base
from app import models # Import models to register them in metadata
import sys
import os

# Ensure app module can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    print(f"Connecting to database: {engine.url}")
    print("Dropping all tables...")
    try:
        # Reflect DB to drop everything including alembic_version if needed, 
        # or just drop specific models. dropping base.metadata.drop_all is safer for just our tables.
        Base.metadata.drop_all(bind=engine)
        print("Tables dropped successfully.")
        
        print("Creating new tables with updated schema...")
        Base.metadata.create_all(bind=engine)
        print("Database reset complete! New columns (body_type, payment_terms, etc.) are ready.")
        
    except Exception as e:
        print(f"Error resetting database: {e}")
