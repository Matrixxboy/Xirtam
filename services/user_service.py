from database.models import User
from datetime import datetime, timedelta
import asyncio

class UserService:
    async def get_user(self, user_id: int) -> User:
        """Get user by ID, create if not exists."""
        user = await User.get(user_id)
        if not user:
            user = User(id=user_id)
            await user.create()
        return user

    async def update_balance(self, user_id: int, amount: int) -> User:
        """Update user balance safely."""
        user = await self.get_user(user_id)
        user.balance += amount
        await user.save()
        return user

    async def update_inventory(self, user_id: int, item: str, count: int = 1) -> User:
        """Update inventory items."""
        user = await self.get_user(user_id)
        current_count = user.inventory.get(item, 0)
        user.inventory[item] = current_count + count
        await user.save()
        return user

    async def can_claim_daily(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        if not user.last_daily:
            return True
        return (datetime.utcnow() - user.last_daily) >= timedelta(days=1)

    async def claim_daily(self, user_id: int, amount: int) -> int:
        user = await self.get_user(user_id)
        user.balance += amount
        user.last_daily = datetime.utcnow()
        await user.save()
        return user.balance

    async def can_work(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        if not user.last_work:
            return True
        return (datetime.utcnow() - user.last_work) >= timedelta(hours=2)

    async def work(self, user_id: int, amount: int):
        user = await self.get_user(user_id)
        user.balance += amount
        user.last_work = datetime.utcnow()
        await user.save()
        return user.balance

    async def get_top_users(self, limit: int = 10):
        # Beanie find with sort and limit
        return await User.find_all().sort("-balance").limit(limit).to_list()

user_service = UserService()
