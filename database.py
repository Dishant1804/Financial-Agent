import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models.user import User
from models.conversation import Conversation

class Database:
    client: AsyncIOMotorClient = None
    
database = Database()

async def connect_to_mongo():
    """Create database connection"""
    database.client = AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    await init_beanie(
        database=database.client.finvest_analysis,
        document_models=[User, Conversation]
    )

async def close_mongo_connection():
    """Close database connection"""
    database.client.close()
