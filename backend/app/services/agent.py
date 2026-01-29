from langchain_community.agent_toolkits import create_sql_agent
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.agents import AgentExecutor
from app.services.database import get_db, generate_enhanced_schema_description
from app.services.llm import get_llm
from app.services.tools import chart_tool
from typing import Optional, List, Dict

def build_agent(memory: Optional[ConversationBufferMemory] = None):
    """
    SQL Agent oluşturur. Memory parametresi ile konuşma geçmişi desteklenir.
    Schema metadata ile zenginleştirilmiş prompt kullanır.
    
    Args:
        memory: ConversationBufferMemory instance. None ise yeni memory oluşturulur.
    """
    db = get_db()
    llm = get_llm()
    
    # Memory yoksa yeni oluştur
    if memory is None:
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
    
    # Schema metadata'yı al
    schema_description = generate_enhanced_schema_description()
    
    # Custom prefix prompt (schema bilgileri ile zenginleştirilmiş)
    prefix_prompt = f"""Sen bir SQL veri analisti asistanısın. Kullanıcıların veritabanı sorularını anlamak ve doğru SQL sorguları üretmek için tasarlandın.

{schema_description}

## GÖREV KURALLARI:
1. Kullanıcının sorusunu dikkatlice analiz et ve önceki konuşma bağlamını (chat history) dikkate al
2. Uygun SQL sorgusu yaz ve çalıştır
3. Sonuçları kullanıcı dostu bir dilde açıkla
4. Eğer kullanıcı görselleştirme isterse (grafik, chart, vb.) veya veri görselleştirmeye uygunsa, MUTLAKA Chart_Data_Formatter aracını kullan
5. Tarih sorgularında SQLite tarih fonksiyonlarını kullan: strftime('%Y-%m-%d', column_name)
6. Türkçe sütun adları için tırnak işareti kullanmayı unutma

## GÖRSELLEŞTİRME KURALI:
Kullanıcı "göster", "grafik", "trend", "dağılım", "karşılaştır" gibi kelimeler kullanıyorsa veya 
sorgu sonucu sayısal veriler içeriyorsa, Chart_Data_Formatter aracını kullanarak grafik verisi oluştur.

Önce SQL sorgusunu çalıştır, sonra sonuçları Chart_Data_Formatter'a uygun formatta gönder.
"""

    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools",
        extra_tools=[chart_tool],
        verbose=True,
        max_iterations=15,  # Metadata ile daha karmaşık sorgular için artırıldı
        agent_executor_kwargs={
            "memory": memory,
            "return_intermediate_steps": True
        },
        prefix=prefix_prompt
    )
    
    return agent_executor

def load_chat_history_to_memory(messages: List[Dict[str, str]]) -> ConversationBufferMemory:
    """
    Geçmiş mesajları memory'ye yükler.
    
    Args:
        messages: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    
    Returns:
        ConversationBufferMemory instance
    """
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="output"
    )
    
    for msg in messages:
        if msg["role"] == "user":
            memory.chat_memory.add_message(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            memory.chat_memory.add_message(AIMessage(content=msg["content"]))
    
    return memory