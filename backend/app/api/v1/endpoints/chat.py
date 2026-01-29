from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse
from app.services.agent import build_agent, load_chat_history
import json
import re
import uuid
from typing import Dict
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory

router = APIRouter()

# Session bazlı chat history store (in-memory)
# Production'da Redis veya database kullanılmalı
session_histories: Dict[str, BaseChatMessageHistory] = {}

def get_or_create_session(session_id: str = None) -> tuple[str, BaseChatMessageHistory]:
    """
    Session ID'yi kontrol eder veya yeni oluşturur.
    
    Returns:
        (session_id, chat_history) tuple
    """
    if session_id and session_id in session_histories:
        return session_id, session_histories[session_id]
    
    # Yeni session oluştur
    new_session_id = session_id or str(uuid.uuid4())
    new_history = InMemoryChatMessageHistory()
    session_histories[new_session_id] = new_history
    return new_session_id, new_history

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Session yönetimi
        session_id, chat_history = get_or_create_session(request.session_id)
        
        # Eğer messages gönderildiyse, history'yi güncelle
        if request.messages:
            chat_history = load_chat_history(
                [{"role": m.role, "content": m.content} for m in request.messages]
            )
            session_histories[session_id] = chat_history
        
        # Agent'ı chat history ile oluştur
        agent, _ = build_agent(chat_history)
        
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
        
        # Chat history'ye mesajları ekle
        from langchain_core.messages import HumanMessage, AIMessage
        chat_history.add_message(HumanMessage(content=request.query))
        chat_history.add_message(AIMessage(content=str(output_text)))
        
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
