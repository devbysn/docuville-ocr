# src/api/routes.py
from fastapi import APIRouter, File, UploadFile, HTTPException
from services.document_processor import process_document_image
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class DocumentData(BaseModel):
    documentType: str
    documentNumber: str
    fullName: str
    dateOfIssue: Optional[str]
    dateOfExpiry: Optional[str]
    isValid: bool

@router.post("/process-document/", response_model=DocumentData)
async def process_document(
    file: UploadFile = File(...),
    documentType: str = "pan"
):
    try:
        contents = await file.read()
        print("File contents:")
        if contents is None:
            raise ValueError("No file contents found")
        result = await process_document_image(contents, documentType)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
