import os
from sqlalchemy import create_engine, text

# Hardcoded from .env just to be sure
DATABASE_URL = "postgresql://root:wDbBnMWO5o9E160TrN34vdVmZayc87e2@tpe1.clusters.zeabur.com:20845/zeabur"

def fix_db():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check columns
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'wine_items'"))
        columns = [row[0] for row in result]
        print(f"Current columns: {columns}")

        # Add missing
        if 'purchase_date' not in columns:
            print("Adding purchase_date...")
            conn.execute(text("ALTER TABLE wine_items ADD COLUMN purchase_date DATE DEFAULT CURRENT_DATE"))
        
        if 'optimal_drinking_start' not in columns:
            print("Adding optimal_drinking_start...")
            conn.execute(text("ALTER TABLE wine_items ADD COLUMN optimal_drinking_start DATE"))

        if 'optimal_drinking_end' not in columns:
            print("Adding optimal_drinking_end...")
            conn.execute(text("ALTER TABLE wine_items ADD COLUMN optimal_drinking_end DATE"))

        if 'preservation_type' not in columns:
            print("Adding preservation_type...")
            conn.execute(text("ALTER TABLE wine_items ADD COLUMN preservation_type VARCHAR(50) DEFAULT 'immediate'"))

        if 'remaining_amount' not in columns:
            print("Adding remaining_amount...")
            conn.execute(text("ALTER TABLE wine_items ADD COLUMN remaining_amount VARCHAR(20) DEFAULT 'full'"))
        
        if 'purchase_price' not in columns:
             print("Adding purchase_price...")
             conn.execute(text("ALTER TABLE wine_items ADD COLUMN purchase_price FLOAT"))

        if 'retail_price' not in columns:
             print("Adding retail_price...")
             conn.execute(text("ALTER TABLE wine_items ADD COLUMN retail_price FLOAT"))
             
        # Also check for 'bottle_status' just in case
        if 'bottle_status' not in columns:
             print("Adding bottle_status...")
             conn.execute(text("ALTER TABLE wine_items ADD COLUMN bottle_status VARCHAR(20) DEFAULT 'unopened'"))

        conn.commit()
        print("Database fix completed.")

if __name__ == "__main__":
    fix_db()
