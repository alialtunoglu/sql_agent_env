from langchain_core.tools import Tool
import json

def generate_chart_json(input_str: str):
    """
    Kullanıcının görselleştirme isteği olduğunda bu aracı kullan.
    
    Girdi (input_str): Aşağıdaki formatta bir JSON string OLMALIDIR:
    {
        "chart_type": "bar", # veya 'line', 'pie', 'scatter'
        "title": "Grafik Başlığı",
        "data": [
            {"name": "Etiket1", "value": 10},
            {"name": "Etiket2", "value": 20}
        ]
    }
    
    Çıktı: Frontend için işaretlenmiş JSON verisi.
    """
    try:
        # LLM bazen JSON'u markdown bloğu içinde verebilir
        clean_input = input_str.replace("```json", "").replace("```", "").strip()
        data_dict = json.loads(clean_input)
        
        # Frontend'in yakalayabilmesi için özel bir blok içine alıyoruz
        return f"CHART_JSON_START{json.dumps(data_dict)}CHART_JSON_END"
    except Exception as e:
        return f"Chart verisi oluşturulurken hata: {e}"

chart_tool = Tool(
    name="Chart_Data_Formatter",
    func=generate_chart_json,
    description="""
    Kullanıcı bir veriyi görselleştirmek istediğinde (grafik, tablo, plot) KESİNLİKLE bu aracı kullanmalısın.
    Bu araç grafik çizmez, sadece grafik için gereken veriyi formatlar.
    
    ADIMLAR:
    1. Önce SQL sorgusu ile veriyi çek.
    2. Sonra bu veriyi şu JSON formatına dönüştür: {"chart_type": "...", "title": "...", "data": [{"name": "X", "value": Y}, ...]}
    3. Bu JSON'ı bu araca girdi olarak ver.
    4. Aracın çıktısını kullanıcıya göster.
    """
)
