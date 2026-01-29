import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent

# 1. Ortam değişkenlerini (.env dosyasını) yükle
load_dotenv()

# API Key kontrolü
if not os.getenv("GOOGLE_API_KEY"):
    print("HATA: GOOGLE_API_KEY bulunamadı. Lütfen .env dosyasını kontrol et.")
    exit()

# 2. Veritabanı Bağlantısı (Senin dosya isminle)
db_path = "sqlite:///Chinook_Sqlite.sqlite"
db = SQLDatabase.from_uri(db_path)

# 3. LLM (Gemini) Ayarları
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash", # Hızlı ve ekonomik model
    temperature=0,            # SQL yazarken yaratıcılık istemiyoruz, kesinlik istiyoruz
    convert_system_message_to_human=True 
)

# 4. SQL Ajanını Oluştur
agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    agent_type="tool-calling", # Modern tool kullanma yöntemi
    verbose=True              # Ajanın düşünce adımlarını terminalde görmek için
)

# 5. Soruyu Sor ve Cevabı Yazdır
soru = "En çok şarkısı (track) olan sanatçı kim ve kaç şarkısı var?"
print(f"\nSoru: {soru}\n{'='*40}")

try:
    response = agent_executor.invoke(soru)
    print(f"\nCevap:\n{response['output']}")
except Exception as e:
    print(f"Bir hata oluştu: {e}")