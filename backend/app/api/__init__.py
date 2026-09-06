from fastapi import APIRouter
from backend.app.api.patients import router as patients_router
from backend.app.api.interviews import router as interviews_router
from backend.app.api.doctors import router as doctors_router
from backend.app.api.clinical import router as clinical_router

api_router = APIRouter()
api_router.include_router(patients_router)
api_router.include_router(interviews_router)
api_router.include_router(doctors_router)
api_router.include_router(clinical_router)
