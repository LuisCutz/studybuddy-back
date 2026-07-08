from fastapi import APIRouter
from app.api.v1.routes import documents
from app.api.v1.routes import auth

api_router = APIRouter()

api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])