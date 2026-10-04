import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors
from fastapi import HTTPException
from database.connection import conversations, messages
from datetime import datetime
from bson import ObjectId

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

print("Gemini connected!")

def chat_request_service(data):

    try:

        print("chat request body is ",data)

        content = data.question
        if data.conversation_id is not None:

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