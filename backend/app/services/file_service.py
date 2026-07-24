import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.core.config import UPLOAD_DIR


ALLOWED_EXTENSIONS = [".pdf"]


def save_uploaded_file(file: UploadFile):

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Only PDF files are allowed.")

    unique_filename = f"{uuid.uuid4()}{extension}"

    save_path = UPLOAD_DIR / unique_filename

    with save_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = save_path.stat().st_size

    return {
        "original_filename": file.filename,
        "saved_filename": unique_filename,
        "file_size": file_size,
        "file_path": str(save_path)
    }