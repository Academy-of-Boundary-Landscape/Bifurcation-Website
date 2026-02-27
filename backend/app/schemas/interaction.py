# app/schemas/interaction.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.story import AuthorInfo


# --- 点赞响应 ---
class LikeToggleResponse(BaseModel):
    status: str   # "success"
    action: str   # "liked" 或 "unliked"
    likes_count: int


# --- 评论请求 ---
class CommentCreate(BaseModel):
    content: str


# --- 评论响应 ---
class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    node_id: int
    book_id: int
    content: str
    created_at: datetime
    deleted_at: Optional[datetime] = None
    user: Optional[AuthorInfo] = None  # 用户注销后为 None，前端显示"已注销"


# --- 通知响应 ---
class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str                          # liked / commented / branched / approved / rejected
    sender: Optional[AuthorInfo] = None  # 系统/审核通知时可为 None
    node_id: Optional[int] = None      # 关联节点 ID（跳转用）
    comment_id: Optional[int] = None   # 关联评论 ID（跳转用）
    message: Optional[str] = None      # 附加文案（驳回原因/系统提示）
    is_read: bool
    created_at: datetime


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int
