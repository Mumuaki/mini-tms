from app.database import SessionLocal, engine
from app.models import Freight
from sqlalchemy import text
import sys
import os

# Add parent dir to path to find app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    db = SessionLocal()
    try:
        print("Cleaning 'freights' table...")
        # Delete all rows
        num_deleted = db.query(Freight).delete()
        db.commit()
        print(f"Deleted {num_deleted} freights.")
        
        # Try to reset ID sequence (for Postgres primarily, but harmless elsewhere)
        try:
             # Adjust table name if needed. Usually 'freights'.
             # Check if sqlalchemy knows the table name
             db.execute(text("VACUUM")) # For SQLite to reclaim space, optional
             # db.execute(text("DELETE FROM sqlite_sequence WHERE name='freights'")) # Reset autoincrement in SQLite
        except: pass
        
    except Exception as e:
        print(f"Error cleaning database: {e}")
        db.rollback()
    finally:
        db.close()
