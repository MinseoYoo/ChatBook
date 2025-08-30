from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nickname: str
    likes: Optional[str] = None
    dislikes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    state: str
    narrative: Optional[str] = None
    constraints_json: Optional[str] = None
    negatives_json: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)

class BookCache(SQLModel, table=True):
    aladin_id: int = Field(primary_key=True)
    title: str
    author: Optional[str] = None
    category: Optional[str] = None
    pubdate: Optional[str] = None
    price: Optional[int] = None
    description: Optional[str] = None
    cover: Optional[str] = None
    rating: Optional[float] = 0.0
    popularity: Optional[int] = 0
    embedding: Optional[bytes] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
