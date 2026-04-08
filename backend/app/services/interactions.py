from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.interaction import NotificationType, StoryComment
from app.models.story import NodeLike, StoryNode
from app.models.user import User
from app.schemas import interaction as interact_schema
from app.utils.notification import send_notification


async def toggle_story_node_like(
    db: AsyncSession,
    current_user: User,
    node_id: int,
) -> dict[str, int | str]:
    node = await db.get(StoryNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    if node.freeze_interactions:
        raise HTTPException(status_code=400, detail="该节点已冻结互动")

    if node.likes_count is None:
        node.likes_count = 0

    stmt = select(NodeLike).where(
        NodeLike.user_id == current_user.id,
        NodeLike.node_id == node_id,
    )
    result = await db.execute(stmt)
    existing_like = result.scalars().first()

    if existing_like:
        await db.delete(existing_like)
        if node.likes_count > 0:
            node.likes_count -= 1
        action = "unliked"
    else:
        db.add(NodeLike(user_id=current_user.id, node_id=node_id))
        node.likes_count += 1
        action = "liked"
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


async def create_story_comment(
    db: AsyncSession,
    current_user: User,
    node_id: int,
    comment_in: interact_schema.CommentCreate,
) -> StoryComment:
    node = await db.get(StoryNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    if node.freeze_interactions:
        raise HTTPException(status_code=400, detail="该节点已冻结互动")
    if not comment_in.content or not comment_in.content.strip():
        raise HTTPException(status_code=400, detail="评论内容不能为空")

    comment = StoryComment(
        node_id=node_id,
        book_id=node.book_id,
        user_id=current_user.id,
        content=comment_in.content.strip(),
    )
    db.add(comment)

    if node.comments_count is None:
        node.comments_count = 0
    node.comments_count += 1

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

    return (
        await db.execute(
            select(StoryComment)
            .options(selectinload(StoryComment.user))
            .where(StoryComment.id == comment.id)
        )
    ).scalars().first()
