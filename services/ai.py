import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors
from fastapi import HTTPException

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

print("Gemini connected!")

def chat_request_service(data):

    try:

        print("chat request body is ",data.question)
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=data.question
        )

        return {
            "answer": response.text
        }

    except errors.ServerError as error:
        raise HTTPException(
            status_code=503,
            detail="AI service temporarily unavailable"
        )