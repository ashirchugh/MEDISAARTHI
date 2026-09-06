from fastapi import FastAPI, Depends, status, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.db.database import get_db
from backend.app.api import api_router

# Initialize logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API service for Medisaarthi — AI-powered hospital pre-consultation platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"], summary="System & PostgreSQL Health Check")
def health_check(response: Response, db: Session = Depends(get_db)):
    """Check application status and verify active PostgreSQL database connectivity."""
    try:
        # Execute active query to test database connectivity
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "connected",
        }
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "error",
            "database": "disconnected",
            "detail": str(e),
        }


# Mount API routers at root as specified in the interface requirements
app.include_router(api_router)
# Also mount under API_V1_STR for versioned clients
app.include_router(api_router, prefix=settings.API_V1_STR)
