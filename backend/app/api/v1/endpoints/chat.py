from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse
from app.services.agent import build_agent, load_chat_history_to_memory
import json
import re
import uuid
from typing import Dict
from langchain.memory import ConversationBufferMemory

router = APIRouter()

# Session bazlı memory store (in-memory)
# Production'da Redis veya database kullanılmalı
session_memories: Dict[str, ConversationBufferMemory] = {}

def get_or_create_session(session_id: str = None) -> tuple[str, ConversationBufferMemory]:
    """
    Session ID'yi kontrol eder veya yeni oluşturur.
    
    Returns:
        (session_id, memory) tuple
    """
    if session_id and session_id in session_memories:
        return session_id, session_memories[session_id]
    
    # Yeni session oluştur
    new_session_id = session_id or str(uuid.uuid4())
    new_memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="output"
    )
    session_memories[new_session_id] = new_memory
    return new_session_id, new_memory

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Session yönetimi
        session_id, memory = get_or_create_session(request.session_id)
        
        # Eğer messages gönderildiyse, memory'yi güncelle
        if request.messages:
            memory = load_chat_history_to_memory(
                [{"role": m.role, "content": m.content} for m in request.messages]
            )
            session_memories[session_id] = memory
        
        # Agent'ı memory ile oluştur
        agent = build_agent(memory)
        
        # Ajanı çalıştır
        result = agent.invoke({"input": request.query})
        output_text = result['output']
        
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
        match = re.search(json_pattern, output_text, re.DOTALL)
        
        cleaned_answer = output_text
        if match:
            json_str = match.group(1)
            try:
                chart_info = json.loads(json_str)
                # chart_info içinde "data" var mı kontrol et
                if "data" in chart_info:
                     # Frontend'in beklediği formatta data gönder
                    chart_data = chart_info["data"]
                    # Answer'dan JSON bloğunu temizle, kullanıcıya ham JSON göstermeyelim
                    cleaned_answer = output_text.replace(match.group(0), "").strip()
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
