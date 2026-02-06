from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
import enum
from sqlalchemy import Enum as SAEnum
from datetime import datetime
from sqlalchemy.sql import func
# 导入Datetime用于时间字段
from sqlalchemy import DateTime
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    WRITER = "writer"
    BANNED = "banned"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50),unique=True,index=True,nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    

    # 简介
    bio: Mapped[str | None] = mapped_column(String(200), nullable=True) 
    # 头像URL，允许为空
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True) 


    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role"), default=UserRole.WRITER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # 时间节点
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),nullable=False,index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True)
    # 关联 (保持不变)
    nodes = relationship("StoryNode", back_populates="author")
    likes = relationship("NodeLike", back_populates="user")

    # 我和其他人的互动
    # 用户发的评论
    comments = relationship("StoryComment", back_populates="user", cascade="save-update, merge")

    # 我收到的通知
    notifications = relationship(
        "Notification",
        back_populates="receiver",
        foreign_keys="[Notification.user_id]",
        cascade="save-update, merge",
    )

# 我发出的通知（我点赞/评论/续写触发的）
    sent_notifications = relationship(
        "Notification",
        back_populates="sender",
        foreign_keys="[Notification.sender_id]",
        cascade="save-update, merge",
    )

    def __repr__(self):
        return f"<User {self.username}>"