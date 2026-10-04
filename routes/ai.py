from fastapi import APIRouter
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from services.ai import chat_request_service, list_history_service

router = APIRouter()

class chatRequest (BaseModel):
    conversation_id: Optional[str] = None
    question: str = Field(..., min_length=1)
    @field_validator("question")
    @classmethod
    def validate_question(cls, value):
        if not value.strip():
            raise ValueError("Question cannot be empty") 
        return value

@router.post("/ai/chat")
def chat(chatRequest: chatRequest):
    return chat_request_service(chatRequest)

@router.get("/list_history/{conversation_id}")
def list_history(conversation_id):
    return list_history_service(conversation_id)