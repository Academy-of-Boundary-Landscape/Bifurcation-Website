import shutil
import os
import uuid
import logging
from typing import Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from pydantic import BaseModel
from app.api import deps
from app.models.user import User
from app.schemas import common as common_schema

router = APIRouter()
logger = logging.getLogger(__name__)

# --- 1. 定义响应模型 (建议放入 schemas/upload.py) ---
class UploadResponse(BaseModel):
    url: str

# --- 2. 配置 ---
UPLOAD_DIR = "static/uploads"
# 启动时确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post(
    "/", 
    response_model=UploadResponse, # ⭐ 消除前端的 any
    summary="上传图片 (返回URL)",
    operation_id="uploadImage",
    responses={
        200: {"description": "上传成功"},
        400: {"model": common_schema.ErrorResponse, "description": "文件类型/大小不合法"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
        500: {"model": common_schema.ErrorResponse, "description": "服务器内部错误"}
    }
)
async def upload_image(
    file: UploadFile = File(...),
    # 🛡️ 增加权限检查：只有登录用户可以上传
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    # 1. 🛡️ 防御性检查：检查文件名是否存在
    if not file.filename:
        raise HTTPException(status_code=400, detail="未选择文件或文件名为空")

    # 2. 🛡️ 验证文件类型 (基于 MIME type)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只能上传图片文件 (jpg, png, gif等)")
    
    # 3. 🛡️ 验证文件大小 (例如限制为 5MB)
    MAX_SIZE = 5 * 1024 * 1024 # 5MB
    # 注意：某些环境下 file.size 可能为 None，需要谨慎处理
    if file.size and file.size > MAX_SIZE:
        raise HTTPException(status_code=400, detail="文件过大，不能超过 5MB")

    # 4. 🛡️ 安全地生成文件名
    file_parts = file.filename.rsplit(".", 1)
    file_ext = file_parts[-1].lower() if len(file_parts) > 1 else "jpg"
    
    # 限制后缀名，防止上传恶意脚本 (如 .php, .sh)
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的文件后缀")

    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # 5. 读取首字节，避免空文件导致 500
    await file.seek(0)
    first_chunk = await file.read(1)
    if not first_chunk:
        raise HTTPException(status_code=400, detail="文件内容为空")
    await file.seek(0)
    
    # 6. 保存文件
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error("文件保存失败: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="服务器文件保存失败，请稍后重试"
        )
    finally:
        await file.close()
        
    # 7. 返回 URL (建议使用相对路径或从配置中读取域名)
    return {"url": f"/static/uploads/{unique_filename}"}