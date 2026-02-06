# app/api/api.py
from fastapi import APIRouter
from app.api.v1 import auth, story, users, interaction, admin, discovery, upload

api_router = APIRouter()

# 挂载 auth 模块
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# 后续会挂载 story 等模块
api_router.include_router(story.router, prefix="/story", tags=["story"])

api_router.include_router(users.router, prefix="/users", tags=["users"])

api_router.include_router(interaction.router, prefix="/interaction", tags=["Interaction"])
# 挂载管理员模块
api_router.include_router(admin.router, prefix="/admin", tags=["Admin (God Mode)"])


api_router.include_router(discovery.router, prefix="/discovery", tags=["Discovery"])

api_router.include_router(upload.router, prefix="/uploads", tags=["Uploads"])