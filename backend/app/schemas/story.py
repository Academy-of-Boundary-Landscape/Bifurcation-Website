# app/schemas/story.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.story import NodeStatus, NodeVisibility, NodeZone


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
    title: Optional[str] = Field(default=None, max_length=120)
    content: str = Field(..., min_length=10)
    branch_name: Optional[str] = Field(default=None, max_length=80)
    summary: Optional[str] = Field(default=None, max_length=600)
    zone: NodeZone = Field(default=NodeZone.SHORT)


class NodeUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=120)
    content: Optional[str] = Field(default=None, min_length=10)
    branch_name: Optional[str] = Field(default=None, max_length=80)
    summary: Optional[str] = Field(default=None, max_length=600)


class StoryNodeListItem(BaseModel):
    """用于列表展示（feed/search/user-nodes），不含 children，不含 content。"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: Optional[int] = None
    root_id: int
    book_id: int

    author: AuthorInfo

    title: Optional[str] = None
    summary: Optional[str] = None
    branch_name: Optional[str] = None

    status: NodeStatus
    visibility: NodeVisibility
    zone: NodeZone

    word_count: int
    likes_count: int
    comments_count: int
    children_count: int

    is_ending: bool
    is_featured: bool

    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class StoryNodeRead(StoryNodeListItem):
    """用于详情页，包含正文和审核相关字段。"""
    content: str
    reject_reason: Optional[str] = None
    archived_reason: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class StoryNodeTreeItem(StoryNodeListItem):
    """专门用于 /tree，包含 children（递归）。"""
    children: List["StoryNodeTreeItem"] = Field(default_factory=list)


class NodeAuditRequest(BaseModel):
    """管理员审核节点请求体。"""
    status: NodeStatus = Field(..., description="新的节点状态（published / archived）")
    reject_reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="驳回/归档原因（status=archived 时建议填写）",
    )
