from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse, ExecuteSQLRequest, ExecuteSQLResponse
from app.services.agent import build_agent
from app.services.memory import create_memory_backend, AbstractChatMemory
from app.services.user_database import get_user_database_service
from app.core.config import MEMORY_BACKEND, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
import json
import re
import uuid
from typing import Dict
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.utilities import SQLDatabase

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
        
        # Check if user has uploaded database
        user_db_service = get_user_database_service()
        user_db_path = user_db_service.get_user_database_path(session_id)
        user_schema = user_db_service.generate_user_schema_description(session_id)
        
        # Agent'ı chat history ve RAG ile oluştur
        # If user has database, use it; otherwise use default Chinook
        agent, _ = build_agent(
            chat_history=chat_history,
            user_query=request.query,
            db_path=user_db_path,  # Will be None if no user database
            user_schema=user_schema,  # Will be None if no user database
            use_rag=(user_db_path is None)  # Use RAG only for default database
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
            sql_query=sql_query,
            requires_approval=False  # Auto-executed by agent
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


@router.post("/execute-sql", response_model=ExecuteSQLResponse)
async def execute_sql(request: ExecuteSQLRequest):
    """
    Execute user-approved SQL query.
    Provides a safety mechanism for reviewing SQL before execution.
    """
    try:
        # Validate SQL - only allow SELECT statements
        sql_upper = request.sql_query.strip().upper()
        
        # Security check: Block dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE']
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise HTTPException(
                    status_code=400,
                    detail=f"Güvenlik nedeniyle {keyword} komutu engellenmiştir. Sadece SELECT sorguları çalıştırılabilir."
                )
        
        if not sql_upper.startswith('SELECT'):
            raise HTTPException(
                status_code=400,
                detail="Güvenlik nedeniyle sadece SELECT sorguları çalıştırılabilir."
            )
        
        # Get appropriate database
        user_db_service = get_user_database_service()
        user_db_path = user_db_service.get_user_database_path(request.session_id)
        
        # Connect to database
        if user_db_path:
            db_uri = f"sqlite:///{user_db_path}"
        else:
            from app.core.config import DB_PATH
            db_uri = f"sqlite:///{DB_PATH}"
        
        db = SQLDatabase.from_uri(db_uri)
        
        # Execute query
        result = db.run(request.sql_query)
        
        # Parse result (typically comes as string)
        row_count = 0
        if result:
            # Try to count rows (rough estimate)
            lines = result.strip().split('\n')
            row_count = max(0, len(lines) - 1)  # Exclude header
        
        return ExecuteSQLResponse(
            success=True,
            message=f"Sorgu başarıyla çalıştırıldı. {row_count} satır döndü.",
            row_count=row_count,
            chart_data=None  # Could be enhanced to auto-generate chart
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ExecuteSQLResponse(
            success=False,
            message="Sorgu çalıştırılamadı.",
            error=str(e)
        )
