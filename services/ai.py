import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors
from fastapi import HTTPException
from database.connection import conversations, messages, users
from datetime import datetime
from bson import ObjectId
from dependencies.auth import hash_password, verify_password, create_token
from fastapi.responses import StreamingResponse

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
            "password": data.password,
            "created_at": datetime.now(),
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

def chat_request_service(data, user_data):

    try:

        print("chat request body is ",data)
        print("user data is ",user_data)

        content = data.question
        if data.conversation_id is not None:

            check_conversation_id = conversations.find_one({"_id": ObjectId(data.conversation_id), "user_id": ObjectId(user_data["_id"])})
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
                "created_at": datetime.now(),
                "user_id": user_data["_id"]
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
                "user_id": user_data["_id"],
                "role": "user",
                "content": data.question,
                "created_at": datetime.now()
            },
            {
                "conversation_id": conversation_id,
                "user_id": user_data["_id"],
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

def list_history_service_by_id(conversation_id, user_data):
    try:

        messages_data = list(conversations.aggregate([
            {
                "$match": {
                    "_id": ObjectId(conversation_id),
                    "user_id": ObjectId(user_data["_id"])
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

def list_history_service(user_data):
    try:
        conversation_data = list(
            conversations.aggregate([
                {
                    "$match": {
                        "user_id": user_data["_id"]
                    }
                }
            ])
        )

        print("conversation data is  ",conversation_data)

        for conversation in conversation_data:
            # print("conversation is ",conversation)
            conversation["_id"] = str(conversation["_id"])
            conversation["user_id"] = str(conversation["user_id"])

 
        return conversation_data

    except ValueError as error:
        print(error)


def delete_history_service(conversation_id, user_data):
    try:

        conversation_data = conversations.find_one({"_id": ObjectId(conversation_id), "user_id": ObjectId(user_data._id)})
        if conversation_data is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation id not exist"
            )
        
        conversation_list =  conversations.delete_one({"_id": ObjectId(conversation_id), "user_id": ObjectId(user_data["_id"])})
        messages_list =messages.delete_many({"conversation_id": ObjectId(conversation_id), "user_id": ObjectId(user_data["_id"])})
        # print("messages data is ",messages_data)
        if conversation_list.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        if messages_list.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return "Chat has been successfully deleted"

    except ValueError as error:
        print(error)


def chat_stream_service(data, user_data):
    try:
        print("user_data ",user_data)
        print("data checking is ",data)

        content = data.question
        if data and data.conversation_id is not None:

            conversation_id = ObjectId(data.conversation_id)
            conversation_data = conversations.find_one({"_id": ObjectId(data.conversation_id)})
            if conversation_data is None:
                raise HTTPException(
                    status_code=404,
                    detail="conversation not exist"
                )

            messages_data = messages.find({"conversation_id": ObjectId(data.conversation_id)}).sort("created_at", 1)
            
            content = [
                {
                    "role": messages["role"],
                    "parts": [
                        {
                            "text": messages["content"]
                        }
                    ]
                }
                for messages in messages_data   
            ] 

            content.append({
                "role": "user",
                "parts": [
                    {
                        "text": data.question
                    }
                ]
            })

        else: 
            conversation_data = conversations.insert_one({
                "title": data.question,
                "created_at": datetime.now(),
                "user_id": user_data["_id"]
            })
            conversation_id = conversation_data.inserted_id

        response = client.models.generate_content_stream(
            model="gemini-3.5-flash-lite",
            contents=content
        )

        try:
            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    yield chunk.text
        except errors.ServerError:
            raise HTTPException(
                status_code=503,
                detail="Ai service temporarily unavailable"
            )
            

        messages.insert_many([
            {
                "conversation_id": conversation_id,
                "user_id": user_data["_id"],
                "role": "user",
                "content": data.question,
                "created_at": datetime.now()
            },
            {
                "conversation_id": conversation_id,
                "user_id": user_data["_id"],
                "role": "model",
                "content": full_response,
                "created_at": datetime.now()
            }
        ])

        

        # return response.text

    except errors.ServerError as error:
        print("error checking is ",error)
        raise HTTPException(
            status_code=503,
            detail="AI service temporarily unavailable"
        )