# app/main.py
from fastapi import FastAPI
from app.routers import chat

app = FastAPI(
    title="STAN Conversational AI Backend",
    description="Human-like chatbot backend with memory & context",
    version="1.0"
)

app.include_router(chat.router)

@app.get("/")
def root():
    return {"message": "STAN backend is running 🚀"}
