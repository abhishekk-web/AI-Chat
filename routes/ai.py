from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator
from services.ai import chat_request_service

router = APIRouter()

class chatRequest (BaseModel):
    question: str = Field(..., min_length=1)
    @field_validator("question")
    @classmethod
    def validate_question(cls, value):
        if not value.strip():
            raise ValueError("Question cannot be empty") 
        return value

@router.post("/ai/chat")
def chat(chatRequest: chatRequest):
    print("chat request is ",chatRequest)
    return chat_request_service(chatRequest)
    # return {
    #     "message": "AI chat endpoint"
    # }