"""一次性对账脚本：从源表重算所有节点的冗余计数，修正历史漂移。

口径（与 services / api 的维护逻辑一致）：
- likes_count    = 该节点的 NodeLike 行数
- comments_count = 该节点未软删（deleted_at IS NULL）的评论数
- children_count = 该节点 status != ARCHIVED 的直接子节点数

用法（在 backend 目录、激活 venv 后）：
    python -m scripts.recount          # 应用修正
    python -m scripts.recount --dry-run  # 只报告不写库

幂等、可重复运行。打印被修正的节点数量。
"""
from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.interaction import StoryComment
from app.models.story import NodeLike, NodeStatus, StoryNode


async def _recount(session: AsyncSession, dry_run: bool) -> int:
    # 真实值子查询
    likes_sq = (
        select(NodeLike.node_id, func.count().label("c"))
        .group_by(NodeLike.node_id)
        .subquery()
    )
    comments_sq = (
        select(StoryComment.node_id, func.count().label("c"))
        .where(StoryComment.deleted_at.is_(None))
        .group_by(StoryComment.node_id)
        .subquery()
    )
    Child = StoryNode.__table__.alias("child")
    children_sq = (
        select(Child.c.parent_id, func.count().label("c"))
        .where(Child.c.parent_id.isnot(None), Child.c.status != NodeStatus.ARCHIVED)
        .group_by(Child.c.parent_id)
        .subquery()
    )

    nodes = (await session.execute(select(StoryNode))).scalars().all()
    fixed = 0
    for node in nodes:
        true_likes = (await session.execute(select(likes_sq.c.c).where(likes_sq.c.node_id == node.id))).scalar() or 0
        true_comments = (await session.execute(select(comments_sq.c.c).where(comments_sq.c.node_id == node.id))).scalar() or 0
        true_children = (await session.execute(select(children_sq.c.c).where(children_sq.c.parent_id == node.id))).scalar() or 0

        if (node.likes_count, node.comments_count, node.children_count) != (true_likes, true_comments, true_children):
            fixed += 1
            print(
                f"node {node.id}: likes {node.likes_count}->{true_likes}  "
                f"comments {node.comments_count}->{true_comments}  "
                f"children {node.children_count}->{true_children}"
            )
            if not dry_run:
                await session.execute(
                    update(StoryNode)
                    .where(StoryNode.id == node.id)
                    .values(
                        likes_count=true_likes,
                        comments_count=true_comments,
                        children_count=true_children,
                    )
                )

    if not dry_run:
        await session.commit()
    return fixed


async def main() -> None:
    parser = argparse.ArgumentParser(description="重算节点冗余计数")
    parser.add_argument("--dry-run", action="store_true", help="只报告不写库")
    args = parser.parse_args()

    async with AsyncSessionLocal() as session:
        fixed = await _recount(session, args.dry_run)

    verb = "需修正" if args.dry_run else "已修正"
    print(f"\n完成：{verb} {fixed} 个节点。")


if __name__ == "__main__":
    asyncio.run(main())
