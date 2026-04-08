# app/api/v1/story.py
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy import desc, select, text, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, defer, raiseload

from app.api import deps
from app.core.database import get_db
from app.models.story import NodeStatus, NodeVisibility, StoryNode
from app.models.story_book import StoryBook, BookPhase
from app.models.user import User, UserRole
from app.schemas import story as node_schema
from app.schemas import story_book as book_schema
from app.schemas import common as common_schema
from app.services.story_nodes import create_story_node_record

router = APIRouter()
logger = logging.getLogger(__name__)


# ==========================================
# 🛠 内部辅助函数
# ==========================================

def _is_node_visible(
    node_status: NodeStatus,
    node_author_id: int,
    is_admin: bool,
    current_user_id: Optional[int],
) -> bool:
    """
    权限规则：
    - published：所有人可见
    - pending / archived：仅管理员和作者本人可见
    """
    if node_status == NodeStatus.PUBLISHED:
        return True
    return is_admin or (current_user_id is not None and current_user_id == node_author_id)


def _visible_filter(stmt, is_admin: bool, current_user_id: Optional[int]):
    """
    为 SQLAlchemy select 语句附加可见性过滤条件。
    - 管理员：不过滤
    - 登录用户：published + 自己的（pending/archived）
    - 游客：只看 published
    """
    if is_admin:
        return stmt
    if current_user_id is not None:
        return stmt.where(
            or_(
                StoryNode.status == NodeStatus.PUBLISHED,
                StoryNode.author_id == current_user_id,
            )
        )
    return stmt.where(StoryNode.status == NodeStatus.PUBLISHED)


def build_memory_tree(nodes: List[StoryNode]) -> List[node_schema.StoryNodeTreeItem]:
    """
    把一堆节点（已预加载 author）组装成内存树。
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
            else:
                # 当父节点因当前视角的权限/状态过滤而缺失时，
                # 仍将可见节点提升为局部 root，避免整段子树直接消失。
                roots.append(item)

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
        phase=book_in.phase,
        start_at=book_in.start_at,
        writing_end_at=book_in.writing_end_at,
        showcase_end_at=book_in.showcase_end_at,
        allow_new_nodes=book_in.allow_new_nodes,
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
    summary="[Admin] 更新活动",
    operation_id="updateBook",
)
async def update_book(
    book_id: int = Path(..., ge=1),
    book_in: book_schema.StoryBookUpdate = Body(...),
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
    phase: Optional[BookPhase] = Query(None, description="按阶段筛选，不传则返回全部（不含 archived）"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(StoryBook).order_by(desc(StoryBook.created_at)).offset(skip).limit(limit)

    if phase is not None:
        stmt = stmt.where(StoryBook.phase == phase)
    else:
        # 默认不返回已归档的活动（归档活动走专门的展示入口）
        stmt = stmt.where(StoryBook.phase != BookPhase.ARCHIVED)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/books/{book_id}",
    response_model=book_schema.StoryBookResponse,
    summary="获取活动详情",
    operation_id="getBookDetail",
    responses={
        200: {"description": "获取成功"},
        404: {"model": common_schema.ErrorResponse, "description": "活动不存在"},
    },
)
async def read_book_detail(
    book_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
):
    book = await db.get(StoryBook, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="活动不存在")
    return book


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
    - 管理员：看到全部节点
    - 登录普通用户：published + 自己写的（含 pending/archived）
    - 游客：只看 published

    技术点：
    - defer(content) 避免树接口把正文大字段从 DB 拉出来
    - selectinload(author) 预加载，避免 MissingGreenlet
    - raiseload(children) 防呆，此接口用 build_memory_tree 自己组树
    """
    is_admin = bool(current_user and current_user.role == UserRole.ADMIN)
    current_user_id = current_user.id if current_user else None

    stmt = (
        select(StoryNode)
        .options(
            selectinload(StoryNode.author),
            defer(StoryNode.content),
            raiseload(StoryNode.children),
        )
        .where(StoryNode.book_id == book_id)
        .order_by(StoryNode.id)
    )
    stmt = _visible_filter(stmt, is_admin, current_user_id)

    nodes = (await db.execute(stmt)).scalars().all()
    logger.info(
        "Story tree query result: book_id=%s user_id=%s role=%s is_admin=%s node_count=%s nodes=%s",
        book_id,
        current_user_id,
        current_user.role.value if current_user else "guest",
        is_admin,
        len(nodes),
        [
            {
                "id": node.id,
                "parent_id": node.parent_id,
                "status": node.status.value,
                "author_id": node.author_id,
            }
            for node in nodes
        ],
    )
    return build_memory_tree(nodes)


@router.get(
    "/node/{node_id}/lineage",
    response_model=List[node_schema.StoryNodeRead],
    summary="获取完整分支阅读路径",
    operation_id="getNodeLineage",
    responses={
        200: {"description": "获取成功"},
        404: {"model": common_schema.ErrorResponse, "description": "路径不存在或无权访问"},
    },
)
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
    返回从根到当前节点的路径（按 id 升序，即插入顺序）。
    权限规则：
    - admin：所有节点可见
    - 普通用户：published + 自己的（pending/archived）
    - 游客：只看 published（传入非 published 节点 id 会返回 404）
    """
    is_admin = bool(current_user and current_user.role == UserRole.ADMIN)
    user_id = current_user.id if current_user else None

    if is_admin:
        anchor_vis = "1=1"
        rec_vis = "1=1"
    elif user_id is not None:
        anchor_vis = "(status = 'published' OR author_id = :user_id)"
        rec_vis = "(n.status = 'published' OR n.author_id = :user_id)"
    else:
        anchor_vis = "status = 'published'"
        rec_vis = "n.status = 'published'"

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
    SELECT * FROM story_path ORDER BY id ASC;
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
        400: {"model": common_schema.ErrorResponse, "description": "活动不允许投稿或分支已完结"},
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
    return await create_story_node_record(db=db, current_user=current_user, node_in=node_in)


@router.get(
    "/node",
    response_model=List[node_schema.StoryNodeListItem],
    summary="获取某个节点的直接子分支",
    operation_id="getNodeChildren",
)
async def read_child_nodes(
    parent_id: int = Query(..., ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(deps.get_current_user_or_none),
    db: AsyncSession = Depends(get_db),
):
    is_admin = bool(current_user and current_user.role == UserRole.ADMIN)
    current_user_id = current_user.id if current_user else None

    stmt = (
        select(StoryNode)
        .options(selectinload(StoryNode.author), defer(StoryNode.content))
        .where(StoryNode.parent_id == parent_id)
        .order_by(desc(StoryNode.created_at))
        .offset(skip)
        .limit(limit)
    )
    stmt = _visible_filter(stmt, is_admin, current_user_id)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/node/{node_id}",
    response_model=node_schema.StoryNodeRead,
    summary="查看节点正文详情",
    operation_id="getNodeDetail",
    responses={
        200: {"description": "获取成功"},
        403: {"model": common_schema.ErrorResponse, "description": "无权访问"},
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
    current_user_id = current_user.id if current_user else None

    if not _is_node_visible(node.status, node.author_id, is_admin, current_user_id):
        raise HTTPException(status_code=403, detail="该内容正在审核中或已归档，无权访问")

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

    if is_admin or is_self:
        # 管理员/本人：可按 status 过滤，不传则看全部
        if status is not None:
            stmt = stmt.where(StoryNode.status == status)
    else:
        # 其他人：只能看 published
        stmt = stmt.where(StoryNode.status == NodeStatus.PUBLISHED)

    return (await db.execute(stmt)).scalars().all()


@router.patch(
    "/node/{node_id}",
    response_model=node_schema.StoryNodeRead,
    summary="修改节点内容",
    operation_id="updateNode",
)
async def update_story_node(
    node_id: int = Path(..., ge=1),
    node_in: node_schema.NodeUpdate = Body(...),
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    node = await db.get(StoryNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")

    if node.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="无权修改")

    update_data = node_in.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="没有可更新的字段")

    if current_user.role != UserRole.ADMIN and node.status == NodeStatus.ARCHIVED:
        raise HTTPException(status_code=400, detail="归档节点不可修改")

    if current_user.role != UserRole.ADMIN and node.status == NodeStatus.PUBLISHED:
        protected_fields = {"content", "title", "branch_name", "summary"}
        if protected_fields.intersection(update_data):
            raise HTTPException(status_code=400, detail="已发布节点暂不允许普通用户直接修改")

    for field, value in update_data.items():
        setattr(node, field, value)

    # 同步更新字数
    if "content" in update_data:
        node.word_count = len(update_data["content"])

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="更新失败") from e

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
    summary="软删除节点（标记为 archived）",
    operation_id="deleteNode",
    responses={
        200: {"description": "节点已归档"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
        403: {"model": common_schema.ErrorResponse, "description": "无权删除"},
        404: {"model": common_schema.ErrorResponse, "description": "节点不存在"},
    }
)
async def delete_story_node(
    node_id: int = Path(..., ge=1),
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    软删除节点：将节点标记为 archived，而非真正从数据库删除。
    
    权限规则：
    - 仅作者本人或管理员可以删除
    - 被驳回（archived）的节点会自动对普通用户隐藏
    
    注意：
    - 不会检查节点是否有子节点（允许删除有子节点的节点）
    - 删除后节点仍保留在数据库中，状态变为 archived
    - 作者和管理员仍可查看被删除的节点
    """
    node = await db.get(StoryNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")

    if node.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="无权删除")

    if node.status == NodeStatus.ARCHIVED:
        return {"detail": "节点已是 archived 状态"}

    try:
        node.status = NodeStatus.ARCHIVED
        node.archived_at = datetime.now(timezone.utc)
        node.archived_reason = "用户主动删除"
        db.add(node)
        
        # 删除节点时同步回收父节点 children_count，避免负值
        if node.parent_id is not None:
            parent_node = await db.get(StoryNode, node.parent_id)
            if parent_node:
                if parent_node.children_count is None:
                    parent_node.children_count = 0
                elif parent_node.children_count > 0:
                    parent_node.children_count -= 1
                db.add(parent_node)
        
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="删除失败") from e

    return {"detail": "节点已归档"}
