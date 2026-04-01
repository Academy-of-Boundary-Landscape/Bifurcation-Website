# app/api/v1/admin.py
from datetime import datetime, timezone
from datetime import timedelta
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_
from sqlalchemy.orm import selectinload

from app.api import deps
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.story import StoryNode, NodeStatus, NodeVisibility
from app.models.interaction import Notification, NotificationType
from app.schemas import story as node_schema
from app.schemas import user as user_schema
from app.schemas import common as common_schema
from app.utils.notification import send_notification

router = APIRouter()


# ==========================================
# 🛡️ 节点审核管理 (Audit)
# ==========================================

@router.get(
    "/nodes/pending",
    response_model=List[node_schema.StoryNodeRead],
    summary="[Admin] 获取待审核节点列表",
    responses={
        200: {"description": "获取成功"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
        403: {"model": common_schema.ErrorResponse, "description": "权限不足"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    },
)
async def get_pending_nodes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    专门给管理员用的"审核工作台"，只看 Pending 的。
    """
    stmt = (
        select(StoryNode)
        .options(selectinload(StoryNode.author))
        .where(StoryNode.status == NodeStatus.PENDING)
        .order_by(StoryNode.created_at)  # 按时间正序，先处理积压的
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch(
    "/nodes/{node_id}/audit",
    response_model=node_schema.StoryNodeRead,
    summary="[Admin] 审核/强制修改节点状态",
    responses={
        200: {"description": "操作成功"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
        403: {"model": common_schema.ErrorResponse, "description": "权限不足"},
        404: {"model": common_schema.ErrorResponse, "description": "节点不存在"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    },
)
async def audit_node(
    node_id: int,
    audit_in: node_schema.NodeAuditRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    # 1. 查节点
    node = await db.get(StoryNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    if audit_in.status == NodeStatus.PENDING:
        raise HTTPException(status_code=400, detail="审核接口不支持将节点设为 pending")

    old_status = node.status
    now = datetime.now(timezone.utc)

    # 2. 修改状态
    node.status = audit_in.status
    node.reviewed_by = current_user.id
    node.reviewed_at = now

    # 3. 根据状态设置额外字段
    if audit_in.status == NodeStatus.PUBLISHED:
        node.published_at = now
        node.visibility = NodeVisibility.PUBLIC
        node.archived_at = None
        node.archived_reason = None
        node.reject_reason = None
        notification_type = NotificationType.APPROVED
        notification_message = None
    elif audit_in.status == NodeStatus.ARCHIVED:
        node.visibility = NodeVisibility.PRIVATE
        node.archived_at = now
        node.reject_reason = audit_in.reject_reason
        node.archived_reason = audit_in.reject_reason or "管理员归档"
        notification_type = NotificationType.REJECTED
        notification_message = audit_in.reject_reason
    else:
        # PENDING 状态通常不会在审核时设置，但保留兼容
        notification_type = None
        notification_message = None

    # 4. 发送通知（状态变化时）
    if old_status != audit_in.status and notification_type:
        await send_notification(
            db=db,
            receiver_id=node.author_id,
            sender_id=current_user.id,
            type=notification_type,
            node_id=node.id,
            book_id=node.book_id,
            message=notification_message,
        )

    db.add(node)
    await db.commit()
    await db.refresh(node)

    # 预加载 author
    node = (
        await db.execute(
            select(StoryNode)
            .options(selectinload(StoryNode.author))
            .where(StoryNode.id == node_id)
        )
    ).scalars().first()

    return node


# ==========================================
# 👮 用户管理 (User Management)
# ==========================================

@router.patch(
    "/users/{user_id}",
    response_model=user_schema.UserResponse,
    summary="[Admin] 管理员强制修改用户信息(含封禁)",
    responses={
        200: {"description": "更新成功"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
        403: {"model": common_schema.ErrorResponse, "description": "权限不足"},
        404: {"model": common_schema.ErrorResponse, "description": "用户不存在"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    },
)
async def admin_update_user(
    user_id: int,
    user_in: user_schema.UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 逐项修改
    if user_in.role is not None:
        user.role = user_in.role

    if user_in.is_active is not None:
        user.is_active = user_in.is_active

    if user_in.username is not None:
        user.username = user_in.username

    if user_in.bio is not None:
        user.bio = user_in.bio

    if user_in.avatar is not None:
        user.avatar = user_in.avatar

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get(
    "/users",
    response_model=List[user_schema.UserResponse],
    summary="[Admin] 获取用户列表",
    responses={
        200: {"description": "获取成功"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
        403: {"model": common_schema.ErrorResponse, "description": "权限不足"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    },
)
async def admin_list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    role: UserRole | None = Query(None, description="按角色筛选：admin/writer/banned"),
    is_active: bool | None = Query(None, description="按活跃状态筛选"),
    keyword: str | None = Query(None, min_length=1, max_length=50, description="邮箱/用户名关键词"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    stmt = select(User).order_by(desc(User.created_at))

    if role is not None:
        stmt = stmt.where(User.role == role)

    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)

    if keyword:
        q = keyword.strip()
        stmt = stmt.where(
            or_(
                User.username.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
            )
        )

    result = await db.execute(stmt.offset(skip).limit(limit))
    return result.scalars().all()


@router.get(
    "/stats",
    summary="[Admin] 仪表盘统计",
    responses={
        200: {"description": "获取成功"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
        403: {"model": common_schema.ErrorResponse, "description": "权限不足"},
    },
)
async def admin_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    users_total = (await db.execute(select(func.count(User.id)))).scalar() or 0
    users_active = (await db.execute(select(func.count(User.id)).where(User.is_active.is_(True)))).scalar() or 0

    nodes_total = (await db.execute(select(func.count(StoryNode.id)))).scalar() or 0
    nodes_pending = (
        await db.execute(select(func.count(StoryNode.id)).where(StoryNode.status == NodeStatus.PENDING))
    ).scalar() or 0
    nodes_published = (
        await db.execute(select(func.count(StoryNode.id)).where(StoryNode.status == NodeStatus.PUBLISHED))
    ).scalar() or 0
    nodes_archived = (
        await db.execute(select(func.count(StoryNode.id)).where(StoryNode.status == NodeStatus.ARCHIVED))
    ).scalar() or 0

    new_nodes_7d = (
        await db.execute(select(func.count(StoryNode.id)).where(StoryNode.created_at >= seven_days_ago))
    ).scalar() or 0
    new_users_7d = (
        await db.execute(select(func.count(User.id)).where(User.created_at >= seven_days_ago))
    ).scalar() or 0

    return {
        "users": {
            "total": users_total,
            "active": users_active,
            "inactive": users_total - users_active,
            "new_7d": new_users_7d,
        },
        "nodes": {
            "total": nodes_total,
            "pending": nodes_pending,
            "published": nodes_published,
            "archived": nodes_archived,
            "new_7d": new_nodes_7d,
        },
    }
