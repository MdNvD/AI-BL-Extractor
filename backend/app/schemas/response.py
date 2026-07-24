from pydantic import BaseModel


class UploadResponse(BaseModel):
    success: bool
    message: str
    original_filename: str
    saved_filename: str
    file_size: int