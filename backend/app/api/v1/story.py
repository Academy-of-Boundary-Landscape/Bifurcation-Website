# app/api/v1/story.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import desc, select, text, or_, update
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
from app.models.interaction import NotificationType
from app.utils.notification import send_notification

router = APIRouter()


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
    is_admin = current_user.role == UserRole.ADMIN

    # 1) 活动检查：phase 必须是 writing（或管理员），且 allow_new_nodes 开关打开
    book = await db.get(StoryBook, node_in.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="活动不存在")

    if not is_admin:
        if book.phase != BookPhase.WRITING:
            raise HTTPException(status_code=400, detail="当前活动阶段不允许投稿")
        if not book.allow_new_nodes:
            raise HTTPException(status_code=400, detail="活动已暂停接受新投稿")

    # 2) 根节点与父节点逻辑
    parent_node: Optional[StoryNode] = None
    root_id: int

    if node_in.parent_id is None:
        # 创建根节点：仅管理员可以
        if not is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以创建开篇")
        # root_id 在 commit 后用自身 id 回填（见下方）
        root_id = 0  # 占位，commit 后更新
    else:
        parent_node = await db.get(StoryNode, node_in.parent_id)
        if not parent_node:
            raise HTTPException(status_code=404, detail="父节点不存在")

        if parent_node.book_id != node_in.book_id:
            raise HTTPException(status_code=400, detail="父节点不属于同一活动")

        if not is_admin:
            if parent_node.is_ending:
                raise HTTPException(status_code=400, detail="该分支已完结")
            if parent_node.status != NodeStatus.PUBLISHED:
                raise HTTPException(status_code=403, detail="无法在未发布节点后续写")

        root_id = parent_node.root_id

    # 3) 创建节点
    now = datetime.now(timezone.utc)
    initial_status = NodeStatus.PUBLISHED if is_admin else NodeStatus.PENDING
    initial_visibility = NodeVisibility.PUBLIC if is_admin else NodeVisibility.PRIVATE

    new_node = StoryNode(
        book_id=node_in.book_id,
        parent_id=node_in.parent_id,
        root_id=root_id,
        author_id=current_user.id,
        title=node_in.title,
        content=node_in.content,
        branch_name=node_in.branch_name,
        summary=node_in.summary,
        zone=node_in.zone,
        word_count=len(node_in.content),
        status=initial_status,
        visibility=initial_visibility,
        published_at=now if is_admin else None,
        last_activity_at=now,
    )
    db.add(new_node)

    try:
        await db.flush()  # 获取 new_node.id，但不 commit

        # 根节点：root_id = 自身 id
        if node_in.parent_id is None:
            new_node.root_id = new_node.id

        await db.commit()
        await db.refresh(new_node)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="创建节点失败") from e

    # 预加载 author，避免 response_model 触发懒加载 MissingGreenlet
    new_node = (
        await db.execute(
            select(StoryNode)
            .options(selectinload(StoryNode.author))
            .where(StoryNode.id == new_node.id)
        )
    ).scalars().first()

    # 4) 通知父节点作者（失败不影响主流程）
    if parent_node and parent_node.author_id != current_user.id:
        try:
            await send_notification(
                db=db,
                receiver_id=parent_node.author_id,
                sender_id=current_user.id,
                type=NotificationType.BRANCHED,
                node_id=parent_node.id,
                book_id=parent_node.book_id,
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
    node_in: node_schema.NodeUpdate = Depends(),
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
        
        # 🔧 修复问题 5: 更新父节点的 children_count
        if node.parent_id is not None:
            await db.execute(
                update(StoryNode)
                .where(StoryNode.id == node.parent_id)
                .values(children_count=StoryNode.children_count - 1)
            )
        
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="删除失败") from e

    return {"detail": "节点已归档"}
