from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String, Boolean, DateTime, Enum as SAEnum, Integer, CheckConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    WRITER = "writer"
    BANNED = "banned"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 登录标识
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # 展示信息
    display_name: Mapped[Optional[str]] = mapped_column(String(60), nullable=True, index=True)
    bio: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 认证与权限
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"),
        default=UserRole.WRITER,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # 密码（如果你确定永远账号密码：nullable=False OK）
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # 封禁（从 role 拆出，便于细粒度控制）
    banned_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    ban_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # 运营/反作弊（可选但很有用）
    trust_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )

    # 关系
    nodes: Mapped[List["StoryNode"]] = relationship(
        "StoryNode",
        back_populates="author",
        cascade="save-update, merge",
    )

    likes: Mapped[List["NodeLike"]] = relationship(
        "NodeLike",
        back_populates="user",
        cascade="save-update, merge",
    )

    comments: Mapped[List["StoryComment"]] = relationship(
        "StoryComment",
        back_populates="user",
        cascade="save-update, merge",
    )

    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="receiver",
        foreign_keys="Notification.user_id",
        cascade="save-update, merge",
    )

    sent_notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="sender",
        foreign_keys="Notification.sender_id",
        cascade="save-update, merge",
    )

    __table_args__ = (
        # 最低限度的用户名长度约束（更复杂的规则建议在 API 层校验）
        CheckConstraint("length(username) >= 3", name="ck_users_username_len"),
        # 常用查询：活跃且未封禁用户（后台管理）
        Index("ix_users_active_role", "is_active", "role"),
    )

    def is_banned(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.utcnow()
        return self.banned_until is not None and self.banned_until > now

    def __repr__(self) -> str:
        return f"<User {self.id} {self.username}>"
