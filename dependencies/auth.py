

from config import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from passlib.context import CryptContext
from bson import ObjectId
from fastapi import HTTPException, Depends
from database.connection import users
from fastapi.security import HTTPBearer
security = HTTPBearer()

def get_current_user(credentials = Depends(security)):
    print("credentials is ",credentials.credentials)
    get_user_data = verify_token(credentials.credentials)
    print("get_user_data ",get_user_data)
    user_data = users.find_one({"_id": ObjectId(get_user_data["user_id"])})
    print("user data is 145 ",user_data)
    if user_data is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user_data


def create_token(user_id):
    print("user id is ",ObjectId(user_id))
    print("algorithm is ",ALGORITHM)
    print("secret key is ",SECRET_KEY)
    return jwt.encode(
        {"user_id": user_id},
        SECRET_KEY,
        algorithm=ALGORITHM

    )

def verify_token(token):
    try:
        print("token while verifying ",token)
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="User not authorized"
        )

def hash_password(password):
    print("password checking is ",password)
    print("password:", repr(password))
    print("type:", type(password))
    print("characters:", len(password))
    print("bytes:", len(password.encode("utf-8")))
    pwd_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto"
    )
    hashpassword = pwd_context.hash(password)
    print("hash password is ",hashpassword)
    return hashpassword

def verify_password(password, hash_password):
    pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto"
        )
    return pwd_context.verify(password, hash_password)