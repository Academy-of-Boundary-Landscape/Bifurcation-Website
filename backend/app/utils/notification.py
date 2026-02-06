# app/utils/notification.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.interaction import Notification, NotificationType

async def send_notification(
    db: AsyncSession,
    sender_id: int,    # 谁触发的 (如果是系统通知，可以是管理员ID，或者约定为0)
    receiver_id: int,  # 发给谁
    type: NotificationType,
    target_id: int     # 关联的资源ID (通常是 node_id)
):
    """
    通用发送通知函数
    """
    # 自己不通知自己
    if sender_id == receiver_id:
        return

    notif = Notification(
        user_id=receiver_id,
        sender_id=sender_id,
        type=type,
        target_id=target_id,
        is_read=False
    )
    db.add(notif)
    # 注意：这里不 commit，依赖调用方的 commit