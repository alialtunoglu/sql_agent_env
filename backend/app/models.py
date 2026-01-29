from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    chart_data: Optional[List[Dict[str, Any]]] = None # Recharts için uygun format: [{name: 'A', value: 10}, ...]
    chart_type: Optional[str] = None # 'bar', 'line', 'pie' etc.
    sql_query: Optional[str] = None
    error: Optional[str] = None
