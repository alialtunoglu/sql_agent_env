"""
File Upload Endpoints
Handles user data uploads (CSV/Excel) and database management
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.user_database import get_user_database_service

router = APIRouter()


class UploadResponse(BaseModel):
    """Response model for file upload"""
    success: bool
    message: str
    table_name: Optional[str] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    columns: Optional[list] = None


class DatabaseStatusResponse(BaseModel):
    """Response model for database status check"""
    has_database: bool
    metadata: Optional[dict] = None


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = None
):
    """
    Upload CSV or Excel file and convert to SQLite database.
    
    Args:
        file: CSV or Excel file
        session_id: User session identifier
    
    Returns:
        UploadResponse with success status and metadata
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id gerekli")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Dosya adı bulunamadı")
    
    # Validate file type
    allowed_extensions = ['.csv', '.xlsx', '.xls']
    file_ext = file.filename.lower().split('.')[-1]
    
    if f'.{file_ext}' not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen dosya formatı. İzin verilen formatlar: {', '.join(allowed_extensions)}"
        )
    
    # Process upload
    service = get_user_database_service()
    success, message, metadata = await service.process_upload(file, session_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Return success response with metadata
    return UploadResponse(
        success=True,
        message=message,
        table_name=metadata.get('table_name'),
        row_count=metadata.get('row_count'),
        column_count=metadata.get('column_count'),
        columns=list(metadata.get('columns', {}).keys())
    )


@router.get("/database-status", response_model=DatabaseStatusResponse)
async def get_database_status(session_id: str):
    """
    Check if user has an uploaded database and return metadata.
    
    Args:
        session_id: User session identifier
    
    Returns:
        DatabaseStatusResponse with database status
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id gerekli")
    
    service = get_user_database_service()
    has_db = service.has_user_database(session_id)
    
    metadata = None
    if has_db:
        metadata = service.get_user_metadata(session_id)
    
    return DatabaseStatusResponse(
        has_database=has_db,
        metadata=metadata
    )


@router.delete("/database")
async def delete_database(session_id: str):
    """
    Delete user's uploaded database.
    
    Args:
        session_id: User session identifier
    
    Returns:
        Success message
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id gerekli")
    
    service = get_user_database_service()
    success = service.delete_user_database(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Veritabanı bulunamadı")
    
    return {"message": "Veritabanı başarıyla silindi"}
