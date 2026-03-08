# app/api/v1/interaction.py
from datetime import datetime, timezone
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update, func
from sqlalchemy.orm import selectinload

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.models.story import StoryNode, NodeLike
from app.models.interaction import StoryComment, Notification, NotificationType
from app.schemas import interaction as interact_schema
from app.schemas import common as common_schema
from app.schemas.story import MessageResponse
from app.utils.notification import send_notification

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
async def toggle_node_like(
    node_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    # 1. 检查节点是否存在
    node = await db.get(StoryNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")

    # 防御 likes_count 为空的情况
    if node.likes_count is None:
        node.likes_count = 0

    # 2. 检查是否点过赞
    stmt = select(NodeLike).where(
        NodeLike.user_id == current_user.id,
        NodeLike.node_id == node_id,
    )
    result = await db.execute(stmt)
    existing_like = result.scalars().first()

    action = ""
    if existing_like:
        await db.delete(existing_like)
        if node.likes_count > 0:
            node.likes_count -= 1
        action = "unliked"
    else:
        new_like = NodeLike(user_id=current_user.id, node_id=node_id)
        db.add(new_like)
        node.likes_count += 1
        action = "liked"

        # 触发通知（自己点自己不通知，send_notification 内部已处理）
        await send_notification(
            db=db,
            receiver_id=node.author_id,
            sender_id=current_user.id,
            type=NotificationType.LIKED,
            node_id=node.id,
            book_id=node.book_id,
            dedupe_key=f"liked:{current_user.id}:{node.id}",
        )

    await db.commit()
    return {
        "status": "success",
        "action": action,
        "likes_count": node.likes_count,
    }


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
async def create_node_comment(
    node_id: int,
    comment_in: interact_schema.CommentCreate,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    node = await db.get(StoryNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")

    if not comment_in.content or not comment_in.content.strip():
        raise HTTPException(status_code=400, detail="评论内容不能为空")

    comment = StoryComment(
        node_id=node_id,
        book_id=node.book_id,   # 冗余 book_id，便于后台聚合
        user_id=current_user.id,
        content=comment_in.content.strip(),
    )
    db.add(comment)

    # 🛡️ 同步更新节点的评论计数器
    if node.comments_count is None:
        node.comments_count = 0
    node.comments_count += 1

    # 触发通知（自己评论自己不通知，send_notification 内部已处理）
    await send_notification(
        db=db,
        receiver_id=node.author_id,
        sender_id=current_user.id,
        type=NotificationType.COMMENTED,
        node_id=node.id,
        book_id=node.book_id,
        dedupe_key=f"commented:{current_user.id}:{node.id}",
    )

    await db.commit()
    await db.refresh(comment)

    # 预加载 user，避免 response_model 触发懒加载
    comment = (
        await db.execute(
            select(StoryComment)
            .options(selectinload(StoryComment.user))
            .where(StoryComment.id == comment.id)
        )
    ).scalars().first()

    return comment


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
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    stmt = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .options(selectinload(Notification.sender))
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
            .where(Notification.is_read == False)
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
        .where(Notification.is_read == False)
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
        
        # 🔧 修复问题 6: 同步更新节点的 comments_count
        node = await db.get(StoryNode, comment.node_id)
        if node:
            if node.comments_count is None:
                node.comments_count = 0
            if node.comments_count > 0:
                node.comments_count -= 1
            db.add(node)
        
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="删除失败") from e
    
    return {"detail": "评论已删除"}
