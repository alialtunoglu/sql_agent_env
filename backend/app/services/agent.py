from langchain_community.agent_toolkits import create_sql_agent
from app.services.database import get_db
from app.services.llm import get_llm
from app.services.tools import chart_tool

def build_agent():
    db = get_db()
    llm = get_llm()

    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools",
        extra_tools=[chart_tool],
        verbose=True,
        max_iterations=10
    )
    
    return agent_executor