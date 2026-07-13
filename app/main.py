from fastapi import FastAPI
from app.api.v1.api import api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="StudyBuddy API")

app.include_router(api_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {
        "status": "ok",
        "module": "StudyBuddy API",
        "version": "1.0.0",
        "visibility": "public",
        "requires_jwt": False,
        "documentation": {
            "swagger_url": "/docs",
            "openapi_json_url": "/openapi.json",
        },
    }