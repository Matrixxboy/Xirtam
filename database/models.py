from typing import List, Optional, Dict, Any
from beanie import Document
from pydantic import BaseModel, Field
from datetime import datetime

class User(Document):
    id: int = Field(alias="_id") # Discord IDs are integers
    balance: int = 0
    inventory: Dict[str, int] = {}
    last_daily: Optional[datetime] = None
    last_work: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"

class Guild(Document):
    id: int = Field(alias="_id")
    config: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "guilds"

class ModCase(Document):
    case_id: int
    guild_id: int
    user_id: int
    moderator_id: int
    action: str
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "mod_cases"

class Giveaway(Document):
    message_id: int = Field(alias="_id")
    channel_id: int
    guild_id: int
    prize: str
    end_time: datetime
    winners_count: int
    status: str = "active"
    participants: List[int] = []

    class Settings:
        name = "giveaways"

class Task(BaseModel):
    id: int
    description: str
    completed: bool = False
    completed_by: Optional[int] = None

class Project(Document):
    name: str
    guild_id: int
    description: Optional[str] = None
    status: str = "In Progress"
    channel_id: int
    role_id: int
    archived: bool = False
    tasks: List[Task] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "projects"
