from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import chat

app = FastAPI(
    title="AI Text-to-SQL Agent",
    description="Doğal dil sorgularını SQL'e çeviren ve grafik çizen AI API",
    version="1.0.0"
)

# CORS Ayarları (Frontend için)
origins = [
    "http://localhost:3000", # Next.js Local
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları ekle
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])

@app.get("/")
def read_root():
    return {"message": "AI SQL Agent API Çalışıyor. /docs adresine gidin."}

if __name__ == "__main__":
    import uvicorn
    # Reload sadece geliştirme ortamında true olmalı
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
