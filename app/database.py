import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# =====================================================
# DATABASE URL (Render Production + Local Fallback)
# =====================================================

DATABASE_URL = os.getenv("DATABASE_URL")

# Fallback for Local Development
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:Fam%40123@localhost:5432/voyageos"

# Required for Render (fixes SSL + connection issues)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# =====================================================
# Dependency
# =====================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
