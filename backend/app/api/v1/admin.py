from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.models.story import StoryNode, NodeStatus
from app.models.interaction import Notification, NotificationType # 用于发审核通知
from app.schemas import story as node_schema
from app.schemas import user as user_schema
from app.schemas import common as common_schema
from app.models.interaction import NotificationType
from app.utils.notification import send_notification 
router = APIRouter()

# ==========================================
# 🛡️ 节点审核管理 (Audit)
# ==========================================

@router.get(
    "/nodes/pending",
    response_model=List[node_schema.StoryNodeTreeItem],
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
    current_user: User = Depends(deps.get_current_admin), # 🔒 只有管理员能调
) -> Any:
    """
    专门给管理员用的“审核工作台”，只看 Pending 的
    """
    stmt = (
        select(StoryNode)
        .options(selectinload(StoryNode.author))
        .where(StoryNode.status == NodeStatus.PENDING)
        .order_by(StoryNode.created_at) # 按时间正序，先处理积压的
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch(
    "/nodes/{node_id}/audit",
    response_model=node_schema.StoryNodeTreeItem,
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
    current_user: User = Depends(deps.get_current_admin), # 🔒
) -> Any:
    # 1. 查节点
    node = await db.get(StoryNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    
    # 2. 修改状态
    old_status = node.status
    node.status = audit_in.status
    
    # 3. 发送通知 (可选：审核通过或驳回时通知作者)
    if old_status != audit_in.status:
        # 1. 审核通过
        if audit_in.status == NodeStatus.PUBLISHED:
            await send_notification(
                db=db,
                sender_id=current_user.id, # 管理员ID
                receiver_id=node.author_id,
                type=NotificationType.APPROVED,
                target_id=node.id
            )
            
        # 2. 审核驳回 (Rejected)
        elif audit_in.status == NodeStatus.REJECTED:
            await send_notification(
                db=db,
                sender_id=current_user.id,
                receiver_id=node.author_id,
                type=NotificationType.REJECTED,
                target_id=node.id
            )
    
    db.add(node)
    await db.commit()
    await db.refresh(node)
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
    current_user: User = Depends(deps.get_current_admin), # 🔒
) -> Any:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 逐项修改
    if user_in.role is not None:
        user.role = user_in.role
    
    if user_in.is_active is not None:
        user.is_active = user_in.is_active # True/False 控制封禁
        
    if user_in.username is not None:
        user.username = user_in.username # 强制改名
        
    if user_in.bio is not None:
        user.bio = user_in.bio
        
    if user_in.avatar is not None:
        user.avatar = user_in.avatar

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user