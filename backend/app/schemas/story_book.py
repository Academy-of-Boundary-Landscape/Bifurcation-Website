# app/schemas/story_book.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class StoryBookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    cover_image: Optional[str] = Field(default=None, max_length=255)
class StoryBookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    cover_image: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None
class StoryBookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    cover_image: Optional[str] = None

    is_active: bool
    created_at: datetime


class StoryBookListResponse(BaseModel):
    books: List[StoryBookResponse]
