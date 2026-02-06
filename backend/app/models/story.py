from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref
from app.models.base import Base
import enum

from sqlalchemy import Enum as SAEnum

from sqlalchemy.sql import func
from sqlalchemy import DateTime

class NodeStatus(str, enum.Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    LOCKED = "locked"
    REJECTED = "rejected"

# 点赞关联表 (多对多: 用户 <-> 节点)
class NodeLike(Base):
    __tablename__ = "node_likes"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("story_nodes.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # 关联方便查询
    user = relationship("User", back_populates="likes")
    node = relationship("StoryNode", back_populates="likes_relationship")

class StoryNode(Base):
    __tablename__ = "story_nodes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 归属哪本书 (哪个活动)
    book_id: Mapped[int] = mapped_column(ForeignKey("story_books.id"), index=True, nullable=False)
    
    # 树结构
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("story_nodes.id"), nullable=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # 内容
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    branch_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # 数据统计
    status: Mapped[NodeStatus] = mapped_column(SAEnum(NodeStatus,name="node_status"), default=NodeStatus.PENDING, index=True)
    depth: Mapped[int] = mapped_column(Integer, default=1)
    likes_count: Mapped[int] = mapped_column(Integer, default=0) # 缓存点赞数，避免频繁count查询
    
    # 时间节点
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),nullable=False,index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    # 关系
    book = relationship("StoryBook", back_populates="nodes")
    author = relationship("User", back_populates="nodes")
    
    # 树状关系
    children = relationship(
    "StoryNode",
    backref=backref("parent", remote_side=[id]),
    cascade="save-update, merge",   # 不要 delete-orphan
    passive_deletes=True,
    )   
    parent_id = mapped_column(ForeignKey("story_nodes.id", ondelete="RESTRICT"), nullable=True)

    
    # 点赞关系
    likes_relationship = relationship("NodeLike", back_populates="node", cascade="all, delete-orphan")
    # 评论关系
    comments = relationship(
    "StoryComment",
    back_populates="node",
    cascade="all, delete-orphan",  # 节点删除时评论一起删 OK
    )

    def __repr__(self):
        return f"<Node {self.id} (Book: {self.book_id})>"