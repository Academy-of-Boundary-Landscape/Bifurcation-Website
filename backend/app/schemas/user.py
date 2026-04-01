# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole

class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50)
    bio: str | None = Field(None, max_length=200)
    avatar: str | None = Field(None, description="头像链接")

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    display_name: str | None = None
    role: UserRole
    is_active: bool
    is_verified: bool
    
    # 新增字段
    bio: str | None
    avatar: str | None

    class Config:
        from_attributes = True

class UserProfileResponse(UserResponse):
    nodes_count: int = 0
    likes_count: int = 0

    class Config:
        from_attributes = True

class UserAdminUpdate(BaseModel):
    role: UserRole | None = None      # 提拔/撤职
    is_active: bool | None = None     # 封禁/解封
    username: str | None = Field(None, min_length=3, max_length=50)  # 强制改名 (违规昵称)
    bio: str | None = None            # 强制清空简介
    avatar: str | None = None         # 强制重置头像
