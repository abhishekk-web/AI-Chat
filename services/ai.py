import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors
from fastapi import HTTPException
from database.connection import conversations, messages, users
from datetime import datetime
from bson import ObjectId
from dependencies.auth import hash_password, verify_password, create_token

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

print("Gemini connected!")

def sign_up_service(data):
    try:

        print("data body is ",data)
        if data.email:
            check_email = users.find_one({"email": data.email})
            if check_email is not None:
                raise HTTPException(
                    status_code=400,
                    detail="Email already exist"
                )
        
        if data.password:
            hashed_password = hash_password(data.password)
            data.password = hashed_password
    
        obj = {
            "name": data.name,
            "email": data.email,
            "password": data.password
        }
    
        create_user = users.insert_one(obj)
    
        print("create user is ",create_user)
        token = create_token(str(create_user.inserted_id))
        print("token checking is ",token)
        get_user = users.find_one({"_id": create_user.inserted_id})
        get_user["_id"] = str(get_user["_id"])        
        return {
            "data": get_user,
            "token": token
        }

    except ValueError as error:
        print(error)

def login_service(data):
    print("body login checking ",data)
    if data.email:
        check_email = users.find_one({"email": data.email})
        if check_email is None:
            raise HTTPException(
                status_code=404,
                detail="email not exist"
            )

    if data.password:
        verifying_password = verify_password(data.password, check_email["password"])
        if verifying_password is False:
            raise HTTPException(
                status_code=400,
                detail="password not matched"
            )

    token = create_token(str(check_email["_id"]))
    return {
        "data": check_email,
        "token": token
    }

def chat_request_service(data):

    try:

        print("chat request body is ",data)

        content = data.question
        if data.conversation_id is not None:

            check_conversation_id = conversations.find_one({"_id": ObjectId(data.conversation_id)})
            if check_conversation_id is None:
                raise HTTPException(
                    status_code=404,
                    detail="conversation id not found"
                )

            conversation_id = ObjectId(data.conversation_id)
            print("conversation_data ",conversation_id)

            message_data = list(messages.find({"conversation_id": ObjectId(data.conversation_id)}, {"_id": 0, "role": 1, "content": 1}))
            print("message data ",message_data)

            content = [
                {
                    "role": message["role"],
                    "parts": [
                        {
                            "text": message["content"]
                        }
                    ]
                }
                for message in message_data
            ]

            print("before print ",content)
            # # Add the new question
            content.append({
                "role": "user",
                "parts": [
                    {
                        "text": data.question
                    }
                ]
            })

            print("after print ",content)

            # content = message_data

        else:
            conversation_data = conversations.insert_one({
                "title": data.question,
                "created_at": datetime.now()
            })
            conversation_id = conversation_data.inserted_id

        # print("content checking is ",content)
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=content
        )

        # print("test ",response.text)


        message_data = messages.insert_many([
            {
                "conversation_id": conversation_id,
                "role": "user",
                "content": data.question,
                "created_at": datetime.now()
            },
            {
                "conversation_id": conversation_id,
                "role": "model",
                "content": response.text,
                "created_at": datetime.now()
            }
        ])

        return {
            "conversation_id": str(conversation_id),
            "answer": response.text
        }

    except errors.ServerError as error:
        print("error checking is ",error)
        raise HTTPException(
            status_code=503,
            detail="AI service temporarily unavailable"
        )

def list_history_service(conversation_id):
    try:

       
        messages_data = list(conversations.aggregate([
            {
                "$match": {
                    "_id": ObjectId(conversation_id)
                }
            },
            {
            "$lookup": {
                "from": "messages",
                "let": {
                    "conversation_id": "$_id"
                },
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$eq": [
                                    "$conversation_id",
                                    "$$conversation_id"
                                ]
                            }
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "role": 1,
                            "content": 1
                        }
                    }
                ],
                "as": "messages"
            }
        },
            # {
            #     "$unwind": {
            #         "path": "$conversation",
            #         "preserveNullAndEmptyArrays": True
            #     }
            # },
            {
                "$project": {
                    "_id": 0,
                    "conversation_id": {
                        "$toString": "$_id"
                    },
                    "messages": 1
                }
            }
            
        ]))
        print("messages data is ",messages_data)
        

        return messages_data

    except ValueError as error:
        print(error)