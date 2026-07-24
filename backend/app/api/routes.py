from fastapi import APIRouter

from app.api.upload import router as upload_router
from app.api.extract import router as extract_router
from app.api.bl_extract import router as bl_router

router = APIRouter()

router.include_router(upload_router)
router.include_router(extract_router)
router.include_router(bl_router)


@router.get("/status")
def api_status():
    return {
        "message": "API Router Working"
    }