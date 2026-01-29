from langchain_community.utilities import SQLDatabase
from app.core.config import DB_PATH

def get_db():
    """Veritabanı bağlantı nesnesini döndürür."""
    # SQLite için URI formatı
    db_uri = f"sqlite:///{DB_PATH}"
    return SQLDatabase.from_uri(db_uri) 