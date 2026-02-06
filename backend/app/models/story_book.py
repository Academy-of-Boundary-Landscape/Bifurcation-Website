from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

from sqlalchemy.sql import func
from sqlalchemy import DateTime
class StoryBook(Base):
    """
    故事集/活动场次
    例如: "奶龙大冒险(第一季)"
    """
    __tablename__ = "story_books"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), index=True, nullable=False) # 活动标题
    description: Mapped[str | None] = mapped_column(Text) # 活动简介
    cover_image: Mapped[str | None] = mapped_column(String(255)) # 封面图URL
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True) # 活动是否正在进行
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),nullable=False,index=True)

    # 关联: 一本书包含很多节点
    nodes = relationship("StoryNode", back_populates="book", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StoryBook {self.title}>"