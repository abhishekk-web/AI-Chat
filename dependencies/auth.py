

from config import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from passlib.context import CryptContext
from bson import ObjectId

def create_token(user_id):
    print("user id is ",ObjectId(user_id))
    print("algorithm is ",ALGORITHM)
    print("secret key is ",SECRET_KEY)
    return jwt.encode(
        {"user_id": user_id},
        SECRET_KEY,
        algorithm=ALGORITHM

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