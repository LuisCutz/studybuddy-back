from fastapi import APIRouter
from app.api.v1.routes import auth, documents, quizzes, rooms, organizations

api_router = APIRouter()

api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(quizzes.router, prefix="/quizzes", tags=["Quizzes"])