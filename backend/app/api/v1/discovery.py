from typing import Any, List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc, desc, or_
from sqlalchemy.orm import selectinload

from app.api import deps
from app.api.pagination import list_total, set_total_header
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
    response: Response,
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
    base = (
        select(StoryNode)
        .where(StoryNode.status == NodeStatus.PUBLISHED)
        .where(StoryNode.is_featured.is_(True))
    )
    await set_total_header(response, db, base)

    stmt = (
        base.options(selectinload(StoryNode.author))
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
    response: Response,
    book_id: Optional[int] = Query(None, ge=1, description="[可选] 只看某个活动/书本的动态"),
    skip: int = Query(0, ge=0), # 🛡️ 修复：防止负数导致 500
    limit: int = Query(20, ge=1, le=100), # 🛡️ 修复：防止请求过多数据
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    获取全站最新发布的节点。
    """
    base = select(StoryNode).where(StoryNode.status == NodeStatus.PUBLISHED)

    # `if book_id is not None` 而不是 `if book_id:`——
    # 后者会让 book_id=0 被当作未传，静默返回全局 feed
    if book_id is not None:
        base = base.where(StoryNode.book_id == book_id)

    await set_total_header(response, db, base)

    stmt = (
        base.options(selectinload(StoryNode.author))
        .order_by(desc(StoryNode.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
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
    response: Response,
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

    window_base = (
        select(StoryNode)
        .where(StoryNode.status == NodeStatus.PUBLISHED)
        .where(StoryNode.created_at >= start_date)
    )
    window_total = await list_total(db, window_base)

    # 🛡️ 兜底：近期太冷清（窗口内不足 3 条）则退回历史总榜，总数也用全站已发布数
    if window_total < 3:
        all_base = select(StoryNode).where(StoryNode.status == NodeStatus.PUBLISHED)
        response.headers["X-Total-Count"] = str(await list_total(db, all_base))
        stmt = (
            all_base.options(selectinload(StoryNode.author))
            .order_by(desc(StoryNode.likes_count))
            .limit(limit)
        )
        return (await db.execute(stmt)).scalars().all()

    response.headers["X-Total-Count"] = str(window_total)
    stmt = (
        window_base.options(selectinload(StoryNode.author))
        .order_by(desc(StoryNode.likes_count))
        .limit(limit)
    )
    return (await db.execute(stmt)).scalars().all()


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
    response: Response,
    q: str = Query(..., min_length=1, max_length=50, description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    简单的模糊搜索 (LIKE %q%)。
    """
    # 🛡️ 过滤特殊字符或空字符串逻辑已经在 Query(min_length=1) 中处理
    base = (
        select(StoryNode)
        .where(StoryNode.status == NodeStatus.PUBLISHED)
        .where(
            or_(
                StoryNode.title.ilike(f"%{q}%"),
                StoryNode.content.ilike(f"%{q}%"),
            )
        )
    )
    await set_total_header(response, db, base)

    stmt = (
        base.options(selectinload(StoryNode.author))
        .order_by(desc(StoryNode.likes_count))  # 搜索结果通常按热度排序
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
