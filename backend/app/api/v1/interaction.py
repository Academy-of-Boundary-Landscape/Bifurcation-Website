# app/api/v1/interaction.py
from datetime import datetime, timezone
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update, func, case
from sqlalchemy.orm import selectinload

from app.api import deps
from app.api.pagination import set_total_header
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.story import StoryNode, NodeLike
from app.models.interaction import StoryComment, Notification, NotificationType
from app.schemas import interaction as interact_schema
from app.schemas import common as common_schema
from app.schemas.story import MessageResponse
from app.services.interactions import create_story_comment, toggle_story_node_like
from app.core.rate_limit import limiter, LIKE_LIMIT, COMMENT_LIMIT

router = APIRouter()


# ==========================================
# ❤️ 点赞模块 (Like)
# ==========================================

@router.post(
    "/node/{node_id}/like",
    response_model=interact_schema.LikeToggleResponse,
    summary="点赞/取消点赞 (Toggle)",
    operation_id="toggleLike",
    responses={
        200: {"description": "操作成功"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
        404: {"model": common_schema.ErrorResponse, "description": "节点不存在"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    },
)
@limiter.limit(LIKE_LIMIT)
async def toggle_node_like(
    request: Request,
    node_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await toggle_story_node_like(db=db, current_user=current_user, node_id=node_id)


# ==========================================
# 💬 评论模块 (Comment)
# ==========================================

@router.get(
    "/node/{node_id}/comments",
    response_model=List[interact_schema.CommentResponse],
    summary="获取评论列表",
    operation_id="getNodeComments",
    responses={
        200: {"description": "获取成功"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    },
)
async def get_node_comments(
    node_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Any:
    stmt = (
        select(StoryComment)
        .where(StoryComment.node_id == node_id)
        .where(StoryComment.deleted_at.is_(None))  # 过滤软删除评论
        .options(selectinload(StoryComment.user))
        .order_by(desc(StoryComment.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post(
    "/node/{node_id}/comment",
    response_model=interact_schema.CommentResponse,
    summary="发表评论",
    operation_id="createComment",
    responses={
        200: {"description": "发表成功"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
        404: {"model": common_schema.ErrorResponse, "description": "节点不存在"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    },
)
@limiter.limit(COMMENT_LIMIT)
async def create_node_comment(
    request: Request,
    node_id: int,
    comment_in: interact_schema.CommentCreate,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await create_story_comment(
        db=db,
        current_user=current_user,
        node_id=node_id,
        comment_in=comment_in,
    )


# ==========================================
# 📬 通知模块 (Notification)
# ==========================================

@router.get(
    "/notifications",
    response_model=List[interact_schema.NotificationResponse],
    summary="我的通知列表",
    operation_id="getNotifications",
    responses={
        200: {"description": "获取成功"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    },
)
async def get_my_notifications(
    response: Response,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    base = select(Notification).where(Notification.user_id == current_user.id)
    await set_total_header(response, db, base)

    stmt = (
        base.options(selectinload(Notification.sender))
        .order_by(desc(Notification.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/notifications/unread-count",
    response_model=interact_schema.NotificationUnreadCountResponse,
    summary="我的未读通知数",
    operation_id="getUnreadNotificationCount",
    responses={
        200: {"description": "获取成功"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
    },
)
async def get_unread_notifications_count(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    unread_count = (
        await db.execute(
            select(func.count(Notification.id))
            .where(Notification.user_id == current_user.id)
            .where(Notification.is_read.is_(False))
        )
    ).scalar() or 0
    return {"unread_count": unread_count}


@router.put(
    "/notifications/{notification_id}/read",
    response_model=MessageResponse,
    summary="单条通知标记已读",
    operation_id="markNotificationRead",
    responses={
        200: {"description": "设为已读"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
        404: {"model": common_schema.ErrorResponse, "description": "通知不存在"},
    },
)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    notification = await db.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="通知不存在")

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        db.add(notification)
        await db.commit()

    return {"detail": "通知已标记为已读"}


@router.put(
    "/notifications/read",
    response_model=MessageResponse,
    summary="一键已读",
    operation_id="markNotificationsRead",
    responses={
        200: {"description": "全部设为已读"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
    },
)
async def mark_notifications_read(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    stmt = (
        update(Notification)
        .where(Notification.user_id == current_user.id)
        .where(Notification.is_read.is_(False))
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    await db.execute(stmt)
    await db.commit()
    return {"detail": "全部通知已标记为已读"}


# ==========================================
# 🗑️ 评论删除模块 (Comment Deletion)
# ==========================================

@router.delete(
    "/comment/{comment_id}",
    response_model=MessageResponse,
    summary="软删除评论",
    operation_id="deleteComment",
    responses={
        200: {"description": "评论已删除"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
        403: {"model": common_schema.ErrorResponse, "description": "无权删除"},
        404: {"model": common_schema.ErrorResponse, "description": "评论不存在"},
    },
)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    软删除评论：将评论标记为 deleted，而非真正从数据库删除。
    
    权限规则：
    - 仅评论作者或管理员可以删除
    
    🔧 修复问题 6: 删除时同步更新节点的 comments_count
    """
    comment = await db.get(StoryComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 权限检查：仅作者或管理员可删除
    is_admin = current_user.role == UserRole.ADMIN
    is_author = comment.user_id == current_user.id
    
    if not is_admin and not is_author:
        raise HTTPException(status_code=403, detail="无权删除此评论")
    
    if comment.deleted_at is not None:
        return {"detail": "评论已是已删除状态"}
    
    try:
        # 软删除评论
        comment.deleted_at = datetime.now(timezone.utc)
        comment.deleted_by = current_user.id
        db.add(comment)
        
        # 原子自减节点 comments_count 并防负（与软删一致）
        await db.execute(
            update(StoryNode)
            .where(StoryNode.id == comment.node_id)
            .values(comments_count=case((StoryNode.comments_count > 0, StoryNode.comments_count - 1), else_=0))
        )

        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="删除失败") from e
    
    return {"detail": "评论已删除"}
