# app/utils/notification.py
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interaction import Notification, NotificationType

DEDUPE_WINDOW_DAYS = 7

logger = logging.getLogger(__name__)


async def send_notification(
    db: AsyncSession,
    receiver_id: int,
    type: NotificationType,
    sender_id: Optional[int] = None,
    node_id: Optional[int] = None,
    comment_id: Optional[int] = None,
    message: Optional[str] = None,
    book_id: Optional[int] = None,
    dedupe_key: Optional[str] = None,
) -> None:
    """
    通用发送通知函数。

    参数说明：
    - receiver_id: 接收者用户 ID
    - type: 通知类型（NotificationType 枚举）
    - sender_id: 触发者用户 ID（系统/审核通知可为 None）
    - node_id: 关联节点 ID（点赞/续写/审核通知）
    - comment_id: 关联评论 ID（评论通知）
    - message: 附加文案（驳回原因/系统提示）
    - book_id: 冗余活动 ID（便于按活动聚合通知）
    - dedupe_key: 去重键，防止同类事件刷屏（有值时若已存在则跳过）

    注意：此函数不 commit，依赖调用方统一 commit。
    """
    # 自己不通知自己
    if sender_id is not None and sender_id == receiver_id:
        return

    # dedupe_key 去重：7 天窗口内同一 key 已存在则跳过，避免反复触发刷屏
    # 超过窗口后重新通知，确保长期沉寂后的互动仍能送达
    if dedupe_key is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=DEDUPE_WINDOW_DAYS)
        result = await db.execute(
            select(Notification).where(
                Notification.user_id == receiver_id,
                Notification.dedupe_key == dedupe_key,
                Notification.created_at >= cutoff,
            )
        )
        if result.scalars().first() is not None:
            logger.debug(
                "通知在去重窗口内已存在，跳过: receiver=%d key=%s window=%dd",
                receiver_id, dedupe_key, DEDUPE_WINDOW_DAYS,
            )
            return

    notif = Notification(
        user_id=receiver_id,
        sender_id=sender_id,
        type=type,
        node_id=node_id,
        comment_id=comment_id,
        message=message,
        book_id=book_id,
        dedupe_key=dedupe_key,
        is_read=False,
    )
    db.add(notif)
    logger.debug(
        "通知已创建: type=%s receiver=%d sender=%s node=%s key=%s",
        type.value, receiver_id, sender_id, node_id, dedupe_key,
    )
