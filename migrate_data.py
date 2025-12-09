import json
import asyncio
import os
import datetime
from database.connection import init_db
from database.models import User

DATA_FILE = "e:/Utsav/Personal Projects/Xirtam/data/economy.json"

async def migrate():
    if not os.path.exists(DATA_FILE):
        print(f"Data file not found: {DATA_FILE}")
        return

    print("Starting MongoDB migration...")
    await init_db()

    with open(DATA_FILE, 'r') as f:
        data = json.load(f)

    for user_id_str, user_data in data.items():
        user_id = int(user_id_str)
        balance = user_data.get("balance", 0)
        inventory = user_data.get("inventory", {})
        
        # Create user or get existing
        user = await User.get(user_id)
        if not user:
            user = User(id=user_id)
            await user.create()

        user.balance = balance
        # Ensure inventory is Dict[str, int]
        user.inventory = {k: int(v) for k,v in inventory.items()}
        
        if user_data.get("last_daily"):
            try:
                user.last_daily = datetime.datetime.fromisoformat(user_data["last_daily"])
            except:
                pass
        
        if user_data.get("last_work"):
            try:
                user.last_work = datetime.datetime.fromisoformat(user_data["last_work"])
            except:
                pass
        
        await user.save()
        print(f"Migrated User: {user_id} | Balance: {balance}")
    
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
