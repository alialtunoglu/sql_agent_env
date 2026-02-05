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
    requires_approval: bool = False  # True if SQL needs user approval before execution
    error: Optional[str] = None


class ExecuteSQLRequest(BaseModel):
    """Request model for executing approved SQL"""
    sql_query: str
    session_id: str


class ExecuteSQLResponse(BaseModel):
    """Response model for SQL execution"""
    success: bool
    message: str
    chart_data: Optional[List[Dict[str, Any]]] = None
    chart_type: Optional[str] = None
    row_count: Optional[int] = None
    data: Optional[List[Dict[str, Any]]] = None  # Full result set for export/download
    error: Optional[str] = None
