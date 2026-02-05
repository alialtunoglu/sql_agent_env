from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse, ExecuteSQLRequest, ExecuteSQLResponse
from app.services.agent import build_agent
from app.services.memory import create_memory_backend, AbstractChatMemory
from app.services.user_database import get_user_database_service
from app.core.config import MEMORY_BACKEND, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, DB_PATH
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


@router.get("/chat-history")
async def get_chat_history(session_id: str):
    """
    Retrieve chat history for a session.
    Used to restore conversation when page is refreshed.
    """
    try:
        messages = memory_backend.get_messages(session_id)
        
        # Convert LangChain messages to frontend format
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": "user" if msg.__class__.__name__ == "HumanMessage" else "assistant",
                "content": msg.content
            })
        
        return {
            "session_id": session_id,
            "messages": formatted_messages,
            "count": len(formatted_messages)
        }
    except Exception as e:
        print(f"Error retrieving chat history: {e}")
        return {
            "session_id": session_id,
            "messages": [],
            "count": 0
        }


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
        print(f"📝 Session ID: {session_id}")
        
        # Mevcut chat history'yi al
        chat_history = memory_backend.get_messages(session_id)
        print(f"📚 Retrieved {len(chat_history)} messages from memory")
        
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
        print(f"💾 Saved messages to memory for session {session_id}")
        print(f"   User: {request.query[:50]}...")
        print(f"   AI: {str(output_text)[:50]}...")
        
        # output_text'in string olduğundan emin ol
        output_str = str(output_text)
        
        chart_data = None
        sql_query = None
        requires_approval = False
        
        # Extract SQL query from output using regex (looks for ```sql code blocks)
        sql_pattern = r"```sql\s*([^`]+)\s*```"
        sql_match = re.search(sql_pattern, output_str, re.IGNORECASE | re.DOTALL)
        
        if sql_match:
            sql_query = sql_match.group(1).strip()
            requires_approval = True  # User must approve before execution
        
        # JSON verisini parse et
        # Format: CHART_JSON_START{...}CHART_JSON_END
        json_pattern = r"CHART_JSON_START(.*?)CHART_JSON_END"
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
            requires_approval=requires_approval  # True if SQL needs user approval
        )
        
    except Exception as e:
        print(f"Hata: {e}")
        import traceback
        traceback.print_exc()
        
        # Hata durumunda bile memory'ye kaydet
        try:
            error_message = f"Bir hata oluştu: {str(e)}"
            memory_backend.add_messages(
                request.session_id or str(uuid.uuid4()),
                [
                    HumanMessage(content=request.query),
                    AIMessage(content=error_message)
                ]
            )
            print(f"💾 Saved error to memory")
        except:
            pass  # Ignore memory errors during error handling
        
        return ChatResponse(
            answer=f"Bir hata oluştu: {str(e)}",
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
        
        # Execute query using direct connection for better result parsing
        import sqlite3
        conn = sqlite3.connect(user_db_path if user_db_path else DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable column name access
        cursor = conn.cursor()
        
        cursor.execute(request.sql_query)
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        result_data = [dict(row) for row in rows]
        row_count = len(result_data)
        
        conn.close()
        
        # Format result as markdown table
        result_summary = f"✓ Sorgu başarıyla çalıştırıldı. **{row_count} satır** döndü.\n\n"
        
        chart_data = None
        
        if row_count > 0:
            # Create markdown table
            columns = list(result_data[0].keys())
            
            # Table header
            result_summary += "| " + " | ".join(columns) + " |\n"
            result_summary += "|" + "---|" * len(columns) + "\n"
            
            # Table rows (show max 10 rows)
            display_rows = min(10, row_count)
            for row in result_data[:display_rows]:
                result_summary += "| " + " | ".join(str(v) for v in row.values()) + " |\n"
            
            if row_count > 10:
                result_summary += f"\n*... ve {row_count - 10} satır daha*"
            
            # Auto-generate chart data if suitable (2 columns, second is numeric)
            if len(columns) == 2:
                try:
                    # Check if second column is numeric
                    first_val = result_data[0][columns[1]]
                    if isinstance(first_val, (int, float)):
                        chart_data = [
                            {"name": str(row[columns[0]]), "value": float(row[columns[1]])}
                            for row in result_data[:10]  # Max 10 bars for chart
                        ]
                except:
                    pass  # If conversion fails, no chart
        
        # Save to chat history
        try:
            memory_backend.add_messages(
                request.session_id,
                [
                    HumanMessage(content=f"Şu SQL sorgusunu çalıştırdım:\n```sql\n{request.sql_query}\n```"),
                    AIMessage(content=result_summary)
                ]
            )
            print(f"💾 Saved SQL execution results to memory for session {request.session_id}")
        except Exception as mem_error:
            print(f"⚠ Failed to save to memory: {mem_error}")
        
        return ExecuteSQLResponse(
            success=True,
            message=result_summary,
            row_count=row_count,
            chart_data=chart_data  # Auto-generated chart or None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ExecuteSQLResponse(
            success=False,
            message="Sorgu çalıştırılamadı.",
            error=str(e)
        )
