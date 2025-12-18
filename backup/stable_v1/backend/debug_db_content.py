from app.database import SessionLocal
from app.models import Freight

def check_db():
    db = SessionLocal()
    try:
        freights = db.query(Freight).order_by(Freight.created_at.desc()).limit(5).all()
        count = db.query(Freight).count()
        
        print(f"Total freights in DB: {count}")
        print("-" * 50)
        
        if not freights:
            print("No freights found.")
        
        for f in freights:
            print(f"ID: {f.id}")
            print(f"Route: {f.loading_place} -> {f.unloading_place}")
            print(f"Distance: {f.distance_km} km")
            print(f"Created: {f.created_at}")
            print("-" * 50)
            
    finally:
        db.close()

if __name__ == "__main__":
    check_db()
