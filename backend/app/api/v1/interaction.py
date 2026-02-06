from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
from sqlalchemy.orm import selectinload

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.models.story import StoryNode, NodeLike
from app.models.interaction import StoryComment, Notification, NotificationType
from app.schemas import interaction as interact_schema
from app.schemas import common as common_schema
from app.schemas.story import MessageResponse # 复用之前定义的通用消息模型
from app.utils.notification import send_notification

router = APIRouter()

# ==========================================
# ❤️ 点赞模块 (Like)
# ==========================================

@router.post(
    "/node/{node_id}/like", 
    response_model=interact_schema.LikeToggleResponse, # ⭐ 新增专门的响应模型
    summary="点赞/取消点赞 (Toggle)",
    operation_id="toggleLike",
    responses={
        200: {"description": "操作成功"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
        404: {"model": common_schema.ErrorResponse, "description": "节点不存在"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    }
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

    # 🛡️ 防御 likes_count 为空的情况
    if node.likes_count is None:
        node.likes_count = 0

    # 2. 检查是否点过赞
    stmt = select(NodeLike).where(
        NodeLike.user_id == current_user.id,
        NodeLike.node_id == node_id
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
        
        # 触发通知
        await send_notification(
            db=db,
            sender_id=current_user.id,
            receiver_id=node.author_id,
            type=NotificationType.LIKED,
            target_id=node.id
        )

    await db.commit()
    return {
        "status": "success", 
        "action": action, 
        "likes_count": node.likes_count
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
    }
)
async def get_node_comments(
    node_id: int,
    skip: int = Query(0, ge=0), # 🛡️ 防御负数
    limit: int = Query(50, ge=1, le=100), # 🛡️ 防御超大请求
    db: AsyncSession = Depends(get_db),
) -> Any:
    stmt = (
        select(StoryComment)
        .where(StoryComment.node_id == node_id)
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
    }
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

    # 🛡️ 内容校验：禁止空白评论
    if not comment_in.content or not comment_in.content.strip():
        raise HTTPException(status_code=400, detail="评论内容不能为空")

    comment = StoryComment(
        node_id=node_id,
        user_id=current_user.id,
        content=comment_in.content
    )
    db.add(comment)
    
    await send_notification(
        db=db,
        sender_id=current_user.id,
        receiver_id=node.author_id,
        type=NotificationType.COMMENTED,
        target_id=node.id
    )

    await db.commit()
    await db.refresh(comment)
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
    }
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


@router.put(
    "/notifications/read", 
    response_model=MessageResponse, # ⭐ 使用统一消息模型
    summary="一键已读",
    operation_id="markNotificationsRead",
    responses={
        200: {"description": "全部设为已读"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
    }
)
async def mark_notifications_read(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    stmt = (
        update(Notification)
        .where(Notification.user_id == current_user.id)
        .where(Notification.is_read == False)
        .values(is_read=True)
    )
    await db.execute(stmt)
    await db.commit()
    return {"msg": "All marked as read"}