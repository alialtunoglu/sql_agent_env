from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse
from app.services.agent import build_agent
from app.services.memory import create_memory_backend, AbstractChatMemory
from app.core.config import MEMORY_BACKEND, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
import json
import re
import uuid
from typing import Dict
from langchain_core.messages import HumanMessage, AIMessage

router = APIRouter()

# Initialize memory backend based on configuration
try:
    if MEMORY_BACKEND.lower() == "redis":
        memory_backend: AbstractChatMemory = create_memory_backend(
            backend_type="redis",
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
        )
        print(f"✓ Using Redis memory backend at {REDIS_HOST}:{REDIS_PORT}")
    else:
        memory_backend: AbstractChatMemory = create_memory_backend(backend_type="in-memory")
        print("⚠ Using in-memory backend (not recommended for production)")
except Exception as e:
    print(f"⚠ Failed to initialize {MEMORY_BACKEND} backend: {e}")
    print("⚠ Falling back to in-memory backend")
    memory_backend: AbstractChatMemory = create_memory_backend(backend_type="in-memory")


def get_or_create_session(session_id: str = None) -> str:
    """
    Session ID'yi kontrol eder veya yeni oluşturur.
    
    Returns:
        session_id
    """
    if session_id and memory_backend.session_exists(session_id):
        return session_id
    
    # Yeni session oluştur
    new_session_id = session_id or str(uuid.uuid4())
    return new_session_id

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Session yönetimi
        session_id = get_or_create_session(request.session_id)
        
        # Mevcut chat history'yi al
        chat_history = memory_backend.get_messages(session_id)
        
        # Agent'ı chat history ve RAG ile oluştur
        agent, _ = build_agent(
            chat_history=chat_history,
            user_query=request.query,
            use_rag=True
        )
        
        # Ajanı çalıştır
        result = agent.invoke({"input": request.query})
        
        # Output'u düzgün al (list veya string olabilir)
        output_text = result.get('output', '')
        if isinstance(output_text, list):
            # List ise, son text elementi al
            output_text = ''
            for item in result['output']:
                if isinstance(item, dict) and 'text' in item:
                    output_text += item['text'] + ' '
                elif isinstance(item, str):
                    output_text += item + ' '
            output_text = output_text.strip()
        
        # Chat history'ye mesajları ekle (Abstract memory layer kullanarak)
        memory_backend.add_messages(
            session_id,
            [
                HumanMessage(content=request.query),
                AIMessage(content=str(output_text))
            ]
        )
        
        chart_data = None
        sql_query = None
        
        # intermediate_steps'ten SQL query çıkar
        if 'intermediate_steps' in result:
            for step in result['intermediate_steps']:
                if hasattr(step[0], 'tool') and 'sql' in step[0].tool.lower():
                    sql_query = step[1]
                    break
        
        # JSON verisini parse et
        # Format: CHART_JSON_START{...}CHART_JSON_END
        json_pattern = r"CHART_JSON_START(.*?)CHART_JSON_END"
        
        # output_text'in string olduğundan emin ol
        output_str = str(output_text)
        match = re.search(json_pattern, output_str, re.DOTALL)
        
        cleaned_answer = output_str
        if match:
            json_str = match.group(1)
            try:
                chart_info = json.loads(json_str)
                # chart_info içinde "data" var mı kontrol et
                if "data" in chart_info:
                     # Frontend'in beklediği formatta data gönder
                    chart_data = chart_info["data"]
                    # Answer'dan JSON bloğunu temizle, kullanıcıya ham JSON göstermeyelim
                    cleaned_answer = output_str.replace(match.group(0), "").strip()
                    # Ek bilgi ekle
                    cleaned_answer += f"\n\n(Aşağıda {chart_info.get('title', 'Grafik')} grafiği görüntülenmektedir)"
            except json.JSONDecodeError:
                print("JSON Parse Hatası")
        
        return ChatResponse(
            answer=cleaned_answer,
            session_id=session_id,
            chart_data=chart_data,
            sql_query=sql_query
        )
        
    except Exception as e:
        print(f"Hata: {e}")
        import traceback
        traceback.print_exc()
        return ChatResponse(
            answer="Bir hata oluştu.",
            session_id=request.session_id or str(uuid.uuid4()),
            error=str(e)
        )
