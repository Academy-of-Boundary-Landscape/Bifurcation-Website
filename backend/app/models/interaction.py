# app/models/interaction.py
from __future__ import annotations

from datetime import datetime
import enum
from typing import Optional, List

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Text,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class NotificationType(str, enum.Enum):
    BRANCHED = "branched"      # 被续写
    LIKED = "liked"            # 被点赞
    COMMENTED = "commented"    # 被评论
    APPROVED = "approved"      # 审核通过
    REJECTED = "rejected"      # 审核驳回


class StoryComment(Base):
    __tablename__ = "story_comments"

    id: Mapped[int] = mapped_column(primary_key=True)

    node_id: Mapped[int] = mapped_column(
        ForeignKey("story_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # 可选：软删除（更安全，避免误删引发 404）
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # 关系（建议都写 back_populates，后续好维护）
    user = relationship("User", back_populates="comments")
    node = relationship("StoryNode", back_populates="comments")

    __table_args__ = (
        # 防止空评论（你也可以在 schema 层限制 min_length）
        CheckConstraint("length(content) > 0", name="ck_story_comments_content_nonempty"),
        # 常见查询：按 node 看最新评论
        Index("ix_story_comments_node_created_at", "node_id", "created_at"),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 接收者
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 触发者（允许为空：系统通知/审核通知）
    sender_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType, name="notification_type"),
        nullable=False,
        index=True,
    )

    # 主要目标：故事节点（绝大多数通知都能指向 node）
    node_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("story_nodes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # 可选目标：评论（只有 COMMENTED 类型或某些扩展类型会填）
    comment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("story_comments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # 关系：多外键指向 User 时一定要写 foreign_keys
    receiver = relationship("User", back_populates="notifications", foreign_keys=[user_id])
    sender = relationship("User", back_populates="sent_notifications", foreign_keys=[sender_id])

    node = relationship("StoryNode", foreign_keys=[node_id])
    comment = relationship("StoryComment", foreign_keys=[comment_id])

    __table_args__ = (
        # 通知必须能定位到一个目标（至少 node_id 或 comment_id 其一）
        CheckConstraint(
            "(node_id IS NOT NULL) OR (comment_id IS NOT NULL)",
            name="ck_notifications_target_present",
        ),
        # 常见查询：我的未读通知列表
        Index("ix_notifications_user_isread_created", "user_id", "is_read", "created_at"),
    )
