from fastapi import APIRouter
from typing import Optional
from pydantic import BaseModel, Field, field_validator, EmailStr
from services.ai import chat_request_service, list_history_service, sign_up_service, login_service
from schemas.user import signup_response


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

class signuprequest(BaseModel):
    name: str = Field(...),
    email: EmailStr = Field(...),
    password: str = Field(..., min_length=8)
    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if not any(char.isupper() for char in value):
            raise ValueError("Password should contain one upper letter")
        if not any(char.islower() for char in value):
                    raise ValueError("Password should contain one lower letter")
        if not any(char.isdigit() for char in value):
                    raise ValueError("Password should contain one number")
        if not any(char in "!@#$%^&*()_+-=" for char in value):
                        raise ValueError("Password should contain one special character")
        return value

class loginrequest(BaseModel):
      email: str = Field(...)
      password: str = Field(...)

@router.post("/signup", response_model=signup_response)
def sign_up(data: signuprequest):
    #    print("data here checking ",data)
       return sign_up_service(data)

@router.post("/login", response_model=signup_response)
def login(data: loginrequest):
    return login_service(data)

@router.post("/ai/chat")
def chat(chatRequest: chatRequest):
    return chat_request_service(chatRequest)

@router.get("/list_history/{conversation_id}")
def list_history(conversation_id):
    return list_history_service(conversation_id)