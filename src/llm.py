from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import GOOGLE_API_KEY

def get_llm():
    """Yapılandırılmış LLM modelini döndürür."""
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY .env dosyasında bulunamadı!")
    
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0, # SQL sorguları için 0 olması önemlidir
        google_api_key=GOOGLE_API_KEY,
        convert_system_message_to_human=True
    )