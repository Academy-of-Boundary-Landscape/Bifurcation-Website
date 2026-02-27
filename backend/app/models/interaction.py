# app/models/interaction.py
from __future__ import annotations

from datetime import datetime
import enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import event, DDL

from app.models.base import Base


class NotificationType(str, enum.Enum):
    BRANCHED = "branched"      # 你的节点被续写/分支
    LIKED = "liked"            # 被点赞
    COMMENTED = "commented"    # 被评论
    APPROVED = "approved"      # 审核通过
    REJECTED = "rejected"      # 审核驳回


class StoryComment(Base):
    __tablename__ = "story_comments"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 冗余：强烈建议，便于“活动最新评论/后台管理”无需 join 节点表
    book_id: Mapped[int] = mapped_column(
        ForeignKey("story_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    node_id: Mapped[int] = mapped_column(
        ForeignKey("story_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 建议 SET NULL：用户删除/注销后评论仍可保留（显示“已注销”）
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # 软删除（不可编辑评论的情况下，这就是唯一修改路径）
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    deleted_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delete_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # relationships
    user = relationship("User", back_populates="comments", foreign_keys=[user_id])
    node = relationship("StoryNode", back_populates="comments")
    deleter = relationship("User", foreign_keys=[deleted_by])

    __table_args__ = (
        CheckConstraint("length(content) > 0", name="ck_story_comments_content_nonempty"),
        # 节点下最新评论
        Index("ix_story_comments_node_created", "node_id", "created_at"),
        # 活动下最新评论
        Index("ix_story_comments_book_created", "book_id", "created_at"),
        # 常用：过滤未删除
        Index("ix_story_comments_node_not_deleted", "node_id", "deleted_at"),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 冗余：按活动筛选通知 & 运营统计更方便
    book_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("story_books.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # 接收者
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 触发者（系统通知/审核通知允许为空）
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

    # 目标：节点 / 评论（二选一或都为空但 message 有值）
    node_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("story_nodes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    comment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("story_comments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # 附加信息：比如“驳回原因/系统提示/摘要”
    message: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    # 去重键：防刷屏（同类事件覆盖或合并）
    # 例：liked:{sender_id}:{node_id} / commented:{sender_id}:{node_id}
    dedupe_key: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    receiver = relationship("User", back_populates="notifications", foreign_keys=[user_id])
    sender = relationship("User", back_populates="sent_notifications", foreign_keys=[sender_id])
    node = relationship("StoryNode", foreign_keys=[node_id])
    comment = relationship("StoryComment", foreign_keys=[comment_id])

    __table_args__ = (
        CheckConstraint(
            "(node_id IS NOT NULL) OR (comment_id IS NOT NULL) OR (message IS NOT NULL)",
            name="ck_notifications_target_or_message_present",
        ),
        Index("ix_notifications_user_unread", "user_id", "is_read", "created_at"),
        Index("ix_notifications_book_user_created", "book_id", "user_id", "created_at"),
        Index("ix_notifications_user_dedupe", "user_id", "dedupe_key"),
    )
