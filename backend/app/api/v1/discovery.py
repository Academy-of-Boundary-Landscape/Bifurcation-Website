from typing import Any, List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc, desc, or_
from sqlalchemy.orm import selectinload

from app.api import deps
from app.core.database import get_db
from app.models.story import StoryNode, NodeStatus
from app.schemas import story as node_schema
from app.schemas import common as common_schema

router = APIRouter()

# ==========================================
# ⭐ 精选节点 (Featured)
# ==========================================

@router.get(
    "/featured",
    response_model=List[node_schema.StoryNodeListItem],
    summary="精选节点",
    operation_id="getFeaturedNodes",
    responses={
        200: {"description": "获取成功"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    },
)
async def get_featured_nodes(
    limit: int = Query(6, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    获取管理员标记的精选节点。
    排序优先级：
    1. `feature_rank` 较小的节点优先
    2. 未设置 `feature_rank` 的节点排后
    3. 同 rank 下按发布时间倒序
    """
    stmt = (
        select(StoryNode)
        .options(selectinload(StoryNode.author))
        .where(StoryNode.status == NodeStatus.PUBLISHED)
        .where(StoryNode.is_featured.is_(True))
        .order_by(
            StoryNode.feature_rank.is_(None),
            asc(StoryNode.feature_rank),
            desc(StoryNode.published_at),
        )
        .limit(limit)
    )

    result = await db.execute(stmt)
    return result.scalars().all()


# ==========================================
# 🌊 最新动态 (Live Feed)
# ==========================================

@router.get(
    "/feed", 
    response_model=List[node_schema.StoryNodeListItem], 
    summary="最新动态 (瀑布流)",
    operation_id="getLatestFeed",
    responses={
        200: {"description": "获取成功"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    },
)
async def get_latest_feed(
    book_id: Optional[int] = Query(None, description="[可选] 只看某个活动/书本的动态"),
    skip: int = Query(0, ge=0), # 🛡️ 修复：防止负数导致 500
    limit: int = Query(20, ge=1, le=100), # 🛡️ 修复：防止请求过多数据
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    获取全站最新发布的节点。
    """
    stmt = (
        select(StoryNode)
        .options(selectinload(StoryNode.author))
        .where(StoryNode.status == NodeStatus.PUBLISHED)
        .order_by(desc(StoryNode.created_at))
    )

    if book_id:
        stmt = stmt.where(StoryNode.book_id == book_id)

    result = await db.execute(stmt.offset(skip).limit(limit))
    return result.scalars().all()


# ==========================================
# 🔥 热门趋势 (Trending)
# ==========================================

@router.get(
    "/trending", 
    response_model=List[node_schema.StoryNodeListItem], 
    summary="热门分支榜",
    operation_id="getTrendingNodes",
    responses={
        200: {"description": "获取成功"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    },
)
async def get_trending_nodes(
    days: int = Query(7, ge=1, le=30, description="统计最近几天的热度 (1-30天)"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    获取 "近期最热" 的节点。
    算法：在最近 N 天内发布的节点中，按 likes_count 倒序排列。
    """
    # 计算时间窗口 (使用 timezone-aware UTC)
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    stmt = (
        select(StoryNode)
        .options(selectinload(StoryNode.author))
        .where(StoryNode.status == NodeStatus.PUBLISHED)
        .where(StoryNode.created_at >= start_date)
        .order_by(desc(StoryNode.likes_count))
        .limit(limit)
    )

    result = await db.execute(stmt)
    nodes = result.scalars().all()
    
    # 🛡️ 兜底逻辑：如果近期太冷清，返回历史总榜
    if len(nodes) < 3:
        stmt_fallback = (
            select(StoryNode)
            .options(selectinload(StoryNode.author))
            .where(StoryNode.status == NodeStatus.PUBLISHED)
            .order_by(desc(StoryNode.likes_count))
            .limit(limit)
        )
        result = await db.execute(stmt_fallback)
        return result.scalars().all()
        
    return nodes


# ==========================================
# 🔍 搜索 (Search)
# ==========================================

@router.get(
    "/search", 
    response_model=List[node_schema.StoryNodeListItem], 
    summary="关键词搜索",
    operation_id="searchNodes",
    responses={
        200: {"description": "获取成功"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    },
)
async def search_nodes(
    q: str = Query(..., min_length=1, max_length=50, description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    简单的模糊搜索 (LIKE %q%)。
    """
    # 🛡️ 过滤特殊字符或空字符串逻辑已经在 Query(min_length=1) 中处理
    stmt = (
        select(StoryNode)
        .options(selectinload(StoryNode.author))
        .where(StoryNode.status == NodeStatus.PUBLISHED)
        .where(
            or_(
                StoryNode.title.ilike(f"%{q}%"),
                StoryNode.content.ilike(f"%{q}%"),
            )
        )
        .order_by(desc(StoryNode.likes_count)) # 搜索结果通常按热度排序
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    return result.scalars().all()
