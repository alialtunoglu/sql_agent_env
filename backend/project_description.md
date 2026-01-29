Kullanıcı "Geçen ay en çok satan ürün hangisiydi?" diye sorduğunda, AI'nın otomatik olarak SQL sorgusu yazıp, veritabanına bağlanıp, veriyi çekip, grafiği çizip ve sonucu raporladığı bir sistem.

Senin Kurgun:

Bir "SQL Agent" kur. Bu ajan, veritabanı şemasını (schema) anlar.

Kullanıcı doğal dilde sorar -> Ajan Python/SQL kodu yazar -> Kodu çalıştırır -> Sonucu görselleştirir.

Hata alırsa (Örn: SQL syntax hatası), hatayı kendi düzeltir (Self-Correction) ve tekrar dener.

Teknoloji Stack:

LangChain (SQLDatabaseToolkit)

PostgreSQL / SQLite (Demo veritabanı olarak Chinook veritabanını kullanabilirsin)

Pandas ve Matplotlib/Plotly (Görselleştirme için)
