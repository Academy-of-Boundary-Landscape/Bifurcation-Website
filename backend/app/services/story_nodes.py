from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, update, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.interaction import NotificationType
from app.models.story import NodeStatus, NodeVisibility, StoryNode
from app.models.story_book import BookPhase, StoryBook
from app.models.user import User, UserRole
from app.schemas import story as node_schema
from app.utils.notification import send_notification

logger = logging.getLogger(__name__)


async def create_story_node_record(
    db: AsyncSession,
    current_user: User,
    node_in: node_schema.StoryNodeCreate,
) -> StoryNode:
    is_admin = current_user.role == UserRole.ADMIN

    book = await db.get(StoryBook, node_in.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="活动不存在")

    if not is_admin:
        if book.phase != BookPhase.WRITING:
            raise HTTPException(status_code=400, detail="当前活动阶段不允许投稿")
        if not book.allow_new_nodes:
            raise HTTPException(status_code=400, detail="活动已暂停接受新投稿")

    parent_node: Optional[StoryNode] = None
    root_id: int

    if node_in.parent_id is None:
        if not is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以创建开篇")
        root_id = 0
    else:
        parent_node = await db.get(StoryNode, node_in.parent_id)
        if not parent_node:
            raise HTTPException(status_code=404, detail="父节点不存在")
        if parent_node.book_id != node_in.book_id:
            raise HTTPException(status_code=400, detail="父节点不属于同一活动")

        if not is_admin:
            if parent_node.freeze_interactions:
                raise HTTPException(status_code=400, detail="该节点已冻结互动，暂不可继续续写")
            if parent_node.is_ending:
                raise HTTPException(status_code=400, detail="该分支已完结")
            if parent_node.status != NodeStatus.PUBLISHED:
                raise HTTPException(status_code=403, detail="无法在未发布节点后续写")

        root_id = parent_node.root_id

    now = datetime.now(timezone.utc)
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
        status=NodeStatus.PUBLISHED if is_admin else NodeStatus.PENDING,
        visibility=NodeVisibility.PUBLIC if is_admin else NodeVisibility.PRIVATE,
        published_at=now if is_admin else None,
        last_activity_at=now,
    )
    db.add(new_node)

    try:
        await db.flush()

        if node_in.parent_id is None:
            new_node.root_id = new_node.id
        elif parent_node is not None:
            # 原子自增父节点 children_count（统计 status != ARCHIVED 的子节点）
            await db.execute(
                update(StoryNode)
                .where(StoryNode.id == parent_node.id)
                .values(children_count=StoryNode.children_count + 1)
            )

        await db.commit()
        await db.refresh(new_node)
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="创建节点失败") from exc

    node_with_author = await load_story_node_with_author(db, new_node.id)

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
        except Exception as e:
            logger.warning("发送 BRANCHED 通知失败，节点创建不受影响: %s", e)
            await db.rollback()

    return node_with_author


async def audit_story_node_record(
    db: AsyncSession,
    current_user: User,
    node_id: int,
    audit_in: node_schema.NodeAuditRequest,
) -> StoryNode:
    node = await db.get(StoryNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    if audit_in.status == NodeStatus.PENDING:
        raise HTTPException(status_code=400, detail="审核接口不支持将节点设为 pending")

    old_status = node.status
    now = datetime.now(timezone.utc)

    node.status = audit_in.status
    node.reviewed_by = current_user.id
    node.reviewed_at = now

    notification_type: NotificationType | None = None
    notification_message: str | None = None

    if audit_in.status == NodeStatus.PUBLISHED:
        node.published_at = now
        node.visibility = NodeVisibility.PUBLIC
        node.archived_at = None
        node.archived_reason = None
        node.reject_reason = None
        notification_type = NotificationType.APPROVED
    elif audit_in.status == NodeStatus.ARCHIVED:
        node.visibility = NodeVisibility.PRIVATE
        node.archived_at = now
        node.reject_reason = audit_in.reject_reason
        node.archived_reason = audit_in.reject_reason or "管理员归档"
        notification_type = NotificationType.REJECTED
        notification_message = audit_in.reject_reason

    # 维护父节点 children_count（仅统计 status != ARCHIVED 的子节点）
    if node.parent_id is not None and old_status != audit_in.status:
        if audit_in.status == NodeStatus.ARCHIVED and old_status != NodeStatus.ARCHIVED:
            await db.execute(
                update(StoryNode)
                .where(StoryNode.id == node.parent_id)
                .values(children_count=case((StoryNode.children_count > 0, StoryNode.children_count - 1), else_=0))
            )
        elif old_status == NodeStatus.ARCHIVED and audit_in.status != NodeStatus.ARCHIVED:
            await db.execute(
                update(StoryNode)
                .where(StoryNode.id == node.parent_id)
                .values(children_count=StoryNode.children_count + 1)
            )

    if old_status != audit_in.status and notification_type:
        logger.info(
            "审核通知: node=%d type=%s reviewer=%d author=%d",
            node.id, notification_type.value, current_user.id, node.author_id,
        )
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
    return await load_story_node_with_author(db, node_id)


async def load_story_node_with_author(db: AsyncSession, node_id: int) -> StoryNode:
    return (
        await db.execute(
            select(StoryNode)
            .options(selectinload(StoryNode.author))
            .where(StoryNode.id == node_id)
        )
    ).scalars().first()
