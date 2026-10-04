from pymongo import MongoClient


client = MongoClient("mongodb://localhost:27017/")
db = client["chat_bot"]
conversations = db["conversations"]
messages = db["messages"]

print(client.admin.command("ping"))