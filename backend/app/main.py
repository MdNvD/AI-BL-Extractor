from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import APP_NAME, APP_VERSION
from app.api.routes import router

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="AI-powered Bill of Lading Extraction API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # We'll restrict this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(router, prefix="/api", tags=["API"])


@app.get("/")
def root():
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "status": "Running",
    }


@app.get("/health")
def health():
    return {
        "status": "Healthy",
        "service": APP_NAME,
    }