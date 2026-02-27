from fastapi import APIRouter, UploadFile, File, HTTPException, status, Request
import shutil
import os
import uuid
from typing import List
from app.config import settings

router = APIRouter()

UPLOAD_DIR = "static/uploads"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(request: Request, file: UploadFile = File(...)):
    """
    Upload a file and return its URL.
    """
    try:
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Generate absolute URL with /api prefix for proxy compatibility
        base_url = str(request.base_url).rstrip("/")
        file_url = f"{base_url}/api/static/uploads/{filename}"
        
        return {
            "filename": filename,
            "url": file_url,
            "original_name": file.filename
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
