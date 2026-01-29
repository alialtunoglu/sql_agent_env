from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse
from app.services.agent import build_agent
import json
import re

router = APIRouter()

# Ajanı bir kez başlat (Global state olarak tutulabilir veya her istekte yeniden oluşturulabilir)
# SQLite bağlantısı thread-safe olmayabilir, bu yüzden her istekte yeni oluşturmak daha güvenli olabilir
# Ancak LLM cache vs için tek instance daha iyi. Şimdilik her istekte build edelim.

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        agent = build_agent()
        
        # Ajanı çalıştır
        result = agent.invoke(request.query)
        output_text = result['output']
        
        chart_data = None
        sql_query = None # Advanced: Ajanın intermediate_steps kısmından SQL çekilebilir
        
        # JSON verisini parse et
        # Format: CHART_JSON_START{...}CHART_JSON_END
        json_pattern = r"CHART_JSON_START(.*?)CHART_JSON_END"
        match = re.search(json_pattern, output_text, re.DOTALL)
        
        cleaned_answer = output_text
        if match:
            json_str = match.group(1)
            try:
                chart_info = json.loads(json_str)
                # chart_info içinde "data" var mı kontrol et
                if "data" in chart_info:
                     # Frontend'in beklediği formatta data gönder
                    chart_data = chart_info["data"]
                    # Answer'dan JSON bloğunu temizle, kullanıcıya ham JSON göstermeyelim
                    cleaned_answer = output_text.replace(match.group(0), "").strip()
                    # Ek bilgi ekle
                    cleaned_answer += f"\n\n(Aşağıda {chart_info.get('title', 'Grafik')} grafiği görüntülenmektedir)"
            except json.JSONDecodeError:
                print("JSON Parse Hatası")
        
        return ChatResponse(
            answer=cleaned_answer,
            chart_data=chart_data
        )
        
    except Exception as e:
        print(f"Hata: {e}")
        return ChatResponse(answer="Bir hata oluştu.", error=str(e))
