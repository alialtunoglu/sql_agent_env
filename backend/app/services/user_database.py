"""
User Database Management Service
Handles CSV/Excel file uploads and converts them to session-specific SQLite databases
"""

import os
import pandas as pd
import sqlite3
from typing import Dict, List, Optional, Tuple
from fastapi import UploadFile
from app.core.config import USER_DB_DIRECTORY
import json
import uuid


class UserDatabaseService:
    """Service for managing user-uploaded databases"""

    def __init__(self):
        # Ensure user database directory exists
        os.makedirs(USER_DB_DIRECTORY, exist_ok=True)

    def _get_user_db_path(self, session_id: str) -> str:
        """Get path to user's database file"""
        return os.path.join(USER_DB_DIRECTORY, f"{session_id}.db")

    def _get_metadata_path(self, session_id: str) -> str:
        """Get path to user's metadata file"""
        return os.path.join(USER_DB_DIRECTORY, f"{session_id}_metadata.json")

    async def process_upload(
        self, file: UploadFile, session_id: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Process uploaded file and create SQLite database.
        
        Args:
            file: Uploaded CSV or Excel file
            session_id: User session identifier
        
        Returns:
            Tuple of (success: bool, message: str, metadata: Optional[Dict])
        """
        try:
            # Read file based on extension
            filename = file.filename.lower()
            
            if filename.endswith('.csv'):
                df = pd.read_csv(file.file)
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file.file)
            else:
                return False, "Desteklenmeyen dosya formatı. Lütfen CSV veya Excel dosyası yükleyin.", None

            # Validate dataframe
            if df.empty:
                return False, "Dosya boş veya okunamadı.", None

            # Get database path
            db_path = self._get_user_db_path(session_id)
            
            # Remove existing database if present
            if os.path.exists(db_path):
                os.remove(db_path)

            # Create SQLite database
            conn = sqlite3.connect(db_path)
            
            # Sanitize table name (remove extension and special chars)
            table_name = self._sanitize_table_name(file.filename)
            
            # Write dataframe to database
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            
            # Generate and save metadata
            metadata = self._generate_metadata(df, table_name, file.filename)
            self._save_metadata(session_id, metadata)
            
            conn.close()
            
            return True, f"Dosya başarıyla yüklendi. Tablo adı: {table_name}", metadata

        except pd.errors.EmptyDataError:
            return False, "Dosya boş veya hatalı formatta.", None
        except Exception as e:
            return False, f"Dosya işlenirken hata oluştu: {str(e)}", None

    def _sanitize_table_name(self, filename: str) -> str:
        """Convert filename to valid SQL table name"""
        # Remove extension
        name = os.path.splitext(filename)[0]
        # Replace spaces and special characters with underscore
        name = "".join(c if c.isalnum() else "_" for c in name)
        # Ensure it starts with a letter
        if not name[0].isalpha():
            name = "t_" + name
        # Limit length
        return name[:50].lower()

    def _generate_metadata(
        self, df: pd.DataFrame, table_name: str, original_filename: str
    ) -> Dict:
        """Generate metadata for user database"""
        column_info = {}
        
        for col in df.columns:
            dtype = str(df[col].dtype)
            sample_values = df[col].dropna().head(3).tolist()
            
            # Determine SQL type
            if pd.api.types.is_integer_dtype(df[col]):
                sql_type = "INTEGER"
            elif pd.api.types.is_float_dtype(df[col]):
                sql_type = "REAL"
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                sql_type = "DATETIME"
            else:
                sql_type = "TEXT"
            
            column_info[col] = {
                "pandas_dtype": dtype,
                "sql_type": sql_type,
                "sample_values": [str(v) for v in sample_values],
                "null_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique())
            }
        
        metadata = {
            "original_filename": original_filename,
            "table_name": table_name,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": column_info,
            "upload_timestamp": pd.Timestamp.now().isoformat(),
        }
        
        return metadata

    def _save_metadata(self, session_id: str, metadata: Dict) -> None:
        """Save metadata to JSON file"""
        metadata_path = self._get_metadata_path(session_id)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def get_user_database_path(self, session_id: str) -> Optional[str]:
        """
        Get path to user's database if it exists.
        
        Returns:
            Path to database file or None if not found
        """
        db_path = self._get_user_db_path(session_id)
        return db_path if os.path.exists(db_path) else None

    def get_user_metadata(self, session_id: str) -> Optional[Dict]:
        """
        Get metadata for user's database.
        
        Returns:
            Metadata dict or None if not found
        """
        metadata_path = self._get_metadata_path(session_id)
        
        if not os.path.exists(metadata_path):
            return None
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def generate_user_schema_description(self, session_id: str) -> Optional[str]:
        """
        Generate schema description for user's database (similar to enhanced_schema_description).
        
        Returns:
            Formatted schema description or None if database doesn't exist
        """
        metadata = self.get_user_metadata(session_id)
        
        if not metadata:
            return None
        
        description = f"""## USER UPLOADED DATABASE

**Original File:** {metadata['original_filename']}
**Table Name:** {metadata['table_name']}
**Records:** {metadata['row_count']} rows
**Columns:** {metadata['column_count']} columns

### Table: {metadata['table_name']}

**Columns:**
"""
        
        for col_name, col_info in metadata['columns'].items():
            description += f"\n- **{col_name}** ({col_info['sql_type']})"
            description += f"\n  - Pandas Type: {col_info['pandas_dtype']}"
            description += f"\n  - Unique Values: {col_info['unique_count']}"
            description += f"\n  - Null Count: {col_info['null_count']}"
            if col_info['sample_values']:
                description += f"\n  - Sample Values: {', '.join(col_info['sample_values'][:3])}"
        
        description += "\n\n**Important:** This is user-uploaded data. Always use the exact table and column names shown above."
        
        return description

    def delete_user_database(self, session_id: str) -> bool:
        """
        Delete user's database and metadata.
        
        Returns:
            True if successfully deleted, False otherwise
        """
        try:
            db_path = self._get_user_db_path(session_id)
            metadata_path = self._get_metadata_path(session_id)
            
            deleted = False
            
            if os.path.exists(db_path):
                os.remove(db_path)
                deleted = True
            
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
                deleted = True
            
            return deleted
        except Exception as e:
            print(f"Error deleting user database: {e}")
            return False

    def has_user_database(self, session_id: str) -> bool:
        """Check if user has an uploaded database"""
        db_path = self._get_user_db_path(session_id)
        return os.path.exists(db_path)


# Singleton instance
_user_db_service: Optional[UserDatabaseService] = None


def get_user_database_service() -> UserDatabaseService:
    """Get or create singleton UserDatabaseService instance"""
    global _user_db_service
    
    if _user_db_service is None:
        _user_db_service = UserDatabaseService()
    
    return _user_db_service
