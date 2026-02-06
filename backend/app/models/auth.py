# 验证码

from sqlalchemy import String, DateTime, func
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

# 枚举类 验证码用途
import enum
class VerificationPurpose(str, enum.Enum):
    REGISTER = "register"      # 注册
    RESET_PASSWORD = "reset_password"  # 重置密码
    CHANGE_EMAIL = "change_email"      # 更改邮箱
from sqlalchemy import Enum as SAEnum

class EmailVerificationCode(Base):
    __tablename__ = "email_verification_codes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    purpose: Mapped[VerificationPurpose] = mapped_column(SAEnum(VerificationPurpose, name="verification_purpose"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False)  # 验证码内容
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    is_used: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)  # 是否已使用

