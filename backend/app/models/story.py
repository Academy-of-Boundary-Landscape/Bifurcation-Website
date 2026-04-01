from __future__ import annotations
import enum
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Boolean, DateTime, Enum as SAEnum, ForeignKey, Index, Integer,
    String, Text, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref
from sqlalchemy.sql import func

# PostgreSQL JSON / SQLite text: SQLAlchemy JSON 在两者都能用（SQLite会当TEXT存）
from sqlalchemy.types import JSON

from app.models.base import Base


class NodeStatus(str, enum.Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class NodeVisibility(str, enum.Enum):
    PRIVATE = "private"     # 待审/作者自见
    PUBLIC = "public"       # 对外公开
    UNLISTED = "unlisted"   # 直链可见，不进列表


class NodeZone(str, enum.Enum):
    LONG = "long"
    SHORT = "short"


class StoryNode(Base):
    __tablename__ = "story_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)

    book_id: Mapped[int] = mapped_column(
        ForeignKey("story_books.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("story_nodes.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    # 强烈建议：根节点id，加速聚合/热榜/树统计
    root_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # ---- content ----
    title: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    branch_name: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(String(600), nullable=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)

    # ---- lifecycle / visibility ----
    status: Mapped[NodeStatus] = mapped_column(
        SAEnum(NodeStatus, name="node_status"),
        default=NodeStatus.PENDING,
        nullable=False,
        index=True,
    )

    visibility: Mapped[NodeVisibility] = mapped_column(
        SAEnum(NodeVisibility, name="node_visibility"),
        default=NodeVisibility.PRIVATE,
        nullable=False,
        index=True,
    )

    zone: Mapped[NodeZone] = mapped_column(
        SAEnum(NodeZone, name="node_zone"),
        default=NodeZone.SHORT,
        nullable=False,
        index=True,
    )

    # ---- moderation / review audit ----
    reviewed_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    reject_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    archived_reason: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    # ---- behavior flags ----
    is_ending: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    freeze_interactions: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # ---- ops / featuring ----
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    feature_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    # ---- counters ----
    likes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    comments_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    children_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # ---- style ----
    # 用 style_key 管理大部分视觉；style_json 做少量覆盖（管理员写）
    style_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    style_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    style_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # ---- timestamps ----
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True)

    # ---- relationships ----
    book = relationship("StoryBook", back_populates="nodes")
    author = relationship("User", back_populates="nodes", foreign_keys=[author_id])

    # 审核人（可选）
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    children = relationship(
        "StoryNode",
        backref=backref("parent", remote_side=[id]),
        cascade="save-update, merge",
        passive_deletes=False,
    )
    likes = relationship(
        "NodeLike",
        back_populates="node",
        cascade="save-update, merge",
    )
    comments = relationship(
        "StoryComment",
        back_populates="node",
        cascade="save-update, merge",
    )

    __table_args__ = (
        # 常用：某节点下公开子节点
        Index("ix_nodes_parent_public", "book_id", "parent_id", "status", "visibility", "published_at"),
        # 常用：书内最新发布
        Index("ix_nodes_book_latest", "book_id", "status", "visibility", "published_at"),
        # 常用：书内热门
        Index("ix_nodes_book_hot", "book_id", "status", "visibility", "likes_count"),
        # 常用：树内聚合/热榜
        Index("ix_nodes_root_hot", "root_id", "status", "visibility", "likes_count"),
    )


class NodeLike(Base):
    __tablename__ = "node_likes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_id: Mapped[int] = mapped_column(
        ForeignKey("story_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user = relationship("User", back_populates="likes")
    node = relationship("StoryNode", back_populates="likes")

    __table_args__ = (
        UniqueConstraint("user_id", "node_id", name="uq_node_likes_user_node"),
        Index("ix_node_likes_node_created", "node_id", "created_at"),
    )
