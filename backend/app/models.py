from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    chart_data: Optional[List[Dict[str, Any]]] = None # Recharts için uygun format: [{name: 'A', value: 10}, ...]
    chart_type: Optional[str] = None # 'bar', 'line', 'pie' etc.
    sql_query: Optional[str] = None
    error: Optional[str] = None
