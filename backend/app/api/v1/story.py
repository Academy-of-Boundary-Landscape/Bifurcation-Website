# app/api/v1/story.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import desc, select, text, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, defer, raiseload
from sqlalchemy.sql import true

from app.api import deps
from app.core.database import get_db
from app.models.story import NodeStatus, StoryNode
from app.models.story_book import StoryBook
from app.models.user import User, UserRole
from app.schemas import story as node_schema
from app.schemas import story_book as book_schema
from app.schemas import common as common_schema
from app.models.interaction import NotificationType
from app.utils.notification import send_notification

router = APIRouter()


# ==========================================
# 🛠 内部辅助函数
# ==========================================
def build_memory_tree(nodes: List[StoryNode]) -> List[node_schema.StoryNodeTreeItem]:
    """
    把一堆节点（已预加载 author/children）组装成内存树。
    关键点：先用 StoryNodeListItem 做一次 model_validate，避免 Pydantic 触碰 children 懒加载。
    """
    node_map: dict[int, node_schema.StoryNodeTreeItem] = {}
    roots: List[node_schema.StoryNodeTreeItem] = []

    for n in nodes:
        base = node_schema.StoryNodeListItem.model_validate(n).model_dump()
        node_map[n.id] = node_schema.StoryNodeTreeItem(**base, children=[])

    for n in nodes:
        item = node_map[n.id]
        if n.parent_id is None:
            roots.append(item)
        else:
            parent = node_map.get(n.parent_id)
            if parent is not None:
                parent.children.append(item)

    return roots


# ==========================================
# 📖 StoryBook (故事集/活动) 模块
# ==========================================
@router.post(
    "/books",
    response_model=book_schema.StoryBookResponse,
    summary="[Admin] 创建活动",
    operation_id="createBook",
)
async def create_book(
    book_in: book_schema.StoryBookCreate,
    current_user: User = Depends(deps.get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    book = StoryBook(
        title=book_in.title,
        description=book_in.description,
        cover_image=book_in.cover_image,
        is_active=True,
        created_at=datetime.utcnow(),  # 如果模型里已有 default，可删
    )
    db.add(book)
    try:
        await db.commit()
        await db.refresh(book)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="创建活动失败") from e
    return book
@router.patch(
    "/books/{book_id}",
    response_model=book_schema.StoryBookResponse,
    summary="[Admin] 更新活动")
async def update_book(
    book_id: int = Path(..., ge=1),
    book_in: book_schema.StoryBookUpdate = Depends(),
    current_user: User = Depends(deps.get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    book = await db.get(StoryBook, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="活动不存在")

    for field, value in book_in.model_dump(exclude_unset=True).items():
        setattr(book, field, value)

    try:
        await db.commit()
        await db.refresh(book)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="更新活动失败") from e
    return book

@router.get(
    "/books",
    response_model=List[book_schema.StoryBookResponse],
    summary="获取活动列表",
    operation_id="getBooks",
    responses={
        200: {"description": "获取成功"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    },
)
async def read_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(StoryBook)
        .where(StoryBook.is_active.is_(True))
        .order_by(desc(StoryBook.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


# ==========================================
# 🌳 StoryNode (故事节点) 模块
# ==========================================
@router.get(
    "/tree",
    response_model=List[node_schema.StoryNodeTreeItem],
    summary="获取故事树结构",
    operation_id="getStoryTree",
)
async def get_story_tree(
    book_id: int = Query(..., ge=1),
    current_user: Optional[User] = Depends(deps.get_current_user_or_none),
    db: AsyncSession = Depends(get_db),
):
    """
    权限规则：
    - 管理员：看到全部
    - 登录普通用户：看到 published/locked + 自己写的（含 pending/rejected）
    - 游客：只看 published/locked

    技术点：
    - defer(content) 避免树接口把正文大字段从 DB 拉出来
    - selectinload(author/children) 预加载，避免 MissingGreenlet
    - build_memory_tree 手动组装，避免 Pydantic 触碰 children 懒加载
    """
    stmt = (
        select(StoryNode)
        .options(
            # 你会在 schema 里返回 author，所以要预加载，避免 MissingGreenlet
            selectinload(StoryNode.author),

            # 树接口不需要正文：减少数据搬运
            defer(StoryNode.content),

            # 防呆：此接口不允许碰 ORM children（我们用 build_memory_tree 自己组树）
            # 如果未来有人误用 node.children，会立刻报错而不是悄悄触发异步懒加载
            raiseload(StoryNode.children),
        )
        .where(StoryNode.book_id == book_id)
        .order_by(StoryNode.id)
    )
    is_admin = bool(current_user and current_user.role == UserRole.ADMIN)

    if is_admin:
        pass
    elif current_user:
        stmt = stmt.where(
            or_(
                StoryNode.status.in_([NodeStatus.PUBLISHED, NodeStatus.LOCKED]),
                StoryNode.author_id == current_user.id,
            )
        )
    else:
        stmt = stmt.where(StoryNode.status.in_([NodeStatus.PUBLISHED, NodeStatus.LOCKED]))

    nodes = (await db.execute(stmt)).scalars().all()
    return build_memory_tree(nodes)


@router.get(
    "/node/{node_id}/path",
    response_model=List[node_schema.StoryNodeRead],
    summary="获取阅读路径 (溯源)",
    operation_id="getNodePath",
    responses={
        200: {"description": "获取成功"},
        404: {"model": common_schema.ErrorResponse, "description": "路径不存在或无权访问"},
    },
)
async def get_node_reading_path(
    node_id: int = Path(..., ge=1),
    current_user: Optional[User] = Depends(deps.get_current_user_or_none),
    db: AsyncSession = Depends(get_db),
):
    """
    返回从根到当前节点的路径（按 depth 升序）
    权限规则与 /tree 一致：
    - admin：所有节点可见
    - 普通用户：published/locked + 自己的
    - 游客：published/locked（游客如果传 pending 节点 id，会返回 404）
    """
    is_admin = bool(current_user and current_user.role == UserRole.ADMIN)
    user_id = current_user.id if current_user else None

    if is_admin:
        anchor_vis = "1=1"
        rec_vis = "1=1"
    elif user_id is not None:
        anchor_vis = "(status IN ('published','locked') OR author_id = :user_id)"
        rec_vis = "(n.status IN ('published','locked') OR n.author_id = :user_id)"
    else:
        anchor_vis = "status IN ('published','locked')"
        rec_vis = "n.status IN ('published','locked')"

    query = text(f"""
    WITH RECURSIVE story_path AS (
        SELECT *
        FROM story_nodes
        WHERE id = :node_id AND ({anchor_vis})

        UNION ALL

        SELECT n.*
        FROM story_nodes n
        INNER JOIN story_path p ON n.id = p.parent_id
        WHERE ({rec_vis})
    )
    SELECT * FROM story_path ORDER BY depth ASC;
    """)

    params = {"node_id": node_id}
    if user_id is not None and not is_admin:
        params["user_id"] = user_id

    rows = (await db.execute(query, params)).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="路径不存在或无权访问")

    author_ids = {r["author_id"] for r in rows if r.get("author_id") is not None}
    users_map: dict[int, User] = {}
    if author_ids:
        user_stmt = select(User).where(User.id.in_(author_ids))
        user_res = await db.execute(user_stmt)
        users_map = {u.id: u for u in user_res.scalars().all()}

    # ✅ 用 schema 再过一遍，避免额外字段/缺字段导致隐蔽问题
    final_list: List[node_schema.StoryNodeRead] = []
    for r in rows:
        item = dict(r)
        item["author"] = users_map.get(item["author_id"])
        final_list.append(node_schema.StoryNodeRead.model_validate(item))

    return final_list


@router.post(
    "/node",
    response_model=node_schema.StoryNodeListItem,
    summary="提交续写内容",
    operation_id="createNode",
    responses={
        200: {"description": "创建成功"},
        400: {"model": common_schema.ErrorResponse, "description": "活动关闭或分支完结"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
        403: {"model": common_schema.ErrorResponse, "description": "无权创建"},
        404: {"model": common_schema.ErrorResponse, "description": "父节点不存在"},
    },
)
async def create_story_node(
    node_in: node_schema.StoryNodeCreate,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    is_admin = current_user.role == UserRole.ADMIN

    # 1) 活动检查
    book = await db.get(StoryBook, node_in.book_id)
    if not book or (not book.is_active and not is_admin):
        raise HTTPException(status_code=400, detail="活动已关闭")

    # 2) 根节点与父节点逻辑
    new_depth = 1
    parent_node: Optional[StoryNode] = None

    if node_in.parent_id is None:
        if not is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以创建开篇")
    else:
        parent_node = await db.get(StoryNode, node_in.parent_id)
        if not parent_node:
            raise HTTPException(status_code=404, detail="父节点不存在")

        if parent_node.book_id != node_in.book_id:
            raise HTTPException(status_code=400, detail="父节点不属于同一活动")

        if not is_admin:
            if parent_node.status == NodeStatus.LOCKED:
                raise HTTPException(status_code=400, detail="该分支已完结")
            if parent_node.status != NodeStatus.PUBLISHED:
                raise HTTPException(status_code=403, detail="无法在未发布节点后续写")

        new_depth = parent_node.depth + 1

    # 3) 创建节点
    initial_status = NodeStatus.PUBLISHED if is_admin else NodeStatus.PENDING
    new_node = StoryNode(
        **node_in.model_dump(),
        author_id=current_user.id,
        depth=new_depth,
        status=initial_status,
    )
    db.add(new_node)

    try:
        await db.commit()
        await db.refresh(new_node)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="创建节点失败") from e

    # ✅ 确保 author 预加载，避免 response_model 触发懒加载 MissingGreenlet
    new_node = (
        await db.execute(
            select(StoryNode)
            .options(selectinload(StoryNode.author))
            .where(StoryNode.id == new_node.id)
        )
    ).scalars().first()

    # 4) 通知父节点作者（通知失败不影响主流程）
    if parent_node:
        try:
            await send_notification(
                db=db,
                sender_id=current_user.id,
                receiver_id=parent_node.author_id,
                type=NotificationType.BRANCHED,
                target_id=parent_node.id,
            )
            await db.commit()
        except Exception:
            await db.rollback()

    return new_node


@router.get(
    "/node/{node_id}",
    response_model=node_schema.StoryNodeRead,
    summary="查看节点正文详情",
    operation_id="getNodeDetail",
    responses={
        200: {"description": "获取成功"},
        403: {"model": common_schema.ErrorResponse, "description": "审核中不可见"},
        404: {"model": common_schema.ErrorResponse, "description": "节点不存在"},
    },
)
async def get_node_detail(
    node_id: int = Path(..., ge=1),
    current_user: Optional[User] = Depends(deps.get_current_user_or_none),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(StoryNode)
        .options(selectinload(StoryNode.author))
        .where(StoryNode.id == node_id)
    )
    node = (await db.execute(stmt)).scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")

    is_admin = bool(current_user and current_user.role == UserRole.ADMIN)
    is_author = bool(current_user and node.author_id == current_user.id)

    if node.status not in [NodeStatus.PUBLISHED, NodeStatus.LOCKED] and not (is_admin or is_author):
        raise HTTPException(status_code=403, detail="该内容正在审核中")

    return node


@router.get(
    "/user/{user_id}/nodes",
    response_model=List[node_schema.StoryNodeListItem],
    summary="获取用户的创作列表",
    operation_id="getUserNodes",
)
async def read_user_nodes(
    user_id: int = Path(..., ge=1),
    status: Optional[NodeStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: Optional[User] = Depends(deps.get_current_user_or_none),
    db: AsyncSession = Depends(get_db),
):
    is_admin = bool(current_user and current_user.role == UserRole.ADMIN)
    is_self = bool(current_user and current_user.id == user_id)

    stmt = (
        select(StoryNode)
        .options(selectinload(StoryNode.author))
        .where(StoryNode.author_id == user_id)
        .order_by(desc(StoryNode.created_at))
        .offset(skip)
        .limit(limit)
    )

    if not (is_admin or is_self):
        stmt = stmt.where(StoryNode.status == NodeStatus.PUBLISHED)
    elif status:
        stmt = stmt.where(StoryNode.status == status)

    return (await db.execute(stmt)).scalars().all()


@router.patch(
    "/node/{node_id}",
    response_model=node_schema.StoryNodeRead,
    summary="修改节点内容",
    operation_id="updateNode",
)
async def update_story_node(
    node_id: int = Path(..., ge=1),
    node_in: node_schema.NodeUpdate = Depends(),  # ✅ 不要 None；让 FastAPI 负责 body 校验
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    node = await db.get(StoryNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")

    if node.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="无权修改")

    update_data = node_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(node, field, value)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="更新失败") from e

    # ✅ 返回 StoryNodeRead 需要 author，重新 select 一次最稳（避免 refresh 不加载 relationship）
    node = (
        await db.execute(
            select(StoryNode)
            .options(selectinload(StoryNode.author))
            .where(StoryNode.id == node_id)
        )
    ).scalars().first()

    return node


@router.delete(
    "/node/{node_id}",
    response_model=node_schema.MessageResponse,
    summary="删除叶子节点",
    operation_id="deleteNode",
)
async def delete_story_node(
    node_id: int = Path(..., ge=1),
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    node = await db.get(StoryNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")

    if node.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="无权删除")

    # 有子节点则不能删除
    child_stmt = select(StoryNode.id).where(StoryNode.parent_id == node_id).limit(1)
    if (await db.execute(child_stmt)).scalar() is not None:
        raise HTTPException(status_code=400, detail="已有后续故事，无法删除")

    try:
        await db.delete(node)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="删除失败") from e

    return {"detail": "节点已成功移除"}
