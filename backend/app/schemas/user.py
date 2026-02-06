# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole

# 基础模型：读写通用的字段
class UserBase(BaseModel):
    email:  EmailStr = Field(..., description="用户邮箱")
    username: str = Field(..., min_length=2, max_length=50,description="用户名，2-50字符")

class UserEmail(BaseModel):
    email:  EmailStr = Field(..., description="用户邮箱")
# 注册请求：需要密码
class UserCreate(UserBase):
    username: str = Field(..., min_length=2, max_length=50,description="用户名，2-50字符")
    email:  EmailStr = Field(...,min_length=2, max_length=100, description="用户邮箱")
    password: str = Field(..., min_length=6, description="密码至少6位")
class UserCreateResponse(UserBase):
    id: int
    role: UserRole = Field(..., description="用户角色(管理员/写手/小黑屋)")
    is_active: bool = Field(..., description="用户是否激活")
    is_verified: bool = Field(..., description="邮箱验证状态")  
    class Config:
        from_attributes = True # 让 Pydantic 支持读取 ORM 对象

# 登录请求：只需要邮箱密码
class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., description="用户密码")

# 邮箱验证请求, 用来发给后端验证验证码对不对
class EmailVerify(BaseModel):
    email: EmailStr = Field(..., description="用户邮箱")
    code: str = Field(..., description="6位验证码")


# 用户信息响应 (返回给前端的，严禁包含 password)
class UserResponse(UserBase):
    id: int
    role: UserRole = Field(..., description="用户角色(管理员/写手/小黑屋)")
    is_active: bool = Field(..., description="用户是否激活")
    is_verified: bool = Field(..., description="邮箱验证状态")

    class Config:
        from_attributes = True # 让 Pydantic 支持读取 ORM 对象
class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=2, max_length=50)
    bio: str | None = Field(None, max_length=200)
    avatar: str | None = Field(None, description="头像链接")

# --- [修改] 基础响应增加 bio 和 avatar ---
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool
    is_verified: bool
    
    # 新增字段
    bio: str | None
    avatar: str | None

    class Config:
        from_attributes = True

# --- [新增] 详细画像 (带统计数据) ---
class UserProfileResponse(UserResponse):
    nodes_count: int = 0
    likes_count: int = 0

    class Config:
        from_attributes = True
class PasswordReset(BaseModel):
    email: EmailStr = Field(..., description="用户邮箱")
    code: str = Field(..., description="6位验证码")
    new_password: str = Field(..., min_length=6, description="新密码，至少6位")


class UserAdminUpdate(BaseModel):
    role: UserRole | None = None      # 提拔/撤职
    is_active: bool | None = None     # 封禁/解封
    username: str | None = None       # 强制改名 (违规昵称)
    bio: str | None = None            # 强制清空简介
    avatar: str | None = None         # 强制重置头像