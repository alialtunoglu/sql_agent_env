from langchain_community.agent_toolkits import create_sql_agent
from src.database import get_db
from src.llm import get_llm

def build_agent():
    """SQL Ajanını oluşturur ve döndürür."""
    db = get_db()
    llm = get_llm()
    
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="tool-calling",
        verbose=True
    )
    return agent_executor