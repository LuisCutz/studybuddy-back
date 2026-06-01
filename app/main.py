from fastapi import FastAPI

app = FastAPI(title="StudyBuddy API")

@app.get("/")
def health_check():
    return {"status": "ok"}