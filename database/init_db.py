import sys
import os

# Add backend directory to sys.path so we can import app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(os.path.dirname(current_dir), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import text, inspect
from app.core.config import settings
from app.core.database import engine, Base
import app.models  # Registers all models with Base.metadata


def init_database():
    """Verify database connection and initialize all relational schema tables."""
    print(f"Connecting to database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            print("Database connection test: OK (SELECT 1 returned", result, ")")
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        sys.exit(1)

    print("Creating relational schema tables via SQLAlchemy ORM...")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Tables found in database:")
    for t in tables:
        print(f"  - {t}")

    expected_tables = ["users", "jobs", "resumes", "interviews", "questions", "answers"]
    missing = [t for t in expected_tables if t not in tables]
    if missing:
        print(f"WARNING: Missing expected tables: {missing}")
        sys.exit(1)

    print("\nDatabase initialization complete! Schema is ready for production.")


if __name__ == "__main__":
    init_database()
