


from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String,
    Text,
    Boolean,
    DateTime,
    Enum as SAEnum,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class BookPhase(str, enum.Enum):
    DRAFTING = "drafting"   # 内测/筹备（可建根节点，但不对外宣传）
    WRITING = "writing"     # 创作期（允许新增节点/分支）
    SHOWCASE = "showcase"   # 展示/投票期（通常禁止新增，只读 + 投票/评论）
    ARCHIVED = "archived"   # 归档只读（活动结束，作为小说馆展示）


class StoryBook(Base):
    """
    故事集/活动场次
    例如: "分岔视界（第1回）"
    """
    __tablename__ = "story_books"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(120), nullable=False, index=True)  # 活动标题
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)      # 活动简介
    cover_image: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # 封面图URL

    # 活动阶段（替代 is_active）
    phase: Mapped[BookPhase] = mapped_column(
        SAEnum(BookPhase, name="book_phase"),
        default=BookPhase.DRAFTING,
        nullable=False,
        index=True,
    )

    # 时间线（可选，但强烈建议：支撑“21天创作 + 7天展示”）
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    writing_end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    showcase_end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # 运行期开关（应急：临时冻结投稿等）
    allow_new_nodes: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # 关联：一本书包含很多节点
    # 不要 delete-orphan：活动内容是资产，避免误操作导致整棵树被删
    nodes: Mapped[List["StoryNode"]] = relationship(
        "StoryNode",
        back_populates="book",
        cascade="save-update, merge",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_story_books_phase_created", "phase", "created_at"),
        Index("ix_story_books_timeline", "start_at", "writing_end_at", "showcase_end_at"),
    )

    def __repr__(self) -> str:
        return f"<StoryBook {self.id} {self.title} ({self.phase})>"