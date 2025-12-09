import os
import motor.motor_asyncio
from beanie import init_beanie
from .models import User, Guild, ModCase, Giveaway, Project

async def init_db():
    # Use MONGO_URI from env, default to local if not set
    # For local dev without env, you might want a default, but print warning
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("MONGO_URI not found in env. Defaulting to local mongodb://localhost:27017")
        mongo_uri = "mongodb://localhost:27017"

    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
    db = client.xirtam_bot  # Database name
    
    await init_beanie(database=db, document_models=[User, Guild, ModCase, Giveaway, Project])
    print(f"✅ Connected to MongoDB: {db.name}")

