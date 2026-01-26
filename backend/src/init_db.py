
import asyncio
from src.database import Base, engine
from src import models  # This imports Invitation via __init__.py

async def init_models():
    print("Creating tables...")
    # This is synchronous in standard SQLAlchemy with psycopg2, 
    # but if using async engine we need await. 
    # Based on main.py, it uses sync engine for create_all usually or run_sync.
    # Let's check database.py content first to be sure.
    # Assuming sync engine based on main.py: Base.metadata.create_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

if __name__ == "__main__":
    init_models()
