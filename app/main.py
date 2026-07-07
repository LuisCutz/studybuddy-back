from fastapi import FastAPI
from app.api.v1.api import api_router

app = FastAPI(title="StudyBuddy API")

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def health_check():
    return {"status": "ok", "version": "1.0.0"}