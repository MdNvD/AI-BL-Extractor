from fastapi import APIRouter, HTTPException
from pathlib import Path

from app.core.config import UPLOAD_DIR
from app.extractor.text_extractor import TextExtractor

router = APIRouter()


@router.get("/extract/{filename}")
def extract_pdf(filename: str):

    pdf_path = UPLOAD_DIR / filename

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="PDF not found."
        )

    extractor = TextExtractor(str(pdf_path))

    return extractor.extract()