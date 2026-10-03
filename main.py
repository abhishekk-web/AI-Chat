from fastapi import FastAPI
from routes.ai import router as ai_router

app = FastAPI()

app.include_router(ai_router)


@app.get("/")
def home():
    return {
        "message": "AI Backend is running"
    }