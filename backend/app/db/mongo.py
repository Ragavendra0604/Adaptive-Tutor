from pymongo import MongoClient
from .schemas import *
from ..core.config import settings

client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB]

# ensure indexes
db.knowledge_documents.create_index([("title","text"),("text","text")], name="text_idx")
db.chats.create_index([("user_id",1)])
db.question_bank.create_index([("concept",1),("difficulty",1)])
