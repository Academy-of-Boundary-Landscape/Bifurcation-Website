# main.py
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.rate_limit import limiter, rate_limit_handler
from app.api.api import api_router
from dotenv import load_dotenv

load_dotenv()  # 加载环境变量

app = FastAPI(title=settings.PROJECT_NAME)

# ==========================================
# 🚦 限流（slowapi，按用户/IP，内存存储）
# ==========================================
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# ==========================================
# 🌐 CORS 跨域配置
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)

# ==========================================
# 🛡️ 全局异常处理
# ==========================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": "请求的资源不存在"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"}
    )

# ==========================================
# 📊 健康检查端点
# ==========================================

@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查端点，用于运维监控"""
    return {"status": "ok", "service": settings.PROJECT_NAME}

# ==========================================
# 📁 静态文件挂载
# ==========================================

app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================
# 🚀 API 路由挂载
# ==========================================

app.include_router(api_router, prefix=settings.API_V1_STR)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", "8057")),
    )
