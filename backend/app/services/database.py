from langchain_community.utilities import SQLDatabase
from app.core.config import DB_PATH
import json
import os

def get_db(db_path: str = None):
    """
    Veritabanı bağlantı nesnesini döndürür.
    
    Args:
        db_path: Custom database path. If None, uses default Chinook DB.
    
    Returns:
        SQLDatabase connection object
    """
    if db_path is None:
        db_path = DB_PATH
    
    # SQLite için URI formatı
    db_uri = f"sqlite:///{db_path}"
    return SQLDatabase.from_uri(db_uri)

def get_schema_metadata():
    """
    Chinook veritabanı şema metadata'sını yükler.
    
    Returns:
        dict: Schema metadata bilgileri
    """
    metadata_path = os.path.join(
        os.path.dirname(DB_PATH),
        "schema_metadata.json"
    )
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Schema metadata dosyası bulunamadı: {metadata_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Schema metadata JSON parse hatası: {e}")
        return {}

def generate_enhanced_schema_description():
    """
    LLM için zenginleştirilmiş şema açıklaması üretir.
    
    Returns:
        str: Agent prompt'una eklenecek şema açıklaması
    """
    metadata = get_schema_metadata()
    
    if not metadata:
        return ""
    
    description_parts = [
        f"## VERİTABANI: {metadata.get('database_name', 'Unknown')}",
        f"{metadata.get('database_description', '')}",
        "\n## TABLO DETAYLARI:\n"
    ]
    
    tables = metadata.get('tables', {})
    for table_name, table_info in tables.items():
        description_parts.append(f"### {table_name}")
        description_parts.append(f"- Açıklama: {table_info.get('description', '')}")
        
        # Sütun açıklamaları
        columns = table_info.get('columns', {})
        if columns:
            description_parts.append("- Sütunlar:")
            for col_name, col_desc in columns.items():
                description_parts.append(f"  * {col_name}: {col_desc}")
        
        # İlişkiler
        relationships = table_info.get('relationships', [])
        if relationships:
            description_parts.append("- İlişkiler:")
            for rel in relationships:
                description_parts.append(f"  * {rel}")
        
        # İş kuralları
        business_rules = table_info.get('business_rules', [])
        if business_rules:
            description_parts.append("- İş Kuralları:")
            for rule in business_rules:
                description_parts.append(f"  * {rule}")
        
        description_parts.append("")  # Boş satır
    
    # Yaygın JOIN pattern'leri
    common_joins = metadata.get('common_join_patterns', [])
    if common_joins:
        description_parts.append("\n## YAYGIN JOIN PATTERN'LERİ:\n")
        for pattern in common_joins:
            description_parts.append(f"- {pattern.get('description', '')}")
            description_parts.append(f"  ```sql\n  {pattern.get('query', '')}\n  ```")
    
    # Görselleştirme ipuçları
    viz_hints = metadata.get('visualization_hints', [])
    if viz_hints:
        description_parts.append("\n## GÖRSELLEŞTİRME İPUÇLARI:\n")
        for hint in viz_hints:
            description_parts.append(
                f"- {hint.get('query_type', '')}: {hint.get('description', '')} "
                f"(Önerilen: {hint.get('suggested_chart', 'bar')} chart)"
            )
    
    return "\n".join(description_parts) 