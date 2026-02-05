from langchain_community.agent_toolkits import create_sql_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from app.services.database import get_db, generate_enhanced_schema_description
from app.services.llm import get_llm
from app.services.tools import chart_tool
from typing import Optional, List, Dict

def build_agent(chat_history: Optional[List[BaseMessage]] = None):
    """
    SQL Agent oluşturur. Chat history ile konuşma geçmişi desteklenir.
    Schema metadata ile zenginleştirilmiş prompt kullanır.
    
    Args:
        chat_history: List of BaseMessage objects. None ise boş liste kullanılır.
    """
    db = get_db()
    llm = get_llm()
    
    # Chat history yoksa boş liste kullan
    if chat_history is None:
        chat_history = []
    
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
            "return_intermediate_steps": True
        },
        prefix=prefix_prompt
    )
    
    return agent_executor, chat_history