import pandas as pd
import matplotlib.pyplot as plt
from langchain_community.agent_toolkits import create_sql_agent
from langchain_core.tools import Tool
from src.database import get_db
from src.llm import get_llm

# --- Grafik Çizme Fonksiyonu ---
def draw_plot(code_str: str):
    """
    Ajanın ürettiği Python kodunu çalıştırır ve grafiği kaydeder.
    """
    try:
        # Kodun içindeki gereksiz markdown işaretlerini temizle (```python ... ``` gibi)
        code_str = code_str.replace("```python", "").replace("```", "").strip()
        
        print(f"\n[DEBUG] Çalıştırılacak Grafik Kodu:\n{code_str}\n")
        
        # Kodu çalıştır (pd ve plt'yi içeri aktarıyoruz)
        exec(code_str, {'pd': pd, 'plt': plt})
        return "Grafik başarıyla 'grafik.png' olarak kaydedildi."
    except Exception as e:
        return f"Grafik çizilirken hata oluştu: {e}"

# --- Ajanı Oluşturma ---
def build_agent():
    db = get_db()
    llm = get_llm()

    # Grafik Aracını Tanımla
    plot_tool = Tool(
        name="Python_Plotter",
        func=draw_plot,
        description="""
        SADECE kullanıcı veriyi görselleştirmek veya grafik çizmek istediğinde bu aracı kullan.
        Önce SQL ile veriyi al, sonra bu aracı kullanarak grafiği çiz.
        Girdi olarak: Veriyi içeren ve matplotlib ile 'grafik.png' dosyası oluşturan TAM PYTHON KODUNU metin olarak ver.
        Veriyi koda manuel olarak (liste veya dict formatında) eklemelisin.
        """
    )

    # create_sql_agent kullanmaya devam ediyoruz, ama 'extra_tools' ekliyoruz
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools", # Gemini için de bu mod genellikle en kararlı çalışandır
        extra_tools=[plot_tool],   # <--- İŞTE SİHİRLİ DOKUNUŞ BURADA
        verbose=True
    )
    
    return agent_executor