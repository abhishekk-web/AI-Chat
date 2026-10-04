from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel, Field, field_validator, EmailStr
from services.ai import chat_request_service, list_history_service, sign_up_service, login_service, list_history_service_by_id, delete_history_service, chat_stream_service
from schemas.user import signup_response
from dependencies.auth import get_current_user
from fastapi.responses import StreamingResponse


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

class stream_all_data(BaseModel):
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
def chat(chatRequest: chatRequest, currentUser = Depends(get_current_user)):
    return chat_request_service(chatRequest, currentUser)

@router.get("/list_history_by_id/{conversation_id}")
def list_history_by_id(conversation_id, currentUser = Depends(get_current_user)):
    return list_history_service_by_id(conversation_id, currentUser)

@router.delete("/delete_history/{conversation_id}")
def delete_history(conversation_id, currentUser = Depends(get_current_user)):
    return delete_history_service(conversation_id, currentUser)

@router.get("/list_history")
def list_history(currentUser = Depends(get_current_user)):
    return list_history_service(currentUser)


@router.post("/ai/chat/stream")
def chat_stream(data: stream_all_data, currentUser = Depends(get_current_user)):
    return StreamingResponse(
        chat_stream_service(data, currentUser),
        media_type="text/plain"
    )