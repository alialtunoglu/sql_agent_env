# SQL Veri Analisti - Text-to-SQL AI Asistanı

Modern, kullanıcı dostu bir SQL veri analisti asistanı. Doğal dil ile veritabanı sorguları oluşturun ve sonuçları görselleştirin.

## 🎯 Özellikler

- **Doğal Dil Sorguları**: Türkçe sorularınızı SQL sorgularına dönüştürür
- **Görselleştirme**: Sorgu sonuçlarını grafiklerle görselleştirin
- **Veri Yükleme**: Kendi CSV/Excel dosyalarınızı yükleyin
- **Güvenli SQL**: Sadece SELECT sorgularına izin verilir
- **ChatGPT Tarzı Arayüz**: Modern, sade ve kullanıcı odaklı tasarım

## 📸 Ekran Görüntüleri

### Ana Ekran
![Ana Ekran](screenshots/main-screen.png)

### Sorgu Sonuçları
![Sorgu Sonuçları](screenshots/query-results.png)

### Grafik Görselleştirme
![Grafik Görselleştirme](screenshots/chart-visualization.png)

### Veri Yükleme
![Veri Yükleme](screenshots/file-upload.png)

## 🚀 Kurulum

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📖 Kullanım

1. Uygulamayı başlatın
2. İsteğe bağlı olarak kendi veritabanınızı yükleyin
3. Doğal dilde sorularınızı sorun (örn: "En çok satan 5 albüm hangisi?")
4. AI SQL sorgusu önerecek, onayladıktan sonra sonuçları görüntüleyin
5. Sonuçları CSV/Excel/JSON olarak indirin

## 🛠️ Teknolojiler

- **Backend**: FastAPI, LangChain, SQLite
- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **AI**: OpenAI GPT (veya diğer LLM'ler)

## 📝 Lisans

MIT
