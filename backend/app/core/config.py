import os
from dotenv import load_dotenv

# .env dosyasını yükle (bir üst dizinde olduğu için path belirtiyoruz)
# .env dosyasını yükle (backend/app/core -> backend/.env)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Veritabanı yolunu dinamik olarak bul (backend/data/...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # backend/app -> backend
DB_PATH = os.path.join(BASE_DIR, "data", "Chinook_Sqlite.sqlite")

# Memory Backend Configuration
MEMORY_BACKEND = os.getenv("MEMORY_BACKEND", "redis")  # Options: 'redis', 'in-memory'
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY = os.path.join(BASE_DIR, "data", "chroma_db")

# User Upload Configuration
USER_DB_DIRECTORY = os.path.join(BASE_DIR, "data", "user_databases")