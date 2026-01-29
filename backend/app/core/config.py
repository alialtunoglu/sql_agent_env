import os
from dotenv import load_dotenv

# .env dosyasını yükle (bir üst dizinde olduğu için path belirtiyoruz)
# .env dosyasını yükle (backend/app/core -> backend/.env)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Veritabanı yolunu dinamik olarak bul (backend/data/...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # backend/app -> backend
DB_PATH = os.path.join(BASE_DIR, "data", "Chinook_Sqlite.sqlite")