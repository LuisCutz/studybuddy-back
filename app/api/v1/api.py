from fastapi import APIRouter
from app.api.v1.routes import auth, chat, documents, quizzes, organizations, flashcards, progress

api_router = APIRouter()

api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(quizzes.router, prefix="/quizzes", tags=["Quizzes"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(flashcards.router, prefix="/flashcards", tags=["Flashcards"])
api_router.include_router(progress.router, prefix="/progress", tags=["Progress"])