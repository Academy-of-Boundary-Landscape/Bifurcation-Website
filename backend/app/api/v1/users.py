from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.models.story import StoryNode, NodeLike
from app.schemas import user as user_schema
from app.schemas import common as common_schema

router = APIRouter()

@router.get(
    "/{user_id}", 
    response_model=user_schema.UserProfileResponse, 
    summary="[公开] 查看他人主页",
    operation_id="getUserProfile",
    responses={
        200: {"description": "获取成功"},
        404: {"model": common_schema.ErrorResponse, "description": "用户不存在"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    }
)
async def read_user_profile(
    user_id: int = Path(..., ge=1, description="要查看的用户ID"), # 🛡️ 增加路径参数校验
    db: AsyncSession = Depends(get_db),
) -> Any:
    # 1. 查找用户
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="用户不存在"
        )

    # 2. 统计数据
    # 统计该用户发布的节点总数
    nodes_count_stmt = (
        select(func.count(StoryNode.id))
        .where(StoryNode.author_id == user.id)
    )
    nodes_count = (await db.execute(nodes_count_stmt)).scalar() or 0

    # 统计该用户收到的点赞总数 (通过 Join StoryNode 实现)
    total_likes_stmt = (
        select(func.count(NodeLike.user_id))
        .select_from(NodeLike)
        .join(StoryNode, NodeLike.node_id == StoryNode.id)
        .where(StoryNode.author_id == user.id)
    )
    total_likes = (await db.execute(total_likes_stmt)).scalar() or 0

    # 3. 组装并验证数据 (使用 Pydantic V2 推荐方式)
    # model_validate 会自动从 SQLAlchemy 对象中提取字段
    profile = user_schema.UserProfileResponse.model_validate(user)
    
    # 注入额外的统计字段
    profile.nodes_count = nodes_count
    profile.total_likes_received = total_likes
    
    return profile