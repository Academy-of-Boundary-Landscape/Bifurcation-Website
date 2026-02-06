# app/schemas/interaction.py
from datetime import datetime
from pydantic import BaseModel
from app.schemas.story import AuthorInfo 

# --- 点赞响应 ---
class LikeToggleResponse(BaseModel):
    status: str # "success"
    action: str # "liked" 或 "unliked"
    likes_count: int
# 评论请求
class CommentCreate(BaseModel):
    content: str

# 评论响应
class CommentResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    user: AuthorInfo # 这样前端能直接拿到评论者的头像和名字
    
    class Config:
        from_attributes = True

# 通知响应
class NotificationResponse(BaseModel):
    id: int
    type: str # liked / commented / branched / Other
    sender: AuthorInfo # 谁触发的
    target_id: int # 跳转链接用
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True