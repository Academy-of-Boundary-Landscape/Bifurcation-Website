# app/schemas/story_book.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.story_book import BookPhase


class StoryBookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None
    cover_image: Optional[str] = Field(default=None, max_length=255)
    phase: BookPhase = Field(default=BookPhase.DRAFTING)
    start_at: Optional[datetime] = None
    writing_end_at: Optional[datetime] = None
    showcase_end_at: Optional[datetime] = None
    allow_new_nodes: bool = Field(default=True)


class StoryBookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = None
    cover_image: Optional[str] = Field(default=None, max_length=255)
    phase: Optional[BookPhase] = None
    start_at: Optional[datetime] = None
    writing_end_at: Optional[datetime] = None
    showcase_end_at: Optional[datetime] = None
    allow_new_nodes: Optional[bool] = None


class StoryBookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    cover_image: Optional[str] = None

    phase: BookPhase
    start_at: Optional[datetime] = None
    writing_end_at: Optional[datetime] = None
    showcase_end_at: Optional[datetime] = None
    allow_new_nodes: bool

    created_at: datetime


class StoryBookListResponse(BaseModel):
    books: List[StoryBookResponse]
