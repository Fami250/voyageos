from pathlib import Path

# Base directory (travel_app folder)
BASE_DIR = Path(__file__).resolve().parent.parent

# SQLite database path
DATABASE_URL = f"sqlite:///{BASE_DIR / 'travel.db'}"
