# app/utils/notification.py
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interaction import Notification, NotificationType


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
    - dedupe_key: 去重键，防止同类事件刷屏

    注意：此函数不 commit，依赖调用方统一 commit。
    """
    # 自己不通知自己
    if sender_id is not None and sender_id == receiver_id:
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
