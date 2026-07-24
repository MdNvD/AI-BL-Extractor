from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.file_service import save_uploaded_file
from app.schemas.response import UploadResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    try:
        result = save_uploaded_file(file)

        return UploadResponse(
            success=True,
            message="File uploaded successfully.",
            original_filename=result["original_filename"],
            saved_filename=result["saved_filename"],
            file_size=result["file_size"],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )