from fastapi import FastAPI

from app.api.v1.routes.auth import auth_router
from app.api.v1.routes.rooms import rooms_router

app = FastAPI(title="StudyBuddy API")

app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(rooms_router, prefix="/api/v1/rooms")


@app.get("/")
def health_check():
    return {"status": "ok"}