from app.services.llm_factory import LLMFactory
from app.core.config import (
    LLM_BACKEND, 
    GOOGLE_API_KEY, 
    OLLAMA_BASE_URL, 
    OLLAMA_MODEL
)

def get_llm():
    """
    Yapılandırılmış LLM modelini döndürür.
    Backend type (Gemini/Ollama) config'den okunur.
    """
    if LLM_BACKEND.lower() == "gemini":
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY .env dosyasında bulunamadı!")
        return LLMFactory.create_chat_model(
            backend="gemini",
            api_key=GOOGLE_API_KEY,
            model="gemini-2.5-flash"
        )
    else:  # ollama
        print(f"✓ Using Ollama LLM: {OLLAMA_MODEL} at {OLLAMA_BASE_URL}")
        return LLMFactory.create_chat_model(
            backend="ollama",
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL
        )