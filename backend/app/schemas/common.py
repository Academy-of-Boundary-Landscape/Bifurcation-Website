from typing import List, Any
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str


class ValidationErrorItem(BaseModel):
    loc: List[Any]
    msg: str
    type: str


class ValidationErrorResponse(BaseModel):
    detail: List[ValidationErrorItem]

class MessageResponse(BaseModel):
    # 将 msg 改为 detail，以匹配 FastAPI 的 HTTPException 默认行为
    detail: str
