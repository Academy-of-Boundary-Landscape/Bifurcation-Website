"""列表端点的总数暴露工具。

约定：列表端点的响应体仍是裸 `List[X]`（非破坏），真实总数通过响应头
`X-Total-Count` 暴露，供前端显示诚实的"共 N 条"而不是被 limit 截断的当前页长度。

用法：
    base = select(Model).where(*filters)          # 仅过滤，不要 order_by/offset/limit/options
    await set_total_header(response, db, base)     # 写入 X-Total-Count
    rows = (await db.execute(base.options(...).order_by(...).offset(skip).limit(limit))).scalars().all()
"""
from __future__ import annotations

from fastapi import Response
from sqlalchemy import func, select


async def list_total(db, base_stmt) -> int:
    """对"仅过滤"的 select 求真实总数（忽略分页与排序）。"""
    result = await db.execute(select(func.count()).select_from(base_stmt.order_by(None).subquery()))
    return result.scalar() or 0


async def set_total_header(response: Response, db, base_stmt) -> int:
    """求总数并写入 X-Total-Count 响应头，返回该总数。"""
    total = await list_total(db, base_stmt)
    response.headers["X-Total-Count"] = str(total)
    return total
