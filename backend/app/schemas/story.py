# app/schemas/story.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.story import NodeStatus


class MessageResponse(BaseModel):
    detail: str


class AuthorInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    avatar: Optional[str] = None


class StoryNodeCreate(BaseModel):
    book_id: int = Field(..., ge=1)
    parent_id: Optional[int] = Field(default=None, ge=1)
    title: Optional[str] = Field(default=None, max_length=100)
    content: str = Field(..., min_length=10)
    branch_name: Optional[str] = Field(default=None, max_length=50)


class NodeUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=100)
    content: Optional[str] = Field(default=None, min_length=10)
    branch_name: Optional[str] = Field(default=None, max_length=50)


class StoryNodeListItem(BaseModel):
    """用于列表展示（feed/search/user-nodes），不含 children，不含 content。"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: Optional[int] = None
    book_id: int

    author: AuthorInfo

    title: Optional[str] = None
    summary: Optional[str] = None
    branch_name: Optional[str] = None

    status: NodeStatus
    depth: int
    likes_count: int

    created_at: datetime


class StoryNodeRead(StoryNodeListItem):
    """用于详情页，包含正文，但仍不含 children。"""
    content: str


class StoryNodeTreeItem(StoryNodeListItem):
    """专门用于 /tree，包含 children（递归）。"""
    children: List["StoryNodeTreeItem"] = Field(default_factory=list)


class NodeAuditRequest(BaseModel):
    status: NodeStatus = Field(..., description="新的节点状态")