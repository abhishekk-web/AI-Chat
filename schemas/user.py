from pydantic import BaseModel, Field, field_validator, EmailStr

class user_data(BaseModel):
    name: str
    email: EmailStr

class signup_response(BaseModel):
    data: user_data
    token: str